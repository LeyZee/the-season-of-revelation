#!/usr/bin/env python3
"""
masques_eau_carte.py - fabrique le matériau d'eau de NOTRE carte (mer, rivières, lacs) et ses masques, comme CA en fait
un pour chacune des siennes. (Le choix du matériau cité par la chaîne reste dans `eau_carte.py`, module de la construction.)

Pourquoi (23.09.2026, 04 h 45 ; rivières et lacs invisibles en jeu depuis le début, question de la construction) :
- le matériau d'eau de CA est PROPRE À CHAQUE CARTE : wh3_main_combi_campaign_water_plane lit Sea/combi_A_mask.dds et
  Sea/combi_combined_flow_mask.dds, celui du prologue Sea/prologue_*, la carte du Chaos a chaos_a/b/c. Notre mer, nos
  rivières et nos lacs employaient celui des Empires, donc leurs masques projetés sur notre carte ;
- masque A, relevé sur celui des Empires : il couvre toute la carte, u = x / largeur du monde, v = z / profondeur du monde
  (espace des hex), ligne 0 au nord (92 % des 206 rivières de CA sur son bleu ; 17 % avec v inversé) ; ALPHA = la mer
  (36 % des pixels, dessin exact des mers des Empires) ; BLEU = le réseau des rivières (3,2 % des pixels) ; R et G =
  un bruit (le shader rigid_campaign_sea a des réglages propres aux rivières : caustics_intensity_rivers,
  normal_strength_rivers) ;
- masque de flux : propre à chaque carte (côtes et rivières des Empires) ; valeurs médianes de CA : terre (129, 128, 206,
  213), mer (170, 130, 173, 183) ; masques B et C : identiques entre Empires et prologue, génériques (cités, pas copiés).
Le rôle exact du bleu n'est pas prouvé (shader compilé) : c'est l'écart qui restait avec CA, le reste (sens des
triangles, format des sommets, profondeurs, drapeaux) étant aligné. L'essai en jeu tranche.

Données (définitions de la construction, 23.09.2026, 04 h 45 - 05 h ; grille du relief 3 524 x 3 200, ligne 0 au nord) :
- mer : `relief-wh1\\mer_finale.npy` (mer au pixel, écrite par terrain_wh1_vers_terry) ; à défaut, relief `height` du
  projet Terry à 0 (« height = surface de l'eau, 0, sur la mer » ; 99,97 % d'accord avec mer_maillages + rivage) ;
- rivières : `relief-wh1\\eau_rivieres.npy` (hauteur de notre eau réelle, NaN hors rivière) ; à défaut,
  rivieres_wh1_masque.Rivieres().masque(4) > 0,5 hors mer ; élargies d'un pixel du masque ;
- lacs : les plans d'eau `ECPolygonMesh` au matériau d'eau des calques du projet (26), élargis d'un pixel.

Sorties (arborescence du pack ; la construction les embarque et y fait pointer rivieres_wh1.MATERIAU_EAU,
props_wh1_vers_layers.MATERIAU_EAU et le water_plane_material du .terry) dans 04-projets\\saison-des-revelations\\eau-carte\\ :
    materials/environment/campaign_sea/wh_dlc05_wood_elves_campaign_water_plane.xml.material
    sea/wh_dlc05_wood_elves_a_mask.dds               (BC7, mips ; R, G : bruit de CA ; B : rivières et lacs ; A : mer)
    sea/wh_dlc05_wood_elves_combined_flow_mask.dds   (BC7, mips ; neutre, dérive de CA sur la mer)
Contrôle (hors pack) : 04-projets\\saison-des-revelations\\terrain-controle\\eau_carte_masque.png

Usage :
    python masques_eau_carte.py            # bilan à blanc
    python masques_eau_carte.py --apply    # écrit les fichiers (à relancer après une chaîne qui change la mer, les
                                           # rivières ou les lacs : relief-wh1/mer_finale.npy, eau_rivieres.npy)
"""

import argparse
import glob
import io
import os
import re
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bc7                                                           # noqa: E402

ATELIER = r"C:\TotalWar-CampaignMap"
DATA_WH3 = r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\data"
PROJET = (r"C:\Program Files (x86)\Steam\steamapps\common\Total War WARHAMMER III\assembly_kit\raw_data\terrain\campaigns"
          r"\wh_dlc05_wood_elves_map_1")
