#!/usr/bin/env python3
"""Dessine images/arbre.svg, l'arbre du « Real de Lego City », et vérifie les renvois de texte.md.

L'arbre se lit de haut en bas. Chaque chapitre est une brique 2 × 1 numérotée, avec son titre dessous ; la
couleur de la brique dit dans quelle partie de l'histoire on se trouve (bande de la marge gauche). Sur chaque
branche, les faces du dé qui y mènent. Flèches à angle droit, pointe pleine.

Usage, depuis la racine du dépôt : python3 source/construire_arbre.py
"""
import base64
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TEXTE = RACINE / "source" / "texte.md"
SORTIE = RACINE / "images" / "arbre.svg"

ENCRE, PAPIER, GRIS = "#22252b", "#f8f4ea", "#a7a49d"
ROUGE, JAUNE, BLEU, VERT, GRIS_BRIQUE = "#d01012", "#f5c518", "#0057b8", "#2c8a3f", "#8c8a85"
FONCE = {ROUGE: "#a80c0e", JAUNE: "#d6a90c", BLEU: "#003f86", VERT: "#1f6a2f", GRIS_BRIQUE: "#6c6a66"}

LARGEUR, CENTRE, ECART = 1100, 620, 300
# Rangées de haut en bas
RANGEES = [["Prologue"], ["1"], ["2", "3"], ["4"], ["5"], ["6", "7"], ["8"], ["9", "10"], ["11"], ["12"],
           ["13", "14"], ["15", "16"], ["17"], ["18", "19"], ["20"], ["21", "22"], ["23"]]
PAS_Y, HAUT_Y = 150, 60
# Les parties de l'histoire : (premier chapitre, dernier, nom, couleur)
PARTIES = [("Prologue", "3", "LA CHUTE", GRIS_BRIQUE), ("4", "7", "L’ÉQUIPE", JAUNE),
           ("8", "11", "LE TOURNOI", BLEU), ("12", "19", "LA FINALE", ROUGE), ("20", "23", "LE RETOUR", VERT)]
SOUS_TITRE = 62


def lire_texte():
    texte = TEXTE.read_text(encoding="utf-8")
    titres, renvois, des = {}, {}, {}
    for bloc in re.split(r"^## ", texte, flags=re.M)[1:]:
        tete = bloc.split("\n", 1)[0]
        nom = "Prologue" if tete.startswith("Prologue") else re.match(r"Chapitre (\d+)", tete)[1]
        titres[nom] = tete.split(". ", 1)[1].strip()
        renvois[nom] = re.findall(r"chapitre (\d+)\.?$", bloc, flags=re.M)
        for libelle, cible in re.findall(r"^- (Un nombre \w+|Un résultat de [\d, ou]+) : poursuis au chapitre (\d+)", bloc, flags=re.M):
            des[(nom, cible)] = (libelle[len("Un résultat de "):] if libelle.startswith("Un résultat")
                                 else libelle.replace("Un nombre ", "").capitalize())
    return titres, renvois, des


def partie(nom, pos):
    y = pos[nom][1]
    for premier, dernier, _, couleur in PARTIES:
        if pos[premier][1] <= y <= pos[dernier][1]:
            return couleur
    return GRIS_BRIQUE


def brique(x, y, nom, couleur):
    """Brique 2 × 1 vue de face : corps, deux tétons, numéro."""
    l, h = 72, 40
    texte = "Prologue" if nom == "Prologue" else nom
    taille = 15 if nom == "Prologue" else 24
    if nom == "Prologue":
        l = 96
    chiffre = ENCRE if couleur == JAUNE else "#fff"
    tetons = "".join(f'<rect x="{x + dx - 9}" y="{y - h / 2 - 8}" width="18" height="10" rx="3" fill="{couleur}" '
                     f'stroke="{FONCE[couleur]}" stroke-width="2"/>' for dx in (-l / 4, l / 4))
    return (tetons
            + f'<rect x="{x - l / 2}" y="{y - h / 2}" width="{l}" height="{h}" rx="5" fill="{couleur}" '
              f'stroke="{FONCE[couleur]}" stroke-width="2"/>'
            + f'<rect x="{x - l / 2 + 2}" y="{y + h / 2 - 7}" width="{l - 4}" height="5" fill="{FONCE[couleur]}" opacity="0.35"/>'
            + f'<text x="{x}" y="{y + taille * 0.36}" text-anchor="middle" font-family="Jost" font-weight="700" '
              f'font-size="{taille}" fill="{chiffre}">{texte}</text>')


