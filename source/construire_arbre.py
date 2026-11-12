#!/usr/bin/env python3
"""Dessine images/arbre.svg, l'arbre du « Real de Lego City », et vérifie les renvois de texte.md.

Un arbre de briques : chaque chapitre est une grosse brique 2 × 4 posée de face, avec ses quatre tenons, son
numéro dans un rond blanc et son titre ; à côté, la figurine ou l'objet le plus marquant de l'étape (une pièce
dessinée par Manon). Les briques changent de couleur au fil de l'histoire (rouge, jaune, bleu, vert, orange).
Les faces du dé sont posées sur de petites briques jaunes ; les liens sont des pointillés.

Usage, depuis la racine du dépôt : python3 source/construire_arbre.py (Pillow facultatif, pour réduire les
images intégrées)
"""
import base64
import re
from io import BytesIO
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TEXTE = RACINE / "source" / "texte.md"
SORTIE = RACINE / "images" / "arbre.svg"

ENCRE, JAUNE = "#22252b", "#f5c518"
COULEURS = ["#d01012", "#f5c518", "#0057b8", "#2c8a3f", "#f2780c"]
FONCES = ["#a80c0e", "#c99d06", "#003f86", "#1f6a2f", "#b8590a"]
# Premier chapitre de chaque couleur
PARTIES = ["Prologue", "4", "8", "12", "20"]

LARGEUR, CENTRE, ECART = 1000, 500, 330
BRIQUE_L, BRIQUE_H = 236, 70
PAS_Y = 170
RANGEES = [["Prologue"], ["1"], ["2", "3"], ["4"], ["5"], ["6", "7"], ["8"], ["9", "10"], ["11"], ["12"],
           ["13", "14"], ["15", "16"], ["17"], ["18", "19"], ["20"], ["21", "22"], ["23"]]
# La pièce montrée à côté de chaque brique
VEDETTES = {"Prologue": "trappe", "1": "kylian", "2": "poubelle", "3": "trampoline", "4": "serviette-le-real-de-lego-city",
            "5": "grue", "6": "zidane", "7": "entraineur-de-l-om", "8": "banderole-allez-le-real", "9": "astronaute",
            "10": "ronaldo", "11": "astronaute", "12": "silhouette", "13": "silhouette", "14": "porte",
            "15": "chaussettes-puantes", "16": "camion-de-pompiers", "17": "brioche", "18": "kylian", "19": "messi",
            "20": "coupe", "21": "chapeau-de-pirate", "22": "projecteur", "23": "minuscule-coupe"}


def lire_texte():
    texte = TEXTE.read_text(encoding="utf-8")
    titres, renvois, des = {}, {}, {}
    for bloc in re.split(r"^## ", texte, flags=re.M)[1:]:
        tete = bloc.split("\n", 1)[0]
        nom = "Prologue" if tete.startswith("Prologue") else re.match(r"Chapitre (\d+)", tete)[1]
        titres[nom] = tete.split(". ", 1)[1].strip()
        renvois[nom] = re.findall(r"chapitre (\d+)\.?$", bloc, flags=re.M)
        for libelle, cible in re.findall(r"^- (Un nombre \w+|Un résultat de [\d, ou]+) : poursuis au chapitre (\d+)",
                                         bloc, flags=re.M):
            des[(nom, cible)] = (libelle[len("Un résultat de "):] if libelle.startswith("Un résultat")
                                 else libelle.replace("Un nombre ", "").capitalize())
    return titres, renvois, des


def lignes(titre, largeur):
    sortie, ligne = [], ""
    for mot in titre.split():
        if ligne and len(ligne) + 1 + len(mot) > largeur:
            sortie.append(ligne)
            ligne = mot
        else:
            ligne = f"{ligne} {mot}".strip()
    return sortie + [ligne]


IMAGES = {}


def image_piece(nom):
    if nom not in IMAGES:
        chemin = RACINE / "images" / "pieces" / f"{nom}.png"
        try:
            from PIL import Image
            im = Image.open(chemin)
            im.thumbnail((140, 140))
            tampon = BytesIO()
            im.save(tampon, "PNG", optimize=True)
            donnees = tampon.getvalue()
        except ImportError:
            donnees = chemin.read_bytes()
        IMAGES[nom] = "data:image/png;base64," + base64.b64encode(donnees).decode()
    return IMAGES[nom]


