import yfinance as yf
import pandas as pd

tkr = yf.Ticker("AAPL")
chain = tkr.option_chain(tkr.options[0])

def process_chain(df, is_call):
    if df.empty: return 0.0, 0.0
    
    # filter to today
    recent_trade = df['lastTradeDate'].max()
    if pd.isna(recent_trade): return 0.0, 0.0
    recent_date_str = recent_trade.strftime('%Y-%m-%d')
    df['tradeDateOnly'] = df['lastTradeDate'].dt.strftime('%Y-%m-%d')
    today_df = df[df['tradeDateOnly'] == recent_date_str].copy()
    
    if today_df.empty: return 0.0, 0.0
    
    today_df['mid'] = (today_df['bid'] + today_df['ask']) / 2
    today_df['prem'] = today_df['volume'].fillna(0) * today_df['lastPrice'].fillna(0) * 100
    
    bullish = 0.0
    bearish = 0.0
    
    for _, row in today_df.iterrows():
        if row['lastPrice'] > row['mid']:
            if is_call: bullish += row['prem']
            else: bearish += row['prem']
        elif row['lastPrice'] < row['mid']:
            if is_call: bearish += row['prem']
            else: bullish += row['prem']
            
    return bullish, bearish

c_bull, c_bear = process_chain(chain.calls, True)
p_bull, p_bear = process_chain(chain.puts, False)

bullish_total = c_bull + p_bull
bearish_total = c_bear + p_bear
net_prem = bullish_total - bearish_total

print(f"Bullish: ${bullish_total/1e6:.1f}M")
print(f"Bearish: ${bearish_total/1e6:.1f}M")
print(f"Net Prem: ${net_prem/1e6:.1f}M")
