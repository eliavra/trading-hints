from __future__ import annotations

import calendar
from dataclasses import dataclass
from datetime import datetime
from io import StringIO
import concurrent.futures

import pandas as pd
import streamlit as st

from models import (
    BreadthIndicator,
    MarketBreadth,
    SeasonalityResult,
    SeasonalityRow,
    SectorData,
    Signal,
)
import data_provider as dp

SECTORS: list[tuple[str, str]] = [
    ("Technology", "XLK"),
    ("Financials", "XLF"),
    ("Energy", "XLE"),
    ("Healthcare", "XLV"),
    ("Industrials", "XLI"),
    ("Communication", "XLC"),
    ("Consumer Disc.", "XLY"),
    ("Consumer Staples", "XLP"),
    ("Utilities", "XLU"),
    ("Real Estate", "XLRE"),
    ("Materials", "XLB"),
]

# We can re-export them if pages import them directly from data.py
get_sp500_tickers = dp.fetch_sp500_tickers
get_nasdaq100_tickers = dp.fetch_nasdaq100_tickers


# ---------------------------------------------------------------------------
# TradingView scanner — breadth snapshot (single HTTP call, ~0.5s)
# ---------------------------------------------------------------------------
@dataclass
class _TvBreadthSnapshot:
    pct_above_sma20: float
    pct_above_sma50: float
    pct_above_sma200: float
    new_highs: int
    new_lows: int
    net_nh_nl: int
    vol_breadth: float
    total: int


@st.cache_data(ttl=300)
def _fetch_tv_breadth(tickers: tuple[str, ...]) -> _TvBreadthSnapshot:
    tv_tickers = []
    for t in tickers:
        tv_tickers.append(f"NYSE:{t}")
        tv_tickers.append(f"NASDAQ:{t}")

    payload = {
        "symbols": {"tickers": tv_tickers},
        "columns": ["close", "SMA20", "SMA50", "SMA200",
                     "price_52_week_high", "price_52_week_low",
                     "volume", "change"],
    }

    try:
        data = dp.execute_managed_fetch(dp.fetch_tv_scan, payload)
        stocks = data.get("data", [])
    except Exception:
        return _TvBreadthSnapshot(0, 0, 0, 0, 0, 0, 1.0, 0)

    above_20 = above_50 = above_200 = new_highs = new_lows = 0
    up_vol = down_vol = 0.0
    valid = 0

    for item in stocks:
        d = item["d"]
        close, sma20, sma50, sma200, h52, l52, vol, chg = d
        if close is None:
            continue
        valid += 1
        if sma20 and close > sma20:
            above_20 += 1
        if sma50 and close > sma50:
            above_50 += 1
        if sma200 and close > sma200:
            above_200 += 1
        if h52 and close >= h52:
            new_highs += 1
        if l52 and close <= l52:
            new_lows += 1
        if vol and chg:
            if chg > 0:
                up_vol += vol
            elif chg < 0:
                down_vol += vol

    if valid == 0:
        return _TvBreadthSnapshot(0, 0, 0, 0, 0, 0, 1.0, 0)

    return _TvBreadthSnapshot(
        pct_above_sma20=round(above_20 / valid * 100, 1),
        pct_above_sma50=round(above_50 / valid * 100, 1),
        pct_above_sma200=round(above_200 / valid * 100, 1),
        new_highs=new_highs,
        new_lows=new_lows,
        net_nh_nl=new_highs - new_lows,
        vol_breadth=round(up_vol / down_vol, 2) if down_vol > 0 else 1.0,
        total=valid,
    )


