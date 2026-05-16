import pandas as pd
from data import compute_options_flow, get_nasdaq100_tickers

tickers = get_nasdaq100_tickers()
df = compute_options_flow(tickers, max_expirations=1)
if not df.empty:
    print(df.nlargest(10, 'Total_Volume')[['Ticker', 'Total_Volume', 'Net_Premium']])
else:
    print("No data")
