# -*- coding: utf-8 -*-
"""
Bloque 3 - Taxonomia y Visualizacion de Senales Polymarket
Parte 3 - Geopolitica y Crudo WTI: Inteligencia en Tiempo Real
Snapshot: 23 de marzo de 2026
"""

import pandas as pd
import numpy as np
import re
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
from matplotlib.gridspec import GridSpec
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

ROOT        = Path(".")
DATA_OUT    = ROOT / "outputs" / "data"    / "parte3"
FIGURES_OUT = ROOT / "outputs" / "figures" / "parte3"
DATA_OUT.mkdir(parents=True, exist_ok=True)
FIGURES_OUT.mkdir(parents=True, exist_ok=True)

# Paleta dark
BG_DARK  = "#0d1117"
BG_PANEL = "#161b22"
BORDER   = "#30363d"
TXT_PRI  = "#e6edf3"
TXT_SEC  = "#8b949e"

# Colores por conviction_tier
TIER_COLORS = {
    "descontado"  : "#2ea043",   # verde fuerte
    "muy_probable": "#56d364",   # verde claro
    "probable"    : "#f0a040",   # naranja
    "cola"        : "#da3633",   # rojo
}
TIER_ORDER = ["descontado", "muy_probable", "probable", "cola"]
CAT_ORDER  = ["supply_side", "price_direct", "tail_risk",
              "macro_derived", "safe_haven", "risk_assets"]
CAT_LABELS = {
    "supply_side"  : "Supply Side\n(Iran/OPEC/Ormuz)",
    "price_direct" : "Price Direct\n(WTI/Brent levels)",
    "tail_risk"    : "Tail Risk\n(extremos)",
    "macro_derived": "Macro Derivada\n(Fed/inflation/war)",
    "safe_haven"   : "Safe Haven\n(Gold/Silver/Bonds)",
    "risk_assets"  : "Risk Assets\n(S&P/Nasdaq/BTC)",
}

# ─────────────────────────────────────────────────────────────────────────────
# Cargar datos
# ─────────────────────────────────────────────────────────────────────────────
df = pd.read_parquet(DATA_OUT / "polymarket_clean.parquet")
print(f"Datos cargados: {df.shape[0]} mercados, {df.shape[1]} columnas")
print(f"Distribucion por categoria:\n{df['category_project'].value_counts().to_string()}")

# ─────────────────────────────────────────────────────────────────────────────
# VIZ 1 — MAPA DE CALOR DE CONVICCION
# ─────────────────────────────────────────────────────────────────────────────
print("\n[1] Generando heatmap de conviccion...")

# Para cada celda (cat, tier): mercado de mayor liquidez
def best_market_for_cell(cat, tier):
    mask = (df["category_project"] == cat) & (df["conviction_tier"] == tier)
    sub  = df[mask].copy()
    if sub.empty:
        return None
    return sub.nlargest(1, "liquidity").iloc[0]

# Construir matriz
heat_prob  = np.full((len(CAT_ORDER), len(TIER_ORDER)), np.nan)
heat_cells = {}

for i, cat in enumerate(CAT_ORDER):
    for j, tier in enumerate(TIER_ORDER):
        best = best_market_for_cell(cat, tier)
        if best is not None:
            heat_prob[i, j] = best["yes_prob"]
            heat_cells[(i, j)] = best

# Conteo por celda (para mostrar N)
heat_count = np.zeros((len(CAT_ORDER), len(TIER_ORDER)), dtype=int)
for i, cat in enumerate(CAT_ORDER):
    for j, tier in enumerate(TIER_ORDER):
        n = ((df["category_project"] == cat) & (df["conviction_tier"] == tier)).sum()
        heat_count[i, j] = n

fig, ax = plt.subplots(figsize=(14, 7))
fig.patch.set_facecolor(BG_DARK)
ax.set_facecolor(BG_PANEL)

cmap = plt.cm.RdYlGn
norm = mcolors.Normalize(vmin=0, vmax=100)