# ---------------------------------------------------------------------------
# A/D Line — needs historical data, still uses yfinance (cached separately)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def _fetch_ad_line_data() -> dict[str, dict]:
    tickers = get_sp500_tickers()
    spy = dp.execute_managed_fetch(dp.fetch_yf_data, "SPY", period="2y", interval="1d", group_by="column")
    if spy.empty:
        return {}

    # For speed: compute from SPY daily advancing/declining via sector ETFs
    all_etfs = [s[1] for s in SECTORS] + ["SPY"]
    df = dp.execute_managed_fetch(dp.fetch_yf_data, all_etfs, period="2y", interval="1d", group_by="ticker")

    closes: dict[str, pd.Series] = {}
    for etf in all_etfs:
        try:
            col = df[etf]["Close"].dropna()
            if isinstance(col, pd.DataFrame):
                col = col.iloc[:, 0]
            if len(col) > 1:
                closes[etf] = col
        except (KeyError, IndexError):
            continue

    if not closes:
        return {}

    combined = pd.DataFrame(closes)
    daily_change = combined.diff()
    advancing = (daily_change > 0).sum(axis=1)
    declining = (daily_change < 0).sum(axis=1)
    net_advances = advancing - declining
    
    # McClellan Oscillator
    ema19 = net_advances.ewm(span=19, adjust=False).mean()
    ema39 = net_advances.ewm(span=39, adjust=False).mean()
    mco_series = ema19 - ema39
    current_mco = float(mco_series.iloc[-1]) if not mco_series.empty else 0.0
    
    results = {"MCO": current_mco}
    periods = {"1M": 21, "3M": 63, "6M": 126, "1Y": 252, "2Y": 504}
    
    for period, days in periods.items():
        period_net = net_advances.tail(days)
        if len(period_net) > 5:
            # We want to start the cumulative sum from the beginning of this period
            cumulative_ad = period_net.iloc[1:].cumsum()
            ad_values = cumulative_ad.tolist()
            ad_dates = [d.strftime("%Y-%m-%d") for d in cumulative_ad.index]
            
            sma10 = cumulative_ad.rolling(10).mean()
            if len(sma10.dropna()) >= 5:
                trend = "RISING" if float(sma10.iloc[-1]) > float(sma10.iloc[-5]) else "FALLING"
            else:
                trend = "N/A"
                
            results[period] = {
                "ad_line": ad_values,
                "ad_dates": ad_dates,
                "trend": trend
            }

    return results


# ---------------------------------------------------------------------------
# High-Low Index (Mathematically Smoothed 10-day SMA of Record High Percent)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def _fetch_high_low_index() -> float:
    try:
        tickers = get_sp500_tickers()
        df = dp.execute_managed_fetch(dp.fetch_yf_data, tickers, period="1y", interval="1d", group_by="column")
        if df.empty:
            return 50.0
            
        highs = df['High']
        lows = df['Low']

        # Calculate 52-week (252 trading days) rolling high and low
        rolling_high = highs.rolling(window=252).max()
        rolling_low = lows.rolling(window=252).min()

        # A stock hits a new 52-week high if its current high is >= its 252-day rolling high
        new_highs = (highs >= rolling_high).sum(axis=1)
        new_lows = (lows <= rolling_low).sum(axis=1)

        # Record High Percent
        rhp = (new_highs / (new_highs + new_lows)) * 100
        rhp = rhp.fillna(50) # If both 0, default to 50

        # High-Low Index = 10-day SMA of RHP
        hl_index = rhp.rolling(window=10).mean()
        
        return round(float(hl_index.iloc[-1]), 1)
    except Exception as e:
        print(f"Error fetching High-Low Index: {e}")
        return 50.0


