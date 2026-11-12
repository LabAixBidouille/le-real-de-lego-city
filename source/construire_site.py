#!/usr/bin/env python3
"""Construit index.html du « Real de Lego City » à partir de source/texte.md.

Le moteur Harlowe est conservé tel quel dans index.html : seules les pages et la feuille de style du livre
sont régénérées.

Mise en page propre au livre d'Ernest et d'Abel, choisie par Manon : sobre comme une notice de montage
(page blanche, gris-bleu clair, numéro de chapitre en gros chiffre encadré comme une étape), les couleurs
franches des briques en accent. La case du dé est cerclée de bleu, ses faces posées sur des briques jaunes ;
le dé est une brique rouge 2 × 2 ; le séparateur, trois briques rouge, jaune et bleue. Police : Jost.

Les illustrations sont facultatives : un chapitre sans image dans images/chapitres/ s'ouvre sur son titre.

Usage, depuis la racine du dépôt : python3 source/construire_site.py
"""
import hashlib
import html
import re
import uuid
from pathlib import Path

RACINE = Path(__file__).resolve().parent.parent
TEXTE = RACINE / "source" / "texte.md"
SORTIE = RACINE / "index.html"
NOINDEX = '<meta name="robots" content="noindex, nofollow, noarchive">'
FAVICON = ('<link rel="icon" type="image/png" sizes="48x48" href="images/favicon-48.png">'
           '<link rel="icon" type="image/png" sizes="180x180" href="images/favicon.png">'
           '<link rel="apple-touch-icon" href="images/favicon.png">')

TITRE = "Le Real de Lego City"
AUTEURS = "Ernest et Abel"

# Résumé provisoire, à remplacer par celui de Manon
SYNOPSIS = (
    "Kylian Mbappé visitait tranquillement le musée du football quand le plancher s’est ouvert sous ses pieds. "
    "Le voici tombé à Lego City, avec des pinces à la place des mains et des jambes qui ne plient plus.\n\n"
    "La ville veut participer à la Ligue des Champions en Briques, mais elle n’a pas d’équipe. Avec Messi, "
    "Ronaldo, un pompier, une boulangère, un pirate et un astronaute, Kylian va devoir en construire une.\n\n"
    "Lance le dé : il décidera de ton atterrissage, de ton entraîneur et de ce qui t’attend avant la finale."
)

AVERTISSEMENT_COURT = "Fan fiction humoristique librement inspirée du football et des jouets LEGO®"
AVERTISSEMENT = (
    "Une fan fiction humoristique, librement inspirée du monde du football et de l’univers des jouets LEGO®. "
    "Les joueurs, l’entraîneur et les clubs qui existent réellement n’y apparaissent que comme des personnages "
    "de fiction : les situations et les paroles qu’on leur prête sont entièrement imaginaires. Ce livre n’est "
    "ni approuvé ni soutenu par eux, par leurs clubs ou par le groupe LEGO. LEGO est une marque déposée de son "
    "propriétaire."
)

# Texte de Manon, modèle commun aux livres de l'atelier ; seule change la phrase sur le genre
CONTEXTE = [
    "En octobre 2026, le L.A.B a animé l’atelier « La quête du curry, une histoire dont tu es le héros » "
    "dans les bibliothèques Méjanes d’Aix-en-Provence. Les enfants ont été accompagnés dans la création "
    "d’un récit complet, depuis l’invention des personnages jusqu’à la construction d’une intrigue "
    "reliant les différentes étapes de leur aventure.",
    "Nous leur avons proposé d’introduire une part de hasard dans leur récit. Le résultat d’un lancer de "
    "dé pouvait modifier le déroulement de certains passages et conduire le lecteur vers un chapitre ou "
    "un autre.",
    "Les enfants ont ainsi exploré, sans écran, des notions liées à la pensée computationnelle, une "
    "manière de décomposer un problème et d’organiser les étapes pour le résoudre. Ils ont formulé des "
    "règles de type « si… alors… », créé des embranchements et réfléchi à la façon dont les chemins se "
    "rejoignent pour former une histoire cohérente.",
    "Ernest et Abel ont choisi d’écrire une fan fiction humoristique, où de vrais footballeurs deviennent des "
    "figurines dans un monde de jouets. Un défi pour une histoire à embranchements, puisque chaque chemin "
    "doit garder son humour et conduire l’équipe jusqu’à la finale.",
    "L’atelier ne durant que deux heures, nous tenions à offrir à chaque enfant un livre complet pour "
    "illustrer leur travail et les rendre fiers de leurs productions. Le L.A.B a donc prolongé et mis en "
    "forme leur récit à l’aide d’outils numériques (l’intelligence artificielle a notamment permis "
    "d’aboutir à une histoire achevée et à un ensemble de visuels correspondant à leurs descriptions mais "
    "uniformes tout au long de la lecture).\n\n<b>À son origine, il y a avant tout les idées, les "
    "personnages et les dessins d’Ernest et d’Abel.</b>",
]
# Une phrase de leur fiche récit, à peine remise au propre
CITATION = ("Il va au musée du football, tombe dans une trappe, se retrouve dans le monde Lego et devient "
            "un Lego à son tour.")

# Couleurs des briques et du papier des illustrations
ROUGE, JAUNE, BLEU, VERT = "#d01012", "#f5c518", "#0057b8", "#2c8a3f"


def svg(code):
    """Une image SVG en data URI, utilisable en CSS."""
    return "data:image/svg+xml," + code.replace("#", "%23").replace("<", "%3C").replace(">", "%3E").replace('"', "'")


