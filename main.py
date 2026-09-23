from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import yfinance as yf
import pandas as pd

app = FastAPI(title="TradePro Trading Platform")

ALLOWED_SYMBOLS = {
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
    "HDFCBANK.NS",
    "TATAMOTORS.NS",
    "^NSEI",      # NIFTY 50
    "^NSEBANK",   # BANK NIFTY
    "^BSESN"      # SENSEX
}

INTERVAL_SETTINGS = {
    "1m": {"period": "5d", "interval": "1m"},
    "5m": {"period": "5d", "interval": "5m"},
    "15m": {"period": "1mo", "interval": "15m"},
    "30m": {"period": "1mo", "interval": "30m"},
    "1h": {"period": "3mo", "interval": "1h"},
    "4h": {"period": "3mo", "interval": "1h"},
    "1d": {"period": "1y", "interval": "1d"}
}

@app.get("/")
async def root():
    return FileResponse("index.html")

@app.get("/api/candles/{symbol}")
async def get_candles(symbol: str, interval: str = "5m"):
    clean_symbol = symbol.strip()
    if clean_symbol not in ALLOWED_SYMBOLS and clean_symbol.upper() not in ALLOWED_SYMBOLS:
        clean_symbol = clean_symbol.upper()
        if clean_symbol not in ALLOWED_SYMBOLS:
            raise HTTPException(status_code=400, detail="Invalid symbol")
    else:
        if clean_symbol in ALLOWED_SYMBOLS:
            pass
        else:
            clean_symbol = clean_symbol.upper()

    if interval not in INTERVAL_SETTINGS:
        raise HTTPException(status_code=400, detail="Invalid interval")

    settings = INTERVAL_SETTINGS[interval]

    try:
        ticker = yf.Ticker(clean_symbol)
        data = ticker.history(
            period=settings["period"],
            interval=settings["interval"],
            auto_adjust=False
        )

        if data.empty:
            raise HTTPException(status_code=404, detail="No market data found")

        # 4H Candle Handling
        if interval == "4h":
            data = data.copy()
            data = data.resample("4h").agg({
                "Open": "first",
                "High": "max",
                "Low": "min",
                "Close": "last",
                "Volume": "sum"
            }).dropna()

        candles = []
        for index, row in data.iterrows():
            if pd.isna(row["Open"]) or pd.isna(row["High"]) or pd.isna(row["Low"]) or pd.isna(row["Close"]):
                continue

            time_value = index.strftime("%Y-%m-%d") if interval == "1d" else int(index.timestamp())
            volume = 0 if pd.isna(row["Volume"]) else int(row["Volume"])

            candles.append({
                "time": time_value,
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": volume
            })

        if not candles:
            raise HTTPException(status_code=404, detail="No valid candle data found")

        return candles

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Market data error: {str(exc)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000)