# ---------------------------------------------------------------------------
# Risk & Volatility Metrics
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def _fetch_risk_metrics() -> dict[str, float]:
    metrics = {"vix": 0.0, "vix_3m": 0.0, "vix_6m": 0.0, "spy_atr_pct": 0.0}
    try:
        # Fetch VIX term structure
        vix_tickers = ["^VIX", "^VIX3M", "^VIX6M"]
        df_vix = dp.execute_managed_fetch(dp.fetch_yf_data, vix_tickers, period="5d", interval="1d", group_by="ticker")
        for t, k in zip(vix_tickers, ["vix", "vix_3m", "vix_6m"]):
            if t in df_vix:
                close = df_vix[t]["Close"].dropna()
                if isinstance(close, pd.DataFrame):
                    close = close.iloc[:, 0]
                if not close.empty:
                    metrics[k] = round(float(close.iloc[-1]), 2)
        
        # Fetch SPY for ATR
        spy = dp.execute_managed_fetch(dp.fetch_yf_data, "SPY", period="1mo", interval="1d", group_by="column")
        if not spy.empty and len(spy) >= 14:
            high = spy["High"].squeeze()
            low = spy["Low"].squeeze()
            close = spy["Close"].squeeze()
            
            prev_close = close.shift(1)
            tr1 = high - low
            tr2 = (high - prev_close).abs()
            tr3 = (low - prev_close).abs()
            
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(14).mean()
            
            current_atr = float(atr.iloc[-1])
            current_close = float(close.iloc[-1])
            metrics["spy_atr_pct"] = round((current_atr / current_close) * 100, 2)
            
    except Exception as e:
        print(f"Error fetching risk metrics: {e}")
        
    return metrics


# ---------------------------------------------------------------------------
# Signal functions
# ---------------------------------------------------------------------------
def _breadth_signal_sma20(val: float) -> tuple[Signal, str]:
    if val > 85:
        return Signal.OVERBOUGHT, "Reduce Longs / Tighten Stops"
    if val < 20:
        return Signal.OVERSOLD, "Look for Long Entries"
    if val > 70:
        return Signal.CAUTION, "Be Selective"
    return Signal.NEUTRAL, "Normal Exposure"


def _breadth_signal_sma50(val: float) -> tuple[Signal, str]:
    if val > 85:
        return Signal.RED_LIGHT, "Reduce Exposure"
    if val < 30:
        return Signal.GREEN_LIGHT, "Increase Exposure"
    if val > 75:
        return Signal.CAUTION, "Hedge Positions"
    return Signal.NEUTRAL, "Hold Current"


def _breadth_signal_sma200(val: float) -> tuple[Signal, str]:
    if val > 80:
        return Signal.STRONG_BULL, "Stay Long"
    if val < 40:
        return Signal.WEAK_BEAR, "Go Defensive"
    if val < 60:
        return Signal.CAUTION, "Tighten Stops"
    return Signal.HEALTHY, "Maintain Positions"


def _breadth_signal_nh_nl(val: int) -> tuple[Signal, str]:
    if val >= 50:
        return Signal.HEALTHY, "Trend Confirmed"
    if val > 0:
        return Signal.CAUTION, "Breadth Thinning - Be Selective"
    return Signal.DIVERGENCE, "Trend Weakening - Reduce"


def _breadth_signal_volume(ratio: float) -> tuple[Signal, str]:
    if ratio > 1.0:
        return Signal.BUYING, "Volume Confirms Trend"
    return Signal.SELLING, "Distribution - Be Cautious"


def _vix_signal(vix: float) -> tuple[Signal, str]:
    if vix >= 35:
        return Signal.FEAR, "Capitulation - Contrarian BUY Zone"
    if vix >= 25:
        return Signal.CAUTION, "Elevated Fear - Hedge / Be Selective"
    if vix <= 15:
        return Signal.EUPHORIA, "Complacency - Watch for Correction"
    return Signal.NEUTRAL, "Normal Volatility"


def _ad_line_signal(trend: str) -> tuple[Signal, str]:
    if trend == "RISING":
        return Signal.HEALTHY, "Broad Participation Confirmed"
    if trend == "FALLING":
        return Signal.DIVERGENCE, "Participation Narrowing - Caution"
    return Signal.NEUTRAL, "Insufficient Data"


