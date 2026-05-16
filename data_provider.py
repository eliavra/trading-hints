import pandas as pd
import requests
from io import StringIO
import streamlit as st
import yfinance as yf

_TV_SCANNER_URL = "https://scanner.tradingview.com/america/scan"
_TV_HEADERS = {"User-Agent": "Mozilla/5.0"}

_FALLBACK_TICKERS = [
    "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "TSLA", "BRK-B", "UNH", "JNJ",
    "V", "XOM", "JPM", "PG", "MA", "HD", "CVX", "LLY", "MRK", "ABBV",
]

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
    # Wrap yf.download
    # yfinance download expects a list of strings or a space-separated string
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
        # Fetch 1m data for SPY to find the absolute most recent market datapoint
        df = yf.download("SPY", period="1d", interval="1m", progress=False)
        if not df.empty:
            last_dt = df.index[-1]
            import pytz
            israel_tz = pytz.timezone('Asia/Jerusalem')
            # Ensure the timestamp is timezone-aware
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
