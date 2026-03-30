# -*- coding: utf-8 -*-
"""
Patch Bloque 1 — Añade columnas operativas a polymarket_clean.parquet:
  · scenario_horizon
  · threshold_value + threshold_direction
  · scenario_family
  · signal_quality_score
  · selection_flag_for_inference
"""

import pandas as pd
import numpy as np
import re
from pathlib import Path

DATA_OUT = Path("outputs/data/parte3")
df = pd.read_parquet(DATA_OUT / "polymarket_clean.parquet")
print(f"Cargado: {df.shape}")

# ─── 1. scenario_horizon ────────────────────────────────────────────────────
def classify_horizon(dtc):
    if pd.isna(dtc):
        return "unknown"
    if dtc <= 7:
        return "short_term"
    if dtc <= 30:
        return "medium_term"
    return "long_term"

df["scenario_horizon"] = df["days_to_close"].apply(classify_horizon)
print("scenario_horizon:\n", df["scenario_horizon"].value_counts().to_string())

# ─── 2. threshold_value + threshold_direction ───────────────────────────────
# Patrones: $100, $4,500, $6,500, 100pts, 4%, etc.
_PRICE_PAT    = re.compile(r"\$([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]+)?)")
_PERCENT_PAT  = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_PLAIN_NUM_PAT= re.compile(r"\b(\d{3,6}(?:\.\d+)?)\b")   # fallback para índices

_ABOVE_WORDS  = {"over", "above", "exceed", "high", "hit high", "close over",
                 "above", "reach", "top", "bull", "breaks above", "surpass"}
_BELOW_WORDS  = {"under", "below", "fall", "drop", "low", "hit low",
                 "dip", "crash", "decline", "below", "sink"}

def extract_threshold(question: str):
    q = question.replace(",", "")
    # Buscar precio con $
    m = _PRICE_PAT.search(q)
    if m:
        val = float(m.group(1).replace(",", ""))
    else:
        # Buscar porcentaje
        mp = _PERCENT_PAT.search(q)
        if mp:
            val = float(mp.group(1))
        else:
            # Fallback número plano
            mn = _PLAIN_NUM_PAT.search(q)
            val = float(mn.group(1)) if mn else None

    if val is None:
        return None, "none"

    qu = question.lower()
    if any(w in qu for w in _ABOVE_WORDS) or "(high)" in qu:
        direction = "above"
    elif any(w in qu for w in _BELOW_WORDS) or "(low)" in qu:
        direction = "below"
    elif "between" in qu or "range" in qu:
        direction = "range"
    else:
        direction = "unknown"

    return val, direction

df["threshold_value"], df["threshold_direction"] = zip(
    *df["question"].apply(extract_threshold)
)
df["threshold_value"] = pd.to_numeric(df["threshold_value"], errors="coerce")
print(f"\nthreshold_value no nulo: {df['threshold_value'].notna().sum()} / {len(df)}")
print("threshold_direction:\n", df["threshold_direction"].value_counts().to_string())

# ─── 3. scenario_family ─────────────────────────────────────────────────────
# Más granular que market_group, orientado a las familias semánticas del proyecto
FAMILY_RULES = [
    # Crudo / oferta
    ("wti_price_level"   , r"(wti|crude oil|cl)\b.{0,60}(\$|\d{2,3})"),
    ("brent_price_level" , r"brent.{0,40}(\$|\d{2,3})"),
    ("ormuz_closure"     , r"(hormuz|ormuz|strait|tanker|ship)"),
    ("iran_military"     , r"iran.{0,50}(attack|strike|military|forces|troops|enter|action)"),
    ("iran_nuclear"      , r"iran.{0,50}(nuclear|bomb|weapon|enrich)"),
    ("iran_regime"       , r"(iranian regime|iran.{0,30}(fall|topple|collapse|end))"),
    ("opec_production"   , r"(opec|production cut|output cut|saudi.{0,30}oil|aramco)"),
    ("ceasefire_talks"   , r"(ceasefire|peace.talk|negotiat|truce|agreement|meeting|end of (war|conflict|operation))"),
    ("sanctions"         , r"(sanction|embargo|restrict).{0,40}(iran|russia|oil)"),
    ("us_military_iran"  , r"(us forces|us troops|us strike|us enter|us attack|us militar).{0,40}iran"),
    # Macro / crisis
    ("war_escalation"    , r"(world war|ww3|nuclear|expand|escalat|regional war|wider conflict)"),
    ("recession_risk"    , r"recession"),
    ("inflation_cpi"     , r"(inflation|cpi|pce|price index|stagflation)"),
    ("fed_rates"         , r"(federal reserve|fed.{0,20}(rate|cut|hike|pivot|pause)|interest rate)"),
    ("dxy_dollar"        , r"(dollar.{0,20}(index|strength|weak)|dxy|usd\b)"),
    ("us_yields"         , r"(treasury|yield|10.year|t.note|t.bond|tnx)"),
    # Activos
    ("gold_price_level"  , r"gold.{0,60}(\$|\d{3,5})"),
    ("silver_price_level", r"silver.{0,60}(\$|\d{2,3})"),
    ("sp500_level"       , r"(s&p|sp500|spx).{0,60}(\$|\d{4,5})"),
    ("sp500_direction"   , r"(s&p|sp500|spx).{0,40}(up|down|bull|bear|rally|correct)"),
    ("nasdaq_level"      , r"nasdaq.{0,40}(\$|\d{4,6})"),
    ("bitcoin_level"     , r"(bitcoin|btc).{0,60}(\$|\d{4,7})"),
    ("equity_general"    , r"(stocks|equity|market|dow|index).{0,40}(up|down|crash|bull|bear)"),
]

