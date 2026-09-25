#!/usr/bin/env python3
"""
etat_clavier.py - touches et boutons que Windows croit enfoncés, et fenêtres posées devant l'écran ; les relâcher.

Pourquoi (23.09.2026, 02 h 50, erreur 108) : après une séance où je pilotais l'écran (caméra de Terry), Windows croyait
AltGr enfoncé (Ctrl gauche + Alt droit) : le bouton du milieu ne déplaçait plus la vue de Terry, le double-clic sur le
lanceur du jeu n'ouvrait rien, Entrée partait dans la barre de saisie de Claude. Deux événements « touche levée » ont
tout remis d'aplomb.

Usage :
    python etat_clavier.py              # lecture seule
    python etat_clavier.py --relacher   # lève chaque touche ou bouton vu enfoncé (rien d'autre n'est envoyé)
À lancer après toute séance de pilotage de l'écran.
"""

import argparse
import ctypes
import sys
import time
from ctypes import wintypes

u = ctypes.WinDLL("user32")
k = ctypes.WinDLL("kernel32")

# touche -> (nom, code de balayage, touche étendue) ; les génériques Ctrl / Alt / Maj suivent leurs côtés
TOUCHES = {0xA0: ("Maj gauche", 0x2A, False), 0xA1: ("Maj droite", 0x36, False),
           0xA2: ("Ctrl gauche", 0x1D, False), 0xA3: ("Ctrl droit", 0x1D, True),
           0xA4: ("Alt gauche", 0x38, False), 0xA5: ("Alt droit (AltGr)", 0x38, True),
           0x5B: ("Windows gauche", 0x5B, True), 0x5C: ("Windows droite", 0x5C, True)}
BOUTONS = {1: ("bouton gauche", 0x0004), 2: ("bouton droit", 0x0010), 4: ("bouton du milieu", 0x0040)}


def enfonce(v):
    return bool(u.GetAsyncKeyState(v) & 0x8000)


def etat():
    return ([n for v, (n, *_) in TOUCHES.items() if enfonce(v)] +
            [n for v, (n, _) in BOUTONS.items() if enfonce(v)])


def processus(hwnd):
    pid = wintypes.DWORD()
    u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    h = k.OpenProcess(0x1000, False, pid.value)
    nom = "?"
    if h:
        buf, taille = ctypes.create_unicode_buffer(520), wintypes.DWORD(520)
        if k.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(taille)):
            nom = buf.value.split("\\")[-1]
        k.CloseHandle(h)
    return nom


def fenetres_devant():
    """Fenêtres visibles « toujours devant » de plus de 200 × 200 px (un voile posé sur l'écran en serait une)."""
    out = []
    proc = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _):
        r = wintypes.RECT()
        u.GetWindowRect(hwnd, ctypes.byref(r))
        if u.IsWindowVisible(hwnd) and u.GetWindowLongW(hwnd, -20) & 0x8 and r.right - r.left > 200 \
                and r.bottom - r.top > 200:
            out.append(f"{processus(hwnd)} ({r.left}, {r.top}, {r.right}, {r.bottom})")
        return True

    u.EnumWindows(proc(cb), 0)
    return out


def relacher():
    for v, (n, balayage, etendue) in TOUCHES.items():
        if enfonce(v):
            u.keybd_event(v, balayage, 0x2 | (0x1 if etendue else 0), 0)
            time.sleep(0.05)
    for v, (n, evenement) in BOUTONS.items():
        if enfonce(v):
            u.mouse_event(evenement, 0, 0, 0, 0)
            time.sleep(0.05)
    time.sleep(0.2)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--relacher", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    vus = etat()
    print("vu enfoncé :", vus or "rien")
    print("fenêtres devant l'écran :", fenetres_devant() or "aucune")
    if vus and a.relacher:
        relacher()
        print("après relâchement :", etat() or "rien")
    return 1 if etat() else 0


if __name__ == "__main__":
    sys.exit(main())
