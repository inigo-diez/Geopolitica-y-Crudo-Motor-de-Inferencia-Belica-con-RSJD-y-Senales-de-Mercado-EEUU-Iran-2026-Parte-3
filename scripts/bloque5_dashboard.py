# -*- coding: utf-8 -*-
"""
Bloque 5 - Intelligence Brief y Dashboard
Parte 3 - Geopolitica y Crudo WTI: Inteligencia en Tiempo Real
Snapshot: 23 de marzo de 2026

Sub-bloques:
  5.1 - Intelligence Brief (Markdown + PNG)
  5.2 - Dashboard HTML interactivo autocontenido
"""

import sys, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

import json
import re
import textwrap
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
import warnings
warnings.filterwarnings("ignore")

ROOT        = Path(".")
DATA_OUT    = ROOT / "outputs" / "data"    / "parte3"
FIGURES_OUT = ROOT / "outputs" / "figures" / "parte3"
DASHBOARD   = ROOT / "dashboard"
DASH_DATA   = ROOT / "dashboard" / "data"

DASH_DATA.mkdir(parents=True, exist_ok=True)
FIGURES_OUT.mkdir(parents=True, exist_ok=True)

BRIEF_DATE   = "23 marzo 2026"
EVENT_TIME   = "11:05 UTC (07:05 ET)"
EVENT_LABEL  = "Trump publica en Truth Social sobre 'conversaciones productivas' con Iran"

CONVICTION_ORDER = {"descontado": 0, "muy_probable": 1, "probable": 2, "cola": 3}

# ─── CARGA DE DATOS ─────────────────────────────────────────────────────────
print("Cargando datos de bloques anteriores...")

# Market snapshot (dict of dicts)
with open(DATA_OUT / "market_snapshot_20260323.json", encoding="utf-8") as f:
    snap_json = json.load(f)
SNAP_ASSETS  = snap_json["assets"]          # {"wti": {...}, "brent": {...}, ...}
SNAP_META    = snap_json.get("metadata", {})

def get_asset(key: str) -> Dict:
    return SNAP_ASSETS.get(key, {})

# Polymarket (yes_prob is 0-100 scale)
poly_df = pd.read_parquet(DATA_OUT / "polymarket_clean.parquet")
poly_df["yes_prob_pct"] = poly_df["yes_prob"]  # already 0-100

# Inference table
inf_df = pd.read_parquet(DATA_OUT / "inference_table.parquet")
# yes_prob in inference table is also 0-100 (stored as-is from polymarket)
inf_df["yes_prob_pct"] = inf_df["yes_prob"]
inf_records = inf_df.to_dict(orient="records")

# Contagion channels
with open(DATA_OUT / "contagion_channels.json", encoding="utf-8") as f:
    contagion_raw = json.load(f)

# Profile 4.1
with open(DATA_OUT / "profile_41.json", encoding="utf-8") as f:
    profile = json.load(f)

print(f"  Activos snapshot  : {len(SNAP_ASSETS)}")
print(f"  Seniales Polymarket: {len(poly_df)}")
print(f"  Escenarios inferidos: {len(inf_df)}")
print(f"  Canales contagio  : {len(contagion_raw)}")

# ─── HELPERS ────────────────────────────────────────────────────────────────
def fmt_money(v, digits=0, prefix="$"):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/d"
    return f"{prefix}{float(v):,.{digits}f}"

def fmt_pct(v, digits=1, signed=False):
    if v is None or (isinstance(v, float) and math.isnan(v)):
        return "n/d"
    fmt = f"{{:{'+' if signed else ''}.{digits}f}}%"
    return fmt.format(float(v))

def summarize_tier(tier: str, max_items: int = 3) -> str:
    rows = poly_df[poly_df["conviction_tier"] == tier].nlargest(max_items, "signal_quality_score")
    if rows.empty:
        return "sin mercados relevantes"
    parts = []
    for _, r in rows.iterrows():
        parts.append(f"{r['question']} ({fmt_pct(r['yes_prob_pct'])})")
    return "; ".join(parts)

def traffic_light(row: Dict) -> str:
    alignment = str(row.get("model_alignment", "")).lower()
    in_domain = row.get("in_model_domain", True)
    if not in_domain:
        return "rojo"
    if alignment == "aligned":
        return "verde"
    if alignment in ("partially_aligned", "divergent"):
        return "amarillo"
    return "gris"

# Add traffic light to inference records
for r in inf_records:
    r["traffic_light"] = traffic_light(r)

def find_inference(question: str) -> Optional[Dict]:
    q_lower = question.lower()
    # Try exact match on question_polymarket
    for r in inf_records:
        if str(r.get("question_polymarket", "")).lower() == q_lower:
            return r
    # Try partial match on scenario_name
    for r in inf_records:
        sn = str(r.get("scenario_name", "")).lower()
        if sn[:30] in q_lower or q_lower[:30] in sn:
            return r
    return None

# ─── SUMMARY CARDS ──────────────────────────────────────────────────────────
stress_level    = profile.get("stress_level", "ESTRES EXTREMO")
dims_active     = profile.get("dimensions_active", 6)
dims_total      = profile.get("dimensions_total", 8)
stress_match    = f"{dims_active} de {dims_total} dimensiones activas -> {stress_level}"

green_scenarios  = [r["scenario_name"] for r in inf_records if r["traffic_light"] == "verde"]
red_scenarios    = [r["scenario_name"] for r in inf_records if r["traffic_light"] == "rojo"]
yellow_scenarios = [r["scenario_name"] for r in inf_records if r["traffic_light"] == "amarillo"]

top_divergence_row = next(
    (r for r in sorted(inf_records, key=lambda x: x["inference_confidence_score"], reverse=True)
     if r["model_alignment"] in ("partially_aligned", "divergent")), None
)
main_divergence = (
    f"{top_divergence_row['scenario_name']}: modelo sugiere {top_divergence_row['model_conclusion_view'][:80]}..."
    if top_divergence_row else "No se detectan divergencias criticas adicionales."
)

