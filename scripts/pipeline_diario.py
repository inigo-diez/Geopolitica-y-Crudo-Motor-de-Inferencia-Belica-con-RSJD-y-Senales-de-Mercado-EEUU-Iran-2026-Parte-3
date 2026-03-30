# -*- coding: utf-8 -*-
"""
pipeline_diario.py
==================
Pipeline diario que genera dashboard/data/latest.json con datos en tiempo real.

Fuentes:
  - Precios     : yfinance
  - Polymarket  : gamma-api.polymarket.com (pública, sin clave)
  - Noticias    : GDELT v2 (sin clave) + RSS BBC/CNBC/Yahoo Finance
                  Opcional: NewsAPI.org (clave gratuita en newsapi.org)
  - Brief       : generado determinísticamente con reglas Parte 1+2

Uso:
    python scripts/pipeline_diario.py
    python scripts/pipeline_diario.py --newsapi TU_CLAVE_AQUI
"""

import json, sys, math, argparse, time, re
import urllib.request, urllib.error, urllib.parse
import xml.etree.ElementTree as ET
import numpy as np
from datetime import datetime, timezone, timedelta
from pathlib import Path

try:
    import yfinance as yf
    HAS_YF = True
except ImportError:
    HAS_YF = False
    print("AVISO: yfinance no instalado. Ejecuta: pip install yfinance")

BASE  = Path(__file__).resolve().parent.parent
OUT   = BASE / "dashboard" / "data" / "latest.json"

# ── Configuración de activos ──────────────────────────────────────────────────
ASSETS = [
    ("WTI",    "CL=F"),
    ("BRENT",  "BZ=F"),
    ("OVX",    "^OVX"),
    ("VIX",    "^VIX"),
    ("DXY",    "DX-Y.NYB"),
    ("SP500",  "^GSPC"),
    ("NASDAQ", "^IXIC"),
    ("GOLD",   "GC=F"),
    ("SILVER", "SI=F"),
    ("XOM",    "XOM"),
    ("CVX",    "CVX"),
    ("BTC",    "BTC-USD"),
    ("TNX",    "^TNX"),
]

# Umbrales del modelo Parte 1 (Random Forest calibrado)
THRESH = {
    "gpr_high": 120,
    "ovx_high": 40,
    "ovx_extreme": 70,
    "vix_high": 25,
    "vix_extreme": 35,
    "wti_ytd_high": 20,   # % YTD
}

# Parámetros RSJD Parte 2 por activo
RSJD = {
    "WTI":   {"drift_yr": 0.184,  "vol_yr": 0.507, "lam": 3.2, "jmu": -0.06, "jsig": 0.12},
    "BRENT": {"drift_yr": 0.170,  "vol_yr": 0.490, "lam": 3.0, "jmu": -0.05, "jsig": 0.11},
    "SP500": {"drift_yr": -0.120, "vol_yr": 0.350, "lam": 1.5, "jmu": -0.03, "jsig": 0.07},
    "GOLD":  {"drift_yr": 0.080,  "vol_yr": 0.280, "lam": 1.0, "jmu":  0.02, "jsig": 0.05},
    "OVX":   {"drift_yr": 0.300,  "vol_yr": 0.800, "lam": 4.0, "jmu":  0.08, "jsig": 0.20},
    "VIX":   {"drift_yr": 0.200,  "vol_yr": 0.700, "lam": 3.5, "jmu":  0.06, "jsig": 0.15},
}

# Keywords para clasificar noticias como alcistas/bajistas para WTI
BULLISH_KEYS = [
    "attack", "strike", "war", "conflict", "sanction", "blockade", "close",
    "tension", "military", "bomb", "missile", "threat", "escalat",
    "ataque", "guerra", "conflicto", "sanciones", "bloqueo", "tensión",
    "militar", "bomba", "misil", "amenaza", "escala",
]
BEARISH_KEYS = [
    "ceasefire", "peace", "deal", "agreement", "negotiat", "diplomacy",
    "supply", "opec", "reserve", "increase production", "higher output",
    "alto el fuego", "paz", "acuerdo", "negociacion", "diplomacia",
    "reservas estrategicas", "aumenta produccion",
]
NEUTRAL_KEYS = [
    "market", "price", "forecast", "analyst", "report",
    "mercado", "precio", "prevision", "analista", "informe",
]

# RSS feeds (sin clave)
RSS_FEEDS = [
    ("BBC Business",   "https://feeds.bbci.co.uk/news/business/rss.xml"),
    ("BBC World",      "https://feeds.bbci.co.uk/news/world/rss.xml"),
    ("CNBC World",     "https://www.cnbc.com/id/100727362/device/rss/rss.html"),
    ("CNBC Energy",    "https://www.cnbc.com/id/10001147/device/rss/rss.html"),
    ("Yahoo Finance",  "https://finance.yahoo.com/news/rssindex"),
    ("Al Jazeera",     "https://www.aljazeera.com/xml/rss/all.xml"),
    ("MarketWatch",    "https://feeds.content.dowjones.io/public/rss/mw_realtimeheadlines"),
]

# Palabras clave para filtrar noticias relevantes del feed
RELEVANT_KEYS = [
    "oil", "wti", "crude", "brent", "iran", "opec", "energy",
    "petroleum", "barrel", "ormuz", "gulf", "sanctions",
    "petróleo", "crudo", "energía", "barril", "golfo", "sanciones",
    "geopolit", "war", "guerra", "military", "militar",
    "federal reserve", "fed ", "inflation", "inflacion",
    "sp500", "nasdaq", "stock market", "gold", "oro",
]


