import yfinance as yf
import pandas as pd
from datetime import datetime, timezone, timedelta

tkr = yf.Ticker("AAPL")
exps = tkr.options
if exps:
    chain = tkr.option_chain(exps[0])
    calls = chain.calls
    
    # Get the most recent trading date from the options chain itself
    recent_trade = calls['lastTradeDate'].max()
    print(f"Most recent trade in this chain: {recent_trade}")
    
    recent_date_str = recent_trade.strftime('%Y-%m-%d')
    calls['tradeDateOnly'] = calls['lastTradeDate'].dt.strftime('%Y-%m-%d')
    today_calls = calls[calls['tradeDateOnly'] == recent_date_str]
    
    print(f"\nCalls traded on {recent_date_str}: {len(today_calls)} / {len(calls)}")
    print(today_calls[['contractSymbol', 'lastTradeDate', 'volume']].head())
