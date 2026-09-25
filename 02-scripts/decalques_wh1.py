#!/usr/bin/env python3
"""
decalques_wh1.py - donner aux décalques de Warhammer 1 les textures que Warhammer 3 cherche.

Pourquoi (22.09.2026, journal `05-journal\\2026-09-22-phase-4\\terry-trous.md` § 5) : dans Terry (vue
« World »), des centaines de décalques de WH1 apparaissaient en carrés opaques (de la terre dans la
neige, par exemple). Un modèle de décalque de campagne (RMV2, 576 octets, matériau 100) est une boîte
qui ne cite **aucune texture** : seulement un chemin de base, sans extension, dans un champ de 256 octets
(`rigidmodels/campaign/decals/roots/wh_roots_03`). Le moteur y ajoute des suffixes, et ce ne sont pas
les mêmes dans les deux jeux :

| | WH1 | WH3 (les 278 décalques de campagne de CA) |
|---|---|---|
| couleur | `_diffuse.dds` (DXT5, forme dans l'alpha) | `_base_colour.dds` (DX10 BC3 sRGB, forme dans l'alpha) |
| matière | `_specgloss.dds` (brillance dans l'alpha), parfois absent | `_material_map.dds` (DX10 BC3 : G = rugosité, B = 0, A = 255) |
| relief | `_parallax.dds` ou `_normal.dds` (DXT5) | les mêmes, au même format |

`modeles_wh1.py` ne suivait que les fichiers **cités** : aucune texture de décalque n'avait été reprise.
Les 430 décalques propres à WH1 ne trouvaient donc rien (carrés) et les 2 103 autres prenaient les
textures remastérisées de WH3.

Conversion, sans réencodage de la couleur :
- `_base_colour` = les blocs DXT5 du `_diffuse` de WH1, sous l'en-tête DX10 de CA (BC3_UNORM_SRGB) ;
- `_parallax` / `_normal` : le fichier de WH1 tel quel ;
- `_material_map` : uniforme, R = 0, G = 255 - brillance moyenne du `_specgloss` de WH1 (255 sans
  `_specgloss`), B = 0, A = 255. Contrôle : décalque de roche `campaign_rock_decal_b`, brillance de WH1
  ≈ 22, rugosité de CA 234,6.

Le chemin de base est celui de WH1 si rien de WH3 n'y commence, sinon il est déplacé sous `_wh1/`
(comme le modèle) et réécrit dans le modèle : jamais un fichier de WH3 n'est remplacé
(`fichiers_wh1.Relocateur` appelle ce module pour tout modèle de matériau 100).

Usage (essai) :
    python decalques_wh1.py rigidmodels/campaign/decals/leaves_03.rigid_model_v2 ...
"""

import io
import os
import struct
import sys

import numpy as np
from PIL import Image

MATERIAU_DECALQUE = 100
SUFFIXES_RELIEF = ("_parallax", "_normal")
RUGOSITE_SANS_SPECGLOSS = 255
TAILLE_CARTE_MATERIAU = 64
DXGI_BC3_UNORM, DXGI_BC3_UNORM_SRGB = 77, 78
DX10_TEXTURE2D = 3


def base_citee(octets):
    """Chemin de base cité par un modèle de décalque (matériau 100), ou None si ce n'est pas un décalque."""
    if octets[:4] != b"RMV2" or len(octets) < 168:
        return None
    premier = struct.unpack_from("<I", octets, 140 + 12)[0]          # premier maillage du LOD 0
    if premier + 80 + 256 > len(octets) or struct.unpack_from("<H", octets, premier)[0] != MATERIAU_DECALQUE:
        return None
    champ = octets[premier + 80:premier + 80 + 256].split(b"\0")[0]
    return champ.decode("ascii").replace("\\", "/").lower() or None


def en_dx10(dds, dxgi):
    """Même fichier DDS (blocs inchangés) sous un en-tête DX10, comme les textures de CA."""
    if dds[84:88] != b"DXT5":
        raise ValueError(f"attendu DXT5, trouvé {dds[84:88]!r}")
    tete = bytearray(dds[:128])
    struct.pack_into("<I", tete, 24, 1)                               # profondeur 1, comme CA
    tete[84:88] = b"DX10"
    return bytes(tete) + struct.pack("<5I", dxgi, DX10_TEXTURE2D, 0, 1, 0) + dds[128:]


DXGI_BC1_UNORM_SRGB = 72


