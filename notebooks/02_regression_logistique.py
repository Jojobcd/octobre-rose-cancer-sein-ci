import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
import statsmodels.api as sm

COLS = ["v005", "v021", "v024", "v025", "v106", "v190", "v484a"]
df = pd.read_stata(
    "data/raw/CIIR81DT/CIIR81FL.DTA",
    columns=COLS,
    convert_categoricals=True,
)

df["poids"] = df["v005"] / 1_000_000
df = df[df["v484a"] != "don't know"].copy()
df["depistee"] = (df["v484a"] == "yes").astype(int)

formula = (
    "depistee ~ "
    "C(v025, Treatment('rural')) + "
    "C(v106, Treatment('no education')) + "
    "C(v190, Treatment('poorest')) + "
    "C(v024, Treatment('abidjan'))"
)

model = smf.glm(
    formula=formula,
    data=df,
    family=sm.families.Binomial(),
    freq_weights=df["poids"],
)
result = model.fit(cov_type="cluster", cov_kwds={"groups": df["v021"]})

summary_df = pd.DataFrame({
    "odds_ratio": np.exp(result.params),
    "ic_bas": np.exp(result.conf_int()[0]),
    "ic_haut": np.exp(result.conf_int()[1]),
    "p_value": result.pvalues,
}).round(3)

summary_df = summary_df.drop(index="Intercept")
summary_df["significatif_5pct"] = summary_df["p_value"] < 0.05
summary_df = summary_df.sort_values("odds_ratio")

pd.set_option("display.max_rows", None)
pd.set_option("display.max_columns", None)
pd.set_option("display.width", 160)
print(summary_df.to_string())
