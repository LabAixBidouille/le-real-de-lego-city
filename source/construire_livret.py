#!/usr/bin/env python3
"""Construit le livret imprimable du « Real de Lego City » à partir de source/texte.md.

Même chaîne que les autres livres de l'atelier (pages de 124 × 186 mm, renvois avec le numéro de page,
imposition sur A4), avec la mise en forme du site d'Ernest et d'Abel, celle d'une notice de montage : police
Jost, bandeau d'étape (numéro dans la case de la couleur du sachet, titre), pièces de l'étape, polaroid,
étapes de montage en fin de chapitre, case du dé cerclée de bleu aux faces sur briques jaunes. Aucun motif PDF
(dégradés, ombres) : certaines visionneuses les affichent mal.

Produit dans le dossier Impression du livre : LeRealDeLegoCity_Livret_lecture.pdf et les impositions A4
bord court et bord long.

Usage, depuis la racine du dépôt : python source/construire_livret.py (avec le venv qui contient pypdf)
"""
import html
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PageObject, PdfReader, PdfWriter, Transformation

sys.path.insert(0, str(Path(__file__).resolve().parent))
from construire_site import (AUTEURS, AVERTISSEMENT, AVERTISSEMENT_COURT, CITATION, CONTEXTE, PIECES, SYNOPSIS, TITRE,  # noqa: E402
                             fichier_piece, illustration, lire_chapitres, lire_choix, minutes_de_lecture, sachet)

RACINE = Path(__file__).resolve().parent.parent
IMPRESSION = RACINE.parent / "Impression"
NOM = "LeRealDeLegoCity"

MM = 72 / 25.4
LARGEUR_PAGE, HAUTEUR_PAGE = 124, 186
A4_L, A4_H = 297 * MM, 210 * MM
ENCRE, DOUCE, NOTICE, TRAIT = "#22252b", "#5b5f68", "#e8eef6", "#cfd8e3"
ROUGE, JAUNE, BLEU, VERT, ORANGE = "#d01012", "#f5c518", "#0057b8", "#2c8a3f", "#f2780c"
COULEURS = {1: ROUGE, 2: JAUNE, 3: BLEU, 4: VERT, 5: ORANGE}

