# -*- coding: utf-8 -*-
"""
Bloque 2 — Snapshot de Mercados Financieros
Parte 3 — Geopolítica y Crudo WTI: Inteligencia en Tiempo Real
Snapshot: 23 de marzo de 2026
"""

import pandas as pd
import numpy as np
import json
import yfinance as yf
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
import warnings
warnings.filterwarnings("ignore")

ROOT        = Path(".")
RAW_OUT     = ROOT / "outputs" / "raw"
DATA_OUT    = ROOT / "outputs" / "data"    / "parte3"
FIGURES_OUT = ROOT / "outputs" / "figures" / "parte3"
DATA_OUT.mkdir(parents=True, exist_ok=True)
FIGURES_OUT.mkdir(parents=True, exist_ok=True)

SNAPSHOT_DATE  = date(2026, 3, 23)
YTD_START      = date(2025, 12, 31)
TRUMP_POST_UTC = pd.Timestamp("2026-03-23 11:05:00", tz="UTC")
TRUMP_POST_ET  = "07:05 ET"

print(f"Snapshot  : {SNAPSHOT_DATE}")
print(f"YTD base  : {YTD_START}")
print(f"Evento    : Trump Truth Social post ~{TRUMP_POST_ET}  ({TRUMP_POST_UTC})")

# ─────────────────────────────────────────────────────────────────────────────
# 1. PRECIOS ACTUALES Y YTD
# ─────────────────────────────────────────────────────────────────────────────
# ytd_base = precio cierre 31-dic-2025 (verificado con yfinance)
ASSET_META = {
    # name     ticker         in_model  hist_start   ytd_base_close
    "wti"   : ("CL=F",       True,  "2015-01-01", 57.42),
    "brent" : ("BZ=F",       True,  "2015-01-01", 60.85),
    "ovx"   : ("^OVX",       True,  "2015-01-01", 30.17),
    "vix"   : ("^VIX",       True,  "2015-01-01", 14.95),
    "dxy"   : ("DX-Y.NYB",   True,  "2015-01-01", 98.28),
    "sp500" : ("^GSPC",      False, "2020-01-01", 6845.50),
    "nasdaq": ("^IXIC",      False, "2020-01-01", 23241.99),
    "gold"  : ("GC=F",       False, "2020-01-01", 4325.60),
    "silver": ("SI=F",       False, "2020-01-01", 70.13),
    "xom"   : ("XOM",        False, "2020-01-01", 119.54),
    "cvx"   : ("CVX",        False, "2020-01-01", 150.93),
    "tnx"   : ("^TNX",       False, "2020-01-01", 4.16),
    "btc"   : ("BTC-USD",    False, "2020-01-01", 87508.83),
}

current_prices = {}
for name in ASSET_META:
    try:
        df = pd.read_parquet(RAW_OUT / f"{name}_daily.parquet")
        last_close = float(df["close"].dropna().iloc[-1])
        current_prices[name] = last_close
    except Exception as e:
        print(f"  ERROR cargando {name}: {e}")

print("\nPrecios actuales:")
for k, v in current_prices.items():
    ytd_base = ASSET_META[k][3]
    ytd_ret  = (v / ytd_base - 1) * 100
    print(f"  {k:8s}  {v:>10.2f}  YTD={ytd_ret:>+7.1f}%")

# ─────────────────────────────────────────────────────────────────────────────
# 2. PERCENTILES HISTORICOS
# ─────────────────────────────────────────────────────────────────────────────
print("\nDescargando historico para percentiles...")
hist_data = {}
for name, (ticker, in_model, hist_start, _) in ASSET_META.items():
    df = yf.download(ticker, start=hist_start, end="2026-01-01",
                     auto_adjust=True, progress=False)
    if df.empty:
        print(f"  VACIO {name}")
        continue
    if hasattr(df.columns, "levels"):
        df.columns = [c[0].lower() for c in df.columns]
    else:
        df.columns = [c.lower() for c in df.columns]
    hist_data[name] = df["close"].dropna()
    print(f"  {name:8s}: {len(df)} sesiones")

percentiles = {}
for name, series in hist_data.items():
    pcts = {p: float(np.percentile(series, p)) for p in [10, 25, 50, 75, 90, 95, 99]}
    curr = current_prices.get(name)
    if curr is not None:
        pcts["current_pct"] = float(np.mean(series.values <= curr) * 100)
    percentiles[name] = pcts