SORTIE = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "eau-carte")
CONTROLE = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "terrain-controle", "eau_carte_masque.png")
RELIEF = os.path.join(ATELIER, "04-projets", "saison-des-revelations", "relief-wh1")

LARGEUR, PROFONDEUR = 266.53, 338.9               # monde de la carte (espace des hex)
LARGEUR_IE, PROFONDEUR_IE = 961.3, 748.1          # monde des Empires (pour garder l'échelle de leur bruit)
# côté des masques : 2 048 comme le prologue de CA (carte plus petite que les Empires, 1 440) ; 7,7 px par unité, bords
# lissés (Charles, 23.09.2026, 04 h 55, sur l'image de contrôle en 1 024 seuillée : « trop pixelisé »)
N = 2048
SURECHANTILLON = 4                                # lacs tracés à 4 x N puis moyennés : bords anti-crénelés
FERMETURE_PX = 5                                  # coupures des rivières comblées jusqu'à ~1,3 unité (disque de 5 px)

MATERIAU_CA = "materials/environment/campaign_sea/wh3_main_combi_campaign_water_plane.xml.material"
MATERIAU = "materials/environment/campaign_sea/wh_dlc05_wood_elves_campaign_water_plane.xml.material"
MASQUE_A_CA = "sea/combi_a_mask.dds"
MASQUE_A = "sea/wh_dlc05_wood_elves_a_mask.dds"
FLUX_CA = "sea/combi_combined_flow_mask.dds"
FLUX = "sea/wh_dlc05_wood_elves_combined_flow_mask.dds"
FLUX_TERRE = (128, 128, 206, 213)                 # médianes de CA hors de l'eau, vecteur de flux nul
FLUX_MER = (170, 130, 173, 183)                   # médianes de CA sur la mer
# Convention du masque de flux, relevée sur celui des Empires (23.09.2026, 06 h 10 ; Charles : « l'eau n'a pas l'air de
# bouger ») : sens réel de leurs rivières (distance à la mer le long du lit du masque A) contre les canaux :
#   R - 128 = composante EST, G - 128 = composante NORD (ligne 0 de l'image au nord), vecteur vers l'AVAL :
#   cosinus moyen +0,72 sur 23 761 px de rivière (73 % au-dessus de 0,7) ; les 7 autres conventions essayées sont nulles
#   ou opposées ;
#   norme dans le lit : médiane 61 (sur 127) ; décroît à peu près linéairement hors du lit, nulle à ~7 px du masque de
#   2 048 des Empires, soit ~3 unités du monde ; terre loin de l'eau : 4,5 ;
#   mer : norme médiane 60, direction autour de l'est (médiane 2°, 80 % entre -63° et +63°) ;
#   B et A : deux bruits lisses indépendants (corrélation 0,86 à 1 px, 0,5 à 8 px, ~0 à 128 px ; B/A 0,07), sans lien
#   avec l'eau : bruit de phase, repris de CA à l'échelle du monde des Empires.
#   près de l'embouchure (10 derniers px, ~4 unités) la norme monte : médiane 73 (p90 98) contre 58 à 64 en amont, sans
#   autre variation avec la distance à la mer.
FLUX_RIV_NORME = 61
FLUX_EMBOUCHURE_NORME = 73
FLUX_EMBOUCHURE_UNITES = 4.0
FLUX_MER_NORME = 60
FLUX_MER_ECART = 40.0                             # degrés autour de l'est, modulés par le bruit B de CA
FLUX_FONDU_UNITES = 1.5                           # fondu de la norme hors du lit (CA ~3 unités pour des lits plus larges)
FLUX_RIVIERES = "flux_rivieres.npy"               # sens du courant de la construction (relief-wh1), voir flux_rivieres()
# 24.09.2026, 04 h 50 (Charles : « l'eau ne bouge pas » ; mesures de la session du rendu sur la chaîne 9) :
# - lacs : flux nul jusqu'ici (chez CA, aucun pixel d'eau intérieure n'a un flux nul ; sans flux, les normales ne
#   défilent pas) : norme FLUX_LAC_NORME, direction du courant qui les traverse (flux_rivieres.npy du rendu), sinon
#   dérive lente vers l'est modulée par le bruit de CA ;
# - embouchures : le flux de la rivière n'est plus coupé net par la mer ; là où flux_rivieres.npy prolonge le courant
#   dans la mer (panache, 3 à 4 u), il se fond dans le courant marin sur FLUX_PANACHE_UNITES depuis la côte ;
# - matériau : normal_strength_rivers de CA (0,3) porté à NORMALES_RIVIERES, à juger en jeu.
FLUX_LAC_NORME = 60                              # 35, puis 60 (05 h 30, session du rendu : on part d'un flux nul)
FLUX_PANACHE_UNITES = 4.0
# 25.09.2026 (rivières blanches ; enquête du rendu, scratchpad a0404878…\enquete_rivieres) : le shader règle l'écume
# d'après l'épaisseur d'eau vue rapportée à river_depth_max_point (0,8 aux Empires) ; nos rivières n'ont que 1 à 5 cm
# d'eau, comme dans WH1, d'où jusqu'à 50 % d'écume vue de loin. river_depth_max_point à 0,2 (valeur de CA sur les cartes
# du prologue et du Chaos) et normales des rivières ramenées à 0,3 (valeur de CA) : de 48 % à 12 % de l'eau très écumeuse
# (simulation du rendu). C4, la mer (Charles, 25.09.2026, 03 h : « je veux vraiment que ça rende comme dans Warhammer
# 1 ») : sea_depth_max_point 1,5 → 0,6 et foam_falloff 7 → 20 (variante simulée par le rendu, e07b_variante).
# 25.09.2026, 04 h 42 (essai A du rendu, validé par Charles pour la chaîne 16) : rivières sans mouvement visible, car
# l'écume des crêtes, les caustiques et l'écume de rive dépendent de l'épaisseur d'eau vue, que C1 et les normales à
# 0,3 avaient divisée par 4 à 20. Normales des rivières 0,3 → 0,6 et écume des rivières (whitewater_strength_rivers de
# CA, 0,35) → 0,2.
NORMALES_RIVIERES = "0.6"
PARAMETRES_EAU = {"river_depth_max_point": "0.2", "sea_depth_max_point": "0.6", "foam_falloff": "20",
                  "whitewater_strength_rivers": "0.2"}
