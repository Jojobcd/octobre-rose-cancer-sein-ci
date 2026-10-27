"""Génère un mini-rapport PDF : erreurs trouvées dans le dashboard v1 et corrections apportées."""
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    HRFlowable, ListFlowable, ListItem, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle,
)

ACCENT = colors.HexColor("#e87ba4")
INK = colors.HexColor("#0b0b0b")
INK_2 = colors.HexColor("#52514e")
GRID = colors.HexColor("#e1e0d9")
SERIOUS = colors.HexColor("#ec835a")
GOOD = colors.HexColor("#0ca30c")

styles = getSampleStyleSheet()
title_style = ParagraphStyle("TitreDoc", parent=styles["Title"], textColor=INK, fontSize=18, spaceAfter=4)
subtitle_style = ParagraphStyle("SousTitre", parent=styles["Normal"], textColor=INK_2, fontSize=10, spaceAfter=18)
h2_style = ParagraphStyle("H2", parent=styles["Heading2"], textColor=ACCENT, fontSize=12.5, spaceBefore=16, spaceAfter=6)
label_style = ParagraphStyle("Label", parent=styles["Normal"], textColor=INK, fontSize=9.5, fontName="Helvetica-Bold", spaceAfter=2)
body_style = ParagraphStyle("Corps", parent=styles["Normal"], textColor=INK, fontSize=9.5, leading=13.5, spaceAfter=8)
verdict_style = ParagraphStyle("Verdict", parent=styles["Normal"], textColor=INK, fontSize=10, leading=14, spaceAfter=6)

doc = SimpleDocTemplate(
    "reports/rapport_corrections.pdf", pagesize=A4,
    leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=1.8 * cm, bottomMargin=1.8 * cm,
)
story = []

story.append(Paragraph("Dashboard Octobre Rose — erreurs identifiées et corrections", title_style))
story.append(Paragraph(
    "Revue de la version 1 du dashboard (dépistage du cancer du sein, EDS-CI 2021), "
    "suite à des retours externes. 8 points soulevés, vérifiés un par un avant correction. "
    "Les 8 se sont révélés fondés.",
    subtitle_style,
))
story.append(HRFlowable(width="100%", color=GRID, thickness=1))

