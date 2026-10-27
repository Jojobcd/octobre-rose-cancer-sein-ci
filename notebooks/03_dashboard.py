import re
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))
import depistage as dp  # noqa: E402

# ---------- Palette (dataviz skill, reference instance) ----------
ACCENT = "#e87ba4"       # marque Octobre Rose (slot catégoriel validé n°5)
GOOD = "#0ca30c"         # favorisé, confirmé après correction
SERIOUS = "#ec835a"      # défavorisé, confirmé après correction
WARNING = "#fab219"      # significatif avant correction, mais pas après (tests multiples)
MUTED = "#898781"        # pas d'effet détecté
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
GRID = "#e1e0d9"
SURFACE = "#fcfcfb"

CHART_LAYOUT = dict(
    paper_bgcolor=SURFACE,
    plot_bgcolor=SURFACE,
    font=dict(family="system-ui, -apple-system, Segoe UI, sans-serif", color=INK, size=11),
    autosize=True,
)

# ---------- Données ----------
df = dp.load_clean()
taux_national = dp.taux_pondere(df)

taux_region = dp.taux_pondere(df, "v024").sort_values()
n_region = dp.effectifs(df, "v024")
taux_educ = dp.taux_pondere(df, "v106").reindex(dp.ORDRE_EDUC)
taux_richesse = dp.taux_pondere(df, "v190").reindex(dp.ORDRE_RICHESSE)

ratio_educ = dp.ratio_taux_bruts(taux_educ, "no education")
ratio_richesse = dp.ratio_taux_bruts(taux_richesse, "poorest")
ratio_region_max = taux_region.max() / taux_region.min()

reg = dp.fit_regression(df)

# ---------- KPI (toutes les valeurs viennent du calcul, aucune tapée à la main) ----------
or_educ_sup = reg.loc[[i for i in reg.index if "v106" in i and "higher" in i][0], "odds_ratio"]
or_richesse_max = reg.loc[[i for i in reg.index if "v190" in i and "richest" in i][0], "odds_ratio"]
or_milieu = reg.loc[[i for i in reg.index if "v025" in i][0]]
or_age = reg.loc["v012"]

mask_region_defav = reg.index.str.contains("v024") & (reg["odds_ratio"] < 1)
n_confirmees = int((mask_region_defav & reg["significatif_corrige"]).sum())
n_a_surveiller = int((mask_region_defav & reg["significatif"] & ~reg["significatif_corrige"]).sum())

kpis = [
    ("Taux national de dépistage (pondéré)", f"{taux_national:.1f} %"),
    ("OR ajusté — Éducation supérieure vs aucune", f"× {or_educ_sup:.2f}"),
    ("OR ajusté — Plus riches vs plus pauvres", f"× {or_richesse_max:.2f}"),
    ("OR ajusté — Âge, par année supplémentaire", f"× {or_age['odds_ratio']:.3f}"),
]

# ---------- Figure 1 : taux par région ----------
fig_region = go.Figure()
fig_region.add_bar(
    x=taux_region.values,
    y=[dp.LABELS_REGION[r] for r in taux_region.index],
    orientation="h",
    marker_color=ACCENT,
    text=[f"{v:.1f} %" for v in taux_region.values],
    textposition="outside",
    textfont=dict(color=INK),
    customdata=[n_region[r] for r in taux_region.index],
    hovertemplate="%{y} : %{x:.1f} %<br>n=%{customdata} femmes interrogées<extra></extra>",
)
fig_region.add_vline(x=taux_national, line_width=1, line_dash="dash", line_color=MUTED,
                      annotation_text=f"Moyenne nationale {taux_national:.1f} %",
                      annotation_font_color=INK_SECONDARY,
                      annotation_position="bottom right", annotation_yshift=10)
fig_region.update_layout(
    **CHART_LAYOUT, bargap=0.25,
    xaxis=dict(title="Taux de dépistage (%)", gridcolor=GRID, zeroline=False, range=[0, 32]),
    yaxis=dict(showgrid=False),
    margin=dict(l=130, r=50, t=10, b=30),
)