# 25.09.2026 (enquête eau du rendu, transmise par la construction) : les lacs partagent le matériau des rivières ; avec
# river_depth_max_point 0,2, leurs 0,2 à 0,3 u d'eau passent en eau profonde (turquoise uniforme). Matériau de lac À NOUS,
# copie du nôtre avec river_depth_max_point 0,8 (valeur des Empires ; CA sépare aussi ses lacs, cwb_cmapaign_lake). Inerte
# tant que le rendu ne le câble pas dans etangs_wh1.entite ; à juger par Charles, un changement par essai.
MATERIAU_LAC = "materials/environment/campaign_sea/wh_dlc05_wood_elves_campaign_lake_plane.xml.material"
PARAMETRES_LAC = dict(PARAMETRES_EAU, river_depth_max_point="0.8")
# 24.09.2026, 05 h 30 (session du rendu, shader rigid_campaign_sea désassemblé, scratchpad\agent_eau\rapport.md) : le
# shader lit tous les masques à uv = (x / W, 1 - z / D), W et D = bornes du monde, et fait défiler les normales par
# uv x wave_tiling + flux x wave_flow_power x temps. Les répétitions se comptent donc sur la LARGEUR DE LA CARTE : sur
# nos 266,53 u (Empires : 961,3), les réglages de CA donnent des rides 3,6 fois plus petites (0,063 u contre 0,23),
# effacées par les mipmaps. Les 7 paramètres de répétition sont ramenés à l'échelle de notre carte (vitesses et
# puissances inchangées).
LARGEUR_IE = 961.3
REPETITIONS = ("wave_tiling_near", "wave_tiling_far", "foam_tiling", "caustics_scale", "flow_distortion_tiling",
               "shore_wave_distortion_tiling", "shore_wave_sparsity_tiling")


def raster(motif):
    chemins = glob.glob(os.path.join(PROJET, f"wh_dlc05_wood_elves_map_1.{motif}.*.tif"))
    if len(chemins) != 1:
        raise SystemExit(f"raster {motif} : {len(chemins)} fichier(s) dans {PROJET}")
    Image.MAX_IMAGE_PIXELS = None
    return np.array(Image.open(chemins[0]), dtype=np.float32)


def reduire(champ, n):
    """Champ (H, L) de 0 à 1 (ou booléen) -> (n, n) : moyenne par boîte (lignes et colonnes proportionnelles)."""
    octets = np.clip(np.round(np.asarray(champ, dtype=np.float64) * 255), 0, 255).astype(np.uint8)
    return np.array(Image.fromarray(octets).resize((n, n), Image.BOX), dtype=np.float64) / 255


