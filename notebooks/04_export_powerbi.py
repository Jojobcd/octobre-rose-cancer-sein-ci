"""Exporte des données propres et labellisées pour Power BI Desktop.

Power BI n'est pas fait pour calculer une régression logistique (ce n'est pas
son métier, DAX ne fait pas ça bien) : on continue à calculer le modèle en
Python, et on exporte seulement son résultat pour que Power BI le visualise.
En revanche, le taux de dépistage pondéré DOIT être recalculé par une mesure
DAX dans Power BI (pas pré-calculé ici) pour que les segments (slicers)
puissent le recalculer dynamiquement quand on filtre.
"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import depistage as dp  # noqa: E402

Path("data/processed").mkdir(parents=True, exist_ok=True)

# ---------- 1. Données individuelles, labellisées, prêtes pour Power BI ----------
df = dp.load_clean()
export = pd.DataFrame({
    "region": df["v024"].map(dp.LABELS_REGION),
    "milieu": df["v025"].map(dp.LABELS_MILIEU),
    "education": df["v106"].map(dp.LABELS_EDUC),
    "richesse": df["v190"].map(dp.LABELS_RICHESSE),
    "age": df["v012"],
    "poids": df["poids"],
    "depistee": df["depistee"],
})
export.to_csv("data/processed/eds_ci_depistage.csv", index=False, encoding="utf-8-sig")
print(f"Export individuel : {len(export)} lignes -> data/processed/eds_ci_depistage.csv")

# ---------- 2. Résultats de la régression, prêts pour le forest plot Power BI ----------
reg = dp.fit_regression(df)


def parse_row(idx: str):
    if "v025" in idx:
        group, raw = "Milieu", re.search(r"\[T\.(.+)\]", idx).group(1)
        label = dp.LABELS_MILIEU[raw]
    elif "v106" in idx:
        group, raw = "Éducation", re.search(r"\[T\.(.+)\]", idx).group(1)
        label = dp.LABELS_EDUC[raw]
    elif "v190" in idx:
        group, raw = "Richesse", re.search(r"\[T\.(.+)\]", idx).group(1)
        label = dp.LABELS_RICHESSE[raw]
    else:
        group, raw = "Région", re.search(r"\[T\.(.+)\]", idx).group(1)
        label = dp.LABELS_REGION[raw]
    return group, label


def statut(row):
    if row["significatif_corrige"] and row["odds_ratio"] < 1:
        return "Défavorisé (confirmé)"
    if row["significatif_corrige"] and row["odds_ratio"] > 1:
        return "Favorisé (confirmé)"
    if row["significatif"] and not row["significatif_corrige"]:
        return "À surveiller (significatif avant correction seulement)"
    return "Pas d'effet significatif"


rows = []
for idx, row in reg.iterrows():
    if idx == "v012":
        rows.append({"groupe": "Âge (contrôle)", "facteur": "par année d'âge supplémentaire", **row.to_dict()})
        continue
    group, label = parse_row(idx)
    rows.append({"groupe": group, "facteur": label, **row.to_dict()})

reg_export = pd.DataFrame(rows)
reg_export["statut"] = reg_export.apply(statut, axis=1)
reg_export = reg_export.rename(columns={
    "odds_ratio": "odds_ratio",
    "ic_bas": "ic_bas",
    "ic_haut": "ic_haut",
    "p_value": "p_value",
})
# colonnes utiles pour un graphique barre-d'erreur dans Power BI (delta vs point central)
reg_export["erreur_bas"] = reg_export["odds_ratio"] - reg_export["ic_bas"]
reg_export["erreur_haut"] = reg_export["ic_haut"] - reg_export["odds_ratio"]

reg_export.to_csv("data/processed/regression_resultats.csv", index=False, encoding="utf-8-sig")
print(f"Export régression : {len(reg_export)} lignes -> data/processed/regression_resultats.csv")