CSS = f"""
@font-face {{ font-family: "Jost"; font-weight: 300 800; src: url("{(RACINE / 'fonts' / 'Jost.woff2').as_uri()}"); }}
@font-face {{ font-family: "Source Livre"; font-weight: 200 900; src: url("{(RACINE / 'fonts' / 'SourceSerif.woff2').as_uri()}"); }}
@font-face {{ font-family: "Source Livre"; font-style: italic; font-weight: 200 900; src: url("{(RACINE / 'fonts' / 'SourceSerif-i.woff2').as_uri()}"); }}
@page {{
  size: {LARGEUR_PAGE}mm {HAUTEUR_PAGE}mm;
  margin: 11mm 11mm 14mm 11mm;
  @bottom-center {{ content: counter(page); font-family: "Jost"; font-weight: 600; font-size: 9pt; color: {DOUCE}; }}
}}
@page sans-numero {{ @bottom-center {{ content: none; }} }}
* {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; box-sizing: border-box; }}
html {{ font-family: "Jost", sans-serif; font-size: 11pt; line-height: 1.32; color: {ENCRE}; }}
body {{ margin: 0; }}
p {{ margin: 0 0 0.5em; orphans: 2; widows: 2; }}
.page-seule {{ break-before: page; }}
.sans-numero {{ page: sans-numero; }}
.marque {{ font-size: 1pt; color: #ffffff; }}

/* Couverture : la boîte de Manon en pleine page */
@page couverture {{ margin: 0; @bottom-center {{ content: none; }} }}
/* Couverture : l'image A5 en pleine page, le titre dans le ciel */
.couverture {{ page: couverture; position: relative; height: 185.5mm; overflow: hidden; }}
.couverture .fond {{ position: absolute; inset: 0; width: 100%; height: 100%; }}
.couverture .coins {{ position: absolute; left: 0; right: 0; top: 0; display: flex; justify-content: space-between; }}
.couverture .set {{ background: {ROUGE}; color: #fff; font-weight: 800; font-size: 13pt; padding: 0.8mm 3mm; border-bottom-right-radius: 2mm; }}
.couverture .age {{ background: {JAUNE}; color: {ENCRE}; font-weight: 800; font-size: 13pt; padding: 0.8mm 3mm; border-bottom-left-radius: 2mm; }}
.couverture .titre {{ position: absolute; left: 0; right: 0; top: 19mm; text-align: center; }}
.couverture .surtitre {{ font-weight: 600; font-size: 6.5pt; letter-spacing: 1.3pt; text-transform: uppercase; color: {ENCRE}; }}
.couverture h1 {{ margin: 1.5mm 0 0; font-weight: 800; font-size: 34pt; line-height: 0.95; color: {ROUGE}; }}
/* La brique bleue : une rangée de tenons sur toute sa longueur */
.couverture .brique {{ position: relative; display: inline-block; margin-top: 3.5mm; padding: 1.2mm 5mm 0.9mm; border-radius: 1.2mm;
  background: {BLEU}; color: #fff; font-weight: 800; font-size: 27pt; line-height: 1.05; }}
.couverture .tenons {{ position: absolute; left: 2.5mm; right: 2.5mm; top: -2.2mm; height: 2.4mm; display: flex; justify-content: space-between; }}
.couverture .tenons i {{ display: block; width: 5mm; height: 2.4mm; background: {BLEU}; border-radius: 0.7mm 0.7mm 0 0; }}
.couverture .par {{ display: table; margin: 2mm auto 0; font-weight: 600; font-size: 10.5pt; color: {ENCRE}; }}
/* Page 2 : l'équipe sous le résumé */
.dos .equipe {{ display: block; width: 100%; height: auto; }}
/* Rangée de briques en bas de la boîte */
.boite .briques {{ position: absolute; left: 0; right: 0; bottom: 0; height: 11mm; display: flex; gap: 0.8mm; padding: 0 0.8mm; }}
.boite .briques i {{ position: relative; flex: 1; margin-top: 3mm; border-radius: 1mm 1mm 0 0; }}
.boite .briques i::before, .boite .briques i::after {{ content: ""; position: absolute; top: -2.2mm; width: 4.5mm; height: 2.4mm;
  border-radius: 0.6mm 0.6mm 0 0; background: inherit; }}
.boite .briques i::before {{ left: 22%; }}
.boite .briques i::after {{ right: 22%; }}
.boite .briques i:nth-child(5n+1) {{ background: {ROUGE}; }}
.boite .briques i:nth-child(5n+2) {{ background: {JAUNE}; }}
.boite .briques i:nth-child(5n+3) {{ background: {BLEU}; }}
.boite .briques i:nth-child(5n+4) {{ background: {VERT}; }}
.boite .briques i:nth-child(5n+5) {{ background: {ORANGE}; }}

/* Page 2 : le dos de la boîte */
.dos {{ height: 158mm; display: flex; flex-direction: column; justify-content: center; text-align: center; gap: 4mm; }}
.dos .surtitre {{ font-weight: 600; font-size: 7pt; letter-spacing: 1.4pt; text-transform: uppercase; color: {DOUCE}; }}
.dos h1 {{ margin: 0; font-weight: 800; font-size: 19pt; line-height: 1.05; }}
.dos .par {{ font-weight: 500; color: {DOUCE}; }}
.dos .resume {{ text-align: left; font-size: 12pt; line-height: 1.55; }}
.dos .contenu {{ border-radius: 3mm; background: {NOTICE}; padding: 2.5mm 3mm 2mm; }}
.dos .contenu span {{ display: block; font-weight: 600; font-size: 6.5pt; letter-spacing: 1.2pt; text-transform: uppercase; color: {DOUCE}; }}
.dos .figs {{ display: flex; justify-content: space-between; align-items: flex-end; margin: 1.5mm 0; }}
.dos .figs img {{ height: 11mm; }}
.dos .chiffres {{ font-size: 8pt; color: {DOUCE}; }}
.dos .chiffres b {{ color: {ENCRE}; }}
.dos .mention {{ font-style: italic; font-size: 7.5pt; color: {DOUCE}; }}

/* Bandeau d'étape et pièces */
/* Chapitre d'album */
.tete {{ display: block; width: 66%; margin: 1mm auto 5mm; border: 1.6mm solid #fff; box-shadow: 0 0 0 0.3mm #c9ccd2;
  transform: rotate(-2deg); }}
.entete {{ text-align: center; margin: 0 0 4mm; break-after: avoid; }}
.entete .num {{ font-family: "Jost"; font-weight: 700; font-size: 7.5pt; letter-spacing: 2pt; text-transform: uppercase; color: {ROUGE}; }}
.entete h1 {{ margin: 1.5mm 0 2mm; font-family: "Jost"; font-weight: 800; font-size: 17pt; line-height: 1.12; color: {ENCRE}; }}
.briques-titre {{ display: flex; justify-content: center; gap: 1.2mm; }}
.briques-titre i {{ position: relative; display: block; width: 3mm; height: 2.6mm; border-radius: 0.5mm; }}
.briques-titre i::before {{ content: ""; position: absolute; left: 0.8mm; top: -0.9mm; width: 1.4mm; height: 1mm; border-radius: 0.3mm 0.3mm 0 0; background: inherit; }}
.briques-titre i:nth-child(1) {{ background: {ROUGE}; }}
.briques-titre i:nth-child(2) {{ background: {JAUNE}; }}
.briques-titre i:nth-child(3) {{ background: {BLEU}; }}
.corps {{ font-family: "Source Livre", serif; font-size: 11pt; line-height: 1.42; text-align: justify; hyphens: none; }}
.corps p {{ text-indent: 5mm; margin: 0; orphans: 3; widows: 3; }}
.corps p:first-child {{ text-indent: 0; }}
.corps p:first-child::first-letter {{ float: left; font-family: "Jost"; font-weight: 800; font-size: 30pt; line-height: 0.88;
  margin: 0.8mm 1.8mm 0 0; color: {BLEU}; }}
.montage {{ display: flex; align-items: center; justify-content: center; gap: 2mm; margin: 5mm 0 4mm; }}
.montage img {{ width: 27mm; height: auto; }}
.montage .fl {{ font-family: "Jost"; font-weight: 700; color: {BLEU}; }}
.de {{ margin-top: 3mm; padding: 2.5mm 0; border-top: 0.4mm solid {ENCRE}; border-bottom: 0.4mm solid {ENCRE}; break-inside: avoid; }}
.consigne {{ font-family: "Source Livre", serif; font-style: italic; font-size: 11pt; margin: 0 0 1.5mm; }}
.tirages {{ display: flex; flex-wrap: wrap; justify-content: space-between; gap: 1mm 4mm; font-family: "Jost"; font-weight: 600; font-size: 10pt; }}
.tirages b {{ color: {ROUGE}; }}
/* Fin de chapitre */
.suite {{ break-inside: avoid; }}
.separateur {{ display: flex; align-items: flex-end; justify-content: center; gap: 1.3mm; margin: 3.5mm 0 2.5mm; }}
.separateur::before, .separateur::after {{ content: ""; width: 14mm; height: 0.4mm; margin: 0 2mm 1.3mm; background: {TRAIT}; }}
.separateur i {{ position: relative; display: block; width: 3.4mm; height: 3mm; border-radius: 0.6mm; }}
.separateur i::before {{ content: ""; position: absolute; left: 0.9mm; top: -1mm; width: 1.6mm; height: 1.1mm; border-radius: 0.4mm 0.4mm 0 0; background: inherit; }}
.separateur i:nth-of-type(1) {{ background: {ROUGE}; }}
.separateur i:nth-of-type(2) {{ background: {JAUNE}; }}
.separateur i:nth-of-type(3) {{ background: {BLEU}; }}
.elan {{ margin-top: 4mm; text-align: center; font-family: "Jost"; font-weight: 700; font-size: 11.5pt; color: {BLEU}; }}
.elan::after {{ content: " →"; color: {ROUGE}; }}

.fin {{ text-align: center; font-weight: 800; font-size: 26pt; color: {ROUGE}; margin-top: 1mm; }}
.fin span {{ display: block; font-weight: 600; font-size: 10pt; color: {DOUCE}; }}

/* Chapitres resserrés : le polaroid et le montage rapetissent, jamais le texte */
.serre .tete {{ width: 54%; }}
.serre .montage img {{ width: 23mm; }}
.serre2 .tete {{ width: 42%; margin-bottom: 3mm; }}
.serre2 .montage {{ margin: 3mm 0 2mm; }}
.serre2 .montage img {{ width: 19mm; }}

/* Contexte, arbre, dos */
.contexte h2 {{ font-weight: 800; font-size: 15pt; text-align: center; margin: 0 0 3mm; }}
.contexte p {{ font-size: 9.6pt; line-height: 1.4; }}
.dessins {{ display: flex; justify-content: center; gap: 8mm; align-items: flex-end; margin: 0 0 3mm; }}
.dessins figure {{ margin: 0; text-align: center; }}
.dessins img {{ height: 17mm; }}
.dessins figcaption {{ font-weight: 600; font-size: 7pt; color: {BLEU}; }}
.citation {{ font-weight: 500; font-size: 11pt; text-align: center; color: {BLEU}; margin: 2.5mm 4mm 3mm; }}
.credits {{ font-size: 8.8pt; color: {DOUCE}; }}
.fiches {{ display: grid; grid-template-columns: 1fr 1fr; gap: 3mm; }}
.fiches img {{ width: 100%; display: block; border: 0.3mm solid {TRAIT}; }}
.fiches .pleine {{ grid-column: 1 / -1; }}
@page arbre {{ margin: 6mm 5mm 6mm; @bottom-center {{ content: none; }} }}
.arbre {{ page: arbre; height: 173mm; display: flex; flex-direction: column; align-items: center; }}
.arbre img {{ flex: 1; min-height: 0; width: 100%; object-fit: contain; }}
.der {{ display: flex; flex-direction: column; justify-content: flex-end; height: 158mm; text-align: center; font-size: 8.5pt; color: {DOUCE}; }}
"""

