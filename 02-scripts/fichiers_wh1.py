#!/usr/bin/env python3
"""
fichiers_wh1.py - reprendre dans le pack privé les fichiers de Warhammer 1 (modèles, textures, matériaux)
**tels qu'ils sont dans WH1**, sans jamais remplacer un fichier de Warhammer 3.

Pourquoi (22.09.2026) : Charles veut la carte de WH1 « exactement pareille, mais dans Warhammer 3 » :
tous les objets et tous les arbres avec leurs modèles de WH1, sans équivalents de WH3. Jusqu'ici
(`modeles_wh1.py`, 21.09.2026), un modèle dont le chemin existe aussi dans WH3 prenait le fichier de WH3
(≈ 15 000 objets), parfois retouché par CA ; et les textures d'un modèle de WH1 présentes dans WH3
prenaient celles de WH3.

Règle, pour chaque fichier de WH1 demandé (et, récursivement, ce qu'il cite) :
- absent des packs de WH3 : repris sous son chemin de WH1 ;
- présent dans WH3 et **identique octet pour octet** : rien à livrer, le fichier de WH3 est le même ;
- présent dans WH3 et différent : la version de WH1 est livrée sous un chemin à nous, le dossier `_wh1`
  inséré après le premier composant (`rigidmodels/_wh1/campaign/...`), et chaque fichier qui la cite est
  corrigé (donc livré lui aussi, déplacé s'il existe dans WH3). Jamais un chemin de WH3 n'est écrasé : le
  pack est chargé par toutes les campagnes.
Les shaders ne sont pas repris (ceux du moteur de WH3 s'appliquent).

Décalques (matériau 100, 22.09.2026) : leur modèle ne cite aucune texture, seulement un chemin de base
auquel le moteur ajoute les suffixes de WH3 (`_base_colour`, `_material_map`...) ; les textures de
WH1 (`_diffuse`...) sont converties par `decalques_wh1.py`, et le modèle comme ses textures vont sous
`_wh1/` dès que WH3 a quelque chose à ce chemin de base.

Correction des chemins cités : dans un fichier XML (`.wsmodel`, `.material`, `.xml`), remplacement du
texte ; dans un modèle `.rigid_model_v2`, les chemins de textures sont dans des champs de taille fixe
(256 octets) : le nouveau chemin (5 caractères de plus) s'écrit à la place de l'ancien si la place est
libre (octets nuls) derrière, sinon le script s'arrête plutôt que d'abîmer le modèle.

Usage (module) :
    r = Relocateur()
    chemin_final = r.cible("rigidmodels/campaign/vegetation/trees/wef_large_autumn_trees_01.rigid_model_v2")
    r.octets   # {chemin final : octets à livrer}
    python fichiers_wh1.py <chemin de WH1>...     # essai : ce que deviendrait chaque fichier
"""

import bisect
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from contenu_pack import SourcePacks                                # noqa: E402
from modeles_wh1 import SourceWH1, norme, DATA_WH3                  # noqa: E402
from decalques_wh1 import base_citee, textures_wh3                  # noqa: E402

PREFIXE = "_wh1"
TEXTE = (".wsmodel", ".material", ".xml")
CHAINE = re.compile(rb"[\x20-\x7e]{6,}")
RACINES = ("rigidmodels/", "materials/", "textures/", "variantmeshes/", "terrain/")


def deplace(chemin):
    """rigidmodels/campaign/x.rigid_model_v2 -> rigidmodels/_wh1/campaign/x.rigid_model_v2"""
    tete, reste = chemin.split("/", 1)
    return f"{tete}/{PREFIXE}/{reste}"


# Textures de TERRAIN citées par des objets (23.09.2026, 21 h ; plantage de rendu +0x1A3DCFA : base des tuiles dans la
# pile, chemins de nos textures de montagnes dans le vidage ; piste « b » retenue avec la session Construction). Quatre
# modèles de WH1 (montagnes de l'Empire `empire_skew`, `empire_square`, `empire_triangle`, 9 poses ; écran d'avant-bataille
# du Chaos) citent en chemin complet des textures de `terrain/textures/campaign/default/`, là où CA range les textures des
# tuiles (les maillages de ses falaises y puisent). Comme les montagnes de WH1 (`montagnes_wh1.TEXTURES_OBJET`), elles vont
# sous un chemin d'objet, et le « dossier des textures » de l'en-tête des morceaux suit : aucun objet ne cite plus
# `terrain/` (contrôlé par `controle_textures_objets.py`).
DOSSIER_TEXTURES_TERRAIN = f"rigidmodels/{PREFIXE}/textures_terrain"
TERRAIN_CITE = re.compile(rb"(?<![\w/\\.-])terrain[/\\][\w/\\.-]*", re.I)


def hors_terrain(chemin):
    """terrain/textures/campaign/default/x/y.dds -> rigidmodels/_wh1/textures_terrain/campaign/default/x/y.dds, sans
    `terrain/` en tête ni `terrain/textures` dans le chemin ; vaut aussi pour un dossier (`.../x/`)."""
    reste = norme(chemin).lstrip("/").split("/", 1)[1]
    if reste.startswith("textures/"):
        reste = reste[len("textures/"):]
    return f"{DOSSIER_TEXTURES_TERRAIN}/{reste}"


def dependances(chemin, octets):
    """Chemins de fichiers cités (textures, modèles, matériaux), hors shaders et hors le fichier lui-même."""
    out = set()
    for s in CHAINE.findall(octets):
        t = s.decode("ascii", "replace")
        for m in re.finditer(r"[\w./\\-]+\.(?:dds|rigid_model_v2|wsmodel|material|xml\.material|xml|tga|png)", t, re.I):
            c = norme(m.group(0)).lstrip("/")
            if c.startswith(RACINES):
                out.add(c)
    return out - {chemin}


def _motif(ancien):
    """Motif insensible à la casse et au sens des barres pour un chemin normalisé."""
    parties = [re.escape(p.encode("ascii")) for p in ancien.split("/")]
    return re.compile(rb"[/\\]".join(parties), re.I)


MATERIAU_FEUILLAGE = 97          # RMV2 v7 de WH1 : arbres, herbes, roseaux, champignons...
TYPE_DIFFUSE, TYPE_BASE_COLOUR = 0, 27


def feuillage_wh3(chemin, octets):
    """Feuillage de WH1 (RMV2 v7, matériau 97) : la texture de couleur passe du type 0 (`diffuse` de WH1) au type 27
    (`base_colour`), le seul que WH3 lie pour ce matériau. Sans cela, arbres et herbes de WH1 s'affichent en grands
    triangles plats sans texture (essai de Charles en jeu et Terry, 22.09.2026 ; corrigé dans Terry à 19 h 30 en
    changeant ce seul champ). Les autres matériaux de WH1 (68, 86, 100) gardent leurs types : WH3 les lit."""
    if not chemin.endswith(".rigid_model_v2") or octets[:4] != b"RMV2" or int.from_bytes(octets[4:8], "little") != 7:
        return octets
    # Morceau par morceau, dans chaque LOD (23.09.2026, erreur 99) : la première version ne regardait que le premier
    # morceau du fichier. Tronc (68) puis feuillage (97) : feuillage jamais converti, gris en jeu (« arbres gris » de la
    # capture de Charles : emp_medium_trees_02 et une quinzaine d'arbustes, herbes et lisières) ; feuillage puis tronc :
    # le tronc converti à tort.
    import struct
    b = bytearray(octets)
    nlod = struct.unpack_from("<I", b, 8)[0]
    for k in range(nlod):
        nb, _, _, off = struct.unpack_from("<IIII", b, 140 + 28 * k)
        for _ in range(nb):
            if off + 12 > len(b):
                break
            mat, _u, taille, voff = struct.unpack_from("<HHII", b, off)
            if mat == MATERIAU_FEUILLAGE:
                for m in re.finditer(rb"[\w/\\.-]+\.dds", bytes(b[off:off + voff])):
                    p = off + m.start() - 4
                    if p >= off and int.from_bytes(b[p:p + 4], "little") == TYPE_DIFFUSE:
                        b[p:p + 4] = TYPE_BASE_COLOUR.to_bytes(4, "little")
            if taille == 0:
                break
            off += taille
    return bytes(b)