def _compute_fear_greed(sma20: float, sma50: float, sma200: float, nh_nl: int, vol_ratio: float) -> float:
    sma20_score = min(max((sma20 - 20) / (85 - 20) * 100, 0), 100)
    sma50_score = min(max((sma50 - 30) / (85 - 30) * 100, 0), 100)
    sma200_score = min(max((sma200 - 40) / (80 - 40) * 100, 0), 100)
    nh_nl_score = min(max((nh_nl + 50) / 100 * 100, 0), 100)
    vol_score = min(max((vol_ratio - 0.5) / (1.5 - 0.5) * 100, 0), 100)
    return round(
        sma20_score * 0.25 + sma50_score * 0.25 + sma200_score * 0.2 + nh_nl_score * 0.15 + vol_score * 0.15, 1
    )


def _vix_term_signal(vix: float, vix_3m: float) -> tuple[Signal, str]:
    if vix == 0.0 or vix_3m == 0.0:
        return Signal.NEUTRAL, "Insufficient Data"
    if vix > vix_3m:
        return Signal.FEAR, "Backwardation (Panic)"
    ratio = vix / vix_3m
    if ratio > 0.9:
        return Signal.CAUTION, "Flattening Curve"
    return Signal.HEALTHY, "Normal Contango"

def _mco_signal(mco: float) -> tuple[Signal, str]:
    if mco > 50:
        return Signal.OVERBOUGHT, "Overbought Breadth"
    if mco < -50:
        return Signal.OVERSOLD, "Oversold Breadth"
    if mco > 0:
        return Signal.BULLISH, "Positive Breadth Momentum"
    return Signal.BEARISH, "Negative Breadth Momentum"

def _hl_ratio_signal(hl_ratio: float) -> tuple[Signal, str]:
    if hl_ratio > 80:
        return Signal.STRONG_BULL, "Strong Highs"
    if hl_ratio < 20:
        return Signal.WEAK_BEAR, "Strong Lows"
    if hl_ratio > 50:
        return Signal.BULLISH, "Highs > Lows"
    return Signal.BEARISH, "Lows > Highs"

def _atr_signal(atr_pct: float) -> tuple[Signal, str]:
    if atr_pct > 2.5:
        return Signal.CAUTION, "High Volatility (Reduce Size)"
    if atr_pct < 1.0:
        return Signal.EUPHORIA, "Low Volatility (Squeeze Risk)"
    return Signal.HEALTHY, "Normal Volatility"


# ---------------------------------------------------------------------------
# Main breadth function
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def compute_market_breadth() -> MarketBreadth:
    return dp.execute_managed_fetch(_compute_market_breadth_logic)

