from fastapi import FastAPI
from fastapi.responses import FileResponse
import yfinance as yf

app = FastAPI()

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/api/candles/{symbol}")
def get_candles(symbol: str):
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="6mo", interval="1d")
    candles = []
    for index, row in df.iterrows():
        candles.append({
            "time": index.strftime('%Y-%m-%d'),
            "open": round(float(row['Open']), 2),
            "high": round(float(row['High']), 2),
            "low": round(float(row['Low']), 2),
            "close": round(float(row['Close']), 2),
        })
    return candles
