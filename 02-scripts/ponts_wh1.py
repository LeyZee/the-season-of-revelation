#!/usr/bin/env python3
"""
ponts_wh1.py - les ponts de WH1 aux croisements des routes et des rivières : les objets des tuiles `river_crossing`.

Pourquoi (23.09.2026, session du rendu ; Charles : « des rivières vraiment fluides, avec les ponts qui les traversent » ;
relevé des Empires, `05-journal\\2026-09-23-essais-auto\\releve-visuel-ie.md` § 2 : 41 contacts route / rivière, aucun
pont). Établi le 23.09.2026 (recherche de la session du rendu, rapport repris dans le journal) : les 20 tuiles
`river_crossing` de WH1 (9 modèles) citent chacune, dans leur `bmd_data.bin`, un lot de 10 objets : une passerelle de
planches sur trois paires de pieux (`rigidmodels/campaign/resources/jetty`, 0,69 x 0,33 unité, en travers de la rivière
le long de la route, tablier 0,056 unité au-dessus du sol de la tuile), deux garde-corps (`fence_1`, `fence_2`), trois
roseaux (`marsh_reeds_01`) et quatre rochers (`mtn_rocks_01` à `_03`). Le maillage de la tuile n'a que son sol et son
ruban d'eau (ce que `rivieres_wh1` reprend) ; ces objets ne sont pas dans `global_props.bin` (le moteur de WH1 les posait
depuis la tuile, pour aucune de ses cartes ils n'y sont compilés) : notre chaîne les avait perdus. Les 20 ponts sont à
moins d'une unité de 40 de nos 41 contacts route / rivière ; le dernier, (206,6 ; 161,3), n'a pas de croisement de WH1.

Format des objets de tuile (enregistrements version 11 du FASTBIN0 v21 de la tuile, établi sur les octets) :
    u16 11 | u16 n + chemin du modèle | 12 f32 : matrice 3 x 3 (lignes = axes X, Y, Z du modèle, échelle comprise), puis
    position x, y, z | 30 octets de drapeaux | u16 n + mode de hauteur (« BHM_TERRAIN ») | u32 0xFFFFFFFF
Unités : celles du ruban d'eau (quart de l'unité du maillage de la tuile) ; pose de la tuile par `rivieres_wh1.vers_raster`
(quarts de tour, miroir 0x04), monde des entités à z x 2/√3 (erreur 89). Une pose en miroir (7 sur 20) est rendue par la
rotation propre la plus proche (axe z du modèle retourné : passerelle et garde-corps sont symétriques).

Hauteur (`BHM_TERRAIN` : relative au sol de la tuile, relief de base de WH1 + BASE) : chez nous, la passerelle et ses
garde-corps prennent pour sol de référence la plus haute de nos deux berges (aux bouts du tablier), et le tablier n'est
jamais à moins de GARDE_EAU au-dessus de notre eau ; roseaux et rochers se posent sur notre sol.

Athel Loren et Bretonnie (Charles, 23.09.2026, 17 h 30 : « dans Athel Loren, que ce soit vraiment respectable par rapport
aux elfes sylvains : reprends les ponts qui étaient dans WH1 exactement, avec leur même texture ; pour les autres ponts,
en dehors d'Athel Loren, tu peux les mettre en pierre ; s'il doit y avoir un pont, il faut que ce soit bien intégré »).
Le plan des traversées est fait par `ajouts_carte_wh3.plan_ponts` : en Athel Loren (les 13 royaumes elfes de la carte,
`ATHEL_LOREN`), le lot de WH1 tel quel (modèles et textures de WH1), ou, à une traversée sans croisement de WH1, le lot du
pont de WH1 le plus proche tourné dans l'axe de la route (`nouveaux`) ; ailleurs, le pont de pierre de CA remplace
passerelle et garde-corps (`remplacees`), les roseaux et rochers de WH1 hors de son emprise restent.

Usage :
    python ponts_wh1.py          # bilan à blanc (objets, poses, modèles)
"""

