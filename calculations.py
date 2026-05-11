import pandas as pd
import numpy as np
from typing import Dict, Any

def normalize(val: float, min_val: float, max_val: float) -> float:
    """Linearly normalizes a value between min/max into a 0-100 score."""
    if val <= min_val: return 0.0
    if val >= max_val: return 100.0
    return ((val - min_val) / (max_val - min_val)) * 100.0

def compute_breadth_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculates S&P 500 breadth metrics from TradingView snapshot."""
    if df.empty:
        return {}

    total = len(df)
    sma20_pct = (df['close'] > df['sma20']).sum() / total * 100
    sma50_pct = (df['close'] > df['sma50']).sum() / total * 100
    sma200_pct = (df['close'] > df['sma200']).sum() / total * 100
    
    # NH-NL (Net New Highs/Lows)
    # TradingView 'high_52_week' is the current 52w high value. 
    # To check if it's hitting it "today", we check if Close >= High.
    new_highs = (df['close'] >= df['hi52']).sum()
    new_lows = (df['close'] <= df['lo52']).sum()
    nh_nl = int(new_highs - new_lows)
    
    # Volume Breadth
    advancing_vol = df[df['change'] > 0]['volume'].sum()
    declining_vol = df[df['change'] < 0]['volume'].sum()
    vol_ratio = advancing_vol / declining_vol if declining_vol > 0 else 1.0
    
    return {
        'sma20_pct': sma20_pct,
        'sma50_pct': sma50_pct,
        'sma200_pct': sma200_pct,
        'nh_nl': nh_nl,
        'vol_ratio': vol_ratio,
        'new_highs': int(new_highs),
        'new_lows': int(new_lows)
    }

def compute_fear_greed_score(metrics: Dict[str, Any]) -> float:
    """
    Custom composite sentiment indicator (0-100).
    Weights: 25% SMA20, 25% SMA50, 20% SMA200, 15% NH-NL, 15% Vol Breadth.
    """
    if not metrics:
        return 50.0
    
    s20 = normalize(metrics['sma20_pct'], 20, 85)
    s50 = normalize(metrics['sma50_pct'], 30, 85)
    s200 = normalize(metrics['sma200_pct'], 40, 80)
    s_nhnl = normalize(metrics['nh_nl'], -50, 50)
    s_vol = normalize(metrics['vol_ratio'], 0.5, 1.5)
    
    score = (s20 * 0.25) + (s50 * 0.25) + (s200 * 0.20) + (s_nhnl * 0.15) + (s_vol * 0.15)
    return round(score, 1)

def compute_ad_line(df_history: pd.DataFrame) -> pd.DataFrame:
    """Calculates Cumulative Advance/Decline Line and its 10-day SMA."""
    if df_history.empty:
        return pd.DataFrame()
    
    # Daily Net Advances: Count(Close > Prev Close) - Count(Close < Prev Close)
    daily_returns = df_history.pct_change()
    net_advances = (daily_returns > 0).sum(axis=1) - (daily_returns < 0).sum(axis=1)
    
    ad_line = net_advances.cumsum()
    ad_sma = ad_line.rolling(window=10).mean()
    
    res = pd.DataFrame({
        'ad_line': ad_line,
        'ad_sma': ad_sma
    }).dropna()
    return res

def compute_sector_metrics(df_tv: pd.DataFrame, df_hist: pd.DataFrame) -> pd.DataFrame:
    """Calculates rotation metrics for 11 Sector ETFs."""
    # This expects df_tv to contain the 11 sector tickers specifically
    # but our main fetch_tv_breadth_data gets S&P stocks.
    # For Sectors, we can calculate performance from df_hist.
    
    if df_hist.empty:
        return pd.DataFrame()
    
    latest_prices = df_hist.iloc[-1]
    
    # Distance from SMA 20 (approximate from daily history)
    sma20 = df_hist.rolling(window=20).mean().iloc[-1]
    dist_sma20 = (latest_prices - sma20) / sma20 * 100
    
    # Historical Performance
    perf_1d = (latest_prices / df_hist.shift(1).iloc[-1] - 1) * 100
    perf_1w = (latest_prices / df_hist.shift(5).iloc[-1] - 1) * 100
    perf_2w = (latest_prices / df_hist.shift(10).iloc[-1] - 1) * 100
    perf_3w = (latest_prices / df_hist.shift(15).iloc[-1] - 1) * 100
    
    metrics = pd.DataFrame({
        'Price': latest_prices,
        'Dist SMA20 %': dist_sma20,
        '1D %': perf_1d,
        '1W %': perf_1w,
        '2W %': perf_2w,
        '3W %': perf_3w
    })
    
    # Add Heat Flags
    metrics['Status'] = metrics['Dist SMA20 %'].apply(lambda x: "HOT" if x > 3 else ("COLD" if x < -3 else "Neutral"))
    
    return metrics

def compute_seasonality(df_hist: pd.DataFrame) -> Dict[str, pd.DataFrame]:
    """Calculates weekly and monthly seasonality statistics."""
    if df_hist.empty:
        return {}
    
    # Calculate weekly returns
    df = df_hist.copy()
    df.columns = ['Close']
    df['Return'] = df['Close'].pct_change()
    df = df.dropna()
    
    df['Month'] = df.index.month
    df['Week'] = df.index.isocalendar().week
    
    # Monthly Seasonality
    monthly = df.groupby('Month')['Return'].agg([
        ('Avg Return', lambda x: x.mean() * 100),
        ('Win Rate', lambda x: (x > 0).sum() / len(x) * 100),
        ('Std Dev', lambda x: x.std() * 100),
        ('Min', lambda x: x.min() * 100),
        ('Max', lambda x: x.max() * 100)
    ])
    
    # Weekly Seasonality
    weekly = df.groupby('Week')['Return'].agg([
        ('Avg Return', lambda x: x.mean() * 100),
        ('Win Rate', lambda x: (x > 0).sum() / len(x) * 100)
    ])
    
    return {'monthly': monthly, 'weekly': weekly}
