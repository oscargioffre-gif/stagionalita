"""
data_fetcher.py — Engine for fetching and computing seasonal stock patterns.

DATA SOURCES (in priority order):
1. Yahoo Finance (yfinance) — primary, free, reliable
2. Stooq.com CSV endpoint — fallback if yfinance fails
3. Cached local data — fallback if both fail (never invent data)

ENGINEERING PRINCIPLES:
- Never fabricate data. If a source fails, mark as MISSING.
- Every data point has a provenance tag: 'yfinance', 'stooq', 'cache', 'missing'.
- Statistical tests use scipy, not approximations.
- All computations are reproducible and logged.
"""

import yfinance as yf
import pandas as pd
import numpy as np
from scipy import stats
from datetime import datetime, timedelta
import requests
import json
import os
import hashlib
import logging
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
log = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# STOCK UNIVERSE — Tickers verified on investing.com 2026-04-07
# ═══════════════════════════════════════════════════════════════

STOCKS = {
    # ── MILANO FTSE MIB ──
    "ENI.MI":    {"name": "ENI",                 "sector": "Energia",           "market": "Milano"},
    "ENEL.MI":   {"name": "Enel",                "sector": "Utilities",         "market": "Milano"},
    "ISP.MI":    {"name": "Intesa Sanpaolo",     "sector": "Banche",            "market": "Milano"},
    "UCG.MI":    {"name": "UniCredit",           "sector": "Banche",            "market": "Milano"},
    "STM.MI":    {"name": "STMicroelectronics",  "sector": "Semiconduttori",    "market": "Milano"},
    "G.MI":      {"name": "Generali",            "sector": "Assicurazioni",     "market": "Milano"},
    "RACE.MI":   {"name": "Ferrari",             "sector": "Auto Lusso",        "market": "Milano"},
    "TEN.MI":    {"name": "Tenaris",             "sector": "Oil Services",      "market": "Milano"},
    "STLAM.MI":  {"name": "Stellantis",          "sector": "Automotive",        "market": "Milano"},
    "BAMI.MI":   {"name": "Banco BPM",           "sector": "Banche",            "market": "Milano"},
    "LDO.MI":    {"name": "Leonardo",            "sector": "Difesa",            "market": "Milano"},
    "CPR.MI":    {"name": "Campari",             "sector": "Bevande",           "market": "Milano"},
    "MONC.MI":   {"name": "Moncler",             "sector": "Moda/Lusso",        "market": "Milano"},
    "PRY.MI":    {"name": "Prysmian",            "sector": "Infrastrutture",    "market": "Milano"},
    "AMP.MI":    {"name": "Amplifon",            "sector": "Healthcare",        "market": "Milano"},
    "SPM.MI":    {"name": "Saipem",              "sector": "Oil Services",      "market": "Milano"},
    "PST.MI":    {"name": "Poste Italiane",      "sector": "Servizi Finanziari","market": "Milano"},
    "SRG.MI":    {"name": "Snam",                "sector": "Gas/Infrastrutture","market": "Milano"},
    "TRN.MI":    {"name": "Terna",               "sector": "Utilities",         "market": "Milano"},
    "MB.MI":     {"name": "Mediobanca",          "sector": "Banche",            "market": "Milano"},
    "PIRC.MI":   {"name": "Pirelli",             "sector": "Auto/Pneumatici",   "market": "Milano"},
    "TIT.MI":    {"name": "Telecom Italia",      "sector": "Telecomunicazioni", "market": "Milano"},
    "REC.MI":    {"name": "Recordati",           "sector": "Farmaceutica",      "market": "Milano"},
    "DIA.MI":    {"name": "DiaSorin",            "sector": "Diagnostica",       "market": "Milano"},
    "HER.MI":    {"name": "Hera",                "sector": "Utilities",         "market": "Milano"},
    "A2A.MI":    {"name": "A2A",                 "sector": "Utilities",         "market": "Milano"},
    # ── MILANO MID CAP ──
    "BCU.MI":    {"name": "Brunello Cucinelli",  "sector": "Moda/Lusso",        "market": "Milano"},
    "BPE.MI":    {"name": "BPER Banca",          "sector": "Banche",            "market": "Milano"},
    "BMED.MI":   {"name": "Banca Mediolanum",    "sector": "Risparmio Gestito", "market": "Milano"},
    "FBK.MI":    {"name": "FinecoBank",          "sector": "Fintech",           "market": "Milano"},
    "BRE.MI":    {"name": "Brembo",              "sector": "Auto/Componenti",   "market": "Milano"},
    "MARR.MI":   {"name": "MARR",                "sector": "Food Distribution", "market": "Milano"},
    "UNI.MI":    {"name": "Unipol",              "sector": "Assicurazioni",     "market": "Milano"},
    "SFER.MI":   {"name": "Ferragamo",           "sector": "Moda/Lusso",        "market": "Milano"},
    "IG.MI":     {"name": "Italgas",             "sector": "Gas/Utilities",     "market": "Milano"},
    # ── NASDAQ ──
    "AAPL":      {"name": "Apple",               "sector": "Tech Consumer",     "market": "NASDAQ"},
    "MSFT":      {"name": "Microsoft",           "sector": "Tech Cloud",        "market": "NASDAQ"},
    "AMZN":      {"name": "Amazon",              "sector": "E-Commerce/Cloud",  "market": "NASDAQ"},
    "GOOGL":     {"name": "Alphabet",            "sector": "Tech Advertising",  "market": "NASDAQ"},
    "META":      {"name": "Meta Platforms",       "sector": "Social Media",      "market": "NASDAQ"},
    "NVDA":      {"name": "NVIDIA",              "sector": "Semiconduttori/AI", "market": "NASDAQ"},
    "TSLA":      {"name": "Tesla",               "sector": "EV/Automotive",     "market": "NASDAQ"},
    "NFLX":      {"name": "Netflix",             "sector": "Streaming",         "market": "NASDAQ"},
    "AMD":       {"name": "AMD",                 "sector": "Semiconduttori",    "market": "NASDAQ"},
    "AVGO":      {"name": "Broadcom",            "sector": "Semiconduttori",    "market": "NASDAQ"},
    "COST":      {"name": "Costco",              "sector": "Retail",            "market": "NASDAQ"},
    "INTC":      {"name": "Intel",               "sector": "Semiconduttori",    "market": "NASDAQ"},
    "INTU":      {"name": "Intuit",              "sector": "Software/Fintech",  "market": "NASDAQ"},
    "PYPL":      {"name": "PayPal",              "sector": "Fintech",           "market": "NASDAQ"},
    "MU":        {"name": "Micron",              "sector": "Semiconduttori",    "market": "NASDAQ"},
    "ISRG":      {"name": "Intuitive Surgical",  "sector": "Healthcare/Robotica","market": "NASDAQ"},
    "DKNG":      {"name": "DraftKings",          "sector": "Gambling/Tech",     "market": "NASDAQ"},
    "PANW":      {"name": "Palo Alto Networks",  "sector": "Cybersecurity",     "market": "NASDAQ"},
    "CRWD":      {"name": "CrowdStrike",         "sector": "Cybersecurity",     "market": "NASDAQ"},
    "ABNB":      {"name": "Airbnb",              "sector": "Travel/Tech",       "market": "NASDAQ"},
    "ENPH":      {"name": "Enphase Energy",      "sector": "Solare/Energia",    "market": "NASDAQ"},
    "SBUX":      {"name": "Starbucks",           "sector": "Food & Beverage",   "market": "NASDAQ"},
    "MELI":      {"name": "MercadoLibre",        "sector": "E-Commerce LatAm",  "market": "NASDAQ"},
    "LRCX":      {"name": "Lam Research",        "sector": "Semiconduttori Eq.","market": "NASDAQ"},
    "TTD":       {"name": "The Trade Desk",      "sector": "Ad Tech",           "market": "NASDAQ"},
    "MNST":      {"name": "Monster Beverage",    "sector": "Bevande Energy",    "market": "NASDAQ"},
    "DASH":      {"name": "DoorDash",            "sector": "Food Delivery",     "market": "NASDAQ"},
    "ROKU":      {"name": "Roku",                "sector": "Streaming/Devices", "market": "NASDAQ"},
}

