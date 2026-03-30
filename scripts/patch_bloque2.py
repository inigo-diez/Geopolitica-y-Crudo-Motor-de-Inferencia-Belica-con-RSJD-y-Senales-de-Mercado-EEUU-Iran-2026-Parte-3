# -*- coding: utf-8 -*-
import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
"""
Patch Bloque 2 — Añade campos analíticos al snapshot de mercados:
  · shock_regime_today
  · tabla pre_trump_vs_post_trump
  · historical_percentile_label
  · event_reaction_type por activo
"""

import pandas as pd
import numpy as np
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.gridspec as mgrid
from pathlib import Path
from datetime import timezone

DATA_OUT    = Path("outputs/data/parte3")
RAW_OUT     = Path("outputs/raw")
FIGURES_OUT = Path("outputs/figures/parte3")

BG_DARK  = "#0d1117"
BG_PANEL = "#161b22"
BORDER   = "#30363d"
TXT_PRI  = "#e6edf3"
TXT_SEC  = "#8b949e"

TRUMP_POST_UTC = pd.Timestamp("2026-03-23 11:05:00", tz="UTC")

snap = pd.read_parquet(DATA_OUT / "market_snapshot_20260323.parquet")
print(f"Snapshot cargado: {snap.shape}")

# ─── 1. historical_percentile_label ─────────────────────────────────────────
def pct_label(pct, asset):
    if pd.isna(pct):
        return "unknown"
    vol_assets = {"ovx", "vix"}
    if asset in vol_assets:
        if pct >= 95: return "extreme"
        if pct >= 80: return "high"
        if pct >= 60: return "elevated"
        return "normal"
    else:
        if pct >= 95 or pct <= 5:  return "extreme"
        if pct >= 80 or pct <= 20: return "high"
        if pct >= 60 or pct <= 40: return "elevated"
        return "normal"

snap["historical_percentile_label"] = snap.apply(
    lambda r: pct_label(r["pct_hist"], r["asset"]), axis=1
)
print("historical_percentile_label:\n", snap[["asset","pct_hist","historical_percentile_label"]].to_string(index=False))

# ─── 2. pre_trump_vs_post_trump ─────────────────────────────────────────────
ASSETS_EVENT = ["wti","gold","vix","ovx","sp500","nasdaq","dxy","xom","cvx","silver","btc","tnx"]

def load_5min(name):
    try:
        df = pd.read_parquet(RAW_OUT / f"{name}_5min.parquet")
        df.index = pd.to_datetime(df.index, utc=True)
        return df
    except Exception:
        return None

pre_post_records = []
for name in ASSETS_EVENT:
    df5 = load_5min(name)
    if df5 is None or len(df5) < 5:
        continue
    # Pre-evento: último cierre antes de 11:05 UTC
    pre_bars = df5[df5.index < TRUMP_POST_UTC]
    if pre_bars.empty:
        continue
    pre_price = float(pre_bars["close"].iloc[-1])

    # Post-evento: 11:05 UTC en adelante (primera hora = primeros 12 bares de 5min)
    post_bars = df5[df5.index >= TRUMP_POST_UTC]
    if post_bars.empty:
        continue

    post_lo  = float(post_bars["low"].min())
    post_hi  = float(post_bars["high"].max())
    t_lo_bar = post_bars["low"].idxmin()
    t_hi_bar = post_bars["high"].idxmax()
    last     = float(df5["close"].iloc[-1])

    # Minutos hasta el extremo más significativo
    pct_lo = (post_lo - pre_price) / pre_price * 100
    pct_hi = (post_hi - pre_price) / pre_price * 100

    # El extremo que más se aleja de pre
    if abs(pct_lo) > abs(pct_hi):
        extreme_price  = post_lo
        extreme_pct    = pct_lo
        extreme_t      = t_lo_bar
        extreme_dir    = "low"
    else:
        extreme_price  = post_hi
        extreme_pct    = pct_hi
        extreme_t      = t_hi_bar
        extreme_dir    = "high"

    minutes_to_extreme = (extreme_t - TRUMP_POST_UTC).total_seconds() / 60
    recovered = (last / pre_price - 1) * 100

    pre_post_records.append({
        "asset"              : name,
        "pre_event_price"    : round(pre_price, 2),
        "post_extreme_price" : round(extreme_price, 2),
        "extreme_direction"  : extreme_dir,
        "absolute_change"    : round(extreme_price - pre_price, 2),
        "pct_change"         : round(extreme_pct, 2),
        "minutes_to_extreme" : round(minutes_to_extreme, 0),
        "close_vs_pre_pct"   : round(recovered, 2),
        "recovered_into_close": last > pre_price if extreme_dir == "low" else last < pre_price,
    })

