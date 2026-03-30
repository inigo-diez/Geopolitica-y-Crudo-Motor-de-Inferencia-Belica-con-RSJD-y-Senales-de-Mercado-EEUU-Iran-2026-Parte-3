"""
build_enhanced_dashboard.py
Enriquece dashboard/data/latest.json con:
  - Series históricas diarias (parquet → JSON)
  - Forecasts RSJD stress-regime (5 días)
  - Matriz de correlaciones
  - Feed de noticias con sentimiento
  - Intelligence Brief mejorado con conclusiones Partes 1+2
Salida: dashboard/data/latest.json  (sobrescribe)
"""

import json, os, math, random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

BASE   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW    = os.path.join(BASE, "outputs", "raw")
DASH   = os.path.join(BASE, "dashboard", "data")
SOURCE = os.path.join(DASH, "latest.json")
OUT    = os.path.join(DASH, "latest.json")

# ── Parámetros RSJD Parte 2 ───────────────────────────────────────────────────
RSJD = {
    "WTI":    {"drift_yr": 0.184,  "vol_yr": 0.507, "jump_lam": 3.2, "jump_mu": -0.06, "jump_sig": 0.12},
    "BRENT":  {"drift_yr": 0.170,  "vol_yr": 0.490, "jump_lam": 3.0, "jump_mu": -0.05, "jump_sig": 0.11},
    "SP500":  {"drift_yr": -0.120, "vol_yr": 0.350, "jump_lam": 1.5, "jump_mu": -0.03, "jump_sig": 0.07},
    "GOLD":   {"drift_yr": 0.080,  "vol_yr": 0.280, "jump_lam": 1.0, "jump_mu":  0.02, "jump_sig": 0.05},
    "OVX":    {"drift_yr": 0.300,  "vol_yr": 0.800, "jump_lam": 4.0, "jump_mu":  0.08, "jump_sig": 0.20},
    "VIX":    {"drift_yr": 0.200,  "vol_yr": 0.700, "jump_lam": 3.5, "jump_mu":  0.06, "jump_sig": 0.15},
}

PARQUET_MAP = {
    "WTI":    "wti_daily.parquet",
    "BRENT":  "brent_daily.parquet",
    "SP500":  "sp500_daily.parquet",
    "NASDAQ": "nasdaq_daily.parquet",
    "GOLD":   "gold_daily.parquet",
    "SILVER": "silver_daily.parquet",
    "OVX":    "ovx_daily.parquet",
    "VIX":    "vix_daily.parquet",
    "DXY":    "dxy_daily.parquet",
    "XOM":    "xom_daily.parquet",
    "CVX":    "cvx_daily.parquet",
    "BTC":    "btc_daily.parquet",
    "TNX":    "tnx_daily.parquet",
}

# ── 1. Leer parquets ──────────────────────────────────────────────────────────
def load_series():
    series = {}
    for name, fname in PARQUET_MAP.items():
        path = os.path.join(RAW, fname)
        if not os.path.exists(path):
            continue
        df = pd.read_parquet(path)
        df = df[["close"]].copy()
        df.index = pd.to_datetime(df.index)
        df = df.sort_index()
        # Eliminar NaN al final (datos del mismo día aún en curso)
        df = df.dropna(subset=["close"])
        series[name] = df
    return series


# ── 2. Forecasts (log-normal GBM simplificado, 5 días) ───────────────────────
def make_forecast(last_price, params, n_days=5, n_paths=500, seed=42):
    rng = np.random.default_rng(seed)
    dt = 1 / 252
    mu   = params["drift_yr"]
    sig  = params["vol_yr"]
    lam  = params["jump_lam"]
    jmu  = params["jump_mu"]
    jsig = params["jump_sig"]

    paths = np.zeros((n_paths, n_days))
    for i in range(n_paths):
        S = last_price
        for t in range(n_days):
            z   = rng.standard_normal()
            N   = rng.poisson(lam * dt)
            J   = sum(rng.normal(jmu, jsig) for _ in range(N))
            ret = (mu - 0.5 * sig ** 2) * dt + sig * math.sqrt(dt) * z + J
            S   = S * math.exp(ret)
            paths[i, t] = S

    mean  = np.mean(paths, axis=0)
    upper = np.percentile(paths, 90, axis=0)
    lower = np.percentile(paths, 10, axis=0)
    return mean.tolist(), upper.tolist(), lower.tolist()


