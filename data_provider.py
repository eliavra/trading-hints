import pandas as pd
import requests
from io import StringIO
import streamlit as st
import yfinance as yf
from datetime import datetime, timedelta
import threading
import pytz

_TV_SCANNER_URL = "https://scanner.tradingview.com/america/scan"
_TV_HEADERS = {"User-Agent": "Mozilla/5.0"}

_FALLBACK_TICKERS = [
    "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "BRK-B", "UNH", "JNJ",
    "V", "XOM", "JPM", "PG", "MA", "HD", "CVX", "LLY", "MRK", "ABBV",
]

# --- Global In-Memory State ---
if "GLOBAL_STATE" not in st.session_state:
    st.session_state["GLOBAL_STATE"] = {
        "data": {},
        "last_updated": None,
        "is_fetching": False
    }

# Reentrant Lock to allow nested calls to execute_managed_fetch without deadlocking
_fetch_lock = threading.RLock()

@st.cache_data(ttl=300)
def fetch_sp500_tickers() -> list[str]:
    try:
        resp = requests.get(
            "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies",
            headers=_TV_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        tables = pd.read_html(StringIO(resp.text))
        tickers = tables[0]["Symbol"].tolist()
        return [t.replace(".", "-") for t in tickers]
    except Exception:
        return _FALLBACK_TICKERS

@st.cache_data(ttl=300)
def fetch_nasdaq100_tickers() -> list[str]:
    try:
        resp = requests.get(
            "https://en.wikipedia.org/wiki/NASDAQ-100",
            headers=_TV_HEADERS,
            timeout=10,
        )
        resp.raise_for_status()
        tables = pd.read_html(StringIO(resp.text), match="Ticker")
        tickers = tables[0]["Ticker"].tolist()
        return [t.replace(".", "-") for t in tickers]
    except Exception:
        return _FALLBACK_TICKERS

@st.cache_data(ttl=300)
def fetch_tv_scan(payload: dict) -> dict:
    try:
        r = requests.post(_TV_SCANNER_URL, json=payload, headers=_TV_HEADERS, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception:
        return {}

@st.cache_data(ttl=300)
def fetch_yf_data(tickers, period: str, interval: str, group_by: str = "column") -> pd.DataFrame:
    df = yf.download(tickers, period=period, interval=interval, group_by=group_by, progress=False, threads=True)
    return df

@st.cache_data(ttl=300)
def fetch_yf_options_expirations(ticker: str) -> tuple:
    try:
        tkr = yf.Ticker(ticker)
        return tkr.options
    except Exception:
        return ()

@st.cache_data(ttl=60)
def fetch_latest_datapoint_time() -> str:
    try:
        df = yf.download("SPY", period="1d", interval="1m", progress=False)
        if not df.empty:
            last_dt = df.index[-1]
            israel_tz = pytz.timezone('Asia/Jerusalem')
            if last_dt.tzinfo is None:
                last_dt = pytz.utc.localize(last_dt)
            last_dt_israel = last_dt.astimezone(israel_tz)
            return last_dt_israel.strftime('%Y-%m-%d %H:%M %Z')
    except Exception:
        pass
    return "N/A"

@st.cache_data(ttl=300)
def fetch_yf_option_chain(ticker: str, expiration: str):
    try:
        tkr = yf.Ticker(ticker)
        chain = tkr.option_chain(expiration)
        return chain.calls, chain.puts
    except Exception:
        return pd.DataFrame(), pd.DataFrame()

# ---------------------------------------------------------------------------
# Background Manager (Stale-While-Revalidate)
# ---------------------------------------------------------------------------
def execute_managed_fetch(func, *args, **kwargs):
    """
    Returns data from session state immediately. 
    Triggers a background refresh if data is stale (> 5 mins).
    Blocks only on the very first call.
    """
    key = f"{func.__name__}_{str(args)}_{str(kwargs)}"
    
    if "GLOBAL_STATE" not in st.session_state:
        st.session_state["GLOBAL_STATE"] = {"data": {}, "is_fetching": False}
        
    state = st.session_state["GLOBAL_STATE"]
    cache = state["data"]
    
    now = datetime.now()
    entry = cache.get(key)
    
    if entry is None:
        # Initial block - use RLock to prevent deadlocks on nested calls
        with _fetch_lock:
            # Re-check after acquiring lock
            entry = cache.get(key)
            if entry is None:
                # Actual fetch
                result = func(*args, **kwargs)
                cache[key] = {"val": result, "ts": now}
                return result
            return entry["val"]
            
    # Check if stale (300 seconds = 5 mins)
    if (now - entry["ts"]).total_seconds() > 300:
        if not state["is_fetching"]:
            def background_task():
                try:
                    state["is_fetching"] = True
                    new_val = func(*args, **kwargs)
                    state["data"][key] = {"val": new_val, "ts": datetime.now()}
                except Exception:
                    pass
                finally:
                    state["is_fetching"] = False
            
            thread = threading.Thread(target=background_task)
            thread.daemon = True
            thread.start()
            
    return entry["val"]