SEPARATEUR = '<div class="separateur"><i></i><i></i><i></i></div>'
SEPARATEUR_TITRE = '<div class="briques-titre"><i></i><i></i><i></i></div>'


def e(texte):
    return html.escape(texte, quote=False)


def cle_de(nom):
    return 0 if nom == "Prologue" else int(nom.split()[-1])


def renvoi(cible, pages):
    return f"Poursuis au chapitre {cible}, page {pages.get(int(cible), '00')}"


def pieces(cle):
    morceaux = []
    for nombre, nom in PIECES.get(cle, []):
        chemin = RACINE / fichier_piece(nom)
        if chemin.exists():
            morceaux.append(f'<figure><img src="{chemin.as_uri()}" alt=""><b>{nombre}×</b></figure>')
    return f'<div class="pieces">{"".join(morceaux)}</div>' if morceaux else ""


def chapitre(ch, suivant, pages):
    """Un chapitre d'album : le polaroid en tête (penché), le numéro, le titre et trois briques, le récit avec une
    lettrine ; à la fin, le montage posé sans cadre et les choix entre deux filets."""
    cle = cle_de(ch["nom"])
    serre = (" serre" if cle in SERRES else "") + (" serre2" if cle in SERRES2 else "")
    image = RACINE / "images" / "chapitres" / f"{illustration(ch['nom'])}.jpg"
    carre = image.with_name(image.stem + "-carre.jpg")
    if carre.exists():
        image = carre
    etapes = sorted((RACINE / "images" / "etapes").glob(f"{illustration(ch['nom'])}-*.png"))
    morceaux = [f'<section class="page-seule chap{serre}"><span class="marque">@@CH{cle}@@</span>']
    if image.exists():
        morceaux.append(f'<img class="tete" src="{image.as_uri()}" alt="">')
    numero = "Prologue" if ch["nom"] == "Prologue" else ch["numero"]
    morceaux.append(f'<div class="entete"><span class="num">{e(numero)}</span><h1>{e(ch["titre"])}</h1>{SEPARATEUR_TITRE}</div>')
    corps, consigne, tirages, cible, fin = lire_choix(ch)
    morceaux.append('<div class="corps">' + "".join(f"<p>{e(p)}</p>" for p in corps) + "</div>")

    fin_bloc = []
    if etapes:
        fin_bloc.append('<div class="montage">' + '<span class="fl">→</span>'.join(
            f'<img src="{x.as_uri()}" alt="">' for x in etapes) + '</div>')
    if tirages:
        fin_bloc.append(f'<div class="de"><p class="consigne">{e(consigne)}</p><div class="tirages">' + "".join(
            f'<span><b>{e(f)}</b> · '
            f'{"tourne la page" if suivant is not None and int(n) == suivant else e(f"chapitre {n}, page {pages.get(int(n), 00)}")}</span>'
            for f, n in tirages) + "</div></div>")
    elif cible and not (suivant is not None and int(cible) == suivant):
        fin_bloc.append(f'<p class="elan">{e(renvoi(cible, pages))}</p>')
    if fin:
        fin_bloc.append(SEPARATEUR + '<div class="fin">Fin</div>')
    if fin_bloc:
        morceaux.append(f'<div class="suite">{"".join(fin_bloc)}</div>')
    morceaux.append("</section>")
    return "".join(morceaux)


