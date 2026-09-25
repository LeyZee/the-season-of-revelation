#!/usr/bin/env python3
"""
lire_vidage.py - lire un vidage memoire (.mdmp) du jeu sans debogueur.

Pourquoi : le `crash_report\\*.stack.txt` que Warhammer 3 depose ne contient que des noms de
modules (« Warhammer3, ntdll, ... ») : inutilisable. Le `.mdmp` a cote, lui, contient tout. Et il
n'y a pas de debogueur sur cette machine (Visual Studio n'est installe qu'en Build Tools, pas
d'IDE, pas de cdb.exe). Ce script lit le format MINIDUMP directement.

Ce qu'il sort :

- l'**exception** : code, adresse, sens de l'acces, adresse lue ou ecrite (flux 6) ;
- le **module** qui contient l'adresse fautive, et l'ecart depuis sa base (flux 4) ;
- les **registres** du fil fautif au moment du plantage (flux 3, CONTEXT x64) ;
- une **pile d'appel reconstituee** : on balaie la pile du fil fautif et on garde les valeurs qui
  tombent dans la partie executable d'un module charge. Sans symboles on n'a pas les noms de
  fonctions, mais on a la suite des `Warhammer3.exe+0xRVA`, ce qui suffit a comparer deux
  plantages et a poser une question precise a quelqu'un qui a les symboles ;
- les **octets de l'instruction fautive**, lus dans le fichier du module sur disque.

Les RVA sont comparables d'un vidage a l'autre tant que le jeu n'est pas mis a jour.

Usage :
    python lire_vidage.py                      # le vidage le plus recent
    python lire_vidage.py <chemin.mdmp> ...    # ceux-la
    python lire_vidage.py --tous               # tous, en tableau comparatif
"""

import glob
import os
import struct
import sys

CRASH = os.path.join(os.environ.get("APPDATA", ""), "The Creative Assembly", "Warhammer3",
                     "crash_report")
JEU = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III"

# flux MINIDUMP utilises
THREAD_LIST, MODULE_LIST, EXCEPTION, MEMORY_LIST, MEMORY64_LIST = 3, 4, 6, 5, 9

# CONTEXT x64 : decalages depuis le debut de la structure (winnt.h)
REGS = [("Rax", 0x78), ("Rcx", 0x80), ("Rdx", 0x88), ("Rbx", 0x90), ("Rsp", 0x98),
        ("Rbp", 0xA0), ("Rsi", 0xA8), ("Rdi", 0xB0), ("R8", 0xB8), ("R9", 0xC0),
        ("R10", 0xC8), ("R11", 0xD0), ("R12", 0xD8), ("R13", 0xE0), ("R14", 0xE8),
        ("R15", 0xF0), ("Rip", 0xF8)]


