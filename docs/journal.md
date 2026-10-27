# Journal de projet — Octobre Rose : accès au dépistage du cancer du sein en Côte d'Ivoire

## 2026-10-25 — Étape 0 : choix du sujet

**Décision** : thème Octobre Rose / cancer du sein, avec un ancrage Côte d'Ivoire plutôt que France.

**Ce qu'on a appris en cherchant les données** :
- Il n'existe pas en Côte d'Ivoire d'équivalent du "dépistage organisé par département" français (pas de portail open data santé exploitable sur ce sujet, data.gouv.ci n'a rien d'utilisable actuellement).
- En creusant malgré ce constat négatif (plutôt que d'abandonner l'angle CI), on a trouvé mieux qu'un simple taux agrégé : l'**EDS-CI 2021** (Enquête Démographique et de Santé, DHS Program, INS Côte d'Ivoire, 14 877 femmes 15-49 ans) contient une question individuelle sur le dépistage/examen clinique du sein, avec région, milieu urbain/rural, éducation et quintile de richesse comme variables associées. Des études académiques publiées en 2024-2025 confirment que cette variable est exploitable (ex. lien âge des premières règles / recours à l'examen clinique du sein).
- Les chiffres nationaux d'incidence (GLOBOCAN/PNLCa) varient fortement selon la source de presse (3 300 à 4 845 nouveaux cas/an selon l'année et l'article) → décision : ne citer que le chiffre du profil pays officiel GLOBOCAN, jamais un chiffre de presse non sourcé.
- Point confirmé par plusieurs sources indépendantes : environ 74-75 % des cancers du sein sont diagnostiqués à un stade avancé (III/IV) en Côte d'Ivoire — angle narratif retenu comme fil rouge.