CACHE_DIR = "data_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Yahoo Finance uses different tickers than investing.com for some stocks.
# This map: our display ticker → list of Yahoo tickers to try in order.
YAHOO_ALIASES = {
    "STM.MI":   ["STMMI.MI", "STM.MI", "STM"],          # STMicro: Yahoo sometimes uses STMMI
    "BCU.MI":   ["BC.MI", "BCU.MI"],                      # Brunello Cucinelli: Yahoo uses BC
    "ENPH":     ["ENPH", "ENPH.O"],                       # Enphase: retry with NASDAQ suffix
    "BRE.MI":   ["BRE.MI", "BREMI.MI"],                   # Brembo
    "SFER.MI":  ["SFER.MI", "SFRGF"],                     # Ferragamo
    "IG.MI":    ["IG.MI", "IGMI.MI"],                     # Italgas
    "BPE.MI":   ["BPE.MI", "BPEMI.MI"],                   # BPER
    "MARR.MI":  ["MARR.MI"],                              # MARR
    "UNI.MI":   ["UNI.MI", "UNPI.MI"],                    # Unipol
    "BMED.MI":  ["BMED.MI"],                              # Mediolanum
    "FBK.MI":   ["FBK.MI"],                               # Fineco
    "TIT.MI":   ["TIT.MI", "TITR.MI"],                    # Telecom Italia
    "STLAM.MI": ["STLAM.MI", "STLA"],                    # Stellantis (also NYSE)
    "RACE.MI":  ["RACE.MI", "RACE"],                      # Ferrari (also NYSE)
}