print("\nPercentiles (valor actual vs historico):")
for name, pcts in percentiles.items():
    curr = current_prices.get(name, 0)
    c_pct = pcts.get("current_pct", 0)
    print(f"  {name:8s}  actual={curr:>10.2f}  "
          f"P50={pcts[50]:>8.2f}  P90={pcts[90]:>8.2f}  "
          f"pct_actual={c_pct:>5.1f}%")

# ─────────────────────────────────────────────────────────────────────────────
# 3. ETIQUETAS CUALITATIVAS
# ─────────────────────────────────────────────────────────────────────────────
VOL_ASSETS = {"ovx", "vix"}

def stress_label(pct: float, asset: str) -> str:
    if asset in VOL_ASSETS:
        if pct >= 90: return "EXTREMO"
        if pct >= 75: return "elevado"
        return "normal"
    else:
        if pct >= 95 or pct <= 5:  return "EXTREMO"
        if pct >= 85 or pct <= 15: return "elevado"
        return "normal"

labels = {}
for name in ASSET_META:
    curr = current_prices.get(name)
    if curr is None or name not in percentiles:
        labels[name] = "N/A"
        continue
    pct = percentiles[name].get("current_pct", 50)
    labels[name] = stress_label(pct, name)

# ─────────────────────────────────────────────────────────────────────────────
# 4. ANALISIS INTRADIARIO
# ─────────────────────────────────────────────────────────────────────────────
intraday = {}
for name in ASSET_META:
    try:
        df = pd.read_parquet(RAW_OUT / f"{name}_5min.parquet")
        df.index = pd.to_datetime(df.index, utc=True)
        intraday[name] = df
    except Exception:
        pass

print(f"\n{'Activo':8s} {'Open':>8} {'High':>8} {'Low':>8} {'Last':>8}  {'Swing%':>7}  {'T_low (UTC)':>19}")
print("-" * 80)

intraday_stats = {}
for name in ASSET_META:
    if name not in intraday:
        continue
    df  = intraday[name]
    op  = float(df["open"].iloc[0])
    hi  = float(df["high"].max())
    lo  = float(df["low"].min())
    cl  = float(df["close"].iloc[-1])
    t_lo = df["low"].idxmin()
    swing = (hi - lo) / op * 100 if op > 0 else 0
    ret_from_open = (cl / op - 1) * 100 if op > 0 else 0

    intraday_stats[name] = {
        "open": op, "high": hi, "low": lo, "close_last": cl,
        "swing_pct": round(swing, 2), "t_low_utc": str(t_lo),
        "ret_from_open": round(ret_from_open, 2)
    }
    print(f"{name:8s} {op:>8.2f} {hi:>8.2f} {lo:>8.2f} {cl:>8.2f}  {swing:>6.1f}%  {str(t_lo)[:19]:>19}")

# WTI crash detail
if "wti" in intraday:
    wti_df  = intraday["wti"]
    bars    = wti_df.loc[:TRUMP_POST_UTC]
    pre     = float(bars["close"].iloc[-2]) if len(bars) >= 2 else None
    bar_lo  = float(wti_df.loc[TRUMP_POST_UTC, "low"]) if TRUMP_POST_UTC in wti_df.index else None
    if pre and bar_lo:
        print(f"\nDetalle crash WTI:")
        print(f"  Pre-anuncio  : ${pre:.2f}")
        print(f"  Minimo barra : ${bar_lo:.2f}")
        print(f"  Caida        : -${pre - bar_lo:.2f}  ({(bar_lo/pre-1)*100:.1f}%)")

# ─────────────────────────────────────────────────────────────────────────────
# 5. SNAPSHOT DATAFRAME
# ─────────────────────────────────────────────────────────────────────────────
records = []
for name, (ticker, in_model, hist_start, ytd_base) in ASSET_META.items():
    curr = current_prices.get(name)
    if curr is None:
        continue
    ytd_ret  = round((curr / ytd_base - 1) * 100, 2)
    pct_hist = percentiles.get(name, {}).get("current_pct")
    label    = labels.get(name, "N/A")
    p50      = percentiles.get(name, {}).get(50)
    p90      = percentiles.get(name, {}).get(90)
    p99      = percentiles.get(name, {}).get(99)
    iday     = intraday_stats.get(name, {})

    records.append({
        "asset"              : name,
        "ticker"             : ticker,
        "in_model"           : in_model,
        "current_value"      : round(curr, 2),
        "ytd_base"           : ytd_base,
        "ytd_return_pct"     : ytd_ret,
        "hist_start"         : hist_start,
        "pct_hist"           : round(pct_hist, 1) if pct_hist is not None else None,
        "p50_hist"           : round(p50, 2) if p50 else None,
        "p90_hist"           : round(p90, 2) if p90 else None,
        "p99_hist"           : round(p99, 2) if p99 else None,
        "stress_label"       : label,
        "intra_open"         : iday.get("open"),
        "intra_high"         : iday.get("high"),
        "intra_low"          : iday.get("low"),
        "intra_close"        : iday.get("close_last"),
        "intra_swing_pct"    : iday.get("swing_pct"),
        "intra_t_low_utc"    : iday.get("t_low_utc"),
        "intra_ret_from_open": iday.get("ret_from_open"),
        "snapshot_date"      : str(SNAPSHOT_DATE),
    })

