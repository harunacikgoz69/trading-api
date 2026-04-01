from tradingagents.dataflows.stockstats_utils import load_ohlcv 
data = load_ohlcv('THYAO.IS', '2026-04-01') 
print('Rows:', len(data)) 
print(data.tail(3)) 