def document(pages, blanches=0):
    figs = "".join(f'<img src="{(RACINE / "images" / "pieces" / f"{f}.png").as_uri()}" alt="">'
                   for f in ("kylian", "messi", "ronaldo", "pompier", "boulangere", "pirate", "astronaute", "zidane"))
    etapes = len(lire_chapitres()) - 1
    figs = "".join(f'<img src="{(RACINE / "images" / "pieces" / f"{f}.png").as_uri()}" alt="">'
                   for f in ("kylian", "messi", "ronaldo", "zidane", "pompier", "policiere", "boulangere", "pirate",
                             "astronaute", "blanchisseur", "maire", "entraineur-de-l-om", "petit-chien", "joueur-adverse"))
    couverture = (
        # Couverture : l'image A5 de Manon (ciel en haut) ; « Le Real » en rouge sur le ciel, « de Lego City » sur une brique bleue
        '<section class="couverture sans-numero">'
        f'<img class="fond" src="{(RACINE / "images" / "couverture-livret.png").as_uri()}" alt="">'
        '<div class="coins"><span class="set">2810</span><span class="age">8+</span></div>'
        '<div class="titre"><div class="surtitre">Une histoire dont le lecteur est le héros</div>'
        '<h1>Le Real</h1><div class="brique"><div class="tenons">' + '<i></i>' * 7 + '</div><span>de Lego City</span></div>'
        f'<div class="par">par {e(AUTEURS)}</div></div></section>'
        '<section class="page-seule sans-numero"><div class="dos">'
        f'<div class="resume">{e(SYNOPSIS)}</div>'
        f'<div class="mention">{e(AVERTISSEMENT_COURT)}</div></div></section>'
    )
    chapitres_lus = lire_chapitres()
    cles = [cle_de(ch["nom"]) for ch in chapitres_lus]
    chapitres = "".join(chapitre(ch, cles[i + 1] if i + 1 < len(cles) else None, pages)
                        for i, ch in enumerate(chapitres_lus))
    paragraphes = [q for p in CONTEXTE for q in p.split("\n\n")]

    def para(p):
        return f"<p>{e(p).replace('&lt;b&gt;', '<b>').replace('&lt;/b&gt;', '</b>')}</p>"

    def dessin(fichier, nom):
        return (f'<figure><img src="{(RACINE / "images" / "dessins" / fichier).as_uri()}" alt="">'
                f'<figcaption>{nom}</figcaption></figure>')
    fiches = RACINE / "images" / "fiches"
    contexte = (
        '<section class="page-seule contexte"><div class="dessins">'
        + dessin("kylian.png", "Kylian") + dessin("messi.png", "Messi") + dessin("ronaldo.png", "Ronaldo")
        + '</div><h2>Comment est née cette histoire</h2>'
        + "".join(para(p) for p in paragraphes[:4])
        + f'<p class="citation">« {e(CITATION)} »</p>'
        + "".join(para(p) for p in paragraphes[4:])
        + '<p class="credits">Une histoire librement inspirée du récit d’Ernest et d’Abel.<br>Réalisation du livre : '
          "Laboratoire d’Aix-périmentation et de Bidouille.</p></section>"
        '<section class="page-seule contexte"><h2>Les fiches de l’atelier</h2><div class="fiches">'
        f'<img src="{(fiches / "fiche_recit.jpg").as_uri()}" alt="">'
        f'<img src="{(fiches / "fiche_personnage_kylian.jpg").as_uri()}" alt="">'
        f'<img class="pleine" src="{(fiches / "fiche_situation_1.jpg").as_uri()}" alt="">'
        "</div></section>"
    )
    arbre = ('<section class="page-seule contexte arbre sans-numero"><h2>L’arbre de l’histoire</h2>'
             f'<img src="{(RACINE / "images/arbre.svg").as_uri()}" alt=""></section>')
    vides = '<section class="page-seule sans-numero">&nbsp;</section>' * blanches
    der = ('<section class="page-seule sans-numero"><div class="der">'
           f'<p><i>{e(AVERTISSEMENT)}</i></p>'
           f"<p><b>{e(TITRE)}</b>, une histoire librement inspirée du récit imaginé par Ernest et Abel pendant l’atelier "
           "« La quête du curry, une histoire dont tu es le héros », à la bibliothèque Li Campaneto "
           "(bibliothèques Méjanes, Aix-en-Provence), en octobre 2026.</p><p>Réalisation du livre : Laboratoire d’Aix-périmentation et de Bidouille.</p>"
           "</div></section>")
    return (f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><style>{CSS}</style></head>'
            f"<body>{couverture}{chapitres}{contexte}{arbre}{vides}{der}</body></html>")