# La brique 2 × 2 qui sert de dé, vue de face, deux tétons visibles ; une version par couleur de sachet
def brique_de(clair, fonce):
    return svg(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
        f'<rect x="20" y="8" width="20" height="14" rx="3" fill="{fonce}"/><rect x="60" y="8" width="20" height="14" rx="3" fill="{fonce}"/>'
        f'<rect x="20" y="6" width="20" height="9" rx="4.5" fill="{clair}"/><rect x="60" y="6" width="20" height="9" rx="4.5" fill="{clair}"/>'
        f'<rect x="6" y="20" width="88" height="74" rx="7" fill="{fonce}"/>'
        f'<rect x="6" y="18" width="88" height="68" rx="7" fill="{clair}"/>'
        '<rect x="12" y="23" width="76" height="5" rx="2.5" fill="#ffffff" opacity="0.28"/>'
        '</svg>')


BRIQUES_DE = {1: brique_de(ROUGE, "#a80c0e"), 2: brique_de(JAUNE, "#c99d06"), 3: brique_de(BLEU, "#003f86"),
              4: brique_de(VERT, "#1f6a2f"), 5: brique_de("#f2780c", "#b8590a")}
BRIQUE_DE = BRIQUES_DE[1]
CSS_BRIQUES = "".join(f'.sachet-{n} .brique .corps {{ background-image: url("{code}"); }}\n'
                      for n, code in BRIQUES_DE.items()) + ".sachet-2 .brique .face { color: #22252b; }\n"

