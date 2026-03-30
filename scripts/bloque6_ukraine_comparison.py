# -*- coding: utf-8 -*-
"""
Bloque 6 — Analisis Comparativo: Episodio Actual vs. Precedente Ucrania 2022
Parte 3 — Geopolitica y Crudo WTI: Inteligencia en Tiempo Real

Sub-bloques:
  6.1 - Trayectoria normalizada WTI, OVX y VIX: Ucrania 2022 vs. Guerra EEUU-Iran 2026
  6.2 - Trayectoria GPR: ambos episodios
  6.3 - Calibracion empirica del RSJD: duracion real del regimen en Ucrania
  6.4 - Tabla comparativa de caracteristicas de cada episodio
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

# Detectar la raiz del proyecto de forma robusta
from pathlib import Path
_cwd = Path.cwd()
if (_cwd / "data_clean").exists():
    ROOT = _cwd           # ejecutado desde la raiz
elif (_cwd.parent / "data_clean").exists():
    ROOT = _cwd.parent    # ejecutado desde notebooks/
else:
    ROOT = _cwd
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D
import warnings
from pathlib import Path
warnings.filterwarnings("ignore")

DATA_CLEAN  = ROOT / "data_clean"
DATA_OUT    = ROOT / "outputs" / "data"    / "parte3"
FIGURES_OUT = ROOT / "outputs" / "figures" / "parte3"
FIGURES_OUT.mkdir(parents=True, exist_ok=True)

# ── Paleta dark ──────────────────────────────────────────────────────────────
BG_DARK  = "#0d1117"
BG_PANEL = "#161b22"
BORDER   = "#30363d"
TXT_PRI  = "#e6edf3"
TXT_SEC  = "#8b949e"
C_UKR    = "#58a6ff"   # azul: Ucrania 2022
C_IRN    = "#f78166"   # naranja: Iran 2026 (datos reales)
C_PROJ   = "#d29922"   # dorado: proyeccion RSJD
C_GRID   = "#21262d"

# ── Fechas clave ─────────────────────────────────────────────────────────────
UKR_START  = pd.Timestamp("2022-02-24")   # invasion rusa de Ucrania
IRN_START  = pd.Timestamp("2026-02-27")   # inicio guerra EEUU-Iran
SNAP_DATE  = pd.Timestamp("2026-03-23")   # snapshot del proyecto

# Parametros RSJD (Parte 2) — regimen high_stress
RSJD_DRIFT_ANNUAL = 0.184    # +18.4% / anio
RSJD_VOL_ANNUAL   = 0.507    # 50.7% / anio
RSJD_PSTAY        = 0.977    # probabilidad de permanecer en regimen
RSJD_LAMBDA       = 3.2      # saltos / anio
TRADING_DAYS      = 252

print("=" * 70)
print("BLOQUE 6 — COMPARATIVA UCRANIA 2022 vs. GUERRA EEUU-IRAN 2026")
print("=" * 70)

# ── Carga de series historicas ────────────────────────────────────────────────
print("\nCargando series historicas...")

wti_h = pd.read_csv(DATA_CLEAN / "wti_usa_clean.csv",
                    parse_dates=["date"]).set_index("date")["wti_close"].dropna()
ovx_h = pd.read_csv(DATA_CLEAN / "ovx_clean.csv",
                    parse_dates=["date"]).set_index("date")["ovx_close"].dropna()
vix_h = pd.read_csv(DATA_CLEAN / "vix_clean.csv",
                    parse_dates=["date"]).set_index("date")["vix_close"].dropna()
dxy_h = pd.read_csv(DATA_CLEAN / "dxy_clean.csv",
                    parse_dates=["date"]).set_index("date")["dxy_close"].dropna()
brent_h = pd.read_csv(DATA_CLEAN / "brent_clean.csv",
                      parse_dates=["date"]).set_index("date")["brent_close"].dropna()

gpr_raw = pd.read_csv(DATA_CLEAN / "gpr_clean.csv", parse_dates=["date"])
gpr_raw["gpr_num"] = (
    gpr_raw["gpr"].astype(str)
    .str.replace(r"\.(?=\d{3}[,.])", "", regex=True)
    .str.replace(",", ".")
    .astype(float)
)
gpr_h = gpr_raw.set_index("date")["gpr_num"].dropna()

print(f"  WTI: {wti_h.index.min().date()} -> {wti_h.index.max().date()}")
print(f"  OVX: {ovx_h.index.min().date()} -> {ovx_h.index.max().date()}")
print(f"  GPR: {gpr_h.index.min().date()} -> {gpr_h.index.max().date()}")


# ── Funcion: extraer ventana relativa de N dias desde una fecha de inicio ─────
def extract_window(series, start_date, n_days=90):
    """
    Devuelve un DataFrame con columna 'value' indexado por dia_relativo (0, 1, 2, ...).
    Se busca el primer dia de negociacion >= start_date.
    """
    s = series[series.index >= start_date].dropna()
    if len(s) == 0:
        return pd.DataFrame()
    s = s.iloc[:n_days]
    df = pd.DataFrame({
        "date": s.index,
        "value": s.values,
        "day_rel": range(len(s))
    })
    return df


def normalize_to_100(df):
    """Normaliza 'value' a 100 en el dia 0."""
    base = df.loc[df["day_rel"] == 0, "value"].values
    if len(base) == 0:
        return df
    df = df.copy()
    df["value_norm"] = df["value"] / base[0] * 100
    return df


N_DAYS = 90   # ventana de comparacion en dias de negociacion

# ── Extraccion de ventanas ────────────────────────────────────────────────────
ukr_wti  = normalize_to_100(extract_window(wti_h,  UKR_START, N_DAYS))
irn_wti  = normalize_to_100(extract_window(wti_h,  IRN_START, N_DAYS))
ukr_ovx  = normalize_to_100(extract_window(ovx_h,  UKR_START, N_DAYS))
irn_ovx  = normalize_to_100(extract_window(ovx_h,  IRN_START, N_DAYS))
ukr_vix  = normalize_to_100(extract_window(vix_h,  UKR_START, N_DAYS))
irn_vix  = normalize_to_100(extract_window(vix_h,  IRN_START, N_DAYS))
ukr_gpr  = normalize_to_100(extract_window(gpr_h,  UKR_START, N_DAYS))
irn_gpr  = normalize_to_100(extract_window(gpr_h,  IRN_START, N_DAYS))

n_irn_actual = len(irn_wti)   # dias observados en el episodio actual
print(f"\n  Ucrania 2022: {len(ukr_wti)} dias observados")
print(f"  Iran 2026:    {n_irn_actual} dias observados (snapshot: dia {n_irn_actual - 1})")

# ── Proyeccion RSJD desde el ultimo dia observado ────────────────────────────
np.random.seed(42)

def rsjd_projection(last_value_norm, last_day, n_proj=90 - n_irn_actual + 1, n_paths=500):
    """
    Simula N_paths trayectorias RSJD desde last_value_norm.
    Devuelve media, P10 y P90 de cada paso.
    """
    dt = 1 / TRADING_DAYS
    drift  = (RSJD_DRIFT_ANNUAL - 0.5 * RSJD_VOL_ANNUAL**2) * dt
    vol_dt = RSJD_VOL_ANNUAL * np.sqrt(dt)
    lam_dt = RSJD_LAMBDA * dt

    paths = np.zeros((n_paths, n_proj + 1))
    paths[:, 0] = last_value_norm

    for t in range(1, n_proj + 1):
        z        = np.random.standard_normal(n_paths)
        n_jumps  = np.random.poisson(lam_dt, n_paths)
        jump_mag = np.where(n_jumps > 0, np.random.normal(-0.05, 0.08, n_paths) * n_jumps, 0)
        paths[:, t] = paths[:, t-1] * np.exp(drift + vol_dt * z + jump_mag)

    days = np.arange(last_day, last_day + n_proj + 1)
    return days, paths.mean(axis=0), np.percentile(paths, 10, axis=0), np.percentile(paths, 90, axis=0)

last_irn_wti = irn_wti["value_norm"].iloc[-1]
last_irn_day = int(irn_wti["day_rel"].iloc[-1])
proj_days, proj_mean, proj_p10, proj_p90 = rsjd_projection(last_irn_wti, last_irn_day)

print(f"\n  Proyeccion RSJD: {len(proj_days)} dias adicionales desde dia {last_irn_day}")
print(f"  WTI normalizado actual: {last_irn_wti:.1f}")
print(f"  Proyeccion media (dia {proj_days[-1]}): {proj_mean[-1]:.1f}")


# ════════════════════════════════════════════════════════════════════════════
# SUB-BLOQUE 6.1 — TRAYECTORIA NORMALIZADA WTI, OVX Y VIX
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("SUB-BLOQUE 6.1 — TRAYECTORIA NORMALIZADA WTI, OVX Y VIX")
print("="*70)

fig, axes = plt.subplots(3, 1, figsize=(14, 14), facecolor=BG_DARK)
fig.suptitle(
    "Trayectoria post-inicio de conflicto — Ucrania 2022 vs. EEUU-Iran 2026\n"
    "(base 100 = primer dia de negociacion tras el inicio del conflicto)",
    color=TXT_PRI, fontsize=13, fontweight="bold", y=0.98
)

datasets = [
    ("WTI (barril spot)",        ukr_wti,  irn_wti),
    ("OVX (volatilidad crudo)",  ukr_ovx,  irn_ovx),
    ("VIX (volatilidad S&P500)", ukr_vix,  irn_vix),
]

for ax, (title, ukr_df, irn_df) in zip(axes, datasets):
    ax.set_facecolor(BG_PANEL)
    for spine in ax.spines.values():
        spine.set_color(BORDER)

    # Ucrania 2022
    if not ukr_df.empty:
        ax.plot(ukr_df["day_rel"], ukr_df["value_norm"],
                color=C_UKR, lw=2.0, label="Ucrania 2022", zorder=3)
        ax.fill_between(ukr_df["day_rel"],
                        ukr_df["value_norm"] - 5, ukr_df["value_norm"] + 5,
                        alpha=0.08, color=C_UKR)

    # Iran 2026 - datos reales
    if not irn_df.empty:
        ax.plot(irn_df["day_rel"], irn_df["value_norm"],
                color=C_IRN, lw=2.5, label="EEUU-Iran 2026 (real)", zorder=4)

    # Proyeccion RSJD (solo para WTI)
    if "WTI" in title and len(proj_days) > 1:
        ax.fill_between(proj_days, proj_p10, proj_p90,
                        alpha=0.15, color=C_PROJ, label="IC 80% RSJD")
        ax.plot(proj_days, proj_mean,
                color=C_PROJ, lw=1.8, ls="--", label="Media RSJD", zorder=3)

    # Linea base 100
    ax.axhline(100, color=TXT_SEC, ls=":", lw=1, alpha=0.5)

    # Marcador del snapshot (dia 17 aprox)
    ax.axvline(last_irn_day, color=C_IRN, ls=":", lw=1.2, alpha=0.6)
    ax.text(last_irn_day + 0.8, ax.get_ylim()[0] if ax.get_ylim()[0] != 0 else 80,
            "Snapshot\n23-Mar", color=C_IRN, fontsize=7.5, va="bottom", alpha=0.8)

    ax.set_title(title, color=TXT_PRI, fontsize=11, pad=6)
    ax.set_xlabel("Dias de negociacion desde inicio del conflicto", color=TXT_SEC, fontsize=9)
    ax.set_ylabel("Indice (base 100)", color=TXT_SEC, fontsize=9)
    ax.tick_params(colors=TXT_SEC, labelsize=8)
    ax.grid(True, color=C_GRID, alpha=0.6, lw=0.5)
    ax.legend(loc="upper right", framealpha=0.3,
              facecolor=BG_PANEL, edgecolor=BORDER,
              labelcolor=TXT_PRI, fontsize=9)

    # Duracion esperada del regimen segun RSJD
    dur_expected = 1 / (1 - RSJD_PSTAY)
    ax.axvspan(0, dur_expected, alpha=0.04, color=C_PROJ,
               label=f"Duracion RSJD esperada (~{dur_expected:.0f}d)")

plt.tight_layout(rect=[0, 0, 1, 0.97])
out_path = FIGURES_OUT / "bloque6_trayectoria_normalizada.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=BG_DARK)
plt.close()
print(f"  Figura guardada: {out_path.name}")


# ════════════════════════════════════════════════════════════════════════════
# SUB-BLOQUE 6.2 — TRAYECTORIA GPR
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("SUB-BLOQUE 6.2 — TRAYECTORIA GPR: AMBOS EPISODIOS")
print("="*70)

fig, ax = plt.subplots(figsize=(14, 5), facecolor=BG_DARK)
ax.set_facecolor(BG_PANEL)
for spine in ax.spines.values():
    spine.set_color(BORDER)

if not ukr_gpr.empty:
    ax.plot(ukr_gpr["day_rel"], ukr_gpr["value_norm"],
            color=C_UKR, lw=2.0, label="GPR — Ucrania 2022")

if not irn_gpr.empty:
    ax.plot(irn_gpr["day_rel"], irn_gpr["value_norm"],
            color=C_IRN, lw=2.5, label="GPR — EEUU-Iran 2026 (real)")

ax.axhline(100, color=TXT_SEC, ls=":", lw=1, alpha=0.5)
ax.axvline(last_irn_day, color=C_IRN, ls=":", lw=1.2, alpha=0.6)

# Umbral critico del modelo GPR > 120 (normalizado)
gpr_ukr_base = gpr_h[gpr_h.index >= UKR_START].dropna().iloc[0] if not ukr_gpr.empty else 120
gpr_irn_base = gpr_h[gpr_h.index >= IRN_START].dropna().iloc[0] if not irn_gpr.empty else 120
umbral_norm_ukr = 120 / gpr_ukr_base * 100
umbral_norm_irn = 120 / gpr_irn_base * 100
ax.axhline(umbral_norm_ukr, color=C_UKR, ls="--", lw=1, alpha=0.5,
           label=f"Umbral GPR=120 (relativo Ucrania)")
ax.axhline(umbral_norm_irn, color=C_IRN, ls="--", lw=1, alpha=0.5,
           label=f"Umbral GPR=120 (relativo Iran)")

ax.set_title(
    "Indice de Riesgo Geopolitico (GPR) — Ucrania 2022 vs. EEUU-Iran 2026\n"
    "(base 100 = valor en dia de inicio del conflicto)",
    color=TXT_PRI, fontsize=12, fontweight="bold"
)
ax.set_xlabel("Dias de negociacion desde inicio del conflicto", color=TXT_SEC, fontsize=10)
ax.set_ylabel("GPR (base 100)", color=TXT_SEC, fontsize=10)
ax.tick_params(colors=TXT_SEC, labelsize=9)
ax.grid(True, color=C_GRID, alpha=0.6, lw=0.5)
ax.legend(framealpha=0.3, facecolor=BG_PANEL, edgecolor=BORDER,
          labelcolor=TXT_PRI, fontsize=9)

plt.tight_layout()
out_path = FIGURES_OUT / "bloque6_gpr_comparativa.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=BG_DARK)
plt.close()
print(f"  Figura guardada: {out_path.name}")


# ════════════════════════════════════════════════════════════════════════════
# SUB-BLOQUE 6.3 — CALIBRACION EMPIRICA RSJD: DURACION REAL EN UCRANIA
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("SUB-BLOQUE 6.3 — CALIBRACION EMPIRICA RSJD: DURACION REAL EN UCRANIA")
print("="*70)

# Definicion de "fin del regimen de alta tension" en Ucrania:
# OVX cae por debajo de 40 (umbral de alerta del modelo) durante 5 dias consecutivos
OVX_EXIT_THRESHOLD = 40.0
EXIT_CONSECUTIVE   = 5

ovx_ukr_window = ovx_h[ovx_h.index >= UKR_START].dropna().iloc[:N_DAYS]
ovx_below = ovx_ukr_window < OVX_EXIT_THRESHOLD

# Encontrar primera secuencia de EXIT_CONSECUTIVE dias consecutivos bajo umbral
exit_day = None
for i in range(len(ovx_below) - EXIT_CONSECUTIVE + 1):
    if ovx_below.iloc[i:i + EXIT_CONSECUTIVE].all():
        exit_day = i
        break

print(f"\n  OVX inicio Ucrania (dia 0): {ovx_ukr_window.iloc[0]:.1f}")
print(f"  OVX maximo en ventana:      {ovx_ukr_window.max():.1f}")
print(f"  Umbral de salida:           {OVX_EXIT_THRESHOLD}")

if exit_day is not None:
    print(f"  Dias hasta salida del regimen (Ucrania): {exit_day} dias de negociacion")
    dur_expected = 1 / (1 - RSJD_PSTAY)
    print(f"  Duracion esperada RSJD (p_stay=0.977):  {dur_expected:.1f} dias")
    error_dias = exit_day - dur_expected
    print(f"  Diferencia RSJD vs. real:               {error_dias:+.1f} dias")
else:
    exit_day = len(ovx_ukr_window)
    print(f"  Regimen NO sali de alta tension en los {N_DAYS} dias de la ventana Ucrania")

# Figura: OVX Ucrania con marcadores de umbral y salida
fig, ax = plt.subplots(figsize=(14, 5), facecolor=BG_DARK)
ax.set_facecolor(BG_PANEL)
for spine in ax.spines.values():
    spine.set_color(BORDER)

days_ukr = np.arange(len(ovx_ukr_window))
ax.plot(days_ukr, ovx_ukr_window.values,
        color=C_UKR, lw=2.0, label="OVX — Ucrania 2022")

# Linea umbral de salida
ax.axhline(OVX_EXIT_THRESHOLD, color="#3fb950", ls="--", lw=1.5, alpha=0.8,
           label=f"Umbral salida OVX={OVX_EXIT_THRESHOLD}")

# Duracion esperada RSJD
dur_expected = 1 / (1 - RSJD_PSTAY)
ax.axvline(dur_expected, color=C_PROJ, ls="--", lw=1.5, alpha=0.8,
           label=f"Duracion RSJD esperada (~{dur_expected:.0f} dias)")

# Dia real de salida
if exit_day is not None and exit_day < N_DAYS:
    ax.axvline(exit_day, color="#3fb950", ls="-", lw=1.5, alpha=0.8,
               label=f"Salida real (dia {exit_day})")

# Zona sombreada de alto estres
ax.fill_between(days_ukr, OVX_EXIT_THRESHOLD, ovx_ukr_window.values,
                where=ovx_ukr_window.values > OVX_EXIT_THRESHOLD,
                alpha=0.15, color=C_UKR)

# OVX actual (Iran)
ax.axhline(ovx_h.iloc[-1], color=C_IRN, ls=":", lw=1.5,
           label=f"OVX actual Iran 2026 ({ovx_h.iloc[-1]:.1f})")

ax.set_title(
    "OVX post-inicio de conflicto — Ucrania 2022\n"
    "Calibracion empirica de la duracion del regimen de alta tension (RSJD p_stay=0.977)",
    color=TXT_PRI, fontsize=12, fontweight="bold"
)
ax.set_xlabel("Dias de negociacion desde inicio del conflicto", color=TXT_SEC, fontsize=10)
ax.set_ylabel("OVX", color=TXT_SEC, fontsize=10)
ax.tick_params(colors=TXT_SEC, labelsize=9)
ax.grid(True, color=C_GRID, alpha=0.6, lw=0.5)
ax.legend(framealpha=0.3, facecolor=BG_PANEL, edgecolor=BORDER,
          labelcolor=TXT_PRI, fontsize=9)

plt.tight_layout()
out_path = FIGURES_OUT / "bloque6_rsjd_calibracion.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=BG_DARK)
plt.close()
print(f"  Figura guardada: {out_path.name}")


# ════════════════════════════════════════════════════════════════════════════
# SUB-BLOQUE 6.4 — TABLA COMPARATIVA DE CARACTERISTICAS
# ════════════════════════════════════════════════════════════════════════════
print("\n" + "="*70)
print("SUB-BLOQUE 6.4 — TABLA COMPARATIVA EPISODIOS")
print("="*70)

# Valores Ucrania en dia 0 y maximo en los 90 dias
wti_ukr_d0  = wti_h[wti_h.index >= UKR_START].dropna().iloc[0]
wti_ukr_max = wti_h[wti_h.index >= UKR_START].dropna().iloc[:N_DAYS].max()
ovx_ukr_d0  = ovx_h[ovx_h.index >= UKR_START].dropna().iloc[0]
ovx_ukr_max = ovx_h[ovx_h.index >= UKR_START].dropna().iloc[:N_DAYS].max()
gpr_ukr_d0  = gpr_h[gpr_h.index >= UKR_START].dropna().iloc[0]
gpr_ukr_max = gpr_h[gpr_h.index >= UKR_START].dropna().iloc[:N_DAYS].max()

# Valores Iran en dia 0 y maximo observado
wti_irn_d0  = wti_h[wti_h.index >= IRN_START].dropna().iloc[0]
wti_irn_max = wti_h[wti_h.index >= IRN_START].dropna().dropna().max()
ovx_irn_d0  = ovx_h[ovx_h.index >= IRN_START].dropna().iloc[0]
ovx_irn_max = ovx_h[ovx_h.index >= IRN_START].dropna().max()
gpr_irn_d0  = gpr_h[gpr_h.index >= IRN_START].dropna().iloc[0]
gpr_irn_max = gpr_h[gpr_h.index >= IRN_START].dropna().max()

rows = [
    ("Fecha inicio",               "24-feb-2022",                 "27-feb-2026"),
    ("Tipo de conflicto",          "Invasion terrestre (Ucrania)", "Guerra aeronaval (Ormuz bloqueado)"),
    ("WTI dia 0 (USD/barril)",     f"{wti_ukr_d0:.2f}",           f"{wti_irn_d0:.2f}"),
    ("WTI maximo en ventana",      f"{wti_ukr_max:.2f}",          f"{wti_irn_max:.2f}"),
    ("WTI var. max. vs dia 0",     f"+{(wti_ukr_max/wti_ukr_d0-1)*100:.1f}%",
                                   f"+{(wti_irn_max/wti_irn_d0-1)*100:.1f}%"),
    ("OVX dia 0",                  f"{ovx_ukr_d0:.1f}",           f"{ovx_irn_d0:.1f}"),
    ("OVX maximo en ventana",      f"{ovx_ukr_max:.1f}",          f"{ovx_irn_max:.1f}"),
    ("GPR dia 0",                  f"{gpr_ukr_d0:.1f}",           f"{gpr_irn_d0:.1f}"),
    ("GPR maximo en ventana",      f"{gpr_ukr_max:.1f}",          f"{gpr_irn_max:.1f}"),
    ("Percentil GPR historico",    f"~P{(gpr_h <= gpr_ukr_max).mean()*100:.0f}",
                                   f"~P{(gpr_h <= gpr_irn_max).mean()*100:.0f}"),
    ("Dias hasta salida OVX<40",   f"{exit_day if exit_day < N_DAYS else '>90'}",
                                   "N/A (en curso)"),
    ("Dur. esperada RSJD (p=0.977)", f"~43 dias",                 f"~43 dias"),
    ("Estrecho de Ormuz afectado", "No",                           "Si — bloqueado"),
    ("Implicacion en modelo",      "In-domain (parcial)",          "Out-of-domain (extremo)"),
]

col_w = [34, 30, 30]
header = f"{'Dimension':<{col_w[0]}} {'Ucrania 2022':^{col_w[1]}} {'EEUU-Iran 2026':^{col_w[2]}}"
sep = "-" * sum(col_w)
print(f"\n{header}")
print(sep)
for dim, val_ukr, val_irn in rows:
    print(f"{dim:<{col_w[0]}} {val_ukr:^{col_w[1]}} {val_irn:^{col_w[2]}}")

# Figura: tabla comparativa visual
fig, ax = plt.subplots(figsize=(14, 7), facecolor=BG_DARK)
ax.set_facecolor(BG_DARK)
ax.axis("off")

col_labels = ["Dimension", "Ucrania 2022", "EEUU-Iran 2026"]
cell_colors = []
for i, (dim, v1, v2) in enumerate(rows):
    row_bg = BG_PANEL if i % 2 == 0 else "#1c2128"
    cell_colors.append([row_bg, row_bg, row_bg])

table = ax.table(
    cellText=rows,
    colLabels=col_labels,
    cellLoc="left",
    loc="center",
    cellColours=cell_colors,
)
table.auto_set_font_size(False)
table.set_fontsize(9)
table.scale(1, 1.45)

for (row, col), cell in table.get_celld().items():
    cell.set_edgecolor(BORDER)
    cell.set_text_props(color=TXT_PRI if row > 0 else "#58a6ff")
    if row == 0:
        cell.set_facecolor("#1f2937")
        cell.set_text_props(color=TXT_PRI, fontweight="bold")

ax.set_title(
    "Tabla comparativa — Episodios de conflicto con impacto en crudo WTI",
    color=TXT_PRI, fontsize=12, fontweight="bold", pad=15
)

plt.tight_layout()
out_path = FIGURES_OUT / "bloque6_tabla_comparativa.png"
fig.savefig(out_path, dpi=150, bbox_inches="tight", facecolor=BG_DARK)
plt.close()
print(f"\n  Figura guardada: {out_path.name}")

print("\n" + "="*70)
print("BLOQUE 6 COMPLETADO")
print("="*70)
