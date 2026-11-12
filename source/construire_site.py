#!/usr/bin/env python3
"""Construit index.html du « Real de Lego City » à partir de source/texte.md.

Le moteur Harlowe est conservé tel quel dans index.html : seules les pages et la feuille de style du livre
sont régénérées.

Mise en page propre au livre d'Ernest et d'Abel, tirée des images de Manon : le papier crème des
illustrations, leur cadre de plaques grises à tétons, les couleurs franches des briques (rouge, jaune, bleu,
vert) et les petits objets dessinés au crayon. Le dé est une brique rouge 2 × 2 ; les étiquettes, les cases
et le séparateur sont faits de briques.

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


# La brique rouge 2 × 2 qui sert de dé : deux tétons visibles, vue de face
BRIQUE_DE = svg(
    '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100">'
    f'<rect x="20" y="8" width="20" height="14" rx="3" fill="#a80c0e"/><rect x="60" y="8" width="20" height="14" rx="3" fill="#a80c0e"/>'
    f'<rect x="20" y="6" width="20" height="9" rx="4.5" fill="{ROUGE}"/><rect x="60" y="6" width="20" height="9" rx="4.5" fill="{ROUGE}"/>'
    f'<rect x="6" y="20" width="88" height="74" rx="7" fill="#a80c0e"/>'
    f'<rect x="6" y="18" width="88" height="68" rx="7" fill="{ROUGE}"/>'
    '<rect x="12" y="23" width="76" height="5" rx="2.5" fill="#ffffff" opacity="0.28"/>'
    '</svg>')

CSS = """
@font-face { font-family: "Fredoka"; font-weight: 300 700; font-display: swap; src: url("fonts/Fredoka.woff2") format("woff2"); }
@font-face { font-family: "Lexend"; font-weight: 300 700; font-display: swap; src: url("fonts/Lexend.woff2") format("woff2"); }