pre_post_df = pd.DataFrame(pre_post_records)
print("\nTabla pre/post Trump:")
print(pre_post_df.to_string(index=False))
pre_post_df.to_parquet(DATA_OUT / "pre_post_trump.parquet", index=False)
pre_post_df.to_json(DATA_OUT / "pre_post_trump.json", orient="records", indent=2, force_ascii=False)

# ─── 3. event_reaction_type ─────────────────────────────────────────────────
REACTION_RULES = {
    "wti"   : lambda r: "panic_reversal"      if r["pct_change"] < -10   else "moderate_drop",
    "gold"  : lambda r: "safe_haven_failed"   if r["pct_change"] < -5    else "resilient",
    "silver": lambda r: "safe_haven_failed"   if r["pct_change"] < -5    else "moderate_drop",
    "vix"   : lambda r: "stress_confirmed"    if r["pre_event_price"]>25  else "stress_released",
    "ovx"   : lambda r: "energy_shock_peak"   if r["pre_event_price"]>70  else "elevated",
    "sp500" : lambda r: "relief_rebound"      if r["pct_change"] > 0      else "partial_decline",
    "nasdaq": lambda r: "relief_rebound"      if r["pct_change"] > 0      else "partial_decline",
    "xom"   : lambda r: "relative_winner"     if r["close_vs_pre_pct"] > -2 else "energy_sector_sell",
    "cvx"   : lambda r: "relative_winner"     if r["close_vs_pre_pct"] > -2 else "energy_sector_sell",
    "dxy"   : lambda r: "policy_uncertainty"  if abs(r["pct_change"]) < 1  else "dollar_flight",
    "tnx"   : lambda r: "inflation_repricing" if r["pct_change"] > 5       else "rates_ambiguous",
    "btc"   : lambda r: "risk_off_correlation" if r["pct_change"] < -3     else "decorrelated",
}

reaction_map = {}
for _, row in pre_post_df.iterrows():
    name = row["asset"]
    rule = REACTION_RULES.get(name)
    reaction_map[name] = rule(row) if rule else "undefined"

pre_post_df["event_reaction_type"] = pre_post_df["asset"].map(reaction_map)
pre_post_df.to_parquet(DATA_OUT / "pre_post_trump.parquet", index=False)
pre_post_df.to_json(DATA_OUT / "pre_post_trump.json", orient="records", indent=2, force_ascii=False)

print("\nevent_reaction_type:")
for _, r in pre_post_df[["asset","pct_change","event_reaction_type"]].iterrows():
    print(f"  {r['asset']:8s}  {r['pct_change']:>+7.2f}%  ->  {r['event_reaction_type']}")

# ─── 4. shock_regime_today ──────────────────────────────────────────────────
snap_dict = snap.set_index("asset")["current_value"].to_dict()
snap_pct  = snap.set_index("asset")["pct_hist"].to_dict()
snap_ytd  = snap.set_index("asset")["ytd_return_pct"].to_dict()

wti_ytd   = snap_ytd.get("wti", 0)
ovx_pct   = snap_pct.get("ovx", 50)
gold_reac = reaction_map.get("gold", "")
vix_reac  = reaction_map.get("vix", "")
wti_reac  = reaction_map.get("wti", "")

active_regimes = []
if wti_ytd  > 30 and ovx_pct >= 85:
    active_regimes.append("energy_shock")
if gold_reac == "safe_haven_failed":
    active_regimes.append("safe_haven_failure")
if wti_reac == "panic_reversal":
    active_regimes.append("policy_reversal_shock")
if "relief_rebound" in [reaction_map.get("sp500"), reaction_map.get("nasdaq")]:
    active_regimes.append("partial_risk_on")
if snap_pct.get("tnx", 50) >= 75:
    active_regimes.append("inflation_shock")
if snap_pct.get("vix", 50) >= 80:
    active_regimes.append("risk_off")

shock_regime = active_regimes[0] if len(active_regimes) == 1 else "mixed_regime"
regime_detail = " + ".join(active_regimes) if active_regimes else "normal"

print(f"\nshock_regime_today : {shock_regime}")
print(f"regimes activos    : {regime_detail}")