# ---------- Figure 2 : éducation et richesse (small multiples, même échelle) ----------
AXIS_MAX = 55

fig_educ = go.Figure()
fig_educ.add_bar(
    x=taux_educ.values,
    y=[dp.LABELS_EDUC[c] for c in taux_educ.index],
    orientation="h", marker_color=ACCENT,
    text=[f"{v:.1f} %" for v in taux_educ.values], textposition="outside",
    textfont=dict(color=INK),
    hovertemplate="%{y} : %{x:.1f} %<extra></extra>",
)
fig_educ.update_layout(
    **CHART_LAYOUT, bargap=0.3,
    xaxis=dict(title="Taux brut (%)", gridcolor=GRID, zeroline=False, range=[0, AXIS_MAX]),
    yaxis=dict(showgrid=False, autorange="reversed"),
    margin=dict(l=110, r=40, t=10, b=28),
)

fig_richesse = go.Figure()
fig_richesse.add_bar(
    x=taux_richesse.values,
    y=[dp.LABELS_RICHESSE[c] for c in taux_richesse.index],
    orientation="h", marker_color=ACCENT,
    text=[f"{v:.1f} %" for v in taux_richesse.values], textposition="outside",
    textfont=dict(color=INK),
    hovertemplate="%{y} : %{x:.1f} %<extra></extra>",
)
fig_richesse.update_layout(
    **CHART_LAYOUT, bargap=0.3,
    xaxis=dict(title="Taux brut (%)", gridcolor=GRID, zeroline=False, range=[0, AXIS_MAX]),
    yaxis=dict(showgrid=False, autorange="reversed"),
    margin=dict(l=110, r=40, t=10, b=28),
)

# ---------- Figure 3 : forest plot (régression, 4 statuts) ----------
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
    return group, f"{group} — {label}"

group_order = {"Milieu": 0, "Éducation": 1, "Richesse": 2, "Région": 3}
rows = []
for idx, row in reg.iterrows():
    if idx == "v012":
        continue  # l'âge est un facteur de contrôle, pas un facteur d'intérêt à afficher
    group, label = parse_row(idx)
    rows.append({"group": group, "label": label, **row.to_dict()})

forest = pd.DataFrame(rows)
forest["group_rank"] = forest["group"].map(group_order)
forest = forest.sort_values(["group_rank", "odds_ratio"], ascending=[True, True])
y_order = list(forest["label"])[::-1]


def status_color(r):
    if r["significatif_corrige"] and r["odds_ratio"] < 1:
        return SERIOUS, "Défavorisé (confirmé)"
    if r["significatif_corrige"] and r["odds_ratio"] > 1:
        return GOOD, "Favorisé (confirmé)"
    if r["significatif"] and not r["significatif_corrige"]:
        sens = "défavorisé" if r["odds_ratio"] < 1 else "favorisé"
        return WARNING, f"À surveiller ({sens}, significatif avant correction seulement)"
    return MUTED, "Pas d'effet détecté"


colors_labels = forest.apply(status_color, axis=1, result_type="expand")
forest["color"], forest["statut"] = colors_labels[0], colors_labels[1]

fig_forest = go.Figure()
fig_forest.add_vline(x=1, line_width=1, line_color=MUTED)
for _, r in forest.iterrows():
    fig_forest.add_trace(go.Scatter(
        x=[r["odds_ratio"]], y=[r["label"]],
        mode="markers",
        marker=dict(size=7, color=r["color"], line=dict(width=1.5, color=SURFACE)),
        error_x=dict(
            type="data", symmetric=False,
            array=[r["ic_haut"] - r["odds_ratio"]],
            arrayminus=[r["odds_ratio"] - r["ic_bas"]],
            color=r["color"], thickness=1.5,
        ),
        hovertemplate=(
            f"{r['label']}<br>OR={r['odds_ratio']:.2f} [{r['ic_bas']:.2f}-{r['ic_haut']:.2f}]"
            f"<br>p={r['p_value']:.3f} (corrigé={r['p_value_corrige']:.3f})"
            f"<br>{r['statut']}<extra></extra>"
        ),
        showlegend=False,
    ))