def _disque(a, r, op):
    """Maximum (ou minimum) sur un disque de rayon r (bords répétés)."""
    p = np.pad(a, r, mode="edge")
    h, l = a.shape
    out = a.copy()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dy * dy + dx * dx <= r * r:
                out = op(out, p[r + dy:r + dy + h, r + dx:r + dx + l])
    return out


def fermer(champ, r):
    """Fermeture en niveaux de gris par un disque (dilatation puis érosion) : comble les coupures de moins de 2r pixels
    sans épaissir le reste ni créer de marches (un carré en créait). Les rubans de WH1 s'estompent au bord de chaque
    tuile : au seuil 0,5, le réseau est coupé en 1 536 morceaux, écart médian 0,3 unité, 90 % sous 1 unité (relevé du
    23.09.2026, 05 h)."""
    return _disque(_disque(champ, r, np.maximum), r, np.minimum)


def adoucir(champ, rayon):
    """Flou gaussien d'un champ de 0 à 1 (rayon en pixels)."""
    octets = np.clip(np.round(np.asarray(champ, dtype=np.float64) * 255), 0, 255).astype(np.uint8)
    return np.array(Image.fromarray(octets).filter(ImageFilter.GaussianBlur(rayon)), dtype=np.float64) / 255


MARQUE_MER = "<!-- mer_wh1 -->"                   # calque du plan de mer (terrain_wh1_vers_terry.MER_PLANS, chaîne 5)


def lacs(mer=False):
    """Polygones monde [(x, z), ...] des plans d'eau au matériau d'eau des calques du projet : les lacs (défaut), ou,
    avec mer=True, le plan de la mer (calque marqué MARQUE_MER en tête : la mer de WH1 élargie de 0,6 u sous la côte,
    posé par la session du rendu le 23.09.2026, 21 h 20 ; ce n'est pas un lac)."""
    out = []
    for f in glob.glob(os.path.join(PROJET, "*.layer")):
        s = open(f, encoding="utf-8", errors="replace").read()
        if "campaign_sea" not in s or (MARQUE_MER in s[:200]) != mer:
            continue
        for m in re.finditer(r'<entity id="[^"]*">(.*?)</entity>', s, re.S):
            b = m.group(1)
            if not re.search(r'<ECPolygonMesh material="[^"]*campaign_sea', b):
                continue
            p = re.search(r'<ECTransform position="([^ ]+) ([^ ]+) ([^ "]+)" rotation="[^ ]+ ([^ ]+) ', b)
            x, z, rot = float(p.group(1)), float(p.group(3)), np.radians(float(p.group(4)))
            pts = [(float(a), float(c)) for a, c in re.findall(r'<point x="([^"]+)" y="([^"]+)"/>', b)]
            out.append([(x + a * np.cos(rot) + c * np.sin(rot), z - a * np.sin(rot) + c * np.cos(rot)) for a, c in pts])
    return out


def vers_masque(x, z):
    return x / LARGEUR * N, (1 - z / PROFONDEUR) * N


def bruit_ca():
    """R et G du masque A des Empires, à l'échelle du monde des Empires : une fenêtre de notre taille (en unités),
    prise au centre de leur carte, étirée à N x N."""
    from contenu_pack import SourcePacks
    b = SourcePacks(DATA_WH3).lire(MASQUE_A_CA)
    if b is None:
        raise SystemExit(f"{MASQUE_A_CA} introuvable dans les packs du jeu")
    a = np.array(Image.open(io.BytesIO(b)).convert("RGBA"))
    h, w = a.shape[:2]
    fw, fh = int(round(LARGEUR / LARGEUR_IE * w)), int(round(PROFONDEUR / PROFONDEUR_IE * h))
    x0, y0 = (w - fw) // 2, (h - fh) // 2
    return tuple(np.array(Image.fromarray(np.ascontiguousarray(a[y0:y0 + fh, x0:x0 + fw, k])).resize((N, N), Image.BILINEAR))
                 for k in (0, 1))


