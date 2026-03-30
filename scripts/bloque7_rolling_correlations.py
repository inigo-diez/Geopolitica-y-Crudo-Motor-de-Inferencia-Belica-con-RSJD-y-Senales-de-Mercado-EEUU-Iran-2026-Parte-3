# -*- coding: utf-8 -*-
"""
Bloque 7 — Analisis de Correlaciones Rodantes
Parte 3 — Geopolitica y Crudo WTI: Inteligencia en Tiempo Real

Sub-bloques:
  7.1 - Correlaciones rodantes (ventana 30d) entre pares clave: 2020-2026
  7.2 - Comparativa de matrices de correlacion: pre-belico vs. periodo belico
  7.3 - Heatmap de cambio de correlacion (delta)
"""

import sys, io, os

# Redirect stdout solo en ejecucion directa (no en Jupyter donde puede fallar)
if not hasattr(sys.stdout, 'getvalue') and hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    except Exception:
        pass

import pandas as pd
import numpy as np
import matplotlib
try:
    matplotlib.use("Agg")
except Exception:
    pass
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import warnings
from pathlib import Path
warnings.filterwarnings("ignore")

# Detectar la raiz del proyecto de forma robusta
_cwd = Path.cwd()
if (_cwd / "data_clean").exists():
    ROOT = _cwd
elif (_cwd.parent / "data_clean").exists():
    ROOT = _cwd.parent
else:
    ROOT = _cwd

DATA_CLEAN  = ROOT / "data_clean"
RAW_OUT     = ROOT / "outputs" / "raw"
FIGURES_OUT = ROOT / "outputs" / "figures" / "parte3"
FIGURES_OUT.mkdir(parents=True, exist_ok=True)

# ── Paleta dark ──────────────────────────────────────────────────────────────
BG_DARK  = "#0d1117"
BG_PANEL = "#161b22"
BORDER   = "#30363d"
TXT_PRI  = "#e6edf3"
TXT_SEC  = "#8b949e"
C_GRID   = "#21262d"

# ── Fechas clave ─────────────────────────────────────────────────────────────
IRN_START  = pd.Timestamp("2026-02-27")   # inicio guerra EEUU-Iran
PRE_START  = pd.Timestamp("2025-01-01")   # inicio periodo pre-belico para comparar
ANALYSIS_START = pd.Timestamp("2020-01-01")  # inicio del periodo de correlaciones rodantes
ROLL_WINDOW = 30  # dias de negociacion

print("=" * 70)
print("BLOQUE 7 — ANALISIS DE CORRELACIONES RODANTES")
print("=" * 70)

# ── Carga de series historicas (CSV) ─────────────────────────────────────────
print("\nCargando series historicas...")

wti_h   = pd.read_csv(DATA_CLEAN / "wti_usa_clean.csv",
                      parse_dates=["date"]).set_index("date")["wti_close"].dropna()
ovx_h   = pd.read_csv(DATA_CLEAN / "ovx_clean.csv",
                      parse_dates=["date"]).set_index("date")["ovx_close"].dropna()
vix_h   = pd.read_csv(DATA_CLEAN / "vix_clean.csv",
                      parse_dates=["date"]).set_index("date")["vix_close"].dropna()
dxy_h   = pd.read_csv(DATA_CLEAN / "dxy_clean.csv",
                      parse_dates=["date"]).set_index("date")["dxy_close"].dropna()
brent_h = pd.read_csv(DATA_CLEAN / "brent_clean.csv",
                      parse_dates=["date"]).set_index("date")["brent_close"].dropna()

# ── Carga de datos del periodo belico (parquets yfinance) ────────────────────
print("Cargando datos periodo belico (yfinance parquets)...")

war_assets = {}
ASSET_LABELS = {
    "wti":    "WTI",
    "brent":  "Brent",
    "ovx":    "OVX",
    "vix":    "VIX",
    "dxy":    "DXY",
    "sp500":  "S&P500",
    "nasdaq": "NASDAQ",
    "gold":   "Oro",
    "silver": "Plata",
    "xom":    "XOM",
    "cvx":    "CVX",
    "tnx":    "TNX",
    "btc":    "Bitcoin",
}

for name in ASSET_LABELS:
    pq_path = RAW_OUT / f"{name}_daily.parquet"
    if pq_path.exists():
        df = pd.read_parquet(pq_path)
        war_assets[name] = df["close"].dropna()
        print(f"  {name:8s}: {len(df)} dias  ({df.index.min().date()} -> {df.index.max().date()})")
    else:
        print(f"  {name:8s}: no encontrado")