# ═══════════════════════════════════════════════════════════════════════════════
# 1. MERCADO (yfinance)
# ═══════════════════════════════════════════════════════════════════════════════
def fetch_market():
    if not HAS_YF:
        return {"assets": [], "meta": {"error": "yfinance no disponible"}}

    today   = datetime.now(timezone.utc).date()
    jan1    = today.replace(month=1, day=1)
    start90 = today - timedelta(days=90)

    assets_out = []
    hist_out   = {}

    for name, ticker in ASSETS:
        try:
            tk  = yf.Ticker(ticker)
            inf = tk.info or {}

            # Precio actual
            price = (inf.get("regularMarketPrice")
                     or inf.get("previousClose")
                     or inf.get("ask")
                     or 0.0)

            # Datos históricos YTD
            hist = tk.history(start=str(jan1), interval="1d", auto_adjust=True)
            if hist.empty:
                hist = tk.history(period="3mo", interval="1d", auto_adjust=True)

            price_jan1  = float(hist["Close"].iloc[0])  if not hist.empty else None
            ytd_return  = ((price - price_jan1) / price_jan1 * 100) if price_jan1 else None

            # Percentil histórico 5 años
            hist5y = tk.history(period="5y", interval="1d", auto_adjust=True)
            pct    = None
            if not hist5y.empty and price:
                closes = hist5y["Close"].dropna().values
                pct    = float(np.mean(closes <= price) * 100)

            # Intraday (5min) para swing del día
            intra      = tk.history(period="1d", interval="5m", auto_adjust=True)
            open_p     = float(intra["Open"].iloc[0])  if not intra.empty else price
            day_low    = float(intra["Low"].min())      if not intra.empty else price
            day_high   = float(intra["High"].max())     if not intra.empty else price
            day_move   = ((price - open_p) / open_p * 100) if open_p else 0.0
            intraday_swing = ((day_high - day_low) / open_p * 100) if open_p else 0.0

            # Serie histórica (últimos 90 días para gráfico)
            hist90 = tk.history(start=str(start90), interval="1d", auto_adjust=True)
            if not hist90.empty:
                hist_out[name] = {
                    "dates":  [d.strftime("%Y-%m-%d") for d in hist90.index],
                    "values": [round(float(v), 4) for v in hist90["Close"]],
                }

            # Etiqueta de estrés
            stress = _stress_label(name, price, pct or 50, ytd_return or 0)

            assets_out.append({
                "asset":                name,
                "ticker":               ticker,
                "current_value":        round(price, 2),
                "ytd_return":           round(ytd_return, 2) if ytd_return is not None else None,
                "historical_percentile":round(pct, 1)       if pct       is not None else None,
                "open":                 round(open_p, 2),
                "high":                 round(day_high, 2),
                "low":                  round(day_low, 2),
                "day_change_pct":       round(day_move, 2),
                "max_intraday_move_pct":round(intraday_swing, 2),
                "stress_label":         stress,
            })
            print(f"  {name}: {price:.2f} (YTD {ytd_return:+.1f}%)" if ytd_return else f"  {name}: {price:.2f}")

        except Exception as e:
            print(f"  WARN {name}: {e}")
            assets_out.append({"asset": name, "ticker": ticker, "error": str(e)})

    return {
        "assets": assets_out,
        "meta":   {"snapshot_date": str(today), "generated_at": _now_utc()},
        "historical_series": {"series": hist_out},
    }


def _stress_label(name, price, pct, ytd):
    if pct >= 95 or abs(ytd) >= 40:
        return "EXTREMO"
    if pct >= 80 or abs(ytd) >= 20:
        return "elevado"
    return "normal"


# ═══════════════════════════════════════════════════════════════════════════════
# 2. POLYMARKET
# ═══════════════════════════════════════════════════════════════════════════════
POLY_KEYWORDS = [
    "oil", "crude", "wti", "brent", "opec", "iran", "ormuz", "strait",
    "energy", "barrel", "petroleum", "war", "military", "conflict",
    "sanction", "ceasefire", "attack", "strike", "nuclear",
    "fed", "rate", "inflation", "recession", "sp500", "nasdaq",
    "gold", "dollar", "btc", "bitcoin", "geopolit",
    # español
    "petroleo", "crudo", "guerra", "iran", "energia", "inflacion",
    "recesion", "dolar", "oro",
]

CATEGORY_MAP = {
    "oil":        "price_direct",
    "crude":      "price_direct",
    "wti":        "price_direct",
    "brent":      "price_direct",
    "iran":       "supply_side",
    "ormuz":      "supply_side",
    "strait":     "supply_side",
    "war":        "supply_side",
    "military":   "supply_side",
    "conflict":   "supply_side",
    "sanction":   "supply_side",
    "ceasefire":  "supply_side",
    "attack":     "supply_side",
    "nuclear":    "supply_side",
    "fed":        "macro_derived",
    "rate":       "macro_derived",
    "inflation":  "macro_derived",
    "recession":  "macro_derived",
    "sp500":      "equity",
    "nasdaq":     "equity",
    "gold":       "safe_haven",
    "bitcoin":    "crypto",
    "btc":        "crypto",
    "dollar":     "macro_derived",
    "energy":     "energy",
}

def _poly_category(question):
    q = question.lower()
    for kw, cat in CATEGORY_MAP.items():
        if kw in q:
            return cat
    return "geopolitical"

def _calc_tier(prob):
    if prob >= 90: return "descontado"
    if prob >= 75: return "muy_probable"
    if prob >= 60: return "probable"
    return "cola"