wti = get_asset("wti")
ovx = get_asset("ovx")
main_takeaway = (
    f"WTI en {fmt_money(wti.get('current_value'), 0)} y OVX en {fmt_pct(ovx.get('current_value'))} "
    f"situan el episodio en zona de estres extremo, pero con una reversion intradiaria "
    f"dominada por el canal politico (swing {fmt_pct(wti.get('intra_swing_pct'), 1, signed=False)} intradiario)."
)

summary_cards = {
    "historical_stress_match"      : stress_match,
    "top_validated_scenarios"      : green_scenarios[:3],
    "top_out_of_domain_scenarios"  : red_scenarios[:3],
    "main_divergence"              : main_divergence,
    "main_takeaway"                : main_takeaway,
}

print("\nSummary cards generadas:")
for k, v in summary_cards.items():
    v_str = str(v)[:90]
    print(f"  {k}: {v_str}")

# ─── 5.1 INTELLIGENCE BRIEF ─────────────────────────────────────────────────
print("\nGenerando Intelligence Brief...")

def bullet_dictamen(records: List[Dict], max_items: int = 6) -> str:
    if not records:
        return "- Sin escenarios destacados"
    lines = []
    for r in records[:max_items]:
        sn   = r.get("scenario_name", "Escenario")
        hist = (r.get("historical_dataset_view") or "sin lectura historica")[:100]
        mod  = (r.get("model_conclusion_view")   or "sin lectura del modelo")[:100]
        tl   = r.get("traffic_light", "gris")
        prob = fmt_pct(r.get("yes_prob_pct"))
        conf = r.get("confidence_label", "n/d")
        lines.append(f"  [{tl.upper()}] **{sn}** (Poly: {prob}, Conf: {conf})")
        lines.append(f"    Historico: {hist}")
        lines.append(f"    Modelo   : {mod}")
    return "\n".join(lines)

contagion_md_lines = [
    "| Canal | Cadena | Modelado | Observado hoy | Divergencia |",
    "|-------|--------|----------|---------------|-------------|",
]
for ch in contagion_raw:
    canal    = ch.get("canal", "")
    cadena   = ch.get("cadena", "")[:60]
    modelado = "SI" if ch.get("in_domain", False) else "NO"
    obs      = (ch.get("comportamiento_real") or ch.get("real_today", ""))[:60]
    div      = (ch.get("divergencia", ""))[:70]
    contagion_md_lines.append(f"| {canal} | {cadena} | {modelado} | {obs} | {div} |")
contagion_md = "\n".join(contagion_md_lines)

brief_md = f"""# INTELLIGENCE BRIEF - Crudo, Geopolitica y Mercados Financieros

**Fecha:** {BRIEF_DATE}
**Fuentes:** Polymarket API + Modelo GPR->WTI (Partes 1+2) + Datos intradiarios
**Evento ancla:** {EVENT_TIME} - {EVENT_LABEL}

---

## SITUACION ACTUAL

- **WTI**: Abrio {fmt_money(wti.get('intra_open'), 0)}, minimo {fmt_money(wti.get('intra_low'), 0)} ({fmt_pct(wti.get('intra_swing_pct'), 1, signed=True)} intradiario), cierre {fmt_money(wti.get('intra_close'), 0)}
- **Evento ancla**: Trump anuncia pausa de 5 dias en ataques y "conversaciones productivas" con Iran
- **Iran desmiente** cualquier contacto. Incertidumbre maxima.
- **Perfil actual**: {stress_match}
- **GPR actual**: {fmt_pct(profile.get('gpr_current'), 1)} (P{profile.get('gpr_percentile', 98)}th historico, umbral modelo: 120)
- **OVX actual**: {fmt_pct(ovx.get('current_value'), 1)} (P{profile.get('ovx_percentile', 99)}th historico, umbral modelo: 40)

---

## SENIALES POLYMARKET POR ACTIVO Y CONVICCION

- **[descontado >90%]**    -> {summarize_tier('descontado')}
- **[muy probable 75-90%]** -> {summarize_tier('muy_probable')}
- **[probable 60-75%]**    -> {summarize_tier('probable')}
- **[cola <60%]**          -> {summarize_tier('cola')}

---

## INFERENCIAS DEL MODELO - CRUDO

**Escenarios dentro del dominio:**
{bullet_dictamen([r for r in inf_records if r.get('in_model_domain') and r.get('asset', '').lower() in ('wti', 'brent', 'oil', 'hormuz')])}

**Escenarios fuera del dominio:**
{bullet_dictamen([r for r in inf_records if not r.get('in_model_domain')])}

---

## INFERENCIAS DEL MODELO - ACTIVOS FINANCIEROS

{bullet_dictamen([r for r in inf_records if r.get('in_model_domain') and r.get('asset', '').lower() not in ('wti', 'brent', 'oil', 'hormuz')])}

---

## DICTAMEN DE LAS PARTES 1 Y 2 SOBRE LAS APUESTAS

*Parte 1 construyo un clasificador RandomForest (AUC=0.615, recall=0.918) entrenado sobre 15 variables macro para predecir regimenes de alta volatilidad en el crudo. Parte 2 calibro un modelo RSJD (Regime-Switching Jump-Diffusion) que estima la dinamica de precio en regimenes de estres (drift=+18.4%, vol=50.7%). El dictamen clasifica cada apuesta segun el respaldo empirico e inferencial de ambos modelos.*

### Verde - Validado por historico y modelo
{bullet_dictamen([r for r in inf_records if r['traffic_light'] == 'verde'])}

### Amarillo - Señal parcial / mixta
{bullet_dictamen([r for r in inf_records if r['traffic_light'] == 'amarillo'])}

### Rojo - Fuera de dominio / no respaldado
{bullet_dictamen([r for r in inf_records if r['traffic_light'] == 'rojo'])}

---

## DIVERGENCIAS CLAVE

- **Lo que Polymarket prica que el modelo no puede validar**: {', '.join(red_scenarios[:3]) or 'No detectado'}
- **Lo que el modelo sugiere que Polymarket no descuenta**: {main_divergence}
- **El factor Trump**: Variable exogena no modelable que movio WTI {fmt_pct(wti.get('intra_swing_pct'), 1, signed=True)} en menos de 60 minutos. Ningun modelo basado en series temporales puede capturar el riesgo de declaracion de un actor politico unico en tiempo real.

---

## TABLA DE CONTAGIO SISTEMICO

{contagion_md}

---

## CONCLUSION

El episodio del 23 de marzo de 2026 combina un shock energetico estructural (guerra EEUU-Iran, Estrecho de Ormuz bloqueado, WTI +44% YTD) con un canal politico intradiario que reescribe el precio en tiempo real. El historico empirico y los modelos de las Partes 1 y 2 siguen siendo utiles para ordenar escenarios y discriminar que apuestas estan respaldadas por precedentes, pero no sustituyen el juicio cuando aparecen variables exogenas de alta velocidad como un post en Truth Social.

Este brief no es una prediccion: es una lectura argumentada del momento mas inestable del mercado del crudo en decadas, separando cuidadosamente senal historica, lectura del modelo y ruido politico.
"""