def bruit_flux_ca():
    """B et A du masque de flux des Empires (bruits de phase), même fenêtre et même échelle que bruit_ca()."""
    from contenu_pack import SourcePacks
    b = SourcePacks(DATA_WH3).lire(FLUX_CA)
    if b is None:
        raise SystemExit(f"{FLUX_CA} introuvable dans les packs du jeu")
    a = np.array(Image.open(io.BytesIO(b)).convert("RGBA"))
    h, w = a.shape[:2]
    fw, fh = int(round(LARGEUR / LARGEUR_IE * w)), int(round(PROFONDEUR / PROFONDEUR_IE * h))
    x0, y0 = (w - fw) // 2, (h - fh) // 2
    return tuple(np.array(Image.fromarray(np.ascontiguousarray(a[y0:y0 + fh, x0:x0 + fw, k])).resize((N, N), Image.BILINEAR))
                 for k in (2, 3))


def _reduire_f(champ, n):
    """Champ flottant (H, L) -> (n, n) par moyenne de boîte."""
    return np.array(Image.fromarray(np.ascontiguousarray(champ, dtype=np.float32), mode="F").resize((n, n), Image.BOX),
                    dtype=np.float64)


def vers_est_nord(dx, dz):
    """Vecteur de la grille du relief (dx vers l'est, dz vers le SUD : ligne 0 au nord ; pixels carrés) -> direction
    unitaire du monde (est, nord). Le monde est l'espace des hex : Terry étire les rasters de 2/√3 en z (GUIDE n° 98)."""
    e, n = dx, -dz * 2 / np.sqrt(3)
    norme = np.hypot(e, n)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(norme > 0, e / norme, 0.0), np.where(norme > 0, n / norme, 0.0)


def pres_de_la_mer(mer, rayon_px):
    """Proximité de la mer de 1 (sur la mer) à 0 (à rayon_px pixels et au-delà), par dilatations successives."""
    prox = mer.astype(np.float64)
    cur = mer.copy()
    for k in range(1, rayon_px + 1):
        nxt = cur.copy()
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            nxt |= np.roll(np.roll(cur, dy, 0), dx, 1)
        prox[nxt & ~cur] = 1 - k / (rayon_px + 1)
        cur = nxt
    return prox


def champ_flux(est, nord, couverture, fondu_px, proximite_mer=None):
    """(R, G) des rivières : direction (est, nord) de norme FLUX_RIV_NORME là où l'eau couvre le pixel (FLUX_EMBOUCHURE_NORME
    à l'embouchure, selon proximite_mer), prolongée hors du lit sur fondu_px pixels avec une norme décroissante (moyenne
    des directions voisines déjà posées), comme CA."""
    pose = couverture > 0.05
    e = np.where(pose, est, 0.0)
    n = np.where(pose, nord, 0.0)
    base = FLUX_RIV_NORME if proximite_mer is None else \
        FLUX_RIV_NORME + (FLUX_EMBOUCHURE_NORME - FLUX_RIV_NORME) * proximite_mer
    norme = np.where(pose, base * np.clip(couverture / 0.5, 0, 1), 0.0)
    for k in range(1, fondu_px + 1):
        se = np.zeros_like(e); sn = np.zeros_like(n); cpt = np.zeros_like(e)
        for dy, dx in ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            p = np.roll(np.roll(pose, dy, 0), dx, 1)
            se += np.where(p, np.roll(np.roll(e, dy, 0), dx, 1), 0)
            sn += np.where(p, np.roll(np.roll(n, dy, 0), dx, 1), 0)
            cpt += p
        neuf = ~pose & (cpt > 0)
        l = np.hypot(se, sn)
        ok = neuf & (l > 1e-6)
        e = np.where(ok, se / np.where(ok, l, 1), e)
        n = np.where(ok, sn / np.where(ok, l, 1), n)
        norme = np.where(ok, FLUX_RIV_NORME * (1 - k / (fondu_px + 1)), norme)
        pose = pose | ok
    return 128 + e * norme, 128 + n * norme, pose


def flux_rivieres(H, L):
    """Sens du courant de la construction (rivieres_wh1.flux_reseau, 23.09.2026, 06 h 12) : relief-wh1/flux_rivieres.npy,
    float32 (H, L, 2) sur la grille du relief (ligne 0 au nord), [..., 0] = composante vers l'EST, [..., 1] = composante
    vers le NORD (positive au nord, pas vers le bas des lignes), vecteur unitaire, NaN hors de l'eau des rivières.
    Rend (est, nord, couverture) à N x N dans le repère du monde, ou None s'il manque."""
    chemin = os.path.join(RELIEF, FLUX_RIVIERES)
    if not os.path.exists(chemin):
        return None
    f = np.load(chemin)
    if f.shape != (H, L, 2):
        raise SystemExit(f"{FLUX_RIVIERES} : forme {f.shape}, attendu {(H, L, 2)}")
    valide = np.isfinite(f).all(axis=2)
    # vers_est_nord attend dz vers le SUD : nord = -dz
    e, n = vers_est_nord(np.where(valide, f[..., 0], 0), np.where(valide, -f[..., 1], 0))
    couv = _reduire_f(valide.astype(np.float32), N)
    se, sn = _reduire_f(np.where(valide, e, 0), N), _reduire_f(np.where(valide, n, 0), N)
    l = np.hypot(se, sn)
    with np.errstate(invalid="ignore", divide="ignore"):
        return np.where(l > 0, se / l, 0.0), np.where(l > 0, sn / l, 0.0), couv