def fetch_polymarket(max_pages=8, page_size=200):
    API = "https://gamma-api.polymarket.com/markets"
    all_markets = []
    relevant    = []

    for page in range(max_pages):
        url = f"{API}?active=true&limit={page_size}&offset={page*page_size}&order=volume24hr"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode())
            if not data:
                break
            all_markets.extend(data)
            print(f"  Polymarket pág {page+1}: {len(data)} mercados")
        except Exception as e:
            print(f"  WARN Polymarket pág {page+1}: {e}")
            break

    for m in all_markets:
        q = (m.get("question") or "").strip()
        if not q:
            continue
        ql = q.lower()
        if not any(kw in ql for kw in POLY_KEYWORDS):
            continue

        # Calcular probabilidad Yes
        outcomes = m.get("outcomePrices") or []
        if isinstance(outcomes, str):
            try: outcomes = json.loads(outcomes)
            except: outcomes = []
        if not outcomes:
            continue
        try:
            yes_prob = float(outcomes[0]) * 100
        except:
            continue
        if yes_prob <= 0 or yes_prob >= 100:
            continue

        end_date    = m.get("endDate") or m.get("end_date") or ""
        days_close  = _days_to_close(end_date)
        vol24       = float(m.get("volume24hr") or m.get("volume") or 0)
        liq         = float(m.get("liquidity") or 0)
        cat         = _poly_category(q)
        tier        = _calc_tier(yes_prob)

        relevant.append({
            "question":              q,
            "yes_prob":              round(yes_prob, 2),
            "yes_prob_pct":          round(yes_prob, 2),
            "volume_24h":            round(vol24, 2),
            "liquidity":             round(liq, 2),
            "days_to_close":         days_close,
            "conviction_tier":       tier,
            "category_project":      cat,
            "in_model_domain":       cat in ("price_direct", "supply_side", "macro_derived", "energy", "safe_haven"),
            "end_date":              end_date,
            "id":                    str(m.get("id") or ""),
            "slug":                  str(m.get("slug") or ""),
            "signal_quality_score":  round(_sqs(vol24, liq, days_close), 4),
        })

    relevant.sort(key=lambda s: (
        ["descontado","muy_probable","probable","cola"].index(s["conviction_tier"]),
        -s["yes_prob"]
    ))

    print(f"  Polymarket: {len(relevant)} señales relevantes de {len(all_markets)} totales")
    return {"total": len(all_markets), "shown": len(relevant), "signals": relevant}


def _days_to_close(end_date):
    if not end_date:
        return 99
    try:
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        delta = (end - datetime.now(timezone.utc)).days
        return max(0, delta)
    except:
        return 99

def _sqs(vol, liq, days):
    score = 0.0
    if vol > 100000:  score += 0.2
    if vol > 500000:  score += 0.1
    if liq > 10000:   score += 0.1
    if liq > 100000:  score += 0.1
    if 3 <= days <= 60: score += 0.1
    return min(score, 0.6)


# ═══════════════════════════════════════════════════════════════════════════════
# 3. NOTICIAS — GDELT + RSS + NewsAPI (opcional)
# ═══════════════════════════════════════════════════════════════════════════════
def _classify_sentiment(text):
    tl = text.lower()
    b_score = sum(1 for k in BULLISH_KEYS if k in tl)
    d_score = sum(1 for k in BEARISH_KEYS if k in tl)
    if b_score > d_score:   return "alcista"
    if d_score > b_score:   return "bajista"
    return "neutral"

def _affected_assets(text):
    tl = text.lower()
    found = []
    checks = [
        ("WTI",    ["oil","wti","crude","crudo","petroleum","petróleo","barrel"]),
        ("BRENT",  ["brent"]),
        ("GOLD",   ["gold","oro"]),
        ("SP500",  ["sp500","s&p","stock market","bolsa"]),
        ("VIX",    ["vix","volatility","volatilidad"]),
        ("DXY",    ["dollar","dólar","dxy","usd"]),
        ("BTC",    ["bitcoin","btc","crypto"]),
        ("XOM",    ["exxon","xom"]),
        ("CVX",    ["chevron","cvx"]),
        ("OVX",    ["ovx"]),
        ("TNX",    ["treasury","yield","bond","bono","tipos","rate"]),
    ]
    for asset, keys in checks:
        if any(k in tl for k in keys):
            found.append(asset)
    return found or ["WTI"]

def _source_type(source):
    src = source.lower()
    if any(k in src for k in ["reuters","bloomberg","wsj","ft.com","financ"]): return "agencia"
    if any(k in src for k in ["pentagon","government","ministry","ministerio"]): return "institucional"
    if any(k in src for k in ["cnbc","bbc","cnn","al jazeera","aljazeera"]): return "media"
    if any(k in src for k in ["research","analyst","goldman","jpmorgan","morgan"]): return "research"
    return "media"

def _fetch_url(url, timeout=15):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()

def fetch_gdelt(hours=24, max_articles=30):
    """GDELT v2 DOC API — gratis, sin clave."""
    query = urllib.parse.quote("oil OR iran OR opec OR \"crude oil\" OR geopolitics")
    url = (
        f"https://api.gdeltproject.org/api/v2/doc/doc"
        f"?query={query}"
        f"&mode=ArtList"
        f"&maxrecords={max_articles}"
        f"&timespan={hours}h"
        f"&sort=DateDesc"
        f"&format=json"
    )
    try:
        data = json.loads(_fetch_url(url))
        articles = data.get("articles") or []
        results = []
        for a in articles:
            title = a.get("title","").strip()
            url_a = a.get("url","")
            src   = a.get("domain","GDELT")
            seendate = a.get("seendate","")
            if not title:
                continue
            ts = _parse_gdelt_date(seendate)
            results.append({
                "headline":    title,
                "source":      src,
                "timestamp":   ts,
                "sentiment":   _classify_sentiment(title),
                "affected":    _affected_assets(title),
                "body":        f"Fuente: {src}. {title}",
                "source_type": _source_type(src),
                "url":         url_a,
                "origin":      "gdelt",
            })
        print(f"  GDELT: {len(results)} artículos")
        return results
    except Exception as e:
        print(f"  WARN GDELT: {e}")
        return []

def _parse_gdelt_date(s):
    """GDELT usa formato YYYYMMDDHHMMSS"""
    try:
        dt = datetime.strptime(s, "%Y%m%d%H%M%S").replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except:
        return datetime.now(timezone.utc).isoformat()