# COULEUR DES FEUILLAGES EN sRGB (24.09.2026, chaîne 13 ; relevé WH1 / WH3 : forêt « vert-gris délavée » ; audit
# `rapport-objets-wh1-textures.md`, D1). `feuillage_wh3` fait lire la couleur de WH1 comme `base_colour`, mais le fichier
# garde son en-tête DXT1 de WH1 : WH3 le lit sans décodage sRGB, plus clair et plus terne (vert 51/48/21 vu vers
# 123/119/82). Toutes les couleurs de CA (600 tirées au hasard, 48 de végétation) sont en DX10 sRGB, et CA a étiqueté
# ainsi le seul feuillage de WH1 qu'il a repris (`emp_shrubs`, couleur brute de WH1). Même recette que nos autres
# couleurs : `decalques_wh1.en_dx10_couleur`, blocs de WH1 inchangés octet pour octet (alpha des découpes gardé), même
# chemin. Ces `_diffuse` ne sont cités par ailleurs qu'en type 0 par des morceaux qui ont leur `_base_colour` voisin.
FEUILLAGE_SRGB = True
# LE TON DES ARBRES BRETONS (25.09.2026, 04 h 40, session du rendu ; Charles, capture de 04 h 05 : « les arbres derrière sont
# tout jaunes », décision : « comme la forêt elfe » ; enquête `scratchpad\enquete_arbres_jaunes\`). Les grands arbres
# bretons de WH1 (47 % des arbres de la carte) citent `brt_trees_diffuse.dds`, le feuillage le plus jaune de WH1 (teinte 53°,
# saturation 0,59), rendu par WH3 environ 2,1 fois sa texture (forêt elfe 1,1 à 1,35 ; shader hérité
# `fx_rigidcampaignvegetation` : texture x teinte du moteur, sans normale). Gain par canal sur les texels opaques (alpha
# inchangé ; recodé en BC7 sRGB) ; fichier cité par aucun modèle de CA. (0,35 ; 0,52 ; 0,57) = le vert sombre de WH1, à
# prendre quand l'éclairage général sera recalé sur WH1.
REGLAGE_FEUILLAGES = {"brt_trees_diffuse.dds": (0.71, 0.77, 1.00)}


def couleurs_feuillage(octets):
    """Chemins (normés) des textures citées en couleur (type 27) par les morceaux de feuillage (matériau 97) d'un RMV2 v7,
    après `feuillage_wh3`."""
    import struct
    if octets[:4] != b"RMV2" or int.from_bytes(octets[4:8], "little") != 7:
        return set()
    out = set()
    nlod = struct.unpack_from("<I", octets, 8)[0]
    for k in range(nlod):
        nb, _, _, off = struct.unpack_from("<IIII", octets, 140 + 28 * k)
        for _ in range(nb):
            if off + 12 > len(octets):
                break
            mat, _u, taille, voff = struct.unpack_from("<HHII", octets, off)
            if mat == MATERIAU_FEUILLAGE:
                for m in re.finditer(rb"[\w/\\.-]+\.dds", octets[off:off + voff]):
                    p = off + m.start() - 4
                    if p >= off and int.from_bytes(octets[p:p + 4], "little") == TYPE_BASE_COLOUR:
                        out.add(norme(m.group().decode("latin-1")))
            if taille == 0:
                break
            off += taille
    return out


# LES TEXTURES D'ATTENTE À NOUS (25.09.2026, 02 h 20 ; enquête sur les arbres vert-jaune, `scratchpad\peaufinage_arbres\`).
# Nos modèles de WH1 citent des textures d'attente absentes des deux jeux (`vegetation/textures/flatnormal.dds`,
# `settlements/textures/test_mask.dds`...), que `modeles_wh1.substituts_de_ca` livrait AU CHEMIN CITÉ. Or 277 citations de
# 283 modèles d'arbres de CA visent ce même `flatnormal.dds` sans que CA le livre : pack actif, nous changions les arbres
# de CA dans toutes les campagnes (règle « les campagnes coexistent »). Et la normale plate livrée (commontextures, format
# « bleu ») n'est pas celle que WH3 lit (format « orange », celui de `brt_trees_normal` et de la normale d'arbre de CA) :
# nos arbres recevaient peu de soleil, sauf les grands arbres bretonniens, seuls à citer leur propre normale (les touffes
# vert-jaune de la vidéo de 00 h 58). Désormais ces textures sont livrées sous un chemin à nous (`_wh1/`, les modèles de WH1
# corrigés), et la normale plate est celle de CA au format orange.
# (25.09.2026, 04 h 40 : l'explication des arbres bretons ci-dessus est RÉFUTÉE ; leurs feuillages passent par le shader
# hérité `fx_rigidcampaignvegetation`, qui ne lit aucune normale ; leur jaune vient de leur texture, voir REGLAGE_FEUILLAGES.)
SUBSTITUTS_A_NOUS = True
SOURCES_SUBSTITUTS = {"test_mask.dds": "commontextures/test_mask.dds", "test_black.dds": "commontextures/test_black.dds",
                      "test_gray.dds": "commontextures/test_gray.dds", "test_white.dds": "commontextures/test_white.dds",
                      "flatnormal.dds": "terrain/textures/common/flat_normal.dds",
                      "test_gloss_map.dds": "commontextures/test_gray.dds"}

EMISSION_K, EMISSION_P = 0.4631, 5 / 9


def emission_wh3(chemin, octets):
    """Intensité d'émission d'un matériau de WH1 (`emissive_intensity`, shader `rigid_building_emissive`) ramenée à
    l'échelle de WH3 : I3 = 0,4631 x I1^(5/9), la loi que CA a suivie pour les matériaux du Chêne des Âges présents
    dans les deux jeux (150 -> 7,48966 ; 60 -> 4,50178 ; 300 -> 11,0078 : trois points exacts). Sans cela, la pierre
    de lien elfe (120) sortait en tache blanche éblouissante dans Terry (22.09.2026, 19 h 40)."""
    if not chemin.endswith(".material"):
        return octets
    t = octets.decode("utf-8", "surrogateescape")
    motif = re.compile(r"(<name>emissive_intensity</name>\s*<type>float</type>\s*<value>)([^<]+)(</value>)")

    def conv(m):
        v = float(m.group(2))
        return m.group(1) + (f"{EMISSION_K * v ** EMISSION_P:.5f}" if v > 0 else m.group(2)) + m.group(3)
    neuf = motif.sub(conv, t)
    return neuf.encode("utf-8", "surrogateescape") if neuf != t else octets


