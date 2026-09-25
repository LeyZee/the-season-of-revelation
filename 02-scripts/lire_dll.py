#!/usr/bin/env python3
"""
lire_dll.py - lire une DLL 64 bits de l'Assembly Kit (BOB, Terry...) sans outil externe.

Écrit le 21.09.2026 pour trouver pourquoi BOB ne créait pas les actions lourdes du terrain de campagne
(journal `05-journal\\2026-09-21-phase-3-terrain\\terrain.md` § 7). Méthode qui a marché : chaîne visible
→ code qui la référence → fonction qui la contient → qui l'appelle → désassemblage annoté par `cdb -z`
→ vérification sous `cdb` avec des points d'arrêt `bu module+décalage`.

Usage :
    python lire_dll.py refs     <dll> "texte 1" "texte 2"   # instructions LEA qui visent ces chaînes
    python lire_dll.py fonction <dll> 29189 2918f            # fonction (table .pdata) et appels directs
    python lire_dll.py vtable   <dll> 1627d8                 # table virtuelle, nom RTTI, constructeur
    python lire_dll.py annoter  <dll> <sortie de cdb>        # remplace adresses par imports et chaînes
Le désassemblage vient de cdb : `cdb -z <dll> -c "u 1800282f0 180029ef6; q" > sortie.txt`
(adresses = 0x180000000 + décalage). Les décalages sont des RVA en hexadécimal.
"""

import re
import struct
import sys


def sections(b):
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    nsec = struct.unpack_from("<H", b, pe + 6)[0]
    optsz = struct.unpack_from("<H", b, pe + 20)[0]
    opt = pe + 24
    base = struct.unpack_from("<Q", b, opt + 24)[0]
    secs = []
    for i in range(nsec):
        o = opt + optsz + 40 * i
        nom = b[o:o + 8].rstrip(b"\0").decode()
        vsz, va, rsz, rptr = struct.unpack_from("<IIII", b, o + 8)
        secs.append((nom, va, vsz, rptr, rsz))
    return base, secs, opt


def rva_vers_offset(secs, rva):
    for nom, va, vsz, rptr, rsz in secs:
        if va <= rva < va + max(vsz, rsz):
            return rptr + rva - va
    return None


def offset_vers_rva(secs, off):
    for nom, va, vsz, rptr, rsz in secs:
        if rptr <= off < rptr + rsz:
            return va + off - rptr
    return None


def codes(b, secs):
    """Toutes les sections exécutables : [(va, taille virtuelle, octets)]. Pas `.text` par son nom :
    dans Warhammer3.exe les noms sont brouillés, `.text` fait 512 octets et le code est dans
    `.sbss` (50 Mo) et `.shared` (160 Mo) — chercher dans `.text` seul y faisait conclure à tort
    « aucune référence aux chaînes » (erreur 56, 21.09.2026)."""
    pe = struct.unpack_from("<I", b, 0x3C)[0]
    optsz = struct.unpack_from("<H", b, pe + 20)[0]
    out = []
    for i, (nom, va, vsz, rptr, rsz) in enumerate(secs):
        carac = struct.unpack_from("<I", b, pe + 24 + optsz + 40 * i + 36)[0]
        if carac & 0x20000000:                                       # IMAGE_SCN_MEM_EXECUTE
            out.append((va, vsz, b[rptr:rptr + rsz]))
    return out


def code_de(b, secs, rva):
    """La section exécutable qui contient cette RVA : (va, taille virtuelle, octets)."""
    for va, vsz, c in codes(b, secs):
        if va <= rva < va + max(vsz, len(c)):
            return va, vsz, c
    raise ValueError(f"0x{rva:x} n'est dans aucune section exécutable")


def dans_le_code(b, secs, rva):
    return any(va <= rva < va + vsz for va, vsz, _ in codes(b, secs))


def leas(b, secs):
    """Toutes les instructions LEA relatives à RIP : cible -> [adresses]."""
    res = {}
    for va, _, c in codes(b, secs):
        for i in range(len(c) - 7):
            if c[i] in (0x48, 0x4C) and c[i + 1] == 0x8D and (c[i + 2] & 0xC7) == 0x05:
                cible = va + i + 7 + struct.unpack_from("<i", c, i + 3)[0]
                res.setdefault(cible, []).append(va + i)
    return res


