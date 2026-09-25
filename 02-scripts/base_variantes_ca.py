#!/usr/bin/env python3
"""
base_variantes_ca.py - lire et écrire les bases de variantes d'assets de CA (`warscape_asset_variation_db/*.assetdb`,
format binaire FASTBIN0), pour y AJOUTER des clés sans toucher à celles de CA (session du rendu, 23.09.2026).

Pourquoi : le jeu prend la texture de sol de chaque groupe de `texture_arrays.xml` dans
`terrain_textures_campaign.assetdb` (espaces `campaign_base_colour`, `campaign_material`, `campaign_normal` ; clé = nom du
groupe ; une variante par clé), commune à toutes les campagnes (erreur 114). Pour montrer les textures de WH1 sur notre
carte seulement, on essaie des groupes NEUFS (noms à nous), déclarés ici ; les 440 entrées de CA restent identiques à
l'octet (contrôle `aller_retour`). La copie modifiée passe devant celle de CA quand le mod est actif : elle est à refaire
depuis celle de CA après chaque mise à jour du jeu (9.0 le 24.09.2026).

Format relevé sur `terrain_textures_campaign.assetdb` (70 965 octets) :
    "FASTBIN0" | u16 version (3) | u32 somme de contrôle des critères
    u32 nombre de critères ; pour chacun : u16 version (1) | chaîne nom | u32 n | n chaînes (valeurs)
    u32 nombre d'entrées ; pour chacune :
        u16 version de clé (1) | chaîne espace | chaîne clé | u16 version de valeur (1) | u32 nombre de variantes ;
        pour chaque variante : u16 version (6) | chaîne fichier | u16 version des drapeaux (1) | u64 drapeaux 0 |
        u64 drapeaux 1 | chaîne nom affiché | u8 r | u8 g | u8 b | u32 uid
    chaîne = u16 longueur + octets (latin-1)
Usage :
    python base_variantes_ca.py      # contrôle d'aller-retour sur la base de CA (lecture seule)
"""

import struct
import sys


def _chaine(b, o):
    n = struct.unpack_from("<H", b, o)[0]
    return b[o + 2:o + 2 + n].decode("latin-1"), o + 2 + n


def _ecrire_chaine(s):
    o = s.encode("latin-1")
    return struct.pack("<H", len(o)) + o


def lire(b):
    """dict : version, controle, criteres [(version, nom, [valeurs])], entrees [dict], reste (octets non lus)."""
    if b[:8] != b"FASTBIN0":
        raise ValueError("pas une base FASTBIN0")
    version, controle = struct.unpack_from("<HI", b, 8)
    o = 14
    n = struct.unpack_from("<I", b, o)[0]
    o += 4
    criteres = []
    for _ in range(n):
        v = struct.unpack_from("<H", b, o)[0]
        nom, o = _chaine(b, o + 2)
        k = struct.unpack_from("<I", b, o)[0]
        o += 4
        valeurs = []
        for _ in range(k):
            s, o = _chaine(b, o)
            valeurs.append(s)
        criteres.append((v, nom, valeurs))
    n = struct.unpack_from("<I", b, o)[0]
    o += 4
    entrees = []
    for _ in range(n):
        vk = struct.unpack_from("<H", b, o)[0]
        espace, o = _chaine(b, o + 2)
        cle, o = _chaine(b, o)
        vv, nv = struct.unpack_from("<HI", b, o)
        o += 6
        variantes = []
        for _ in range(nv):
            vvar = struct.unpack_from("<H", b, o)[0]
            fichier, o = _chaine(b, o + 2)
            vf, f0, f1 = struct.unpack_from("<HQQ", b, o)
            o += 18
            affiche, o = _chaine(b, o)
            r, g, bl, uid = struct.unpack_from("<BBBI", b, o)
            o += 7
            variantes.append({"version": vvar, "fichier": fichier, "version_drapeaux": vf, "drapeaux0": f0,
                              "drapeaux1": f1, "affiche": affiche, "rgb": (r, g, bl), "uid": uid})
        entrees.append({"version_cle": vk, "espace": espace, "cle": cle, "version_valeur": vv, "variantes": variantes})
    return {"version": version, "controle": controle, "criteres": criteres, "entrees": entrees, "reste": b[o:]}


def ecrire(base):
    out = bytearray(b"FASTBIN0") + struct.pack("<HI", base["version"], base["controle"])
    out += struct.pack("<I", len(base["criteres"]))
    for v, nom, valeurs in base["criteres"]:
        out += struct.pack("<H", v) + _ecrire_chaine(nom) + struct.pack("<I", len(valeurs))
        for s in valeurs:
            out += _ecrire_chaine(s)
    out += struct.pack("<I", len(base["entrees"]))
    for e in base["entrees"]:
        out += struct.pack("<H", e["version_cle"]) + _ecrire_chaine(e["espace"]) + _ecrire_chaine(e["cle"])
        out += struct.pack("<HI", e["version_valeur"], len(e["variantes"]))
        for var in e["variantes"]:
            out += struct.pack("<H", var["version"]) + _ecrire_chaine(var["fichier"])
            out += struct.pack("<HQQ", var["version_drapeaux"], var["drapeaux0"], var["drapeaux1"])
            out += _ecrire_chaine(var["affiche"]) + struct.pack("<BBBI", *var["rgb"], var["uid"])
    out += base["reste"]
    return bytes(out)


def ajouter(base, espace, cle, fichier, affiche, rgb, modele=None):
    """Ajoute une clé (une variante, drapeaux de `modele` ou de la première entrée de l'espace) ; refuse une clé de CA."""
    if any(e["espace"] == espace and e["cle"] == cle for e in base["entrees"]):
        raise ValueError(f"clé déjà présente : {espace}/{cle}")
    ref = modele or next(e for e in base["entrees"] if e["espace"] == espace)
    v0 = ref["variantes"][0]
    uid = 1 + max((v["uid"] for e in base["entrees"] if e["espace"] == espace for v in e["variantes"]), default=0)
    base["entrees"].append({"version_cle": ref["version_cle"], "espace": espace, "cle": cle,
                            "version_valeur": ref["version_valeur"],
                            "variantes": [dict(v0, fichier=fichier, affiche=affiche, rgb=tuple(rgb), uid=uid)]})
    return base


def aller_retour(b):
    """Vrai si lire puis écrire rend exactement les mêmes octets."""
    return ecrire(lire(b)) == b


def main():
    import os
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from contenu_pack import SourcePacks
    s = SourcePacks(r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data")
    for c in ("warscape_asset_variation_db/terrain_textures_campaign.assetdb",
              "warscape_asset_variation_db/terrain_textures_battle.assetdb",
              "warscape_asset_variation_db/environment_map.assetdb"):
        b = s.lire(c)
        base = lire(b)
        esp = {}
        for e in base["entrees"]:
            esp[e["espace"]] = esp.get(e["espace"], 0) + 1
        print(f"{c} : {len(b)} o ; critères {[n for _, n, _ in base['criteres']]} ; {len(base['entrees'])} entrées "
              f"{esp} ; reste {len(base['reste'])} o ; aller-retour à l'octet : {aller_retour(b)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