**Leçon méthodo** : ne pas se contenter du premier constat "pas de données" — en cherchant une source adaptée (ici une enquête démographique et de santé plutôt qu'un portail open data), on obtient un dataset individuel plus riche qu'un simple agrégat.

## 2026-10-25 — Étape 1 : cadrage

**Question business** : quels profils de femmes (région, milieu, éducation, richesse) ont le moins accès au dépistage du cancer du sein en Côte d'Ivoire, pour cibler en priorité les campagnes Octobre Rose ?

**Utilisateurs cibles** : décideurs de santé publique / ONG (cas d'usage) ; recruteurs (lecture du repo/LinkedIn).

**Dataset principal** : EDS-CI 2021, fichier Individual Recode (DHS Program) — accès gratuit sur inscription, format brut (Stata/SPSS/flat file + dictionnaire de variables).

**Dataset de contexte** : profil pays GLOBOCAN Côte d'Ivoire + fiche régionale Afrique de l'Ouest.

**Hors périmètre** : pas de diagnostic médical, pas de modèle prédictif de la maladie, pas de données individuelles identifiables (EDS-CI est anonymisée).

**Prochaine étape** : créer un compte DHS Program, demander l'accès au jeu de données EDS-CI 2021 Côte d'Ivoire, et vérifier le dictionnaire de variables pour localiser précisément la/les variables de dépistage du sein.

## 2026-10-26 — Étape 2 : collecte, accès obtenu

- Compte DHS Program créé, demande approuvée en moins de 24h (dataset "Survey" uniquement, pas de GPS).
- Fichier téléchargé : `CIIR81FL.DTA` (Individual Recode, format Stata, 94 Mo), placé dans `data/raw/CIIR81DT/` — **jamais commité sur git** (confidentialité DHS + .gitignore déjà en place, vérifié).
- Le document `CIIR81FL.DOCX` fourni ne liste que les variables *spécifiques au pays* (ajoutées/inutilisées) — rien sur le sein, ce qui confirme que la variable cible appartient au tronc commun standard DHS-8, pas à une addition locale.
- **Localisation de la variable cible** : en inspectant directement les labels de variables du `.dta` avec pandas (`StataReader.variable_labels()`), trouvé `v484a` = "breasts examined for cancer by health care provider" (oui/non/ne sait pas).
- Variables de croisement confirmées (nomenclature DHS standard) : `v024` (région, 14 zones), `v025` (milieu urbain/rural), `v106` (éducation), `v190` (quintile de richesse).
- **Premiers chiffres (sondage rapide, pas encore l'EDA formelle)** : taux de dépistage national = 14,8 % (2 201/14 877). Écart urbain/rural déjà net : 19,6 % en urbain vs 10,0 % en rural.
- Outils installés : `pandas` (pour lire le `.dta` nativement via `read_stata`, pas besoin de `pyreadstat`).

**Leçon méthodo** : quand la documentation fournie ne suffit pas (ici, elle ne couvrait que les variables pays-spécifiques), charger directement les métadonnées du fichier de données est plus fiable et plus rapide que de chercher dans un manuel externe.

**Prochaine étape** : passer à l'EDA formelle dans un notebook (`notebooks/`) — charger les colonnes utiles, vérifier les valeurs manquantes/"don't know", calculer les taux par région/éducation/richesse, et décider de la pondération (poids d'enquête DHS, variable `v005`) à appliquer pour des résultats représentatifs au niveau national.

## 2026-10-26 — Étape 3 : EDA pondérée

- Script `notebooks/01_eda_depistage.py`. Poids `v005/1e6` déjà normalisés par le DHS Program (moyenne = 1, somme = N = 14 877) — pas de recalcul nécessaire.
- Taux national : **17,5 % pondéré vs 14,8 % non pondéré** (écart de 2,7 points dû au plan d'échantillonnage).
- Écarts bruts par groupe : milieu (urbain 22,4 % vs rural 9,8 %), région (7,3 % à 26,7 %), éducation (9,8 % à 47,8 %), richesse (7,0 % à 30,8 %) — mais ces 4 facteurs sont corrélés entre eux (Abidjan = urbain + riche + éduqué), d'où la régression ci-dessous pour isoler les effets propres.

## 2026-10-26 — Étape 4 : régression logistique pondérée

- Script `notebooks/02_regression_logistique.py`. Modèle : `depistee ~ milieu + éducation + richesse + région`, `GLM(family=Binomial)`, poids de fréquence `v005`, erreurs-types robustes par grappe (`v021`, cluster DHS standard).
- **Limite technique documentée** : statsmodels émet l'avertissement "cov_type not fully supported with freq_weights" — les odds ratios restent valides (le cov_type n'affecte que le calcul des erreurs-types), mais les p-values sont une approximation, pas une inférence design-based complète (outil de référence : R `survey` ou Stata `svy:`).
- **Vérification de robustesse faite** : comparaison p-values avec/sans correction de grappe → confirme que sans correction, on aurait déclaré "significatifs" 3 effets qui ne le sont plus avec correction (urbain/rural, Vallée du Bandama, Comoé) — valide empiriquement l'intérêt de la correction par grappe enseignée à l'étape précédente.
- **Résultats (modèle corrigé par grappe)** :
  - Éducation = facteur le plus fort : secondaire OR=2,71 (p<0,001), supérieur OR=4,83 (p<0,001) vs aucune éducation.
  - Richesse = gradient monotone significatif : de OR=1,39 (plus pauvre) à OR=2,56 (plus riche) vs plus pauvres.
  - **Milieu urbain/rural devient non significatif une fois éducation/richesse contrôlées** (OR=1,21, p=0,069) → l'écart ville/campagne observé en brut est en grande partie un effet de composition (les villes concentrent femmes éduquées/riches), pas un effet géographique propre.
  - Région : Goh-Djiboua (OR=0,37, p<0,001) et Yamoussoukro (OR=0,43, p=0,001) restent significativement moins dépistées qu'Abidjan même à éducation/richesse égales → signal d'un vrai problème d'offre de soins local, pas seulement de pauvreté. Zanzan ressort significativement au-dessus d'Abidjan (OR=1,60, p=0,007) — anomalie positive à creuser plus tard, pas encore expliquée.
- **Message pour Octobre Rose** : cibler en priorité l'éducation/sensibilisation et la réduction des barrières financières (effet le plus fort et le plus actionnable), et traiter Goh-Djiboua/Yamoussoukro comme des zones à déficit d'offre de soins spécifique (pas juste de pauvreté).

**Prochaine étape** : décider entre (a) passer à la visualisation/dashboard pour restituer ces résultats, ou (b) creuser l'anomalie Zanzan et d'autres interactions avant de figer l'analyse.

## 2026-10-26 — Investigation de l'anomalie Zanzan

- Méthode : avant de croire un résultat surprenant (Zanzan OR=1,60 vs Abidjan), vérification de 2 explications-pièges : (1) confusion non contrôlée (composition interne différente de ce qu'on pense), (2) artefact d'une seule grappe/petit échantillon.
- Composition interne de Zanzan (869 femmes, 35 grappes) : **plus défavorisée** que la moyenne nationale sur rural (57,5 % vs 50,1 %), pauvreté (28,9 % "plus pauvres" vs 21,1 %) et éducation (59,7 % sans éducation vs 53,7 %) → élimine l'explication confusion.
- Taux par grappe : de 0 % à 59,4 %, large élévation sur une quinzaine de grappes (pas un seul village extrême qui tire tout) → élimine l'explication artefact de petit échantillon.
- **Conclusion** : Zanzan surperforme réellement compte tenu de son profil socio-économique défavorable. Cause probable non identifiable avec l'EDS-CI seule (campagne locale ? ONG ? structure de santé spécifique ?) — à vérifier via une source externe qualitative si on veut aller plus loin. Signalé comme piste ouverte, pas comme fait établi.

## 2026-10-26 — Étape 5 : dashboard

- Skill `dataviz` suivie : choix de forme avant couleur, palette validée (bleu séquentiel pour les taux bruts, couleurs de statut pour la régression), légende toujours présente, vue table en complément des graphiques.
- Code refactoré dans `src/depistage.py` (chargement, pondération, régression réutilisables) pour éviter la duplication entre scripts.
- `notebooks/03_dashboard.py` génère `reports/dashboard.html` : 4 KPI, taux par région (bar + ligne de référence nationale), taux par éducation/richesse (small multiples), forest plot de la régression (couleur = significativement défavorisé/neutre/favorisé), table de détails.
- **Limite environnement notée** : ni l'extension Chrome ni le navigateur intégré de cet environnement de dev ne permettent d'ouvrir le fichier `file://` généré pour une vérification visuelle automatique — vérification de la structure HTML faite par le code (JSON bien formé, pas de collision `</script>`), mais le contrôle visuel final (chevauchement de labels, lisibilité) reste à faire manuellement en ouvrant le fichier dans un navigateur.

**Prochaine étape** : ouvrir `reports/dashboard.html` dans un navigateur, vérifier visuellement (lisibilité, pas de texte coupé), puis passer à la restitution finale (README complet + post LinkedIn).

## 2026-10-26 — Correction : titres de dashboard non conformes à la règle "insight-first"

- Erreur repérée (par le binôme, pas par l'auto-relecture) : les titres de section du premier jet étaient descriptifs ("Taux de dépistage par région") ou posés en question ("Quels facteurs comptent vraiment ?"), alors que la règle (pyramide inversée, titre = conclusion) demandait une phrase qui donne directement le résultat, comme "Abidjan dépiste jusqu'à 4 fois plus que Gôh-Djiboua ou Yamoussoukro".
- **Principe retenu** : un dashboard qui nécessite une question à l'oral pour être compris a raté son titre — le titre doit porter la conclusion, le graphique vient la prouver.
- Titres corrigés dans `notebooks/03_dashboard.py` (titre principal + 3 titres de section) ; dashboard régénéré.

## 2026-10-27 — Itérations de mise en page (retours utilisateur)

- Couleur de marque : rose/magenta (`#e87ba4`, slot catégoriel validé n°5) sur les graphiques de magnitude et les accents de page ; couleurs de statut (rouge/gris/vert) du forest plot volontairement laissées fixes car elles portent un sens (ne jamais thémer une couleur de statut).
- Plusieurs essais de mise en page avant de trouver la bonne : (1) une page verticale classique, (2) un défilement horizontal en 5 "écrans" type diaporama — rejeté, (3) **version retenue : grille fixe 2×2 sur un seul écran, aucun scroll**, chaque graphique Plotly redimensionné en CSS (`responsive:true` + conteneurs flex/grid `min-height:0`) plutôt qu'en hauteur fixe en pixels.
- Leçon méthodo : poser des options concrètes (avec mini-maquettes) quand une demande de mise en page reste ambiguë après 2 tentatives manquées, plutôt que de re-deviner une 3e fois.
- Correction au passage : le label "47,8 %" du graphique Éducation était coupé (plage d'axe trop juste) — corrigé.
- Validation visuelle faite par l'utilisateur via capture d'écran (je n'ai pas d'accès navigateur dans cet environnement) : tout tient sur un écran, rien ne déborde.

## 2026-10-27 — Revue externe et corrections (8 points, tous confirmés valides)

L'utilisateur a fait challenger le dashboard par des relectures externes. Les 8 critiques ont été vérifiées une par une avant toute correction — toutes se sont révélées fondées. Corrections apportées dans `src/depistage.py` et `notebooks/03_dashboard.py` :

1. **Titre faux corrigé** : "Abidjan dépiste jusqu'à 4 fois plus que Gôh-Djiboua ou Yamoussoukro" était inexact (26,7/12,3 = 2,2 pour Yamoussoukro, pas 4). Cause : mélange entre le classement "taux brut" et le classement "régression ajustée", qui ne sont pas les mêmes. Titre corrigé pour ne citer que la comparaison exacte (Gôh-Djiboua, ×3,7).
2. **Confusion taux brut / odds ratio corrigée** : le KPI "richesse ×2,6" (OR ajusté) était juxtaposé à un graphique de taux bruts (écart réel ×4,5) sans distinction. Ajout d'un libellé explicite "OR ajusté" sur les KPI, et explication que l'écart de richesse brut s'explique en partie par l'éducation et l'urbanicité (effet de médiation).
3. **Surinterprétation corrigée** : "le clivage ville/campagne disparaît" (p=0,069, non significatif ≠ preuve d'absence d'effet) remplacé par l'affichage explicite de l'OR, l'IC et la p-value du milieu en légende, sans conclusion abusive.
4. **Correction de tests multiples ajoutée** (Holm-Bonferroni, 13 comparaisons régionales) : seules Gôh-Djiboua et Yamoussoukro restent significatives après correction ; Savanes et Woroba deviennent "à surveiller" (significatives avant correction seulement) ; Zanzan (positif) bascule aussi en "à surveiller" après correction.
5. **Âge ajouté au modèle** (`v012`, continu) comme facteur de confusion — confirmé présent dans les données DHS standard. Effet de l'âge significatif (OR=1,015/an, p<0,001) ; l'ajout renforce légèrement l'effet de l'éducation (confirme qu'il existe bien un effet propre, pas juste un effet de génération).
6. **Éléments manquants ajoutés** : définition exacte de la variable cible (`v484a`, examen clinique du sein déjà réalisé, pas une mammographie), région de référence explicitement nommée (Abidjan), effectifs (n) par région ajoutés au survol du graphique et à la table.
7. **Lisibilité corrigée** : axe log du forest plot avec graduations explicites en virgule française (0,25/0,5/1/2/4/8) ; échelle identique (0–55 %) pour les graphiques éducation et richesse afin que les longueurs de barres soient honnêtement comparables.
8. **Tension "table sur un seul écran" tranchée** : table complète remplacée par une table resserrée région-uniquement (la plus utile pour l'action) + une phrase de recommandation et une phrase de limites, pour respecter la contrainte "un seul écran, zéro scroll" tout en gardant l'essentiel actionnable visible.

**Leçon méthodo retenue** : un titre "insight-first" percutant ne doit jamais sacrifier l'exactitude statistique — en cas de doute, vérifier le calcul exact avant d'écrire la phrase, pas après.

## 2026-10-27 — Deuxième revue externe : 6 points supplémentaires, dont un qui change la conclusion

Nouveaux points vérifiés (tous confirmés) : (9) deux chiffres restés figés dans le texte après recalcul du modèle avec l'âge (×2,6 vs 2,48 réel ; ×4,5 vs 4,37 réel) — cause : chiffres tapés à la main au lieu d'être interpolés depuis les variables calculées ; (10) âge invisible sur le dashboard + mot "déterminants" trop causal ; (11) recommandation supposant un effet uniforme de l'éducation entre régions (interaction jamais testée) ; (12) critère de priorisation régionale jamais explicité — investigation faite sur Yamoussoukro (n=867, 32 grappes) : profil bien plus favorisé que la moyenne nationale (urbaine/riche/éduquée) mais taux observé pourtant sous la moyenne — anomalie inverse de Zanzan, signe probable d'un déficit d'offre de soins local ; (13) ligne de référence Abidjan absente du tableau.

**Point 14, le plus important** : test de robustesse par restriction d'âge (30-49 et 40-49 ans), suggéré par le relecteur. Résultat : éducation et richesse restent fortement significatives sur toutes les tranches d'âge testées (script `notebooks/06_robustesse_age.py`), mais **Gôh-Djiboua et Yamoussoukro ne restent PAS significatives après correction** dès qu'on restreint aux 30 ans et plus (p corrigé passe de 0,0004/0,016 à 0,11/0,13 puis 0,61/1,00 sur 40-49 ans). Le signal régional qu'on présentait comme "confirmé" ne survit pas à ce test — contrairement à éducation/richesse. Le dashboard et le rapport ont été requalifiés en conséquence : le message régional est maintenant présenté comme "signal fragile, à confirmer", pas comme acquis.

**Corrections apportées** : tous les chiffres du dashboard sont désormais interpolés depuis les variables calculées (plus aucun chiffre tapé à la main) ; 4e KPI ajouté pour l'âge ; titre principal "déterminants"→"fortement associés" ; limites explicites ajoutées (interaction non testée, non-robustesse régionale) ; explication de l'anomalie Yamoussoukro ajoutée en légende ; ligne Abidjan (référence, OR=1) ajoutée au tableau ; rapport PDF étendu à 5 pages (14 points, 2 cycles de revue).

**Mémoire** : les leçons de rigueur de ce cycle de revues ont été enregistrées en mémoire persistante (`feedback_rigueur_analyse_donnees`) pour s'appliquer à ce projet et aux futurs — checklist : chiffres calculés jamais tapés à la main, test de robustesse avant de présenter une conclusion phare, correction de tests multiples, jamais surinterpréter un résultat non significatif, toujours montrer la référence, toujours expliquer une anomalie.