def imprimer(source_html, pdf):
    subprocess.run(["google-chrome", "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
                    "--virtual-time-budget=10000", f"--print-to-pdf={pdf}", source_html.as_uri()],
                   check=True, capture_output=True)


def reperer_pages(pdf):
    """Numéro de page où commence chaque partie, d'après les marques invisibles."""
    pages = {}
    total = len(PdfReader(str(pdf)).pages)
    for n in range(1, total + 1):
        texte = subprocess.run(["pdftotext", "-f", str(n), "-l", str(n), str(pdf), "-"],
                               capture_output=True, text=True, check=True).stdout
        for cle in re.findall(r"@@CH(\d+)@@", texte):
            pages[int(cle)] = n
    return pages, total


def stabiliser(source, pdf, pages):
    for _ in range(5):
        source.write_text(document(pages), encoding="utf-8")
        imprimer(source, pdf)
        nouvelles, total = reperer_pages(pdf)
        if nouvelles == pages:
            return pages, total
        pages = nouvelles
    raise SystemExit("Les numéros de page ne se stabilisent pas.")


def queues_courtes(pdf, pages, seuil=6):
    """Chapitres dont la dernière page ne porte que quelques lignes (à surveiller à la relecture)."""
    debuts = sorted((page, cle) for cle, page in pages.items())
    courtes = []
    for (debut, cle), (suivant, _) in zip(debuts, debuts[1:]):
        fin = suivant - 1
        if fin <= debut:
            continue
        texte = subprocess.run(["pdftotext", "-f", str(fin), "-l", str(fin), str(pdf), "-"],
                               capture_output=True, text=True, check=True).stdout
        lignes = [l for l in texte.splitlines() if l.strip() and not l.strip().isdigit()]
        if len(lignes) <= seuil:
            courtes.append(cle)
    return courtes