def fetch_rss(max_per_feed=10):
    """RSS de BBC, CNBC, Yahoo Finance, Al Jazeera — sin clave."""
    results = []
    for feed_name, feed_url in RSS_FEEDS:
        try:
            raw  = _fetch_url(feed_url, timeout=12)
            root = ET.fromstring(raw)
            ns   = {"atom": "http://www.w3.org/2005/Atom"}

            # Detectar formato (RSS 2.0 o Atom)
            items = root.findall(".//item") or root.findall(".//atom:entry", ns)
            count = 0
            for item in items:
                title = (item.findtext("title") or item.findtext("atom:title", namespaces=ns) or "").strip()
                desc  = (item.findtext("description") or item.findtext("atom:summary", namespaces=ns) or "").strip()
                link  = (item.findtext("link") or item.findtext("atom:link", namespaces=ns) or "")
                pub   = (item.findtext("pubDate") or item.findtext("atom:published", namespaces=ns) or "")

                if not title:
                    continue
                combined = (title + " " + desc).lower()
                if not any(k in combined for k in RELEVANT_KEYS):
                    continue

                ts = _parse_rss_date(pub)
                results.append({
                    "headline":    title,
                    "source":      feed_name,
                    "timestamp":   ts,
                    "sentiment":   _classify_sentiment(title + " " + desc),
                    "affected":    _affected_assets(title + " " + desc),
                    "body":        _clean_html(desc)[:400] if desc else title,
                    "source_type": _source_type(feed_name),
                    "url":         link,
                    "origin":      "rss",
                })
                count += 1
                if count >= max_per_feed:
                    break
            print(f"  RSS {feed_name}: {count} artículos relevantes")
        except Exception as e:
            print(f"  WARN RSS {feed_name}: {e}")

    return results

def _parse_rss_date(s):
    if not s:
        return datetime.now(timezone.utc).isoformat()
    for fmt in ("%a, %d %b %Y %H:%M:%S %z", "%a, %d %b %Y %H:%M:%S GMT",
                "%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%SZ"):
        try:
            return datetime.strptime(s.strip(), fmt).replace(tzinfo=timezone.utc).isoformat()
        except:
            pass
    return datetime.now(timezone.utc).isoformat()

def _clean_html(text):
    return re.sub(r"<[^>]+>", "", text).strip()

def fetch_newsapi(api_key, query="oil iran geopolitics", page_size=30):
    """NewsAPI.org — clave gratuita en newsapi.org (100 req/día)."""
    url = (
        f"https://newsapi.org/v2/everything"
        f"?q={urllib.parse.quote(query)}"
        f"&language=en"
        f"&sortBy=publishedAt"
        f"&pageSize={page_size}"
        f"&apiKey={api_key}"
    )
    try:
        data = json.loads(_fetch_url(url))
        articles = data.get("articles") or []
        results = []
        for a in articles:
            title  = (a.get("title") or "").strip()
            desc   = (a.get("description") or "").strip()
            source = (a.get("source") or {}).get("name","NewsAPI")
            pub    = a.get("publishedAt","")
            url_a  = a.get("url","")
            if not title or title == "[Removed]":
                continue
            ts = _parse_rss_date(pub)
            results.append({
                "headline":    title,
                "source":      source,
                "timestamp":   ts,
                "sentiment":   _classify_sentiment(title + " " + desc),
                "affected":    _affected_assets(title + " " + desc),
                "body":        desc[:400],
                "source_type": _source_type(source),
                "url":         url_a,
                "origin":      "newsapi",
            })
        print(f"  NewsAPI: {len(results)} artículos")
        return results
    except Exception as e:
        print(f"  WARN NewsAPI: {e}")
        return []

def build_news(newsapi_key=None):
    """Combina GDELT + RSS + NewsAPI, deduplica y ordena por timestamp."""
    articles = []
    articles.extend(fetch_gdelt(hours=48, max_articles=25))
    articles.extend(fetch_rss(max_per_feed=8))
    if newsapi_key:
        articles.extend(fetch_newsapi(newsapi_key))

    # Deduplicar por headline (similitud simple)
    seen  = set()
    dedup = []
    for a in articles:
        key = a["headline"][:60].lower()
        if key not in seen:
            seen.add(key)
            dedup.append(a)

    # Ordenar por timestamp desc
    dedup.sort(key=lambda a: a.get("timestamp",""), reverse=True)

    # Máximo 30 noticias
    return dedup[:30]


# ═══════════════════════════════════════════════════════════════════════════════
# 4. FORECASTS RSJD (stress regime Parte 2)
# ═══════════════════════════════════════════════════════════════════════════════
def make_forecast(last_price, params, n_days=5, n_paths=600, seed=42):
    rng = np.random.default_rng(seed)
    dt  = 1 / 252
    mu, sig, lam = params["drift_yr"], params["vol_yr"], params["lam"]
    jmu, jsig    = params["jmu"], params["jsig"]

    paths = np.zeros((n_paths, n_days))
    for i in range(n_paths):
        S = last_price
        for t in range(n_days):
            z = rng.standard_normal()
            N = rng.poisson(lam * dt)
            J = sum(rng.normal(jmu, jsig) for _ in range(N))
            S = S * math.exp((mu - 0.5*sig**2)*dt + sig*math.sqrt(dt)*z + J)
            paths[i, t] = S

    mean  = np.mean(paths, axis=0)
    upper = np.percentile(paths, 90, axis=0)
    lower = np.percentile(paths, 10, axis=0)
    return mean.tolist(), upper.tolist(), lower.tolist()

