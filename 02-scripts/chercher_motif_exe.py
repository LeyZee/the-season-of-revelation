#!/usr/bin/env python3
"""
chercher_motif_exe.py - retrouver un motif d'octets dans Warhammer3.exe et rendre son adresse
virtuelle, celle que `cdb` et les piles d'appel emploient.

Pourquoi (20.09.2026, journal `phase-2-startpos-temoin.md` § 11) : le plantage du startpos lit
un tableau de 10 octets par hex, indexe par `y * largeur + x`, dont le dword a l'offset 0 est une
clef a deux niveaux. Pour savoir ce que cette clef designe il faut trouver le code qui **ecrit**
ce tableau, pas seulement celui qui le lit. Les lecteurs et l'ecrivain partagent une signature
tres reconnaissable :

    mov  r??, [base+0A0h]      ; 48/49 8b 8? a0 00 00 00
    lea  r??, [r??+r??*4]      ; 8d, modrm mod=00 rm=100, SIB scale=4 index==base  -> *5
    mov  ..., [r??+r??*2]      ; puis *2, donc un pas de 10 octets

Le script ne devine rien : il rend des adresses, a desassembler ensuite avec
`cdb -z <vidage> -c "u <adresse> L20; q"`.

Conversion offset fichier -> adresse virtuelle : lue dans l'en-tete PE (ImageBase et la table des
sections), jamais supposee.

Usage :
    python chercher_motif_exe.py --exe <Warhammer3.exe> --pas-de-10
    python chercher_motif_exe.py --exe <Warhammer3.exe> --octets "49 8b 81 a0 00 00 00"
    python chercher_motif_exe.py --exe <Warhammer3.exe> --va 0x142a43ffe    (VA -> offset)
"""

import argparse
import re
import struct
import sys

# modrm avec mod=00 et rm=100 (un octet SIB suit), pour chaque registre destination
MODRM_SIB = {0x04, 0x0C, 0x14, 0x1C, 0x24, 0x2C, 0x34, 0x3C}
# SIB avec scale=4 et index == base : donne [r+r*4] == r*5
SIB_X5 = {(2 << 6) | (r << 3) | r for r in range(8)}


def sections(blob):
    """Rend (image_base, [(nom, virtual_address, raw_offset, raw_size), ...]) lus dans le PE."""
    if blob[:2] != b"MZ":
        raise SystemExit("ce n'est pas un executable PE")
    pe = struct.unpack_from("<I", blob, 0x3C)[0]
    if blob[pe:pe + 4] != b"PE\0\0":
        raise SystemExit("signature PE absente")
    nb_sections = struct.unpack_from("<H", blob, pe + 6)[0]
    taille_opt = struct.unpack_from("<H", blob, pe + 20)[0]
    magic = struct.unpack_from("<H", blob, pe + 24)[0]
    if magic != 0x20B:
        raise SystemExit(f"executable non 64 bits (magic {magic:#x})")
    image_base = struct.unpack_from("<Q", blob, pe + 24 + 24)[0]
    debut = pe + 24 + taille_opt
    secs = []
    for i in range(nb_sections):
        o = debut + i * 40
        nom = blob[o:o + 8].rstrip(b"\0").decode("latin-1")
        # IMAGE_SECTION_HEADER : +12 VirtualAddress, +16 SizeOfRawData, +20 PointerToRawData
        va, raw_size, raw_off = struct.unpack_from("<III", blob, o + 12)
        secs.append((nom, va, raw_off, raw_size))
    return image_base, secs


def offset_vers_va(off, image_base, secs):
    for nom, va, raw_off, raw_size in secs:
        if raw_off <= off < raw_off + raw_size:
            return image_base + va + (off - raw_off), nom
    return None, None


def va_vers_offset(va, image_base, secs):
    rva = va - image_base
    for nom, sva, raw_off, raw_size in secs:
        if sva <= rva < sva + raw_size:
            return raw_off + (rva - sva), nom
    return None, None


def cherche_pas_de_10(blob, image_base, secs, fenetre):
    """Tous les endroits ou un `lea r,[r+r*4]` suit de pres une lecture de [base+0A0h]."""
    ancre = re.compile(rb"[\x48-\x4f]\x8b[\x80-\xbf]\xa0\x00\x00\x00")
    trouves = []
    for m in ancre.finditer(blob):
        fin = m.end()
        for i in range(fin, min(fin + fenetre, len(blob) - 3)):
            if blob[i] == 0x8D and blob[i + 1] in MODRM_SIB and blob[i + 2] in SIB_X5:
                va, sec = offset_vers_va(m.start(), image_base, secs)
                if va is not None:
                    suite = blob[i + 3:i + 8]
                    trouves.append((va, sec, i - fin, suite.hex(" ")))
                break
    return trouves


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--exe", required=True)
    ap.add_argument("--octets", help='motif litteral, ex. "49 8b 81 a0 00 00 00"')
    ap.add_argument("--pas-de-10", action="store_true",
                    help="chercher les acces a un tableau de 10 octets indexe depuis [base+0A0h]")
    ap.add_argument("--fenetre", type=int, default=24,
                    help="octets tolerés entre la lecture de la base et le lea (defaut 24)")
    ap.add_argument("--va", help="convertir une adresse virtuelle en offset fichier")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")

    with open(a.exe, "rb") as f:
        blob = f.read()
    image_base, secs = sections(blob)
    print(f"{a.exe}\n  {len(blob)} octets, base {image_base:#x}, {len(secs)} section(s)")
    for nom, va, raw_off, raw_size in secs:
        print(f"    {nom:8s} VA {image_base + va:#014x}  fichier {raw_off:#011x}  {raw_size} octets")
    print()

    if a.va:
        va = int(a.va, 0)
        off, sec = va_vers_offset(va, image_base, secs)
        print(f"{va:#x} -> offset fichier {off:#x} (section {sec})" if off is not None
              else f"{va:#x} : hors des sections")

    if a.octets:
        motif = bytes(int(x, 16) for x in a.octets.split())
        n = 0
        for m in re.finditer(re.escape(motif), blob):
            va, sec = offset_vers_va(m.start(), image_base, secs)
            if va is not None:
                print(f"  {va:#014x}  ({sec})")
                n += 1
        print(f"{n} occurrence(s) de {motif.hex(' ')}")

    if a.pas_de_10:
        trouves = cherche_pas_de_10(blob, image_base, secs, a.fenetre)
        print(f"{len(trouves)} acces a un tableau de pas 10 depuis [base+0A0h] :")
        for va, sec, ecart, suite in trouves:
            print(f"  {va:#014x}  ({sec})  lea a +{ecart:2d}  suite: {suite}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