def build_forecast_dates(last_date, n=5):
    dates = []
    d = last_date
    while len(dates) < n:
        d = d + timedelta(days=1)
        if d.weekday() < 5:   # lunes–viernes
            dates.append(d.strftime("%Y-%m-%d"))
    return dates


# ── 3. Correlaciones (retornos log diarios) ───────────────────────────────────
def build_correlations(series):
    rets = {}
    for name, df in series.items():
        r = np.log(df["close"] / df["close"].shift(1)).dropna()
        rets[name] = r

    # Alinear por fecha
    df_rets = pd.DataFrame(rets).dropna(how="all")
    # Sólo columnas con datos suficientes
    valid = [c for c in df_rets.columns if df_rets[c].count() >= 5]
    df_rets = df_rets[valid].dropna()
    if df_rets.empty or len(df_rets) < 3:
        return {"assets": [], "matrix": []}

    corr = df_rets.corr().round(3)
    return {
        "assets": corr.columns.tolist(),
        "matrix": corr.values.tolist()
    }


# ── 4. Noticias con sentimiento ───────────────────────────────────────────────
NEWS = [
    # WTI / Energía – alcistas
    {
        "headline": "Estrecho de Ormuz permanece bloqueado: Irán mantiene patrullas navales",
        "source": "Reuters Energy",
        "timestamp": "2026-03-23T06:45:00Z",
        "sentiment": "alcista",
        "affected": ["WTI", "BRENT"],
        "body": "Las Fuerzas Navales de la Guardia Revolucionaria Iraní han intensificado las patrullas en el Estrecho de Ormuz, bloqueando efectivamente el tráfico de petroleros desde el 18 de marzo. Analistas de Goldman Sachs estiman que el bloqueo total retira ~20 mb/d del mercado global.",
        "source_type": "agencia"
    },
    {
        "headline": "Arabia Saudí activa capacidad de reserva: 2 mb/d adicionales disponibles",
        "source": "Bloomberg Commodities",
        "timestamp": "2026-03-23T07:15:00Z",
        "sentiment": "bajista",
        "affected": ["WTI", "BRENT"],
        "body": "Aramco confirma que Arabia Saudí activará 2 millones de barriles/día de capacidad de reserva para compensar parcialmente el bloqueo de Ormuz. La noticia limitó temporalmente el avance del crudo antes del post de Trump.",
        "source_type": "agencia"
    },
    {
        "headline": "Trump publica en Truth Social: 'conversaciones productivas' con Irán — pausa de 5 días",
        "source": "Truth Social / AFP",
        "timestamp": "2026-03-23T11:05:00Z",
        "sentiment": "bajista",
        "affected": ["WTI", "BRENT", "OVX"],
        "body": "El Presidente Trump publicó a las 07:05 ET: 'Hemos tenido conversaciones muy productivas con Irán. Estamos pausando las operaciones militares 5 días para llegar a un acuerdo histórico.' WTI cayó un 14.4% en 56 minutos.",
        "source_type": "politica"
    },
    {
        "headline": "Irán desmiente contacto con EE.UU.: 'No existe ninguna negociación'",
        "source": "FARS News Agency",
        "timestamp": "2026-03-23T12:01:00Z",
        "sentiment": "alcista",
        "affected": ["WTI", "OVX", "VIX"],
        "body": "La agencia de noticias oficial iraní FARS desmentió el post de Trump 56 minutos después: 'No existe ningún canal de negociación abierto con Washington.' WTI recuperó la mitad de las pérdidas en 20 minutos.",
        "source_type": "politica"
    },
    {
        "headline": "IEA activa reservas estratégicas: 60 millones de barriles liberados",
        "source": "IEA Press Release",
        "timestamp": "2026-03-23T14:30:00Z",
        "sentiment": "bajista",
        "affected": ["WTI", "BRENT"],
        "body": "La Agencia Internacional de Energía activa por segunda vez en el mes las reservas estratégicas, liberando 60 millones de barriles. Los miembros de la OCDE contribuyen con 2 mb/d durante 30 días. Impacto estimado: -$8/barril a corto plazo.",
        "source_type": "institucional"
    },
    {
        "headline": "XOM y CVX marcan máximos históricos: energía lidera el S&P 500 en 2026",
        "source": "Wall Street Journal",
        "timestamp": "2026-03-23T09:30:00Z",
        "sentiment": "alcista",
        "affected": ["XOM", "CVX", "SP500"],
        "body": "ExxonMobil (+41% YTD) y Chevron (+24% YTD) son los principales beneficiarios del shock energético. Con WTI sobre $85, el FCF de las grandes petroleras está en máximos desde 2008. Los analistas elevan los PO: XOM a $185, CVX a $230.",
        "source_type": "mercado"
    },
    {
        "headline": "Fed mantiene tipos en abril: mercado descuenta 95.3% de probabilidad",
        "source": "CME FedWatch / Polymarket",
        "timestamp": "2026-03-23T10:00:00Z",
        "sentiment": "neutral",
        "affected": ["SP500", "TNX", "DXY"],
        "body": "Con la inflación disparada por el shock energético, la Fed se encuentra en un dilema de stagflación. El mercado de futuros y Polymarket (95.3%) descuentan que mantendrá tipos en abril para no agravar la desaceleración económica.",
        "source_type": "macro"
    },
    {
        "headline": "Inflación de marzo ≥2.8%: apuesta Polymarket al 96.8%",
        "source": "Polymarket / BLS Data",
        "timestamp": "2026-03-23T08:30:00Z",
        "sentiment": "bajista",
        "affected": ["TNX", "SP500", "GOLD"],
        "body": "El shock energético trasladará un aumento significativo al IPC de marzo. Con WTI en $98 vs $68 en enero, la gasolina ha subido un 38% YTD. Los economistas de JPMorgan estiman +0.6pp al IPC headline de marzo.",
        "source_type": "macro"
    },
    {
        "headline": "Oro toca $4,570: rally de safe haven pese a tipos reales al alza",
        "source": "Bloomberg Markets",
        "timestamp": "2026-03-23T15:00:00Z",
        "sentiment": "alcista",
        "affected": ["GOLD", "SILVER"],
        "body": "El oro cierra en $4,570 (+$140 en la sesión) a pesar de que los tipos reales suben. La paradoja del safe haven se mantiene: el riesgo geopolítico extremo supera la presión de los tipos. Banco central de China confirmó compras adicionales de 30 toneladas.",
        "source_type": "mercado"
    },
    {
        "headline": "Bitcoin sube a $71,300 mientras WTI cae: ¿nuevo activo refugio?",
        "source": "CoinDesk / Bloomberg",
        "timestamp": "2026-03-23T12:30:00Z",
        "sentiment": "alcista",
        "affected": ["BTC"],
        "body": "BTC subió de $67,800 a $71,300 durante la caída intradiaria de WTI, sugiriendo un posible desacoplamiento del riesgo tradicional. El volumen de BTC alcanzó 3x la media diaria. Analistas de Ark Invest califican el movimiento como 'primeras señales de adopción como activo geopolítico.'",
        "source_type": "mercado"
    },
    {
        "headline": "OVX alcanza 120: volatilidad del crudo en máximos desde la pandemia",
        "source": "CBOE / Reuters",
        "timestamp": "2026-03-23T11:20:00Z",
        "sentiment": "bajista",
        "affected": ["WTI", "OVX", "VIX"],
        "body": "El índice de volatilidad implícita del crudo (OVX) tocó 120 intradiario, el nivel más alto desde marzo 2020. El swing intradiario de WTI de +17.4% es el mayor movimiento en una sola sesión en la historia del contrato de futuros CL.",
        "source_type": "mercado"
    },
    {
        "headline": "S&P 500 sorprende con caída limitada: -1.1% pese al caos energético",
        "source": "CNBC Markets",
        "timestamp": "2026-03-23T15:45:00Z",
        "sentiment": "alcista",
        "affected": ["SP500", "NASDAQ"],
        "body": "El S&P 500 cierra con una caída contenida del 1.1%, mucho menor de lo esperado. El sector energía (+4.2%) y materiales (+1.8%) compensan las pérdidas de consumo y tecnología. El mercado descuenta una resolución rápida del conflicto.",
        "source_type": "mercado"
    },
    {
        "headline": "Turquía ofrece mediación entre EE.UU. e Irán: cumbre en Ankara",
        "source": "Anadolu Agency",
        "timestamp": "2026-03-23T16:00:00Z",
        "sentiment": "bajista",
        "affected": ["WTI", "OVX", "VIX"],
        "body": "El presidente Erdogan ofreció formalmente Ankara como sede para conversaciones de emergencia entre delegaciones de Washington y Teherán. Qatar y Omán también han ofrecido sus buenos oficios. El WTI bajó $2 en respuesta.",
        "source_type": "politica"
    },
    {
        "headline": "Goldman Sachs: WTI alcanzará $120 si Ormuz permanece cerrado en abril",
        "source": "Goldman Sachs Research",
        "timestamp": "2026-03-23T10:30:00Z",
        "sentiment": "alcista",
        "affected": ["WTI", "BRENT"],
        "body": "El equipo de materias primas de Goldman Sachs revisó al alza su objetivo para WTI: $120/barril si el bloqueo de Ormuz continúa en abril, $105 en escenario base con resolución parcial, y $78 en caso de ceasefire completo antes del 15 de abril.",
        "source_type": "research"
    },
    {
        "headline": "JPMorgan: probabilidad de recesión EE.UU. en 2026 sube al 40%",
        "source": "JPMorgan Economics",
        "timestamp": "2026-03-23T11:00:00Z",
        "sentiment": "bajista",
        "affected": ["SP500", "TNX", "DXY"],
        "body": "El equipo de economía de JPMorgan eleva la probabilidad de recesión al 40% para 2026, desde 25% anterior. El doble shock energético + inflación crea un escenario de stagflación que históricamente precede recesiones. S&P bear market: 35% de probabilidad.",
        "source_type": "research"
    },
    {
        "headline": "DXY cae: inversores venden dólares por euros y francos suizos",
        "source": "FX Wire",
        "timestamp": "2026-03-23T13:00:00Z",
        "sentiment": "bajista",
        "affected": ["DXY"],
        "body": "El índice del dólar cae 0.7% ante la incertidumbre sobre la capacidad de la Fed para actuar. Los inversores rotan hacia EUR y CHF como refugios frente al dólar, que históricamente se debilita cuando la Fed está paralizada por stagflación.",
        "source_type": "mercado"
    },
    {
        "headline": "Congreso EE.UU. debate Acta de Poderes de Guerra: ¿límite al Ejecutivo?",
        "source": "Washington Post",
        "timestamp": "2026-03-23T14:00:00Z",
        "sentiment": "neutral",
        "affected": ["SP500", "VIX"],
        "body": "Líderes bipartidistas en el Senado convocan audiencias de emergencia para revisar el alcance del Acta de Poderes de Guerra. Si el Congreso limita la autoridad de Trump para continuar operaciones militares en Irán sin aprobación legislativa, el escenario geopolítico podría cambiar radicalmente.",
        "source_type": "politica"
    },
    {
        "headline": "Gasolineras en EE.UU. escasean: precio medio supera $5.50/galón",
        "source": "AAA Gas Prices",
        "timestamp": "2026-03-23T08:00:00Z",
        "sentiment": "bajista",
        "affected": ["SP500", "TNX"],
        "body": "El precio medio de la gasolina en EE.UU. supera los $5.50/galón por primera vez, con colas en algunas estaciones del sur. Los economistas advierten del efecto negativo sobre el consumo discrecional: cada $0.10 de subida en gasolina resta ~$15B anuales al gasto del consumidor.",
        "source_type": "macro"
    },
    {
        "headline": "Rusia aumenta exportaciones de crudo a Asia: oportunismo geopolítico",
        "source": "Reuters Commodities",
        "timestamp": "2026-03-23T09:00:00Z",
        "sentiment": "bajista",
        "affected": ["WTI", "BRENT"],
        "body": "Moscú aprovecha la disrupción para aumentar exportaciones a India y China, con descuentos del 15% sobre el precio de mercado. Esto mitiga parcialmente la restricción de oferta global, aunque el gap sigue siendo de ~6-8 mb/d sin Ormuz operativo.",
        "source_type": "geopolitica"
    },
    {
        "headline": "Fuerzas EE.UU. refuerzan presencia naval en Golfo Pérsico: portaaviones adicional",
        "source": "Pentagon / AP",
        "timestamp": "2026-03-23T07:00:00Z",
        "sentiment": "alcista",
        "affected": ["WTI", "OVX", "VIX"],
        "body": "El Pentágono confirma el despliegue del USS Dwight D. Eisenhower al Golfo Pérsico, sumándose al USS Gerald Ford ya presente. La presencia de dos grupos de batalla refuerza la posibilidad de operaciones de apertura forzada del Estrecho de Ormuz.",
        "source_type": "militar"
    },
]

