from fastapi import FastAPI
from fastapi.responses import FileResponse
import yfinance as yf

app = FastAPI()

@app.get("/")
def home():
    return FileResponse("index.html")

@app.get("/api/c/{sym}")
def get_c(sym: str):
    df = yf.Ticker(sym).history(period="6mo", interval="1d")
    candles = []
    for idx, r in df.iterrows():
        candles.append({
            "time": idx.strftime("%Y-%m-%d"),
            "open": round(float(r["Open"]), 2),
            "high": round(float(r["High"]), 2),
            "low": round(float(r["Low"]), 2),
            "close": round(float(r["Close"]), 2)
        })
    return candles