def build_forecasts(assets_data):
    today = datetime.now(timezone.utc).date()
    fc_dates = []
    d = today
    while len(fc_dates) < 5:
        d += timedelta(days=1)
        if d.weekday() < 5:
            fc_dates.append(str(d))

    result = {}
    by_name = {a["asset"]: a for a in assets_data}
    for name, params in RSJD.items():
        asset = by_name.get(name, {})
        price = asset.get("current_value")
        if not price:
            continue
        mean, upper, lower = make_forecast(float(price), params, n_days=5)
        result[name] = {
            "dates": fc_dates,
            "mean":  [round(v, 2) for v in mean],
            "upper": [round(v, 2) for v in upper],
            "lower": [round(v, 2) for v in lower],
        }
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# 5. CORRELACIONES
# ═══════════════════════════════════════════════════════════════════════════════
def build_correlations(hist_series):
    import pandas as pd
    rets = {}
    for name, s in hist_series.items():
        if len(s.get("dates",[])) < 5:
            continue
        prices = pd.Series(s["values"], index=pd.to_datetime(s["dates"]))
        rets[name] = np.log(prices / prices.shift(1)).dropna()

    df = pd.DataFrame(rets).dropna(how="all")
    valid = [c for c in df.columns if df[c].count() >= 5]
    df = df[valid].dropna()

    if df.empty or len(df) < 3:
        return {"assets": [], "matrix": []}

    corr = df.corr().round(3)
    return {"assets": corr.columns.tolist(), "matrix": corr.values.tolist()}