# ── Construccion del dataset maestro de precios ──────────────────────────────
# Series historicas disponibles (5 activos core, desde 2020)
core_series = {
    "WTI":   wti_h,
    "Brent": brent_h,
    "OVX":   ovx_h,
    "VIX":   vix_h,
    "DXY":   dxy_h,
}

df_core = pd.DataFrame(core_series).loc[ANALYSIS_START:]
df_core = df_core.dropna(how="all")
df_core = df_core.ffill(limit=3)

print(f"\n  Dataset core (5 activos): {df_core.shape}")
print(f"  Rango: {df_core.index.min().date()} -> {df_core.index.max().date()}")

# Log-retornos para correlaciones
log_ret_core = np.log(df_core / df_core.shift(1)).dropna()

# ── Dataset periodo belico (todos los activos disponibles) ───────────────────
war_dfs = []
for name, ser in war_assets.items():
    label = ASSET_LABELS[name]
    war_dfs.append(ser.rename(label))

if war_dfs:
    df_war_full = pd.concat(war_dfs, axis=1)
    df_war_full = df_war_full.dropna(how="all").ffill(limit=3)
    log_ret_war = np.log(df_war_full / df_war_full.shift(1)).dropna()
    print(f"\n  Dataset belico completo: {df_war_full.shape}")
else:
    log_ret_war = pd.DataFrame()
    print("\n  AVISO: sin datos de periodo belico via parquet")


# ════════════════════════════════════════════════════════════════════════════
# SUB-BLOQUE 7.1 — CORRELACIONES RODANTES 30d (2020-2026)
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("SUB-BLOQUE 7.1 — CORRELACIONES RODANTES (ventana 30d, 2020-2026)")
print("="*70)

# Pares de interes analitico
PAIRS = [
    ("WTI",   "OVX",   "WTI-OVX\n(crudo vs. volatilidad propia)",      "#58a6ff"),
    ("WTI",   "VIX",   "WTI-VIX\n(crudo vs. miedo sistemico)",          "#f78166"),
    ("WTI",   "DXY",   "WTI-DXY\n(crudo vs. dolar: relacion inversa)",  "#3fb950"),
    ("OVX",   "VIX",   "OVX-VIX\n(vol. energia vs. vol. sistemica)",    "#d29922"),
    ("WTI",   "Brent", "WTI-Brent\n(convergencia de precios de crudo)", "#bc8cff"),
]

fig, axes = plt.subplots(len(PAIRS), 1, figsize=(14, 16), facecolor=BG_DARK)
fig.suptitle(
    f"Correlaciones rodantes ({ROLL_WINDOW} dias de negociacion) — 2020-2026\n"
    "Log-retornos diarios. Sombreado rojo: inicio guerra EEUU-Iran (27-feb-2026)",
    color=TXT_PRI, fontsize=12, fontweight="bold", y=0.99
)

for ax, (a, b, label, color) in zip(axes, PAIRS):
    ax.set_facecolor(BG_PANEL)
    for spine in ax.spines.values():
        spine.set_color(BORDER)

    if a in log_ret_core.columns and b in log_ret_core.columns:
        roll_corr = log_ret_core[a].rolling(ROLL_WINDOW).corr(log_ret_core[b]).dropna()
        ax.plot(roll_corr.index, roll_corr.values, color=color, lw=1.5, alpha=0.9)
        ax.fill_between(roll_corr.index, 0, roll_corr.values,
                        where=roll_corr.values > 0, alpha=0.12, color=color)
        ax.fill_between(roll_corr.index, 0, roll_corr.values,
                        where=roll_corr.values < 0, alpha=0.12, color="#f85149")

        # Estadisticos clave
        mean_pre = roll_corr[roll_corr.index < IRN_START].mean()
        mean_war = roll_corr[roll_corr.index >= IRN_START].mean()
        last_val = roll_corr.iloc[-1]

        ax.axhline(0, color=TXT_SEC, ls=":", lw=0.8, alpha=0.5)
        ax.axhline(mean_pre, color=color, ls="--", lw=0.8, alpha=0.5,
                   label=f"Media pre-guerra: {mean_pre:.2f}")

        # Sombreado periodo belico
        ax.axvspan(IRN_START, roll_corr.index.max(),
                   alpha=0.08, color="#f85149", label="Periodo belico")

        # Valor snapshot
        ax.text(0.99, 0.88, f"Ultimo: {last_val:.2f}",
                transform=ax.transAxes, ha="right", va="top",
                color=TXT_PRI, fontsize=9, fontweight="bold")
        ax.text(0.99, 0.72, f"Media guerra: {mean_war:.2f}",
                transform=ax.transAxes, ha="right", va="top",
                color=color, fontsize=8.5)

    ax.set_title(label, color=TXT_PRI, fontsize=10, pad=5)
    ax.set_ylabel("Correlacion", color=TXT_SEC, fontsize=8)
    ax.set_ylim(-1.05, 1.05)
    ax.tick_params(colors=TXT_SEC, labelsize=8)
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m"))
    ax.xaxis.set_major_locator(mdates.MonthLocator(interval=4))
    ax.grid(True, color=C_GRID, alpha=0.5, lw=0.5)
    ax.legend(loc="upper left", framealpha=0.25, facecolor=BG_PANEL,
              edgecolor=BORDER, labelcolor=TXT_PRI, fontsize=8)

