import pandas as pd
import yfinance as yf
import requests
import json
from typing import List, Dict, Any

# Constants
WIKI_SP500_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
SECTOR_ETFS = ["XLK", "XLF", "XLE", "XLV", "XLI", "XLC", "XLY", "XLP", "XLU", "XLRE", "XLB"]
_FALLBACK_TICKERS = ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "BRK.B", "TSLA", "UNH", "JPM"]

def get_sp500_tickers() -> List[str]:
    """Scrapes S&P 500 tickers from Wikipedia with fallback."""
    try:
        table = pd.read_html(WIKI_SP500_URL)[0]
        tickers = table['Symbol'].tolist()
        # Clean tickers (replace . with - for yfinance compatibility)
        return [t.replace('.', '-') for t in tickers]
    except Exception as e:
        print(f"Warning: Wikipedia scrape failed ({e}). Using fallback tickers.")
        return _FALLBACK_TICKERS

def fetch_tv_breadth_data() -> pd.DataFrame:
    """
    Fetches real-time breadth data (Price, SMAs, 52-week High/Low, Volume) 
    for S&P 500 stocks via a direct TradingView Scanner API POST request.
    """
    url = "https://scanner.tradingview.com/america/scan"
    
    payload = {
        "filter": [
            {"left": "index", "operation": "in_range", "right": ["S&P 500"]}
        ],
        "options": {"lang": "en"},
        "markets": ["america"],
        "symbols": {"query": {"types": []}, "tickers": []},
        "columns": [
            "name",
            "close",
            "SMA20",
            "SMA50",
            "SMA200",
            "price_52_week_high",
            "price_52_week_low",
            "volume",
            "change"
        ],
        "sort": {"sortBy": "name", "sortOrder": "asc"},
        "range": [0, 550]
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        rows = []
        for item in data.get('data', []):
            d = item.get('d', [])
            rows.append({
                'ticker': item.get('s').split(':')[-1],
                'close': d[1],
                'sma20': d[2],
                'sma50': d[3],
                'sma200': d[4],
                'hi52': d[5],
                'lo52': d[6],
                'volume': d[7],
                'change': d[8]
            })
        return pd.DataFrame(rows)
    except Exception as e:
        print(f"Error fetching TradingView data: {e}")
        return pd.DataFrame()

def fetch_historical_sectors(months: int = 6) -> pd.DataFrame:
    """Fetches historical closing prices for Sector ETFs + SPY."""
    tickers = SECTOR_ETFS + ["SPY"]
    period = f"{months}mo"
    try:
        data = yf.download(tickers, period=period, interval="1d", group_by='ticker', auto_adjust=True)
        # Extract only 'Close' and flatten columns
        closes = pd.DataFrame({t: data[t]['Close'] for t in tickers})
        return closes.dropna()
    except Exception as e:
        print(f"Error fetching historical sector data: {e}")
        return pd.DataFrame()

def fetch_vix() -> float:
    """Fetches latest VIX close price."""
    try:
        vix = yf.Ticker("^VIX")
        return vix.history(period="1d")['Close'].iloc[-1]
    except Exception as e:
        print(f"Error fetching VIX: {e}")
        return 0.0

def fetch_ticker_history(ticker: str, years: int = 10) -> pd.DataFrame:
    """Fetches long-term weekly history for a specific ticker (Seasonality)."""
    try:
        data = yf.download(ticker, period=f"{years}y", interval="1wk")
        return data[['Close']].dropna()
    except Exception as e:
        print(f"Error fetching history for {ticker}: {e}")
        return pd.DataFrame()