def brique(x, y, nom, titre, clair, fonce, cote):
    """Brique 2 × 4 vue de face : quatre tenons, le numéro dans un rond blanc, le titre ; la pièce à côté."""
    x0, y0 = x - BRIQUE_L / 2, y - BRIQUE_H / 2
    tenons = "".join(
        f'<rect x="{x0 + 18 + i * 56}" y="{y0 - 11}" width="32" height="14" rx="3" fill="{clair}" stroke="{fonce}" stroke-width="2"/>'
        f'<rect x="{x0 + 22 + i * 56}" y="{y0 - 9}" width="24" height="3" rx="1.5" fill="#fff" opacity="0.35"/>'
        for i in range(4))
    corps = (f'<rect x="{x0}" y="{y0}" width="{BRIQUE_L}" height="{BRIQUE_H}" rx="7" fill="{clair}" stroke="{fonce}" stroke-width="2.5"/>'
             f'<rect x="{x0 + 3}" y="{y0 + BRIQUE_H - 12}" width="{BRIQUE_L - 6}" height="9" rx="4" fill="{fonce}" opacity="0.45"/>'
             f'<rect x="{x0 + 8}" y="{y0 + 6}" width="{BRIQUE_L - 16}" height="5" rx="2.5" fill="#fff" opacity="0.3"/>')
    texte_couleur = ENCRE if clair == JAUNE else "#fff"
    if nom == "Prologue":
        numero = (f'<text x="{x}" y="{y0 + 26}" text-anchor="middle" font-family="Jost" font-weight="700" font-size="13" '
                  f'letter-spacing="2" fill="{texte_couleur}" opacity="0.85">PROLOGUE</text>')
        corps_titre = "".join(f'<text x="{x}" y="{y0 + 48 + i * 17}" text-anchor="middle" font-family="Jost" font-weight="700" '
                              f'font-size="16" fill="{texte_couleur}">{l}</text>' for i, l in enumerate(lignes(titre, 26)))
    else:
        numero = (f'<circle cx="{x0 + 36}" cy="{y - 2}" r="24" fill="#fff"/>'
                  f'<text x="{x0 + 36}" y="{y + 8}" text-anchor="middle" font-family="Jost" font-weight="800" '
                  f'font-size="{28 if len(nom) == 1 else 24}" fill="{fonce}">{nom}</text>')
        texte = lignes(titre, 18)
        debut = y + 3 - (len(texte) - 1) * 9
        corps_titre = "".join(f'<text x="{x0 + 72}" y="{debut + i * 18}" font-family="Jost" font-weight="700" font-size="15.5" '
                              f'fill="{texte_couleur}">{l}</text>' for i, l in enumerate(texte))
    piece = ""
    if nom in VEDETTES:
        px = x0 - 72 if cote == "gauche" else x0 + BRIQUE_L + 10
        piece = (f'<image x="{px}" y="{y - 40}" width="62" height="74" preserveAspectRatio="xMidYMid meet" '
                 f'href="{image_piece(VEDETTES[nom])}"/>')
    return tenons + corps + numero + corps_titre + piece


def petite_brique(x, y, texte):
    largeur = 28 + len(texte) * 8.2
    return (f'<rect x="{x - 13}" y="{y - 19}" width="10" height="7" rx="2" fill="{JAUNE}"/>'
            f'<rect x="{x + 3}" y="{y - 19}" width="10" height="7" rx="2" fill="{JAUNE}"/>'
            f'<rect x="{x - largeur / 2}" y="{y - 13}" width="{largeur}" height="26" rx="4" fill="{JAUNE}"/>'
            f'<rect x="{x - largeur / 2}" y="{y + 8}" width="{largeur}" height="5" rx="2" fill="#000" opacity="0.13"/>'
            f'<text x="{x}" y="{y + 5}" text-anchor="middle" font-family="Jost" font-weight="700" font-size="14" '
            f'fill="{ENCRE}">{texte}</text>')


def police(fichier, nom):
    code = base64.b64encode((RACINE / "fonts" / fichier).read_bytes()).decode()
    return (f'@font-face {{ font-family: "{nom}"; font-weight: 300 800; '
            f'src: url(data:font/woff2;base64,{code}) format("woff2"); }}')


def construire():
    titres, renvois, des = lire_texte()
    pos = {}
    for i, noms in enumerate(RANGEES):
        y = 50 + BRIQUE_H / 2 + i * PAS_Y
        for j, nom in enumerate(noms):
            pos[nom] = (CENTRE + (j - (len(noms) - 1) / 2) * ECART, y)
    hauteur = 50 + BRIQUE_H + (len(RANGEES) - 1) * PAS_Y + 30
    assert set(pos) == set(renvois), f"Chapitres absents de l'arbre : {set(renvois) ^ set(pos)}"

    couleur_de, courant = {}, 0
    for n in [n for rangee in RANGEES for n in rangee]:
        if n in PARTIES:
            courant = PARTIES.index(n)
        couleur_de[n] = courant

    traits, pointes, etiquettes, faites = [], set(), [], set()
    for a, cibles in renvois.items():
        for b in cibles:
            assert b in pos, f"Renvoi vers un chapitre inconnu : {a} -> {b}"
            (x1, y1), (x2, y2) = pos[a], pos[b]
            assert y2 > y1, f"Renvoi en arrière non prévu : {a} -> {b}"
            depart, arrivee = y1 + BRIQUE_H / 2, y2 - BRIQUE_H / 2 - 14
            if x1 == x2:
                traits.append(f'<path d="M{x1} {depart} V{arrivee - 10}"/>')
            else:
                traits.append(f'<path d="M{x1} {depart} V{depart + 22} H{x2} V{arrivee - 10}"/>')
            pointes.add((x2, arrivee))
            if (a, b) in des and b not in faites:
                faites.add(b)
                etiquettes.append(petite_brique(x2, (depart + 22 + arrivee - 10) / 2 + 3, des[(a, b)]))
    fleches = "".join(f'<path d="M{x} {y} l-8 -12 h16 z"/>' for x, y in sorted(pointes))

    briques = "".join(brique(*pos[n], n, titres[n], COULEURS[couleur_de[n]], FONCES[couleur_de[n]],
                             "droite" if pos[n][0] > CENTRE else "gauche") for n in pos)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LARGEUR} {hauteur:.0f}" width="{LARGEUR}" '
        f'height="{hauteur:.0f}"><style>' + police("Jost.woff2", "Jost") + "</style>"
        + f'<g fill="none" stroke="{ENCRE}" stroke-width="3.5" stroke-dasharray="0.5 8" stroke-linecap="round">{"".join(traits)}</g>'
        + f'<g fill="{ENCRE}">{fleches}</g>'
        + "".join(etiquettes) + briques + "</svg>"
    )
    SORTIE.write_text(svg, encoding="utf-8")
    print(f"{SORTIE} : {len(pos)} étapes, {sum(len(c) for c in renvois.values())} renvois, {len(des)} branches au dé")


if __name__ == "__main__":
    construire()