TICKVALS = [0.25, 0.5, 1, 2, 4, 8]
fig_forest.update_layout(
    **CHART_LAYOUT,
    xaxis=dict(
        title="Odds ratio ajusté (éch. log, réf.=1)", type="log", gridcolor=GRID, zeroline=False,
        tickvals=TICKVALS, ticktext=["0,25", "0,5", "1", "2", "4", "8"],
    ),
    yaxis=dict(categoryorder="array", categoryarray=y_order, showgrid=False),
    margin=dict(l=160, r=30, t=10, b=28),
)

# ---------- Table région uniquement (pour la case "priorisation") ----------
region_rows = forest[forest["group"] == "Région"].copy()
region_rows["region_key"] = region_rows["label"].str.replace("Région — ", "", regex=False)
label_to_key = {v: k for k, v in dp.LABELS_REGION.items()}
region_rows["taux_brut"] = region_rows["region_key"].map(
    lambda lbl: taux_region[label_to_key[lbl]]
)
region_rows["n"] = region_rows["region_key"].map(lambda lbl: n_region[label_to_key[lbl]])
region_rows = region_rows.sort_values("odds_ratio")

# Ligne Abidjan = référence du modèle (OR=1 par définition, jamais une ligne de la régression)
abidjan_row = (
    f"<tr><td><i>Abidjan (réf.)</i></td><td>{n_region['abidjan']}</td>"
    f"<td>{taux_region['abidjan']:.1f}%</td><td>1.00</td><td>Référence</td></tr>"
)
table_rows_html = abidjan_row + "".join(
    f"<tr><td>{r['region_key']}</td><td>{r['n']}</td><td>{r['taux_brut']:.1f}%</td>"
    f"<td>{r['odds_ratio']:.2f}</td><td>{r['statut']}</td></tr>"
    for _, r in region_rows.iterrows()
)

# Composition de Yamoussoukro vs nationale, pour expliquer l'anomalie (calculé, pas estimé)
yam = df[df["v024"] == "yamoussoukro"]
pct_riche_yam = yam["v190"].isin(["richer", "richest"]).mean() * 100
pct_riche_nat = df["v190"].isin(["richer", "richest"]).mean() * 100
pct_educ_yam = (~yam["v106"].eq("no education")).mean() * 100
pct_educ_nat = (~df["v106"].eq("no education")).mean() * 100


def kpi_html(label, value):
    return f"""<div class="kpi">
      <div class="kpi-value">{value}</div>
      <div class="kpi-label">{label}</div>
    </div>"""