CSS = """
@font-face { font-family: "Jost"; font-weight: 300 800; font-display: swap; src: url("fonts/Jost.woff2") format("woff2"); }

/* Couleurs prises aux images : le crème du papier, le gris des plaques à tétons, les briques */
:root {
  --papier: #ffffff;
  --notice: #e8eef6;
  --notice-trait: #cfd8e3;
  --encre: #22252b;
  --encre-douce: #5b5f68;
  --plaque: #c9c6bf;
  --plaque-fonce: #a7a49d;
  --rouge: ROUGE;
  --rouge-fonce: #a80c0e;
  --jaune: JAUNE;
  --bleu: BLEU;
  --bleu-fonce: #003f86;
  --vert: VERT;
}
html, body, tw-story { background-color: var(--papier); color: var(--encre); }

tw-story {
  font-family: "Jost", "Trebuchet MS", sans-serif;
  font-weight: 400;
  font-size: 1.08em;
  line-height: 1.7;
  padding: 0.8em 1.2em 3em;
}
tw-passage { max-width: 1120px; margin: 0 auto; }
tw-sidebar { display: none; }
tw-story { overflow: clip; }

/* Les tétons d'une brique, en rangée : un dégradé rond répété */
.tetons { background-image: radial-gradient(circle at 50% 55%, rgba(0,0,0,0.18) 0 4.2px, transparent 4.6px),
                            radial-gradient(circle at 50% 45%, currentColor 0 4.2px, transparent 4.6px);
          background-size: 14px 10px; background-repeat: repeat-x; }

/* Chapitres centrés : l'image en tête (carrée, avec son cadre de briques), puis le titre et le texte */
.page { max-width: 42em; margin: 0 auto; }
.cote { margin: 0 auto 1.6em; max-width: 34em; }
.cote img { display: block; width: 100%; height: auto; }
.page:not(:has(.cote)) .texte { padding-top: 2.2em; }

/* En-tête d'étape, comme les cartes de l'arbre : un bandeau cerclé de gris-bleu, le gros numéro dans une case de
   la couleur du sachet, le sachet et le titre à côté ; dessous, l'encadré bleu clair des pièces de l'étape */
.page { --sachet: var(--rouge); --sur-sachet: #fff; }
.etape { margin: 0.6em 0 1.3em; }
.sachet-2 { --sachet: var(--jaune); --sur-sachet: var(--encre); }
.sachet-3 { --sachet: var(--bleu); }
.sachet-4 { --sachet: var(--vert); }
.sachet-5 { --sachet: #f2780c; }
.bande { display: flex; align-items: stretch; border: 2.5px solid var(--notice-trait); border-radius: 10px; overflow: hidden; }
.bande .num { flex: none; display: flex; align-items: center; justify-content: center; min-width: 2.1em; padding: 0 0.25em;
  background: var(--sachet); color: var(--sur-sachet); font-family: "Jost", sans-serif; font-weight: 800; font-size: 3em; line-height: 1; }
.bande-texte { padding: 0.6em 1em 0.65em; }
.bande .sachet { display: block; font-family: "Jost", sans-serif; font-weight: 600; font-size: 0.82em; letter-spacing: 0.04em;
  color: var(--encre-douce); }
.pieces { display: inline-flex; flex-wrap: wrap; align-items: flex-end; gap: 0.35em 1.1em; margin: 0.7em 0 0; padding: 0.55em 0.9em;
  list-style: none; border-radius: 10px; background: var(--notice); }
.pieces li { font-size: 0.92em; }
.pieces li b { font-weight: 700; color: var(--bleu); }
.pieces li.avec-image { display: flex; flex-direction: column; align-items: center; gap: 0.1em; }
.pieces li.avec-image img { display: block; height: 3.4em; width: auto; }
.pieces li.avec-image b { font-size: 0.85em; }
.chapitre { text-align: left; margin: 0.1em 0 0; font-weight: 400; font-size: 1em; line-height: 1.1; }
.chapitre .titre {
  display: block;
  font-family: "Jost", sans-serif;
  font-weight: 700;
  font-size: 1.85em;
  line-height: 1.12;
  color: var(--encre);
}

/* Séparateur : trois briques 1 × 1, rouge, jaune et bleue, chacune avec son tenon */
.separateur { display: flex; align-items: flex-end; justify-content: center; gap: 0.4em; margin: 2em 0 1.4em; }
.separateur::before, .separateur::after { content: ""; width: 4em; height: 2px; margin: 0 0.7em 0.45em; background: var(--notice-trait); }
.separateur i { position: relative; display: block; width: 1em; height: 0.95em; border-radius: 3px;
  box-shadow: inset 0 -3px 0 rgba(0,0,0,0.22); }
.separateur i::before { content: ""; position: absolute; left: 50%; top: -0.3em; width: 0.56em; height: 0.34em;
  transform: translateX(-50%); border-radius: 2px 2px 0 0; background: inherit; box-shadow: inset 0 -1px 0 rgba(0,0,0,0.15); }
.separateur i:nth-child(1) { background: var(--rouge); }
.separateur i:nth-child(2) { background: var(--jaune); }
.separateur i:nth-child(3) { background: var(--bleu); }

/* Lien Couverture */
.retour { max-width: 1120px; margin: 0 auto 0.6em; text-align: left; }
.retour tw-link, .retour .enchantment-link, .lien-retour tw-link, .lien-retour .enchantment-link {
  font-family: "Jost", sans-serif; font-weight: 500; font-size: 0.95em; color: var(--encre-douce);
}
.retour tw-link::before, .lien-retour tw-link::before { content: "← "; }
.retour tw-link:hover, .lien-retour tw-link:hover { color: var(--bleu); }

tw-link, .enchantment-link { color: var(--bleu-fonce); font-weight: 500; text-decoration: none; }
tw-link:hover, .enchantment-link:hover { color: var(--bleu); }

/* Poursuis : en rouge, la flèche avance au survol */
.elan { text-align: center; margin-top: 0.4em; }
.elan tw-link, .elan .enchantment-link {
  font-family: "Jost", sans-serif; font-weight: 600; font-size: 1.3em; color: var(--bleu);
  text-decoration: none; transition: color 0.2s ease;
}
.elan tw-link::after, .elan .enchantment-link::after { content: ""; display: inline-block; width: 1.5em; height: 0.9em;
  margin-left: 0.45em; vertical-align: -0.05em; transition: transform 0.2s ease;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 40 24'%3E%3Cpath d='M2 8h22V2l14 10-14 10v-6H2z' fill='%23ffffff' stroke='%2322252b' stroke-width='2.4' stroke-linejoin='round'/%3E%3C/svg%3E") no-repeat center / contain; }
.elan tw-link:hover::after { transform: translateX(5px); }
.elan tw-link:hover { color: var(--bleu-fonce); }

/* La case du dé : un cadre bleu aux coins arrondis, les faces du dé sur de petites briques jaunes */
.de {
  display: flex;
  align-items: center;
  gap: 1.2em;
  margin-top: 1.8em;
  padding: 1em 1.3em 0.9em;
  border: 3px solid var(--bleu);
  border-radius: 10px;
  background: #fff;
}
.de-texte { flex: 1; min-width: 0; }
.de .consigne { display: block; font-family: "Jost", sans-serif; font-weight: 600; font-size: 1.08em;
  color: var(--encre); margin-bottom: 0.5em; }
.choix { display: flex; flex-direction: column; align-items: flex-start; gap: 0.45em; }
.tirage { display: inline-flex; align-items: center; gap: 0.8em; }
/* Les faces du dé, sur une petite brique jaune */
.tirage b {
  flex: none;
  min-width: 5.6em;
  padding: 0.12em 0.7em 0.08em;
  border-radius: 4px;
  background: var(--jaune);
  box-shadow: inset 0 -3px 0 rgba(0,0,0,0.15);
  font-family: "Jost", sans-serif;
  font-weight: 600;
  font-size: 0.88em;
  text-align: center;
  white-space: nowrap;
  color: var(--encre);
}
.de .choix tw-link, .de .choix .enchantment-link {
  font-family: "Jost", sans-serif; font-weight: 600; font-size: 1.05em; color: var(--bleu);
  white-space: nowrap; transition: color 0.2s ease;
}
.de .choix tw-link:hover { color: var(--bleu-fonce); }

/* La brique-dé : elle sautille tant qu'on ne l'a pas touchée, s'emboîte en tournant, puis montre le nombre */
.lancer { flex: none; width: 7.5em; display: flex; flex-direction: column; align-items: center; gap: 0.25em; }
.brique { position: relative; width: 4.6em; height: 4.6em; padding: 0; border: none; background: none; font: inherit; cursor: pointer; }
.brique .corps { position: absolute; inset: 0; background: url("BRIQUE_DE") no-repeat center / contain; }
.brique:not(.touche) .corps { animation: sautille 1.8s ease-in-out infinite; }
@keyframes sautille { 0%, 100% { transform: translateY(0); } 40% { transform: translateY(-7px); } 55% { transform: translateY(0) scaleY(0.95); } }
.brique:hover .corps { transform: rotate(-6deg); }
.brique.roule .corps { animation: tourne 0.9s cubic-bezier(.4, 0, .2, 1); }
@keyframes tourne { 0% { transform: rotate(0) translateY(0); } 50% { transform: rotate(200deg) translateY(-10px); } 100% { transform: rotate(360deg) translateY(0); } }
.brique .face { position: absolute; left: 0; right: 0; top: 18%; bottom: 6%; display: flex; align-items: center;
  justify-content: center; font-family: "Jost", sans-serif; font-weight: 700; font-size: 2.5em; color: #fff;
  opacity: 0; transition: opacity 0.3s ease 0.1s; }
.brique.montre .face { opacity: 1; }
.lancer .aide { font-family: "Jost", sans-serif; font-weight: 500; font-size: 0.82em; color: var(--encre-douce); }
.resultat { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }

/* Fin */
.fin { text-align: center; margin-top: 0.4em; }
.fin .bravo { display: block; margin: -0.2em 0 1em; font-weight: 600; font-size: 1.15em; color: var(--encre-douce); }
.fin .mot-fin { display: block; font-family: "Jost", sans-serif; font-weight: 700; font-size: 3.4em; line-height: 1;
  color: var(--encre); margin-bottom: 0.4em; }
.secondaires { display: flex; flex-wrap: wrap; justify-content: center; gap: 0.5em 1.6em; }
.secondaires tw-link, .secondaires .enchantment-link { font-family: "Jost", sans-serif; font-weight: 600;
  font-size: 1.05em; color: var(--bleu); text-decoration: underline 2px var(--notice-trait); text-underline-offset: 0.3em; }

/* Couverture, sans défilement : le titre dans un encadré de notice, le résumé, le bouton bleu */
tw-story:has(.garde) { padding-top: 0; padding-bottom: 0; }
.garde { position: relative; min-height: 100vh; box-sizing: border-box; padding: 4vh 0 9vh;
  display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;
  gap: clamp(0.8em, 2.4vh, 1.3em); }
.garde .boite { position: relative; display: flex; flex-direction: column; align-items: center; gap: 0.45em;
  min-width: min(34em, 92vw); padding: 1.3em 3em 0; border: 3px solid var(--encre); border-radius: 8px; overflow: hidden; }
.garde .boite-haut { position: absolute; left: 0; right: 0; top: 0; display: flex; justify-content: space-between; }
.garde .set { padding: 0.15em 0.7em; background: var(--encre); color: #fff; font-weight: 800; font-size: 1.05em;
  letter-spacing: 0.06em; border-bottom-right-radius: 6px; }
.garde .age { padding: 0.15em 0.7em; background: var(--jaune); color: var(--encre); font-weight: 800; font-size: 1.05em;
  border-bottom-left-radius: 6px; }
.garde .boite .surtitre { margin-top: 2.6em; }
.garde .boite-bas { align-self: stretch; display: flex; justify-content: center; gap: 1.8em; margin-top: 0.8em;
  padding: 0.55em 1em; background: var(--notice); margin-left: -3em; margin-right: -3em; font-size: 0.95em; color: var(--encre-douce); }
.garde .boite-bas b { color: var(--encre); font-weight: 800; }
.garde .surtitre { font-family: "Jost", sans-serif; font-weight: 600; font-size: 0.85em; letter-spacing: 0.18em;
  text-transform: uppercase; color: var(--encre-douce); }
.garde .grand-titre { font-family: "Jost", sans-serif; font-weight: 800; font-size: clamp(2.8em, 9vh, 4.6em);
  line-height: 1; color: var(--encre); }
.garde .grand-titre span { display: block; font-size: 0.6em; color: var(--bleu); }
.garde .nom-auteur { font-family: "Jost", sans-serif; font-weight: 500; font-size: 1.15em; color: var(--encre-douce); }
.garde .synopsis { max-width: 34em; font-size: clamp(0.92em, 2.1vh, 1.05em); line-height: 1.65; }
.garde .synopsis p { margin: 0.5em 0; }
.garde .commencer tw-link, .garde .commencer .enchantment-link {
  display: inline-block; padding: 0.35em 1.4em 0.32em; border-radius: 4px; background: var(--bleu);
  font-family: "Jost", sans-serif; font-weight: 700; font-size: 1.5em; color: #fff; transition: background 0.15s ease;
}
.garde .commencer tw-link:hover { background: var(--bleu-fonce); color: #fff; }
/* Sous le bouton, en petit dans le bouton : « commencer l'histoire » */
.garde .commencer tw-link::after, .garde .commencer .enchantment-link::after { content: "commencer l’histoire"; display: block;
  margin-top: 0.1em; font-weight: 500; font-size: 0.52em; letter-spacing: 0.08em; text-transform: uppercase; opacity: 0.85; }
.garde .secondaires { gap: 0; font-size: 0.95em; }
.garde .secondaires tw-link, .garde .secondaires .enchantment-link { text-decoration: none; color: var(--encre-douce); }
.garde .secondaires tw-link:hover { color: var(--bleu); }
.garde .secondaires .point { margin: 0 0.8em; color: var(--notice-trait); }
.garde .mention { position: absolute; left: 0; right: 0; bottom: 1.5vh; font-size: 0.8em; font-style: italic;
  color: var(--encre-douce); }

/* Page de l'arbre */
.arbre .lien-retour { display: block; font-size: 0.9em; }
.arbre-tete { text-align: center; margin: 0.5em 0 1.5em; }
.arbre h1 { margin: 0; font-family: "Jost", sans-serif; font-weight: 800; font-size: 2.3em; color: var(--encre); }
.arbre .arbre-sous-titre { display: block; color: var(--encre-douce); margin-top: 0.3em; }
.arbre img { display: block; width: 100%; max-width: 900px; height: auto; margin: 0 auto; }

/* Page « Comment est née cette histoire » */
.contexte { max-width: 40em; margin: 1em auto 0; text-align: center; }
.contexte .lien-retour { display: block; text-align: left; margin-bottom: 1em; }
.contexte h1 { font-family: "Jost", sans-serif; font-weight: 700; font-size: 2.2em; line-height: 1.15; color: var(--encre); margin: 1em 0 0; }
.contexte-texte { text-align: left; }
.citation { margin: 1.8em auto; max-width: 28em; text-align: center; font-family: "Jost", sans-serif; font-weight: 500;
  font-size: 1.3em; line-height: 1.4; color: var(--bleu-fonce); }
.citation .source { display: block; margin-top: 0.5em; font-size: 0.6em; letter-spacing: 0.12em; text-transform: uppercase; color: var(--encre-douce); }
.dessins { display: flex; justify-content: center; align-items: flex-end; gap: 2.5em; margin: 0.6em auto 0.4em; }
.dessins figure { margin: 0; }
.dessins img { display: block; height: 8em; width: auto; margin: 0 auto; }
.dessins figcaption { margin-top: 0.4em; font-family: "Jost", sans-serif; font-weight: 600; font-size: 0.9em; color: var(--bleu-fonce); }
.table-fiches { margin: 2.6em auto 0; }
.table-fiches .titre-table { display: block; font-family: "Jost", sans-serif; font-weight: 600; font-size: 1.3em; margin-bottom: 1.2em; }
.miniatures { display: flex; justify-content: center; align-items: flex-start; flex-wrap: wrap; gap: 1.6em; }
.miniatures figure { margin: 0; }
.miniatures figcaption { margin-top: 0.7em; color: var(--encre-douce); }
.miniature { display: block; padding: 0; border: none; background: none; cursor: zoom-in; }
.miniature img { display: block; height: 13em; width: auto; border: 2px solid var(--notice-trait); border-radius: 6px; transition: transform 0.2s ease; }
.miniature:hover img { transform: scale(1.04); }
.contexte .credits { display: block; margin-top: 2em; font-size: 0.9em; color: var(--encre-douce); }
.contexte .avertissement { display: block; margin-top: 0.8em; font-size: 0.82em; font-style: italic; color: var(--encre-douce); }
.contexte .secondaires { margin-top: 1.4em; }
.agrandi { position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center;
  padding: 2vh 2vw; background: rgba(34, 37, 43, 0.88); cursor: zoom-out; }
.agrandi img { max-width: 100%; max-height: 96vh; }

@media (max-width: 600px) {
  tw-story { font-size: 1.03em; padding: 0.8em 1em 3em; }
  .bande .num { font-size: 2.3em; }
  .chapitre .titre { font-size: 1.5em; }
  .garde .boite { padding: 1.3em 1.2em 0; }
  .garde .boite-bas { gap: 0.9em; margin-left: -1.2em; margin-right: -1.2em; flex-wrap: wrap; }
  .chapitre .titre { font-size: 1.9em; }
  .de { flex-direction: column-reverse; align-items: stretch; }
  .lancer { align-self: center; width: auto; }
  .tirage { flex-wrap: wrap; }
  .miniature img { height: 10em; }
  .garde .mention { position: static; }
}
""".replace("ROUGE", ROUGE).replace("JAUNE", JAUNE).replace("BLEU", BLEU).replace("VERT", VERT).replace("BRIQUE_DE", BRIQUE_DE) + CSS_BRIQUES