issues = [
    dict(
        titre="1. Titre factuellement faux (graphique Région)",
        erreur=(
            "« Abidjan dépiste jusqu'à 4 fois plus que Gôh-Djiboua <b>ou Yamoussoukro</b> ». "
            "Calcul : Abidjan/Gôh-Djiboua = 26,7/7,3 = <b>3,7</b> (correct, arrondi à « presque 4 »). "
            "Abidjan/Yamoussoukro = 26,7/12,3 = <b>2,2</b>, pas 4."
        ),
        cause=(
            "Les deux noms de régions ont été choisis à partir du classement de la "
            "<b>régression ajustée</b> (les 2 régions les plus significativement défavorisées), "
            "puis réutilisés dans une phrase sur le <b>taux brut</b> sans revérifier que le ratio "
            "brut correspondait aussi pour la seconde région. Deux classements différents ont été mélangés."
        ),
        correction=(
            "Titre réécrit pour ne citer que la comparaison exacte : « Abidjan dépiste environ 3,7× "
            "plus que Gôh-Djiboua, la région la plus en retard »."
        ),
    ),
    dict(
        titre="2. Confusion entre taux brut et odds ratio ajusté",
        erreur=(
            "Le KPI « richesse ×2,6 » (odds ratio ajusté) était affiché juste à côté d'un graphique "
            "de <b>taux bruts</b> (7,0 % → 30,8 %, soit un écart réel de ×4,5), sans distinction. "
            "Pour l'éducation les deux chiffres étaient proches par coïncidence (OR=4,83 vs ratio "
            "brut=4,88) — mais pour la richesse l'écart est net (OR=2,56 vs ratio brut=4,49)."
        ),
        cause=(
            "Les KPI ont été calculés à partir du tableau de régression (odds ratio ajustés), tandis "
            "que les graphiques juste à côté montrent des taux bruts — sans jamais nommer explicitement "
            "laquelle des deux mesures était utilisée où."
        ),
        correction=(
            "Chaque KPI porte désormais le libellé « OR ajusté ». La légende du graphique éducation/"
            "richesse explique maintenant que l'écart de richesse brut (×4,5) retombe à ×2,6 une fois "
            "éducation et urbanicité contrôlées — c'est-à-dire qu'une partie de l'effet apparent de la "
            "richesse est en réalité un effet d'éducation et d'urbanicité qui passe <i>à travers</i> la richesse."
        ),
    ),
    dict(
        titre="3. Odds ratio présenté comme une multiplication directe du taux",
        erreur=(
            "Une formulation du type « OR=4,83 → 4,8 fois plus de chances d'être dépistée » confond "
            "odds ratio et risque relatif. Ces deux mesures ne coïncident que lorsque l'événement est "
            "rare (&lt;10 %) — ici les taux vont de 7 % à 48 %, donc elles divergent nettement."
        ),
        cause=(
            "Simplification pédagogique excessive : l'odds ratio a été vulgarisé comme un simple "
            "multiplicateur de taux, ce qui n'est vrai qu'en apparence pour l'éducation dans ce jeu "
            "de données précis (coïncidence numérique), pas en général."
        ),
        correction=(
            "Les textes du dashboard distinguent maintenant explicitement « taux brut » et « odds "
            "ratio ajusté » partout où les deux apparaissent, sans jamais les présenter comme des "
            "équivalents."
        ),
    ),
    dict(
        titre="4. Surinterprétation : « le clivage ville/campagne disparaît »",
        erreur=(
            "Milieu urbain (ajusté) : OR=1,21 [0,99–1,49], p=0,069. Non significatif à 5 % ne veut "
            "pas dire « preuve d'absence d'effet » — l'intervalle de confiance reste compatible avec "
            "un effet positif modéré (jusqu'à +49 %)."
        ),
        cause=(
            "Volonté d'un titre percutant (règle « le titre doit porter la conclusion ») appliquée au "
            "détriment de la prudence statistique. Point aggravant : Abidjan, la région de référence "
            "du modèle, est elle-même 100 % urbaine — ce qui dilue structurellement l'effet propre du "
            "milieu qu'on peut détecter séparément de l'effet région."
        ),
        correction=(
            "Le titre principal ne mentionne plus le milieu urbain/rural. L'OR, l'intervalle de "
            "confiance et la p-value du milieu sont affichés explicitement en légende du forest plot, "
            "avec la précision sur la redondance Abidjan/urbain — sans conclusion abusive."
        ),
    ),
    dict(
        titre="5. Tests multiples non corrigés (13 régions testées)",
        erreur=(
            "13 comparaisons région-vs-Abidjan testées simultanément à p&lt;0,05 chacune, sans "
            "correction. Même si aucune région n'avait de vrai effet, on attendrait ~0,65 faux "
            "positif par hasard rien qu'avec ce nombre de tests."
        ),
        cause=(
            "Chaque odds ratio régional a été interprété comme un test indépendant isolé, sans tenir "
            "compte du nombre total de comparaisons effectuées dans la même famille de tests."
        ),
        correction=(
            "Correction de Holm-Bonferroni appliquée aux 13 p-values régionales. Résultat : Gôh-Djiboua "
            "(p corrigé=0,0004) et Yamoussoukro (p corrigé=0,016) restent confirmées. Savanes et Woroba "
            "(significatives avant correction, p=0,040 et 0,038) basculent en « à surveiller ». Zanzan "
            "(positif, p=0,007 avant correction) bascule aussi en « à surveiller »."
        ),
    ),
    dict(
        titre="6. Facteur de confusion manquant : l'âge",
        erreur=(
            "L'âge n'était pas dans le modèle, alors qu'il est plausiblement lié à la fois à "
            "l'éducation (générations plus jeunes plus scolarisées en Côte d'Ivoire) et à "
            "l'exposition cumulée aux soins de santé."
        ),
        cause="Omission au moment de la spécification initiale du modèle.",
        correction=(
            "Âge (v012, continu) ajouté comme covariable de contrôle. Résultat : effet de l'âge "
            "significatif (OR=1,015 par année, p&lt;0,001) ; l'ajout renforce légèrement l'effet mesuré "
            "de l'éducation (secondaire : 2,71→3,04 ; supérieur : 4,83→5,04), confirmant qu'il s'agit "
            "bien d'un effet propre de l'éducation, pas d'un effet de génération déguisé."
        ),
    ),
    dict(
        titre="7. Éléments de traçabilité manquants",
        erreur=(
            "Définition exacte de la variable de dépistage absente du dashboard ; région de référence "
            "du modèle non nommée explicitement ; effectifs (n) par région absents — impossible de "
            "juger si un taux repose sur 50 ou 500 femmes."
        ),
        cause="Informations connues et documentées dans le journal de projet, mais jamais reportées sur le livrable visuel lui-même.",
        correction=(
            "Ajout sur le dashboard : définition précise (« examen clinique du sein par un "
            "professionnel de santé, déjà eu dans sa vie — pas une mammographie »), mention explicite "
            "d'Abidjan/rural/aucune éducation/plus pauvres comme références, et effectif (n) par "
            "région visible au survol et dans la table."
        ),
    ),
    dict(
        titre="8. Lisibilité : axes et mise en page",
        erreur=(
            "Graduations de l'axe logarithmique du forest plot ambiguës sous 1 (affichage sans le "
            "« 0, »). Graphiques éducation (échelle 0–65) et richesse (échelle 0–40) sur des échelles "
            "différentes bien que comparés côte à côte, faussant la lecture visuelle des longueurs de barres."
        ),
        cause="Paramètres par défaut de la bibliothèque graphique non ajustés pour ce cas précis.",
        correction=(
            "Graduations log explicites avec virgule française (0,25 / 0,5 / 1 / 2 / 4 / 8). "
            "Éducation et richesse réglés sur la même échelle (0–55 %)."
        ),
    ),
]