def materiau(parametres=None, nom_interne="wh_dlc05_wood_elves_campaign_water_plane.xml"):
    """Le matériau d'eau de CA pour notre carte ; `parametres` remplace PARAMETRES_EAU (matériau de lac)."""
    from contenu_pack import SourcePacks
    parametres = PARAMETRES_EAU if parametres is None else parametres
    b = SourcePacks(DATA_WH3).lire(MATERIAU_CA)
    if b is None:
        raise SystemExit(f"{MATERIAU_CA} introuvable dans les packs du jeu")
    t = b.decode("utf-8")
    remplacements = [
        ("<name>wh3_main_combi_campaign_water_plane.xml</name>", f"<name>{nom_interne}</name>"),
        ("<source>Sea/combi_A_mask.dds</source>", "<source>Sea/wh_dlc05_wood_elves_a_mask.dds</source>"),
        ("<source>Sea/combi_combined_flow_mask.dds</source>",
         "<source>Sea/wh_dlc05_wood_elves_combined_flow_mask.dds</source>"),
    ]
    for de, vers in remplacements:
        if t.count(de) != 1:
            raise SystemExit(f"matériau de CA : « {de} » trouvé {t.count(de)} fois (attendu 1)")
        t = t.replace(de, vers)
    motif = re.compile(r"(<name>normal_strength_rivers</name>\s*<type>float</type>\s*<value>)([^<]*)(</value>)")
    if len(motif.findall(t)) != 1:
        raise SystemExit("matériau de CA : normal_strength_rivers introuvable ou en double")
    t = motif.sub(lambda m: m.group(1) + NORMALES_RIVIERES + m.group(3), t)
    for nom, valeur in parametres.items():
        motif = re.compile(rf"(<name>{nom}</name>\s*<type>float</type>\s*<value>)([^<]*)(</value>)")
        if len(motif.findall(t)) != 1:
            raise SystemExit(f"matériau de CA : {nom} introuvable ou en double")
        t = motif.sub(lambda m, v=valeur: m.group(1) + v + m.group(3), t)
    echelle = LARGEUR / LARGEUR_IE
    for nom in REPETITIONS:
        motif = re.compile(rf"(<name>{nom}</name>\s*<type>float</type>\s*<value>)([^<]*)(</value>)")
        if len(motif.findall(t)) != 1:
            raise SystemExit(f"matériau de CA : {nom} introuvable ou en double")
        t = motif.sub(lambda m: m.group(1) + f"{float(m.group(2)) * echelle:.2f}" + m.group(3), t)
    return t.encode("utf-8")


def donnees():
    """(mer, rivières, sources) sur la grille du relief (ligne 0 au nord) : les tableaux finaux de la chaîne s'ils
    existent (relief-wh1), sinon le relief du projet Terry et le réseau de WH1."""
    hauteur = raster("height")
    H, L = hauteur.shape
    sources = []
    chemin = os.path.join(RELIEF, "mer_finale.npy")
    if os.path.exists(chemin):
        m = np.load(chemin)
        mer_px = m if m.dtype == bool else np.isfinite(m)
        sources.append("mer : mer_finale.npy")
    else:
        mer_px = hauteur == 0
        sources.append("mer : height = 0 (mer_finale.npy absent)")
    chemin = os.path.join(RELIEF, "eau_rivieres.npy")
    if os.path.exists(chemin):
        # eau au pixel (12 px par unité) : bords adoucis d'un pixel et demi avant réduction, sans marches d'escalier
        riv = adoucir(np.isfinite(np.load(chemin)), 1.5)
        sources.append("rivières : eau_rivieres.npy")
    else:
        # le ruban de WH1 lui-même (blend0 des tuiles), déjà dégradé de 0 à 1 sur ses bords : pris tel quel, sans seuil
        import rivieres_wh1_masque as RM
        riv = np.clip(RM.Rivieres().masque(4)[:H, :L].astype(np.float64), 0, 1)
        sources.append("rivières : réseau de WH1 (eau_rivieres.npy absent)")
    if mer_px.shape != (H, L) or riv.shape != (H, L):
        raise SystemExit(f"grilles différentes : relief {(H, L)}, mer {mer_px.shape}, rivières {riv.shape}")
    return mer_px, np.where(mer_px, 0.0, riv), sources