snap_df = pd.DataFrame(records)
out_parquet = DATA_OUT / "market_snapshot_20260323.parquet"
snap_df.to_parquet(out_parquet, index=False)
print(f"\nSnapshot DF guardado: {out_parquet}  shape={snap_df.shape}")

# ─────────────────────────────────────────────────────────────────────────────
# 6. JSON
# ─────────────────────────────────────────────────────────────────────────────
wti_swing = {}
if "wti" in intraday:
    wti_df = intraday["wti"]
    bars   = wti_df.loc[:TRUMP_POST_UTC]
    if len(bars) >= 2 and TRUMP_POST_UTC in wti_df.index:
        pre    = float(bars["close"].iloc[-2])
        lo_val = float(wti_df.loc[TRUMP_POST_UTC, "low"])
        cl_val = float(wti_df["close"].iloc[-1])
        wti_swing = {
            "pre_announcement_price": round(pre, 2),
            "intraday_low"          : round(lo_val, 2),
            "drop_pct"              : round((lo_val / pre - 1) * 100, 2),
            "recovery_close"        : round(cl_val, 2),
        }

snapshot_json = {
    "metadata": {
        "snapshot_date": str(SNAPSHOT_DATE),
        "generated_at" : datetime.now(timezone.utc).isoformat(),
        "event_anchor" : {
            "description"  : "Trump Truth Social post -- 5-day pause + productive conversations",
            "timestamp_et" : TRUMP_POST_ET,
            "timestamp_utc": str(TRUMP_POST_UTC),
            "iran_denial"  : "FARS News Agency denied any contact ~56 min later",
            "wti_swing"    : wti_swing,
        }
    },
    "assets": {}
}

for _, row in snap_df.iterrows():
    asset_dict = {}
    for k, v in row.items():
        if k == "asset":
            continue
        if v is None:
            continue
        if isinstance(v, float) and np.isnan(v):
            continue
        asset_dict[k] = v
    snapshot_json["assets"][row["asset"]] = asset_dict

json_path = DATA_OUT / "market_snapshot_20260323.json"
with open(json_path, "w", encoding="utf-8") as f:
    json.dump(snapshot_json, f, ensure_ascii=False, indent=2, default=str)