def assign_family(question: str) -> str:
    q = question.lower()
    for family, pattern in FAMILY_RULES:
        if re.search(pattern, q):
            return family
    return "other"

df["scenario_family"] = df["question"].apply(assign_family)
print("\nscenario_family (top 20):\n", df["scenario_family"].value_counts().head(20).to_string())

# ─── 4. signal_quality_score ────────────────────────────────────────────────
def minmax(series):
    lo, hi = series.min(), series.max()
    if hi == lo:
        return pd.Series(0.5, index=series.index)
    return (series - lo) / (hi - lo)

# time_weight: mercados más cortos puntúan más (urgencia)
df["_time_w"] = 1 / (df["days_to_close"].clip(lower=1))

df["signal_quality_score"] = (
    0.35 * minmax(df["yes_prob"])        +
    0.30 * minmax(df["liquidity"])       +
    0.20 * minmax(df["volume_24h"])      +
    0.15 * minmax(df["_time_w"])
).round(4)
df.drop(columns=["_time_w"], inplace=True)

print(f"\nsignal_quality_score desc:\n{df['signal_quality_score'].describe().round(3).to_string()}")

# ─── 5. selection_flag_for_inference ────────────────────────────────────────
q75_sqs = df["signal_quality_score"].quantile(0.75)
q50_sqs = df["signal_quality_score"].quantile(0.50)

HIGH_RELEVANCE_CATS = {"supply_side", "price_direct", "tail_risk"}

df["selection_flag_for_inference"] = (
    (df["signal_quality_score"] >= q75_sqs)                                     # top cuartil en calidad
    | ((df["category_project"].isin(HIGH_RELEVANCE_CATS)) &
       (df["signal_quality_score"] >= q50_sqs))                                 # relevante + calidad media
    | (df["in_model_domain"] & (df["signal_quality_score"] >= q50_sqs))         # dentro del dominio + calidad media
    | (df["conviction_tier"].isin(["descontado","muy_probable"]) &
       df["category_project"].isin(HIGH_RELEVANCE_CATS))                        # alta convicción en crudo/geo
)

n_selected = df["selection_flag_for_inference"].sum()
print(f"\nselection_flag_for_inference = True: {n_selected} / {len(df)}  ({n_selected/len(df)*100:.1f}%)")

# ─── Guardar ────────────────────────────────────────────────────────────────
new_cols = ["scenario_horizon","threshold_value","threshold_direction",
            "scenario_family","signal_quality_score","selection_flag_for_inference"]
print(f"\nColumnas nuevas: {new_cols}")
df.to_parquet(DATA_OUT / "polymarket_clean.parquet", index=False)
print(f"polymarket_clean.parquet actualizado: {df.shape}")

# Resumen mercados seleccionados para inferencia
print("\nTop 20 mercados seleccionados para inferencia (por signal_quality_score):")
top_inf = (df[df["selection_flag_for_inference"]]
           .nlargest(20, "signal_quality_score")
           [["question","yes_prob","signal_quality_score","category_project",
             "scenario_horizon","threshold_value","threshold_direction"]])
print(top_inf.to_string(index=False))
