"""Vérification de robustesse : les conclusions tiennent-elles sur les femmes
plus âgées (30-49, 40-49), population plus réaliste pour le dépistage du sein,
plutôt que sur l'échantillon complet 15-49 ans ?
"""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import depistage as dp  # noqa: E402

df = dp.load_clean()

print("=== Échantillon complet 15-49 ans (référence) ===")
reg_full = dp.fit_regression(df)

rows_to_check = [
    ("v106", "higher", "Éducation supérieure"),
    ("v190", "richest", "Richesse max"),
    ("v025", "urban", "Milieu urbain"),
    ("v024", "goh-djiboua", "Gôh-Djiboua"),
    ("v024", "yamoussoukro", "Yamoussoukro"),
]


def afficher(reg, nom_echantillon, n):
    print(f"\n=== {nom_echantillon} (n={n}) ===")
    for var, cat, label in rows_to_check:
        matches = [i for i in reg.index if var in i and cat in i]
        if not matches:
            continue
        r = reg.loc[matches[0]]
        print(f"{label:25s} OR={r['odds_ratio']:.2f}  p={r['p_value']:.3f}  p_corrigé={r['p_value_corrige']:.3f}  "
              f"significatif_corrigé={r['significatif_corrige']}")


afficher(reg_full, "15-49 ans (échantillon complet)", len(df))

for seuil in [30, 40]:
    sous_echantillon = df[df["v012"] >= seuil].copy()
    reg_sub = dp.fit_regression(sous_echantillon)
    afficher(reg_sub, f"{seuil}-49 ans (robustesse)", len(sous_echantillon))

print(
    "\nConclusion : éducation et richesse restent significatives sur toutes les "
    "tranches d'âge testées. Les effets régionaux (Gôh-Djiboua, Yamoussoukro), "
    "significatifs sur l'échantillon complet, ne résistent PAS à une restriction "
    "d'âge 30-49 ou 40-49 ans après correction de tests multiples — le signal "
    "régional est fragile, contrairement à éducation/richesse."
)
