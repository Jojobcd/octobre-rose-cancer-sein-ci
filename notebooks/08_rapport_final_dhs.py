"""Génère le rapport de synthèse à envoyer au DHS Program (obligation des conditions
d'utilisation : toute publication issue des données doit leur être transmise en PDF).
Document distinct du rapport de corrections (`rapport_corrections.pdf`), qui est un
journal de travail interne — celui-ci est la version présentable, destinée à un tiers.
"""
import sys
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import depistage as dp  # noqa: E402

ACCENT = colors.HexColor("#e87ba4")
INK = colors.HexColor("#0b0b0b")
INK_2 = colors.HexColor("#52514e")
GRID = colors.HexColor("#e1e0d9")

styles = getSampleStyleSheet()
title_style = ParagraphStyle("Titre", parent=styles["Title"], textColor=INK, fontSize=16, spaceAfter=2)
subtitle_style = ParagraphStyle("SousTitre", parent=styles["Normal"], textColor=INK_2, fontSize=9.5, spaceAfter=14)
h2_style = ParagraphStyle("H2", parent=styles["Heading2"], textColor=ACCENT, fontSize=12, spaceBefore=14, spaceAfter=5)
body_style = ParagraphStyle("Corps", parent=styles["Normal"], textColor=INK, fontSize=9.7, leading=14, spaceAfter=7)
meta_style = ParagraphStyle("Meta", parent=styles["Normal"], textColor=INK_2, fontSize=8.8, leading=13)

doc = SimpleDocTemplate(
    "reports/rapport_final_dhs.pdf", pagesize=A4,
    leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
)
story = []

story.append(Paragraph("Déterminants de l'accès au dépistage du cancer du sein chez les femmes en Côte d'Ivoire", title_style))
story.append(Paragraph(
    "Analyse à partir de l'EDS-CI 2021 (DHS Program / INS Côte d'Ivoire) — "
    "projet enregistré sous le titre « Determinants of Breast Cancer Screening Uptake "
    "Among Women in Côte d'Ivoire ». Auteur : Konan Jean Jaurès N'dri. Novembre 2026.",
    subtitle_style,
))
story.append(HRFlowable(width="100%", color=GRID, thickness=1))

story.append(Paragraph("Objectif", h2_style))
story.append(Paragraph(
    "Identifier les profils de femmes (région, milieu, éducation, richesse, âge) les moins "
    "couverts par le dépistage du cancer du sein en Côte d'Ivoire, pour informer le ciblage "
    "de campagnes de sensibilisation (type Octobre Rose). Projet pédagogique de portfolio, "
    "ne remplace pas un avis médical ni une étude épidémiologique de référence.",
    body_style,
))

story.append(Paragraph("Données et méthode", h2_style))
story.append(Paragraph(dp.DEFINITION_VARIABLE_CIBLE, body_style))
story.append(Paragraph(
    "Échantillon : 14 870 femmes de 15 à 49 ans (fichier Individual Recode, EDS-CI 2021). "
    "Taux pondérés par le poids d'enquête (v005). Régression logistique pondérée "
    "(âge, éducation, richesse, région, milieu), erreurs-types cluster-robustes sur la "
    "grappe d'enquête (v021), correction de Holm-Bonferroni sur les 13 comparaisons "
    "régionales. Robustesse vérifiée par restriction d'âge (30-49 et 40-49 ans).",
    body_style,
))

story.append(Paragraph("Résultats clés", h2_style))
story.append(Paragraph(
    "Taux national de dépistage (pondéré) : 17,5 %. L'éducation et la richesse sont les "
    "facteurs les plus fortement et les plus robustement associés au dépistage "
    "(odds ratio ajusté respectivement ×5,04 et ×2,48 pour les catégories extrêmes), "
    "confirmés sur l'ensemble des tranches d'âge testées. Aucun effet indépendant du "
    "milieu urbain/rural n'est démontré une fois éducation et richesse prises en compte "
    "(OR=1,23, p=0,050). Le signal régional observé sur l'échantillon complet (deux régions "
    "apparemment défavorisées) ne résiste pas à une restriction d'âge plus réaliste pour le "
    "dépistage — il est traité comme une piste à confirmer, pas comme un résultat acquis.",
    body_style,
))

story.append(Paragraph("Aperçu du tableau de bord", h2_style))
img = Image("reports/dashboard.png", width=16.5 * cm, height=16.5 * cm * (1000 / 1800))
story.append(img)
story.append(Spacer(1, 6))

story.append(Paragraph("Limites", h2_style))
story.append(Paragraph(
    "Données transversales et déclaratives (association, pas causalité). Effet de "
    "l'éducation supposé uniforme entre régions (interaction éducation×région non "
    "testée). Plan de sondage corrigé pour les grappes mais pas pour les strates. "
    "Analyse soumise à une revue critique externe en deux cycles (14 points vérifiés et "
    "corrigés) — détail disponible sur demande.",
    body_style,
))

story.append(Paragraph("Code source, reproductibilité et confidentialité", h2_style))
story.append(Paragraph(
    "Code et documentation complète : github.com/Jojobcd/octobre-rose-cancer-sein-ci. "
    "Conformément aux conditions d'utilisation du DHS Program, les microdonnées "
    "individuelles ne sont ni incluses ni redistribuées dans ce dépôt — seuls des "
    "résultats agrégés y sont publiés.",
    body_style,
))

doc.build(story)
print("Rapport final DHS écrit : reports/rapport_final_dhs.pdf")
