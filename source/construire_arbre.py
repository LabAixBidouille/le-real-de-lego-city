#!/usr/bin/env python3
"""Dessine images/arbre.svg, l'arbre du « Real de Lego City », et vérifie les renvois de texte.md.

Dans l'esprit d'une notice de montage : l'arbre se lit de haut en bas, chaque chapitre est une carte d'étape
(gros numéro, titre à côté), les parties de l'histoire sont les sachets numérotés qui ouvrent chaque section.
Les flèches sont noires, à angle droit et pointe pleine ; les faces du dé sont posées sur de petites briques
jaunes, comme dans la case du dé du site.

Usage, depuis la racine du dépôt : python3 source/construire_arbre.py
"""
import base64
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TEXTE = RACINE / "source" / "texte.md"
SORTIE = RACINE / "images" / "arbre.svg"

ENCRE, DOUCE, TRAIT, JAUNE = "#22252b", "#5b5f68", "#cfd8e3", "#f5c518"

LARGEUR, CENTRE, ECART = 1000, 520, 300
CARTE_L, CARTE_H = 250, 76
PAS_Y, ENTETE = 150, 70
RANGEES = [["Prologue"], ["1"], ["2", "3"], ["4"], ["5"], ["6", "7"], ["8"], ["9", "10"], ["11"], ["12"],
           ["13", "14"], ["15", "16"], ["17"], ["18", "19"], ["20"], ["21", "22"], ["23"]]
# Les sachets : premier chapitre de chacun et son nom
SACHETS = [("Prologue", "La chute"), ("4", "L’équipe"), ("8", "Le tournoi"), ("12", "La finale"), ("20", "Le retour")]


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


def carte(x, y, nom, titre):
    """Carte d'étape : cadre gris-bleu, gros numéro à gauche, titre à droite (sur une ou deux lignes)."""
    x0, y0 = x - CARTE_L / 2, y - CARTE_H / 2
    fond = (f'<rect x="{x0}" y="{y0}" width="{CARTE_L}" height="{CARTE_H}" rx="9" fill="#fff" stroke="{TRAIT}" '
            f'stroke-width="2.5"/>')
    if nom == "Prologue":
        etiquette = (f'<text x="{x}" y="{y0 + 26}" text-anchor="middle" font-family="Jost" font-weight="600" '
                     f'font-size="12" letter-spacing="1.5" fill="{DOUCE}">PROLOGUE</text>')
        corps = "".join(f'<text x="{x}" y="{y0 + 48 + i * 18}" text-anchor="middle" font-family="Jost" '
                        f'font-weight="600" font-size="15.5" fill="{ENCRE}">{l}</text>'
                        for i, l in enumerate(lignes(titre, 28)))
        return fond + etiquette + corps
    numero = (f'<text x="{x0 + 42}" y="{y + 15}" text-anchor="middle" font-family="Jost" font-weight="800" '
              f'font-size="{42 if len(nom) == 1 else 36}" fill="{ENCRE}">{nom}</text>')
    separation = (f'<line x1="{x0 + 80}" y1="{y0 + 14}" x2="{x0 + 80}" y2="{y0 + CARTE_H - 14}" stroke="{TRAIT}" '
                  'stroke-width="2"/>')
    texte = lignes(titre, 21)
    debut = y + 5.5 - (len(texte) - 1) * 9
    corps = "".join(f'<text x="{x0 + 94}" y="{debut + i * 18}" font-family="Jost" font-weight="500" font-size="15" '
                    f'fill="{ENCRE}">{l}</text>' for i, l in enumerate(texte))
    return fond + numero + separation + corps


def brique(x, y, texte):
    largeur = 26 + len(texte) * 8.2
    return (f'<rect x="{x - largeur / 2}" y="{y - 12}" width="{largeur}" height="24" rx="4" fill="{JAUNE}"/>'
            f'<rect x="{x - largeur / 2}" y="{y + 8}" width="{largeur}" height="4" rx="2" fill="#000" opacity="0.13"/>'
            f'<text x="{x}" y="{y + 5}" text-anchor="middle" font-family="Jost" font-weight="600" font-size="14" '
            f'fill="{ENCRE}">{texte}</text>')


