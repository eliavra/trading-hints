import yfinance as yf
import pandas as pd
from datetime import datetime, timezone, timedelta

tkr = yf.Ticker("AAPL")
exps = tkr.options
chain = tkr.option_chain(exps[0])
calls = chain.calls
recent_trade = calls['lastTradeDate'].max()
recent_date_str = recent_trade.strftime('%Y-%m-%d')
calls['tradeDateOnly'] = calls['lastTradeDate'].dt.strftime('%Y-%m-%d')
today_calls = calls[calls['tradeDateOnly'] == recent_date_str]

vol = today_calls['volume'].sum()
oi = today_calls['openInterest'].sum()
print(f"Volume: {vol}, OI: {oi}, Ratio: {vol/oi if oi else 0}")
