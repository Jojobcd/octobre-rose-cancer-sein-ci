import pandas as pd

COLS = ["v005", "v024", "v025", "v106", "v190", "v484a"]
df = pd.read_stata(
    "data/raw/CIIR81DT/CIIR81FL.DTA",
    columns=COLS,
    convert_categoricals=True,
)

df["poids"] = df["v005"] / 1_000_000

print("Répartition brute de v484a :")
print(df["v484a"].value_counts(dropna=False))
print()

df_clean = df[df["v484a"] != "don't know"].copy()
df_clean["depistee"] = (df_clean["v484a"] == "yes").astype(int)

def taux_pondere(data, group_col=None):
    if group_col is None:
        return (data["depistee"] * data["poids"]).sum() / data["poids"].sum() * 100
    return data.groupby(group_col, observed=True).apply(
        lambda g: (g["depistee"] * g["poids"]).sum() / g["poids"].sum() * 100
    ).sort_values(ascending=False)

print(f"Taux national PONDÉRÉ   : {taux_pondere(df_clean):.1f} %")
print(f"Taux national NON pondéré : {df_clean['depistee'].mean()*100:.1f} %")
print()

print("--- Par milieu (v025) ---")
print(taux_pondere(df_clean, "v025").round(1))
print()

print("--- Par région (v024) ---")
print(taux_pondere(df_clean, "v024").round(1))
print()

print("--- Par éducation (v106) ---")
print(taux_pondere(df_clean, "v106").round(1))
print()

print("--- Par richesse (v190) ---")
print(taux_pondere(df_clean, "v190").round(1))