IMPROVED_BRIEF = """# INTELLIGENCE BRIEF — Crudo, Geopolítica y Mercados Financieros
**Fecha:** 23 marzo 2026  |  **Snapshot puntual — no actualizable automáticamente**
**Evento ancla:** 11:05 UTC — Trump publica en Truth Social sobre 'conversaciones productivas' con Irán

---

## SITUACIÓN ACTUAL

- **WTI**: Abrió $99.2 · Máximo $101.7 · Mínimo intradiario $84.4 (−14.4%) · Cierre $86.0
- **Regime actual**: 6 de 8 dimensiones activas → **ESTRÉS EXTREMO**
- **GPR actual**: 248.8 (P97.8 histórico · umbral modelo Parte 1: 120)
- **OVX actual**: 91.8 (P98.6 histórico · umbral modelo Parte 1: 40)
- **Shock combinado**: energy_shock + policy_reversal_shock + inflation_shock + risk_off

---

## BASE EMPÍRICA: CONCLUSIONES DE LAS PARTES 1 Y 2

### Parte 1 — Clasificador de Estrés (Random Forest, 2010-2026)
- **Modelo**: Random Forest sobre 15 variables macro (GPR, OVX, GoldsteinScale, VIX, DXY, WTI log-returns, GDELT event counts, OVX percentile, extreme_event_dummy…)
- **Performance**: AUC=0.615 · F1=0.571 · Recall=0.918 · Umbral óptimo=0.46
- **Regla principal identificada**: GPR>120 + GoldsteinScale<−7 + OVX>P90 → probabilidad de high_stress_day sube sustancialmente (el modelo habría disparado ALERTA HOY)
- **Episodios comparables en training**: Golfo Pérsico 1990 (WTI +160%), Irak 2003 (WTI +30% previo), COVID-19 2020 (WTI −65%), Ucrania 2022 (WTI +50%)
- **Hoy en el modelo**: GPR=248.8 >> 120 · GoldsteinScale estimado < −9 · OVX=91.8 >> P90=40 → **ALERTA MÁXIMA ACTIVADA**

### Parte 2 — Modelo RSJD (Regime-Switching Jump-Diffusion)
- **Modelo**: Dos regímenes (normal/estrés) calibrados sobre 10,119 días de datos WTI
- **Régimen de estrés** (activo hoy): drift=+18.4%/año · vol=50.7%/año · λ_jump=3.2 saltos/año · μ_jump=−6%
- **Régimen normal**: drift=+4%/año · vol=25%/año
- **Probabilidad de estar en estrés hoy**: >98% según GPR/OVX actuales
- **Implicación**: La distribución de precios en el horizonte de 5-10 días es bimodal: escenario resolución (+recuperación) vs escenario escalada (+subida adicional)

---

## SEÑALES POLYMARKET — LECTURA POR CONVICTION TIER

### Descontado (>90%) — El mercado tiene alta convicción
- **Fed pausa en abril** (95.3%) → Respaldado por Parte 1: histórico de shocks energéticos muestra que la Fed suele pausar para no agravar el shock. **Convergencia modelo-mercado.**
- **Inflación ≥2.8% en marzo** (96.8%) → Aritméticamente inevitable: gasolina +38% YTD. No requiere modelo.
- **WTI < $90 en junio** (91.5%) → Parte 2 (RSJD): en régimen de estrés, la reversión media ocurre en 45-90 días. **Señal convergente.**

### Muy probable (75-90%) — Alta convicción, con incertidumbre
- **WTI < $90 en marzo** (86.8%) → WTI ya tocó $84.4 hoy intradiario. **YA SE HA PRODUCIDO** durante la sesión. Parte 1 marcó high_stress_day con recall=0.918.
- **Acción militar Irán-Golfo** (84.9%) → Dentro del dominio del modelo. GDELT cubre estos eventos.
- **Conflicto Irán-Israel/EEUU termina por diciembre** (86.0%) → Histórico: guerras regionales de esta escala raramente superan 12 meses. Parte 1 incluye Ucrania (aún sin resolver) como excepción OOD.
- **Reunión EEUU-Irán antes de junio** (87.5%) → Señal diplomática positiva. Si se confirma → WTI −15/−20%.

### Probable (60-75%) — Señal mixta
- **Acción militar Irán-Israel 25 marzo** (74.0%) → Parte 1 no distingue escalada de desescalada táctica. Señal incierta.
- **Ceasefire EEUU-Irán antes del 15 abril** (68.5%) → El post de Trump eleva esta probabilidad. Irán desmiente. **Alta divergencia política-mercado.**
- **Ormuz cerrado hasta abril** (55.5%) → Parte 1 cubre episodios de tensión en Ormuz (2019). En esos casos, la interrupción media fue de 12-18 días.

### Cola (<60%) — Eventos extremos
- **WTI > $100 en marzo** (41.1%) → Parte 2 (RSJD): con vol=50.7%/año, P(WTI>$100 en 8 días)~38%. **Consistente con Polymarket.**
- **Fuerzas EEUU entran en Irán** (13.5%) → PARCIALMENTE FUERA DE DOMINIO. El modelo fue entrenado con amenazas, no con invasiones directas a Irán. Única analogía: Irak 2003.
- **Caída del régimen iraní** (1.8%) → FUERA DE DOMINIO. Sin precedente en el dataset.
- **WTI > $150** (1.6%) → FUERA DE DOMINIO. Max histórico en training: $123.64 (2022). $150 implica un shock de oferta sin precedente en era moderna.
- **Bitcoin como refugio** (84.0%) → COMPLETAMENTE FUERA DEL DOMINIO. BTC no es variable en ninguno de los dos modelos.

---

## DICTAMEN FINAL — PARTES 1 Y 2 SOBRE LAS APUESTAS

| Apuesta Polymarket | Prob. | Color | Respaldo Parte 1 | Respaldo Parte 2 | Veredicto |
|---|---|---|---|---|---|
| Fed pausa abril | 95.3% | [VERDE] | Alto: histórico 100% en shocks energéticos | N/A (no modela política monetaria) | VALIDADO |
| WTI <$90 en junio | 91.5% | [VERDE] | Alto: reversión media en 45-90 días | Alto: drift negativo en reversión de régimen | VALIDADO |
| Inflación ≥2.8% | 96.8% | [VERDE] | Alto: aritmético, no requiere modelo | N/A | VALIDADO |
| WTI <$90 en marzo | 86.8% | [AMARILLO] | Medio: YA ocurrió intradiario, señal mixta | Medio: vol alta → realización intradiaria probable | PARCIAL |
| Ceasefire antes 15 abril | 68.5% | [AMARILLO] | Bajo: modelo no modeliza diplomacia | Bajo: no captura policy shocks | INCIERTO |
| WTI >$100 en marzo | 41.1% | [AMARILLO] | Medio: 38% probabilidad según RSJD | Medio: bimodalidad de distribución | INCIERTO |
| Recesión EEUU 2026 | 31.5% | [AMARILLO] | Bajo: señal contradictoria (GPR↑ → stress, pero recesión requiere demanda↓) | N/A | INCIERTO |
| Fuerzas EEUU en Irán | 13.5% | [ROJO] | Muy bajo: parcialmente OOD | Muy bajo: OOD | NO RESPALDADO |
| WTI >$150 | 1.6% | [ROJO] | Nulo: fuera de dominio de training | Nulo: extrapolación extrema | NO RESPALDADO |
| Caída régimen iraní | 1.8% | [ROJO] | Nulo: sin precedente en dataset | Nulo: OOD absoluto | NO RESPALDADO |

---

## TENDENCIAS DE APUESTAS POLYMARKET — ANÁLISIS DE FLUJO

**Volúmenes más altos (>$500K en 24h):**
1. Bitcoin $150K (Vol: $592K) → Apuesta especulativa, sin relación causal con el conflicto
2. Caída del régimen iraní (Vol: $1.26M) → El mayor volumen individual. Indica interés especulativo extremo, no convicción informada
3. Fuerzas EEUU en Irán (Vol: $1.52M) → Alto volumen relativo a probabilidad baja → smart money apostando al NO

**Señal de smart money:**
- El ratio volumen/liquidez más alto está en contratos de WTI <$90 y Fed pausa → consistente con cobertura institucional, no especulación
- Bajo volumen en WTI >$150 (prob. 1.6%) → el mercado NO cree en el escenario de colapso de oferta total
- Alto volumen en "Irán entra en Irán" al 13.5% → lectura: el mercado cree que NO ocurrirá, pero existe una prima de riesgo real

**Pendiente divergente:**
- Ceasefire EEUU-Irán antes 15 abril: 68.5% → Esta apuesta subió desde 45% hace 48h (post-Trump). Irán desmentido → probabilidad debería corregir
- WTI >$100 en marzo: cayó de 65% ayer a 41% hoy. El mercado asume que el swing a la baja de hoy ha reducido esta probabilidad

---

## DIVERGENCIAS CLAVE

**[ROJO] Lo que Polymarket prica que el modelo NO puede validar:**
- WTI > $150 (1.6%): el modelo fue entrenado hasta $123.64. Extrapolación pura.
- Ormuz cerrado hasta junio (27.0%): 90+ días consecutivos sin precedente en el dataset (max histórico: 28 días en 2019)
- Caída del régimen iraní (1.8%): evento N=1, sin análogos en el training

**[AMARILLO] Lo que el modelo sugiere que Polymarket NO descuenta suficientemente:**
- Bimodalidad de la distribución WTI: el RSJD sugiere que la distribución a 10 días tiene dos modos (~$78 y ~$105), pero Polymarket trata esto como lineal
- Riesgo de contagio al S&P: el modelo de Parte 1 identifica un canal GPR→VIX→S&P que históricamente materializa en 5-15 días, pero el S&P hoy solo cayó 1.1%
- Paradoja safe haven en oro: Polymarket no tiene apuestas explícitas sobre oro, pero el comportamiento del precio sugiere que el canal tipos reales → oro no está descontado

**[VERDE] Lo que coincide: modelo y Polymarket están de acuerdo:**
- Fed pausa en abril: alta convergencia
- Inflación elevada: aritméticamente inevitable
- WTI con alta volatilidad continuada: ambos fuentes coinciden en vol elevada

**Factor Trump (no modelable):**
El mayor swing intradiario de WTI de la historia moderna (+17.4% en 60 minutos) fue causado por un post en una red social. La varianza condicional del mercado ahora incluye un término de riesgo Trump que ningún modelo basado en series temporales puede capturar.

---

## TABLA DE CONTAGIO SISTÉMICO

| # | Canal | Cadena | Modelado | Observado hoy | Divergencia clave |
|---|---|---|---|---|---|
| 1 | Inflación-Tipos-Renta Variable | GPR↑ → OVX↑ → WTI↑ → IPC↑ → Fed pausa → yields↑ → S&P↓ | SI | WTI↑ con swing −14%, TNX↑, S&P↓ −1.1% (no crash) | S&P más resiliente de lo esperado. El mercado descuenta resolución rápida |
| 2 | Safe Haven Paradox | GPR↑ → WTI↑ → IPC↑ → tipos reales↑ → ORO↓ (presión tipos) vs GPR↑ → ORO↑ (demanda refugio) | NO | Oro↓ −8.8% intradiario, recuperación parcial a cierre +$140 | La paradoja se materializó: canal tipos reales dominó intradiario, canal refugio dominó al cierre |
| 3 | Risk-off Selectivo | GPR↑ → VIX↑ → S&P↓ → BTC↑ (activos fuera del sistema financiero tradicional) | NO | BTC SUBIÓ +5.1% mientras WTI caía. Posible desacoplamiento | Primera evidencia potencial de BTC como refugio geopolítico. No modelable en Parte 1/2 |
| 4 | Equity Energético Desacoplado | WTI↑ → revenues XOM/CVX↑ → equity energético outperforms | SI | CONFIRMADO: XOM +41% YTD, CVX +24% YTD. Canal perfecto | Sin divergencia. Canal funciona exactamente como predice el modelo |
| 5 | Factor Trump (no modelable) | Post red social → expectativa diplomática → WTI −14% en 56 min → desmentido iraní → recuperación parcial | NO | El mayor swing intradiario de WTI registrado | DIVERGENCIA MÁXIMA. Ningún modelo puede anticipar, detectar ni modelar este canal |

---

## CONCLUSIÓN

El episodio del 23 de marzo de 2026 es un **experimento natural extremo**: el primer shock energético de magnitud comparable al de 1973 que ocurre en la era de los mercados de predicción y los modelos de ML entrenados en décadas de datos.

**Lo que las Partes 1 y 2 aciertan:**
El clasificador de estrés (Parte 1) habría disparado alerta máxima correctamente: GPR=248 >> umbral, OVX=91.8 >> P90. El modelo RSJD (Parte 2) reproduce correctamente la distribución bimodal y la alta volatilidad realizada (OVX=91 vs vol_modelo=50.7%). El canal XOM/CVX (Canal 4) funciona exactamente como se esperaba.

**Lo que los modelos no capturan:**
El post de Trump a las 11:05 UTC creó el mayor swing intradiario de WTI de la historia moderna en menos de 60 minutos. Este es un riesgo de tipo N=1 que ningún modelo basado en series temporales puede modelar. La paradoja del safe haven en oro y el comportamiento de BTC como refugio son fenómenos emergentes no cubiertos por el training.

**Lectura integrada modelo + Polymarket:**
Polymarket descuenta con alta convicción (~87-95%) los escenarios que el modelo respalda empíricamente (Fed pausa, inflación alta, WTI volátil). La divergencia crítica está en el ceasefire: Polymarket lo prica al 68.5% (subió +23pp post-Trump), pero el desmentido iraní sugiere que esta probabilidad está sobreestimada. Si Polymarket corrige, WTI debería recuperar hacia $95-100.

Este brief no es una predicción: es una lectura argumentada del momento más inestable del mercado del crudo en décadas, separando cuidadosamente señal histórica, lectura del modelo y ruido político."""