import math
import os
import re
import struct
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ACTIF = True
UNITE_BMD = 4.0                         # unités des objets de tuile -> unités du maillage de la tuile
MOTIF = re.compile(rb"\x0b\x00(.)(.)((?:rigidmodels|RigidModels|terrain)/[\x20-\x7e]+?\.(?:wsmodel|rigid_model_v2))", re.S)
PASSERELLE = "rigidmodels/campaign/resources/jetty.rigid_model_v2"
GARDE_CORPS = ("rigidmodels/campaign/resources/fence_1.rigid_model_v2", "rigidmodels/campaign/resources/fence_2.rigid_model_v2")
TABLIER_Y = 0.975                       # hauteur du tablier dans le modèle de la passerelle (aire horizontale maximale)
TABLIER_SUR_SOL = 0.056                 # dans WH1 : le tablier au-dessus du sol de la tuile
GARDE_EAU = 0.06                        # chez nous : le tablier au moins à tant au-dessus de l'eau
DEMI_LONGUEUR = 1.29                    # demi-longueur du tablier dans le modèle (boîte x -1,25 .. 1,33)
# les royaumes d'Athel Loren (provinces elfes de la carte, clés sans `wh_dlc05_`) : les ponts de WH1 y restent
ATHEL_LOREN = ("anmyr", "argwylon", "arranoc", "atylwyth", "cavaroc", "cythral", "fyr_darric", "modryn", "oak_of_ages",
               "talsyn", "tirsyth", "torgovann", "wydrioth")
EMPRISE_PIERRE = (1.15, 0.6)            # demi-longueur, demi-largeur (u) du pont de pierre : les objets de WH1 dedans partent
# intégration (Charles : « s'il doit y avoir un pont, il faut que ça rentre bien ») : chaque bout du tablier à MARGE_BERGE
# au moins de l'eau visible. Notre eau est plus large que dans WH1 à 5 traversées d'Athel Loren sur 8 (la passerelle y
# finissait dans l'eau) : la passerelle de WH1 y est alignée sur la traversée (de la route d'une rive à celle de l'autre)
# et, s'il le faut, allongée avec ses garde-corps (mêmes modèles, mêmes textures) ; là où elle enjambait déjà l'eau, elle
# reste exactement à sa place de WH1.
MARGE_BERGE = 0.1                       # bouts à 10 cm de l'eau quand on recale
MARGE_GARDER = 0.06                     # une passerelle dont les bouts sont à 6 cm au moins de l'eau reste à sa place de WH1
ETIREMENT_MAX = 2.0


def lire_objets(b):
    """Objets d'un `bmd_data.bin` de tuile de WH1 : dicts (modele, matrice (9), position (3), hauteur)."""
    out = []
    for m in MOTIF.finditer(b):
        n = m.group(1)[0] | (m.group(2)[0] << 8)
        chemin = m.group(3)
        if n != len(chemin):
            continue
        o = m.end()
        f = struct.unpack_from("<12f", b, o)
        o += 48 + 30
        k = struct.unpack_from("<H", b, o)[0]
        mode = b[o + 2:o + 2 + k]
        if not mode.startswith(b"BHM_"):
            continue
        out.append(dict(modele=chemin.decode("ascii").lower(), matrice=f[:9], position=f[9:12], hauteur=mode.decode("ascii")))
    return out


def objets_ponts():
    """[dict] des objets des tuiles `river_crossing` de WH1, dans notre monde : modele, pose (k), matrice (lignes = axes du
    modèle dans le monde des entités, échelle comprise, rotation propre), x, z (monde), y_rel (au sol de la tuile),
    miroir, role (« passerelle », « garde-corps », « berge »)."""
    import montagnes_wh1 as M
    import rivieres_wh1 as RW
    from modeles_wh1 import SourceWH1
    wh1 = SourceWH1()
    out = []
    for p in RW.poses():
        if p.famille != "river_crossing":
            continue
        b = wh1.lire(p.nom + "bmd_data.bin")
        if b is None:
            raise SystemExit(f"{p.nom}bmd_data.bin absent des packs de WH1")
        for o in lire_objets(b):
            m = np.array(o["matrice"], np.float64).reshape(3, 3)
            px_, py_, pz_ = o["position"]

            def vers(x_, z_):
                X, Z = RW.vers_raster(p, np.array([x_ * UNITE_BMD]), np.array([z_ * UNITE_BMD]))
                return float(X[0]), float(Z[0])
            cx, cz = vers(px_, pz_)
            lignes = []
            for i in range(3):
                ax, az = vers(px_ + m[i, 0], pz_ + m[i, 2])
                lignes.append([ax - cx, m[i, 1] * UNITE_BMD * M.S, (az - cz) * M.Z_VERS_MONDE])
            lignes = np.array(lignes)
            miroir = bool(np.linalg.det(lignes) < 0)
            if miroir:
                lignes[2] = -lignes[2]
            role = ("passerelle" if o["modele"] == PASSERELLE else "garde-corps" if o["modele"] in GARDE_CORPS
                    else "berge")
            out.append(dict(modele=o["modele"], pose=p.k, tuile=p.nom, matrice=lignes.ravel().tolist(), x=cx,
                            z=cz * M.Z_VERS_MONDE, y_rel=float(py_ * UNITE_BMD * M.S), miroir=miroir, role=role,
                            hauteur=o["hauteur"]))
    return out