html = f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Dépistage du cancer du sein en Côte d'Ivoire — Octobre Rose</title>
<script src="https://cdn.jsdelivr.net/npm/plotly.js-dist-min@2.35.2/plotly.min.js"></script>
<style>
  :root {{
    --surface: {SURFACE}; --ink: {INK}; --ink-2: {INK_SECONDARY}; --muted: {MUTED};
    --grid: {GRID}; --good: {GOOD}; --serious: {SERIOUS}; --warning: {WARNING}; --accent: {ACCENT};
  }}
  html, body {{
    height: 100%; width: 100%; margin: 0; overflow: hidden;
    background: #f9f9f7; color: var(--ink);
    font-family: system-ui, -apple-system, "Segoe UI", sans-serif;
  }}
  .dashboard {{
    height: 100vh; width: 100vw; box-sizing: border-box;
    padding: 10px 18px; display: flex; flex-direction: column; gap: 6px;
  }}
  h1 {{
    font-size: 0.98rem; margin: 0; padding-left: 10px; line-height: 1.2;
    border-left: 4px solid var(--accent); flex: 0 0 auto;
  }}
  .subtitle {{ color: var(--ink-2); font-size: 0.68rem; padding-left: 14px; flex: 0 0 auto; }}
  h2 {{ font-size: 0.76rem; margin: 0 0 1px; flex: 0 0 auto; }}
  .caption {{ color: var(--ink-2); font-size: 0.6rem; margin-bottom: 3px; flex: 0 0 auto; line-height: 1.25; }}
  .kpi-row {{ display: flex; gap: 8px; flex: 0 0 auto; }}
  .kpi {{
    background: var(--surface); border: 1px solid var(--grid); border-top: 3px solid var(--accent);
    border-radius: 6px; padding: 6px 12px; flex: 1 1 0;
  }}
  .kpi-value {{ font-size: 1.15rem; font-weight: 600; line-height: 1.1; }}
  .kpi-label {{ color: var(--ink-2); font-size: 0.6rem; margin-top: 1px; }}
  .main-grid {{
    flex: 1 1 auto; min-height: 0;
    display: grid; grid-template-columns: 1fr 1fr; grid-template-rows: 0.75fr 1.25fr;
    gap: 8px;
  }}
  .cell {{
    background: var(--surface); border: 1px solid var(--grid); border-radius: 8px;
    padding: 6px 10px; min-height: 0; overflow: auto;
    display: flex; flex-direction: column;
  }}
  .cell-chart {{ flex: 1 1 auto; min-height: 0; }}
  .side-by-side {{ display: flex; gap: 8px; flex: 1 1 auto; min-height: 0; }}
  .side-by-side > div {{ flex: 1 1 0; min-height: 0; display: flex; flex-direction: column; }}
  .side-by-side .cell-chart {{ flex: 1 1 auto; }}
  .legend-status {{ display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 1px; font-size: 0.58rem; color: var(--ink-2); flex: 0 0 auto; }}
  .legend-status span.dot {{ display: inline-block; width: 7px; height: 7px; border-radius: 50%; margin-right: 3px; }}
  table {{ border-collapse: collapse; width: 100%; font-size: 0.6rem; }}
  th, td {{ text-align: left; padding: 1px 5px; border-bottom: 1px solid var(--grid); }}
  th {{ color: var(--ink-2); font-weight: 600; }}
  .reco {{ font-size: 0.62rem; line-height: 1.3; margin-top: 4px; flex: 0 0 auto; }}
  .reco b {{ color: var(--ink); }}
  footer {{ color: var(--muted); font-size: 0.56rem; flex: 0 0 auto; margin-top: 2px; }}