# ═══════════════════════════════════════════════════════════════
# DATA FETCHING — Multi-source with fallbacks
# ═══════════════════════════════════════════════════════════════

def _cache_path(ticker):
    safe = hashlib.md5(ticker.encode()).hexdigest()
    return os.path.join(CACHE_DIR, f"{safe}.json")


def _save_cache(ticker, data):
    path = _cache_path(ticker)
    with open(path, 'w') as f:
        json.dump({"ticker": ticker, "ts": datetime.now().isoformat(), "data": data}, f)


def _load_cache(ticker):
    path = _cache_path(ticker)
    if os.path.exists(path):
        with open(path) as f:
            d = json.load(f)
        age_h = (datetime.now() - datetime.fromisoformat(d["ts"])).total_seconds() / 3600
        return d["data"], age_h
    return None, None


def _try_yfinance(yf_ticker, years=11):
    """Try downloading from Yahoo Finance with a specific ticker string."""
    try:
        end = datetime.now()
        start = end - timedelta(days=365 * years + 60)
        df = yf.download(yf_ticker, start=start.strftime('%Y-%m-%d'),
                         end=end.strftime('%Y-%m-%d'), interval='1mo',
                         progress=False, timeout=20)
        if df is None or len(df) < 24:
            return None

        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        df = df[['Close']].dropna()
        df['Return'] = df['Close'].pct_change() * 100
        df = df.dropna()
        df['Year'] = df.index.year
        df['Month'] = df.index.month

        result = {}
        for _, row in df.iterrows():
            y, m = int(row['Year']), int(row['Month'])
            result[f"{y}-{m}"] = round(row['Return'], 2)

        if len(result) >= 24:
            return result
        return None
    except Exception:
        return None


def fetch_monthly_returns_yfinance(ticker, years=11):
    """Primary source: Yahoo Finance — tries multiple ticker aliases."""
    aliases = YAHOO_ALIASES.get(ticker, [ticker])
    all_attempts = [ticker] + [a for a in aliases if a != ticker]
    # Remove duplicates preserving order
    seen = set()
    attempts = []
    for a in all_attempts:
        if a not in seen:
            seen.add(a)
            attempts.append(a)

    for yf_ticker in attempts:
        log.info(f"  Trying yfinance: {yf_ticker}")
        result = _try_yfinance(yf_ticker, years)
        if result:
            _save_cache(ticker, result)
            return result, f"yfinance ({yf_ticker})"
        time.sleep(0.3)  # Rate limit courtesy

    return None, f"yfinance: all aliases failed {attempts}"


def fetch_monthly_returns_stooq(ticker, years=11):
    """Fallback source: Stooq.com CSV API."""
    try:
        # Try multiple stooq ticker formats
        stooq_attempts = []
        if '.MI' in ticker:
            base = ticker.replace('.MI', '')
            stooq_attempts = [f"{base.lower()}.it", base.lower()]
        else:
            stooq_attempts = [ticker.lower(), f"{ticker.lower()}.us"]

        for stooq_ticker in stooq_attempts:
            end = datetime.now()
            start = end - timedelta(days=365 * years + 60)
            url = f"https://stooq.com/q/d/l/?s={stooq_ticker}&d1={start.strftime('%Y%m%d')}&d2={end.strftime('%Y%m%d')}&i=m"
            
            resp = requests.get(url, timeout=15, headers={'User-Agent': 'Mozilla/5.0'})
            if resp.status_code != 200 or len(resp.text) < 100:
                continue

            from io import StringIO
            df = pd.read_csv(StringIO(resp.text))
            if 'Close' not in df.columns or len(df) < 24:
                continue

            df['Date'] = pd.to_datetime(df['Date'])
            df = df.sort_values('Date')
            df['Return'] = df['Close'].pct_change() * 100
            df = df.dropna(subset=['Return'])

            result = {}
            for _, row in df.iterrows():
                y, m = row['Date'].year, row['Date'].month
                result[f"{y}-{m}"] = round(row['Return'], 2)

            if len(result) >= 24:
                _save_cache(ticker, result)
                return result, f"stooq ({stooq_ticker})"

    except Exception as e:
        log.warning(f"stooq failed for {ticker}: {e}")
    
    return None, "stooq: all attempts failed"


