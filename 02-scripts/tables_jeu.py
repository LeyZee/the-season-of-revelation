"""Tables de base de WH3 lues dans les packs du jeu (format DB binaire), d'après le schéma de RPFM (schema_wh3.ron).

Le kit (raw_data\\db) n'a pas toutes les données du jeu : 33 arbres de technologie sur plus de cent (23.09.2026). Pour
auditer les mécaniques des factions, on lit donc db.pack et les autres packs du jeu ; nos packs à part.

    import tables_jeu as TJ
    lignes = TJ.table("technology_node_sets")           # packs du jeu : [dict]
    nous = TJ.table("missions", pack=TJ.PACK_NOUS)      # un pack donné

    python tables_jeu.py <table> [colonne=valeur ...]    # affiche les lignes

Lecture seule. Format (RPFM) : en-tête facultatif GUID (FD FE FC FF, u16 n, UTF-16), version (FC FD FE FF, u32), u8, u32
nombre de lignes ; champs : Boolean u8, I16/I32/I64, F32/F64, ColourRGB u32, StringU8 (u16 n + octets), StringU16 (u16 n
+ 2n octets), Optional* (u8 drapeau puis la valeur). Les tables à séquences imbriquées ne sont pas prises en charge.
"""
import os
import pickle
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import contenu_pack as CP  # noqa: E402

JEU = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III"
DATA = os.path.join(JEU, "data")
PACK_NOUS = os.path.join(DATA, "saison_des_revelations.pack")
PACK_STARTPOS = os.path.join(DATA, "zz_startpos_db.pack")
SCHEMA = os.path.join(os.environ.get("APPDATA", ""), "FrodoWazEre", "rpfm", "config", "schemas", "schema_wh3.ron")
CACHE = os.path.join(os.environ.get("TEMP", "."), "tables_jeu_cache")
EXCLURE = ("saison_des_revelations", "zz_startpos_db", "zz_saison")

_SCHEMA = None
_SRC = None


def schema():
    """{table_tables: {version: [(nom, type)]}}, mis en cache."""
    global _SCHEMA
    if _SCHEMA is not None:
        return _SCHEMA
    os.makedirs(CACHE, exist_ok=True)
    cache = os.path.join(CACHE, "schema.pkl")
    if os.path.exists(cache) and os.path.getmtime(cache) > os.path.getmtime(SCHEMA):
        _SCHEMA = pickle.load(open(cache, "rb"))
        return _SCHEMA
    texte = open(SCHEMA, encoding="utf-8").read()
    out = {}
    # "<table>_tables": [ (version: n, fields: [ (name: "x", field_type: T, ...), ... ], ...), ... ]
    for m in re.finditer(r'\n        "([a-z0-9_]+)": \[\n(.*?)\n        \],', texte, re.S):
        table, corps = m.group(1), "\n" + m.group(2)
        versions = {}
        for v in re.finditer(r'\n            \(\n                version: (\d+),\n                fields: \[\n(.*?)\n                \],', corps, re.S):
            champs = re.findall(r'name: "([^"]+)",\n\s+field_type: ([A-Za-z0-9]+)', v.group(2))
            versions[int(v.group(1))] = champs
        out[table] = versions
    pickle.dump(out, open(cache, "wb"))
    _SCHEMA = out
    return out


def source():
    global _SRC
    if _SRC is None:
        _SRC = CP.SourcePacks(DATA, exclure=EXCLURE)
    return _SRC


def _chaine8(b, o):
    n = struct.unpack_from("<H", b, o)[0]
    return b[o + 2:o + 2 + n].decode("utf-8", "replace"), o + 2 + n


def _chaine16(b, o):
    n = struct.unpack_from("<H", b, o)[0]
    return b[o + 2:o + 2 + 2 * n].decode("utf-16-le", "replace"), o + 2 + 2 * n


FIXES = {"Boolean": ("<B", 1), "I16": ("<h", 2), "I32": ("<i", 4), "I64": ("<q", 8), "F32": ("<f", 4),
         "F64": ("<d", 8), "ColourRGB": ("<I", 4)}


def _champ(b, o, t):
    if t in FIXES:
        fmt, n = FIXES[t]
        return struct.unpack_from(fmt, b, o)[0], o + n
    if t == "StringU8":
        return _chaine8(b, o)
    if t == "StringU16":
        return _chaine16(b, o)
    if t.startswith("Optional"):
        drapeau = b[o]
        o += 1
        if not drapeau:
            return ("" if "String" in t else None), o
        return _champ(b, o, t[len("Optional"):])
    raise ValueError(f"type de champ non pris en charge : {t}")


def decoder(octets, table_tables):
    """Lignes (dicts) d'un fichier de table."""
    b = octets
    o = 0
    if b[o:o + 4] == b"\xfd\xfe\xfc\xff":
        o += 4
        n = struct.unpack_from("<H", b, o)[0]
        o += 2 + 2 * n
    version = 0
    if b[o:o + 4] == b"\xfc\xfd\xfe\xff":
        version = struct.unpack_from("<I", b, o + 4)[0]
        o += 8
    o += 1
    n = struct.unpack_from("<I", b, o)[0]
    o += 4
    champs = schema().get(table_tables, {}).get(version)
    if champs is None:
        raise ValueError(f"{table_tables} : version {version} absente du schéma")
    lignes = []
    for _ in range(n):
        ligne = {}
        for nom, t in champs:
            ligne[nom], o = _champ(b, o, t)
        lignes.append(ligne)
    return lignes


def table(nom, pack=None):
    """Toutes les lignes de <nom> : packs du jeu (défaut) ou un pack donné. Chaque ligne porte '_fichier'."""
    tt = nom if nom.endswith("_tables") else nom + "_tables"
    pref = f"db/{tt}/"
    out = []
    if pack is None:
        src = source()
        for c in sorted(k for k in src.ou if k.startswith(pref)):
            for ligne in decoder(src.lire(c), tt):
                ligne["_fichier"] = c
                out.append(ligne)
    else:
        with open(pack, "rb") as f:
            for c, taille, off, comp in CP.index(pack):
                cn = c.replace("\\", "/").lower()
                if cn.startswith(pref):
                    f.seek(off)
                    b = f.read(taille)
                    for ligne in decoder(CP.decompresser(b) if comp else b, tt):
                        ligne["_fichier"] = cn
                        out.append(ligne)
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        print(__doc__)
        return 1
    filtres = dict(a.split("=", 1) for a in sys.argv[2:])
    for ligne in table(sys.argv[1]):
        if all(str(ligne.get(k, "")) == v for k, v in filtres.items()):
            print(ligne)
    return 0


if __name__ == "__main__":
    sys.exit(main())