def lignes(titre, largeur=26):
    sortie, ligne = [], ""
    for mot in titre.split():
        if ligne and len(ligne) + 1 + len(mot) > largeur:
            sortie.append(ligne)
            ligne = mot
        else:
            ligne = f"{ligne} {mot}".strip()
    return sortie + [ligne]


def titre_svg(x, y, titre):
    tspans = "".join(f'<tspan x="{x}" dy="{0 if i == 0 else 18}">{l}</tspan>' for i, l in enumerate(lignes(titre)))
    return (f'<text x="{x}" y="{y + 42}" text-anchor="middle" font-family="Jost" font-weight="500" '
            f'font-size="15" fill="{ENCRE}">{tspans}</text>')


def pastille(x, y, texte):
    largeur = 22 + len(texte) * 8.6
    return (f'<rect x="{x - largeur / 2}" y="{y - 12}" width="{largeur}" height="24" rx="4" fill="{ROUGE}"/>'
            f'<text x="{x}" y="{y + 5.5}" text-anchor="middle" font-family="Jost" font-weight="600" '
            f'font-size="15" fill="#fff">{texte}</text>')


def police(fichier, nom):
    code = base64.b64encode((RACINE / "fonts" / fichier).read_bytes()).decode()
    return f'@font-face {{ font-family: "{nom}"; src: url(data:font/woff2;base64,{code}) format("woff2"); }}'


def construire():
    titres, renvois, des = lire_texte()
    pos = {}
    for i, noms in enumerate(RANGEES):
        for j, nom in enumerate(noms):
            pos[nom] = (CENTRE + (j - (len(noms) - 1) / 2) * ECART, HAUT_Y + i * PAS_Y)
    assert set(pos) == set(renvois), f"Chapitres absents de l'arbre : {set(renvois) ^ set(pos)}"
    hauteur = HAUT_Y + (len(RANGEES) - 1) * PAS_Y + 110

    traits, pointes, etiquettes, etiquetees = [], set(), [], set()
    for a, cibles in renvois.items():
        for b in cibles:
            assert b in pos, f"Renvoi vers un chapitre inconnu : {a} -> {b}"
            (x1, y1), (x2, y2) = pos[a], pos[b]
            assert y2 > y1, f"Renvoi en arrière non prévu : {a} -> {b}"
            depart, arrivee = y1 + SOUS_TITRE, y2 - 34
            if x1 == x2:
                traits.append(f'<path d="M{x1} {depart} V{arrivee - 10}"/>')
            else:
                palier = depart + 14 if len(cibles) > 1 else arrivee - 30
                traits.append(f'<path d="M{x1} {depart} V{palier} H{x2} V{arrivee - 10}"/>')
            pointes.add((x2, arrivee))
            if (a, b) in des and b not in etiquetees:
                etiquetees.add(b)
                etiquettes.append(pastille(x2, arrivee - 24, des[(a, b)]))
    fleches = "".join(f'<path d="M{x} {y} l-7 -11 h14 z"/>' for x, y in sorted(pointes))

    marge = []
    debuts = [pos[p][1] - 48 for p, _, _, _ in PARTIES]
    for i, (premier, dernier, texte, couleur) in enumerate(PARTIES):
        haut = debuts[i]
        bas = debuts[i + 1] - 12 if i + 1 < len(PARTIES) else pos[dernier][1] + SOUS_TITRE + 10
        milieu = (haut + bas) / 2
        marge.append(f'<rect x="40" y="{haut}" width="34" height="{bas - haut}" rx="5" fill="{couleur}"/>'
                     f'<text transform="translate(63,{milieu}) rotate(-90)" text-anchor="middle" font-family="Jost" '
                     f'font-weight="700" font-size="18" letter-spacing="2" fill="{ENCRE if couleur == JAUNE else "#fff"}">{texte}</text>')

    noeuds = "".join(brique(*pos[n], n, partie(n, pos)) + titre_svg(*pos[n], titres[n]) for n in pos)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LARGEUR} {hauteur}" width="{LARGEUR}" height="{hauteur}">'
        "<style>" + police("Jost.woff2", "Jost") + "</style>"
        + "".join(marge)
        + f'<g fill="none" stroke="{BLEU}" stroke-width="3" stroke-linejoin="miter">{"".join(traits)}</g>'
        + f'<g fill="{BLEU}">{fleches}</g>'
        + "".join(etiquettes) + noeuds + "</svg>"
    )
    SORTIE.write_text(svg, encoding="utf-8")
    print(f"{SORTIE} : {len(pos)} étapes, {sum(len(c) for c in renvois.values())} renvois, {len(des)} branches au dé")


if __name__ == "__main__":
    construire()