for issue in issues:
    story.append(Paragraph(issue["titre"], h2_style))
    story.append(Paragraph("Erreur identifiée", label_style))
    story.append(Paragraph(issue["erreur"], body_style))
    story.append(Paragraph("Cause", label_style))
    story.append(Paragraph(issue["cause"], body_style))
    story.append(Paragraph("Correction apportée", label_style))
    story.append(Paragraph(issue["correction"], body_style))

story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", color=GRID, thickness=1))
story.append(Paragraph("Verdict — 1ère revue", h2_style))
story.append(Paragraph(
    "Sur les 8 catégories de critiques reçues, les 8 se sont révélées fondées après vérification "
    "indépendante des chiffres. Aucune n'a été écartée. La correction la plus structurante "
    "(au-delà des libellés) est la correction de tests multiples sur les régions, qui change "
    "réellement le nombre de régions qu'on peut défendre comme prioritaires sans ambiguïté : "
    "<b>2 confirmées (Gôh-Djiboua, Yamoussoukro) et 2 à surveiller (Savanes, Woroba)</b>, et non "
    "4 traitées avec la même confiance.",
    verdict_style,
))

story.append(Spacer(1, 6))
story.append(HRFlowable(width="100%", color=GRID, thickness=1))
story.append(Paragraph("Deuxième revue : nouvelles erreurs trouvées", h2_style))