def fonctions(b, secs, opt):
    rva, taille = struct.unpack_from("<II", b, opt + 112 + 8 * 3)
    o = rva_vers_offset(secs, rva)
    return [struct.unpack_from("<III", b, o + 12 * i)[:2] for i in range(taille // 12)]


def fonction_de(fns, rva):
    for debut, fin in fns:
        if debut <= rva < fin:
            return debut, fin
    return None


def appels_vers(b, secs, cible):
    res = []
    for va, _, c in codes(b, secs):
        for op in (0xE8, 0xE9):
            i = c.find(bytes([op]))
            while i != -1 and i < len(c) - 5:
                if va + i + 5 + struct.unpack_from("<i", c, i + 1)[0] == cible:
                    res.append(("call" if op == 0xE8 else "jmp", va + i))
                i = c.find(bytes([op]), i + 1)
    return res


def pointeurs_vers(b, secs, base, cible):
    res = []
    motif = struct.pack("<Q", base + cible)
    for nom, va, vsz, rptr, rsz in secs:
        if nom in (".rdata", ".data"):
            seg = b[rptr:rptr + rsz]
            j = seg.find(motif)
            while j != -1:
                res.append((nom, va + j))
                j = seg.find(motif, j + 1)
    return res


def imports(b, secs, opt):
    rva, _ = struct.unpack_from("<II", b, opt + 112 + 8)
    res = {}
    o = rva_vers_offset(secs, rva)
    while True:
        oft, _, _, nom_rva, ft = struct.unpack_from("<IIIII", b, o)
        if nom_rva == 0:
            break
        dll = b[rva_vers_offset(secs, nom_rva):].split(b"\0", 1)[0].decode()
        i = 0
        while True:
            v = struct.unpack_from("<Q", b, rva_vers_offset(secs, oft or ft) + 8 * i)[0]
            if v == 0:
                break
            nom = f"#{v & 0xffff}" if v >> 63 else \
                b[rva_vers_offset(secs, v & 0x7fffffff) + 2:].split(b"\0", 1)[0].decode(errors="replace")
            res[ft + 8 * i] = f"{dll.split('.')[0]}!{nom}"
            i += 1
        o += 20
    return res


def chaine(b, secs, rva):
    o = rva_vers_offset(secs, rva)
    if o is None:
        return None
    s = b[o:o + 200]
    m = re.match(rb"[\x20-\x7e]{3,}", s)
    if m and (len(s) == len(m.group()) or s[len(m.group())] == 0):
        return '"' + m.group().decode() + '"'
    m = re.match(rb"(?:[\x20-\x7e]\x00){3,}", s)
    return 'L"' + m.group().decode("utf-16-le") + '"' if m else None


def cmd_refs(b, base, secs, opt, textes):
    tous = leas(b, secs)
    for t in textes:
        for m in re.finditer(re.escape(t.encode()) + b"\x00", b):
            if m.start() and b[m.start() - 1] != 0:
                continue
            rva = offset_vers_rva(secs, m.start())
            for r in tous.get(rva, []):
                print(f"0x{r:x}  lea -> 0x{rva:x}  \"{t}\"")


def cmd_fonction(b, base, secs, opt, adresses):
    fns = fonctions(b, secs, opt)
    for a in adresses:
        f = fonction_de(fns, int(a, 16))
        if not f:
            print(f"0x{int(a, 16):x} : hors fonction")
            continue
        appels = ", ".join(f"{k} 0x{v:x}" for k, v in appels_vers(b, secs, f[0])) or "aucun appel direct"
        ptrs = ", ".join(f"{n} 0x{v:x}" for n, v in pointeurs_vers(b, secs, base, f[0])) or "aucun pointeur"
        print(f"0x{int(a, 16):x} dans 0x{f[0]:x}-0x{f[1]:x} ; {appels} ; {ptrs}")


def cmd_vtable(b, base, secs, opt, adresses):
    tous = leas(b, secs)
    fns = fonctions(b, secs, opt)
    for a in adresses:
        vt = int(a, 16)
        while dans_le_code(b, secs, struct.unpack_from("<Q", b, rva_vers_offset(secs, vt - 8))[0] - base):
            vt -= 8
        col = struct.unpack_from("<Q", b, rva_vers_offset(secs, vt - 8))[0] - base
        td = struct.unpack_from("<I", b, rva_vers_offset(secs, col) + 12)[0]
        nom = b[rva_vers_offset(secs, td) + 16:].split(b"\0", 1)[0].decode(errors="replace")
        print(f"entrée 0x{int(a, 16):x} : table 0x{vt:x} (rang {(int(a, 16) - vt) // 8}), type {nom}")
        for r in tous.get(vt, []):
            f = fonction_de(fns, r)
            print(f"    constructeur : lea en 0x{r:x}, fonction 0x{f[0]:x}" if f else f"    lea en 0x{r:x}")


def cmd_annoter(b, base, secs, opt, fichiers):
    imp = imports(b, secs, opt)
    for ligne in open(fichiers[0], encoding="utf-8", errors="replace"):
        ligne = ligne.rstrip("\n")
        if not re.match(r"^[0-9a-f]{8}`[0-9a-f]{8} ", ligne):
            continue
        notes = []
        for m in re.finditer(r"\(([0-9a-f]{8})`([0-9a-f]{8})\)", ligne):
            rva = int(m.group(1) + m.group(2), 16) - base
            notes.append(imp.get(rva) or chaine(b, secs, rva) or "")
        adresse = int(ligne[:17].replace("`", ""), 16) - base
        reste = re.sub(r"\s+", " ", ligne[17:].strip()).split(" ", 1)[-1]
        reste = re.sub(r"\w+!\w+\+0x[0-9a-f]+ ", "", reste)
        notes = [n for n in notes if n]
        print(f"{adresse:06x}  {reste}" + ("   ; " + " | ".join(notes) if notes else ""))


def main():
    if len(sys.argv) < 4:
        sys.exit(__doc__)
    sys.stdout.reconfigure(encoding="utf-8")
    b = open(sys.argv[2], "rb").read()
    base, secs, opt = sections(b)
    {"refs": cmd_refs, "fonction": cmd_fonction, "vtable": cmd_vtable,
     "annoter": cmd_annoter}[sys.argv[1]](b, base, secs, opt, sys.argv[3:])


if __name__ == "__main__":
    main()