def remplissage(pdf, n):
    """Part de la hauteur utile de la page n occupée par le contenu (0 à 1)."""
    ppm = subprocess.run(["pdftoppm", "-r", "30", "-gray", "-f", str(n), "-l", str(n), str(pdf)],
                         capture_output=True, check=True).stdout
    entete = ppm.split(b"\n", 3)
    largeur, hauteur = map(int, entete[1].split())
    pixels = entete[3]
    bas_utile = int(hauteur * (1 - 15 / HAUTEUR_PAGE)) - 2      # au-dessus du numéro de page
    lignes = [y for y in range(bas_utile) if min(pixels[y * largeur:(y + 1) * largeur]) < 200]
    return (lignes[-1] / bas_utile) if lignes else 0


def pages_trouees(pdf, pages, seuil=0.8):
    """Chapitres dont une page intermédiaire est restée à moitié vide (le dernier paragraphe est parti avec
    la case du dé sur la page suivante)."""
    debuts = sorted((page, cle) for cle, page in pages.items())
    trouees = []
    for (debut, cle), (suivant, _) in zip(debuts, debuts[1:]):
        if any(remplissage(pdf, n) < seuil for n in range(debut, suivant - 1)):
            trouees.append(cle)
    return trouees


SERRES, SERRES2 = set(), set()