plt.tight_layout(rect=[0, 0, 1, 0.98])
out_path = FIGURES_OUT / "bloque7_correlaciones_rodantes.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=BG_DARK)
plt.close()
print(f"  Figura guardada: {out_path.name}")

# Imprimir cambios de correlacion relevantes
print("\n  Cambios de correlacion (pre-guerra vs. periodo belico):")
print(f"  {'Par':<20} {'Media pre':>10} {'Media guerra':>13} {'Delta':>8}")
print("  " + "-"*55)
for a, b, _, _ in PAIRS:
    if a in log_ret_core.columns and b in log_ret_core.columns:
        rc = log_ret_core[a].rolling(ROLL_WINDOW).corr(log_ret_core[b]).dropna()
        pre  = rc[rc.index < IRN_START].mean()
        war  = rc[rc.index >= IRN_START].mean()
        delta = war - pre
        flag = " <<< RUPTURA" if abs(delta) > 0.25 else ""
        print(f"  {a}-{b:<15} {pre:>10.3f} {war:>13.3f} {delta:>+8.3f}{flag}")


# ════════════════════════════════════════════════════════════════════════════
# SUB-BLOQUE 7.2 — COMPARATIVA DE MATRICES: PRE-BELICO vs. PERIODO BELICO
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("SUB-BLOQUE 7.2 — MATRICES DE CORRELACION: PRE-BELICO vs. BELICO")
print("="*70)

# Periodo pre-belico: 2025-01-01 a 2026-02-26
ret_pre = log_ret_core[(log_ret_core.index >= PRE_START) &
                       (log_ret_core.index <  IRN_START)]
# Periodo belico: 2026-02-27 a 2026-03-23
ret_war_core = log_ret_core[log_ret_core.index >= IRN_START]

print(f"  Periodo pre-belico:  {len(ret_pre)} dias ({PRE_START.date()} -> {IRN_START.date()})")
print(f"  Periodo belico:      {len(ret_war_core)} dias ({IRN_START.date()} -> {log_ret_core.index.max().date()})")

corr_pre = ret_pre.corr()
corr_war = ret_war_core.corr()
corr_delta = corr_war - corr_pre

print("\n  Matriz pre-belico:")
print(corr_pre.round(3).to_string())
print("\n  Matriz periodo belico:")
print(corr_war.round(3).to_string())
print("\n  Delta (guerra - pre-guerra):")
print(corr_delta.round(3).to_string())

# Figura: 3 heatmaps lado a lado
fig, axes = plt.subplots(1, 3, figsize=(18, 6), facecolor=BG_DARK)
fig.suptitle(
    "Matrices de correlacion (log-retornos diarios): pre-belico vs. periodo belico vs. delta",
    color=TXT_PRI, fontsize=12, fontweight="bold"
)

labels = list(corr_pre.columns)
n = len(labels)