def remplacer(chemin, octets, remplacements):
    """Réécrit dans `octets` chaque chemin cité `ancien` en `nouveau` (voir la docstring du module)."""
    if chemin.endswith(TEXTE):
        t = octets.decode("utf-8", "surrogateescape")
        for ancien, nouveau in remplacements.items():
            def sub(m, nouveau=nouveau):
                s = m.group(0)
                return nouveau.replace("/", "\\") if "\\" in s else nouveau
            t = re.sub(r"[/\\]".join(re.escape(p) for p in ancien.split("/")), sub, t, flags=re.I)
        return t.encode("utf-8", "surrogateescape")
    b = bytearray(octets)
    for ancien, nouveau in remplacements.items():
        for m in list(_motif(ancien).finditer(bytes(b))):
            p, L = m.start(), m.end() - m.start()
            n = nouveau.replace("/", "\\") if b"\\" in m.group(0) else nouveau
            nb = n.encode("ascii")
            libre = bytes(b[p + L:p + len(nb) + 1])
            if len(nb) > L and (len(libre) < len(nb) - L + 1 or any(libre)):
                raise ValueError(f"{chemin} : pas de place pour réécrire {ancien} -> {nouveau} (octet {p})")
            b[p:p + len(nb)] = nb
            if len(nb) < L:
                b[p + len(nb):p + L] = bytes(L - len(nb))
    return bytes(b)


# TEXTURES AUX DIMENSIONS DE CA (25.09.2026 ; audit des textures `rapport-pack-textures.md` § 4.4, point C1 ; accord de
# Charles du 24.09 : « Oui, vas-y pour les montagnes et les textures »). 49 textures de WH1 que nous livrons sont plus
# grandes que la version que CA a faite du même objet pour WH3 : racines des décalques en 2048 là où CA a jugé 512
# suffisant, colonies orques et crâne en 2048 contre 1024, pierre de lien en 1024 x 3072 contre 256 x 768, etc. On les
# ramène aux dimensions de CA SANS réencodage (`reduire_mips`) : les n premiers niveaux de mipmaps sont retirés (facteur
# 2^n), les niveaux restants sont ceux de WH1 octet pour octet ; l'en-tête (et DX10) ne change que par la largeur, la
# hauteur, le nombre de niveaux et `pitchOrLinearSize`. Version de CA du même objet (`Relocateur._version_de_ca`) : même
# nom de fichier sous `rigidmodels/campaign/` (celle du même dossier d'abord, `_wh1/` retiré) ; pour une carte de WH1 que
# CA ne livre plus (`_diffuse`, `_specular`, `_gloss_map`, `_spec`, `_gloss`), le `_base_colour` de CA à la même base.
# Réduite seulement si le rapport est la même puissance de 2 sur les deux côtés et que la chaîne a assez de niveaux ;
# sinon laissée et notée (`tailles_de_ca_laissees` : l'atlas `emp_shrubs` que CA a refait en 128 x 256). Aucun fichier
# de CA n'est touché. Captures avant / après, même cadrage (le détail au zoom le plus proche est celui de CA).
TAILLES_DE_CA = True
DDSD_LINEARSIZE = 0x80000
OCTETS_PAR_BLOC_FOURCC = {b"DXT1": 8, b"DXT2": 16, b"DXT3": 16, b"DXT4": 16, b"DXT5": 16, b"ATI1": 8, b"BC4U": 8,
                          b"BC4S": 8, b"ATI2": 16, b"BC5U": 16, b"BC5S": 16}
OCTETS_PAR_BLOC_DXGI = {**{d: 8 for d in (70, 71, 72, 79, 80, 81)},
                        **{d: 16 for d in (73, 74, 75, 76, 77, 78, 82, 83, 84, 94, 95, 96, 97, 98, 99)}}
CARTES_WH1_SEULEMENT = re.compile(r"(.+?)(_diffuse|_specular|_gloss_map|_spec|_gloss)\.dds$")