SEPARATEUR = '<div class="separateur"><i></i><i></i><i></i></div>'

DE_VIRTUEL = (
    '<div class="lancer"><button class="brique" type="button" aria-label="Toucher la brique pour lancer le dé">'
    '<span class="corps"></span><span class="face"></span></button>'
    '<span class="aide">touche la brique</span>'
    '<span class="resultat" aria-live="polite"></span></div>'
)

SCRIPT = """
// La brique tourne, s'emboîte et montre le nombre tiré ; elle ne choisit jamais à la place du lecteur
document.addEventListener('click', function (evenement) {
  var brique = evenement.target.closest('.brique');
  if (!brique || brique.classList.contains('roule')) return;
  var resultat = brique.parentNode.querySelector('.resultat');
  var face = 1 + Math.floor(Math.random() * 6);
  brique.classList.add('touche');
  brique.classList.remove('montre');
  brique.classList.add('roule');
  resultat.textContent = '';
  setTimeout(function () {
    brique.classList.remove('roule');
    brique.querySelector('.face').textContent = face;
    brique.classList.add('montre');
    resultat.textContent = 'La brique montre ' + face + '.';
  }, 900);
});

// Page de contexte : une miniature s'ouvre en grand, un clic referme
document.addEventListener('click', function (evenement) {
  var ouvert = document.querySelector('.agrandi');
  if (ouvert) { ouvert.remove(); return; }
  var miniature = evenement.target.closest('.miniature');
  if (!miniature) return;
  var fond = document.createElement('div');
  fond.className = 'agrandi';
  var image = document.createElement('img');
  image.src = miniature.querySelector('img').src;
  image.alt = miniature.querySelector('img').alt;
  fond.appendChild(image);
  document.body.appendChild(fond);
});
document.addEventListener('keydown', function (evenement) {
  var ouvert = document.querySelector('.agrandi');
  if (ouvert && evenement.key === 'Escape') ouvert.remove();
});
"""