class Vidage:
    def __init__(self, chemin):
        self.chemin = chemin
        self.f = open(chemin, "rb")
        sig, _ver, n, rva = struct.unpack("<4sIII", self.f.read(16))
        if sig != b"MDMP":
            raise ValueError(f"{chemin} n'est pas un MINIDUMP")
        self.f.seek(rva)
        self.flux = {t: (taille, loc) for t, taille, loc in
                     (struct.unpack("<III", self.f.read(12)) for _ in range(n))}
        self.modules = self._modules()
        self.plages = self._plages()

    # ------------------------------------------------------------------ flux
    def _modules(self):
        if MODULE_LIST not in self.flux:
            return []
        _t, loc = self.flux[MODULE_LIST]
        self.f.seek(loc)
        cnt = struct.unpack("<I", self.f.read(4))[0]
        brut = [struct.unpack("<QIIII", self.f.read(24)) + (self.f.read(84),) for _ in range(cnt)]
        out = []
        for base, taille, _cks, _ts, rva_nom, _reste in brut:
            self.f.seek(rva_nom)
            ln = struct.unpack("<I", self.f.read(4))[0]
            nom = self.f.read(ln).decode("utf-16-le", "replace")
            out.append((base, taille, os.path.basename(nom), nom))
        return sorted(out)

    def _plages(self):
        """(adresse, taille, position dans le fichier) des blocs de memoire du vidage."""
        out = []
        if MEMORY64_LIST in self.flux:
            _t, loc = self.flux[MEMORY64_LIST]
            self.f.seek(loc)
            n, base_rva = struct.unpack("<QQ", self.f.read(16))
            pos = base_rva
            for _ in range(n):
                adr, taille = struct.unpack("<QQ", self.f.read(16))
                out.append((adr, taille, pos))
                pos += taille
        if MEMORY_LIST in self.flux:
            _t, loc = self.flux[MEMORY_LIST]
            self.f.seek(loc)
            n = struct.unpack("<I", self.f.read(4))[0]
            for _ in range(n):
                adr, taille, rva = struct.unpack("<QII", self.f.read(16))
                out.append((adr, taille, rva))
        return sorted(out)

    def lire(self, adresse, longueur):
        for adr, taille, pos in self.plages:
            if adr <= adresse < adr + taille:
                self.f.seek(pos + (adresse - adr))
                return self.f.read(min(longueur, taille - (adresse - adr)))
        return b""

    def module_de(self, adresse):
        for base, taille, nom, _plein in self.modules:
            if base <= adresse < base + taille:
                return nom, adresse - base
        return None, None

    # ------------------------------------------------------------ exception
    def exception(self):
        _t, loc = self.flux[EXCEPTION]
        self.f.seek(loc)
        fil, _al = struct.unpack("<II", self.f.read(8))
        code, _fl, _rec, adr, npar, _a2 = struct.unpack("<IIQQII", self.f.read(32))
        info = struct.unpack("<15Q", self.f.read(120))
        taille_ctx, rva_ctx = struct.unpack("<II", self.f.read(8))
        return dict(fil=fil, code=code, adresse=adr, params=info[:npar],
                    ctx=(taille_ctx, rva_ctx))

    def registres(self, rva_ctx):
        self.f.seek(rva_ctx)
        ctx = self.f.read(1232)
        return {nom: struct.unpack_from("<Q", ctx, off)[0] for nom, off in REGS}

    # ----------------------------------------------------------------- pile
    def pile(self, rsp, limite=40, profondeur=0x6000):
        """Sans symboles, on balaie la pile et on garde les valeurs qui pointent dans le code
        d'un module charge : ce sont les adresses de retour, plus quelques faux positifs."""
        brut = self.lire(rsp, profondeur)
        vus, out = set(), []
        for i in range(0, len(brut) - 8, 8):
            v = struct.unpack_from("<Q", brut, i)[0]
            nom, rva = self.module_de(v)
            if nom and rva and v not in vus:
                vus.add(v)
                out.append((rsp + i, nom, rva))
                if len(out) >= limite:
                    break
        return out


def octets_instruction(nom_module, rva, n=16):
    """Les octets de l'instruction fautive, relus dans le fichier du module sur disque."""
    chemins = [os.path.join(JEU, nom_module),
               os.path.join(JEU, "assembly_kit", "binaries", nom_module)]
    for p in chemins:
        if not os.path.exists(p):
            continue
        try:
            import pefile  # noqa: F401
        except ImportError:
            pass
        # conversion RVA -> decalage fichier par la table des sections du PE
        with open(p, "rb") as f:
            mz = f.read(0x400)
            e_lfanew = struct.unpack_from("<I", mz, 0x3C)[0]
            f.seek(e_lfanew)
            if f.read(4) != b"PE\0\0":
                return None
            machine, nsec, _ts, _p1, _p2, taille_opt, _car = struct.unpack("<HHIIIHH", f.read(20))
            opt = f.read(taille_opt)
            for i in range(nsec):
                s = f.read(40)
                nom = s[:8].rstrip(b"\0").decode("ascii", "replace")
                vtaille, vadr, rtaille, radr = struct.unpack_from("<IIII", s, 8)
                if vadr <= rva < vadr + max(vtaille, rtaille):
                    f.seek(radr + (rva - vadr))
                    return nom, f.read(n)
    return None


def rva_vers_fichier(chemin_pe):
    """Table des sections d'un PE : liste de (rva, taille, decalage fichier)."""
    with open(chemin_pe, "rb") as f:
        mz = f.read(0x400)
        e_lfanew = struct.unpack_from("<I", mz, 0x3C)[0]
        f.seek(e_lfanew)
        if f.read(4) != b"PE\0\0":
            return []
        _m, nsec, _ts, _p1, _p2, taille_opt, _car = struct.unpack("<HHIIIHH", f.read(20))
        f.read(taille_opt)
        out = []
        for _ in range(nsec):
            s = f.read(40)
            vtaille, vadr, rtaille, radr = struct.unpack_from("<IIII", s, 8)
            out.append((vadr, max(vtaille, rtaille), radr))
        return out


