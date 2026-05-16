import yfinance as yf
import pandas as pd
import time
from data import get_sp500_tickers

tickers = get_sp500_tickers()
start = time.time()
df = yf.download(tickers, period="2y", interval="1d", progress=False)
print(f"Time: {time.time() - start:.2f}s")

highs = df['High']
lows = df['Low']

# Calculate 52-week (252 trading days) rolling high and low
rolling_high = highs.rolling(window=252).max()
rolling_low = lows.rolling(window=252).min()

# A stock hits a new 52-week high if its current high is >= its 252-day rolling high
# A stock hits a new 52-week low if its current low is <= its 252-day rolling low
new_highs = (highs >= rolling_high).sum(axis=1)
new_lows = (lows <= rolling_low).sum(axis=1)

# Record High Percent
rhp = (new_highs / (new_highs + new_lows)) * 100
rhp = rhp.fillna(50) # If both 0, default to 50

# High-Low Index = 10-day SMA of RHP
hl_index = rhp.rolling(window=10).mean()

print(f"Current HL Index: {hl_index.iloc[-1]:.2f}")
print(f"Current Daily RHP: {rhp.iloc[-1]:.2f}")
print(f"Current NH: {new_highs.iloc[-1]}, NL: {new_lows.iloc[-1]}")