def fetch_monthly_returns_wsj(ticker, years=11):
    """Fallback 3: Wall Street Journal / MarketWatch historical data API."""
    try:
        # Map to MarketWatch-style ticker
        if '.MI' in ticker:
            base = ticker.replace('.MI', '')
            mw_ticker = f"it/{base.lower()}"
            country = "it"
        else:
            mw_ticker = f"us/{ticker.lower()}"
            country = "us"

        end = datetime.now()
        start = end - timedelta(days=365 * years + 60)
        
        # Try BigCharts/MarketWatch CSV endpoint
        url = f"https://api.wsj.net/api/dylan/quotes/v2/comp/quoteByDialect?id={ticker}&needed=CompositeTrading&MaxInstrumentMatches=1&accept=application/json&EntitlementToken=cecc4267a0194af89ca343805a3e57af"
        
        # This likely won't work but we try - the real fallback is retry yfinance with delay
        resp = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        if resp.status_code == 200:
            log.info(f"WSJ responded for {ticker}")
        
    except Exception:
        pass
    
    return None, "wsj: unavailable"


def fetch_monthly_returns_retry(ticker, years=11):
    """Last resort: retry yfinance with longer timeout and daily data converted to monthly."""
    try:
        aliases = YAHOO_ALIASES.get(ticker, [ticker])
        all_tickers = list(dict.fromkeys([ticker] + aliases))
        
        for yf_ticker in all_tickers:
            log.info(f"  Retry with daily data: {yf_ticker}")
            end = datetime.now()
            start = end - timedelta(days=365 * years + 60)
            
            df = yf.download(yf_ticker, start=start.strftime('%Y-%m-%d'),
                             end=end.strftime('%Y-%m-%d'), interval='1d',
                             progress=False, timeout=30)
            
            if df is None or len(df) < 200:
                continue

            if isinstance(df.columns, pd.MultiIndex):
                df.columns = df.columns.get_level_values(0)

            df = df[['Close']].dropna()
            
            # Resample daily to monthly (last business day of month)
            monthly = df['Close'].resample('ME').last().dropna()
            monthly_ret = monthly.pct_change().dropna() * 100
            
            result = {}
            for date, ret in monthly_ret.items():
                result[f"{date.year}-{date.month}"] = round(ret, 2)
            
            if len(result) >= 24:
                _save_cache(ticker, result)
                return result, f"yfinance-daily ({yf_ticker})"
            
            time.sleep(0.5)

    except Exception as e:
        log.warning(f"Retry failed for {ticker}: {e}")
    
    return None, "retry: all attempts failed"


def fetch_monthly_returns(ticker):
    """Fetch with 4-level cascading fallbacks. NEVER fabricate data."""
    # 1. Yahoo Finance (monthly interval, with aliases)
    data, src = fetch_monthly_returns_yfinance(ticker)
    if data:
        return data, src

    # 2. Stooq.com (multiple ticker formats)
    data, src = fetch_monthly_returns_stooq(ticker)
    if data:
        return data, src

    # 3. Yahoo Finance retry with daily data → resample to monthly
    data, src = fetch_monthly_returns_retry(ticker)
    if data:
        return data, src

    # 4. Cache (stale is better than nothing, but flag it)
    cached, age_h = _load_cache(ticker)
    if cached:
        log.info(f"Using cache for {ticker} (age: {age_h:.0f}h)")
        return cached, f"cache ({age_h:.0f}h old)"

    # FAIL — do NOT invent data
    log.error(f"ALL 4 SOURCES FAILED for {ticker}")
    return None, "NO_DATA"


# ═══════════════════════════════════════════════════════════════
# SEASONAL ANALYSIS
# ═══════════════════════════════════════════════════════════════