def e(texte):
    return html.escape(texte, quote=True)


def lire_chapitres():
    blocs = re.split(r"^## ", TEXTE.read_text(encoding="utf-8"), flags=re.M)[1:]
    chapitres = []
    for bloc in blocs:
        lignes = bloc.strip().split("\n")
        numero, titre = lignes[0].strip().split(". ", 1)
        paragraphes = [p.strip() for p in "\n".join(lignes[1:]).split("\n\n") if p.strip()]
        chapitres.append({"nom": numero, "numero": numero, "titre": titre, "paragraphes": paragraphes})
    return chapitres


def lien(texte, cible):
    return f"[[{texte}->{cible}]]"


# Les renvois du texte de Manon, tous affichés « Poursuis au chapitre X »
TIRAGE = re.compile(r"^(Un nombre pair|Un nombre impair|Un résultat de [\d, ou]+) : poursuis au chapitre (\d+)\.?$")
RENVOI = re.compile(r"^Poursuis au chapitre (\d+)\.?$")


def faces(libelle):
    """« Un nombre pair » → « Pair », « Un résultat de 1, 2 ou 3 » → « 1, 2 ou 3 »."""
    if libelle.startswith("Un résultat de "):
        return libelle[len("Un résultat de "):]
    return libelle.replace("Un nombre ", "").capitalize()


