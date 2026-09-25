#!/usr/bin/env python3
"""
restaurer_lignes_kit.py - remettre NOS lignes dans `assembly_kit\\raw_data\\db` après une mise à jour du kit par Steam.

24.09.2026, 17 h 13 : Steam a mis le kit à jour (9.0) et réécrit 1 322 XML de `raw_data\\db` : toutes nos lignes ont
disparu. On ne recopie PAS les anciens fichiers (CA a changé ~7 500 lignes entre 8.1 et 9.0) : on reprend seulement nos
lignes et on les insère dans les XML de la 9.0.

Nos lignes se reconnaissent à leur `record_timestamp` (créées par nos scripts à partir du 20.09.2026, SEUIL) et à leur
`record_uuid` absent du kit neuf. Source de chaque table : la copie la plus récente parmi la photo d'avant la mise à jour
(`03-references\\instantane-wh3-8.1\\kit_raw_data_db.zip`, 23.09 à 14 h 34) et les sauvegardes de `05-journal\\db-backups`
(chacune = l'état d'une table juste AVANT une écriture). Ce qui a été écrit après la dernière sauvegarde d'une table
(lots rejoués depuis) se reprend en relançant son script, qui ne réécrit pas ce qui existe déjà.

Le texte des lignes est recopié tel quel (format du kit gardé). Colonnes : une ligne à nous qui porte une colonne
retirée par la 9.0, ou à qui manque une colonne obligatoire ajoutée par la 9.0, est signalée (rien n'est inventé).

Usage :
    python restaurer_lignes_kit.py            # à blanc : bilan par table
    python restaurer_lignes_kit.py --apply    # sauvegarde du kit 9.0 vierge dans db-backups, puis insertion
"""
import argparse
import datetime
import glob
import os
import re
import shutil
import sys
import zipfile

KIT_DB = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\db"
ATELIER = r"C:\TotalWar-CampaignMap"
PHOTO = os.path.join(ATELIER, r"03-references\instantane-wh3-8.1\kit_raw_data_db.zip")
PHOTO_QUAND = "20260923-143400"
SAUVEGARDES = os.path.join(ATELIER, r"05-journal\db-backups")
SEUIL = int(datetime.datetime(2026, 9, 20, tzinfo=datetime.timezone.utc).timestamp() * 1000)
QUAND = re.compile(r"^(\d{8}-\d{4,6})")
LIGNE = re.compile(rb'<(?P<t>[A-Za-z0-9_]+) record_uuid="(?P<u>[^"]+)"(?P<reste>[^>]*)>.*?</(?P=t)>', re.S)
HORO = re.compile(rb'record_timestamp="(\d+)"')
CHAMP = re.compile(rb"<([A-Za-z0-9_]+)(?:\s[^>]*)?>")


def copies():
    """{table.xml : [(quand, lecteur d'octets)]} : la photo, puis chaque sauvegarde datée."""
    out = {}
    z = zipfile.ZipFile(PHOTO)
    for nom in z.namelist():
        base = os.path.basename(nom)
        if base.endswith(".xml") and not base.startswith(("TWaD_", "TExc_")):
            out.setdefault(base, []).append((PHOTO_QUAND, lambda n=nom: z.read(n)))
    for d in sorted(os.listdir(SAUVEGARDES)):
        m = QUAND.match(d)
        p = os.path.join(SAUVEGARDES, d)
        if not m or not os.path.isdir(p):
            continue
        quand = m.group(1).ljust(15, "0")
        for f in glob.glob(os.path.join(p, "*.xml")):
            out.setdefault(os.path.basename(f), []).append((quand, lambda f=f: open(f, "rb").read()))
    return out


def champs_twad(table):
    p = os.path.join(KIT_DB, f"TWaD_{table}.xml")
    if not os.path.exists(p):
        return None, set()
    t = open(p, "rb").read().decode("utf-8", "replace")
    noms, obligatoires = [], set()
    for bloc in re.findall(r"<field>(.*?)</field>", t, re.S):
        n = re.search(r"<name>([^<]+)</name>", bloc)
        if not n:
            continue
        noms.append(n.group(1))
        if re.search(r"<required>1</required>", bloc):
            obligatoires.add(n.group(1))
    return set(noms), obligatoires


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    toutes = copies()
    plan, alertes, total = {}, [], 0
    for base, liste in sorted(toutes.items()):
        cible = os.path.join(KIT_DB, base)
        if not os.path.exists(cible):
            alertes.append(f"{base} : table absente du kit 9.0")
            continue
        quand, lire = max(liste, key=lambda x: x[0])
        source = lire()
        neuf = open(cible, "rb").read()
        deja = set(m.group("u") for m in LIGNE.finditer(neuf))
        table = base[:-4]
        a_nous = []
        for m in LIGNE.finditer(source):
            if m.group("t").decode() != table or m.group("u") in deja:
                continue
            h = HORO.search(m.group("reste"))
            if h and int(h.group(1)) >= SEUIL:
                a_nous.append(m.group(0))
        if not a_nous:
            continue
        noms, obligatoires = champs_twad(table)
        if noms is not None:
            vus = set()
            for l in a_nous:
                vus |= {c.decode() for c in CHAMP.findall(l)[1:]}
            retirees = sorted(vus - noms)
            manquantes = sorted(obligatoires - vus)
            if retirees or manquantes:
                alertes.append(f"{table} : colonnes retirées par la 9.0 {retirees} ; obligatoires absentes {manquantes}")
        plan[base] = (quand, a_nous, neuf)
        total += len(a_nous)
    print(f"{total} lignes à nous à remettre dans {len(plan)} tables")
    for base, (quand, lignes, _) in sorted(plan.items(), key=lambda x: -len(x[1][1])):
        print(f"  {base[:-4]:55s} {len(lignes):5d}  (copie du {quand})")
    print(f"{len(alertes)} alerte(s)")
    for al in alertes:
        print("  !!", al)
    if not a.apply:
        print("à blanc : rien n'est écrit")
        return 0
    horo = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    dest = os.path.join(SAUVEGARDES, f"{horo}-kit-9.0-vierge")
    os.makedirs(dest)
    for base in plan:
        shutil.copy2(os.path.join(KIT_DB, base), dest)
    for base, (_, lignes, neuf) in plan.items():
        fin = neuf.rfind(b"</dataroot>")
        if fin < 0:
            print(f"  !! {base} : pas de </dataroot>, laissé")
            continue
        insertion = b"\r\n".join(lignes) + b"\r\n"
        with open(os.path.join(KIT_DB, base), "wb") as f:
            f.write(neuf[:fin] + insertion + neuf[fin:])
    print(f"écrit : {len(plan)} tables ; sauvegarde des XML 9.0 d'origine dans {dest}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