issues_round2 = [
    dict(
        titre="9. Deux chiffres restés figés après une mise à jour du modèle",
        erreur=(
            "La légende du panneau éducation/richesse affichait « retombe à ×2,6 » alors que le KPI, "
            "lui, affichait 2,48 (modèle recalculé avec l'âge). Le titre du panneau annonçait « ×4,5 » "
            "pour le taux brut de richesse, alors que 30,8/7,0 = 4,37."
        ),
        cause=(
            "Les deux chiffres avaient été tapés à la main dans le texte au moment de la première "
            "rédaction, au lieu de référencer les variables déjà calculées dans le script "
            "(<code>or_richesse_max</code>, <code>ratio_richesse</code>). Quand le modèle a été recalculé "
            "avec l'âge, le texte figé n'a pas suivi."
        ),
        correction=(
            "Tous les chiffres dérivés du dashboard sont désormais interpolés directement depuis les "
            "variables calculées (f-strings), plus aucun chiffre tapé à la main dans un titre ou une "
            "légende."
        ),
    ),
    dict(
        titre="10. L'âge, contrôlé mais invisible",
        erreur=(
            "L'âge était dans le modèle mais n'apparaissait dans aucun graphique, aucun KPI, aucune "
            "mention. Le titre principal employait aussi le mot « déterminants », qui sonne causal, "
            "alors que le dashboard lui-même précise plus loin qu'il s'agit d'association, pas de causalité."
        ),
        cause="Oubli d'affichage, et incohérence de vocabulaire entre le titre et les limites annoncées.",
        correction=(
            "Un 4ᵉ KPI affiche désormais l'effet de l'âge (OR=1,015/an). Le titre principal remplace "
            "« déterminants » par « fortement associés »."
        ),
    ),
    dict(
        titre="11. Recommandation plus forte que ce que le modèle prouve",
        erreur=(
            "« Cibler les femmes pauvres et peu éduquées, quelle que soit leur région » suppose que "
            "l'effet de l'éducation est le même partout — jamais testé (pas d'interaction éducation×région "
            "dans le modèle)."
        ),
        cause="Généralisation implicite d'un effet moyen national à toutes les régions sans vérification.",
        correction=(
            "La limite « effet de l'éducation supposé uniforme entre régions (interaction non testée) » "
            "est désormais explicitement affichée."
        ),
    ),
    dict(
        titre="12. Yamoussoukro : critère de priorité jamais expliqué",
        erreur=(
            "Yamoussoukro était citée parmi les régions « confirmées », alors que son taux brut (12,3 %) "
            "n'est que le 7ᵉ sur 14 — ni le plus bas ni un cas visuellement évident. Le critère utilisé "
            "pour choisir les régions prioritaires n'était jamais énoncé."
        ),
        cause=(
            "Les régions ont été choisies sur la base de l'odds ratio ajusté (régression), sans jamais "
            "dire explicitement que ce critère diffère du simple classement par taux brut."
        ),
        correction=(
            "Vérification faite : la composition de Yamoussoukro est beaucoup plus favorable que la "
            "moyenne nationale (urbaine, riche, éduquée), ce qui devrait prédire un taux bien supérieur à "
            "ce qui est observé. C'est l'inverse exact du cas Zanzan (étudié plus tôt) : une région qui "
            "sous-performe par rapport à son profil, signe probable d'un déficit d'offre de soins local. "
            "Le dashboard explique maintenant ce critère et cette anomalie directement en légende."
        ),
    ),
    dict(
        titre="13. Ligne de référence manquante dans le tableau",
        erreur="Abidjan, la région de référence du modèle (OR=1 par définition), n'apparaissait dans aucune table.",
        cause="Oubli — la référence n'est jamais une ligne de sortie de la régression, donc jamais ajoutée automatiquement.",
        correction="Ligne Abidjan ajoutée explicitement au tableau (effectif, taux brut, OR=1,00, statut = Référence).",
    ),
    dict(
        titre="14. Test de robustesse par âge (suggéré par le relecteur) — la correction la plus importante",
        erreur=(
            "Le dashboard présentait Gôh-Djiboua et Yamoussoukro comme des régions « confirmées » sur "
            "l'échantillon complet (15-49 ans), sans avoir vérifié si ce résultat tenait sur une "
            "population plus réaliste pour le dépistage du sein (femmes plus âgées)."
        ),
        cause="Aucun test de robustesse (sous-échantillon, spécification alternative) n'avait été fait avant de présenter la conclusion régionale comme solide.",
        correction=(
            "Modèle refait sur les 30-49 ans (n=6 853) et les 40-49 ans (n=2 572). Résultat : "
            "<b>éducation et richesse restent fortement significatives sur les deux sous-échantillons</b> "
            "(OR éducation supérieure : 3,90 et 5,15 ; OR richesse max : 3,80 et 3,21). En revanche, "
            "<b>ni Gôh-Djiboua ni Yamoussoukro ne restent significatives après correction</b> dès qu'on "
            "restreint aux 30 ans et plus (p corrigé passe de 0,0004/0,016 à 0,11/0,13, puis à 0,61/1,00 "
            "sur les 40-49 ans). Le signal régional est fragile ; le signal éducation/richesse est robuste. "
            "Le dashboard ne présente plus les régions comme « confirmées » mais comme « signal fragile, à "
            "confirmer », et la recommandation met l'accent sur éducation/richesse en priorité."
        ),
    ),
]

for issue in issues_round2:
    story.append(Paragraph(issue["titre"], h2_style))
    story.append(Paragraph("Erreur identifiée", label_style))
    story.append(Paragraph(issue["erreur"], body_style))
    story.append(Paragraph("Cause", label_style))
    story.append(Paragraph(issue["cause"], body_style))
    story.append(Paragraph("Correction apportée", label_style))
    story.append(Paragraph(issue["correction"], body_style))

story.append(Spacer(1, 10))
story.append(HRFlowable(width="100%", color=GRID, thickness=1))
story.append(Paragraph("Verdict final", h2_style))
story.append(Paragraph(
    "Sur un total de 14 critiques reçues en deux cycles de revue, les 14 se sont révélées fondées après "
    "vérification indépendante. La découverte la plus importante est la 14ᵉ : le signal régional "
    "(Gôh-Djiboua, Yamoussoukro) ne résiste pas à un simple changement de tranche d'âge, alors que "
    "l'effet de l'éducation et de la richesse, lui, tient bon sur toutes les spécifications testées. "
    "Le dashboard final met donc l'accent sur le message robuste (éducation, richesse) et traite le "
    "signal régional avec la prudence qu'il mérite, plutôt que de le présenter comme acquis.",
    verdict_style,
))
story.append(Paragraph(
    "Leçon retenue : un titre « insight-first » percutant ne doit jamais être écrit avant d'avoir "
    "vérifié le calcul exact qu'il annonce, et une conclusion « phare » ne doit jamais être présentée "
    "avant d'avoir survécu à au moins un test de robustesse.",
    verdict_style,
))

doc.build(story)
print("Rapport PDF écrit : reports/rapport_corrections.pdf")