</style>
</head>
<body>
<div class="dashboard">

  <h1>Éducation et richesse sont les facteurs les plus fortement associés à l'accès au dépistage du sein</h1>
  <div class="subtitle">EDS-CI 2021 — modèle ajusté : âge + éducation + richesse + région + milieu (association, pas causalité). Réf. : Abidjan / rural / aucune éducation / plus pauvres.</div>

  <div class="kpi-row">
    {''.join(kpi_html(l, v) for l, v in kpis)}
  </div>

  <div class="main-grid">

    <div class="cell">
      <h2>Abidjan dépiste environ {ratio_region_max:.1f}× plus que Gôh-Djiboua, la région la plus en retard (taux bruts)</h2>
      <div class="caption">Taux brut par région, pondéré ; pointillé = moyenne nationale. Abidjan = référence du modèle ajusté ci-dessous — mais le classement brut ≠ le classement ajusté (voir Yamoussoukro, case régression).</div>
      <div id="fig-region" class="cell-chart"></div>
    </div>

    <div class="cell">
      <h2>Taux brut ×{ratio_educ['higher']:.1f} (éducation) et ×{ratio_richesse['richest']:.1f} (richesse) entre les deux extrêmes</h2>
      <div class="caption">Taux bruts (non ajustés). Une fois les autres facteurs contrôlés (régression ci-dessous), l'effet propre de la richesse retombe à OR={or_richesse_max:.2f} : une partie de son effet brut passe en réalité par l'éducation et l'urbanicité, pas par la richesse elle-même. Taux brut ≠ odds ratio ajusté (voir rapport).</div>
      <div class="side-by-side">
        <div><div id="fig-educ" class="cell-chart"></div></div>
        <div><div id="fig-richesse" class="cell-chart"></div></div>
      </div>
    </div>

    <div class="cell">
      <h2>Éducation et richesse restent significatives une fois âge/région/milieu neutralisés</h2>
      <div class="legend-status">
        <div><span class="dot" style="background:{SERIOUS}"></span>Défavorisé confirmé</div>
        <div><span class="dot" style="background:{WARNING}"></span>À surveiller</div>
        <div><span class="dot" style="background:{MUTED}"></span>Pas d'effet</div>
        <div><span class="dot" style="background:{GOOD}"></span>Favorisé confirmé</div>
      </div>
      <div id="fig-forest" class="cell-chart"></div>
      <div class="caption">
        Milieu urbain/rural : OR={or_milieu['odds_ratio']:.2f} [{or_milieu['ic_bas']:.2f}–{or_milieu['ic_haut']:.2f}], p={or_milieu['p_value']:.3f} — pas d'effet indépendant démontré (Abidjan, la référence, est elle-même 100% urbaine).
        Critère de priorité région : effet ajusté (OR), pas le taux brut — Yamoussoukro n'est que 7ᵉ/14 en taux brut (12,3%) mais ressort défavorisée ajustée : son profil ({pct_riche_yam:.0f}% riches/plus riches vs {pct_riche_nat:.0f}% national, {pct_educ_yam:.0f}% scolarisées vs {pct_educ_nat:.0f}%) laisse attendre un taux bien supérieur à ce qui est observé.
      </div>
    </div>

    <div class="cell">
      <h2>Régions à prioriser — signal fragile, à confirmer (voir rapport)</h2>
      <table>
        <thead><tr><th>Région</th><th>n</th><th>Taux brut</th><th>OR ajusté</th><th>Statut</th></tr></thead>
        <tbody>{table_rows_html}</tbody>
      </table>
      <div class="reco">
        <b>Recommandation :</b> cibler en priorité les femmes pauvres et peu éduquées (effet le plus robuste, confirmé sur toutes les tranches d'âge) ; traiter le signal régional (Gôh-Djiboua, Yamoussoukro) comme une piste à confirmer avant d'y concentrer des moyens dédiés.<br>
        <b>Limites :</b> données transversales et déclaratives (association, pas causalité) ; effet de l'éducation supposé uniforme entre régions (interaction non testée) ; le signal régional ne résiste pas à une restriction d'âge 30-49 ans, contrairement à éducation/richesse (voir rapport PDF) ; plan de sondage corrigé pour les grappes mais pas les strates.
      </div>
      <footer>
        Source : EDS-CI 2021 (DHS Program / INS Côte d'Ivoire). {dp.DEFINITION_VARIABLE_CIBLE} Résultats agrégés uniquement, aucune redistribution des microdonnées.
      </footer>
    </div>

  </div>
</div>
<script>
  const layoutDefaults = {{displayModeBar: false, responsive: true}};
  Plotly.newPlot('fig-region', {fig_region.to_json()}.data, {fig_region.to_json()}.layout, layoutDefaults);
  Plotly.newPlot('fig-educ', {fig_educ.to_json()}.data, {fig_educ.to_json()}.layout, layoutDefaults);
  Plotly.newPlot('fig-richesse', {fig_richesse.to_json()}.data, {fig_richesse.to_json()}.layout, layoutDefaults);
  Plotly.newPlot('fig-forest', {fig_forest.to_json()}.data, {fig_forest.to_json()}.layout, layoutDefaults);
</script>
</body>
</html>
"""

out_path = Path("reports/dashboard.html")
out_path.write_text(html, encoding="utf-8")
print(f"Dashboard écrit : {out_path.resolve()}")