for i in range(len(CAT_ORDER)):
    for j in range(len(TIER_ORDER)):
        val = heat_prob[i, j]
        n   = heat_count[i, j]
        facecolor = cmap(norm(val)) if not np.isnan(val) else "#21262d"
        rect = mpatches.FancyBboxPatch(
            (j - 0.45, i - 0.45), 0.9, 0.9,
            boxstyle="round,pad=0.05",
            facecolor=facecolor, edgecolor=BORDER, linewidth=0.8
        )
        ax.add_patch(rect)

        if not np.isnan(val):
            # Probabilidad grande
            txt_color = "black" if 0.35 < norm(val) < 0.85 else "white"
            ax.text(j, i + 0.12, f"{val:.0f}%",
                    ha="center", va="center",
                    fontsize=13, fontweight="bold", color=txt_color)
            # Pregunta del mercado representativo
            best = heat_cells.get((i, j))
            if best is not None:
                q_short = best["question"][:42] + "..." if len(best["question"]) > 42 else best["question"]
                ax.text(j, i - 0.18, q_short,
                        ha="center", va="center",
                        fontsize=5.5, color=txt_color, alpha=0.85,
                        wrap=True)
            # N mercados en celda
            ax.text(j + 0.43, i + 0.42, f"n={n}",
                    ha="right", va="top", fontsize=6, color=txt_color, alpha=0.7)
        else:
            ax.text(j, i, "—", ha="center", va="center",
                    fontsize=11, color=TXT_SEC)

ax.set_xlim(-0.55, len(TIER_ORDER) - 0.45)
ax.set_ylim(-0.55, len(CAT_ORDER) - 0.45)
ax.set_xticks(range(len(TIER_ORDER)))
ax.set_xticklabels(
    [f"{t.replace('_',' ').upper()}" for t in TIER_ORDER],
    fontsize=10, color=TXT_PRI, fontweight="bold"
)
ax.set_yticks(range(len(CAT_ORDER)))
ax.set_yticklabels(
    [CAT_LABELS[c] for c in CAT_ORDER],
    fontsize=9, color=TXT_PRI
)
ax.tick_params(length=0)
for spine in ax.spines.values():
    spine.set_edgecolor(BORDER)

# Colorbar
sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.02)
cbar.ax.yaxis.set_tick_params(color=TXT_SEC, labelcolor=TXT_SEC)
cbar.set_label("Probabilidad implícita Yes (%)", color=TXT_SEC, fontsize=9)
cbar.ax.set_facecolor(BG_PANEL)

ax.set_title(
    "Mapa de Convicción Polymarket — 23 Marzo 2026\n"
    "Cada celda: mercado de mayor liquidez por (categoría × tier). Color = yes_prob.",
    color=TXT_PRI, fontsize=12, fontweight="bold", pad=12
)
ax.set_xlabel("Conviction Tier  →  certeza creciente", color=TXT_SEC, fontsize=9)
ax.set_ylabel("Categoría del proyecto", color=TXT_SEC, fontsize=9)

plt.tight_layout()
path1 = FIGURES_OUT / "polymarket_heatmap.png"
plt.savefig(path1, dpi=150, bbox_inches="tight",
            facecolor=BG_DARK, edgecolor="none")
plt.close()
print(f"   Guardado: {path1}")

# ─────────────────────────────────────────────────────────────────────────────
# VIZ 2 — RANKING POR CATEGORIA
# ─────────────────────────────────────────────────────────────────────────────
print("[2] Generando ranking por categoria...")

fig2, axes2 = plt.subplots(2, 3, figsize=(20, 14))
fig2.patch.set_facecolor(BG_DARK)
axes2_flat = axes2.flatten()

MAX_BARS = 15   # max mercados por subplot