print(f"JSON guardado: {json_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 7. FIGURA
# ─────────────────────────────────────────────────────────────────────────────
PLOT_ASSETS = [
    ("wti",    "WTI ($/bbl)",       "#d62728", True),
    ("brent",  "Brent ($/bbl)",     "#ff7f0e", True),
    ("ovx",    "OVX (vol impl.)",   "#9467bd", True),
    ("gold",   "Oro ($/oz)",        "#bcbd22", False),
    ("silver", "Plata ($/oz)",      "#17becf", False),
    ("vix",    "VIX",               "#e377c2", True),
    ("sp500",  "S&P 500",           "#1f77b4", False),
    ("nasdaq", "Nasdaq",            "#2ca02c", False),
    ("xom",    "XOM ($)",           "#8c564b", False),
    ("cvx",    "CVX ($)",           "#7f7f7f", False),
    ("dxy",    "DXY",               "#aec7e8", True),
    ("tnx",    "10Y Yield (%)",     "#ffbb78", False),
    ("btc",    "Bitcoin ($)",       "#ff9896", False),
]

fig, axes = plt.subplots(5, 3, figsize=(20, 24))
fig.patch.set_facecolor("#0d1117")
axes_flat = axes.flatten()

for ax in axes_flat:
    ax.set_facecolor("#161b22")
    ax.tick_params(colors="#8b949e", labelsize=7)
    for spine in ax.spines.values():
        spine.set_edgecolor("#30363d")


def load_daily_series(name):
    try:
        df = pd.read_parquet(RAW_OUT / f"{name}_daily.parquet")
        df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        return df["close"].dropna()
    except Exception:
        return None


def load_5min_series(name):
    try:
        df = pd.read_parquet(RAW_OUT / f"{name}_5min.parquet")
        df.index = pd.to_datetime(df.index, utc=True).tz_convert("US/Eastern").tz_localize(None)
        return df["close"].dropna()
    except Exception:
        return None


for idx, (name, label_txt, color, in_model) in enumerate(PLOT_ASSETS):
    ax = axes_flat[idx]
    daily    = load_daily_series(name)
    intra_5m = load_5min_series(name)

    if daily is None:
        ax.text(0.5, 0.5, f"{name}\nNo data", transform=ax.transAxes,
                ha="center", va="center", color="#8b949e", fontsize=9)
        ax.set_title(label_txt, color="#e6edf3", fontsize=9, pad=4)
        continue

    daily_prev = daily[daily.index < pd.Timestamp("2026-03-23")]

    if intra_5m is not None and len(intra_5m) > 0:
        ax.plot(daily_prev.index, daily_prev.values,
                color=color, linewidth=1.2, alpha=0.85)
        ax.plot(intra_5m.index, intra_5m.values,
                color=color, linewidth=0.9, alpha=1.0)
        ax.axvline(pd.Timestamp("2026-03-23 04:00"),
                   color="#8b949e", linewidth=0.5, linestyle=":", alpha=0.6)
        # Línea evento Trump
        trump_ts = pd.Timestamp("2026-03-23 07:05")
        ax.axvline(trump_ts, color="#ff4d4f", linewidth=1.5,
                   linestyle="--", alpha=0.85)
    else:
        ax.plot(daily.index, daily.values, color=color, linewidth=1.2, alpha=0.85)

    # Anotacion WTI crash
    if name == "wti" and intra_5m is not None:
        lo_val = intra_5m.min()
        lo_idx = intra_5m.idxmin()
        ax.annotate(f"${lo_val:.2f}\n({TRUMP_POST_ET})",
                    xy=(lo_idx, lo_val),
                    xytext=(lo_idx - timedelta(hours=3), lo_val + 2),
                    color="#ff4d4f", fontsize=6.5,
                    arrowprops=dict(arrowstyle="->", color="#ff4d4f", lw=0.8))

    # Anotacion Gold crash
    if name == "gold" and intra_5m is not None:
        lo_val = intra_5m.min()
        lo_idx = intra_5m.idxmin()
        ax.annotate(f"${lo_val:,.0f}\n(-8.8%)",
                    xy=(lo_idx, lo_val),
                    xytext=(lo_idx + timedelta(hours=1), lo_val + 80),
                    color="#ff4d4f", fontsize=6.5,
                    arrowprops=dict(arrowstyle="->", color="#ff4d4f", lw=0.8))

    # Bandas P10/P90
    p90 = percentiles.get(name, {}).get(90)
    p10 = percentiles.get(name, {}).get(10)
    if p90:
        ax.axhline(p90, color="#ffa640", linewidth=0.7, linestyle=":", alpha=0.5)
    if p10:
        ax.axhline(p10, color="#58a6ff", linewidth=0.7, linestyle=":", alpha=0.5)

    # Título y metainfo
    in_m_tag = " [modelo]" if in_model else ""
    ax.set_title(f"{label_txt}{in_m_tag}", color="#e6edf3",
                 fontsize=8.5, pad=4, fontweight="bold")

    last_val = float(daily.dropna().iloc[-1])
    ytd_base = ASSET_META[name][3]
    ytd_ret  = (last_val / ytd_base - 1) * 100
    pct_h    = percentiles.get(name, {}).get("current_pct")
    lbl_str  = labels.get(name, "")
    lbl_color = ("#ff4d4f" if lbl_str == "EXTREMO"
                 else "#f0a040" if lbl_str == "elevado"
                 else "#3fb950")
    pct_str  = f"P{pct_h:.0f}" if pct_h is not None else ""
    info_txt = f"${last_val:,.1f}\nYTD {ytd_ret:+.1f}%\n{pct_str} {lbl_str}"
    ax.text(0.02, 0.97, info_txt, transform=ax.transAxes,
            va="top", ha="left", color=lbl_color, fontsize=7,
            bbox=dict(boxstyle="round,pad=0.2", facecolor="#0d1117",
                      alpha=0.7, edgecolor="none"))

    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m/%d"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(interval=1))
    plt.setp(ax.xaxis.get_majorticklabels(), rotation=30, ha="right")

# Panel 13: resumen evento
ax_ev = axes_flat[13]
ax_ev.set_facecolor("#0d1117")
for spine in ax_ev.spines.values():
    spine.set_edgecolor("#30363d")
ax_ev.axis("off")
ev_lines = [
    "EVENTO ANCLA — 23 MARZO 2026",
    "",
    "07:05 ET — Trump en Truth Social:",
    "  'Pausa 5 dias + conversaciones",
    "   productivas con Iran'",
    "",
    "Reaccion (primeros 10min):",
    "  WTI:  $98.59 -> $84.37  (-14.3%)",
    "  Gold: $4,365 -> $4,100  (-8.8%)",
    "  VIX:  31.0  -> 20.3    (-34%)",
    "  S&P:  rebote fuerte",
    "",
    "08:01 ET — FARS News Agency:",
    "  Iran niega cualquier contacto",
    "",
    "Resultado:",
    "  WTI cierra ~$86-88",
    "  Gold rebota a ~$4,500",
    "  ~$3 trillones cap. en 56 min",
]
ax_ev.text(0.05, 0.97, "\n".join(ev_lines),
           transform=ax_ev.transAxes, va="top", ha="left",
           color="#e6edf3", fontsize=8.5, family="monospace",
           bbox=dict(boxstyle="round", facecolor="#161b22",
                     alpha=0.8, edgecolor="#ff4d4f"))

# Panel 14: leyenda
ax_leg = axes_flat[14]
ax_leg.set_facecolor("#0d1117")
for spine in ax_leg.spines.values():
    spine.set_edgecolor("#30363d")
ax_leg.axis("off")
legend_elements = [
    Line2D([0], [0], color="#ff4d4f", lw=1.5, ls="--",
           label="Trump Truth Social post"),
    Line2D([0], [0], color="#ffa640", lw=0.8, ls=":",
           label="P90 historico"),
    Line2D([0], [0], color="#58a6ff", lw=0.8, ls=":",
           label="P10 historico"),
    mpatches.Patch(color="#ff4d4f", label="EXTREMO"),
    mpatches.Patch(color="#f0a040", label="elevado"),
    mpatches.Patch(color="#3fb950", label="normal"),
    mpatches.Patch(color="#8b949e", label="[modelo] = var. en Partes 1-2"),
]
ax_leg.legend(handles=legend_elements, loc="center", fontsize=8.5,
              facecolor="#161b22", edgecolor="#30363d",
              labelcolor="#e6edf3", framealpha=0.9)
ax_leg.set_title("Leyenda", color="#e6edf3", fontsize=9, pad=4)

fig.suptitle(
    "Snapshot de Mercados — 23 Marzo 2026\n"
    "Guerra EEUU-Iran activa | Ormuz cerrado | WTI +71% desde inicio conflicto (27-feb)",
    color="#e6edf3", fontsize=13, fontweight="bold", y=1.01
)

plt.tight_layout(pad=1.5)
fig_path = FIGURES_OUT / "market_snapshot.png"
plt.savefig(fig_path, dpi=150, bbox_inches="tight",
            facecolor=fig.get_facecolor(), edgecolor="none")
plt.close()
print(f"Figura guardada: {fig_path}")

# ─────────────────────────────────────────────────────────────────────────────
# 8. TABLA RESUMEN FINAL
# ─────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 80)
print("SNAPSHOT MERCADOS — 23 MARZO 2026")
print("=" * 80)
print(f"{'Activo':8s} {'Valor':>10} {'YTD%':>8} {'Pct_hist':>9} {'Nivel':>10}  "
      f"{'Intra_low':>10} {'Swing%':>8}  Modelo?")
print("-" * 80)
for _, r in snap_df.sort_values("ytd_return_pct", ascending=False).iterrows():
    pct_str   = f"{r['pct_hist']:.0f}%" if pd.notna(r["pct_hist"]) else "N/A"
    swing_str = f"{r['intra_swing_pct']:.1f}%" if pd.notna(r["intra_swing_pct"]) else "N/A"
    lo_str    = f"{r['intra_low']:.2f}" if pd.notna(r["intra_low"]) else "N/A"
    lbl       = r["stress_label"]
    lbl_sym   = "!!" if lbl == "EXTREMO" else ("!" if lbl == "elevado" else " ")
    mdl       = "[Si]" if r["in_model"] else ""
    print(f"{r['asset']:8s} {r['current_value']:>10.2f} {r['ytd_return_pct']:>+8.1f}% "
          f"{pct_str:>8} {lbl_sym}{lbl:>9}  {lo_str:>10} {swing_str:>8}  {mdl}")

print("\n=== SENALES EXTREMAS ===")
for _, r in snap_df[snap_df["stress_label"] == "EXTREMO"].iterrows():
    print(f"  {r['asset']:8s}  {r['current_value']:>10.2f}  "
          f"pct_hist={r['pct_hist']}%  YTD={r['ytd_return_pct']:+.1f}%")