brief_md_path = DATA_OUT / "intelligence_brief.md"
brief_md_path.write_text(brief_md, encoding="utf-8")
print(f"  Brief MD guardado: {brief_md_path}")

# ─── BRIEF PNG ──────────────────────────────────────────────────────────────
print("  Generando intelligence_brief.png...")

def render_brief_png(text: str, output_path: Path) -> None:
    lines_raw = text.splitlines()
    wrapped = []
    for raw in lines_raw:
        stripped = raw.rstrip()
        if stripped.startswith("# ") or stripped.startswith("## "):
            wrapped.append(stripped)
            wrapped.append("")
            continue
        chunks = textwrap.wrap(stripped, width=115) if stripped else [""]
        wrapped.extend(chunks)

    n = max(len(wrapped), 40)
    height = max(18, n * 0.26)
    fig = plt.figure(figsize=(15, height), dpi=130)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_axis_off()
    ax.add_patch(Rectangle((0, 0), 1, 1, transform=ax.transAxes, color="#0d1117"))

    y = 0.99
    step = 0.95 / max(n, 1)
    for line in wrapped:
        color, size, weight = "#e6edf3", 10.5, "normal"
        if line.startswith("# "):
            line, color, size, weight = line[2:], "#ffffff", 18, "bold"
        elif line.startswith("## "):
            line, color, size, weight = line[3:], "#79c0ff", 13, "bold"
        elif line.startswith("### "):
            line, color, size, weight = line[4:], "#56d364", 11.5, "bold"
        elif line.startswith("- **[VERDE]"):
            color = "#56d364"
        elif line.startswith("- **[AMARILLO]"):
            color = "#e3b341"
        elif line.startswith("- **[ROJO]"):
            color = "#f85149"
        elif line.startswith("  Historico:") or line.startswith("  Modelo   :"):
            color, size = "#8b949e", 9.5
        ax.text(0.025, y, line, va="top", ha="left", family="DejaVu Sans",
                fontsize=size, color=color, fontweight=weight)
        y -= step
        if y < 0.01:
            break

    fig.savefig(output_path, bbox_inches="tight", facecolor="#0d1117", dpi=130)
    plt.close(fig)

render_brief_png(brief_md, FIGURES_OUT / "intelligence_brief.png")
print(f"  Brief PNG guardado: {FIGURES_OUT / 'intelligence_brief.png'}")

# ─── BUILD latest.json ──────────────────────────────────────────────────────
print("\nConstruyendo latest.json...")

def serialize(obj):
    if isinstance(obj, float) and math.isnan(obj):
        return None
    if isinstance(obj, (bool, int, float, str, type(None))):
        return obj
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [serialize(x) for x in obj]
    return str(obj)

# Normalize polymarket for JS (trim to top 200 by signal_quality_score)
poly_top = (
    poly_df.sort_values("signal_quality_score", ascending=False)
    .head(200)
    .where(pd.notnull(poly_df.sort_values("signal_quality_score", ascending=False).head(200)), None)
    .to_dict(orient="records")
)

# Normalize inference records for JS
inf_js = []
for r in inf_records:
    inf_js.append({
        "scenario"                : r.get("scenario_name"),
        "asset"                   : r.get("asset"),
        "category_project"        : r.get("category"),
        "yes_prob"                : r.get("yes_prob_pct"),
        "conviction_tier"         : r.get("conviction_tier"),
        "days_to_close"           : r.get("days_to_close"),
        "in_model_domain"         : r.get("in_model_domain"),
        "historical_dataset_view" : r.get("historical_dataset_view"),
        "model_conclusion_view"   : r.get("model_conclusion_view"),
        "if_yes_implication"      : r.get("if_yes_historical"),
        "if_no_implication"       : r.get("if_no_historical"),
        "precedent"               : r.get("precedent"),
        "precedent_strength"      : r.get("precedent_strength"),
        "confidence_label"        : r.get("confidence_label"),
        "confidence_score"        : r.get("inference_confidence_score"),
        "model_alignment"         : r.get("model_alignment"),
        "real_today"              : r.get("real_today"),
        "expected_market_path"    : r.get("expected_market_path"),
        "traffic_light"           : r.get("traffic_light"),
    })

# Normalize contagion for JS
contagion_js = []
for ch in contagion_raw:
    contagion_js.append({
        "canal"      : ch.get("canal", ""),
        "cadena"     : ch.get("cadena", ""),
        "modelado"   : "SI" if ch.get("in_domain", False) else "NO",
        "observado"  : ch.get("comportamiento_real", ch.get("real_today", "")),
        "divergencia": ch.get("divergencia", ""),
    })

# Normalize assets for JS
assets_js = {}
for key, asset in SNAP_ASSETS.items():
    assets_js[key] = {
        "asset"                  : key.upper(),
        "ticker"                 : asset.get("ticker"),
        "current_value"          : asset.get("current_value") or asset.get("intra_close"),
        "ytd_return"             : asset.get("ytd_return_pct"),
        "historical_percentile"  : asset.get("pct_hist"),
        "open"                   : asset.get("intra_open"),
        "high"                   : asset.get("intra_high"),
        "low"                    : asset.get("intra_low"),
        "provisional_close"      : asset.get("intra_close"),
        "max_intraday_move_pct"  : asset.get("intra_swing_pct"),
        "time_of_low"            : asset.get("intra_t_low_utc"),
        "stress_label"           : asset.get("stress_label"),
    }