for idx, cat in enumerate(CAT_ORDER):
    ax = axes2_flat[idx]
    ax.set_facecolor(BG_PANEL)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)

    sub = (df[df["category_project"] == cat]
           .sort_values("yes_prob", ascending=True)
           .tail(MAX_BARS)
           .copy())

    if sub.empty:
        ax.axis("off")
        continue

    # Acortar preguntas
    sub["q_short"] = sub["question"].apply(
        lambda q: q[:58] + "..." if len(q) > 58 else q
    )

    colors = [TIER_COLORS.get(t, "#8b949e") for t in sub["conviction_tier"]]
    bars = ax.barh(range(len(sub)), sub["yes_prob"], color=colors,
                   height=0.7, edgecolor=BORDER, linewidth=0.4)

    # Etiquetas
    for k, (bar, row) in enumerate(zip(bars, sub.itertuples())):
        # Porcentaje al final de la barra
        ax.text(bar.get_width() + 1, k, f"{row.yes_prob:.0f}%",
                va="center", ha="left", fontsize=7.5,
                color=TIER_COLORS.get(row.conviction_tier, TXT_SEC),
                fontweight="bold")
        # dias hasta cierre
        dtc_str = f"{row.days_to_close}d" if pd.notna(row.days_to_close) else ""
        ax.text(-1, k, dtc_str, va="center", ha="right", fontsize=6.5,
                color=TXT_SEC)

    ax.set_yticks(range(len(sub)))
    ax.set_yticklabels(sub["q_short"], fontsize=6.5, color=TXT_PRI)
    ax.set_xlim(-8, 112)
    ax.axvline(50, color=BORDER, linewidth=0.7, linestyle="--", alpha=0.5)
    ax.axvline(75, color=TIER_COLORS["muy_probable"], linewidth=0.5,
               linestyle=":", alpha=0.4)
    ax.axvline(90, color=TIER_COLORS["descontado"], linewidth=0.5,
               linestyle=":", alpha=0.4)
    ax.tick_params(colors=TXT_SEC, labelsize=7)
    ax.set_xlabel("Probabilidad implícita Yes (%)", color=TXT_SEC, fontsize=8)

    # Titulo con stats del grupo
    n_total = (df["category_project"] == cat).sum()
    w_avg   = np.average(
        df[df["category_project"] == cat]["yes_prob"],
        weights=df[df["category_project"] == cat]["liquidity"].fillna(1) + 1
    )
    ax.set_title(
        f"{CAT_LABELS[cat].replace(chr(10),' — ')}  "
        f"[N={n_total}  avg_liq={w_avg:.1f}%]",
        color=TXT_PRI, fontsize=9, fontweight="bold", pad=6
    )

# Leyenda global
legend_patches = [
    mpatches.Patch(color=TIER_COLORS["descontado"],   label=">90%  descontado"),
    mpatches.Patch(color=TIER_COLORS["muy_probable"], label="75-90%  muy probable"),
    mpatches.Patch(color=TIER_COLORS["probable"],     label="60-75%  probable"),
    mpatches.Patch(color=TIER_COLORS["cola"],         label="<60%   cola"),
]
fig2.legend(handles=legend_patches, loc="lower center", ncol=4,
            fontsize=9, facecolor=BG_PANEL, edgecolor=BORDER,
            labelcolor=TXT_PRI, framealpha=0.9, bbox_to_anchor=(0.5, -0.02))

fig2.suptitle(
    "Ranking Polymarket por Categoría — 23 Marzo 2026\n"
    "Top 15 mercados por yes_prob. Número a la izquierda = dias hasta cierre.",
    color=TXT_PRI, fontsize=13, fontweight="bold", y=1.01
)
plt.tight_layout(pad=1.8)
path2 = FIGURES_OUT / "polymarket_ranking.png"
plt.savefig(path2, dpi=150, bbox_inches="tight",
            facecolor=BG_DARK, edgecolor="none")
plt.close()
print(f"   Guardado: {path2}")

# ─────────────────────────────────────────────────────────────────────────────
# VIZ 3 — CURVA DE PROBABILIDADES IMPLICITAS
# ─────────────────────────────────────────────────────────────────────────────
print("[3] Generando curva de probabilidades implicitas...")

def extract_price_threshold(question: str):
    """
    Extrae (threshold, direction) de preguntas tipo:
      'Will Crude Oil (CL) hit (HIGH) $100 by end of March?'
      'Will Gold (GC) hit (LOW) $4,500 by end of June?'
      'Will S&P 500 (SPX) close over $6,500 ...'
    Devuelve (float, 'HIGH'|'LOW'|'OVER'|'UNDER') o (None, None).
    """
    q = question.upper()
    # Buscar precio numerico
    price_match = re.search(r"\$([0-9,]+(?:\.[0-9]+)?)", question.replace(",", ""))
    if not price_match:
        return None, None
    price = float(price_match.group(1).replace(",", ""))

    if "(HIGH)" in q or "HIT HIGH" in q or "HIGH)" in q:
        direction = "HIGH"
    elif "(LOW)" in q or "HIT LOW" in q or "LOW)" in q:
        direction = "LOW"
    elif "OVER" in q or "ABOVE" in q or "CLOSE OVER" in q:
        direction = "HIGH"
    elif "UNDER" in q or "BELOW" in q:
        direction = "LOW"
    else:
        direction = "UNKNOWN"
    return price, direction