def composer(dossier):
    """Compose le livret ; les chapitres dont la fin tient en quelques lignes sont resserrés (un cran, puis
    deux), et un resserrement qui ne sert à rien est retiré."""
    source = Path(dossier) / "livret.html"
    pdf = Path(dossier) / "livret.pdf"
    pages, total = stabiliser(source, pdf, {})
    for _ in range(4):
        courtes = set(queues_courtes(pdf, pages)) | set(pages_trouees(pdf, pages))
        nouvelles = (courtes - SERRES) | {c for c in courtes & SERRES if c not in SERRES2}
        if not nouvelles:
            break
        SERRES2.update(courtes & SERRES)
        SERRES.update(courtes)
        pages, total = stabiliser(source, pdf, {})
    blanches = (-total) % 4
    if blanches:
        source.write_text(document(pages, blanches), encoding="utf-8")
        imprimer(source, pdf)
        assert reperer_pages(pdf)[0] == pages
    return pdf, pages


def traits_de_coupe(dossier):
    x0, y0 = (297 - 2 * LARGEUR_PAGE) / 2, (210 - HAUTEUR_PAGE) / 2
    gauche, droite, haut, bas = x0, x0 + 2 * LARGEUR_PAGE, y0, y0 + HAUTEUR_PAGE
    coupe = [f'<line x1="0" y1="{y}" x2="297" y2="{y}"/>' for y in (haut, bas)]
    coupe += [f'<line x1="{x}" y1="0" x2="{x}" y2="210"/>' for x in (gauche, droite)]
    pli = x0 + LARGEUR_PAGE
    source = Path(dossier) / "traits.html"
    source.write_text(
        '<!doctype html><html><head><style>@page { size: 297mm 210mm; margin: 0; } body { margin: 0; }</style></head>'
        '<body><svg xmlns="http://www.w3.org/2000/svg" width="297mm" height="210mm" viewBox="0 0 297 210">'
        f'<g stroke="#c9c9c9" stroke-width="0.2">{"".join(coupe)}</g>'
        f'<line x1="{pli}" y1="0" x2="{pli}" y2="210" stroke="#cfd8e3" stroke-width="0.2"/>'
        '</svg></body></html>', encoding="utf-8")
    pdf = Path(dossier) / "traits.pdf"
    imprimer(source, pdf)
    return PdfReader(str(pdf)).pages[0]


