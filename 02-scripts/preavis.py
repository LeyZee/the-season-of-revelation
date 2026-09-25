"""Préavis d'écriture dans le kit (CLAUDE.md § 3 : 5 minutes avant toute écriture) : l'heure annoncée et la fin du
minuteur sont LA MÊME valeur, calculée une seule fois (quatre préavis devancés le 23.09.2026 : minuteur réglé à la main
sur « environ 5 min », message annonçant une autre heure).

    python preavis.py heure [--minutes 6]      écrit l'heure cible (HH:MM:SS) dans preavis_cible.txt et l'affiche :
                                               c'est elle, et elle seule, qu'on annonce aux autres sessions
    python preavis.py attendre                 dort jusqu'à l'heure cible (+ 2 s), puis affiche l'heure : à lancer en
                                               arrière-plan ; n'écrire qu'à sa fin

Le fichier cible est dans le dossier temporaire de l'utilisateur (un préavis à la fois par session)."""
import argparse
import os
import sys
import time
from datetime import datetime, timedelta

CIBLE = os.path.join(os.environ.get("TEMP", os.path.expanduser("~")), "preavis_cible.txt")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("action", choices=["heure", "attendre"])
    ap.add_argument("--minutes", type=float, default=6.0, help="délai avant l'écriture (au moins 5)")
    a = ap.parse_args()
    if a.action == "heure":
        if a.minutes < 5:
            ap.error("le préavis est d'au moins 5 minutes")
        cible = datetime.now().replace(microsecond=0) + timedelta(minutes=a.minutes)
        open(CIBLE, "w", encoding="utf-8").write(cible.isoformat())
        print(cible.strftime("%H:%M:%S"))
        return 0
    cible = datetime.fromisoformat(open(CIBLE, encoding="utf-8").read().strip())
    attente = (cible - datetime.now()).total_seconds() + 2
    print(f"écriture autorisée à {cible.strftime('%H:%M:%S')} ; attente {max(0, attente):.0f} s", flush=True)
    if attente > 0:
        time.sleep(attente)
    print("fin du préavis :", datetime.now().strftime("%H:%M:%S"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