def _niveau(w, h, bloc):
    return max(1, (w + 3) // 4) * max(1, (h + 3) // 4) * bloc


def forme_dds(dds):
    """(largeur, hauteur, niveaux, octets par bloc, début des données) d'un DDS 2D compressé par blocs (BC1 à BC7, en-tête
    ancien ou DX10) ; ValueError pour un cube, un volume, un tableau ou un format non compressé."""
    if dds[:4] != b"DDS " or struct.unpack_from("<I", dds, 4)[0] != 124:
        raise ValueError("pas un DDS")
    h, w = struct.unpack_from("<II", dds, 12)
    niveaux = max(1, struct.unpack_from("<I", dds, 28)[0])
    if struct.unpack_from("<I", dds, 112)[0] & 0x200200:                     # DDSCAPS2 cube ou volume
        raise ValueError("cube ou volume")
    if bytes(dds[84:88]) == b"DX10":
        dxgi, dim, misc, tableau = struct.unpack_from("<IIII", dds, 128)
        if dim != 3 or misc & 0x4 or tableau != 1:
            raise ValueError(f"DX10 : pas une texture 2D simple (dimension {dim}, misc {misc}, tableau {tableau})")
        bloc, debut = OCTETS_PAR_BLOC_DXGI.get(dxgi), 148
    else:
        bloc, debut = OCTETS_PAR_BLOC_FOURCC.get(bytes(dds[84:88])), 128
    if bloc is None:
        raise ValueError(f"format non compressé par blocs ({bytes(dds[84:88])!r})")
    return w, h, niveaux, bloc, debut


def reduire_mips(dds, facteur):
    """`dds` sans ses n premiers niveaux de mipmaps (facteur = 2^n), sans réencodage : largeur, hauteur, nombre de niveaux
    et `pitchOrLinearSize` mis à jour, le reste de l'en-tête (DX10 compris) gardé, données des niveaux restants octet pour
    octet. ValueError si le facteur n'est pas une puissance de 2, si un côté ne se divise pas par lui, s'il n'y a pas
    assez de niveaux ou si la taille des données n'est pas celle de la chaîne annoncée."""
    if facteur < 1 or facteur & (facteur - 1):
        raise ValueError(f"facteur {facteur} : puissance de 2 attendue")
    n = facteur.bit_length() - 1
    w, h, niveaux, bloc, debut = forme_dds(dds)
    if n == 0:
        return bytes(dds)
    if w % facteur or h % facteur:
        raise ValueError(f"{w} x {h} non divisible par {facteur}")
    if niveaux <= n:
        raise ValueError(f"{niveaux} niveaux : pas assez pour en retirer {n}")
    tailles = [_niveau(max(1, w >> k), max(1, h >> k), bloc) for k in range(niveaux)]
    if len(dds) - debut != sum(tailles):
        raise ValueError(f"données {len(dds) - debut} o, chaîne annoncée {sum(tailles)} o")
    tete = bytearray(dds[:debut])
    nw, nh = w >> n, h >> n
    pitch, drapeaux = struct.unpack_from("<II", tete, 20)[0], struct.unpack_from("<I", tete, 8)[0]
    struct.pack_into("<II", tete, 12, nh, nw)
    if pitch == max(1, (w + 3) // 4) * bloc and not drapeaux & DDSD_LINEARSIZE:    # pas d'une ligne de blocs
        struct.pack_into("<I", tete, 20, max(1, (nw + 3) // 4) * bloc)
    elif pitch or drapeaux & DDSD_LINEARSIZE:                                      # taille du niveau 0
        struct.pack_into("<I", tete, 20, _niveau(nw, nh, bloc))
    struct.pack_into("<I", tete, 28, niveaux - n)
    return bytes(tete) + bytes(dds[debut + sum(tailles[:n]):])


class _OctetsLivres(dict):
    """{chemin final : octets à livrer} : avec `TAILLES_DE_CA`, chaque texture y entre aux dimensions de CA
    (`Relocateur._taille_de_ca`), quel que soit l'endroit du Relocateur qui la pose."""

    def __init__(self, reloc):
        super().__init__()
        self._reloc = reloc

    def __setitem__(self, chemin, octets):
        super().__setitem__(chemin, self._reloc._taille_de_ca(chemin, octets))


class Relocateur:
    def __init__(self, wh1=None, wh3=None):
        self.wh1 = wh1 or SourceWH1()
        self.wh3 = wh3 or SourcePacks(DATA_WH3)
        self.final = {}           # chemin de WH1 -> chemin final (None : introuvable dans WH1)
        self.octets = _OctetsLivres(self)   # chemin final -> octets à livrer (aux dimensions de CA : TAILLES_DE_CA)
        self.tailles_de_ca = {}             # texture réduite -> (l, h, l de CA, h de CA, niveaux retirés, octets gagnés)
        self.tailles_de_ca_laissees = {}    # texture plus grande que chez CA, non réduite -> raison
        self._ca_par_nom, self._dims_ca = None, {}
        self.identiques, self.deplaces, self.propres, self.introuvables = set(), set(), set(), []
        self.decalques = set()
        self.feuillages = 0
        self.emissions = 0
        self._en_cours = set()
        self._cles_wh3 = None
        self.cartes_citees = {}   # _diffuse de WH1 -> (spéculaire, brillance) cités à côté de lui par un modèle (types 11, 12)

    def _commence_dans_wh3(self, prefixe):
        if self._cles_wh3 is None:
            self._cles_wh3 = sorted(self.wh3.ou)
        i = bisect.bisect_left(self._cles_wh3, prefixe)
        return i < len(self._cles_wh3) and self._cles_wh3[i].startswith(prefixe)

    # Textures « détournées » (23.09.2026, erreur 100 ; capture de Charles : cristaux de glace roses). Pour un modèle v7,
    # le moteur de WH3 cherche d'abord, à côté de la texture citée X_diffuse (X_specular, X_gloss_map...), ses propres
    # noms X_base_colour et X_material_map. Quand CA a converti l'objet de WH1 pour WH3, ces fichiers existent au même
    # chemin de base : notre modèle de WH1 prend alors les textures de CA (la glace de CA est rose : 255/162/165 contre
    # 125/145/158 chez WH1). 30 jeux étaient touchés (arbustes emp_shrubs, toiles, pierres, pierres de lien, glace...).
    # Règle : tout le jeu de textures de WH1 va sous `_wh1/` dès que WH3 a l'un de ces noms à sa base.
    SUFFIXES_WH1 = ("_diffuse", "_specular", "_gloss_map", "_normal", "_mask", "_spec", "_gloss", "_emissive")
    SUFFIXES_WH3 = ("_base_colour.dds", "_material_map.dds")

    # Shaders de WH1 absents de WH3 (23.09.2026, revue complète ; contrôle du brouillon `shaders_absents.py`) : un objet
    # qui en dépend ne s'affiche pas correctement. Lave (`lava_flowing_01` : 8 modèles, 2 686 poses ; son maillage ne
    # porte que la texture factice `test_gray`) : CA a refait ces objets pour WH3 au même chemin (shader `rigid_lava`),
    # on prend les siens. Cascade (`wh_waterfall_01` : 9 poses, aucun modèle de CA) : CA a converti ce matériau
    # (`materials/environment/wh_waterfall_01`) en shader `rigid_waterfall_simple`, emplacements `s_X` -> `t_xml_X`
    # (version 2), masque `_diffuse` -> `_base_colour`, mêmes paramètres ; on applique la même conversion au nôtre.
    SHADERS_CONVERTIS = {"shaders/wh_waterfall_01.xml.shader": "shaders/rigid_waterfall_simple.xml.shader"}

    def _shader_absent(self, brut):
        """Un matériau de ce wsmodel de WH1 emploie-t-il un shader que WH3 n'a pas (et que l'on ne sait pas convertir) ?"""
        for m in re.findall(rb"<material[^>]*>([^<]+)</material>", brut):
            mb = self.wh1.lire(norme(m.decode("utf-8", "replace").strip()))
            sh = re.search(rb"<shader>([^<]+)</shader>", mb or b"")
            if sh:
                s = norme(sh.group(1).decode("utf-8", "replace").strip())
                if s not in self.wh3 and s not in self.SHADERS_CONVERTIS:
                    return True
        return False

    # Glace de WH1 (23.09.2026, revue ; Terry : cristaux de la clairière d'hiver vert-noir et brillants). Un modèle v7 sans
    # `_base_colour` est dessiné par WH3 selon un chemin de compatibilité où un spéculaire fort (165 pour la glace)
    # assombrit tout (obsidienne). CA a converti cette glace pour WH3 : `_material_map` R = spéculaire de WH1 (173),
    # G = 255 - brillance de WH1 (98,6 pour 156 : exact), mais une couleur rose (255 / 162 / 165). On applique sa recette
    # avec la couleur de WH1 (bleu-gris 125 / 145 / 158) : `_base_colour` = le `_diffuse` de WH1 (blocs inchangés, en-tête
    # DX10 sRGB), `_material_map` uniforme ; posés à côté du `_diffuse` cité, où le moteur les cherche (GUIDE n° 103).
    GLACE_WH1 = re.compile(r"/wef_ice_[a-z0-9_]+_diffuse\.dds$")
    # Tous les jeux de WH1 (23.09.2026, 04 h 40 ; captures de Charles en jeu : épines, rochers et falaises « noirs veinés de
    # blanc », l'obsidienne de la glace d'avant sa conversion, erreur 117) : même recette pour tout `_diffuse` de WH1 qui a
    # son `_specular` et son `_gloss_map`, sauf quand WH3 a déjà un `_base_colour` à ce chemin (le moteur prend alors celui
    # de CA) ou qu'un `_base_colour` est déjà fourni (feuillages).
    PBR_WH1 = re.compile(r"_diffuse\.dds$")
    # Le MÉTAL (canal R de `_material_map`) : 23.09.2026, 12 h 50 (Charles : « les statues n'ont toujours pas de texture »).
    # La recette posait R = spéculaire de WH1 partout : la statue de pierre de lune (spéculaire 154, brillance 22) devenait
    # un métal rugueux à 60 %, gris terne où la couleur disparaît. Les conversions de CA des mêmes objets de WH1 : R = 0 pour
    # la pierre, le bois, la toile (maison 57 / 34 -> 0 ; pierre de lien 27 -> 0 ; tumeur 57 -> 1,7 ; toiles 57 -> 3,9 ;
    # arche 16 -> 10,8), R fort pour ce qui est spéculaire ET brillant (or 147 / 178 -> 216 ; fer 125 / 107 -> 216 ;
    # gemmes 117 / 230 -> 158 ; armes 100 / 99 -> 139 ; glace 165 / 156 -> 173). G = 255 - brillance (tumeur, toiles, glace,
    # arche : exact). Donc métal = 1,5 x spéculaire si spéculaire et brillance >= SEUIL_METAL, sinon 0 ; la glace garde la
    # recette de CA (R = spéculaire).
    SEUIL_METAL, FACTEUR_METAL = 90, 1.5
    # LA GLACE N'EST PAS UN MÉTAL (24.09.2026, 05 h 30, session du rendu ; Charles, pack de 04 h 50 : cristaux de Tal Amere
    # et de la clairière d'hiver « lavande pâle, mats, plats », WH1 : turquoise, qui accrochent la lumière). Agent de
    # recherche (`scratchpad\agent_cristaux\rapport.md`, shader `rigid_default` désassemblé) : R du `_material_map` y est le
    # métal ; R = spéculaire de WH1 (165) faisait de la glace un métal à 65 %, couleur propre à 35 %, reflets bleu-gris : la
    # lavande terne. La glace de WH1 n'est ni transparente ni émissive (texture opaque, spéculaire neutre fort) ; la glace
    # dessinée par CA pour WH3 (`gen_icicle`) a un métal d'environ 14. La glace de WH1 prend METAL_GLACE partout, sa
    # brillance (G) reste point par point. (Mieux, plus tard : le shader de glace de CA `rigid_ice_crystal` par un .wsmodel.)
    METAL_GLACE = 14

    def _metal(self, c, spec_moyen, brillance_moyenne):
        if self.GLACE_WH1.search(c):
            return self.METAL_GLACE
        if spec_moyen >= self.SEUIL_METAL and brillance_moyenne >= self.SEUIL_METAL:
            return int(min(255, round(self.FACTEUR_METAL * spec_moyen)))
        return 0

    # ... et PIXEL PAR PIXEL (même heure ; relevé de la session d'audit) : CA fait ses `_material_map` en 512 x 512, BC3,
    # G = 255 - brillance de WH1 point par point (glace : écart-type 87, comme la brillance de WH1), alors que les nôtres
    # étaient des aplats de 64 x 64. Sur une statue presque unie (pierre de lune : couleur à 5-6 d'écart-type, glace 10-16),
    # tout le détail visible de WH1 est dans le spéculaire et la brillance : l'aplat la laissait « sans texture ».
    COTE_MAX_CARTE = 512

    def _carte_pixels(self, c, spec, gloss):
        """`_material_map` à la résolution des cartes de WH1 (512 au plus), BC7 : R = métal (`_metal`, point par point pour
        la glace et les métaux, 0 sinon), G = 255 - brillance, B 0, A 255."""
        import io
        import numpy as np
        from PIL import Image
        import bc7
        s = np.array(Image.open(io.BytesIO(spec)).convert("RGBA"))[..., 0].astype(np.float64)
        g = np.array(Image.open(io.BytesIO(gloss)).convert("RGBA"))[..., 0].astype(np.float64)
        cote = min(self.COTE_MAX_CARTE, max(s.shape[0], g.shape[0]))
        def a_la_taille(a):
            if a.shape != (cote, cote):
                a = np.array(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).resize((cote, cote), Image.BILINEAR),
                             np.float64)
            return a
        s, g = a_la_taille(s), a_la_taille(g)
        metal_moyen = self._metal(c, s.mean(), g.mean())
        if metal_moyen == 0:
            r = np.zeros_like(s)
        elif self.GLACE_WH1.search(c):
            r = np.full_like(s, float(self.METAL_GLACE))
        else:
            r = np.clip(self.FACTEUR_METAL * s, 0, 255)
        rgba = np.dstack([r, 255 - g, np.zeros_like(s), np.full_like(s, 255)])
        rgba = np.clip(np.round(rgba), 0, 255).astype(np.uint8)
        return bc7.dds_bc7(bc7.chaine(rgba), srgb=False), metal_moyen

    # Couleur des MÉTAUX (même heure) : chez CA, la couleur de base d'un métal de WH1 est celle de son SPÉCULAIRE (or : CA
    # 157 / 122 / 69, spéculaire de WH1 147 / 115 / 65, diffuse 58 / 43 / 20 ; fer : 134 contre 125 et 43), celle d'un
    # non-métal reste sa diffuse (maison, pierre de lien). Mélange point par point selon le métal.
    def _couleur_metal(self, diffuse, spec):
        import io
        import numpy as np
        from PIL import Image
        import bc7
        d = np.array(Image.open(io.BytesIO(diffuse)).convert("RGBA")).astype(np.float64)
        s = Image.open(io.BytesIO(spec)).convert("RGBA")
        if s.size != (d.shape[1], d.shape[0]):
            s = s.resize((d.shape[1], d.shape[0]), Image.BILINEAR)
        s = np.array(s).astype(np.float64)
        m = np.clip(self.FACTEUR_METAL * s[..., :1], 0, 255) / 255
        rgb = d[..., :3] * (1 - m) + s[..., :3] * m
        rgba = np.clip(np.round(np.dstack([rgb, d[..., 3:]])), 0, 255).astype(np.uint8)
        return bc7.dds_bc7(bc7.chaine(rgba), srgb=True)

    def _pbr_glace(self, c, f):
        import decalques_wh1 as D
        base1, basef = c[:-len("_diffuse.dds")], f[:-len("_diffuse.dds")]
        if basef + "_base_colour.dds" in self.octets:
            return
        if any(basef + s in self.wh3 for s in ("_base_colour.dds", "_material_map.dds")):
            self.pbr_de_ca = getattr(self, "pbr_de_ca", 0) + 1
            return
        diffuse = self.wh1.lire(c)
        # WH1 nomme aussi ses cartes `_spec` et `_gloss` (23.09.2026, 05 h ; Charles : « statues des elfes sans texture » en
        # Athel Loren) : 9 jeux étaient sautés sans bruit (pierres de lien, arches de bois-de-rêve, pierres dressées des
        # elfes, statue naine, pierres bretonnes, arbre de la sorcière, tertres de crânes, tumeurs du Chaos)
        spec = self.wh1.lire(base1 + "_specular.dds") or self.wh1.lire(base1 + "_spec.dds")
        gloss = self.wh1.lire(base1 + "_gloss_map.dds") or self.wh1.lire(base1 + "_gloss.dds")
        # sinon les cartes que le modèle cite lui-même à côté de ce `_diffuse` (autre base : statue de la Dame du Lac ;
        # textures factices `test_black` / `test_gloss_map` : accessoires des hommes-bêtes, 20 modèles)
        cite_spec, cite_gloss = self.cartes_citees.get(c, (None, None))
        spec = spec or (self.wh1.lire(cite_spec) or self.wh3.lire(cite_spec) if cite_spec else None)
        gloss = gloss or (self.wh1.lire(cite_gloss) or self.wh3.lire(cite_gloss) if cite_gloss else None)
        # factices absentes des deux jeux : `test_black` = aucun spéculaire (R 0), brillance sans objet -> mat (G 255)
        r = 0 if spec is None and cite_spec and cite_spec.rsplit("/", 1)[-1].startswith("test_black") else None
        g = 255 if gloss is None and cite_gloss and cite_gloss.rsplit("/", 1)[-1].startswith("test_gloss") else None
        if diffuse is None or (spec is None and r is None) or (gloss is None and g is None):
            self.pbr_incomplets = getattr(self, "pbr_incomplets", set()) | {c}
            return
        try:
            couleur = D.en_dx10_couleur(diffuse)
            if spec is not None and gloss is not None:
                carte, metal = self._carte_pixels(c, spec, gloss)        # cartes réelles de WH1 : point par point
                if metal and not self.GLACE_WH1.search(c):
                    couleur = self._couleur_metal(diffuse, spec)
                    self.metaux = getattr(self, "metaux", 0) + 1
            else:                                                        # factices : aplat (R 0 ou métal, G 255)
                brillance = D.moyenne_canal(gloss, 0) if gloss is not None else 0.0
                r = self._metal(c, D.moyenne_canal(spec, 0), brillance) if r is None else r
                g = int(round(255 - brillance)) if g is None else g
                carte = D.carte_materiau_rg(r, g)
        except Exception:                                                    # noqa: BLE001 - format inattendu : laissé
            self.pbr_ignores = getattr(self, "pbr_ignores", 0) + 1
            return
        self.octets[basef + "_base_colour.dds"] = couleur
        self.octets[basef + "_material_map.dds"] = carte
        if self.GLACE_WH1.search(c):
            self.glaces = getattr(self, "glaces", 0) + 1
        else:
            self.pbr = getattr(self, "pbr", 0) + 1

    def _noter_cartes(self, brut):
        """Retient, pour chaque morceau d'un modèle (hors feuillages, matériau 97), le spéculaire et la brillance cités à
        côté de son `_diffuse` (types 0, 11, 12) : `_pbr_glace` s'en sert quand WH1 n'a pas ces cartes à la même base."""
        from audit_textures import textures_du_modele
        try:
            textures = textures_du_modele(brut)
        except Exception:                                                    # noqa: BLE001 - modèle illisible : rien
            return
        morceaux = {}
        for lod, m, mat, typ, chemin in textures:
            if mat != 97:
                morceaux.setdefault((lod, m), {})[typ] = norme(chemin).lstrip("/")
        for t in morceaux.values():
            if 0 in t and t[0].endswith("_diffuse.dds") and 11 in t and 12 in t:
                self.cartes_citees.setdefault(t[0], (t[11], t[12]))

    # Emplacements de texture de WH1 (version 1, `s_X`) -> ceux des shaders de WH3 du même nom (version 2, `t_xml_X`)
    # (23.09.2026, 05 h 10 ; Charles : « statues des elfes sans texture » en Athel Loren). WH3 a gardé les shaders
    # `rigid_building_emissive`, `rigid_vertexpush`, `parallax_02`, mais ils ne lisent plus que les emplacements v2 : un
    # matériau de WH1 n'y branche AUCUNE texture (pierres de lien des elfes, lanternes, ambre, champignons et tumeurs du
    # Chaos, toiles). CA a converti ces mêmes matériaux (même chemin, ou `_alpha_off` pour la pierre de lien) :
    # `s_diffuse` -> `t_xml_base_colour` (`_base_colour`), `s_specular` + `s_gloss` -> `t_xml_material_map`, `s_normal`
    # -> `t_xml_normal`, émissifs et parallaxe renommés, `t_xml_dither` ajouté, paramètres retouchés (intensité de la
    # pierre de lien 120 -> 1,13, de la lanterne 2 500 -> 1,47 ; `emissive_scale` -> `emissive_tiling`). On part de SA
    # version et on y met NOS textures de WH1 ; sans version de CA, conversion générique des emplacements.
    V1_V2 = {"s_diffuse": "t_xml_base_colour", "s_diffuse_secondary": "t_xml_diffuse_secondary", "s_normal": "t_xml_normal",
             "s_emissive": "t_xml_emissive", "s_emissive_texture": "t_xml_emissive_texture", "s_mask": "t_xml_mask",
             "s_parallax": "t_xml_parallax", "s_parallax_secondary": "t_xml_parallax_secondary"}
    COULEURS_V2 = ("t_xml_base_colour", "t_xml_diffuse_secondary", "t_xml_parallax", "t_xml_parallax_secondary")
    SOURCES_GENERIQUES = ("commontextures/", "vfx/")

    def _couleur_wh3(self, src):
        """`X_diffuse.dds` de WH1 -> `X_base_colour.dds` (fait par `_pbr_glace`, sinon ici : couleur seule)."""
        if not src.endswith("_diffuse.dds"):
            return src
        import decalques_wh1 as D
        bc = src[:-len("_diffuse.dds")] + "_base_colour.dds"
        if bc in self.octets or bc in self.wh3:
            return bc
        d = self.octets.get(src) or self.wh1.lire(src)
        try:
            self.octets[bc] = D.en_dx10_couleur(d)
        except Exception:                                                    # noqa: BLE001 - illisible : on garde le _diffuse
            return src
        return bc

    def _carte_materiau_wh3(self, diffuse, spec, gloss):
        """`X_material_map.dds` à côté du `_diffuse` (fait par `_pbr_glace`, sinon ici d'après les cartes du matériau)."""
        import decalques_wh1 as D
        mm = diffuse[:-len("_diffuse.dds")] + "_material_map.dds"
        if mm in self.octets or mm in self.wh3:
            return mm
        s = (self.octets.get(spec) or self.wh1.lire(spec)) if spec else None
        g = (self.octets.get(gloss) or self.wh1.lire(gloss)) if gloss else None
        try:
            if s and g:
                self.octets[mm] = self._carte_pixels(diffuse, s, g)[0]
                return mm
            r = self._metal(diffuse, D.moyenne_canal(s, 0), 0.0) if s else 0
            v = int(round(255 - D.moyenne_canal(g, 0))) if g else 255
        except Exception:                                                    # noqa: BLE001
            r, v = 0, 255
        self.octets[mm] = D.carte_materiau_rg(r, v)
        return mm

    def _materiau_wh3(self, c, octets):
        """Matériau de WH1 converti pour les shaders de WH3 : shader disparu converti comme CA l'a fait
        (`SHADERS_CONVERTIS`), ou emplacements de WH1 (`s_X`) portés sur la version de CA du même matériau (`V1_V2`)."""
        t = octets.decode("utf-8", "replace")
        m = re.search(r"<shader>([^<]+)</shader>", t)
        shader = norme(m.group(1).strip()) if m else None
        if shader in self.SHADERS_CONVERTIS:
            t = t.replace(m.group(0), f"<shader>{self.SHADERS_CONVERTIS[shader]}</shader>")
            t = re.sub(r"<slot>s_([A-Za-z0-9_]+)</slot>", r'<slot version="2">t_xml_\1</slot>', t)
            t = re.sub(r"(vfx/textures/50pc_mask)_diffuse\.dds", r"\1_base_colour.dds", t, flags=re.I)
            self.convertis = getattr(self, "convertis", 0) + 1
            return t.encode("utf-8")
        if not shader or shader not in self.wh3 or not re.search(r"<slot>s_", t):
            return octets
        wh1 = {s.strip(): norme(src.strip()).lstrip("/")
               for s, src in re.findall(r"<slot[^>]*>([^<]+)</slot>\s*<source>([^<]*)</source>", t)}
        nos = {}
        for s1, s2 in self.V1_V2.items():
            if s1 in wh1 and wh1[s1]:
                nos[s2] = self._couleur_wh3(wh1[s1]) if s2 in self.COULEURS_V2 else wh1[s1]
        if wh1.get("s_diffuse", "").endswith("_diffuse.dds"):
            nos["t_xml_material_map"] = self._carte_materiau_wh3(wh1["s_diffuse"], wh1.get("s_specular"), wh1.get("s_gloss"))
        ca = None
        for chemin_ca in (c, c.replace(".xml.material", "_alpha_off.xml.material")):
            b = self.wh3.lire(chemin_ca)
            if b and norme((re.search(rb"<shader>([^<]+)</shader>", b) or [b"", b""])[1].decode().strip()) == shader:
                ca = b.decode("utf-8", "replace")
                break
        if ca:
            def sub(mm):
                slot, src = mm.group(2).strip(), mm.group(4)
                if slot in nos and not norme(src.strip()).startswith(self.SOURCES_GENERIQUES):
                    return mm.group(1) + mm.group(2) + mm.group(3) + nos[slot] + mm.group(5)
                return mm.group(0)
            neuf = re.sub(r"(<slot[^>]*>)([^<]+)(</slot>\s*<source>)([^<]*)(</source>)", sub, ca)
            nom = re.search(r"<name>[^<]*</name>", t)
            if nom:
                neuf = re.sub(r"<name>[^<]*</name>", lambda _: nom.group(0), neuf, count=1)
            self.v2_de_ca = getattr(self, "v2_de_ca", 0) + 1
        else:
            nos.setdefault("t_xml_dither", "commontextures/dither.dds")
            blocs = "".join(f'  <texture>\n   <slot version="2">{s}</slot>\n   <source>{src}</source>\n  </texture>\n'
                            for s, src in sorted(nos.items()))
            neuf = re.sub(r"<textures>.*?</textures>", lambda _: "<textures>\n" + blocs + " </textures>", t, flags=re.S)
            neuf = neuf.replace("<name>emissive_scale</name>", "<name>emissive_tiling</name>")
            self.v2_generiques = getattr(self, "v2_generiques", 0) + 1
        return neuf.encode("utf-8")

    def _sans_terrain(self, c, octets):
        """Ce qu'un fichier cite encore sous `terrain/` une fois ses textures déplacées (`hors_terrain`) : le « dossier des
        textures » de l'en-tête de chaque morceau d'un modèle de WH1, une texture introuvable. Réécrit de même ; un autre
        fichier cité sous `terrain/` (modèle, matériau) garde son chemin, qui est celui où on le livre."""
        restes = {norme(m.decode("latin-1")).lstrip("/") for m in TERRAIN_CITE.findall(octets)}
        restes = {r for r in restes if r.endswith((".dds", "/")) or "." not in r.rsplit("/", 1)[-1]}
        self.cites_terrain = getattr(self, "cites_terrain", set()) | {c}
        if not restes:
            return octets
        return remplacer(c, octets, {r: hors_terrain(r) for r in sorted(restes, key=len, reverse=True)})

    def _jeu_detourne(self, c):
        if not c.endswith(".dds") or c.startswith("rigidmodels/_wh1/"):
            return False
        for s in self.SUFFIXES_WH1:
            if c.endswith(s + ".dds"):
                base = c[:-len(s + ".dds")]
                return any(base + s3 in self.wh3 for s3 in self.SUFFIXES_WH3)
        return False

    def _feuillage_srgb(self, c, octets):
        """Couleurs des feuillages du modèle `c` (déjà relocalisées, donc livrées par nous) sous l'en-tête DX10 sRGB
        (`FEUILLAGE_SRGB`). Une couleur que nous ne livrons pas (fichier de CA) n'est pas touchée : notée à part."""
        import decalques_wh1 as D
        for t in couleurs_feuillage(octets):
            o = self.octets.get(t)
            if o is None:
                self.feuillages_srgb_hors = getattr(self, "feuillages_srgb_hors", set()) | {t}
                continue
            gains = REGLAGE_FEUILLAGES.get(t.rsplit("/", 1)[-1])
            if gains and t not in getattr(self, "feuillages_regles", set()) and bytes(o[84:88]) in (b"DXT1", b"DXT5"):
                # (25.09.2026) ton réglé (`REGLAGE_FEUILLAGES`), directement en BC7 sRGB
                self.octets[t] = self._regler_feuillage(o, gains)
                self.feuillages_regles = getattr(self, "feuillages_regles", set()) | {t}
                self.feuillages_srgb = getattr(self, "feuillages_srgb", set()) | {t}
            elif bytes(o[84:88]) in (b"DXT1", b"DXT5"):
                self.octets[t] = D.en_dx10_couleur(o)
                self.feuillages_srgb = getattr(self, "feuillages_srgb", set()) | {t}
            elif bytes(o[84:88]) != b"DX10":
                self.feuillages_srgb_autres = getattr(self, "feuillages_srgb_autres", set()) | {t}

    @staticmethod
    def _regler_feuillage(o, gains):
        """Feuillage DXT de WH1 `o`, couleur des texels opaques multipliée par `gains` (R, V, B), en BC7 sRGB."""
        import io
        import numpy as np
        from PIL import Image
        import bc7
        d = np.array(Image.open(io.BytesIO(bytes(o))).convert("RGBA")).astype(np.float64)
        opaque = d[..., 3] > 0
        d[..., :3] = np.where(opaque[..., None], d[..., :3] * np.array(gains, np.float64), d[..., :3])
        return bc7.dds_bc7(bc7.chaine(np.clip(np.round(d), 0, 255).astype(np.uint8)), srgb=True)

    def _decalque(self, c, brut, base1):
        """Modèle de décalque de WH1 : textures converties aux noms de WH3 (`decalques_wh1`), sous la base
        de WH1 si rien de WH3 n'y commence, sinon sous `_wh1/`, le modèle réécrit pour citer cette base."""
        textures = textures_wh3(self.wh1.lire, base1)
        if textures is None:
            self.introuvables.append(base1 + "_diffuse.dds")
            textures = {}
        occupe = c in self.wh3 or self._commence_dans_wh3(base1 + "_")
        base = deplace(base1) if occupe else base1
        f = deplace(c) if occupe else c
        for s, o in textures.items():
            chemin = base + s + ".dds"
            if chemin in self.wh3:
                raise ValueError(f"{chemin} existe dans WH3 : jamais remplacé")
            self.octets[chemin] = o
        (self.deplaces if occupe else self.propres).add(c)
        self.decalques.add(c)
        self.final[c] = f
        self.octets[f] = remplacer(c, brut, {base1: base}) if base != base1 else brut
        return f

    def _dimensions_ca(self, k):
        if k not in self._dims_ca:
            o = self.wh3.lire(k)
            self._dims_ca[k] = struct.unpack_from("<II", o, 12)[::-1] if o and o[:4] == b"DDS " else None
        return self._dims_ca[k]

    def _version_de_ca(self, c):
        """(chemin, (largeur, hauteur)) de la version de CA du même objet que la texture `c` (voir `TAILLES_DE_CA`), ou
        None (pas de version de CA, ou versions de CA de dimensions différentes : notée)."""
        if self._ca_par_nom is None:
            self._ca_par_nom = {}
            for k in self.wh3.ou:
                if k.startswith("rigidmodels/campaign/") and k.endswith(".dds"):
                    self._ca_par_nom.setdefault(k.rsplit("/", 1)[-1], []).append(k)
        dossier, nom = c.replace(f"/{PREFIXE}/", "/", 1).rsplit("/", 1)
        candidats = self._ca_par_nom.get(nom)
        if not candidats:
            m = CARTES_WH1_SEULEMENT.match(nom)
            candidats = self._ca_par_nom.get(m.group(1) + "_base_colour.dds") if m else None
        if not candidats:
            return None
        candidats = [k for k in candidats if k.rsplit("/", 1)[0] == dossier] or sorted(candidats)
        dims = {self._dimensions_ca(k) for k in candidats} - {None}
        if len(dims) != 1:
            self.tailles_de_ca_laissees[c] = f"versions de CA de dimensions différentes : {sorted(dims)}"
            return None
        return candidats[0], dims.pop()

    def _taille_de_ca(self, c, octets):
        """Texture `c` ramenée aux dimensions de la version de CA du même objet quand elle est plus grande
        (`TAILLES_DE_CA`) ; tout autre fichier, ou une réduction impossible (notée), passe tel quel."""
        if not TAILLES_DE_CA or not c.endswith(".dds") or not c.startswith("rigidmodels/") or octets[:4] != b"DDS ":
            return octets
        ca = self._version_de_ca(c)
        if ca is None:
            return octets
        chemin_ca, (lca, hca) = ca
        h, w = struct.unpack_from("<II", octets, 12)
        if w * h <= lca * hca:
            self.tailles_de_ca_laissees.pop(c, None)
            return octets
        facteur = w // lca
        if w != facteur * lca or h != facteur * hca or facteur & (facteur - 1):
            self.tailles_de_ca_laissees[c] = f"{w} x {h} -> CA {lca} x {hca} ({chemin_ca}) : pas une puissance de 2 commune"
            return octets
        try:
            reduit = reduire_mips(octets, facteur)
        except ValueError as e:
            self.tailles_de_ca_laissees[c] = f"{w} x {h} -> CA {lca} x {hca} : {e}"
            return octets
        self.tailles_de_ca_laissees.pop(c, None)
        self.tailles_de_ca[c] = (w, h, lca, hca, facteur.bit_length() - 1, len(octets) - len(reduit), chemin_ca)
        return reduit

    def cible(self, chemin):
        c = norme(chemin).lstrip("/")
        if c in self.final:
            return self.final[c]
        if c in self._en_cours:                     # référence circulaire : le chemin d'origine
            return c
        brut = self.wh1.lire(c)
        if brut is None and SUBSTITUTS_A_NOUS and c.startswith("rigidmodels/") and "/" + PREFIXE + "/" not in c:
            src = SOURCES_SUBSTITUTS.get(c.rsplit("/", 1)[-1])
            o = self.wh3.lire(src) if src else None
            if o is not None and self.wh3.lire(c) is None:
                f = deplace(c)
                self.octets[f] = o
                self.final[c] = f
                self.substitues = getattr(self, "substitues", set()) | {c}
                return f
        if brut is None:
            self.introuvables.append(c)
            self.final[c] = None
            return None
        base = base_citee(brut) if c.endswith(".rigid_model_v2") else None
        if base:
            return self._decalque(c, brut, base)
        if c.endswith(".wsmodel") and c in self.wh3 and self._shader_absent(brut):
            # objet refait par CA pour WH3 au même chemin (lave) : le sien, rien de WH1 à livrer
            self.par_ca = getattr(self, "par_ca", set()) | {c}
            self.final[c] = c
            return c
        self._en_cours.add(c)
        if c.endswith(".rigid_model_v2"):
            self._noter_cartes(brut)
        remplacements = {}
        for d in sorted(dependances(c, brut)):
            fd = self.cible(d)
            if fd and fd != d:
                remplacements[d] = fd
        self._en_cours.discard(c)
        octets = remplacer(c, brut, remplacements) if remplacements else brut
        if not c.endswith(".dds") and TERRAIN_CITE.search(brut):
            octets = self._sans_terrain(c, octets)
        octets = emission_wh3(c, feuillage_wh3(c, octets))
        if FEUILLAGE_SRGB and c.endswith(".rigid_model_v2"):
            self._feuillage_srgb(c, octets)
        if c.endswith(".xml.material"):
            octets = self._materiau_wh3(c, octets)
        if octets != brut:
            self.feuillages += int(feuillage_wh3(c, brut) != brut)
            self.emissions += int(emission_wh3(c, brut) != brut)
        if c.endswith(".dds") and c.startswith("terrain/"):
            f = hors_terrain(c)
            if f in self.wh3:
                raise ValueError(f"{f} existe dans WH3 : jamais remplacé")
            self.textures_terrain = getattr(self, "textures_terrain", set()) | {c}
            self.final[c] = f
            self.octets[f] = octets
            if self.PBR_WH1.search(c):
                self._pbr_glace(c, f)
            return f
        if self._jeu_detourne(c):
            f = deplace(c)
            if f in self.wh3:
                raise ValueError(f"{f} existe dans WH3 : jamais remplacé")
            self.deplaces.add(c)
            self.detournes = getattr(self, "detournes", set()) | {c}
            self.final[c] = f
            self.octets[f] = octets
            if self.PBR_WH1.search(c):
                self._pbr_glace(c, f)
            return f
        if c in self.wh3:
            if octets == brut and self.wh3.lire(c) == brut:
                self.identiques.add(c)
                self.final[c] = c
                return c
            f = deplace(c)
            self.deplaces.add(c)
        else:
            f = c
            self.propres.add(c)
        self.final[c] = f
        self.octets[f] = octets
        if self.PBR_WH1.search(c):
            self._pbr_glace(c, f)
        return f

    def bilan(self):
        tailles = sum(len(o) for o in self.octets.values()) / 1e6
        return (f"{len(self.final)} fichiers de WH1 examinés : {len(self.propres)} repris sous leur chemin, "
                f"{len(self.deplaces)} déplacés (différents de WH3), {len(self.identiques)} identiques à WH3, "
                f"{len(self.introuvables)} introuvables dans WH1 ; dont {len(self.decalques)} décalques (textures "
                f"converties aux noms de WH3), {self.feuillages} feuillages (couleur en type 27 ; "
                f"{len(getattr(self, 'feuillages_srgb', ()))} couleurs de feuillage en DX10 sRGB, "
                f"{len(getattr(self, 'feuillages_srgb_hors', ()))} non livrées par nous, "
                f"{len(getattr(self, 'feuillages_srgb_autres', ()))} d'un autre format), "
                f"{self.emissions} matériaux émissifs (échelle de WH3), "
                f"{len(getattr(self, 'par_ca', ()))} objets pris chez CA (shader de WH1 absent de WH3), "
                f"{getattr(self, 'convertis', 0)} matériaux convertis au shader de WH3, "
                f"{getattr(self, 'v2_de_ca', 0)} matériaux de WH1 portés sur la version de CA (emplacements v2) et "
                f"{getattr(self, 'v2_generiques', 0)} convertis sans version de CA, "
                f"{getattr(self, 'glaces', 0)} glaces de WH1 au rendu de WH3, "
                f"{getattr(self, 'pbr', 0)} autres jeux de WH1 au rendu de WH3 (recette de CA ; "
                f"{getattr(self, 'pbr_de_ca', 0)} laissés au _base_colour de CA, {getattr(self, 'pbr_ignores', 0)} illisibles, "
                f"{len(getattr(self, 'pbr_incomplets', ()))} sans spéculaire ni brillance dans WH1 ; "
                f"{getattr(self, 'metaux', 0)} métaux à la couleur de leur spéculaire) ; "
                f"{len(getattr(self, 'textures_terrain', ()))} textures de terrain citées par "
                f"{len(getattr(self, 'cites_terrain', ()))} objets, rangées sous {DOSSIER_TEXTURES_TERRAIN}/ ; "
                f"{len(self.tailles_de_ca)} textures ramenées aux dimensions de CA "
                f"(-{sum(v[5] for v in self.tailles_de_ca.values()) / 1e6:.1f} Mo), "
                f"{len(self.tailles_de_ca_laissees)} plus grandes que chez CA laissées ; "
                f"{len(self.octets)} à livrer, {tailles:.1f} Mo")


def ecrire(octets, racines):
    """Écrit {chemin : octets} sous chaque racine (dossier du projet, working_data du kit), en remplaçant."""
    for c, o in octets.items():
        for racine in racines:
            cible = os.path.join(racine, *c.split("/"))
            os.makedirs(os.path.dirname(cible), exist_ok=True)
            if os.path.exists(cible) and open(cible, "rb").read() == o:
                continue
            with open(cible, "wb") as f:
                f.write(o)


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    r = Relocateur()
    for a in sys.argv[1:]:
        print(a, "->", r.cible(a))
    print(r.bilan())
    for c in sorted(r.deplaces)[:20]:
        print("   déplacé :", c)