def en_forme(ecrivain, page):
    """La page entière devient un objet « forme » PDF. Placée ensuite par une translation, elle emmène avec
    elle ses motifs (hachures, ombres) : posée directement sur la feuille, une page garde ses motifs calés
    sur la feuille et non sur elle, et les hachures se décalent."""
    from pypdf.generic import ArrayObject, DecodedStreamObject, FloatObject, NameObject
    forme = DecodedStreamObject()
    forme.set_data(page.get_contents().get_data())
    forme[NameObject("/Type")] = NameObject("/XObject")
    forme[NameObject("/Subtype")] = NameObject("/Form")
    forme[NameObject("/BBox")] = ArrayObject([FloatObject(v) for v in page.mediabox])
    forme[NameObject("/Resources")] = page["/Resources"].clone(ecrivain)
    return ecrivain._add_object(forme)


def imposer(lecture, traits, sortie, bord_long):
    from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
    pages = PdfReader(str(lecture)).pages
    n = len(pages)
    assert n % 4 == 0
    x0 = (A4_L - 2 * LARGEUR_PAGE * MM) / 2
    y0 = (A4_H - HAUTEUR_PAGE * MM) / 2
    ecrivain = PdfWriter()
    formes = {}

    def face(gauche, droite, retournee):
        feuille = ecrivain.add_blank_page(width=A4_L, height=A4_H)
        feuille.merge_page(traits)
        objets = DictionaryObject()
        dessin = ""
        for indice, x in ((gauche, x0), (droite, x0 + LARGEUR_PAGE * MM)):
            if indice not in formes:
                formes[indice] = en_forme(ecrivain, pages[indice - 1])
            nom = f"/Page{indice}"
            objets[NameObject(nom)] = formes[indice]
            dessin += f"q 1 0 0 1 {x:.3f} {y0:.3f} cm {nom} Do Q\n"
        ressources = feuille["/Resources"]
        if "/XObject" in ressources:
            ressources["/XObject"].update(objets)
        else:
            ressources[NameObject("/XObject")] = objets
        ajout = DecodedStreamObject()
        ajout.set_data(dessin.encode())
        contenu = feuille.get_contents()
        tout = DecodedStreamObject()
        tout.set_data((contenu.get_data() if contenu else b"") + b"\n" + ajout.get_data())
        feuille.replace_contents(tout)
        if retournee:
            feuille.rotate(180)

    for i in range(n // 4):
        face(n - 2 * i, 1 + 2 * i, False)
        face(2 + 2 * i, n - 1 - 2 * i, bord_long)
    with open(sortie, "wb") as f:
        ecrivain.write(f)


def construire():
    IMPRESSION.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as dossier:
        pdf, pages = composer(dossier)
        lecture = IMPRESSION / f"{NOM}_Livret_lecture.pdf"
        lecture.write_bytes(pdf.read_bytes())
        traits = traits_de_coupe(dossier)
        imposer(lecture, traits, IMPRESSION / f"{NOM}_Livret_A4_bord_court.pdf", bord_long=False)
        imposer(lecture, traits, IMPRESSION / f"{NOM}_Livret_A4_bord_long.pdf", bord_long=True)
    total = len(PdfReader(str(lecture)).pages)
    print(f"{lecture} : {total} pages, soit {total // 4} feuilles A4 recto verso")
    print("Chapitres resserrés :", ", ".join(str(c) + ("+" if c in SERRES2 else "") for c in sorted(SERRES)) or "aucun")
    print("Pages à moitié vides :", ", ".join(str(c) for c in pages_trouees(lecture, pages)) or "aucune")
    print("Fins de chapitre de quelques lignes :", ", ".join(str(c) for c in queues_courtes(lecture, pages)) or "aucune")
    print("Pages des chapitres :", ", ".join(f"{k}→{v}" for k, v in sorted(pages.items())))


if __name__ == "__main__":
    construire()