def lire_choix(ch):
    """Rend (corps, consigne, tirages, renvoi, fin) pour un chapitre."""
    corps, consigne, tirages, renvoi, fin = [], None, [], None, False
    for p in ch["paragraphes"]:
        if p.startswith("- "):
            for ligne in p.split("\n"):
                ligne = ligne[2:].strip()
                if m := TIRAGE.match(ligne):
                    tirages.append((faces(m[1]), m[2]))
                elif m := RENVOI.match(ligne):
                    renvoi = m[1]
                else:
                    raise ValueError(f"Choix illisible dans {ch['nom']} : {ligne}")
        elif p == "FIN":
            fin = True
        elif p.startswith("**") and p.endswith("**"):
            consigne = p[2:-2].strip()
        else:
            corps.append(p)
    return corps, consigne, tirages, renvoi, fin


# Les parties de l'histoire sont les sachets numérotés d'une boîte LEGO
SACHETS = [(0, 3, "La chute"), (4, 7, "L’équipe"), (8, 11, "Le tournoi"), (12, 19, "La finale"), (20, 23, "Le retour")]
# Les pièces de chaque étape, revues à la main : (nombre, nom). Si images/pieces/<nom en minuscules, tirets>.png
# existe, l'image remplace le nom (encadré des pièces d'une notice : l'image et « 1× » dessous).
PIECES = {
    0: [(1, "Kylian en civil"), (1, "vitrine vide"), (1, "étiquette « Jamais remportée »"), (1, "trappe")],
    1: [(1, "Kylian"), (1, "banderole « Lego City cherche ses joueurs »"), (3, "briques")],
    2: [(1, "poubelle"), (1, "petit chien"), (1, "blanchisseur"), (1, "machine à laver"), (1, "Messi"), (1, "Ronaldo")],
    3: [(1, "trampoline"), (1, "camion de glaces"), (1, "ballon"), (1, "panneau d’affichage"), (1, "Messi"), (1, "Ronaldo")],
    4: [(1, "serviette « Le Real de Lego City »"), (1, "pompier"), (1, "policière"), (1, "astronaute"), (1, "pirate"),
        (1, "boulangère")],
    5: [(1, "caisse de briques"), (1, "grue"), (1, "poteau de but"), (1, "maillot blanc"), (1, "banderole « Allez le Real ! »")],
    6: [(1, "Zidane"), (1, "ballon"), (1, "plot d’entraînement")],
    7: [(1, "entraîneur de l’OM"), (1, "tableau à flèches"), (1, "sifflet"), (1, "casque d’astronaute")],
    8: [(1, "banderole « Allez le Real ! »"), (1, "perruque"), (1, "camion de pompiers"), (1, "joueur adverse")],
    9: [(1, "astronaute"), (1, "pompier"), (1, "ballon")],
    10: [(1, "Ronaldo"), (1, "joueur adverse"), (1, "ballon")],
    11: [(1, "astronaute"), (1, "ballon"), (1, "joueur adverse")],
    12: [(1, "coupe"), (1, "brioche"), (2, "silhouette"), (1, "grand sac")],
    13: [(1, "Kylian"), (2, "silhouette"), (1, "porte")],
    14: [(1, "Kylian"), (1, "Messi"), (1, "Ronaldo"), (1, "porte")],
    15: [(1, "chaussettes puantes"), (1, "casier"), (1, "blanchisseur"), (1, "pirate")],
    16: [(1, "bombe de déodorant"), (1, "camion de pompiers"), (1, "lance à incendie"), (1, "car du Bricksenal FC")],
    17: [(1, "brioche"), (1, "gourde"), (1, "casque d’astronaute"), (1, "ballon")],
    18: [(1, "Kylian"), (1, "ballon"), (1, "joueur adverse")],
    19: [(1, "Messi"), (1, "ballon"), (1, "joueur adverse")],
    20: [(1, "coupe"), (1, "maire"), (1, "brioche")],
    21: [(1, "estrade en briques"), (1, "chapeau de pirate"), (1, "astronaute")],
    22: [(1, "Kylian"), (1, "habitant"), (1, "projecteur")],
    23: [(1, "gardien du musée"), (1, "minuscule coupe"), (1, "crayon"), (1, "étiquette « Jamais remportée »")],
}


def fichier_piece(nom):
    """« camion de pompiers » → images/pieces/camion-de-pompiers.png"""
    import unicodedata
    base = unicodedata.normalize("NFD", nom.lower())
    base = "".join(c for c in base if unicodedata.category(c) != "Mn")
    return "images/pieces/" + re.sub(r"[^a-z0-9]+", "-", base).strip("-") + ".png"


