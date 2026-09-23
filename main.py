from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import yfinance as yf

app = FastAPI()

PAGE = """@app.get("/", response_class=HTMLResponse)
def home():
return PAGE

@app.get("/api/candles/{symbol}")
def get_candles(symbol: str):
ticker = yf.Ticker(symbol)
df = ticker.history(period="1mo", interval="1d")
candles = []
for idx, row in df.iterrows():
candles.append({
"time": idx.strftime("%Y-%m-%d"),
"open": round(float(row["Open"]), 2),
"high": round(float(row["High"]), 2),
"low": round(float(row["Low"]), 2),
"close": round(float(row["Close"]), 2)
})
return candles