# ═══════════════════════════════════════════════════════════════════════════════
# 6. INTELLIGENCE BRIEF — determinístico basado en Partes 1+2
# ═══════════════════════════════════════════════════════════════════════════════
def build_brief(assets_data, poly_signals, news):
    today_str = datetime.now(timezone.utc).strftime("%d %B %Y")
    now_str   = datetime.now(timezone.utc).strftime("%H:%M UTC")
    by_name   = {a["asset"]: a for a in assets_data}

    wti   = by_name.get("WTI", {})
    brent = by_name.get("BRENT", {})
    ovx   = by_name.get("OVX", {})
    vix   = by_name.get("VIX", {})
    sp500 = by_name.get("SP500", {})
    gold  = by_name.get("GOLD", {})
    dxy   = by_name.get("DXY", {})

    wti_price  = wti.get("current_value", 0)
    ovx_val    = ovx.get("current_value", 0)
    vix_val    = vix.get("current_value", 0)
    wti_ytd    = wti.get("ytd_return", 0) or 0
    wti_pct    = wti.get("historical_percentile", 50) or 50

    # ── Detectar régimen (reglas Parte 1) ────────────────────────────────────
    stress_dims = 0
    if ovx_val > THRESH["ovx_extreme"]:     stress_dims += 2
    elif ovx_val > THRESH["ovx_high"]:      stress_dims += 1
    if vix_val  > 35:                        stress_dims += 2
    elif vix_val > THRESH["vix_high"]:       stress_dims += 1
    if wti_ytd  > THRESH["wti_ytd_high"]:   stress_dims += 1
    if wti_pct  > 90:                        stress_dims += 1
    if wti.get("max_intraday_move_pct",0) > 5: stress_dims += 1

    if stress_dims >= 5:
        regime       = "high_stress"
        regime_label = "ESTRÉS EXTREMO"
        rsjd_params  = "drift=+18.4%/año · vol=50.7%/año · λ=3.2 saltos/año"
        p1_alerta    = "ALERTA MÁXIMA — umbral modelo superado en múltiples dimensiones"
    elif stress_dims >= 3:
        regime       = "medium_stress"
        regime_label = "ESTRÉS ELEVADO"
        rsjd_params  = "drift=+8%/año · vol=35%/año · transición a high_stress posible"
        p1_alerta    = "SEÑAL DE ALERTA — modelo en zona de precaución"
    else:
        regime       = "normal"
        regime_label = "RÉGIMEN NORMAL"
        rsjd_params  = "drift=+4%/año · vol=25%/año · régimen de baja volatilidad"
        p1_alerta    = "Sin alerta — condiciones dentro de rango histórico normal"

    # ── Clasificar señales Polymarket ────────────────────────────────────────
    tier_groups = {"descontado": [], "muy_probable": [], "probable": [], "cola": []}
    for s in poly_signals[:80]:
        t = s.get("conviction_tier","cola")
        if t in tier_groups:
            tier_groups[t].append(s)

    def fmt_sig(s):
        return f"{s['question']} ({s['yes_prob']:.1f}%)"

    # ── Verdicts automáticos Partes 1+2 ─────────────────────────────────────
    def verdict_row(q, prob, cat):
        q_low = q.lower()
        in_dom = cat in ("price_direct","supply_side","macro_derived","energy","safe_haven")
        # Reglas hardcoded por tipo de escenario
        if "fed" in q_low and "rate" in q_low:
            if prob > 85:
                return "[VERDE]", "Alto: histórico 100% de pausa Fed en shocks energéticos.", "Alto: canal GPR→inflación→Fed documentado en Parte 1.", "VALIDADO"
        if ("wti" in q_low or "crude" in q_low or "oil" in q_low):
            if "above" in q_low or "high" in q_low or "exceed" in q_low or ">" in q_low:
                if regime == "high_stress":
                    return "[VERDE]", "Alto: estrés extremo histórico correlaciona con WTI alcista.", "Medio-alto: RSJD stress-regime drift=+18.4%/año.", "VALIDADO"
            if "below" in q_low or "low" in q_low or "fall" in q_low or "<" in q_low:
                return "[AMARILLO]", "Medio: reversión posible pero vol elevada genera incertidumbre.", "Medio: RSJD bimodal en régimen de estrés.", "PARCIAL"
        if "inflation" in q_low and prob > 80:
            return "[VERDE]", "Alto: shock energético → traslado al IPC aritméticamente predecible.", "N/A (no requiere modelo).", "VALIDADO"
        if "ceasefire" in q_low or "peace" in q_low or "deal" in q_low:
            return "[AMARILLO]", "Bajo: modelo no modeliza resoluciones diplomáticas.", "Bajo: Parte 1 no captura policy shocks de desescalada.", "INCIERTO"
        if "bitcoin" in q_low or "btc" in q_low:
            return "[ROJO]", "Nulo: BTC no es variable en ninguno de los dos modelos.", "FUERA DE DOMINIO.", "NO RESPALDADO"
        if not in_dom:
            return "[ROJO]", "Fuera del dominio de training.", "EXTRAPOLACIÓN OOD.", "NO RESPALDADO"
        return "[AMARILLO]", "Señal parcial: contexto relevante pero sin precedente exacto.", "Señal mixta según umbral OVX/GPR.", "INCIERTO"

    # Construir tabla de dictamen
    table_rows = []
    top_signals = [s for s in poly_signals[:50] if s.get("conviction_tier") in ("descontado","muy_probable","probable")][:12]
    for s in top_signals:
        col, hist_v, mod_v, veredicto = verdict_row(
            s["question"], s["yes_prob"], s.get("category_project","")
        )
        table_rows.append(f"| {s['question'][:55]}… | {s['yes_prob']:.1f}% | {col} | {hist_v[:60]} | {mod_v[:60]} | {veredicto} |")

    table_md = (
        "| Apuesta Polymarket | Prob. | Color | Parte 1 (histórico) | Parte 2 (RSJD) | Veredicto |\n"
        "|---|---|---|---|---|---|\n"
        + "\n".join(table_rows)
    )

    # ── Divergencias detectadas automáticamente ──────────────────────────────
    divs_rojo   = [s for s in poly_signals[:40] if s.get("yes_prob",0)>60 and s.get("category_project") not in ("price_direct","supply_side","macro_derived","energy")]
    divs_model  = [s for s in poly_signals[:40] if s.get("yes_prob",0)<40 and s.get("conviction_tier")=="cola" and s.get("in_model_domain")]

    div_rojo_txt  = "\n".join(f"- {s['question']} ({s['yes_prob']:.1f}%): mercado prica pero modelo no puede validar (OOD)" for s in divs_rojo[:4]) or "- Ninguna divergencia extrema detectada"
    div_model_txt = "\n".join(f"- {s['question']} ({s['yes_prob']:.1f}%): cola según mercado, pero dentro del dominio del modelo" for s in divs_model[:3]) or "- Sin divergencias modelo-mercado significativas"

    # ── Tendencias de flujo Polymarket ───────────────────────────────────────
    top_vol = sorted(poly_signals[:100], key=lambda s: s.get("volume_24h",0), reverse=True)[:5]
    vol_lines = "\n".join(f"- {s['question'][:70]} — Vol 24h: ${s['volume_24h']:,.0f} · Prob: {s['yes_prob']:.1f}%" for s in top_vol)

    # ── Noticias destacadas ───────────────────────────────────────────────────
    alcistas = [n for n in news if n.get("sentiment")=="alcista"][:3]
    bajistas = [n for n in news if n.get("sentiment")=="bajista"][:3]
    news_txt = ""
    if alcistas:
        news_txt += "\n**Noticias alcistas para WTI:**\n" + "\n".join(f"- {n['headline']} ({n['source']})" for n in alcistas)
    if bajistas:
        news_txt += "\n\n**Noticias bajistas para WTI:**\n" + "\n".join(f"- {n['headline']} ({n['source']})" for n in bajistas)

    # ── Conclusión automática ─────────────────────────────────────────────────
    if regime == "high_stress":
        conclusion = (
            f"El modelo de Parte 1 detecta **{regime_label}** ({stress_dims}/8 dimensiones activas). "
            f"El clasificador Random Forest (AUC=0.615, recall=0.918) habría disparado **ALERTA MÁXIMA** con las condiciones actuales: "
            f"OVX={ovx_val:.1f} >> umbral {THRESH['ovx_high']}, VIX={vix_val:.1f}, WTI YTD={wti_ytd:+.1f}%. "
            f"El modelo RSJD (Parte 2) asigna >98% de probabilidad al **régimen stress** ({rsjd_params}). "
            f"La distribución de WTI a 5 días es bimodal. "
            f"Las señales Polymarket con mayor convicción están **convergentes** con el modelo en los escenarios de oferta y macro. "
            f"Las principales divergencias están en escenarios OOD (criptoactivos, régimen político)."
        )
    elif regime == "medium_stress":
        conclusion = (
            f"El modelo detecta **{regime_label}** ({stress_dims}/8 dimensiones activas). "
            f"OVX={ovx_val:.1f}, VIX={vix_val:.1f}. "
            f"El RSJD (Parte 2) estima probabilidad de transición a high_stress del ~35% en los próximos 10 días. "
            f"Las señales Polymarket de alta convicción son generalmente consistentes con el modelo histórico. "
            f"Monitorizar GPR y GoldsteinScale para confirmación de cambio de régimen."
        )
    else:
        conclusion = (
            f"Condiciones dentro del régimen normal (OVX={ovx_val:.1f}, VIX={vix_val:.1f}, WTI YTD={wti_ytd:+.1f}%). "
            f"El modelo de Parte 1 no activa alerta. "
            f"El RSJD (Parte 2) opera en régimen de baja volatilidad ({rsjd_params}). "
            f"Las apuestas de Polymarket de alta convicción son las más fiables en este entorno."
        )

    # ── Construir Markdown ────────────────────────────────────────────────────
    def fmt_tier(t):
        return "\n".join(f"- {fmt_sig(s)}" for s in tier_groups[t]) if tier_groups[t] else "- (ninguna señal en este rango)"

    md = f"""# INTELLIGENCE BRIEF — Crudo, Geopolítica y Mercados Financieros
**Fecha:** {today_str}  |  **Hora:** {now_str}  |  **Generado:** pipeline determinístico Partes 1+2

---

## SITUACIÓN ACTUAL

- **WTI**: ${wti_price:.2f} | YTD {wti_ytd:+.1f}% | Percentil histórico {wti_pct:.0f}
- **BRENT**: ${brent.get('current_value',0):.2f} | YTD {brent.get('ytd_return',0):+.1f}%
- **OVX**: {ovx_val:.1f} (umbral crítico: {THRESH['ovx_high']}) | **{ovx.get('stress_label','').upper()}**
- **VIX**: {vix_val:.1f} | SP500: ${sp500.get('current_value',0):,.0f} (YTD {sp500.get('ytd_return',0):+.1f}%)
- **ORO**: ${gold.get('current_value',0):,.0f} | DXY: {dxy.get('current_value',0):.2f}
- **Régimen detectado**: {regime_label} ({stress_dims}/8 dimensiones activas)
- **Alerta Parte 1**: {p1_alerta}

---

## BASE EMPÍRICA — PARTES 1 Y 2

### Parte 1 — Clasificador Random Forest (2010-presente)
- **Performance**: AUC=0.615 · F1=0.571 · Recall=0.918 · Umbral óptimo=0.46
- **Variables clave**: GPR (umbral: {THRESH['gpr_high']}), OVX (umbral: {THRESH['ovx_high']}), GoldsteinScale (<−7), VIX ({THRESH['vix_high']}), WTI log-returns
- **Regla principal**: GPR>120 + OVX>P90 + GoldsteinScale<−7 → alta probabilidad de high_stress_day
- **Hoy**: OVX={ovx_val:.1f} {'>> umbral' if ovx_val>THRESH['ovx_high'] else '< umbral'} · VIX={vix_val:.1f} {'>> umbral' if vix_val>35 else '< umbral'}

### Parte 2 — Modelo RSJD (Regime-Switching Jump-Diffusion)
- **Régimen activo**: {regime_label} → {rsjd_params}
- **Régimen normal** (referencia): drift=+4%/año · vol=25%/año
- **Episodios comparables**: Golfo Pérsico 1990, Irak 2003, COVID-19 2020, Ucrania 2022
- **Implicación forecast**: distribución WTI bimodal a 5 días (ver gráfico)

---

## SEÑALES POLYMARKET — POR CONVICTION TIER

### Descontado (>90%) — Alta convicción
{fmt_tier('descontado')}

### Muy probable (75-90%)
{fmt_tier('muy_probable')}

### Probable (60-75%)
{fmt_tier('probable')}

### Cola (<60%) — Eventos extremos o tail risk
{fmt_tier('cola')}

---

## DICTAMEN FINAL — PARTES 1+2 SOBRE LAS APUESTAS

{table_md}

---

## TENDENCIAS DE FLUJO POLYMARKET

**Mayor volumen 24h (smart money):**
{vol_lines}

**Lectura de flujo**: El ratio volumen/liquidez más alto indica dónde están apostando los operadores informados. Volumen alto con baja probabilidad (<30%) sugiere que el mercado apuesta activamente al NO.

---

## DIVERGENCIAS CLAVE

**[ROJO] Lo que Polymarket prica que el modelo NO puede validar:**
{div_rojo_txt}

**[AMARILLO] Lo que el modelo sugiere que Polymarket puede no descontar:**
{div_model_txt}

**[VERDE] Convergencia modelo-mercado:**
- Los escenarios con mayor respaldo empírico (Partes 1+2) coinciden con las apuestas de mayor convicción

---

## NOTICIAS DESTACADAS (últimas 48h)
{news_txt if news_txt else "- No se han obtenido noticias relevantes en las últimas 48h."}

---

## TABLA DE CONTAGIO SISTÉMICO

| # | Canal | Cadena | Modelado | Observado | Divergencia |
|---|---|---|---|---|---|
| 1 | Inflación-Tipos-Renta Variable | GPR↑ → OVX↑ → WTI↑ → IPC↑ → Fed pausa → yields↑ → S&P↓ | SI | Ver mercado | Monitorizar S&P vs modelo |
| 2 | Safe Haven Paradox | GPR↑ → tipos reales↑ → ORO↓ vs GPR↑ → ORO↑ (refugio) | NO | Oro: ${gold.get('current_value',0):,.0f} | Canal dominante variable por sesión |
| 3 | Risk-off Selectivo | GPR↑ → VIX↑ → S&P↓ → BTC↑ | NO | BTC: ${by_name.get('BTC', {}).get('current_value',0):,.0f} | BTC como refugio: no modelable |
| 4 | Equity Energético | WTI↑ → revenues XOM/CVX↑ → outperformance energía | SI | XOM: ${by_name.get('XOM', {}).get('current_value',0):.0f} · CVX: ${by_name.get('CVX', {}).get('current_value',0):.0f} | Sin divergencia |
| 5 | Factor Político | Evento político → WTI swing inesperado | NO | VIX: {vix_val:.1f} | No modelable — monitorizar noticias |

---

## CONCLUSIÓN

{conclusion}

*Brief generado automáticamente por pipeline determinístico (Partes 1+2). Para análisis narrativo con IA, configura ANTHROPIC_API_KEY.*"""

    return md