def modeles():
    """Chemins de WH1 des modèles des ponts (pour `modeles_wh1.rassembler_tout`)."""
    return sorted({o["modele"] for o in objets_ponts()})


def passerelle(lot):
    pas_ = [o for o in lot if o["role"] == "passerelle"]
    if len(pas_) != 1:
        raise SystemExit(f"pose {lot[0]['pose']} : {len(pas_)} passerelles")
    return pas_[0]


def tourner(lot, x, z, angle):
    """Le lot d'un pont de WH1 déplacé en (x, z), tourné pour que la passerelle suive la direction `angle` (degrés,
    atan2(dz, dx) du monde) ; la plus petite rotation (la passerelle est symétrique)."""
    j = passerelle(lot)
    m = np.array(j["matrice"]).reshape(3, 3)
    a_src = math.degrees(math.atan2(m[0, 2], m[0, 0]))
    th = math.radians((angle - a_src + 90.0) % 180.0 - 90.0)
    c, s = math.cos(th), math.sin(th)
    out = []
    for o in lot:
        dx, dz = o["x"] - j["x"], o["z"] - j["z"]
        mm = np.array(o["matrice"], np.float64).reshape(3, 3).copy()
        mm[:, 0], mm[:, 2] = mm[:, 0] * c - mm[:, 2] * s, mm[:, 0] * s + mm[:, 2] * c
        out.append(dict(o, x=x + dx * c - dz * s, z=z + dx * s + dz * c, matrice=mm.ravel().tolist()))
    return out


def axe_et_demi(lot):
    """(centre (x, z), direction unitaire de la passerelle, demi-longueur du tablier en u)."""
    j = passerelle(lot)
    m = np.array(j["matrice"]).reshape(3, 3)
    ax = np.array([m[0, 0], m[0, 2]])
    n = float(np.hypot(*ax))
    return (j["x"], j["z"]), ax / n, DEMI_LONGUEUR * n


def plage_eau(visible, x, z, u, portee=1.5, pas_t=0.02):
    """(t0, t1) de la plage d'eau visible le long de u passant au plus près de (x, z), ou None."""
    t = np.arange(-portee, portee + 1e-9, pas_t)
    w = np.array([visible(x + s * u[0], z + s * u[1]) for s in t])
    if not w.any():
        return None
    idx = np.nonzero(w)[0]
    a = b_ = idx[np.argmin(np.abs(t[idx]))]
    while a > 0 and w[a - 1]:
        a -= 1
    while b_ < len(t) - 1 and w[b_ + 1]:
        b_ += 1
    return float(t[a]), float(t[b_])


def etirer(lot, f):
    """Passerelle et garde-corps allongés de `f` le long de la passerelle, autour de son centre ; le reste inchangé."""
    if f <= 1.0:
        return lot
    (xc, zc), u, _ = axe_et_demi(lot)
    out = []
    for o in lot:
        if o["role"] not in ("passerelle", "garde-corps"):
            out.append(o)
            continue
        rel = np.array([o["x"] - xc, o["z"] - zc])
        pos = rel + (f - 1.0) * float(rel @ u) * u
        mm = np.array(o["matrice"], np.float64).reshape(3, 3).copy()
        comp = mm[:, 0] * u[0] + mm[:, 2] * u[1]
        mm[:, 0] += (f - 1.0) * comp * u[0]
        mm[:, 2] += (f - 1.0) * comp * u[1]
        out.append(dict(o, x=xc + pos[0], z=zc + pos[1], matrice=mm.ravel().tolist()))
    return out