CURVE_ASSETS = [
    {
        "name"     : "WTI Crude Oil",
        "group"    : "wti_price",
        "color_hi" : "#d62728",
        "color_lo" : "#ff7f0e",
        "unit"     : "$/bbl",
        "current"  : 98.32,
        "dtc_buckets": [(0, 15, "Marzo"), (90, 110, "Junio")],
    },
    {
        "name"     : "Gold",
        "group"    : "gold_price",
        "color_hi" : "#bcbd22",
        "color_lo" : "#17becf",
        "unit"     : "$/oz",
        "current"  : 4570.0,
        "dtc_buckets": [(0, 15, "Marzo"), (90, 110, "Junio")],
    },
    {
        "name"     : "S&P 500",
        "group"    : "sp500_level",
        "color_hi" : "#1f77b4",
        "color_lo" : "#aec7e8",
        "unit"     : "pts",
        "current"  : 6506.0,
        "dtc_buckets": [(0, 15, "Marzo")],
    },
]

fig3, axes3 = plt.subplots(1, 3, figsize=(21, 7))
fig3.patch.set_facecolor(BG_DARK)

for idx, asset_cfg in enumerate(CURVE_ASSETS):
    ax = axes3[idx]
    ax.set_facecolor(BG_PANEL)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)

    sub = df[df["market_group"] == asset_cfg["group"]].copy()
    sub["threshold"], sub["direction"] = zip(
        *sub["question"].apply(extract_price_threshold)
    )
    sub = sub.dropna(subset=["threshold"])
    sub["threshold"] = sub["threshold"].astype(float)

    plotted = False
    for dtc_lo, dtc_hi, label in asset_cfg["dtc_buckets"]:
        bucket = sub[
            (sub["days_to_close"] >= dtc_lo) &
            (sub["days_to_close"] <= dtc_hi)
        ].copy()
        if bucket.empty:
            continue

        for direction, col_key in [("HIGH", "color_hi"), ("LOW", "color_lo")]:
            curve = (bucket[bucket["direction"] == direction]
                     .sort_values("threshold")
                     .drop_duplicates("threshold"))
            if len(curve) < 2:
                continue

            color = asset_cfg[col_key]
            ls    = "-" if dtc_lo < 20 else "--"
            lbl   = f"{direction} — {label}"
            ax.plot(curve["threshold"], curve["yes_prob"],
                    "o-", color=color, linewidth=1.8, markersize=5,
                    linestyle=ls, label=lbl, alpha=0.9)

            # Anotar puntos
            for _, row in curve.iterrows():
                ax.annotate(f"{row['yes_prob']:.0f}%",
                            xy=(row["threshold"], row["yes_prob"]),
                            xytext=(0, 6), textcoords="offset points",
                            ha="center", fontsize=6.5, color=color)
            plotted = True

    # Linea vertical: precio actual
    ax.axvline(asset_cfg["current"], color="#ff4d4f", linewidth=1.5,
               linestyle="--", alpha=0.8,
               label=f"Actual: {asset_cfg['current']:,.0f}")
    ax.axhline(50, color=BORDER, linewidth=0.7, linestyle=":", alpha=0.6)

    ax.tick_params(colors=TXT_SEC, labelsize=8)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)
    ax.set_ylim(-5, 105)
    ax.set_xlabel(f"Umbral ({asset_cfg['unit']})", color=TXT_SEC, fontsize=9)
    ax.set_ylabel("Probabilidad implícita Yes (%)", color=TXT_SEC, fontsize=9)
    ax.set_title(
        f"Curva Implícita — {asset_cfg['name']}\n"
        f"(HIGH = prob. de tocar ese nivel hacia arriba; LOW = hacia abajo)",
        color=TXT_PRI, fontsize=10, fontweight="bold", pad=8
    )
    ax.legend(fontsize=7.5, facecolor=BG_PANEL, edgecolor=BORDER,
              labelcolor=TXT_PRI, framealpha=0.85, loc="best")
    ax.set_facecolor(BG_PANEL)

    # Zona sombreada entre P10–P90 historico si disponemos del snapshot
    try:
        snap = pd.read_parquet(DATA_OUT / "market_snapshot_20260323.parquet")
        asset_key = {"WTI Crude Oil": "wti", "Gold": "gold", "S&P 500": "sp500"}
        k = asset_key.get(asset_cfg["name"])
        if k:
            row_snap = snap[snap["asset"] == k]
            if not row_snap.empty:
                p10 = float(row_snap["p50_hist"].iloc[0]) if pd.notna(row_snap["p50_hist"].iloc[0]) else None
                p90 = float(row_snap["p90_hist"].iloc[0]) if pd.notna(row_snap["p90_hist"].iloc[0]) else None
                if p10 and p90:
                    ax.axvspan(p10, p90, alpha=0.06, color="#58a6ff",
                               label=f"P50–P90 hist.")
    except Exception:
        pass