def build_enhanced_json():
    # Cargar JSON base
    with open(SOURCE, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 1. Cargar series históricas
    series = load_series()

    # Añadir fecha del evento (Mar 23) usando provisional_close del market_snapshot
    # El parquet tenía NaN ese día (intradiario), lo inyectamos manualmente
    SNAP_CLOSES = {
        "WTI":    85.98,   # cierre provisional tras el swing de Trump
        "BRENT":  97.28,
        "SP500":  6640.73,
        "NASDAQ": 22151.81,
        "GOLD":   4485.60,
        "SILVER": 70.64,
        "OVX":    86.71,
        "VIX":    24.21,
        "DXY":    98.97,
        "XOM":    159.70,
        "CVX":    202.82,
        "BTC":    71301.11,
        "TNX":    4.32,
    }
    snap_date = pd.Timestamp("2026-03-23")
    for name, close_val in SNAP_CLOSES.items():
        if name in series:
            df = series[name]
            if snap_date not in df.index:
                new_row = pd.DataFrame({"close": [close_val]}, index=[snap_date])
                series[name] = pd.concat([df, new_row]).sort_index()

    # 2. Construir historical_series para el dashboard
    hist_out = {"dates": {}, "series": {}}
    for name, df in series.items():
        hist_out["series"][name] = {
            "dates":  [d.strftime("%Y-%m-%d") for d in df.index],
            "values": [round(float(v), 4) for v in df["close"]]
        }

    # 3. Forecasts (sólo assets con parámetros RSJD)
    forecasts_out = {}
    for name, params in RSJD.items():
        if name not in series:
            continue
        df = series[name]
        last_price = float(df["close"].iloc[-1])
        last_date  = df.index[-1]
        fdates = build_forecast_dates(last_date, n=5)
        mean, upper, lower = make_forecast(last_price, params, n_days=5)
        forecasts_out[name] = {
            "dates": fdates,
            "mean":  [round(v, 2) for v in mean],
            "upper": [round(v, 2) for v in upper],
            "lower": [round(v, 2) for v in lower],
        }

    # 4. Correlaciones
    correlations = build_correlations(series)

    # 5. Noticias
    news_out = NEWS

    # 6. Brief mejorado
    data["intelligence_brief"]["markdown"] = IMPROVED_BRIEF

    # Inyectar nuevos campos
    data["historical_series"] = hist_out
    data["forecasts"]         = forecasts_out
    data["correlations"]      = correlations
    data["news"]              = news_out

    # Guardar
    os.makedirs(DASH, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))

    print(f"OK Guardado: {OUT}")
    print(f"  Assets historicos: {list(hist_out['series'].keys())}")
    print(f"  Forecasts: {list(forecasts_out.keys())}")
    print(f"  Correlaciones: {correlations['assets']}")
    print(f"  Noticias: {len(news_out)}")


if __name__ == "__main__":
    build_enhanced_json()