def dans_emprise(x, z, pont):
    """(x, z) dans l'emprise du pont de pierre `pont` = (x0, z0, lacet) ? (x local vers l'angle monde -lacet)."""
    x0, z0, lacet = pont
    t = math.radians(lacet)
    dx, dz = x - x0, z - z0
    return abs(dx * math.cos(t) - dz * math.sin(t)) <= EMPRISE_PIERRE[0] and \
        abs(dx * math.sin(t) + dz * math.cos(t)) <= EMPRISE_PIERRE[1]


def entites(sol, eau_riv, pas, bilan=None, remplacees=None, nouveaux=(), traversees=None):
    """[blocs XML <entity>] des objets des ponts (calque `ponts_wh1`), hauteurs posées sur notre relief (`sol`, ligne 0 au
    nord) et au-dessus de notre eau (`eau_riv`, NaN hors de l'eau) ; `pas` px par unité. `remplacees` : {pose: (x, z,
    lacet)} du pont de pierre de CA qui remplace passerelle et garde-corps ; `nouveaux` : [(x, z, angle de la route)] des
    traversées d'Athel Loren sans croisement de WH1 (lot du pont de WH1 gardé le plus proche, tourné) ; `traversees` :
    {pose: (x, z, angle)} des traversées du plan, où une passerelle gardée qui n'enjambe pas notre eau est réalignée."""
    import props_wh1_vers_layers as PL
    H, L = sol.shape
    r3 = PL.Z_VERS_RASTER
    modeles_ = PL.Modeles()
    b = bilan if bilan is not None else {}
    remplacees = remplacees or {}
    traversees = traversees or {}

    def px(x, z):
        return (int(min(max(round((H - 1.5) - z * r3 * pas), 0), H - 1)), int(min(max(round(x * pas - 0.5), 0), L - 1)))

    def sol_max(x, z, r=1):
        i, j = px(x, z)
        return float(np.max(sol[max(i - r, 0):i + r + 1, max(j - r, 0):j + r + 1]))

    def visible(x, z):
        p = px(x, z)
        return bool(eau_riv[p] > sol[p])

    def enjambe(lot):
        (xc, zc), u, demi = axe_et_demi(lot)
        pl = plage_eau(visible, xc, zc, u)
        return pl is None or (pl[0] >= -demi + MARGE_GARDER and pl[1] <= demi - MARGE_GARDER)

    def ajuster(lot, cle):
        """La passerelle centrée sur l'eau le long de son axe et allongée s'il le faut (bouts à MARGE_BERGE de l'eau)."""
        (xc, zc), u, demi = axe_et_demi(lot)
        pl = plage_eau(visible, xc, zc, u)
        if pl is None:
            return lot
        milieu = (pl[0] + pl[1]) / 2
        lot = tourner(lot, xc + milieu * u[0], zc + milieu * u[1], math.degrees(math.atan2(u[1], u[0])))
        f = ((pl[1] - pl[0]) / 2 + MARGE_BERGE) / demi
        if f > ETIREMENT_MAX:
            b.setdefault("passerelles trop courtes même allongées", []).append(cle)
            f = ETIREMENT_MAX
        if f > 1.0:
            b.setdefault("passerelles allongées", []).append(round(f, 2))
        return etirer(lot, f)
    objs = objets_ponts()
    par_pose = {}
    for o in objs:
        par_pose.setdefault(o["pose"], []).append(o)
    lots = []
    for k, lot in sorted(par_pose.items()):
        if k not in remplacees and enjambe(lot):
            b["passerelles de WH1 à leur place exacte"] = b.get("passerelles de WH1 à leur place exacte", 0) + 1
        elif k not in remplacees:
            if k in traversees:
                x, z, angle = traversees[k]
                lot = tourner(lot, x, z, angle)
                b["passerelles de WH1 réalignées sur la traversée"] = \
                    b.get("passerelles de WH1 réalignées sur la traversée", 0) + 1
            lot = ajuster(lot, k)
        lots.append((k, lot))
    gardes = [(k, lot) for k, lot in lots if k not in remplacees] or lots
    for x, z, angle in nouveaux:
        k, lot = min(gardes, key=lambda kl: math.hypot(passerelle(kl[1])["x"] - x, passerelle(kl[1])["z"] - z))
        cle = f"{k}:vers:{x:.2f}:{z:.2f}"
        lots.append((cle, ajuster(tourner(lot, x, z, angle), cle)))
        b["passerelles de WH1 recopiées (Athel Loren)"] = b.get("passerelles de WH1 recopiées (Athel Loren)", 0) + 1
    out = []
    for k, lot in lots:
        pierre = remplacees.get(k)
        j = passerelle(lot)
        m = np.array(j["matrice"]).reshape(3, 3)
        bouts = [(j["x"] + s * DEMI_LONGUEUR * m[0, 0], j["z"] + s * DEMI_LONGUEUR * m[0, 2]) for s in (-1, 1)]
        ref = max(sol_max(x, z) for x, z in bouts)
        # l'eau sous le tablier (échantillons le long de la passerelle)
        eau = [eau_riv[px(j["x"] + t * m[0, 0], j["z"] + t * m[0, 2])] for t in np.linspace(-DEMI_LONGUEUR, DEMI_LONGUEUR, 15)]
        eau = [e for e in eau if np.isfinite(e)]
        tablier = ref + TABLIER_SUR_SOL
        if eau and tablier < max(eau) + GARDE_EAU:
            b["passerelles relevées au-dessus de l'eau"] = b.get("passerelles relevées au-dessus de l'eau", 0) + 1
            tablier = max(eau) + GARDE_EAU
            ref = tablier - TABLIER_SUR_SOL
        if pierre is None:
            b.setdefault("tablier au-dessus de l'eau (min)", 9.9)
            if eau:
                b["tablier au-dessus de l'eau (min)"] = round(min(b["tablier au-dessus de l'eau (min)"], tablier - max(eau)),
                                                              3)
            # intégration : les deux bouts du tablier sur la terre (sinon la passerelle s'arrête dans l'eau) ; eau visible
            # seulement (le ruban glisse sous les berges : 22 % de ses pixels sont sous le sol, voulu)
            if any(eau_riv[px(x, z)] > sol[px(x, z)] for x, z in bouts):
                b.setdefault("passerelles dont un bout est dans l'eau", []).append((round(j["x"], 1), round(j["z"], 1)))
        for o in lot:
            if pierre is not None and (o["role"] in ("passerelle", "garde-corps") or dans_emprise(o["x"], o["z"], pierre)):
                b[f"{o['role']} de WH1 remplacés par le pont de pierre"] = \
                    b.get(f"{o['role']} de WH1 remplacés par le pont de pierre", 0) + 1
                continue
            y = ref + o["y_rel"] if o["role"] in ("passerelle", "garde-corps") else sol[px(o["x"], o["z"])] + o["y_rel"]
            cible, mode = modeles_.resout(o["modele"])
            if cible is None:
                raise SystemExit(f"modèle de pont sans fichier : {o['modele']} (lancer modeles_wh1.py --apply)")
            rot, ech = PL.rotation_terry(o["matrice"])
            o_ = {"region": f"pont:{k}", "modele": o["modele"], "drapeaux": b"\x00" * 30}
            out.append(PL.entite(o_, cible, rot, ech, (o["x"], float(y), o["z"]), ""))
            b[o["role"]] = b.get(o["role"], 0) + 1
    b["poses"] = len(par_pose)
    return out


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    objs = objets_ponts()
    poses = sorted({o["pose"] for o in objs})
    print(f"{len(objs)} objets sur {len(poses)} poses river_crossing ; miroirs : {sum(o['miroir'] for o in objs)}")
    for m in modeles():
        print("  ", m, sum(1 for o in objs if o["modele"] == m))
    j = [o for o in objs if o["role"] == "passerelle"]
    for o in j:
        m = np.array(o["matrice"]).reshape(3, 3)
        print(f"  pose {o['pose']:5d} passerelle ({o['x']:7.2f} ; {o['z']:7.2f}) y_rel {o['y_rel']:+.3f} "
              f"longueur {2 * DEMI_LONGUEUR * np.linalg.norm(m[0]):.2f} lacet {math.degrees(math.atan2(-m[0, 2], m[0, 0])):6.1f}"
              f"{' miroir' if o['miroir'] else ''}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