fig3.suptitle(
    "Curvas de Probabilidad Implícita Polymarket — 23 Marzo 2026\n"
    "Analogo a una superficie de volatilidad implícita: prob. vs umbral de precio",
    color=TXT_PRI, fontsize=13, fontweight="bold", y=1.02
)
plt.tight_layout(pad=2.0)
path3 = FIGURES_OUT / "polymarket_implied_curve.png"
plt.savefig(path3, dpi=150, bbox_inches="tight",
            facecolor=BG_DARK, edgecolor="none")
plt.close()
print(f"   Guardado: {path3}")

# ─────────────────────────────────────────────────────────────────────────────
# TABLA DE SINTESIS POR CATEGORIA
# ─────────────────────────────────────────────────────────────────────────────
print("\n[4] Tabla de sintesis por categoria...")

synthesis_records = []
for cat in CAT_ORDER:
    sub = df[df["category_project"] == cat].copy()
    if sub.empty:
        continue
    n_total = len(sub)
    # Prob media ponderada por liquidez
    liq_weights = sub["liquidity"].fillna(0) + 1
    w_avg_prob  = np.average(sub["yes_prob"], weights=liq_weights)
    # Mercado mayor conviccion (mayor yes_prob con liquidez minima)
    top_conv = sub.nlargest(1, "yes_prob").iloc[0]
    # Mercado mayor volumen 24h
    top_vol  = sub.nlargest(1, "volume_24h").iloc[0]
    # Tier dominante
    dom_tier = sub["conviction_tier"].value_counts().index[0]

    synthesis_records.append({
        "categoria"         : cat,
        "n_mercados"        : n_total,
        "prob_media_pond"   : round(w_avg_prob, 1),
        "tier_dominante"    : dom_tier,
        "top_conv_question" : top_conv["question"][:70],
        "top_conv_prob"     : top_conv["yes_prob"],
        "top_conv_dtc"      : int(top_conv["days_to_close"]) if pd.notna(top_conv["days_to_close"]) else None,
        "top_vol_question"  : top_vol["question"][:70],
        "top_vol_24h"       : round(top_vol["volume_24h"], 0),
        "top_vol_prob"      : top_vol["yes_prob"],
    })

synth_df = pd.DataFrame(synthesis_records)
synth_path = DATA_OUT / "synthesis_by_category.parquet"
synth_df.to_parquet(synth_path, index=False)
synth_json_path = DATA_OUT / "synthesis_by_category.json"
synth_df.to_json(synth_json_path, orient="records", indent=2, force_ascii=False)

# Imprimir tabla
print()
print("=" * 100)
print("TABLA DE SINTESIS — BLOQUE 3")
print("=" * 100)
for _, r in synth_df.iterrows():
    print(f"\n  [{r['categoria'].upper():14s}]  N={r['n_mercados']:3d}  "
          f"prob_media_pond={r['prob_media_pond']:5.1f}%  "
          f"tier_dominante={r['tier_dominante']}")
    print(f"    Mayor conviccion : [{r['top_conv_prob']:5.1f}%] {r['top_conv_question']}  (dtc={r['top_conv_dtc']}d)")
    print(f"    Mayor volumen 24h: [{r['top_vol_prob']:5.1f}%] {r['top_vol_question']}  (vol=${r['top_vol_24h']:,.0f})")

print(f"\nSintesis guardada: {synth_path}")
print(f"Sintesis JSON    : {synth_json_path}")

# ─────────────────────────────────────────────────────────────────────────────
# RESUMEN EJECUTIVO
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("RESUMEN EJECUTIVO — BLOQUE 3")
print("=" * 80)
print(f"  Total mercados analizados  : {len(df)}")
print(f"  Mercados 'descontado' (>90%): {(df['conviction_tier']=='descontado').sum()}")
print(f"  Mercados 'cola' (<60%)     : {(df['conviction_tier']=='cola').sum()}")
print()
print("  Top 10 mercados crudo/geopolitico por volumen 24h:")
top_geo = (df[df["keyword_layer"] == 1]
           .nlargest(10, "volume_24h")
           [["question","yes_prob","volume_24h","conviction_tier","days_to_close"]])
for _, r in top_geo.iterrows():
    q = r["question"][:62]
    print(f"    [{r['yes_prob']:5.1f}%] {q:<64} vol=${r['volume_24h']:>10,.0f}  {r['conviction_tier']}")
