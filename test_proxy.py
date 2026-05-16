import yfinance as yf
import pandas as pd
from datetime import datetime

tkr = yf.Ticker("AAPL")
exps = tkr.options
chain = tkr.option_chain(exps[0])
calls = chain.calls

# filter to today
recent_trade = calls['lastTradeDate'].max()
recent_date_str = recent_trade.strftime('%Y-%m-%d')
calls['tradeDateOnly'] = calls['lastTradeDate'].dt.strftime('%Y-%m-%d')
today_calls = calls[calls['tradeDateOnly'] == recent_date_str].copy()

today_calls['mid'] = (today_calls['bid'] + today_calls['ask']) / 2
today_calls['proxy_side'] = today_calls.apply(
    lambda row: "Ask" if row['lastPrice'] >= row['mid'] else "Bid", axis=1
)

print(today_calls[['strike', 'lastPrice', 'mid', 'proxy_side', 'volume']].head(10))
