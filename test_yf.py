import yfinance as yf
import time
from concurrent.futures import ThreadPoolExecutor

tickers = ["AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "BRK-B", "TSLA", "UNH", "JPM"] * 5

def fetch(sym):
    try:
        tkr = yf.Ticker(sym)
        exps = tkr.options
        if exps:
            chain = tkr.option_chain(exps[0])
            return 1
    except:
        pass
    return 0

start = time.time()
with ThreadPoolExecutor(max_workers=20) as executor:
    results = list(executor.map(fetch, tickers))
print(f"Time: {time.time() - start:.2f}s, successes: {sum(results)}/{len(tickers)}")