SEASONAL_CAUSES = {
    1: {"up": "January Effect; nuovi flussi PAC; ottimismo inizio anno.", "down": "Prese di profitto post-Santa Claus Rally; riposizionamento istituzionale."},
    2: {"up": "Reporting Q4/annuale positivo; flussi da bonus; guidance.", "down": "Delusione risultati annuali; bassa liquidità pre-earnings."},
    3: {"up": "Window dressing Q1; ripresa economica primaverile.", "down": "Sell in March anticipato; scadenze tributarie; profit-taking."},
    4: {"up": "Stagione utili Q1 ottimistica; flussi primaverili.", "down": "Tax day USA (15/4); vendite per imposte; realizzo Q1."},
    5: {"up": "Risultati Q1 sopra attese; buyback post-earnings.", "down": "Sell in May and go away; inizio bassa liquidità estiva."},
    6: {"up": "Russell reconstitution; dividendi semestrali EU; OPEX.", "down": "Fine semestre profit-taking; calo volumi pre-estivo."},
    7: {"up": "Inizio reporting Q2; Summer rally.", "down": "Bassa liquidità estiva; vacanze istituzionali; volumi minimi."},
    8: {"up": "Posizionamento pre-autunno; Jackson Hole dovish.", "down": "Agosto storicamente debole; Jackson Hole hawkish; volumi minimi."},
    9: {"up": "Posizionamento Q4; nuovi lanci prodotto.", "down": "September Effect (mese peggiore); ribilanciamento fondi pensione."},
    10: {"up": "October reversal post-settembre; inizio earnings Q3.", "down": "Volatilità elevata; panic selling su earnings deludenti."},
    11: {"up": "Thanksgiving rally; inizio Best Six Months; Black Friday.", "down": "Tax-loss harvesting anticipato; incertezza Fed dicembre."},
    12: {"up": "Santa Claus Rally; window dressing fine anno; ottimismo.", "down": "Tax-loss selling; rebalancing annuale; realizzo plusvalenze."},
}


def analyze_ticker_seasonality(ticker, monthly_data):
    """Compute seasonal patterns for one ticker. Pure math, no fabrication."""
    if not monthly_data:
        return []

    now = datetime.now()
    cur_year, cur_month = now.year, now.month

    results = []
    for month in range(1, 13):
        vals = []
        year_detail = {}
        for key, ret in monthly_data.items():
            parts = key.split('-')
            y, m = int(parts[0]), int(parts[1])
            if m == month and y >= cur_year - 10:
                # Skip current month if not complete
                if y == cur_year and m == cur_month:
                    year_detail[y] = {"val": None, "status": "in_corso"}
                    continue
                vals.append(ret)
                year_detail[y] = {"val": ret, "status": "verified"}

        if len(vals) < 5:
            continue

        mean_ret = np.mean(vals)
        std_ret = np.std(vals, ddof=1) if len(vals) > 1 else 0
        n = len(vals)
        pos_pct = sum(1 for v in vals if v > 0) / n * 100

        # t-test
        t_stat, p_value = stats.ttest_1samp(vals, 0)
        direction = "up" if mean_ret > 0 else "down"
        consistency = pos_pct if direction == "up" else (100 - pos_pct)

        # Only keep significant patterns
        if p_value < 0.10 and consistency >= 60:
            cause = SEASONAL_CAUSES[month][direction]
            results.append({
                "month": month,
                "month_name": ['','Gen','Feb','Mar','Apr','Mag','Giu','Lug','Ago','Set','Ott','Nov','Dic'][month],
                "direction": direction,
                "mean_return": round(mean_ret, 2),
                "std": round(std_ret, 2),
                "positive_pct": round(pos_pct, 1),
                "n_years": n,
                "t_stat": round(t_stat, 2),
                "p_value": round(p_value, 4),
                "consistency": round(consistency, 1),
                "cause": cause,
                "yearly": year_detail,
            })

    return results


def run_full_analysis(progress_callback=None):
    """Run seasonal analysis on all stocks. Returns DataFrame + metadata."""
    all_results = []
    errors = []
    total = len(STOCKS)

    for i, (ticker, info) in enumerate(STOCKS.items()):
        if progress_callback:
            progress_callback(i / total, f"Analisi {info['name']} ({ticker})...")

        data, source = fetch_monthly_returns(ticker)

        if data is None:
            errors.append({"ticker": ticker, "name": info["name"], "error": source})
            continue

        patterns = analyze_ticker_seasonality(ticker, data)

        for p in patterns:
            all_results.append({
                "ticker": ticker,
                "name": info["name"],
                "sector": info["sector"],
                "market": info["market"],
                "source": source,
                **p
            })

    df = pd.DataFrame(all_results)
    if len(df) > 0:
        df = df.sort_values('p_value')

    return df, errors


def get_last_update_time():
    """Check when data was last fetched."""
    times = []
    for ticker in STOCKS:
        path = _cache_path(ticker)
        if os.path.exists(path):
            times.append(os.path.getmtime(path))
    if times:
        return datetime.fromtimestamp(max(times))
    return None
