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
from construire_site import (AUTEURS, AVERTISSEMENT, CITATION, CONTEXTE, PIECES, SYNOPSIS, TITRE,  # noqa: E402
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
@page {{
  size: {LARGEUR_PAGE}mm {HAUTEUR_PAGE}mm;
  margin: 11mm 11mm 14mm 11mm;
  @bottom-center {{ content: counter(page); font-family: "Jost"; font-weight: 600; font-size: 9pt; color: {DOUCE}; }}
}}
@page sans-numero {{ @bottom-center {{ content: none; }} }}
* {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; box-sizing: border-box; }}
html {{ font-family: "Jost", sans-serif; font-size: 11pt; line-height: 1.45; color: {ENCRE}; }}
body {{ margin: 0; }}
p {{ margin: 0 0 0.5em; orphans: 2; widows: 2; }}
.page-seule {{ break-before: page; }}
.sans-numero {{ page: sans-numero; }}
.marque {{ font-size: 1pt; color: #ffffff; }}

/* Couverture : la boîte de Manon en pleine page */
@page couverture {{ margin: 0; @bottom-center {{ content: none; }} }}
/* Couverture : l'image du prologue sur toute la largeur, jusqu'en bas (jamais recadrée) ; l'encadré blanc du site par-dessus */
.couverture {{ page: couverture; position: relative; height: 185.5mm; overflow: hidden; background: #fff; }}
.couverture .fond {{ position: absolute; left: 0; bottom: 0; width: 100%; height: auto; }}
.couverture .encadre {{ position: absolute; left: 9mm; right: 9mm; top: 10mm; padding: 9mm 4mm 4.5mm; background: #fff;
  border: 0.8mm solid {ENCRE}; border-radius: 3mm; overflow: hidden; text-align: center; }}
.couverture .coins {{ position: absolute; left: 0; right: 0; top: 0; display: flex; justify-content: space-between; }}
.couverture .set {{ background: {ROUGE}; color: #fff; font-weight: 800; font-size: 13pt; padding: 0.8mm 3mm; border-bottom-right-radius: 2mm; }}
.couverture .age {{ background: {JAUNE}; color: {ENCRE}; font-weight: 800; font-size: 13pt; padding: 0.8mm 3mm; border-bottom-left-radius: 2mm; }}
.couverture .surtitre {{ font-weight: 600; font-size: 6pt; letter-spacing: 1.2pt; text-transform: uppercase; color: {DOUCE}; }}
.couverture h1 {{ margin: 1mm 0 0; font-weight: 800; font-size: 22pt; line-height: 1.05; color: {ENCRE}; }}
.couverture .par {{ margin-top: 1mm; font-weight: 600; font-size: 10pt; color: {DOUCE}; }}
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
.bande {{ display: flex; align-items: stretch; border: 0.6mm solid {TRAIT}; border-radius: 2.5mm; overflow: hidden; break-inside: avoid; }}
.bande .num {{ flex: none; display: flex; align-items: center; justify-content: center; min-width: 14mm; padding: 0 1.5mm;
  font-weight: 800; font-size: 22pt; line-height: 1; color: #fff; }}
.bande .num.jaune {{ color: {ENCRE}; }}
.bande .texte {{ padding: 1.8mm 3mm; }}
.bande .sachet {{ display: block; font-weight: 600; font-size: 7pt; color: {DOUCE}; }}
.bande h1 {{ margin: 0; font-weight: 700; font-size: 14pt; line-height: 1.12; }}
.pieces {{ display: flex; flex-wrap: wrap; align-items: flex-end; gap: 1mm 3mm; margin: 2mm 0 3mm; padding: 1.5mm 2.5mm;
  border-radius: 2.5mm; background: {NOTICE}; width: fit-content; }}
.pieces figure {{ margin: 0; display: flex; flex-direction: column; align-items: center; }}
.pieces img {{ height: 9mm; width: auto; }}
.pieces b {{ font-size: 6.5pt; color: {BLEU}; }}
.pola {{ float: left; width: 52%; margin: 0.5mm 4mm 2mm 0; }}
.suite, .montage, .de {{ clear: both; }}
.scene {{ display: block; height: 70mm; width: auto; margin: 2mm auto 3mm; }}
.ouvre {{ padding-top: 2mm; }}

/* Fin de chapitre */
.suite {{ break-inside: avoid; break-before: avoid; }}
.separateur {{ display: flex; align-items: flex-end; justify-content: center; gap: 1.3mm; margin: 3.5mm 0 2.5mm; }}
.separateur::before, .separateur::after {{ content: ""; width: 14mm; height: 0.4mm; margin: 0 2mm 1.3mm; background: {TRAIT}; }}
.separateur i {{ position: relative; display: block; width: 3.4mm; height: 3mm; border-radius: 0.6mm; }}
.separateur i::before {{ content: ""; position: absolute; left: 0.9mm; top: -1mm; width: 1.6mm; height: 1.1mm; border-radius: 0.4mm 0.4mm 0 0; background: inherit; }}
.separateur i:nth-of-type(1) {{ background: {ROUGE}; }}
.separateur i:nth-of-type(2) {{ background: {JAUNE}; }}
.separateur i:nth-of-type(3) {{ background: {BLEU}; }}
.elan {{ text-align: center; font-weight: 700; font-size: 11.5pt; color: {BLEU}; }}
.elan::after {{ content: " →"; color: {ROUGE}; }}
.de {{ margin-top: 3.5mm; padding: 2.5mm 3.5mm 2mm; border: 0.7mm solid {BLEU}; border-radius: 2.5mm; break-inside: avoid; }}
.consigne {{ font-weight: 600; font-size: 10.5pt; margin: 0 0 1.8mm; }}
.tirage {{ display: grid; grid-template-columns: 22mm 1fr; gap: 3mm; align-items: center; margin: 0 0 1.4mm; }}
.tirage b {{ text-align: center; background: {JAUNE}; border-radius: 1mm; padding: 0.3mm 0; font-weight: 700; font-size: 9pt; }}
.renvoi {{ font-weight: 700; color: {BLEU}; }}
.pola + .montage {{ margin: 0 0 3mm; }}
.montage-haut .pola {{ width: 44% !important; }}

.montage-haut .montage {{ padding: 1mm 9mm; margin-bottom: 2mm !important; }}
.montage {{ display: flex; align-items: center; justify-content: space-between; gap: 1.5mm; margin-top: 3mm; padding: 2mm 2.5mm;
  border-radius: 2.5mm; background: {NOTICE}; break-inside: avoid; }}
.montage img {{ flex: 1 1 0; min-width: 0; width: 100%; height: auto; }}
.montage .fl {{ flex: none; font-weight: 700; color: {BLEU}; }}
.fin {{ text-align: center; font-weight: 800; font-size: 26pt; color: {ROUGE}; margin-top: 1mm; }}
.fin span {{ display: block; font-weight: 600; font-size: 10pt; color: {DOUCE}; }}

/* Chapitres resserrés pour éviter les pages presque vides */
.serre {{ font-size: 10.4pt; line-height: 1.38; }}
.serre .pola {{ width: 48%; }}
.serre2 {{ font-size: 9.9pt; line-height: 1.33; }}
.serre2 .pola {{ width: 44%; }}

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
    cle = cle_de(ch["nom"])
    serre = (" serre" if cle in SERRES else "") + (" serre2" if cle in SERRES2 else "")
    n_sachet, nom_sachet = sachet(cle)
    image = RACINE / "images" / "chapitres" / f"{illustration(ch['nom'])}.jpg"
    etapes = sorted((RACINE / "images" / "etapes").glob(f"{illustration(ch['nom'])}-*.png"))
    couleur = COULEURS[n_sachet]
    if ch["nom"] == "Prologue":
        bande = (f'<div class="bande"><div class="texte"><span class="sachet">Prologue</span>'
                 f'<h1>{e(ch["titre"])}</h1></div></div>')
    else:
        bande = (f'<div class="bande"><span class="num{" jaune" if couleur == JAUNE else ""}" style="background:{couleur}">'
                 f'{ch["numero"].split()[-1]}</span><div class="texte"><span class="sachet">Sachet {n_sachet} · {e(nom_sachet)}</span>'
                 f'<h1>{e(ch["titre"])}</h1></div></div>')
    serre += " montage-haut" if cle in MONTAGE_HAUT else ""
    morceaux = [f'<section class="page-seule ouvre{serre}"><span class="marque">@@CH{cle}@@</span>', bande]
    if etapes:
        morceaux.append(pieces(cle))
    if image.exists():
        classe = "pola" if etapes else "scene"
        morceaux.append(f'<img class="{classe}" src="{image.as_uri()}" alt="">')

    corps, consigne, tirages, cible, fin = lire_choix(ch)
    morceaux += [f"<p>{e(p)}</p>" for p in corps]
    suite = []
    if tirages:
        suite.append(f'<div class="de"><p class="consigne">{e(consigne)}</p>' + "".join(
            f'<div class="tirage"><b>{e(f)}</b><span class="renvoi">{e(renvoi(n, pages))}</span></div>'
            for f, n in tirages) + "</div>")
    elif cible and not (suivant is not None and int(cible) == suivant):
        suite += [SEPARATEUR, f'<p class="elan">{e(renvoi(cible, pages))}</p>']
    if fin:
        suite += [SEPARATEUR, '<div class="fin">Fin<span>Ton modèle est terminé.</span></div>']
    montage = ('<div class="montage">' + '<span class="fl">→</span>'.join(
        f'<img src="{x.as_uri()}" alt="">' for x in etapes) + '</div>') if etapes else ""
    if montage and cle in MONTAGE_HAUT:
        # Chapitre trop court pour laisser le montage seul sur une page : il passe avant la case du dé ou le renvoi
        morceaux.append(montage)
        montage = ""
    if suite:
        morceaux.append(f'<div class="suite">{"".join(suite)}</div>')
    if montage:
        morceaux.append(montage)
    if False:
        morceaux.append('<div class="montage">' + '<span class="fl">→</span>'.join(
            f'<img src="{x.as_uri()}" alt="">' for x in etapes) + '</div>')
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
        # Couverture : l'image du prologue en pleine page ; par-dessus, l'encadré blanc du site
        '<section class="couverture sans-numero">'
        f'<img class="fond" src="{(RACINE / "images" / "chapitres" / "prologue.jpg").as_uri()}" alt="">'
        '<div class="encadre"><div class="coins"><span class="set">2810</span><span class="age">6+</span></div>'
        '<div class="surtitre">Une histoire dont le lecteur est le héros</div>'
        f'<h1>{e(TITRE)}</h1>'
        f'<div class="par">par {e(AUTEURS)}</div></div></section>'
        '<section class="page-seule sans-numero"><div class="dos">'
        f'<div class="resume">{e(SYNOPSIS)}</div>'
        f'<img class="equipe" src="{(RACINE / "images" / "equipe.jpg").as_uri()}" alt="">'
        '<div class="mention">Fan fiction librement inspirée du football et des jouets LEGO®. La boîte est une image : '
        'ce livre n’est pas un produit LEGO.</div></div></section>'
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


SERRES, SERRES2, MONTAGE_HAUT = set(), set(), set()


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
    # Ce qui reste court après deux crans de resserrement : le montage passe avant la fin du chapitre
    restes = set(queues_courtes(pdf, pages)) | set(pages_trouees(pdf, pages))
    if restes:
        MONTAGE_HAUT.update(restes)
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
    print("Montage sous le polaroid :", ", ".join(str(c) for c in sorted(MONTAGE_HAUT)) or "aucun")
    print("Pages à moitié vides :", ", ".join(str(c) for c in pages_trouees(lecture, pages)) or "aucune")
    print("Fins de chapitre de quelques lignes :", ", ".join(str(c) for c in queues_courtes(lecture, pages)) or "aucune")
    print("Pages des chapitres :", ", ".join(f"{k}→{v}" for k, v in sorted(pages.items())))


if __name__ == "__main__":
    construire()
