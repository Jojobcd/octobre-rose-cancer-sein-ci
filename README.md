# Octobre Rose — Accès au dépistage du cancer du sein en Côte d'Ivoire

Analyse des disparités d'accès au dépistage du cancer du sein en Côte d'Ivoire, pour identifier quels leviers (éducation, richesse, milieu, région) cibler en priorité lors des campagnes de sensibilisation type Octobre Rose.

**[📊 Voir le dashboard](reports/dashboard.html)** · **[📄 Rapport des corrections (revue externe)](reports/rapport_corrections.pdf)** · **[📓 Journal de projet](docs/journal.md)**

## Question business

Quels profils de femmes (région, milieu urbain/rural, éducation, niveau de richesse) ont le moins accès au dépistage du cancer du sein en Côte d'Ivoire ?

## Méthodologie

- **Source** : EDS-CI 2021 (DHS Program / INS Côte d'Ivoire), fichier Individual Recode, 14 870 femmes de 15 à 49 ans.
- **Variable cible** : `v484a` — a déjà eu un examen clinique du sein par un professionnel de santé (pas une mammographie).
- **Taux pondérés** par le poids d'enquête (`v005`), pour corriger le plan d'échantillonnage.
- **Régression logistique pondérée** (âge + éducation + richesse + région + milieu), erreurs-types cluster-robustes sur la grappe d'enquête (`v021`), correction de Holm-Bonferroni sur les 13 comparaisons régionales.
- **Test de robustesse** : le modèle a été refait sur les 30-49 ans et 40-49 ans pour vérifier si les conclusions tiennent sur une population plus proche de la cible réelle du dépistage (`notebooks/06_robustesse_age.py`).

## Résultats clés

- Taux national de dépistage (pondéré) : **17,5 %** — à peine une femme sur six.
- **Éducation et richesse sont les facteurs les plus fortement et les plus robustement associés** au dépistage (odds ratio ajusté ×5,04 et ×2,48), confirmés sur toutes les tranches d'âge testées.
- Le signal régional (deux régions semblant défavorisées) ne résiste **pas** à une restriction d'âge plus réaliste — traité comme une piste à confirmer, pas comme un acquis.
- Aucun effet indépendant démontré du simple fait de vivre en ville ou à la campagne, une fois éducation et richesse pris en compte.

## Process : construit, challengé, corrigé

Ce projet n'a pas été présenté tel quel au premier jet. Il a été soumis à une revue critique externe en deux cycles — **14 points soulevés, les 14 confirmés fondés après vérification** : un titre avec un chiffre faux, une confusion entre taux brut et odds ratio ajusté, des tests multiples non corrigés, un facteur de confusion (l'âge) oublié, et surtout un test de robustesse qui a fait tomber une conclusion présentée comme solide. Le détail complet (erreur → cause → correction) est dans [`reports/rapport_corrections.pdf`](reports/rapport_corrections.pdf).

## Reproduire l'analyse

```bash
pip install -r requirements.txt
```

Les microdonnées DHS ne sont pas incluses dans ce dépôt (licence DHS, redistribution interdite — voir ci-dessous). Pour reproduire : demander l'accès gratuit sur [dhsprogram.com](https://dhsprogram.com) (enquête "Côte d'Ivoire: Standard DHS, 2021"), placer le fichier `CIIR81FL.DTA` dans `data/raw/CIIR81DT/`, puis exécuter les scripts dans `notebooks/` dans l'ordre.

## Structure

```
notebooks/   scripts d'analyse, dans l'ordre d'exécution
src/         code réutilisable (chargement, pondération, régression)
reports/     dashboard HTML et rapport PDF (livrables finaux)
docs/        journal de projet (décisions, leçons apprises)
data/        non versionné (licence DHS), structure préservée par .gitkeep
```

## Confidentialité des données

Conformément aux conditions d'utilisation du DHS Program, les microdonnées individuelles ne sont ni incluses ni redistribuées dans ce dépôt — seuls des résultats agrégés sont publiés. Ce projet est pédagogique et ne remplace pas un avis médical.

## Outils

Python, pandas, statsmodels (régression logistique pondérée, erreurs-types cluster-robustes), Plotly (dashboard).