def chaines_autour(chemin_pe, rva, avant=0x900, apres=0x200):
    """Les chaines de caracteres que le code reference autour de `rva`.

    Sans symboles, c'est le seul moyen de savoir **de quoi** parle une fonction : on cherche les
    `lea r64, [rip+disp32]` (48/4C 8D modrm disp32) du voisinage, on resout la cible, et on lit ce
    qu'il y a dessus. Une chaine lisible nomme souvent la table ou le champ manipule.
    """
    sections = rva_vers_fichier(chemin_pe)
    if not sections:
        return []

    def lire_rva(r, n):
        for vadr, vtaille, radr in sections:
            if vadr <= r < vadr + vtaille:
                with open(chemin_pe, "rb") as f:
                    f.seek(radr + (r - vadr))
                    return f.read(n)
        return b""

    debut = rva - avant
    brut = lire_rva(debut, avant + apres)
    trouve, vus = [], set()
    for i in range(len(brut) - 7):
        if brut[i] in (0x48, 0x4C, 0x4D, 0x49) and brut[i + 1] == 0x8D and (brut[i + 2] & 0xC7) == 0x05:
            disp = struct.unpack_from("<i", brut, i + 3)[0]
            cible = debut + i + 7 + disp
            if cible in vus:
                continue
            vus.add(cible)
            data = lire_rva(cible, 96)
            fin = data.find(b"\0")
            s = data[:fin if fin > 0 else 96]
            if len(s) >= 4 and all(32 <= c < 127 for c in s):
                trouve.append((debut + i - rva, cible, s.decode("ascii")))
    return trouve


def montre(chemin, court=False):
    v = Vidage(chemin)
    e = v.exception()
    nom, rva = v.module_de(e["adresse"])
    sens = {0: "lecture", 1: "ecriture", 8: "execution (DEP)"}
    acces = ""
    if len(e["params"]) >= 2:
        acces = f"{sens.get(e['params'][0], e['params'][0])} de 0x{e['params'][1]:X}"
    tete = f"{os.path.basename(chemin):30s} 0x{e['code']:08X}  {acces:24s} {nom}+0x{rva:X}"
    if court:
        print(tete)
        return
    print("=" * 100)
    print(tete)
    print(f"  fil fautif : {e['fil']}   modules charges : {len(v.modules)}")

    r = v.registres(e["ctx"][1])
    print("\n  registres :")
    for i in range(0, len(REGS), 4):
        print("   ", "  ".join(f"{n}={r[n]:016X}" for n, _o in REGS[i:i + 4]))

    ins = octets_instruction(nom, rva)
    if ins:
        print(f"\n  octets a {nom}+0x{rva:X} (section {ins[0]}) : "
              + " ".join(f"{c:02X}" for c in ins[1]))

    pe = os.path.join(JEU, nom)
    if os.path.exists(pe):
        ch = chaines_autour(pe, rva)
        if ch:
            print(f"\n  chaines referencees autour de {nom}+0x{rva:X} :")
            for ecart, cible, s in ch:
                print(f"    {ecart:+6d}  ->  0x{cible:X}  {s!r}")

    print("\n  pile reconstituee (adresses de retour plausibles, du plus recent au plus ancien) :")
    for adr, m, rv in v.pile(r["Rsp"]):
        marque = "  <-- ici" if (m == nom and abs(rv - rva) < 0x200) else ""
        pe_m = os.path.join(JEU, m)
        extra = ""
        if m == nom and os.path.exists(pe_m):
            noms = [s for _e, _c, s in chaines_autour(pe_m, rv, avant=0x300, apres=0x80)
                    if 4 <= len(s) <= 60 and " " not in s]
            if noms:
                extra = "   [" + ", ".join(noms[:3]) + "]"
        print(f"    {adr:016X}   {m}+0x{rv:X}{marque}{extra}")


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8")
    args = [a for a in argv[1:] if not a.startswith("--")]
    tous = "--tous" in argv
    if tous or not args:
        fichiers = sorted(glob.glob(os.path.join(CRASH, "*.mdmp")))
        if not tous:
            fichiers = fichiers[-1:]
    else:
        fichiers = args
    if not fichiers:
        print("aucun vidage dans", CRASH)
        return 1
    for i, f in enumerate(fichiers):
        montre(f, court=tous)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