def sachet(y, numero, nom):
    return (f'<circle cx="54" cy="{y}" r="15" fill="{ENCRE}"/>'
            f'<text x="54" y="{y + 5.5}" text-anchor="middle" font-family="Jost" font-weight="700" font-size="16" '
            f'fill="#fff">{numero}</text>'
            f'<text x="80" y="{y + 6}" font-family="Jost" font-weight="600" font-size="17" fill="{ENCRE}">Sachet {numero}'
            f'<tspan fill="{DOUCE}" font-weight="500"> · {nom}</tspan></text>')


def police(fichier, nom):
    code = base64.b64encode((RACINE / "fonts" / fichier).read_bytes()).decode()
    return (f'@font-face {{ font-family: "{nom}"; font-weight: 300 800; '
            f'src: url(data:font/woff2;base64,{code}) format("woff2"); }}')


def construire():
    titres, renvois, des = lire_texte()
    debuts = {premier: (i, nom) for i, (premier, nom) in enumerate(SACHETS, start=1)}
    pos, entetes, y = {}, [], 0
    for noms in RANGEES:
        if noms[0] in debuts:
            entetes.append((y + 30, *debuts[noms[0]]))
            y += ENTETE + CARTE_H / 2
        else:
            y += PAS_Y - CARTE_H / 2
        for j, nom in enumerate(noms):
            pos[nom] = (CENTRE + (j - (len(noms) - 1) / 2) * ECART, y)
        y += CARTE_H / 2
    hauteur = y + 30
    assert set(pos) == set(renvois), f"Chapitres absents de l'arbre : {set(renvois) ^ set(pos)}"

    traits, pointes, etiquettes, faites = [], set(), [], set()
    for a, cibles in renvois.items():
        for b in cibles:
            assert b in pos, f"Renvoi vers un chapitre inconnu : {a} -> {b}"
            (x1, y1), (x2, y2) = pos[a], pos[b]
            assert y2 > y1, f"Renvoi en arrière non prévu : {a} -> {b}"
            depart, arrivee = y1 + CARTE_H / 2, y2 - CARTE_H / 2 - 2
            if x1 == x2:
                traits.append(f'<path d="M{x1} {depart} V{arrivee - 11}"/>')
            else:
                palier = depart + 16 if len(cibles) > 1 else arrivee - 46
                traits.append(f'<path d="M{x1} {depart} V{palier} H{x2} V{arrivee - 11}"/>')
            pointes.add((x2, arrivee))
            if (a, b) in des and b not in faites:
                faites.add(b)
                etiquettes.append(brique(x2, arrivee - 28, des[(a, b)]))
    fleches = "".join(f'<path d="M{x} {y} l-7.5 -12 h15 z"/>' for x, y in sorted(pointes))
    sections = "".join(sachet(y_, n, nom) for y_, n, nom in entetes)
    cartes = "".join(carte(*pos[n], n, titres[n]) for n in pos)
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {LARGEUR} {hauteur:.0f}" width="{LARGEUR}" '
        f'height="{hauteur:.0f}"><style>' + police("Jost.woff2", "Jost") + "</style>"
        + sections
        + f'<g fill="none" stroke="{ENCRE}" stroke-width="2.5" stroke-linejoin="miter">{"".join(traits)}</g>'
        + f'<g fill="{ENCRE}">{fleches}</g>'
        + "".join(etiquettes) + cartes + "</svg>"
    )
    SORTIE.write_text(svg, encoding="utf-8")
    print(f"{SORTIE} : {len(pos)} étapes, {sum(len(c) for c in renvois.values())} renvois, {len(des)} branches au dé")


if __name__ == "__main__":
    construire()