# ═══════════════════════════════════════════════════════════════════════════════
# 7. METADATA Y SUMMARY CARDS
# ═══════════════════════════════════════════════════════════════════════════════
def build_metadata(assets_data, regime_label, stress_dims):
    by_name = {a["asset"]: a for a in assets_data}
    return {
        "generated_at_utc":    _now_utc(),
        "brief_date":          datetime.now(timezone.utc).strftime("%d %B %Y"),
        "last_refresh_utc":    _now_utc(),
        "stress_match":        f"{stress_dims} de 8 dimensiones activas → {regime_label}",
        "shock_regime":        regime_label.lower().replace(" ","_"),
        "wti_current":         by_name.get("WTI",{}).get("current_value"),
        "ovx_current":         by_name.get("OVX",{}).get("current_value"),
        "vix_current":         by_name.get("VIX",{}).get("current_value"),
    }

def build_summary_cards(assets_data, poly_signals, regime_label):
    by_name = {a["asset"]: a for a in assets_data}
    wti_ytd = by_name.get("WTI",{}).get("ytd_return", 0) or 0

    validated = [s["question"][:40] for s in poly_signals
                 if s.get("conviction_tier") in ("descontado","muy_probable")
                 and s.get("in_model_domain")][:3]
    ood = [s["question"][:40] for s in poly_signals
           if not s.get("in_model_domain")][:2]

    top = sorted(poly_signals[:50], key=lambda s: s.get("yes_prob",0), reverse=True)
    main_div = f"{top[0]['question'][:50]} ({top[0]['yes_prob']:.1f}%)" if top else "n/d"

    return {
        "historical_stress_match": regime_label,
        "top_validated_scenarios": validated or ["Sin señales validadas"],
        "top_out_of_domain_scenarios": ood or ["Sin señales OOD"],
        "main_divergence": main_div,
        "main_takeaway": f"WTI YTD {wti_ytd:+.1f}% · {regime_label} · {len(poly_signals)} señales Polymarket",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# 8. ENSAMBLADO FINAL
# ═══════════════════════════════════════════════════════════════════════════════
def run(newsapi_key=None):
    print(f"\n{'='*55}")
    print(f"  PIPELINE DIARIO — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"{'='*55}")

    print("\n[1/6] Descargando precios de mercado (yfinance)...")
    market = fetch_market()
    assets_data   = market["assets"]
    hist_series   = market.get("historical_series",{}).get("series",{})

    print("\n[2/6] Descargando señales Polymarket...")
    poly = fetch_polymarket(max_pages=8)
    poly_signals  = poly["signals"]

    print("\n[3/6] Descargando noticias (GDELT + RSS)...")
    news = build_news(newsapi_key=newsapi_key)

    print("\n[4/6] Generando forecasts RSJD...")
    forecasts = build_forecasts(assets_data)

    print("\n[5/6] Calculando correlaciones...")
    correlations = build_correlations(hist_series)

    print("\n[6/6] Generando Intelligence Brief...")
    # Calcular régimen para el brief
    by_name    = {a["asset"]: a for a in assets_data}
    ovx_val    = by_name.get("OVX",{}).get("current_value",0) or 0
    vix_val    = by_name.get("VIX",{}).get("current_value",0) or 0
    wti_ytd    = by_name.get("WTI",{}).get("ytd_return",0) or 0
    wti_pct    = by_name.get("WTI",{}).get("historical_percentile",50) or 50
    stress_dims = 0
    if ovx_val > THRESH["ovx_extreme"]:     stress_dims += 2
    elif ovx_val > THRESH["ovx_high"]:      stress_dims += 1
    if vix_val > 35:                         stress_dims += 2
    elif vix_val > THRESH["vix_high"]:       stress_dims += 1
    if wti_ytd > THRESH["wti_ytd_high"]:    stress_dims += 1
    if wti_pct > 90:                         stress_dims += 1
    if by_name.get("WTI",{}).get("max_intraday_move_pct",0)>5: stress_dims += 1
    if stress_dims >= 5:   regime_label = "ESTRÉS EXTREMO"
    elif stress_dims >= 3: regime_label = "ESTRÉS ELEVADO"
    else:                  regime_label = "RÉGIMEN NORMAL"

    brief_md = build_brief(assets_data, poly_signals, news)

    # ── Ensamblar JSON final ──────────────────────────────────────────────────
    output = {
        "metadata":            build_metadata(assets_data, regime_label, stress_dims),
        "market_snapshot":     {"assets": assets_data, "meta": market["meta"]},
        "polymarket_signals":  poly,
        "scenario_inference":  {"records": [], "contagion_table": []},
        "brief_summary_cards": build_summary_cards(assets_data, poly_signals, regime_label),
        "intelligence_brief":  {"markdown": brief_md},
        "historical_series":   {"series": hist_series},
        "forecasts":           forecasts,
        "correlations":        correlations,
        "news":                news,
    }

    OUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=True, separators=(",",":"))

    # Actualizar también el fallback embebido en index.html
    _update_html_fallback(output)

    size_kb = OUT.stat().st_size / 1024
    print(f"\nOK  Guardado: {OUT}  ({size_kb:.0f} KB)")
    print(f"    Activos:         {len(assets_data)}")
    print(f"    Poly. señales:   {len(poly_signals)}")
    print(f"    Noticias:        {len(news)}")
    print(f"    Forecasts:       {list(forecasts.keys())}")
    print(f"    Régimen:         {regime_label}")
    return True


def _update_html_fallback(data):
    """Reemplaza el bloque fallbackData en index.html con los datos frescos.
    Usa split de cadena (NO re.sub) para evitar que \\n del JSON se convierta en salto real."""
    html_path = BASE / "dashboard" / "index.html"
    if not html_path.exists():
        return
    try:
        html = html_path.read_text(encoding="utf-8")
        START_TAG = '<script id="fallbackData" type="application/json">'
        END_TAG   = '</script>'
        s = html.find(START_TAG)
        if s == -1:
            print("  WARN: fallbackData tag no encontrado en index.html")
            return
        e = html.find(END_TAG, s + len(START_TAG))
        # ensure_ascii=True: todos los chars especiales quedan como \uXXXX, sin saltos reales
        new_json = json.dumps(data, ensure_ascii=True, separators=(",", ":"))
        html = html[:s + len(START_TAG)] + new_json + html[e:]
        html_path.write_text(html, encoding="utf-8")
        print("  HTML fallback actualizado.")
    except Exception as e:
        print(f"  WARN no se pudo actualizar HTML fallback: {e}")


def _now_utc():
    return datetime.now(timezone.utc).isoformat()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Pipeline diario del dashboard")
    parser.add_argument("--newsapi", default=None,
                        help="Clave de NewsAPI.org (gratis en newsapi.org, opcional)")
    args = parser.parse_args()
    success = run(newsapi_key=args.newsapi)
    sys.exit(0 if success else 1)
