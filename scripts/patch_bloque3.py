# -*- coding: utf-8 -*-
"""
Patch Bloque 3 — Regenera todas las figuras con mejoras:
  · Diferenciación visual in_model_domain en heatmap y ranking
  · Figura top_inference_markets (por signal_quality_score)
  · Síntesis ampliada (avg_days_to_close, % in_model_domain, top_signal_quality)
  · Curvas implícitas mejoradas con scenario_horizon y threshold_value
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
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

DATA_OUT    = Path("outputs/data/parte3")
FIGURES_OUT = Path("outputs/figures/parte3")

BG_DARK  = "#0d1117"
BG_PANEL = "#161b22"
BORDER   = "#30363d"
TXT_PRI  = "#e6edf3"
TXT_SEC  = "#8b949e"

TIER_COLORS = {
    "descontado"  : "#2ea043",
    "muy_probable": "#56d364",
    "probable"    : "#f0a040",
    "cola"        : "#da3633",
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
HORIZON_COLORS = {
    "short_term" : "#ff4d4f",
    "medium_term": "#f0a040",
    "long_term"  : "#58a6ff",
}

df = pd.read_parquet(DATA_OUT / "polymarket_clean.parquet")
print(f"Datos cargados: {df.shape}")
print(f"Columnas: {list(df.columns)}")

# ─── FIG 1: HEATMAP con in_model_domain diferenciado ───────────────────────
print("\n[1] Heatmap actualizado con in_model_domain...")

def best_market_for_cell(cat, tier):
    mask = (df["category_project"] == cat) & (df["conviction_tier"] == tier)
    sub  = df[mask].copy()
    if sub.empty:
        return None
    return sub.nlargest(1, "liquidity").iloc[0]

heat_prob  = np.full((len(CAT_ORDER), len(TIER_ORDER)), np.nan)
heat_cells = {}
heat_count = np.zeros((len(CAT_ORDER), len(TIER_ORDER)), dtype=int)
heat_imd   = np.full((len(CAT_ORDER), len(TIER_ORDER)), np.nan)  # % in_model_domain

for i, cat in enumerate(CAT_ORDER):
    for j, tier in enumerate(TIER_ORDER):
        best = best_market_for_cell(cat, tier)
        if best is not None:
            heat_prob[i, j]  = best["yes_prob"]
            heat_cells[(i,j)] = best
            heat_imd[i, j]   = best["in_model_domain"]
        mask = (df["category_project"]==cat) & (df["conviction_tier"]==tier)
        heat_count[i, j] = mask.sum()

fig, ax = plt.subplots(figsize=(15, 7.5))
fig.patch.set_facecolor(BG_DARK)
ax.set_facecolor(BG_PANEL)
cmap = plt.cm.RdYlGn
norm = mcolors.Normalize(vmin=0, vmax=100)

for i in range(len(CAT_ORDER)):
    for j in range(len(TIER_ORDER)):
        val = heat_prob[i, j]
        n   = heat_count[i, j]
        imd = heat_imd[i, j]
        fc  = cmap(norm(val)) if not np.isnan(val) else "#21262d"

        # Borde sólido si in_model_domain, punteado si OOD
        ls  = "-" if imd == 1.0 else "--"
        lw  = 1.5 if imd == 1.0 else 0.8
        ec  = "#58a6ff" if imd == 1.0 else "#ff4d4f"

        rect = mpatches.FancyBboxPatch(
            (j-0.45, i-0.45), 0.9, 0.9,
            boxstyle="round,pad=0.05",
            facecolor=fc, edgecolor=ec, linewidth=lw,
            linestyle=ls
        )
        ax.add_patch(rect)

        if not np.isnan(val):
            txt_color = "black" if 0.35 < norm(val) < 0.85 else "white"
            ax.text(j, i+0.12, f"{val:.0f}%",
                    ha="center", va="center", fontsize=13,
                    fontweight="bold", color=txt_color)
            best = heat_cells.get((i,j))
            if best is not None:
                q_short = best["question"][:40]+"..." if len(best["question"])>40 else best["question"]
                ax.text(j, i-0.18, q_short,
                        ha="center", va="center", fontsize=5.5,
                        color=txt_color, alpha=0.85)
                # OOD label
                if not best["in_model_domain"]:
                    ax.text(j-0.42, i+0.42, "OOD",
                            ha="left", va="top", fontsize=6,
                            color="#ff4d4f", fontweight="bold")
            ax.text(j+0.43, i+0.42, f"n={n}",
                    ha="right", va="top", fontsize=6, color=txt_color, alpha=0.7)
        else:
            ax.text(j, i, "—", ha="center", va="center",
                    fontsize=11, color=TXT_SEC)

ax.set_xlim(-0.55, len(TIER_ORDER)-0.45)
ax.set_ylim(-0.55, len(CAT_ORDER)-0.45)
ax.set_xticks(range(len(TIER_ORDER)))
ax.set_xticklabels([t.replace("_"," ").upper() for t in TIER_ORDER],
                    fontsize=10, color=TXT_PRI, fontweight="bold")
ax.set_yticks(range(len(CAT_ORDER)))
ax.set_yticklabels([CAT_LABELS[c] for c in CAT_ORDER], fontsize=9, color=TXT_PRI)
ax.tick_params(length=0)
for spine in ax.spines.values():
    spine.set_edgecolor(BORDER)

sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
sm.set_array([])
cbar = fig.colorbar(sm, ax=ax, fraction=0.025, pad=0.02)
cbar.ax.yaxis.set_tick_params(color=TXT_SEC, labelcolor=TXT_SEC)
cbar.set_label("Probabilidad implícita Yes (%)", color=TXT_SEC, fontsize=9)

legend_elements = [
    mpatches.Patch(edgecolor="#58a6ff", facecolor="none", linewidth=2,
                   label="In-model domain (borde azul sólido)"),
    mpatches.Patch(edgecolor="#ff4d4f", facecolor="none", linewidth=1.5,
                   linestyle="--", label="Out of domain (borde rojo punteado + OOD)"),
]
ax.legend(handles=legend_elements, loc="upper right", fontsize=8,
          facecolor=BG_PANEL, edgecolor=BORDER, labelcolor=TXT_PRI)

ax.set_title(
    "Mapa de Convicción Polymarket — 23 Marzo 2026\n"
    "Borde azul sólido = in_model_domain · Borde rojo punteado = Out of Domain (OOD)",
    color=TXT_PRI, fontsize=12, fontweight="bold", pad=12
)
ax.set_xlabel("Conviction Tier  →  certeza creciente", color=TXT_SEC, fontsize=9)
ax.set_ylabel("Categoría del proyecto", color=TXT_SEC, fontsize=9)

plt.tight_layout()
p1 = FIGURES_OUT / "polymarket_heatmap.png"
plt.savefig(p1, dpi=150, bbox_inches="tight", facecolor=BG_DARK, edgecolor="none")
plt.close()
print(f"   Guardado: {p1}")

# ─── FIG 2: RANKING con in_model_domain diferenciado ───────────────────────
print("[2] Ranking actualizado con in_model_domain...")
MAX_BARS = 15

fig2, axes2 = plt.subplots(2, 3, figsize=(20, 14))
fig2.patch.set_facecolor(BG_DARK)
axes2_flat = axes2.flatten()

for idx, cat in enumerate(CAT_ORDER):
    ax = axes2_flat[idx]
    ax.set_facecolor(BG_PANEL)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)

    sub = (df[df["category_project"] == cat]
           .sort_values("yes_prob", ascending=True)
           .tail(MAX_BARS).copy())
    if sub.empty:
        ax.axis("off")
        continue

    sub["q_short"] = sub["question"].apply(lambda q: q[:56]+"..." if len(q)>56 else q)
    # Color barra por tier; alpha por in_model_domain
    bar_colors = [TIER_COLORS.get(t, "#8b949e") for t in sub["conviction_tier"]]
    alphas = [0.95 if imd else 0.45 for imd in sub["in_model_domain"]]

    for k, (row, color, alpha) in enumerate(zip(sub.itertuples(), bar_colors, alphas)):
        # Borde sólido si in-domain, punteado si OOD
        ls = "-" if row.in_model_domain else "--"
        ax.barh(k, row.yes_prob, color=color, height=0.7,
                edgecolor=BORDER, linewidth=0.8 if row.in_model_domain else 1.2,
                alpha=alpha, linestyle=ls)
        # Porcentaje
        ax.text(row.yes_prob+1, k, f"{row.yes_prob:.0f}%",
                va="center", ha="left", fontsize=7.5,
                color=TIER_COLORS.get(row.conviction_tier, TXT_SEC), fontweight="bold")
        # OOD tag
        if not row.in_model_domain:
            ax.text(row.yes_prob+1, k-0.22, "OOD",
                    va="center", ha="left", fontsize=5.5, color="#ff4d4f")
        # dias
        dtc_str = f"{row.days_to_close}d" if pd.notna(row.days_to_close) else ""
        ax.text(-1, k, dtc_str, va="center", ha="right", fontsize=6.5, color=TXT_SEC)
        # horizon tag
        hz_color = HORIZON_COLORS.get(row.scenario_horizon, TXT_SEC)
        ax.text(-5, k, row.scenario_horizon[:3].upper(),
                va="center", ha="right", fontsize=5.5, color=hz_color)

    ax.set_yticks(range(len(sub)))
    ax.set_yticklabels(sub["q_short"], fontsize=6.5, color=TXT_PRI)
    ax.set_xlim(-10, 112)
    ax.axvline(50, color=BORDER, linewidth=0.7, linestyle="--", alpha=0.5)
    ax.axvline(75, color=TIER_COLORS["muy_probable"], linewidth=0.5, linestyle=":", alpha=0.4)
    ax.axvline(90, color=TIER_COLORS["descontado"],   linewidth=0.5, linestyle=":", alpha=0.4)
    ax.tick_params(colors=TXT_SEC, labelsize=7)
    ax.set_xlabel("Probabilidad implícita Yes (%)", color=TXT_SEC, fontsize=8)

    n_total  = (df["category_project"] == cat).sum()
    liq_w    = df[df["category_project"]==cat]["liquidity"].fillna(0)+1
    w_avg    = np.average(df[df["category_project"]==cat]["yes_prob"], weights=liq_w)
    pct_imd  = df[df["category_project"]==cat]["in_model_domain"].mean()*100
    ax.set_title(
        f"{CAT_LABELS[cat].replace(chr(10),' — ')}  [N={n_total}  avg_liq={w_avg:.1f}%  IMD={pct_imd:.0f}%]",
        color=TXT_PRI, fontsize=8.5, fontweight="bold", pad=6
    )

legend_patches = [
    mpatches.Patch(color=TIER_COLORS["descontado"],   label=">90%  descontado"),
    mpatches.Patch(color=TIER_COLORS["muy_probable"], label="75-90%  muy probable"),
    mpatches.Patch(color=TIER_COLORS["probable"],     label="60-75%  probable"),
    mpatches.Patch(color=TIER_COLORS["cola"],         label="<60%   cola"),
    mpatches.Patch(facecolor="white", alpha=0.9,      label="Alpha alto = in-model-domain"),
    mpatches.Patch(facecolor="white", alpha=0.35,     label="Alpha bajo + OOD = out-of-domain"),
    mpatches.Patch(color=HORIZON_COLORS["short_term"],  label="SHO = short_term (≤7d)"),
    mpatches.Patch(color=HORIZON_COLORS["medium_term"], label="MED = medium_term (8-30d)"),
    mpatches.Patch(color=HORIZON_COLORS["long_term"],   label="LON = long_term (>30d)"),
]
fig2.legend(handles=legend_patches, loc="lower center", ncol=5, fontsize=8,
            facecolor=BG_PANEL, edgecolor=BORDER, labelcolor=TXT_PRI,
            framealpha=0.9, bbox_to_anchor=(0.5, -0.04))

fig2.suptitle(
    "Ranking Polymarket por Categoría — 23 Marzo 2026\n"
    "Barra opaca = in-model-domain · Barra transparente + 'OOD' = out-of-domain · "
    "Tag izquierda = scenario_horizon",
    color=TXT_PRI, fontsize=12, fontweight="bold", y=1.01
)
plt.tight_layout(pad=1.8)
p2 = FIGURES_OUT / "polymarket_ranking.png"
plt.savefig(p2, dpi=150, bbox_inches="tight", facecolor=BG_DARK, edgecolor="none")
plt.close()
print(f"   Guardado: {p2}")

# ─── FIG 3: TOP INFERENCE MARKETS ──────────────────────────────────────────
print("[3] Top inference markets...")

top_inf = (df[df["selection_flag_for_inference"]]
           .nlargest(20, "signal_quality_score")
           .copy())

fig3, ax3 = plt.subplots(figsize=(16, 9))
fig3.patch.set_facecolor(BG_DARK)
ax3.set_facecolor(BG_PANEL)
for spine in ax3.spines.values():
    spine.set_edgecolor(BORDER)

top_inf = top_inf.sort_values("signal_quality_score", ascending=True)
top_inf["q_short"] = top_inf["question"].apply(lambda q: q[:68]+"..." if len(q)>68 else q)

cat_palette = {
    "supply_side"  : "#d62728",
    "price_direct" : "#ff7f0e",
    "tail_risk"    : "#9467bd",
    "macro_derived": "#1f77b4",
    "safe_haven"   : "#bcbd22",
    "risk_assets"  : "#17becf",
    "other"        : "#8b949e",
}
bar_colors = [cat_palette.get(c, "#8b949e") for c in top_inf["category_project"]]
alphas     = [0.95 if imd else 0.45 for imd in top_inf["in_model_domain"]]

for k, (row, color, alpha) in enumerate(zip(top_inf.itertuples(), bar_colors, alphas)):
    ax3.barh(k, row.signal_quality_score, color=color, height=0.75,
             edgecolor=BORDER, linewidth=0.8, alpha=alpha)
    ax3.text(row.signal_quality_score+0.005, k,
             f"  [{row.yes_prob:.0f}%]  {row.conviction_tier}  "
             f"{row.scenario_horizon[:3].upper()}  "
             f"{'OOD' if not row.in_model_domain else ''}",
             va="center", ha="left", fontsize=7,
             color=TIER_COLORS.get(row.conviction_tier, TXT_SEC))

ax3.set_yticks(range(len(top_inf)))
ax3.set_yticklabels(top_inf["q_short"], fontsize=7.5, color=TXT_PRI)
ax3.set_xlabel("signal_quality_score (0–1)", color=TXT_SEC, fontsize=9)
ax3.set_title(
    "Mercados Prioritarios para Inferencia — Top 20 por signal_quality_score\n"
    "Color = category_project · Alpha = in_model_domain · "
    "[%] = yes_prob · SHO/MED/LON = scenario_horizon",
    color=TXT_PRI, fontsize=11, fontweight="bold", pad=10
)
ax3.tick_params(colors=TXT_SEC)
ax3.set_xlim(0, top_inf["signal_quality_score"].max() * 1.35)

cat_patches = [mpatches.Patch(color=v, label=k)
               for k, v in cat_palette.items() if k != "other"]
ax3.legend(handles=cat_patches, loc="lower right", fontsize=8,
           facecolor=BG_PANEL, edgecolor=BORDER, labelcolor=TXT_PRI)

plt.tight_layout()
p3 = FIGURES_OUT / "polymarket_top_inference.png"
plt.savefig(p3, dpi=150, bbox_inches="tight", facecolor=BG_DARK, edgecolor="none")
plt.close()
print(f"   Guardado: {p3}")

# ─── FIG 4: CURVAS IMPLICITAS con scenario_horizon ─────────────────────────
print("[4] Curvas implicitas actualizadas...")

CURVE_ASSETS = [
    {"name":"WTI Crude Oil", "family":"wti_price_level",   "unit":"$/bbl", "current":98.32},
    {"name":"Gold",          "family":"gold_price_level",  "unit":"$/oz",  "current":4570.0},
    {"name":"S&P 500",       "family":"sp500_level",       "unit":"pts",   "current":6506.0},
]
HORIZON_LS = {
    "short_term" : {"ls":"-",  "ms":7,  "lw":2.0},
    "medium_term": {"ls":"--", "ms":5,  "lw":1.5},
    "long_term"  : {"ls":":",  "ms":4,  "lw":1.2},
}

fig4, axes4 = plt.subplots(1, 3, figsize=(21, 8))
fig4.patch.set_facecolor(BG_DARK)

for idx, cfg in enumerate(CURVE_ASSETS):
    ax = axes4[idx]
    ax.set_facecolor(BG_PANEL)
    for spine in ax.spines.values():
        spine.set_edgecolor(BORDER)

    # Usar threshold_value del parquet (ya calculado en patch_bloque1)
    sub = df[df["scenario_family"] == cfg["family"]].copy()
    # Fallback: si scenario_family no tiene suficientes, usar market_group
    if len(sub) < 4:
        family_fallback = {"wti_price_level":"wti_price","gold_price_level":"gold_price",
                           "sp500_level":"sp500_level"}
        sub = df[df["market_group"] == family_fallback.get(cfg["family"],"")].copy()

    sub = sub.dropna(subset=["threshold_value"])
    sub = sub[sub["threshold_direction"].isin(["above","below"])]

    if sub.empty:
        ax.text(0.5, 0.5, "Sin datos suficientes", transform=ax.transAxes,
                ha="center", color=TXT_SEC)
        continue

    # Una curva por (direction, scenario_horizon)
    for direction in ["above", "below"]:
        base_color = "#d62728" if direction == "above" else "#1f77b4"
        dir_sub = sub[sub["threshold_direction"] == direction]

        for horizon in ["short_term","medium_term","long_term"]:
            hz_sub = (dir_sub[dir_sub["scenario_horizon"] == horizon]
                      .sort_values("threshold_value")
                      .drop_duplicates("threshold_value"))
            if len(hz_sub) < 2:
                continue

            style = HORIZON_LS[horizon]
            # Modular el color por horizonte: más oscuro = más corto
            alpha = {"short_term":0.95,"medium_term":0.7,"long_term":0.45}[horizon]
            hz_short = {"short_term":"≤7d","medium_term":"8-30d","long_term":">30d"}[horizon]
            label = f"{direction.upper()} {hz_short}"

            ax.plot(hz_sub["threshold_value"], hz_sub["yes_prob"],
                    marker="o", linestyle=style["ls"], linewidth=style["lw"],
                    markersize=style["ms"], color=base_color, alpha=alpha,
                    label=label)

            # Anotar puntos con % y si es OOD
            for _, row in hz_sub.iterrows():
                ood_tag = " OOD" if not row["in_model_domain"] else ""
                ax.annotate(f"{row['yes_prob']:.0f}%{ood_tag}",
                            xy=(row["threshold_value"], row["yes_prob"]),
                            xytext=(0, 7), textcoords="offset points",
                            ha="center", fontsize=5.5, color=base_color,
                            alpha=alpha)

    # Precio actual
    ax.axvline(cfg["current"], color="#ff4d4f", linewidth=1.8, linestyle="--",
               alpha=0.9, label=f"Actual: {cfg['current']:,.0f}")
    ax.axhline(50, color=BORDER, linewidth=0.7, linestyle=":", alpha=0.5)
    ax.set_ylim(-5, 108)
    ax.set_xlabel(f"Umbral de precio ({cfg['unit']})", color=TXT_SEC, fontsize=9)
    ax.set_ylabel("Probabilidad implícita Yes (%)", color=TXT_SEC, fontsize=9)
    ax.set_title(
        f"Curva Implícita — {cfg['name']}\n"
        f"Una curva por (dirección × horizon). Análogo a vol surface.",
        color=TXT_PRI, fontsize=10, fontweight="bold", pad=8
    )
    ax.legend(fontsize=7, facecolor=BG_PANEL, edgecolor=BORDER,
              labelcolor=TXT_PRI, framealpha=0.85, loc="best", ncol=2)
    ax.tick_params(colors=TXT_SEC, labelsize=8)

fig4.suptitle(
    "Curvas de Probabilidad Implícita Polymarket — 23 Marzo 2026\n"
    "Línea continua = short_term (≤7d) · punteada = medium · discontinua = long. "
    "Rojo = ABOVE · Azul = BELOW · 'OOD' = Out of model domain",
    color=TXT_PRI, fontsize=12, fontweight="bold", y=1.02
)
plt.tight_layout(pad=2.0)
p4 = FIGURES_OUT / "polymarket_implied_curve.png"
plt.savefig(p4, dpi=150, bbox_inches="tight", facecolor=BG_DARK, edgecolor="none")
plt.close()
print(f"   Guardado: {p4}")

# ─── TABLA SÍNTESIS AMPLIADA ────────────────────────────────────────────────
print("[5] Tabla sintesis ampliada...")

synthesis_records = []
for cat in CAT_ORDER:
    sub = df[df["category_project"] == cat].copy()
    if sub.empty:
        continue
    liq_w   = sub["liquidity"].fillna(0) + 1
    w_avg   = np.average(sub["yes_prob"], weights=liq_w)
    top_conv = sub.nlargest(1, "yes_prob").iloc[0]
    top_vol  = sub.nlargest(1, "volume_24h").iloc[0]
    top_sqs  = sub.nlargest(1, "signal_quality_score").iloc[0]
    dom_tier = sub["conviction_tier"].value_counts().index[0]
    pct_imd  = sub["in_model_domain"].mean() * 100
    avg_dtc  = sub["days_to_close"].mean()

    synthesis_records.append({
        "categoria"             : cat,
        "n_mercados"            : len(sub),
        "prob_media_pond"       : round(w_avg, 1),
        "tier_dominante"        : dom_tier,
        "pct_in_model_domain"   : round(pct_imd, 1),
        "avg_days_to_close"     : round(avg_dtc, 1),
        "top_conv_question"     : top_conv["question"][:70],
        "top_conv_prob"         : top_conv["yes_prob"],
        "top_conv_dtc"          : int(top_conv["days_to_close"]) if pd.notna(top_conv["days_to_close"]) else None,
        "top_vol_question"      : top_vol["question"][:70],
        "top_vol_24h"           : round(top_vol["volume_24h"], 0),
        "top_vol_prob"          : top_vol["yes_prob"],
        "top_sqs_question"      : top_sqs["question"][:70],
        "top_sqs_score"         : top_sqs["signal_quality_score"],
        "top_sqs_prob"          : top_sqs["yes_prob"],
    })

synth_df = pd.DataFrame(synthesis_records)
synth_df.to_parquet(DATA_OUT / "synthesis_by_category.parquet", index=False)
synth_df.to_json(DATA_OUT / "synthesis_by_category.json",
                  orient="records", indent=2, force_ascii=False)

print("\n" + "=" * 110)
print("TABLA DE SINTESIS AMPLIADA — BLOQUE 3")
print("=" * 110)
for _, r in synth_df.iterrows():
    print(f"\n  [{r['categoria'].upper():14s}]  N={r['n_mercados']:3d}  "
          f"prob_pond={r['prob_media_pond']:5.1f}%  "
          f"IMD={r['pct_in_model_domain']:5.1f}%  "
          f"avg_dtc={r['avg_days_to_close']:5.1f}d  "
          f"tier_dom={r['tier_dominante']}")
    print(f"    Top conviccion  : [{r['top_conv_prob']:5.1f}%] {r['top_conv_question']}  (dtc={r['top_conv_dtc']}d)")
    print(f"    Top volumen 24h : [{r['top_vol_prob']:5.1f}%] {r['top_vol_question']}  (vol=${r['top_vol_24h']:,.0f})")
    print(f"    Top sqs         : [{r['top_sqs_prob']:5.1f}%] {r['top_sqs_question']}  (sqs={r['top_sqs_score']:.4f})")

print(f"\nSintesis guardada: {DATA_OUT}/synthesis_by_category.parquet")
print("Todas las figuras actualizadas.")