def pieces_html(cle):
    elements = []
    for nombre, nom in PIECES.get(cle, []):
        image = fichier_piece(nom)
        if (RACINE / image).exists():
            elements.append(f'<li class="avec-image"><img src="{image}" alt="{nom}"><b>{nombre}×</b></li>')
        else:
            elements.append(f'<li><b>{nombre}×</b> {nom}</li>')
    return "".join(elements)


def sachet(cle):
    for numero, (debut, fin, nom) in enumerate(SACHETS, start=1):
        if debut <= cle <= fin:
            return numero, nom
    return 1, SACHETS[0][2]


def illustration(nom):
    return "prologue" if nom == "Prologue" else f"chapitre-{int(nom.split()[-1]):02d}"


def passage_chapitre(ch):
    corps, consigne, tirages, renvoi, fin = lire_choix(ch)
    poursuis = lambda n: lien(f"Poursuis au chapitre {n}", f"Chapitre {n}")
    image = RACINE / f"images/chapitres/{illustration(ch['nom'])}.jpg"
    cote = f'<div class="cote"><img src="images/chapitres/{image.name}" alt="{ch["titre"]}"></div>' if image.exists() else ""

    suite = []
    if tirages:
        lignes = "".join(f'<span class="tirage"><b>{f}</b><span>{poursuis(n)}</span></span>' for f, n in tirages)
        suite.append(f'<div class="de"><div class="de-texte"><span class="consigne">{consigne}</span>'
                     f'<div class="choix">{lignes}</div></div>{DE_VIRTUEL}</div>')
    else:
        suite.append(SEPARATEUR)
        if renvoi:
            suite.append(f'<div class="elan">{poursuis(renvoi)}</div>')
    if fin:
        suite.append('<div class="fin"><span class="mot-fin">Fin</span><span class="bravo">Ton modèle est terminé.</span>'
                     f'<div class="secondaires">{lien("Comment est née cette histoire", "Comment est née cette histoire")}'
                     f'{lien("Relire depuis le début", "Prologue")}</div></div>')
    cle = 0 if ch["nom"] == "Prologue" else int(ch["nom"].split()[-1])
    n_sachet, nom_sachet = sachet(cle)
    liste = pieces_html(cle)
    numero = ("" if ch["nom"] == "Prologue"
              else f'<span class="num" aria-label="{ch["numero"]}">{ch["numero"].split()[-1]}</span>')
    entete = (f'<div class="etape"><div class="bande">{numero}<div class="bande-texte">'
              f'<span class="sachet">Sachet {n_sachet} · {nom_sachet}</span>'
              f'<h1 class="chapitre"><span class="titre">{ch["titre"]}</span></h1></div></div>'
              + (f'<ul class="pieces">{liste}</ul>' if liste else "") + '</div>')
    texte = (f'<div class="texte">{entete}'
             + "\n\n".join(corps) + "".join(suite) + "</div>")
    return f'<div class="page sachet-{n_sachet}">{cote}{texte}</div>'


def minutes_de_lecture(mots_par_minute=120):
    """Temps de lecture d'un chemin moyen, du prologue à la fin, arrondi à 5 minutes (un enfant de 9 ou 10 ans
    lit environ 120 mots par minute)."""
    chapitres = {ch["nom"]: ch for ch in lire_chapitres()}

    def longueurs(nom):
        corps, _, tirages, renvoi, _ = lire_choix(chapitres[nom])
        mots = len(" ".join(corps).split())
        cibles = [f"Chapitre {n}" for _, n in tirages] + ([f"Chapitre {renvoi}"] if renvoi else [])
        return [mots + m for c in cibles for m in longueurs(c)] or [mots]
    chemins = longueurs("Prologue")
    return max(5, round(sum(chemins) / len(chemins) / mots_par_minute / 5) * 5)


def passage_garde():
    resume = "".join(f"<p>{p}</p>" for p in SYNOPSIS.split("\n\n"))
    etapes = len(lire_chapitres()) - 1
    minutes = minutes_de_lecture()
    return (
        '<div class="garde">'
        '<div class="boite"><div class="boite-haut"><span class="set">2810</span><span class="age">6+</span></div>'
        '<span class="surtitre">Une histoire dont le lecteur est le héros</span>'
        '<span class="grand-titre">Le Real<span>de Lego City</span></span>'
        f'<span class="nom-auteur">par {AUTEURS}</span>'
        f'<div class="boite-bas"><span><b>{etapes}</b> étapes</span><span><b>{len(SACHETS)}</b> sachets</span>'
        f'<span><b>{minutes}</b> minutes de lecture</span></div></div>'
        f'<div class="synopsis">{resume}</div>'
        f'<div class="commencer">{lien("Ouvrir le premier sachet", "Prologue")}</div>'
        f'<div class="secondaires">{lien("Comment est née cette histoire", "Comment est née cette histoire")}'
        f'<span class="point">·</span>{lien("L’arbre de l’histoire", "L’arbre de l’histoire")}</div>'
        f'<span class="mention">{AVERTISSEMENT_COURT}</span></div>'
    )


def version_arbre():
    chemin = RACINE / "images" / "arbre.svg"
    return hashlib.md5(chemin.read_bytes()).hexdigest()[:8] if chemin.exists() else "0"


