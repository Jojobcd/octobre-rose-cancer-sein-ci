"""Chargement et calculs partagés : dépistage du cancer du sein, EDS-CI 2021."""
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.stats.multitest import multipletests

DTA_PATH = "data/raw/CIIR81DT/CIIR81FL.DTA"
COLS = ["v005", "v021", "v024", "v025", "v106", "v190", "v484a", "v012"]

LABELS_REGION = {
    "abidjan": "Abidjan", "sassandra-marahoue": "Sassandra-Marahoué",
    "montagnes": "Montagnes", "bas sassandra": "Bas-Sassandra",
    "denguele": "Denguélé", "savanes": "Savanes", "woroba": "Woroba",
    "lagunes": "Lagunes", "vallee du bandama": "Vallée du Bandama",
    "goh-djiboua": "Gôh-Djiboua", "lacs": "Lacs", "zanzan": "Zanzan",
    "yamoussoukro": "Yamoussoukro", "comoe": "Comoé",
}
LABELS_EDUC = {
    "no education": "Aucune éducation", "primary": "Primaire",
    "secondary": "Secondaire", "higher": "Supérieur",
}
LABELS_RICHESSE = {
    "poorest": "Plus pauvres", "poorer": "Pauvres", "middle": "Moyen",
    "richer": "Riches", "richest": "Plus riches",
}
LABELS_MILIEU = {"rural": "Rural", "urban": "Urbain"}

ORDRE_EDUC = ["no education", "primary", "secondary", "higher"]
ORDRE_RICHESSE = ["poorest", "poorer", "middle", "richer", "richest"]

# Variable cible : v484a = "a déjà eu un examen clinique du sein par un
# professionnel de santé" (question posée une seule fois, "jamais/déjà" -
# pas une fréquence, pas spécifiquement une mammographie). Population :
# femmes de 15 à 49 ans (échantillon standard EDS-CI).
DEFINITION_VARIABLE_CIBLE = (
    "Dépistage = a déjà eu un examen clinique du sein par un professionnel de "
    "santé (v484a, question binaire 'jamais vs déjà', pas une mammographie), "
    "parmi les femmes de 15 à 49 ans."
)


def load_clean(path: str = DTA_PATH) -> pd.DataFrame:
    df = pd.read_stata(path, columns=COLS, convert_categoricals=True)
    df["poids"] = df["v005"] / 1_000_000
    df = df[df["v484a"] != "don't know"].copy()
    df["depistee"] = (df["v484a"] == "yes").astype(int)
    return df


def taux_pondere(data: pd.DataFrame, group_col: str | None = None) -> pd.Series | float:
    if group_col is None:
        return (data["depistee"] * data["poids"]).sum() / data["poids"].sum() * 100
    return data.groupby(group_col, observed=True).apply(
        lambda g: (g["depistee"] * g["poids"]).sum() / g["poids"].sum() * 100
    )


def effectifs(data: pd.DataFrame, group_col: str) -> pd.Series:
    """Nombre de femmes interrogées (non pondéré) par groupe - pour juger la robustesse d'un taux."""
    return data.groupby(group_col, observed=True).size()


def ratio_taux_bruts(taux: pd.Series, reference: str) -> pd.Series:
    """Ratio du taux brut de chaque groupe vs le groupe de référence (PAS un odds ratio)."""
    return taux / taux[reference]


def fit_regression(df: pd.DataFrame) -> pd.DataFrame:
    """Régression logistique pondérée, erreurs-types cluster-robustes (v021),
    AVEC l'âge (v012, continu) comme facteur de confusion contrôlé.
    Référence : Abidjan / rural / aucune éducation / plus pauvres.
    """
    formula = (
        "depistee ~ "
        "C(v025, Treatment('rural')) + "
        "C(v106, Treatment('no education')) + "
        "C(v190, Treatment('poorest')) + "
        "C(v024, Treatment('abidjan')) + "
        "v012"
    )
    model = smf.glm(formula=formula, data=df, family=sm.families.Binomial(), freq_weights=df["poids"])
    result = model.fit(cov_type="cluster", cov_kwds={"groups": df["v021"]})

    out = pd.DataFrame({
        "odds_ratio": np.exp(result.params),
        "ic_bas": np.exp(result.conf_int()[0]),
        "ic_haut": np.exp(result.conf_int()[1]),
        "p_value": result.pvalues,
    }).drop(index="Intercept")
    out["significatif"] = out["p_value"] < 0.05

    # Correction de tests multiples (Holm-Bonferroni), appliquée uniquement à la
    # famille des 13 comparaisons régionales (c'est là que le nombre de tests
    # simultanés est élevé et pose un vrai risque de faux positifs).
    mask_region = out.index.str.contains("v024")
    rejet, p_corrige, _, _ = multipletests(out.loc[mask_region, "p_value"], method="holm")
    out["p_value_corrige"] = out["p_value"]
    out.loc[mask_region, "p_value_corrige"] = p_corrige
    out["significatif_corrige"] = out["p_value_corrige"] < 0.05
    # Hors région, pas de correction appliquée (une seule comparaison par famille) :
    out.loc[~mask_region, "significatif_corrige"] = out.loc[~mask_region, "significatif"]

    return out