latest_json = serialize({
    "metadata": {
        "generated_at_utc"   : datetime.now(timezone.utc).isoformat(),
        "brief_date"         : BRIEF_DATE,
        "anchor_event_time"  : EVENT_TIME,
        "anchor_event_label" : EVENT_LABEL,
        "stress_match"       : stress_match,
        "shock_regime"       : SNAP_META.get("shock_regime_today", "mixed_regime"),
    },
    "market_snapshot": {
        "assets" : list(assets_js.values()),
        "meta"   : SNAP_META,
    },
    "polymarket_signals": {
        "total"      : len(poly_df),
        "shown"      : len(poly_top),
        "signals"    : poly_top,
    },
    "scenario_inference": {
        "records"         : inf_js,
        "contagion_table" : contagion_js,
    },
    "brief_summary_cards" : summary_cards,
    "intelligence_brief"  : {
        "markdown": brief_md,
    },
})

with open(DASH_DATA / "latest.json", "w", encoding="utf-8") as f:
    json.dump(latest_json, f, ensure_ascii=False, indent=2)
print(f"  latest.json guardado: {DASH_DATA / 'latest.json'}")

# ─── 5.2 DASHBOARD HTML ──────────────────────────────────────────────────────
print("\nGenerando dashboard/index.html...")

# ensure_ascii=True: convierte →↑≥ etc. a \uXXXX para embedding seguro en HTML
initial_json_str = json.dumps(latest_json, ensure_ascii=True)