def _compute_market_breadth_logic() -> MarketBreadth:
    tickers = get_sp500_tickers()
    snap = _fetch_tv_breadth(tuple(tickers))

    sma20 = snap.pct_above_sma20
    sma50 = snap.pct_above_sma50
    sma200 = snap.pct_above_sma200
    nh = snap.new_highs
    nl = snap.new_lows
    nh_nl = snap.net_nh_nl
    vol_ratio = snap.vol_breadth

    # Make High-Low Index non-blocking by providing a fallback if it fails
    try:
        hl_ratio = _fetch_high_low_index()
    except Exception:
        hl_ratio = (nh / (nh + nl) * 100) if (nh + nl) > 0 else 50.0
        
    fg = _compute_fear_greed(sma20, sma50, sma200, nh_nl, vol_ratio)
    
    risk_metrics = _fetch_risk_metrics()
    vix = risk_metrics["vix"]
    vix_3m = risk_metrics["vix_3m"]
    vix_6m = risk_metrics["vix_6m"]
    spy_atr_pct = risk_metrics["spy_atr_pct"]
    
    ad_data = _fetch_ad_line_data()
    mco = ad_data.get("MCO", 0.0)

    sig20, act20 = _breadth_signal_sma20(sma20)
    sig50, act50 = _breadth_signal_sma50(sma50)
    sig200, act200 = _breadth_signal_sma200(sma200)
    sig_nh, act_nh = _breadth_signal_nh_nl(nh_nl)
    sig_hl, act_hl = _hl_ratio_signal(hl_ratio)
    sig_vol, act_vol = _breadth_signal_volume(vol_ratio)
    sig_vix, act_vix = _vix_signal(vix)
    sig_term, act_term = _vix_term_signal(vix, vix_3m)
    sig_mco, act_mco = _mco_signal(mco)
    sig_atr, act_atr = _atr_signal(spy_atr_pct)
    
    trend_6m = ad_data.get("6M", {}).get("trend", "N/A")
    sig_ad, act_ad = _ad_line_signal(trend_6m)

    fg_signal = Signal.OVERBOUGHT if fg > 75 else (Signal.OVERSOLD if fg < 25 else Signal.NEUTRAL)
    fg_action = (
        "Reduce Longs / Tighten Stops" if fg > 75
        else "Look for Long Entries" if fg < 25
        else "Normal Exposure"
    )

    indicators = [
        BreadthIndicator("pct_sma20", sma20, sig20, act20, "pct_above_sma20_help", "trend"),
        BreadthIndicator("pct_sma50", sma50, sig50, act50, "pct_above_sma50_help", "trend"),
        BreadthIndicator("pct_sma200", sma200, sig200, act200, "pct_above_sma200_help", "trend"),
        BreadthIndicator("nh_nl_net", nh_nl, sig_nh, act_nh, "nh_nl_help", "internals"),
        BreadthIndicator("hl_index", hl_ratio, sig_hl, act_hl, "hl_index_desc", "internals"),
        BreadthIndicator("volume_breadth", vol_ratio, sig_vol, act_vol, "vol_breadth_help", "internals"),
        BreadthIndicator("mco", mco, sig_mco, act_mco, "mco_desc", "internals"),
        BreadthIndicator("ad_trend", trend_6m, sig_ad, act_ad, "ad_trend_help", "internals"),
        BreadthIndicator("fear_greed_score", fg, fg_signal, fg_action, "fg_indicator_desc", "risk"),
        BreadthIndicator("vix", vix, sig_vix, act_vix, "vix_help", "risk"),
        BreadthIndicator("vix_term_structure", f"{vix:.1f} vs {vix_3m:.1f}", sig_term, act_term, "vix_term_structure_desc", "risk"),
        BreadthIndicator("spy_atr", spy_atr_pct, sig_atr, act_atr, "spy_atr_help", "risk"),
    ]

    return MarketBreadth(
        pct_above_sma20=sma20,
        pct_above_sma50=sma50,
        pct_above_sma200=sma200,
        new_highs_lows=nh_nl,
        high_low_ratio=hl_ratio,
        volume_breadth_ratio=vol_ratio,
        fear_greed_score=fg,
        vix=vix,
        vix_3m=vix_3m,
        vix_6m=vix_6m,
        mcclellan_osc=mco,
        spy_atr_pct=spy_atr_pct,
        ad_data=ad_data,
        indicators=indicators,
    )


# ---------------------------------------------------------------------------
# Sector Rotation (TradingView + yfinance for multi-timeframe)
# ---------------------------------------------------------------------------
def _perf_at_offset(close: pd.Series, offset: int) -> float:
    if len(close) <= offset:
        return 0.0
    return (float(close.iloc[-1]) / float(close.iloc[-1 - offset]) - 1)


@st.cache_data(ttl=300)
def compute_sector_data() -> list[SectorData]:
    return dp.execute_managed_fetch(_compute_sector_data_logic)