# Añadir al snapshot
snap["shock_regime_today"] = shock_regime
snap["shock_regime_detail"] = regime_detail
snap = snap.merge(
    pre_post_df[["asset","pre_event_price","post_extreme_price","pct_change",
                 "minutes_to_extreme","close_vs_pre_pct","event_reaction_type"]],
    on="asset", how="left"
)
snap.to_parquet(DATA_OUT / "market_snapshot_20260323.parquet", index=False)

# Actualizar JSON
with open(DATA_OUT / "market_snapshot_20260323.json") as f:
    snap_json = json.load(f)
snap_json["metadata"]["shock_regime_today"]  = shock_regime
snap_json["metadata"]["shock_regime_detail"] = regime_detail
snap_json["pre_post_trump"] = pre_post_df.to_dict(orient="records")
with open(DATA_OUT / "market_snapshot_20260323.json", "w", encoding="utf-8") as f:
    json.dump(snap_json, f, ensure_ascii=False, indent=2, default=str)

print(f"\nSnapshot actualizado: {snap.shape}")
print(f"JSON actualizado: market_snapshot_20260323.json")

# ─── 5. Figura pre/post Trump ────────────────────────────────────────────────
print("\nGenerando figura pre/post Trump...")

# Colores por reaction type
REACTION_COLORS = {
    "panic_reversal"     : "#d62728",
    "safe_haven_failed"  : "#ff7f0e",
    "stress_confirmed"   : "#9467bd",
    "relief_rebound"     : "#2ca02c",
    "relative_winner"    : "#1f77b4",
    "energy_shock_peak"  : "#8c564b",
    "policy_uncertainty" : "#7f7f7f",
    "inflation_repricing": "#e377c2",
    "risk_off_correlation": "#bcbd22",
    "moderate_drop"      : "#ff9896",
    "elevated"           : "#aec7e8",
    "partial_decline"    : "#98df8a",
    "decorrelated"       : "#c5b0d5",
    "energy_sector_sell" : "#c49c94",
    "rates_ambiguous"    : "#f7b6d2",
    "resilient"          : "#c7c7c7",
    "undefined"          : "#555555",
}

fig, ax = plt.subplots(figsize=(14, 6))
fig.patch.set_facecolor(BG_DARK)
ax.set_facecolor(BG_PANEL)
for spine in ax.spines.values():
    spine.set_edgecolor(BORDER)

ppd = pre_post_df.sort_values("pct_change")
colors = [REACTION_COLORS.get(r, "#8b949e") for r in ppd["event_reaction_type"]]

bars = ax.barh(range(len(ppd)), ppd["pct_change"], color=colors,
               height=0.7, edgecolor=BORDER, linewidth=0.5)

for k, (bar, row) in enumerate(zip(bars, ppd.itertuples())):
    xpos = bar.get_width()
    ha   = "left" if xpos >= 0 else "right"
    off  = 0.3 if xpos >= 0 else -0.3
    ax.text(xpos + off, k,
            f"{row.pct_change:+.1f}%  [{row.event_reaction_type}]",
            va="center", ha=ha, fontsize=7.5, color=TXT_PRI)

ax.set_yticks(range(len(ppd)))
ax.set_yticklabels(ppd["asset"].str.upper(), fontsize=9, color=TXT_PRI)
ax.axvline(0, color=TXT_SEC, linewidth=0.8, alpha=0.6)
ax.set_xlabel("% cambio desde precio pre-evento hasta extremo intradiario", color=TXT_SEC, fontsize=9)
ax.set_title(
    "Impacto del Anuncio Trump — Pre-evento vs Extremo Intradiario\n"
    "23 Marzo 2026 · Barra 11:05 UTC (07:05 ET). Color = event_reaction_type.",
    color=TXT_PRI, fontsize=11, fontweight="bold", pad=10
)
ax.tick_params(colors=TXT_SEC)

plt.tight_layout()
fig_path = FIGURES_OUT / "pre_post_trump.png"
plt.savefig(fig_path, dpi=150, bbox_inches="tight", facecolor=BG_DARK, edgecolor="none")
plt.close()
print(f"Figura guardada: {fig_path}")

print("\n=== RESUMEN shock_regime_today ===")
print(f"  Regime       : {shock_regime}")
print(f"  Componentes  : {regime_detail}")
print(f"  WTI YTD      : {wti_ytd:+.1f}%")
print(f"  OVX pct_hist : {ovx_pct:.0f}th percentile")
print(f"  Gold reaction: {gold_reac}")
print(f"  WTI reaction : {wti_reac}")