html = """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Dashboard Geopolitica y Crudo WTI - 23 marzo 2026</title>
  <style>
    :root {
      --bg: #0d1117; --panel: #161b22; --panel2: #1c2333;
      --muted: #8b949e; --text: #e6edf3; --border: #30363d;
      --green: #1a7f37; --green2: #56d364; --yellow: #9e6a03; --yellow2: #e3b341;
      --red: #b42318; --red2: #f85149; --blue: #1f6feb; --blue2: #79c0ff;
      --gray: #484f58; --gray2: #8b949e;
      --radius: 14px; --shadow: 0 8px 32px rgba(0,0,0,.4);
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { background: var(--bg); color: var(--text);
           font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif; }
    .page { padding: 16px; }
    /* TOP BAR */
    .topbar { display:flex; justify-content:space-between; align-items:center;
              gap:12px; margin-bottom:16px; flex-wrap:wrap; }
    .title h1 { font-size:22px; font-weight:700; }
    .title p { font-size:13px; color:var(--muted); margin-top:4px; }
    .actions { display:flex; gap:10px; align-items:center; flex-wrap:wrap; }
    .badge { background:var(--panel2); border:1px solid var(--border); border-radius:999px;
             padding:6px 12px; font-size:12px; color:var(--muted); }
    button { background:var(--blue); color:white; border:none; border-radius:10px;
             padding:8px 14px; font-size:13px; font-weight:600; cursor:pointer; }
    button:hover { filter:brightness(1.1); }
    /* SUMMARY CARDS */
    .cards-grid { display:grid; grid-template-columns:repeat(5,minmax(0,1fr));
                  gap:10px; margin-bottom:16px; }
    .card { background:var(--panel); border:1px solid var(--border);
            border-radius:var(--radius); padding:12px; box-shadow:var(--shadow); }
    .card .k { font-size:11px; color:var(--muted); text-transform:uppercase;
               letter-spacing:.05em; }
    .card .v { font-size:13px; font-weight:600; margin-top:6px; line-height:1.45; }
    /* LAYOUT */
    .layout { display:grid; grid-template-columns:1fr 1.3fr 1.1fr; gap:14px; align-items:start; }
    .panel { background:var(--panel); border:1px solid var(--border);
             border-radius:var(--radius); padding:14px; box-shadow:var(--shadow); }
    .panel h2 { font-size:16px; font-weight:700; margin-bottom:12px; }
    /* MARKET PANEL */
    .asset-big { border:1px solid var(--border); border-radius:12px; padding:12px;
                 margin-bottom:10px; background:var(--panel2); }
    .asset-row { display:flex; justify-content:space-between; align-items:center; }
    .asset-name { font-size:18px; font-weight:800; }
    .asset-tag { font-size:11px; color:var(--muted); margin-top:3px; }
    .asset-price { text-align:right; }
    .asset-price .big { font-size:20px; font-weight:800; }
    .asset-price .sm { font-size:12px; color:var(--muted); margin-top:3px; }
    .pbar { width:100%; height:8px; background:#21262d; border-radius:999px; overflow:hidden;
            margin-top:10px; border:1px solid var(--border); }
    .pbar-fill { height:100%; background:linear-gradient(90deg,var(--blue),var(--blue2)); }
    .compact-grid { display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:8px; margin-top:10px; }
    .compact { border:1px solid var(--border); border-radius:10px; padding:9px;
               background:var(--panel2); }
    .compact .cn { font-weight:700; font-size:13px; }
    .compact .cv { font-size:14px; font-weight:700; margin-top:3px; }
    .compact .cm { font-size:11px; color:var(--muted); margin-top:2px; }
    .event-note { font-size:11px; color:var(--muted); margin-top:10px; padding:8px;
                  border:1px solid var(--border); border-radius:8px; }
    /* SIGNALS PANEL */
    .filters { display:flex; flex-wrap:wrap; gap:6px; margin-bottom:10px; }
    .chip { padding:5px 10px; border-radius:999px; border:1px solid var(--border);
            background:var(--panel2); color:var(--text); cursor:pointer; font-size:11px; }
    .chip.active { border-color:var(--blue2); background:#0d2844; color:var(--blue2); }
    .signals-scroll { max-height:72vh; overflow-y:auto; padding-right:4px; }
    .signals-scroll::-webkit-scrollbar { width:4px; }
    .signals-scroll::-webkit-scrollbar-thumb { background:var(--border); border-radius:2px; }
    .sig-card { border:1px solid var(--border); border-radius:12px; margin-bottom:8px;
                overflow:hidden; background:var(--panel2); }
    .sig-head { padding:10px 12px; cursor:pointer; }
    .sig-head:hover { background:rgba(255,255,255,.03); }
    .sig-title { font-weight:600; font-size:13px; line-height:1.4; }
    .sig-meta { display:flex; flex-wrap:wrap; gap:8px; margin-top:6px;
                font-size:11px; color:var(--muted); }
    .prob-bar { width:100%; height:8px; background:#21262d; border-radius:999px;
                overflow:hidden; margin-top:8px; }
    .prob-fill { height:100%; border-radius:999px; }
    .t-descontado { background:var(--green); }
    .t-muy_probable { background:var(--green2); }
    .t-probable { background:var(--yellow2); }
    .t-cola { background:var(--red); }
    .sig-body { display:none; padding:0 12px 12px; border-top:1px solid var(--border); }
    .sig-body.open { display:block; }
    .dl { margin-top:8px; font-size:12px; line-height:1.6; }
    .dl .lbl { font-size:10px; color:var(--muted); text-transform:uppercase;
               letter-spacing:.05em; display:block; margin-top:6px; }
    .tl-dot { width:9px; height:9px; border-radius:999px; display:inline-block; margin-right:5px; }
    /* BRIEF PANEL */
    .brief-scroll { max-height:50vh; overflow-y:auto; padding-right:4px; }
    .brief-scroll::-webkit-scrollbar { width:4px; }
    .brief-scroll::-webkit-scrollbar-thumb { background:var(--border); border-radius:2px; }
    .brief-text { font-size:12px; line-height:1.65; }
    .brief-text h1 { font-size:15px; color:white; margin:8px 0 4px; }
    .brief-text h2 { font-size:13px; color:var(--blue2); margin:10px 0 4px; }
    .brief-text h3 { font-size:12px; color:var(--green2); margin:6px 0 2px; }
    .brief-table { width:100%; border-collapse:collapse; font-size:11px; margin:8px 0 10px; }
    .brief-table th { background:#0d1117; color:var(--muted); font-size:10px; text-transform:uppercase;
                      letter-spacing:.04em; padding:7px 8px; border:1px solid var(--border); text-align:left; }
    .brief-table td { padding:6px 8px; border:1px solid var(--border); vertical-align:top;
                      word-break:break-word; max-width:200px; }
    .contagion-wrap { margin-top:14px; }
    .contagion-title { font-size:11px; font-weight:700; text-transform:uppercase;
                       letter-spacing:.06em; color:var(--muted); margin-bottom:8px; }
    /* Canal cards */
    .canal-card { border-radius:10px; padding:10px 12px; margin-bottom:8px;
                  border-left:3px solid; }
    .canal-card.si  { border-left-color:var(--green2); background:rgba(86,211,100,.06); }
    .canal-card.no  { border-left-color:var(--yellow2); background:rgba(227,179,65,.06); }
    .canal-card.trump { border-left-color:var(--red2); background:rgba(248,81,73,.08); }
    .canal-header { display:flex; align-items:flex-start; gap:7px; margin-bottom:5px; flex-wrap:wrap; }
    .canal-num  { font-size:9px; color:var(--muted); font-weight:700; text-transform:uppercase;
                  letter-spacing:.06em; white-space:nowrap; padding-top:2px; }
    .canal-name { font-size:12px; font-weight:700; flex:1; line-height:1.3; }
    .canal-badge { font-size:9px; font-weight:700; padding:2px 7px; border-radius:999px;
                   text-transform:uppercase; letter-spacing:.05em; white-space:nowrap; }
    .cbadge-si    { background:rgba(86,211,100,.15); color:var(--green2); }
    .cbadge-no    { background:rgba(227,179,65,.15); color:var(--yellow2); }
    .cbadge-trump { background:rgba(248,81,73,.15);  color:var(--red2); }
    .canal-chain { font-size:11px; color:var(--blue2); font-family:"SF Mono","Fira Code",monospace;
                   margin-bottom:8px; line-height:1.5; }
    .canal-chain .arrow { color:#58a6ff; font-weight:700; }
    .canal-body { display:grid; grid-template-columns:1fr 1fr; gap:8px; }
    .canal-section .clbl { font-size:9px; color:var(--muted); text-transform:uppercase;
                           letter-spacing:.05em; margin-bottom:3px; }
    .canal-section .cval { font-size:11px; line-height:1.5; }
    .trump-alert { font-size:10px; font-weight:700; color:var(--red2);
                   margin-top:6px; letter-spacing:.04em; }
    /* Generic table (brief-table only) */
    table { width:100%; border-collapse:collapse; font-size:11px; }
    th, td { padding:8px; border-bottom:1px solid var(--border); text-align:left; vertical-align:top; }
    th { background:#0d1117; position:sticky; top:0; color:var(--muted); font-size:10px;
         text-transform:uppercase; letter-spacing:.04em; }
    tr:last-child td { border-bottom:none; }
    .footer { font-size:11px; color:var(--muted); margin-top:10px; }
    /* RESPONSIVE */
    @media (max-width:1300px) { .layout { grid-template-columns:1fr; }
      .cards-grid { grid-template-columns:repeat(2,minmax(0,1fr)); } }
    @media (max-width:600px) { .compact-grid { grid-template-columns:1fr; } }
    .toast { position:fixed; bottom:24px; right:24px; padding:10px 18px; border-radius:10px;
             font-size:13px; font-weight:600; opacity:0; transform:translateY(8px);
             transition:opacity .3s,transform .3s; pointer-events:none; z-index:9999; }
    .toast.show { opacity:1; transform:translateY(0); }
    .toast-ok  { background:#1a7f37; color:#fff; }
    .toast-err { background:#b42318; color:#fff; }
  </style>
</head>
<body>
  <div class="page">
    <div class="topbar">
      <div class="title">
        <h1>Dashboard &mdash; Crudo, Geopolitica y Mercados Financieros</h1>
        <p>Dashboard de inteligencia geopolitica sobre el conflicto EEUU-Iran y el mercado del crudo WTI &middot; <strong style="color:#e6edf3">Iñigo Díez Osua</strong></p>
      </div>
      <div class="actions">
        <span class="badge" id="lastUpdated">Cargando...</span>
        <button id="refreshBtn">Recargar datos</button>
      </div>
    </div>

    <div class="cards-grid" id="summaryCards"></div>

    <div class="layout">
      <section class="panel">
        <h2>Termometro de mercado</h2>
        <div id="marketPanel"></div>
      </section>
      <section class="panel">
        <h2>Señales Polymarket</h2>
        <div class="filters" id="filtersContainer"></div>
        <div class="signals-scroll" id="signalsPanel"></div>
      </section>
      <section class="panel">
        <h2>Intelligence Brief</h2>
        <div class="brief-scroll" id="briefPanel"></div>
        <div class="contagion-wrap">
          <div id="contagionTable"></div>
        </div>
        <div class="footer" id="footerNote">
          Dashboard autocontenido. Los datos del modelo estan embebidos. El boton actualiza los precios de Polymarket en tiempo real.
        </div>
      </section>
    </div>
  </div>

  <div id="toast" class="toast"></div>
  <script id="initialData" type="application/json">__INITIAL_DATA__</script>
  <script>
    const TIER_ORDER = { descontado: 0, muy_probable: 1, probable: 2, cola: 3 };
    const TL_COLORS = { verde: '#1a7f37', amarillo: '#9e6a03', rojo: '#b42318', gris: '#484f58' };
    let STATE = JSON.parse(document.getElementById('initialData').textContent);
    let activeCategory = 'all';

    const fmtPct = (v, signed=false) => {
      if (v == null || isNaN(+v)) return 'n/d';
      const s = signed && +v > 0 ? '+' : '';
      return `${s}${(+v).toFixed(1)}%`;
    };
    const fmtMoney = (v, d=0) => {
      if (v == null || isNaN(+v)) return 'n/d';
      return new Intl.NumberFormat('en-US', { style:'currency', currency:'USD',
        minimumFractionDigits:d, maximumFractionDigits:d }).format(+v);
    };
    const fmtNum = (v, d=1) => v == null || isNaN(+v) ? 'n/d' : (+v).toFixed(d);
    const esc = s => String(s||'').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
    const getAsset = key => (STATE.market_snapshot.assets||[]).find(a => (a.asset||'').toLowerCase() === key);

    const CAT_LABELS = {
      macro_derived: 'Macro / Derivado', iran_conflict: 'Conflicto Iran',
      safe_haven: 'Activos Refugio', gold_price: 'Precio Oro',
      oil_price: 'Precio Petroleo', energy: 'Energia',
      us_policy: 'Politica EE.UU.', geopolitical: 'Geopolitico',
      military: 'Militar', diplomatic: 'Diplomatico', financial: 'Financiero',
      crypto: 'Cripto', equity: 'Renta Variable',
    };
    const fmtCat = s => s === 'all' ? 'Todas'
      : (CAT_LABELS[s] || s.replace(/_/g,' ').replace(/\b\w/g,c=>c.toUpperCase()));
    const calcTier = p => p>=90?'descontado':p>=75?'muy_probable':p>=60?'probable':'cola';

    function buildCards() {
      const c = STATE.brief_summary_cards || {};
      const items = [
        ['Estres historico', c.historical_stress_match || 'n/d'],
        ['Escenarios validados', (c.top_validated_scenarios||[]).join(' | ') || 'Ninguno'],
        ['Fuera de dominio', (c.top_out_of_domain_scenarios||[]).join(' | ') || 'Ninguno'],
        ['Divergencia principal', c.main_divergence || 'n/d'],
        ['Lectura final', c.main_takeaway || 'n/d'],
      ];
      document.getElementById('summaryCards').innerHTML =
        items.map(([k,v]) =>
          `<div class="card"><div class="k">${k}</div><div class="v">${esc(v)}</div></div>`
        ).join('');
    }

    function renderMarket() {
      const wti = getAsset('wti') || {};
      const big = `
        <div class="asset-big">
          <div class="asset-row">
            <div>
              <div class="asset-name">WTI Crudo</div>
              <div class="asset-tag">Apertura ${fmtMoney(wti.open,0)} &middot; Minimo ${fmtMoney(wti.low,0)} &middot; ${STATE.metadata.anchor_event_time||''}</div>
            </div>
            <div class="asset-price">
              <div class="big">${fmtMoney(wti.current_value||wti.provisional_close,0)}</div>
              <div class="sm">YTD ${fmtPct(wti.ytd_return,true)} &middot; Pctl ${fmtPct(wti.historical_percentile)}</div>
            </div>
          </div>
          <div class="pbar"><div class="pbar-fill" style="width:${Math.max(0,Math.min(100,+(wti.historical_percentile||0)))}%"></div></div>
          <div class="asset-tag" style="margin-top:8px">
            Swing intradiario: ${fmtPct(wti.max_intraday_move_pct,true)} &middot; Hora del minimo: ${wti.time_of_low||STATE.metadata.anchor_event_time||'n/d'}
          </div>
        </div>`;

      const compacts = ['gold','silver','sp500','vix','ovx','xom','cvx','bitcoin'];
      const grid = compacts.map(k => {
        const r = getAsset(k) || { asset: k.toUpperCase() };
        return `<div class="compact">
          <div class="cn">${r.asset||k.toUpperCase()}</div>
          <div class="cv">${fmtMoney(r.current_value,0)}</div>
          <div class="cm">YTD: ${fmtPct(r.ytd_return,true)} | dia: ${fmtPct(r.max_intraday_move_pct,true)}</div>
        </div>`;
      }).join('');

      const eventNote = `<div class="event-note">
        Evento ancla: ${esc(STATE.metadata.anchor_event_label||'')}. Iran desmiente contacto.
      </div>`;

      document.getElementById('marketPanel').innerHTML = big +
        `<div class="compact-grid">${grid}</div>` + eventNote;
    }

    function uniqueCats() {
      const sigs = STATE.polymarket_signals.signals || [];
      const cats = [...new Set(sigs.map(s => s.category_project).filter(Boolean))].sort();
      return ['all', ...cats];
    }

    function renderFilters() {
      const cats = uniqueCats();
      document.getElementById('filtersContainer').innerHTML = cats.map(c =>
        `<button class="chip ${activeCategory===c?'active':''}" data-cat="${c}">${fmtCat(c)}</button>`
      ).join('');
      document.querySelectorAll('.chip').forEach(btn =>
        btn.addEventListener('click', () => {
          activeCategory = btn.dataset.cat;
          renderFilters();
          renderSignals();
        })
      );
    }

    function findInference(question) {
      const records = STATE.scenario_inference.records || [];
      const q = question.toLowerCase();
      return records.find(r => String(r.scenario||'').toLowerCase() === q)
          || records.find(r => q.slice(0,28) === String(r.scenario||'').toLowerCase().slice(0,28));
    }

    function renderSignals() {
      let sigs = [...(STATE.polymarket_signals.signals || [])];
      sigs.sort((a,b) =>
        (TIER_ORDER[a.conviction_tier]??99) - (TIER_ORDER[b.conviction_tier]??99)
        || (+(b.yes_prob_pct||b.yes_prob||0)) - (+(a.yes_prob_pct||a.yes_prob||0))
      );
      if (activeCategory !== 'all') sigs = sigs.filter(s => s.category_project === activeCategory);

      const panel = document.getElementById('signalsPanel');
      panel.innerHTML = sigs.slice(0,80).map((s, i) => {
        const inf = findInference(s.question) || {};
        const prob = +(s.yes_prob_pct || s.yes_prob || 0);
        const tier = s.conviction_tier || 'cola';
        const did = `d${i}`;
        const tl = inf.traffic_light || 'gris';
        return `
          <div class="sig-card">
            <div class="sig-head" onclick="document.getElementById('${did}').classList.toggle('open')">
              <div class="sig-title">${esc(s.question||'Mercado')}</div>
              <div class="sig-meta">
                <span>${fmtCat(s.category_project||'')}</span>
                <span>${esc(tier)}</span>
                <span>${s.days_to_close??'?'}d</span>
                <span>dominio: ${s.in_model_domain??'?'}</span>
                <span style="color:${TL_COLORS[tl]}">&bull; ${tl}</span>
              </div>
              <div class="prob-bar">
                <div class="prob-fill t-${tier}" style="width:${Math.max(0,Math.min(100,prob))}%"></div>
              </div>
              <div class="sig-meta" style="margin-top:4px">
                <span>Prob: ${fmtPct(prob)}${s.delta_pp!=null&&s.delta_pp!==0?` <span style="color:${s.delta_pp>0?'#56d364':'#f85149'};font-size:10px">${s.delta_pp>0?'+':''}${s.delta_pp}pp</span>`:''}</span>
                <span>Liq: ${fmtMoney(s.liquidity||0,0)}</span>
                <span>Vol.24h: ${fmtMoney(s.volume_24h||0,0)}</span>
                ${s.signal_quality_score!=null ? `<span>SQS: ${fmtNum(s.signal_quality_score,3)}</span>` : ''}
              </div>
            </div>
            <div id="${did}" class="sig-body">
              <div class="dl">
                <span class="lbl">Probabilidad Polymarket</span>${fmtPct(prob)}
                <span class="lbl">Precedente historico</span>${esc(inf.precedent||'No disponible')}
                <span class="lbl">Lectura del historico observado</span>${esc(inf.historical_dataset_view||'No disponible')}
                <span class="lbl">Lectura del modelo (Partes 1 y 2)</span>${esc(inf.model_conclusion_view||'No disponible')}
                <span class="lbl">Si se cumple</span>${esc(inf.if_yes_implication||'No disponible')}
                <span class="lbl">Si no se cumple</span>${esc(inf.if_no_implication||'No disponible')}
                <span class="lbl">Ruta esperada de mercado</span>${esc(inf.expected_market_path||'No disponible')}
                <span class="lbl">Confianza</span>${esc(inf.confidence_label||'n/d')}${inf.confidence_score!=null?' &middot; score '+fmtNum(inf.confidence_score,1):''}
                <span class="lbl">Semaforo final</span>
                <span><span class="tl-dot" style="background:${TL_COLORS[tl]}"></span>${tl}</span>
              </div>
            </div>
          </div>`;
      }).join('');
    }

    function parseMdTable(block) {
      const lines = block.trim().split('\\n').filter(l => l.trim().startsWith('|'));
      let out = '<table class="brief-table">';
      let headerDone = false;
      for (const line of lines) {
        const t = line.trim();
        if (/^\\|[-:\\s|]+\\|$/.test(t)) continue; // separator row
        const cells = t.split('|').slice(1, -1).map(c => c.trim());
        if (!headerDone) {
          out += '<thead><tr>' + cells.map(c => '<th>' + c + '</th>').join('') + '</tr></thead><tbody>';
          headerDone = true;
        } else {
          out += '<tr>' + cells.map(c => '<td>' + c + '</td>').join('') + '</tr>';
        }
      }
      out += '</tbody></table>';
      return out;
    }

    function renderBrief() {
      const md = (STATE.intelligence_brief||{}).markdown || '';
      // 1. Parse markdown tables BEFORE newline conversion
      let html = md.replace(/((?:^\|[^\\n]+\\n?)+)/gm, parseMdTable);
      // 2. Convert remaining markdown
      html = html
        .replace(/`([^`]+)`/g, '<code style="background:#1c2333;padding:1px 4px;border-radius:3px;font-size:11px">$1</code>')
        .replace(/^# (.+)$/gm, '<h1>$1</h1>')
        .replace(/^## (.+)$/gm, '<h2>$1</h2>')
        .replace(/^### (.+)$/gm, '<h3>$1</h3>')
        .replace(/[*][*](.+?)[*][*]/g, '<strong>$1</strong>')
        .replace(/\[VERDE\]/g, '<span style="color:#56d364;font-weight:700">[VERDE]</span>')
        .replace(/\[AMARILLO\]/g, '<span style="color:#e3b341;font-weight:700">[AMARILLO]</span>')
        .replace(/\[ROJO\]/g, '<span style="color:#f85149;font-weight:700">[ROJO]</span>')
        .replace(/^- (.+)$/gm, '<li style="margin-left:14px">$1</li>')
        .replace(/^---$/gm, '<hr style="border-color:#30363d;margin:8px 0">')
        .replace(/\\n/g, '<br>');
      document.getElementById('briefPanel').innerHTML = '<div class="brief-text">' + html + '</div>';
    }

    function renderContagion() {
      const rows = (STATE.scenario_inference||{}).contagion_table || [];
      const wrap = document.getElementById('contagionTable');
      if (!rows.length) {
        wrap.innerHTML = '<p style="color:var(--muted);font-size:12px">No disponible</p>';
        return;
      }

      const cards = rows.map(r => {
        const isTrump = (r.canal||'').toLowerCase().includes('trump');
        const isSI    = r.modelado === 'SI';
        const cardCls = isTrump ? 'trump' : (isSI ? 'si' : 'no');

        const badgeCls  = isTrump ? 'cbadge-trump' : (isSI ? 'cbadge-si' : 'cbadge-no');
        const badgeTxt  = isTrump ? 'FUERA DE MODELO' : (isSI ? 'MODELADO' : 'OOD');

        // Split "Canal N — Nombre" into number + name
        const m = (r.canal||'').match(/^(Canal \\d+)[^a-zA-Z0-9]*(.*)$/);
        const cNum  = m ? m[1] : '';
        const cName = m ? m[2] : (r.canal||'');

        // Highlight arrows in chain
        const chain = esc(r.cadena||'').replace(/\u2192/g,
          '<span class="arrow">\u2192</span>');

        const trumpAlert = isTrump
          ? '<div class="trump-alert">DIVERGENCIA MAXIMA: evento no modelable. N=1.</div>'
          : '';

        return '<div class="canal-card ' + cardCls + '">'
          + '<div class="canal-header">'
          +   '<span class="canal-num">' + esc(cNum) + '</span>'
          +   '<span class="canal-name">' + esc(cName) + '</span>'
          +   '<span class="canal-badge ' + badgeCls + '">' + badgeTxt + '</span>'
          + '</div>'
          + '<div class="canal-chain">' + chain + '</div>'
          + '<div class="canal-body">'
          +   '<div class="canal-section">'
          +     '<div class="clbl">Observado hoy</div>'
          +     '<div class="cval">' + esc(r.observado||'') + '</div>'
          +   '</div>'
          +   '<div class="canal-section">'
          +     '<div class="clbl">Divergencia</div>'
          +     '<div class="cval">' + esc(r.divergencia||'') + '</div>'
          +   '</div>'
          + '</div>'
          + trumpAlert
          + '</div>';
      });

      wrap.innerHTML = '<div class="contagion-title">Canales de contagio sistemico</div>'
        + cards.join('');
    }

    function updateTimestamp() {
      const meta = STATE.metadata || {};
      const ts = meta.last_refresh_utc || meta.generated_at_utc;
      const tsStr = ts ? new Date(ts).toLocaleString('es-ES') : 'Datos embebidos';
      const stats = meta.refresh_stats;
      const statsStr = stats ? ` · ${stats.matched} ok / ${stats.noMatch} sin match` : '';
      document.getElementById('lastUpdated').textContent = 'Actualizado: ' + tsStr + statsStr;
    }

    async function fetchLatestJson() {
      try {
        const res = await fetch('./data/latest.json', { cache: 'no-store' });
        if (!res.ok) return;
        STATE = await res.json();
      } catch (e) { /* file:// mode - use embedded data */ }
    }

    function showToast(msg, isErr=false) {
      const t = document.getElementById('toast');
      t.textContent = msg;
      t.className = 'toast ' + (isErr ? 'toast-err' : 'toast-ok') + ' show';
      clearTimeout(t._tid);
      t._tid = setTimeout(() => { t.className = 'toast'; }, 4000);
    }

    async function refreshPolymarket() {
      const btn = document.getElementById('refreshBtn');

      // Cuando se abre con file://, fetch a archivos locales esta bloqueado por el navegador.
      // La actualizacion de datos se hace con el script Python: python update_polymarket.py
      if (window.location.protocol === 'file:') {
        showToast('Archivo local: ejecuta "python update_polymarket.py" y recarga la pagina', true);
        return;
      }

      btn.disabled = true;
      btn.textContent = 'Cargando...';
      try {
        const res = await fetch('./data/latest.json', { cache: 'no-store' });
        if (!res.ok) throw new Error(`HTTP ${res.status}`);
        STATE = await res.json();
        renderAll();
        const stats = STATE.metadata?.refresh_stats;
        const statsStr = stats ? ` · ${stats.matched} actualizados` : '';
        showToast('Datos recargados desde latest.json' + statsStr);
      } catch(e) {
        showToast('No se pudo leer latest.json: ' + e.message, true);
      } finally {
        btn.disabled = false;
        btn.textContent = 'Recargar datos';
      }
    }

    function renderAll() {
      buildCards();
      renderMarket();
      renderFilters();
      renderSignals();
      renderBrief();
      renderContagion();
      updateTimestamp();
    }

    document.getElementById('refreshBtn').addEventListener('click', refreshPolymarket);

    (async () => {
      await fetchLatestJson();
      renderAll();
    })();
  </script>
</body>
</html>
"""

# Inject the data (escape any closing script tags in JSON)
safe_json = initial_json_str.replace("</script>", "<\\/script>")
html_final = html.replace("__INITIAL_DATA__", safe_json)

html_path = DASHBOARD / "index.html"
DASHBOARD.mkdir(parents=True, exist_ok=True)
html_path.write_text(html_final, encoding="utf-8")
print(f"  Dashboard guardado: {html_path}")

# ─── RESUMEN FINAL ──────────────────────────────────────────────────────────
print("\n" + "="*60)
print("BLOQUE 5 COMPLETADO")
print("="*60)
print(f"  outputs/data/parte3/intelligence_brief.md")
print(f"  outputs/figures/parte3/intelligence_brief.png")
print(f"  dashboard/data/latest.json")
print(f"  dashboard/index.html")
print()
print(f"Tam latest.json : {(DASH_DATA / 'latest.json').stat().st_size // 1024} KB")
print(f"Tam index.html  : {html_path.stat().st_size // 1024} KB")