def _compute_sector_data_logic() -> list[SectorData]:
    etfs = [s[1] for s in SECTORS]

    # TradingView for current price + SMA20
    tv_tickers = [f"AMEX:{e}" for e in etfs]
    payload = {
        "symbols": {"tickers": tv_tickers},
        "columns": ["close", "SMA20"],
    }
    try:
        data = dp.execute_managed_fetch(dp.fetch_tv_scan, payload)
        tv_data = {item["s"].split(":")[-1]: item["d"] for item in data.get("data", [])}
    except Exception:
        tv_data = {}

    # yfinance for multi-timeframe performance (11 ETFs, 1mo — fast)
    df = dp.execute_managed_fetch(dp.fetch_yf_data, etfs, period="1mo", interval="1d", group_by="ticker")
    perf_map: dict[str, dict[str, float]] = {}
    for etf in etfs:
        try:
            close = df[etf]["Close"].dropna()
            if isinstance(close, pd.DataFrame):
                close = close.iloc[:, 0]
            perf_map[etf] = {
                "day": _perf_at_offset(close, 1),
                "1w": _perf_at_offset(close, 5),
                "2w": _perf_at_offset(close, 10),
                "3w": _perf_at_offset(close, 15),
            }
        except (KeyError, IndexError):
            perf_map[etf] = {"day": 0, "1w": 0, "2w": 0, "3w": 0}

    results: list[SectorData] = []
    for name, etf in SECTORS:
        d = tv_data.get(etf)
        if d and d[0] is not None and d[1] is not None:
            price, sma20 = float(d[0]), float(d[1])
            pct = (price - sma20) / sma20 if sma20 else 0
        else:
            price = sma20 = pct = 0.0

        if pct > 0.03:
            sig = Signal.HOT
        elif pct < -0.03:
            sig = Signal.COLD
        else:
            sig = Signal.NEUTRAL

        p = perf_map.get(etf, {})
        results.append(SectorData(
            name=name, etf=etf,
            price=round(price, 2), sma20=round(sma20, 2),
            pct_vs_sma20=round(pct, 4), signal=sig,
            perf_day=round(p.get("day", 0), 4),
            perf_1w=round(p.get("1w", 0), 4),
            perf_2w=round(p.get("2w", 0), 4),
            perf_3w=round(p.get("3w", 0), 4),
        ))

    return results


# ---------------------------------------------------------------------------
# Seasonality (yfinance — 10yr weekly, per ticker)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def compute_seasonality(ticker: str) -> SeasonalityResult:
    return dp.execute_managed_fetch(_compute_seasonality_logic, ticker)

def _compute_seasonality_logic(ticker: str) -> SeasonalityResult:
    df = dp.fetch_yf_data(ticker, period="10y", interval="1wk", group_by="column")
    if df.empty:
        return SeasonalityResult(ticker=ticker)

    close = df["Close"].dropna()
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    returns = close.pct_change().dropna()
    ret_df = returns.to_frame(name="return")
    ret_df["month"] = ret_df.index.month
    ret_df["week"] = ret_df.index.isocalendar().week.astype(int)

    monthly: list[SeasonalityRow] = []
    for m in range(1, 13):
        subset = ret_df[ret_df["month"] == m]["return"]
        if len(subset) == 0:
            monthly.append(SeasonalityRow(m, calendar.month_abbr[m], 0, 0, 0, 0, 0))
            continue
        monthly.append(SeasonalityRow(
            period=m,
            label=calendar.month_abbr[m],
            avg_return=round(float(subset.mean()), 6),
            win_rate=round(float((subset > 0).sum() / len(subset)), 4),
            std_dev=round(float(subset.std()), 6),
            min_return=round(float(subset.min()), 6),
            max_return=round(float(subset.max()), 6),
        ))

    weekly: list[SeasonalityRow] = []
    for w in range(1, 53):
        subset = ret_df[ret_df["week"] == w]["return"]
        if len(subset) == 0:
            weekly.append(SeasonalityRow(w, f"W{w}", 0, 0, 0, 0, 0))
            continue
        weekly.append(SeasonalityRow(
            period=w,
            label=f"W{w}",
            avg_return=round(float(subset.mean()), 6),
            win_rate=round(float((subset > 0).sum() / len(subset)), 4),
            std_dev=round(float(subset.std()), 6),
            min_return=round(float(subset.min()), 6),
            max_return=round(float(subset.max()), 6),
        ))

    current_month = calendar.month_name[datetime.now().month]
    cm_data = monthly[datetime.now().month - 1]
    if cm_data.avg_return > 0.01:
        sig = Signal.BULLISH
    elif cm_data.avg_return < -0.01:
        sig = Signal.BEARISH
    else:
        sig = Signal.FLAT

    return SeasonalityResult(
        ticker=ticker,
        monthly=monthly,
        weekly=weekly,
        current_month=current_month,
        signal=sig,
    )