/* Couleurs prises aux images : le crème du papier, le gris des plaques à tétons, les briques */
:root {
  --papier: #f8f4ea;
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
  font-family: "Lexend", "Trebuchet MS", sans-serif;
  font-weight: 350;
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

/* Le numéro du chapitre : une plaque jaune 1 × 6, ses tétons au-dessus */
.chapitre { text-align: center; margin: 0 0 1.2em; font-weight: 400; font-size: 1em; line-height: 1.1; }
.chapitre .numero {
  position: relative;
  display: inline-block;
  margin: 10px 0 0.7em;
  padding: 0.28em 1.1em 0.22em;
  border-radius: 5px;
  background: var(--jaune);
  box-shadow: inset 0 -3px 0 rgba(0,0,0,0.16);
  font-family: "Fredoka", sans-serif;
  font-weight: 600;
  font-size: 0.85em;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  color: var(--encre);
}
.chapitre .numero::before {
  content: "";
  position: absolute;
  left: 10px; right: 10px; top: -7px; height: 8px;
  color: var(--jaune);
  background-image: radial-gradient(ellipse 5px 4px at 50% 100%, #d6a90c 0 98%, transparent 100%),
                    radial-gradient(ellipse 5px 4px at 50% 60%, var(--jaune) 0 98%, transparent 100%);
  background-size: 16px 8px;
  background-position: center;
  background-repeat: repeat-x;
}
.chapitre .titre {
  display: block;
  font-family: "Fredoka", sans-serif;
  font-weight: 600;
  font-size: 2.3em;
  line-height: 1.12;
  color: var(--encre);
}

/* Séparateur : trois briques 1 × 1, rouge, jaune et bleue, entre deux traits de crayon */
.separateur { display: flex; align-items: flex-end; justify-content: center; gap: 0.35em; margin: 1.8em 0 1.4em; }
.separateur::before, .separateur::after { content: ""; width: 4em; height: 1.5px; margin: 0 0.6em 0.35em;
  background: var(--plaque-fonce); border-radius: 1px; }
.separateur i { position: relative; display: block; width: 0.9em; height: 0.75em; border-radius: 2px;
  box-shadow: inset 0 -2px 0 rgba(0,0,0,0.2); }
.separateur i::before { content: ""; position: absolute; left: 50%; top: -0.22em; width: 0.5em; height: 0.26em;
  transform: translateX(-50%); border-radius: 2px 2px 0 0; background: inherit; }
.separateur i:nth-child(1) { background: var(--rouge); }
.separateur i:nth-child(2) { background: var(--jaune); }
.separateur i:nth-child(3) { background: var(--bleu); }

/* Lien Couverture */
.retour { max-width: 1120px; margin: 0 auto 0.6em; text-align: left; }
.retour tw-link, .retour .enchantment-link, .lien-retour tw-link, .lien-retour .enchantment-link {
  font-family: "Fredoka", sans-serif; font-weight: 500; font-size: 0.95em; color: var(--encre-douce);
}
.retour tw-link::before, .lien-retour tw-link::before { content: "← "; }
.retour tw-link:hover, .lien-retour tw-link:hover { color: var(--bleu); }

tw-link, .enchantment-link { color: var(--bleu-fonce); font-weight: 500; text-decoration: none; }
tw-link:hover, .enchantment-link:hover { color: var(--bleu); }

/* Poursuis : en rouge, la flèche avance au survol */
.elan { text-align: center; margin-top: 0.4em; }
.elan tw-link, .elan .enchantment-link {
  font-family: "Fredoka", sans-serif; font-weight: 600; font-size: 1.3em; color: var(--rouge);
  text-decoration: none; transition: color 0.2s ease;
}
.elan tw-link::after, .elan .enchantment-link::after { content: "→"; display: inline-block; margin-left: 0.35em;
  color: var(--bleu); transition: transform 0.2s ease; }
.elan tw-link:hover::after { transform: translateX(5px); }
.elan tw-link:hover { color: var(--rouge-fonce); }

/* La case du dé : une plaque blanche cerclée de gris, comme le cadre des images, ses tétons sur le bord haut */
.de {
  position: relative;
  display: flex;
  align-items: center;
  gap: 1.2em;
  margin-top: 2em;
  padding: 1em 1.3em 0.9em;
  border: 3px solid var(--plaque);
  border-radius: 10px;
  background: #fff;
  box-shadow: 0 4px 0 var(--plaque-fonce);
}
.de::before {
  content: "";
  position: absolute;
  left: 14px; right: 14px; top: -10px; height: 9px;
  background-image: radial-gradient(ellipse 5.5px 4.5px at 50% 100%, var(--plaque-fonce) 0 98%, transparent 100%),
                    radial-gradient(ellipse 5.5px 4.5px at 50% 65%, var(--plaque) 0 98%, transparent 100%);
  background-size: 22px 9px;
  background-repeat: repeat-x;
}
.de-texte { flex: 1; min-width: 0; }
.de .consigne { display: block; font-family: "Fredoka", sans-serif; font-weight: 600; font-size: 1.08em;
  color: var(--encre); margin-bottom: 0.5em; }
.choix { display: flex; flex-direction: column; align-items: flex-start; gap: 0.45em; }
.tirage { display: inline-flex; align-items: center; gap: 0.8em; }
/* Les faces du dé, sur une petite brique rouge 1 × 2 */
.tirage b {
  flex: none;
  min-width: 5.6em;
  padding: 0.12em 0.7em 0.08em;
  border-radius: 4px;
  background: var(--rouge);
  box-shadow: inset 0 -3px 0 rgba(0,0,0,0.2);
  font-family: "Fredoka", sans-serif;
  font-weight: 600;
  font-size: 0.88em;
  text-align: center;
  white-space: nowrap;
  color: #fff;
}
.de .choix tw-link, .de .choix .enchantment-link {
  font-family: "Fredoka", sans-serif; font-weight: 600; font-size: 1.05em; color: var(--bleu);
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
  justify-content: center; font-family: "Fredoka", sans-serif; font-weight: 700; font-size: 2.5em; color: #fff;
  opacity: 0; transition: opacity 0.3s ease 0.1s; }
.brique.montre .face { opacity: 1; }
.lancer .aide { font-family: "Fredoka", sans-serif; font-weight: 500; font-size: 0.82em; color: var(--encre-douce); }
.resultat { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }

/* Fin */
.fin { text-align: center; margin-top: 0.4em; }
.fin .mot-fin { display: block; font-family: "Fredoka", sans-serif; font-weight: 700; font-size: 3.4em; line-height: 1;
  color: var(--rouge); margin-bottom: 0.4em; }
.secondaires { display: flex; flex-wrap: wrap; justify-content: center; gap: 0.5em 1.6em; }
.secondaires tw-link, .secondaires .enchantment-link { font-family: "Fredoka", sans-serif; font-weight: 600;
  font-size: 1.05em; color: var(--bleu); text-decoration: underline 2px var(--jaune); text-underline-offset: 0.3em; }

/* Couverture, sans défilement : le titre en briques, le résumé, les boutons ; la mention en bas de page */
tw-story:has(.garde) { padding-top: 0; padding-bottom: 0; }
.garde { position: relative; min-height: 100vh; box-sizing: border-box; padding: 5vh 0 9vh;
  display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center;
  gap: clamp(0.8em, 2.4vh, 1.4em); }
.garde .surtitre { font-family: "Fredoka", sans-serif; font-weight: 600; font-size: 0.9em; letter-spacing: 0.18em;
  text-transform: uppercase; color: var(--bleu); }
.garde .grand-titre { font-family: "Fredoka", sans-serif; font-weight: 700; font-size: clamp(2.8em, 10vh, 5em);
  line-height: 0.98; color: var(--rouge); }
.garde .grand-titre span { display: block; font-size: 0.62em; color: var(--bleu); }
.garde .nom-auteur { font-family: "Fredoka", sans-serif; font-weight: 500; font-size: 1.2em; color: var(--encre-douce); }
.garde .synopsis { max-width: 34em; font-size: clamp(0.9em, 2.1vh, 1.02em); line-height: 1.65; }
.garde .synopsis p { margin: 0.5em 0; }
.garde .commencer tw-link, .garde .commencer .enchantment-link {
  display: inline-block; padding: 0.35em 1.3em 0.3em; border-radius: 8px; background: var(--rouge);
  box-shadow: inset 0 -5px 0 rgba(0,0,0,0.2); font-family: "Fredoka", sans-serif; font-weight: 700; font-size: 1.6em;
  color: #fff; transition: transform 0.15s ease;
}
.garde .commencer tw-link:hover { transform: translateY(-2px); color: #fff; }
.garde .secondaires { gap: 0; font-size: 0.95em; }
.garde .secondaires tw-link, .garde .secondaires .enchantment-link { text-decoration: none; color: var(--encre-douce); }
.garde .secondaires tw-link:hover { color: var(--bleu); }
.garde .secondaires .point { margin: 0 0.8em; color: var(--rouge); }
.garde .mention { position: absolute; left: 0; right: 0; bottom: 1.5vh; font-size: 0.78em; font-style: italic;
  color: var(--encre-douce); }

/* Page de l'arbre */
.arbre .lien-retour { display: block; font-size: 0.9em; }
.arbre-tete { text-align: center; margin: 0.5em 0 1.5em; }
.arbre h1 { margin: 0; font-family: "Fredoka", sans-serif; font-weight: 700; font-size: 2.3em; color: var(--rouge); }
.arbre .arbre-sous-titre { display: block; color: var(--encre-douce); margin-top: 0.3em; }
.arbre img { display: block; width: 100%; max-width: 900px; height: auto; margin: 0 auto; }

/* Page « Comment est née cette histoire » */
.contexte { max-width: 40em; margin: 1em auto 0; text-align: center; }
.contexte .lien-retour { display: block; text-align: left; margin-bottom: 1em; }
.contexte h1 { font-family: "Fredoka", sans-serif; font-weight: 700; font-size: 2.2em; line-height: 1.15; color: var(--encre); margin: 1em 0 0; }
.contexte-texte { text-align: left; }
.citation { margin: 1.8em auto; max-width: 28em; text-align: center; font-family: "Fredoka", sans-serif; font-weight: 500;
  font-size: 1.3em; line-height: 1.4; color: var(--bleu-fonce); }
.citation .source { display: block; margin-top: 0.5em; font-size: 0.6em; letter-spacing: 0.12em; text-transform: uppercase; color: var(--encre-douce); }
.dessins { display: flex; justify-content: center; align-items: flex-end; gap: 2.5em; margin: 0.6em auto 0.4em; }
.dessins figure { margin: 0; }
.dessins img { display: block; height: 8em; width: auto; margin: 0 auto; }
.dessins figcaption { margin-top: 0.4em; font-family: "Fredoka", sans-serif; font-weight: 600; font-size: 0.9em; color: var(--bleu-fonce); }
.table-fiches { margin: 2.6em auto 0; }
.table-fiches .titre-table { display: block; font-family: "Fredoka", sans-serif; font-weight: 600; font-size: 1.3em; margin-bottom: 1.2em; }
.miniatures { display: flex; justify-content: center; align-items: flex-start; flex-wrap: wrap; gap: 1.6em; }
.miniatures figure { margin: 0; }
.miniatures figcaption { margin-top: 0.7em; color: var(--encre-douce); }
.miniature { display: block; padding: 0; border: none; background: none; cursor: zoom-in; }
.miniature img { display: block; height: 13em; width: auto; border: 3px solid var(--plaque); border-radius: 6px; transition: transform 0.2s ease; }
.miniature:hover img { transform: scale(1.04); }
.contexte .credits { display: block; margin-top: 2em; font-size: 0.9em; color: var(--encre-douce); }
.contexte .avertissement { display: block; margin-top: 0.8em; font-size: 0.82em; font-style: italic; color: var(--encre-douce); }
.contexte .secondaires { margin-top: 1.4em; }
.agrandi { position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center;
  padding: 2vh 2vw; background: rgba(34, 37, 43, 0.88); cursor: zoom-out; }
.agrandi img { max-width: 100%; max-height: 96vh; }

@media (max-width: 600px) {
  tw-story { font-size: 1.03em; padding: 0.8em 1em 3em; }
  .chapitre .titre { font-size: 1.9em; }
  .de { flex-direction: column-reverse; align-items: stretch; }
  .lancer { align-self: center; width: auto; }
  .tirage { flex-wrap: wrap; }
  .miniature img { height: 10em; }
  .garde .mention { position: static; }
}
""".replace("ROUGE", ROUGE).replace("JAUNE", JAUNE).replace("BLEU", BLEU).replace("VERT", VERT).replace("BRIQUE_DE", BRIQUE_DE)

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
        suite.append('<div class="fin"><span class="mot-fin">Fin</span>'
                     f'<div class="secondaires">{lien("Comment est née cette histoire", "Comment est née cette histoire")}'
                     f'{lien("Relire depuis le début", "Prologue")}</div></div>')
    numero = "" if ch["nom"] == "Prologue" else f'<span class="numero">{ch["numero"]}</span>'
    texte = (f'<div class="texte"><h1 class="chapitre">{numero}<span class="titre">{ch["titre"]}</span></h1>'
             + "\n\n".join(corps) + "".join(suite) + "</div>")
    return f'<div class="page">{cote}{texte}</div>'


def passage_garde():
    resume = "".join(f"<p>{p}</p>" for p in SYNOPSIS.split("\n\n"))
    return (
        '<div class="garde">'
        '<span class="surtitre">Une histoire dont le lecteur est le héros</span>'
        '<span class="grand-titre">Le Real<span>de Lego City</span></span>'
        f'<span class="nom-auteur">une histoire par {AUTEURS}</span>'
        f'{SEPARATEUR}<div class="synopsis">{resume}</div>'
        f'<div class="commencer">{lien("Commencer l’histoire", "Prologue")}</div>'
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