def tracer(polys):
    """Polygones monde -> champ (N, N) de 0 à 1, tracés à SURECHANTILLON x N puis moyennés (bords anti-crénelés)."""
    grand = Image.new("L", (N * SURECHANTILLON, N * SURECHANTILLON), 0)
    d = ImageDraw.Draw(grand)
    for poly in polys:
        d.polygon([tuple(c * SURECHANTILLON for c in vers_masque(x, z)) for x, z in poly], fill=255)
    return np.array(grand.resize((N, N), Image.BOX), dtype=np.float64) / 255


def construire():
    mer_px, riv, sources = donnees()
    # mer : au pixel, plus l'emprise du plan de mer (sa marge de 0,6 u sous la côte montre de l'eau là où le fond est
    # sous 0 : elle doit avoir le style de la mer, pas celui des rivières ; sur la terre émergée, le relief la cache)
    plans_mer = lacs(mer=True)
    mer_n = reduire(mer_px, N)
    if plans_mer:
        mer_n = np.maximum(mer_n, tracer(plans_mer))
        sources.append(f"plan de mer : {len(plans_mer)} polygone(s)")
    alpha = np.round(adoucir(mer_n, 1.0) * 255).astype(np.uint8)
    # rivières : moyenne par boîte (7,7 px par unité), léger flou, puis courbe en S (de 0,08 à 0,35) : le cœur des
    # ruisseaux faibles de WH1 sature, les bords restent dégradés ; aucun seuil ni filtre de maximum, qui donnaient des
    # marches d'escalier
    def en_s(x, a, b_):
        t = np.clip((x - a) / (b_ - a), 0, 1)
        return t * t * (3 - 2 * t)
    # coupures aux jonctions des tuiles de WH1 comblées par une fermeture en disque, puis bords adoucis
    b = en_s(adoucir(fermer(reduire(riv, N), FERMETURE_PX), 0.8), 0.08, 0.35)
    # lacs (sans le plan de mer)
    polys = lacs()
    lacs_n = tracer(polys)
    b = np.maximum(b, lacs_n)
    b = b * (1 - alpha / 255)                      # la mer n'est pas une rivière (CA : 8,7 % de recouvrement)
    bleu = np.round(b * 255).astype(np.uint8)
    r, g = bruit_ca()
    masque_a = np.dstack([r, g, bleu, alpha]).astype(np.uint8)

    # flux (convention de CA, voir FLUX_RIV_NORME) : B et A = bruits de phase de CA ; mer : courant vers l'est, direction
    # modulée par le bruit B ; rivières : sens du courant de la construction (flux_rivieres.npy), sinon vecteur nul
    fb, fa = bruit_flux_ca()
    zb = (fb - fb.mean()) / max(fb.std(), 1e-6)
    theta = np.radians(FLUX_MER_ECART) * np.clip(zb, -1.5, 1.5)
    poids_mer = alpha / 255.0
    rr = 128 + FLUX_MER_NORME * np.cos(theta) * poids_mer
    gg = 128 + FLUX_MER_NORME * np.sin(theta) * poids_mer
    H, L = riv.shape
    fr = flux_rivieres(H, L)
    px_flux = px_panache = 0
    mer_bin = alpha > 127
    if fr is not None:
        est, nord, couv = fr
        fondu = max(1, int(round(FLUX_FONDU_UNITES * N / LARGEUR)))
        prox = pres_de_la_mer(mer_bin, max(1, int(round(FLUX_EMBOUCHURE_UNITES * N / LARGEUR))))
        # panache : dans la mer, le courant de la rivière (s'il y est prolongé) pèse de 1 à la côte à 0 à
        # FLUX_PANACHE_UNITES au large ; sur terre, poids 1 (plus de coupure par la mer)
        pres_cote = pres_de_la_mer(~mer_bin, max(1, int(round(FLUX_PANACHE_UNITES * N / LARGEUR))))
        poids_riv = np.where(mer_bin, pres_cote, 1.0)
        r_riv, g_riv, pose = champ_flux(est, nord, couv * poids_riv, fondu, prox)
        w = np.where(mer_bin, np.clip(couv / 0.5, 0, 1) * pres_cote, 1.0)
        rr = np.where(pose, rr * (1 - w) + r_riv * w, rr)
        gg = np.where(pose, gg * (1 - w) + g_riv * w, gg)
        px_flux = int((couv > 0.05).sum())
        px_panache = int((pose & mer_bin & (w > 0.05)).sum())
        sources.append(f"flux : {FLUX_RIVIERES} ({px_flux} px d'eau orientée, fondu {fondu} px, panaches {px_panache} px)")
    else:
        sources.append(f"flux : {FLUX_RIVIERES} absent, rivières sans courant")
    # lacs : norme FLUX_LAC_NORME ; direction du courant déjà posé (rivière qui les traverse), sinon dérive vers l'est
    lac = (lacs_n > 0.05) & ~mer_bin
    ve, vn = rr - 128, gg - 128
    l = np.hypot(ve, vn)
    oriente = lac & (l > 1)
    de = np.where(oriente, ve / np.where(oriente, l, 1), np.cos(theta))
    dn = np.where(oriente, vn / np.where(oriente, l, 1), np.sin(theta))
    k = FLUX_LAC_NORME * np.clip(lacs_n / 0.5, 0, 1)
    rr = np.where(lac, 128 + de * k, rr)
    gg = np.where(lac, 128 + dn * k, gg)
    sources.append(f"flux des lacs : {int(lac.sum())} px (norme {FLUX_LAC_NORME}, {int(oriente.sum())} px orientés "
                   f"par une rivière)")
    flux = np.dstack([np.clip(np.round(rr), 0, 255), np.clip(np.round(gg), 0, 255), fb, fa]).astype(np.uint8)
    return masque_a, flux, {"mer": float((alpha > 127).mean()), "rivieres_lacs": float((bleu > 127).mean()),
                           "lacs": len(polys), "px_rivieres_raster": int((riv > 0.5).sum()), "sources": sources,
                           "px_flux": px_flux}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    masque_a, flux, bilan = construire()
    print(f"masque A {N} x {N} : mer {bilan['mer'] * 100:.2f} % ; rivières et lacs {bilan['rivieres_lacs'] * 100:.2f} % "
          f"({bilan['px_rivieres_raster']} px de rivière au relief, {bilan['lacs']} lacs) ; " + " ; ".join(bilan["sources"]))
    for nom, img in (("masque A", masque_a), ("flux", flux)):
        print(f"  contrôle BC7 {nom} : PSNR {bc7.controle(img):.1f} dB")
    apercu = np.zeros((N, N, 3), np.uint8)
    apercu[..., 0] = masque_a[..., 3] // 2
    apercu[..., 1] = masque_a[..., 2]
    apercu[..., 2] = np.maximum(masque_a[..., 3], masque_a[..., 2])
    if not a.apply:
        print("à blanc : rien d'écrit (--apply)")
        return 0
    fichiers = {
        MATERIAU: materiau(),
        MATERIAU_LAC: materiau(PARAMETRES_LAC, "wh_dlc05_wood_elves_campaign_lake_plane.xml"),
        MASQUE_A: bc7.dds_bc7(bc7.chaine(masque_a), srgb=False),
        FLUX: bc7.dds_bc7(bc7.chaine(flux), srgb=False),
    }
    for chemin, octets in fichiers.items():
        dest = os.path.join(SORTIE, *chemin.split("/"))
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with open(dest, "wb") as f:
            f.write(octets)
        print(f"  écrit {dest} ({len(octets) / 1e6:.2f} Mo)")
    os.makedirs(os.path.dirname(CONTROLE), exist_ok=True)
    Image.fromarray(apercu).resize((N // 2, N // 2), Image.LANCZOS).save(CONTROLE)
    # détail à pleine résolution (un quart de la carte, au centre-est : Athel Loren) pour juger les bords
    x0, y0 = N // 2, N // 3
    Image.fromarray(apercu[y0:y0 + N // 4, x0:x0 + N // 4]).resize((N // 2, N // 2), Image.LANCZOS).save(
        CONTROLE.replace(".png", "_detail.png"))
    print(f"  contrôle : {CONTROLE} et _detail (violet = mer, cyan = rivières et lacs)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