# ---------------------------------------------------------------------------
# Options Flow Analysis (yfinance — nearest expirations)
# ---------------------------------------------------------------------------
@st.cache_data(ttl=300)
def compute_options_flow(tickers: list[str], max_expirations: int = 1) -> pd.DataFrame:
    """
    Scans options chains to approximate Unusual Whales Net Premium logic.
    Bullish Flow = Calls bought at Ask + Puts sold at Bid
    Bearish Flow = Puts bought at Ask + Calls sold at Bid
    (Proxy uses lastPrice vs mid-price)
    """
    def _process_chain(df, is_call, recent_date_str):
        if df.empty: return 0.0, 0.0, 0, 0
        df = df.copy()
        df['tradeDateOnly'] = df['lastTradeDate'].dt.strftime('%Y-%m-%d')
        today_df = df[df['tradeDateOnly'] == recent_date_str].copy()
        if today_df.empty: return 0.0, 0.0, 0, 0
        
        today_df['mid'] = (today_df['bid'] + today_df['ask']) / 2
        today_df['prem'] = today_df['volume'].fillna(0) * today_df['lastPrice'].fillna(0) * 100
        
        bullish = 0.0
        bearish = 0.0
        vol = today_df['volume'].sum()
        oi = today_df['openInterest'].sum()
        
        for _, row in today_df.iterrows():
            if row['lastPrice'] > row['mid']:
                if is_call: bullish += row['prem']
                else: bearish += row['prem']
            elif row['lastPrice'] < row['mid']:
                if is_call: bearish += row['prem']
                else: bullish += row['prem']
                
        return bullish, bearish, vol, oi

    def _fetch_flow(sym):
        try:
            exps = dp.fetch_yf_options_expirations(sym)
            if not exps: return None
            
            total_bullish = 0.0
            total_bearish = 0.0
            total_vol = 0
            total_oi = 0
            
            for exp in exps[:max_expirations]:
                calls, puts = dp.fetch_yf_option_chain(sym, exp)
                
                recent_trade = None
                if not calls.empty:
                    recent_trade = calls['lastTradeDate'].max()
                if not puts.empty:
                    p_recent = puts['lastTradeDate'].max()
                    if recent_trade is None or p_recent > recent_trade:
                        recent_trade = p_recent
                        
                if recent_trade is None: continue
                recent_date_str = recent_trade.strftime('%Y-%m-%d')
                
                c_bull, c_bear, c_vol, c_oi = _process_chain(calls, True, recent_date_str)
                p_bull, p_bear, p_vol, p_oi = _process_chain(puts, False, recent_date_str)
                
                total_bullish += c_bull + p_bull
                total_bearish += c_bear + p_bear
                total_vol += c_vol + p_vol
                total_oi += c_oi + p_oi
                
            net_prem = total_bullish - total_bearish
            vol_oi_ratio = total_vol / total_oi if total_oi > 0 else 0
            
            return {
                "Ticker": sym, 
                "Net_Premium": net_prem,
                "Bullish_Premium": total_bullish,
                "Bearish_Premium": total_bearish,
                "Total_Volume": total_vol,
                "Total_OI": total_oi,
                "Vol_OI_Ratio": vol_oi_ratio
            }
        except Exception:
            return None

    results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=20) as executor:
        for res in executor.map(_fetch_flow, tickers):
            if res: results.append(res)
            
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values(by="Net_Premium", ascending=True)
    return df