def en_dx10_couleur(dds):
    """Texture de couleur de WH1 (DXT1 ou DXT5), blocs inchangés, sous l'en-tête DX10 sRGB de CA (BC1 ou BC3)."""
    dxgi = {b"DXT1": DXGI_BC1_UNORM_SRGB, b"DXT5": DXGI_BC3_UNORM_SRGB}.get(bytes(dds[84:88]))
    if dxgi is None:
        raise ValueError(f"couleur : DXT1 ou DXT5 attendu, trouvé {dds[84:88]!r}")
    tete = bytearray(dds[:128])
    struct.pack_into("<I", tete, 24, 1)
    tete[84:88] = b"DX10"
    return bytes(tete) + struct.pack("<5I", dxgi, DX10_TEXTURE2D, 0, 1, 0) + dds[128:]


def carte_materiau_rg(r, g, taille=TAILLE_CARTE_MATERIAU):
    """`_material_map` uniforme R `r`, G `g` (rugosité), B 0, A 255 ; DX10 BC3, niveaux jusqu'à 1 x 1."""
    bloc = bytes([255, 255, 0, 0, 0, 0, 0, 0]) + struct.pack("<HHI", rgb565(r, g, 0), rgb565(r, g, 0), 0)
    niveaux, donnees, w = 0, b"", taille
    while True:
        donnees += bloc * (max(1, w // 4) ** 2)
        niveaux += 1
        if w == 1:
            break
        w //= 2
    tete = bytearray(128)
    tete[0:4] = b"DDS "
    struct.pack_into("<7I", tete, 4, 124, 0xA1007, taille, taille, (taille // 4) ** 2 * 16, 1, niveaux)
    struct.pack_into("<II", tete, 76, 32, 0x4)
    tete[84:88] = b"DX10"
    struct.pack_into("<I", tete, 108, 0x401008)
    return bytes(tete) + struct.pack("<5I", DXGI_BC3_UNORM, DX10_TEXTURE2D, 0, 1, 0) + donnees


def moyenne_canal(dds, canal=0):
    """Moyenne d'un canal (0 R ... 3 A) d'une texture DDS lisible par Pillow."""
    return float(np.array(Image.open(io.BytesIO(dds)).convert("RGBA"))[..., canal].mean())


def rgb565(r, g, b):
    return ((r * 31 + 127) // 255) << 11 | ((g * 63 + 127) // 255) << 5 | ((b * 31 + 127) // 255)


def carte_materiau(rugosite, taille=TAILLE_CARTE_MATERIAU):
    """`_material_map` uniforme (R 0, G rugosité, B 0, A 255), DX10 BC3, niveaux jusqu'à 1 x 1."""
    bloc = bytes([255, 255, 0, 0, 0, 0, 0, 0]) + struct.pack("<HHI", rgb565(0, rugosite, 0), rgb565(0, rugosite, 0), 0)
    niveaux, donnees, w = 0, b"", taille
    while True:
        donnees += bloc * (max(1, w // 4) ** 2)
        niveaux += 1
        if w == 1:
            break
        w //= 2
    tete = bytearray(128)
    tete[0:4] = b"DDS "
    struct.pack_into("<7I", tete, 4, 124, 0xA1007, taille, taille, (taille // 4) ** 2 * 16, 1, niveaux)
    struct.pack_into("<II", tete, 76, 32, 0x4)
    tete[84:88] = b"DX10"
    struct.pack_into("<I", tete, 108, 0x401008)
    return bytes(tete) + struct.pack("<5I", DXGI_BC3_UNORM, DX10_TEXTURE2D, 0, 1, 0) + donnees


def rugosite_de(specgloss):
    if specgloss is None:
        return RUGOSITE_SANS_SPECGLOSS
    a = np.array(Image.open(io.BytesIO(specgloss)).convert("RGBA"))[..., 3]
    return int(round(255 - float(a.mean())))


def textures_wh3(lire_wh1, base1):
    """{suffixe WH3 : octets} pour le décalque de WH1 de chemin de base `base1` ; None si son `_diffuse`
    manque dans WH1."""
    diffuse = lire_wh1(base1 + "_diffuse.dds")
    if diffuse is None:
        return None
    out = {"_base_colour": en_dx10(diffuse, DXGI_BC3_UNORM_SRGB),
           "_material_map": carte_materiau(rugosite_de(lire_wh1(base1 + "_specgloss.dds")))}
    for s in SUFFIXES_RELIEF:
        b = lire_wh1(base1 + s + ".dds")
        if b is not None:
            out[s] = b
    return out


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from modeles_wh1 import SourceWH1
    wh1 = SourceWH1()
    for chemin in sys.argv[1:]:
        brut = wh1.lire(chemin)
        base = base_citee(brut) if brut else None
        t = textures_wh3(wh1.lire, base) if base else None
        print(chemin, "->", base, {k: len(v) for k, v in (t or {}).items()})