def draw_heatmap(ax, corr_matrix, title, vmin=-1, vmax=1, cmap="RdYlBu"):
    ax.set_facecolor(BG_PANEL)
    for spine in ax.spines.values():
        spine.set_color(BORDER)

    data = corr_matrix.values
    im = ax.imshow(data, cmap=cmap, vmin=vmin, vmax=vmax, aspect="auto")

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9, color=TXT_PRI)
    ax.set_yticklabels(labels, fontsize=9, color=TXT_PRI)
    ax.tick_params(colors=TXT_SEC)

    for i in range(n):
        for j in range(n):
            val = data[i, j]
            txt_color = "white" if abs(val) > 0.5 else "black"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=8, color=txt_color, fontweight="bold")

    ax.set_title(title, color=TXT_PRI, fontsize=11, pad=8, fontweight="bold")
    plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04).ax.tick_params(colors=TXT_SEC)

draw_heatmap(axes[0], corr_pre,
             f"Pre-belico\n({PRE_START.strftime('%d-%b-%Y')} — {IRN_START.strftime('%d-%b-%Y')})",
             cmap="RdYlBu")
draw_heatmap(axes[1], corr_war,
             f"Periodo belico\n({IRN_START.strftime('%d-%b-%Y')} — 23-Mar-2026)",
             cmap="RdYlBu")
draw_heatmap(axes[2], corr_delta,
             "Delta (guerra - pre-guerra)\nRojo=correlacion mas negativa, Azul=mas positiva",
             vmin=-0.8, vmax=0.8, cmap="RdBu")

plt.tight_layout()
out_path = FIGURES_OUT / "bloque7_matrices_correlacion.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=BG_DARK)
plt.close()
print(f"\n  Figura guardada: {out_path.name}")


# ════════════════════════════════════════════════════════════════════════════
# SUB-BLOQUE 7.3 — HEATMAP COMPLETO PERIODO BELICO (todos los activos)
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("SUB-BLOQUE 7.3 — HEATMAP COMPLETO PERIODO BELICO (13 activos)")
print("="*70)

if not log_ret_war.empty and len(log_ret_war) >= 5:
    corr_war_full = log_ret_war.corr()
    n_full = len(corr_war_full)
    labels_full = list(corr_war_full.columns)

    fig, ax = plt.subplots(figsize=(13, 11), facecolor=BG_DARK)
    ax.set_facecolor(BG_PANEL)
    for spine in ax.spines.values():
        spine.set_color(BORDER)

    data = corr_war_full.values
    im = ax.imshow(data, cmap="RdYlBu", vmin=-1, vmax=1, aspect="auto")

    ax.set_xticks(range(n_full))
    ax.set_yticks(range(n_full))
    ax.set_xticklabels(labels_full, rotation=45, ha="right", fontsize=10, color=TXT_PRI)
    ax.set_yticklabels(labels_full, fontsize=10, color=TXT_PRI)
    ax.tick_params(colors=TXT_SEC)

    for i in range(n_full):
        for j in range(n_full):
            val = data[i, j]
            txt_color = "white" if abs(val) > 0.5 else "#1a1a2e"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=8.5, color=txt_color, fontweight="bold")

    cbar = plt.colorbar(im, ax=ax, fraction=0.03, pad=0.03)
    cbar.ax.tick_params(colors=TXT_SEC)
    cbar.set_label("Correlacion (log-retornos)", color=TXT_SEC, fontsize=9)

    ax.set_title(
        f"Matriz de correlaciones — Periodo belico completo\n"
        f"({IRN_START.strftime('%d-%b-%Y')} — 23-Mar-2026) — {len(log_ret_war)} dias de negociacion",
        color=TXT_PRI, fontsize=12, fontweight="bold", pad=12
    )

    plt.tight_layout()
    out_path = FIGURES_OUT / "bloque7_heatmap_belico_completo.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=BG_DARK)
    plt.close()
    print(f"  Figura guardada: {out_path.name}")

    # Destacar correlaciones sorprendentes
    print("\n  Correlaciones destacadas (|r| > 0.6):")
    print(f"  {'Par':<22} {'Correlacion':>12}  Interpretacion")
    print("  " + "-"*70)
    seen = set()
    for i, a in enumerate(labels_full):
        for j, b in enumerate(labels_full):
            if i >= j:
                continue
            val = corr_war_full.loc[a, b]
            if abs(val) > 0.6:
                key = tuple(sorted([a, b]))
                if key not in seen:
                    seen.add(key)
                    direction = "positiva" if val > 0 else "negativa"
                    print(f"  {a}-{b:<17} {val:>12.3f}  Correlacion {direction} fuerte")
else:
    print("  AVISO: datos insuficientes para heatmap completo del periodo belico")

print("\n" + "="*70)
print("BLOQUE 7 COMPLETADO")
print("="*70)