def passage_arbre():
    return (
        f'<div class="arbre"><span class="lien-retour">{lien("Couverture", "Page de garde")}</span>'
        f'<div class="arbre-tete"><h1>{TITRE}</h1>'
        f'<span class="arbre-sous-titre">Tous les chemins de l’histoire imaginée par {AUTEURS}</span></div>'
        f'<img src="images/arbre.svg?v={version_arbre()}" alt="L’arbre de toutes les branches de l’histoire"></div>'
    )


def miniature(fichier, legende, description):
    return (f'<figure><button class="miniature" type="button" aria-label="Agrandir {description}">'
            f'<img src="images/fiches/{fichier}" alt="{description}"></button>'
            f'<figcaption>{legende}</figcaption></figure>')


def dessin(fichier, legende):
    return (f'<figure><img src="images/dessins/{fichier}" alt="{legende}, dessiné par Ernest et Abel">'
            f'<figcaption>{legende}</figcaption></figure>')


def passage_contexte():
    return (
        '<div class="contexte"><span class="lien-retour">[[Couverture->Page de garde]]</span>\n'
        '<div class="dessins">'
        + dessin("kylian.png", "Kylian") + dessin("messi.png", "Messi") + dessin("ronaldo.png", "Ronaldo")
        + '</div>'
        f'<h1>Comment est née cette histoire</h1>{SEPARATEUR}'
        '<div class="contexte-texte">'
        + "\n\n".join(CONTEXTE[:4])
        + f'<div class="citation">« {CITATION} »<span class="source">Ernest et Abel, sur leur fiche récit</span></div>'
        + CONTEXTE[4]
        + '</div><div class="table-fiches"><span class="titre-table">Les fiches de l’atelier</span>'
        '<div class="miniatures">'
        + miniature("fiche_recit.jpg", "Le récit", "la fiche récit d’Ernest et d’Abel")
        + miniature("fiche_personnage_kylian.jpg", "Une fiche personnage", "la fiche personnage de Kylian")
        + miniature("fiche_situation_1.jpg", "Une fiche à embranchement", "la fiche situation n° 1, avec ses choix au dé")
        + '</div></div>'
        + '<span class="credits">Une histoire librement inspirée du récit d’Ernest et d’Abel.\nRéalisation du livre : '
        "Laboratoire d’Aix-périmentation et de Bidouille.</span>"
        + f'<span class="avertissement">{AVERTISSEMENT}</span>'
        + f'<div class="secondaires">{lien("Commencer le livre", "Prologue")}</div>\n</div>'
    )


def construire():
    modele = SORTIE.read_text(encoding="utf-8")
    debut = modele[: modele.index("<tw-storydata")]
    moteur = modele[modele.index("</tw-storydata>"):]
    if NOINDEX not in debut:
        debut = debut.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + NOINDEX)
    debut = re.sub(r"<link rel=\"(?:icon|apple-touch-icon)\"[^>]*>", "", debut)
    debut = debut.replace('<meta charset="utf-8">', '<meta charset="utf-8">\n' + FAVICON)
    debut = re.sub(r"<title>[^<]*</title>", f"<title>{TITRE}</title>", debut)
    lire = re.compile(r"JavaScript (?:needs to be enabled to play|doit être activé pour lire) [^<.]*\.")
    debut = lire.sub(f"JavaScript doit être activé pour lire {TITRE}.", debut)
    moteur = lire.sub(f"JavaScript doit être activé pour lire {TITRE}.", moteur)

    passages = [
        ("Bouton couverture", "header",
         '(unless: (a: "Page de garde", "Comment est née cette histoire", "L’arbre de l’histoire") contains (passage:)\'s name)'
         '[<div class="retour">[[Couverture->Page de garde]]</div>]'),
        ("Page de garde", "", passage_garde()),
        ("Comment est née cette histoire", "", passage_contexte()),
        ("L’arbre de l’histoire", "", passage_arbre()),
    ]
    for ch in lire_chapitres():
        passages.append((ch["nom"], "", passage_chapitre(ch)))

    # Espaces insécables de la typographie française
    insecables = [("« ", "« "), (" »", " »"), (" :", " :"), (" ?", " ?"),
                  (" !", " !"), (" ;", " ;")]
    for i, (nom, tags, contenu) in enumerate(passages):
        if tags != "header":
            contenu = contenu.replace("'", "’")
            for avant, apres in insecables:
                contenu = contenu.replace(avant, apres)
            passages[i] = (nom, tags, contenu)

    noms = {p[0] for p in passages}
    for nom, _, contenu in passages:
        for cible in re.findall(r"->([^\]]+)\]\]", contenu):
            assert cible in noms, f"Lien cassé dans {nom} : {cible}"

    xml = [f'<tw-storydata name="{e(TITRE)}" startnode="2" creator="Twine" creator-version="2.12.1" '
           f'format="Harlowe" format-version="3.3.9" ifid="{str(uuid.uuid5(uuid.NAMESPACE_URL, TITRE)).upper()}" '
           'options="" tags="" zoom="1" hidden>',
           f'<style role="stylesheet" id="twine-user-stylesheet" type="text/twine-css">{CSS}</style>',
           '<script role="script" id="twine-user-script" type="text/twine-javascript">' + SCRIPT + '</script>']
    for pid, (nom, tags, contenu) in enumerate(passages, start=1):
        xml.append(f'<tw-passagedata pid="{pid}" name="{e(nom)}" tags="{tags}" '
                   f'position="{pid * 150},0" size="100,100">{e(contenu)}</tw-passagedata>')
    SORTIE.write_text(debut + "".join(xml) + moteur, encoding="utf-8")
    print(f"{SORTIE} : {len(passages)} passages")


if __name__ == "__main__":
    construire()
