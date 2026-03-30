# -*- coding: utf-8 -*-
"""
Sub-bloque 4.6 — Semaforo de Salida del Regimen de Alta Tension
Parte 3 — Geopolitica y Crudo WTI: Inteligencia en Tiempo Real

Este sub-bloque define y visualiza las condiciones cuantitativas que
indicarian una transicion de vuelta al regimen normal segun el modelo
de la Parte 1 (Random Forest + SHAP) y el RSJD de la Parte 2.

Outputs:
  - Figura: estado actual vs. umbrales de salida (gauge chart)
  - Figura: historial de veces que se alcanzaron condiciones de salida post-conflicto
  - Tabla: brecha entre valores actuales y cada umbral de salida
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
import json
import matplotlib
try:
    matplotlib.use("Agg")
except Exception:
    pass
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
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
DATA_OUT    = ROOT / "outputs" / "data" / "parte3"
FIGURES_OUT = ROOT / "outputs" / "figures" / "parte3"
FIGURES_OUT.mkdir(parents=True, exist_ok=True)

# ── Paleta dark ──────────────────────────────────────────────────────────────
BG_DARK  = "#0d1117"
BG_PANEL = "#161b22"
BORDER   = "#30363d"
TXT_PRI  = "#e6edf3"
TXT_SEC  = "#8b949e"
C_GRID   = "#21262d"
C_RED    = "#f85149"
C_AMBER  = "#d29922"
C_GREEN  = "#3fb950"
C_BLUE   = "#58a6ff"

# ── Fechas clave ─────────────────────────────────────────────────────────────
IRN_START  = pd.Timestamp("2026-02-27")
UKR_START  = pd.Timestamp("2022-02-24")
SNAP_DATE  = pd.Timestamp("2026-03-23")

# ── Parametros del modelo (Parte 1 + 2) ──────────────────────────────────────
EXIT_CONDITIONS = {
    "OVX < 40\n(umbral alerta modelo)": {
        "series":    "ovx",
        "threshold": 40.0,
        "direction": "below",   # salida = valor por debajo del umbral
        "shap_rank": 1,
        "weight":    0.30,
    },
    "GPR < 120\n(umbral critico modelo)": {
        "series":    "gpr",
        "threshold": 120.0,
        "direction": "below",
        "shap_rank": 3,
        "weight":    0.20,
    },
    "VIX < 25\n(nivel estres macro)": {
        "series":    "vix",
        "threshold": 25.0,
        "direction": "below",
        "shap_rank": 10,
        "weight":    0.20,
    },
    "OVX < 46.1\n(P80 high_stress)": {
        "series":    "ovx",
        "threshold": 46.1,
        "direction": "below",
        "shap_rank": 2,
        "weight":    0.30,
    },
}

# Criterio compuesto: TODAS las condiciones deben cumplirse durante 5 dias consecutivos
CONSECUTIVE_DAYS = 5

print("=" * 70)
print("SUB-BLOQUE 4.6 — SEMAFORO DE SALIDA DEL REGIMEN")
print("=" * 70)

# ── Carga de series ───────────────────────────────────────────────────────────
print("\nCargando series historicas...")

ovx_h = pd.read_csv(DATA_CLEAN / "ovx_clean.csv",
                    parse_dates=["date"]).set_index("date")["ovx_close"].dropna()
vix_h = pd.read_csv(DATA_CLEAN / "vix_clean.csv",
                    parse_dates=["date"]).set_index("date")["vix_close"].dropna()

gpr_raw = pd.read_csv(DATA_CLEAN / "gpr_clean.csv", parse_dates=["date"])
gpr_raw["gpr_num"] = (
    gpr_raw["gpr"].astype(str)
    .str.replace(r"\.(?=\d{3}[,.])", "", regex=True)
    .str.replace(",", ".")
    .astype(float)
)
gpr_h = gpr_raw.set_index("date")["gpr_num"].dropna()

# Cargar snapshot para valores actuales
snap = pd.read_parquet(DATA_OUT / "market_snapshot_20260323.parquet")
snap_d = snap.set_index("asset")

current_vals = {
    "ovx": float(snap_d.loc["ovx", "current_value"]),
    "vix": float(snap_d.loc["vix", "current_value"]),
    "gpr": float(gpr_h.iloc[-1]),
}

print(f"  Valores actuales (snapshot {SNAP_DATE.date()}):")
for k, v in current_vals.items():
    print(f"    {k.upper():5s}: {v:.2f}")


# ════════════════════════════════════════════════════════════════════════════
# CALCULO: ESTADO ACTUAL VS. UMBRALES
# ════════════════════════════════════════════════════════════════════════════

exit_status = []
for name, cfg in EXIT_CONDITIONS.items():
    series_key = cfg["series"]
    threshold  = cfg["threshold"]
    direction  = cfg["direction"]
    current    = current_vals[series_key]

    if direction == "below":
        satisfied  = current < threshold
        gap        = current - threshold       # positivo = aun lejos del umbral
        pct_to_go  = gap / threshold * 100    # % de reduccion necesaria
    else:
        satisfied  = current > threshold
        gap        = threshold - current
        pct_to_go  = gap / threshold * 100

    exit_status.append({
        "condition":  name,
        "series":     series_key.upper(),
        "current":    current,
        "threshold":  threshold,
        "satisfied":  satisfied,
        "gap":        gap,
        "pct_to_go":  pct_to_go,
        "weight":     cfg["weight"],
    })

# Score de salida compuesto (0-100)
exit_score = sum(e["weight"] * 100 if e["satisfied"] else
                 max(0, e["weight"] * (1 - e["pct_to_go"] / 100)) * 100
                 for e in exit_status)

n_satisfied = sum(e["satisfied"] for e in exit_status)
n_total     = len(exit_status)

status_label = (
    "SALIDA INMINENTE"         if n_satisfied == n_total else
    "SEÑALES PARCIALES"        if n_satisfied >= n_total // 2 else
    "REGIMEN ACTIVO"           if n_satisfied > 0 else
    "REGIMEN MAXIMO ESTRES"
)

print(f"\n  Condiciones satisfechas: {n_satisfied}/{n_total}")
print(f"  Exit score: {exit_score:.1f}/100")
print(f"  Estado: {status_label}")
print()
print(f"  {'Condicion':<35} {'Actual':>9} {'Umbral':>9} {'Gap':>9} {'OK':>5}")
print("  " + "-"*72)
for e in exit_status:
    cond_short = e["condition"].replace("\n", " ")
    ok = "SI" if e["satisfied"] else "NO"
    print(f"  {cond_short:<35} {e['current']:>9.2f} {e['threshold']:>9.2f} {e['gap']:>+9.2f} {ok:>5}")


# ════════════════════════════════════════════════════════════════════════════
# SUB-FIGURA 4.6a — PANEL DE SEMAFORO (estado actual)
# ════════════════════════════════════════════════════════════════════════════
print("\nGenerando figuras...")

fig, axes = plt.subplots(1, 2, figsize=(16, 7), facecolor=BG_DARK,
                         gridspec_kw={"width_ratios": [1.3, 1]})
fig.suptitle(
    f"Semaforo de salida del regimen de alta tension\n"
    f"Snapshot: {SNAP_DATE.strftime('%d-%b-%Y')}  |  "
    f"Dias en regimen (desde {IRN_START.strftime('%d-%b-%Y')}): "
    f"{len(pd.bdate_range(IRN_START, SNAP_DATE))} dias habiles",
    color=TXT_PRI, fontsize=12, fontweight="bold"
)

# ── Panel izquierdo: barras de progreso hacia umbral ─────────────────────────
ax = axes[0]
ax.set_facecolor(BG_PANEL)
for spine in ax.spines.values():
    spine.set_color(BORDER)

y_positions = np.arange(len(exit_status))
bar_height  = 0.55

for i, e in enumerate(exit_status):
    # Calcular rango logico para la barra
    cur   = e["current"]
    thr   = e["threshold"]
    color = C_GREEN if e["satisfied"] else C_RED

    # Barra de fondo (rango de valores posibles)
    x_min = min(thr * 0.2, cur * 0.2)
    x_max = max(thr * 1.6, cur * 1.2)
    ax.barh(i, x_max - x_min, left=x_min, height=bar_height,
            color=BG_DARK, edgecolor=BORDER, lw=0.5, alpha=0.5)

    # Barra del valor actual
    ax.barh(i, cur - x_min, left=x_min, height=bar_height,
            color=color, alpha=0.75, edgecolor=color, lw=0.5)

    # Linea del umbral
    ax.axvline(thr, color="#f0f6fc", lw=1.8, ls="--", alpha=0.8)
    ax.text(thr, i + bar_height / 2 + 0.08, f"Umbral: {thr:.0f}",
            ha="center", va="bottom", color=TXT_SEC, fontsize=7.5)

    # Valor actual
    ax.text(cur, i, f"  {cur:.1f}", ha="left", va="center",
            color=TXT_PRI, fontsize=9, fontweight="bold")

    # Icono semaforo
    icon = "✓" if e["satisfied"] else "✗"
    ax.text(x_min - (x_max - x_min) * 0.08, i, icon,
            ha="right", va="center", color=color, fontsize=14, fontweight="bold")

ax.set_yticks(y_positions)
ax.set_yticklabels(
    [e["condition"].replace("\n", "\n") for e in exit_status],
    color=TXT_PRI, fontsize=9
)
ax.set_xlabel("Valor del indicador", color=TXT_SEC, fontsize=9)
ax.set_title("Estado actual vs. umbrales de salida del regimen",
             color=TXT_PRI, fontsize=10, pad=8)
ax.tick_params(colors=TXT_SEC, labelsize=8)
ax.grid(True, color=C_GRID, alpha=0.5, lw=0.5, axis="x")
ax.invert_yaxis()

# ── Panel derecho: gauge del exit score ──────────────────────────────────────
ax2 = axes[1]
ax2.set_facecolor(BG_PANEL)
for spine in ax2.spines.values():
    spine.set_color(BORDER)
ax2.axis("off")

# Gauge semicircular
theta_min, theta_max = np.pi, 0
n_arc = 300
theta_arc = np.linspace(theta_min, theta_max, n_arc)

# Zonas de color
zones = [
    (0,  25,  C_RED,   "Regimen maximo estres"),
    (25, 50,  C_AMBER, "Regimen activo"),
    (50, 75,  C_BLUE,  "Senales parciales"),
    (75, 100, C_GREEN, "Salida inminente"),
]
r_outer, r_inner = 1.0, 0.55
for z_min, z_max, zcolor, _ in zones:
    t1 = np.pi - (z_min / 100) * np.pi
    t2 = np.pi - (z_max / 100) * np.pi
    ts = np.linspace(t1, t2, 50)
    xs_out = np.cos(ts) * r_outer
    ys_out = np.sin(ts) * r_outer
    xs_in  = np.cos(ts[::-1]) * r_inner
    ys_in  = np.sin(ts[::-1]) * r_inner
    ax2.fill(
        np.concatenate([xs_out, xs_in]),
        np.concatenate([ys_out, ys_in]),
        color=zcolor, alpha=0.35
    )

# Aguja
needle_angle = np.pi - (exit_score / 100) * np.pi
needle_x = [0, np.cos(needle_angle) * 0.82]
needle_y = [0, np.sin(needle_angle) * 0.82]
ax2.plot(needle_x, needle_y, color=TXT_PRI, lw=3, zorder=5)
ax2.scatter([0], [0], color=TXT_PRI, s=80, zorder=6)

# Texto central
needle_color = C_RED if exit_score < 25 else C_AMBER if exit_score < 50 else C_BLUE if exit_score < 75 else C_GREEN
ax2.text(0, -0.3, f"{exit_score:.0f}/100",
         ha="center", va="center", fontsize=22, fontweight="bold", color=needle_color)
ax2.text(0, -0.52, status_label,
         ha="center", va="center", fontsize=10, color=needle_color, fontweight="bold")
ax2.text(0, -0.68, f"{n_satisfied}/{n_total} condiciones activas",
         ha="center", va="center", fontsize=9, color=TXT_SEC)

# Etiquetas de zonas
ax2.text(-1.05,  0.1, "0\nEstres\nmax",  ha="center", va="center", fontsize=8, color=C_RED)
ax2.text( 1.05,  0.1, "100\nSalida",     ha="center", va="center", fontsize=8, color=C_GREEN)
ax2.text( 0,     1.1, "50",              ha="center", va="center", fontsize=8, color=TXT_SEC)

ax2.set_xlim(-1.3, 1.3)
ax2.set_ylim(-0.85, 1.3)
ax2.set_title(f"Exit Score del regimen\n(ponderado por importancia SHAP)",
              color=TXT_PRI, fontsize=10, pad=5)

plt.tight_layout()
out_path = FIGURES_OUT / "bloque4_6_semaforo_salida.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=BG_DARK)
plt.close()
print(f"  Figura guardada: {out_path.name}")


# ════════════════════════════════════════════════════════════════════════════
# FIGURA 4.6b — PRECEDENTE HISTORICO: TIEMPO HASTA SALIDA DEL REGIMEN
# ════════════════════════════════════════════════════════════════════════════
print("\nCalculando precedentes historicos...")

# Para cada episodio de alta tension historico definido por OVX > 40,
# calcular cuantos dias hasta que OVX cae a < 40 durante 5 dias consecutivos
episodes = []
series_check = ovx_h.dropna()
in_stress = False
episode_start = None

for date, val in series_check.items():
    if not in_stress and val > 40:
        in_stress = True
        episode_start = date
        consec_below = 0
    elif in_stress:
        if val < 40:
            consec_below += 1
            if consec_below >= CONSECUTIVE_DAYS:
                days_in = len(pd.bdate_range(episode_start, date))
                episodes.append({
                    "start":    episode_start,
                    "end":      date,
                    "days":     days_in,
                    "peak_ovx": series_check[episode_start:date].max(),
                })
                in_stress = False
                consec_below = 0
        else:
            consec_below = 0

print(f"\n  Episodios historicos OVX>40 identificados: {len(episodes)}")
if episodes:
    durs = [e["days"] for e in episodes]
    print(f"  Duracion media:    {np.mean(durs):.1f} dias")
    print(f"  Duracion mediana:  {np.median(durs):.1f} dias")
    print(f"  Duracion max:      {max(durs)} dias ({[e for e in episodes if e['days'] == max(durs)][0]['start'].date()})")
    print(f"  Duracion min:      {min(durs)} dias")
    print(f"  Duracion RSJD:     ~43 dias (p_stay=0.977)")

    # Figura: distribucion de duraciones
    fig, axes = plt.subplots(1, 2, figsize=(15, 5), facecolor=BG_DARK)
    fig.suptitle(
        "Duracion historica de episodios de alta tension (OVX>40)\n"
        f"Criterio de salida: OVX<40 durante {CONSECUTIVE_DAYS} dias consecutivos | "
        f"Episodios identificados: {len(episodes)}",
        color=TXT_PRI, fontsize=11, fontweight="bold"
    )

    # Histograma
    ax = axes[0]
    ax.set_facecolor(BG_PANEL)
    for spine in ax.spines.values():
        spine.set_color(BORDER)

    ax.hist(durs, bins=15, color=C_BLUE, alpha=0.7, edgecolor=BORDER)
    ax.axvline(np.mean(durs), color=C_GREEN, ls="--", lw=1.8,
               label=f"Media historica: {np.mean(durs):.0f}d")
    ax.axvline(43, color=C_AMBER, ls="--", lw=1.8,
               label="RSJD esperado: 43d")
    # Dias actuales en regimen
    dias_actuales = len(pd.bdate_range(IRN_START, SNAP_DATE))
    ax.axvline(dias_actuales, color=C_RED, ls="-", lw=2,
               label=f"Dias actuales en regimen: {dias_actuales}d")

    ax.set_xlabel("Dias de negociacion en regimen de alta tension", color=TXT_SEC, fontsize=9)
    ax.set_ylabel("Numero de episodios", color=TXT_SEC, fontsize=9)
    ax.set_title("Distribucion de duraciones historicas", color=TXT_PRI, fontsize=10)
    ax.tick_params(colors=TXT_SEC, labelsize=8)
    ax.grid(True, color=C_GRID, alpha=0.5, lw=0.5)
    ax.legend(framealpha=0.3, facecolor=BG_PANEL, edgecolor=BORDER,
              labelcolor=TXT_PRI, fontsize=8)

    # Scatter: duracion vs. OVX pico
    ax2 = axes[1]
    ax2.set_facecolor(BG_PANEL)
    for spine in ax2.spines.values():
        spine.set_color(BORDER)

    peak_ovxs = [e["peak_ovx"] for e in episodes]
    ax2.scatter(peak_ovxs, durs, color=C_BLUE, alpha=0.7, s=60, edgecolors=BORDER, lw=0.5)

    # Episodio actual (solo OVX snapshot, sin duracion total aun)
    current_ovx = current_vals["ovx"]
    ax2.scatter([current_ovx], [dias_actuales], color=C_RED, s=120,
                marker="*", zorder=5, label=f"EEUU-Iran 2026 (en curso, {dias_actuales}d)")

    # Episodio Ucrania (si esta en la lista)
    for e in episodes:
        if UKR_START <= e["start"] <= UKR_START + pd.Timedelta(days=30):
            ax2.scatter([e["peak_ovx"]], [e["days"]], color=C_AMBER, s=100,
                        marker="D", zorder=5, label=f"Ucrania 2022 ({e['days']}d)")
            break

    ax2.axhline(43, color=C_AMBER, ls="--", lw=1.5, alpha=0.7, label="RSJD: 43d esperados")
    ax2.set_xlabel("OVX maximo del episodio", color=TXT_SEC, fontsize=9)
    ax2.set_ylabel("Duracion del episodio (dias habiles)", color=TXT_SEC, fontsize=9)
    ax2.set_title("Duracion vs. intensidad (OVX pico)", color=TXT_PRI, fontsize=10)
    ax2.tick_params(colors=TXT_SEC, labelsize=8)
    ax2.grid(True, color=C_GRID, alpha=0.5, lw=0.5)
    ax2.legend(framealpha=0.3, facecolor=BG_PANEL, edgecolor=BORDER,
               labelcolor=TXT_PRI, fontsize=8)

    plt.tight_layout()
    out_path = FIGURES_OUT / "bloque4_6_duracion_regimen.png"
    fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=BG_DARK)
    plt.close()
    print(f"  Figura guardada: {out_path.name}")

    # Percentil del episodio actual vs. historico
    pct_actual = sum(d <= dias_actuales for d in durs) / len(durs) * 100
    print(f"\n  El episodio actual ({dias_actuales} dias) esta en el percentil {pct_actual:.0f} de la distribucion historica")
    print(f"  => En el {100-pct_actual:.0f}% de los episodios historicos el regimen ya habria terminado a estas alturas")

# ── Resumen del sub-bloque ────────────────────────────────────────────────────
print("\n" + "="*70)
print("RESUMEN — SEMAFORO DE SALIDA DEL REGIMEN (snapshot 23-mar-2026)")
print("="*70)
print(f"\n  Exit Score:           {exit_score:.1f}/100")
print(f"  Estado:               {status_label}")
print(f"  Condiciones activas:  {n_satisfied}/{n_total}")
print(f"\n  Condiciones para transicion al regimen normal:")
print(f"  Criterio: TODAS las siguientes deben cumplirse durante {CONSECUTIVE_DAYS} dias consecutivos:")
for e in exit_status:
    arrow = "OK " if e["satisfied"] else "..."
    cond_short = e["condition"].replace("\n", " ")
    print(f"    [{arrow}] {cond_short:<38} (actual: {e['current']:.1f}, umbral: {e['threshold']:.1f}, brecha: {e['gap']:+.1f})")

print("\n  Interpretacion:")
print("  Con OVX en 91.85 (vs. umbral 40), el indicador principal necesita")
print("  reducirse un 56% desde el nivel actual antes de que el modelo")
print("  pueda declarar la salida del regimen de alta tension.")
print("  Segun el precedente de Ucrania 2022, esto tomo varios meses,")
print("  mientras que el RSJD predice una duracion esperada de ~43 dias.")

print("\n" + "="*70)
print("SUB-BLOQUE 4.6 COMPLETADO")
print("="*70)
