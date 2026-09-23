from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import yfinance as yf

app = FastAPI(title="Professional Trading Platform")


ALLOWED_SYMBOLS = {
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
}


INTERVAL_SETTINGS = {
    "1d": {
        "period": "1mo",
        "interval": "1d",
    },
    "1h": {
        "period": "1mo",
        "interval": "1h",
    },
    "15m": {
        "period": "5d",
        "interval": "15m",
    },
    "5m": {
        "period": "5d",
        "interval": "5m",
    },
}


@app.get("/")
async def root():
    return FileResponse("index.html")


@app.get("/api/candles/{symbol}")
async def get_candles(
    symbol: str,
    interval: str = "1d"
):
    symbol = symbol.upper()

    if symbol not in ALLOWED_SYMBOLS:
        raise HTTPException(
            status_code=400,
            detail="Invalid symbol"
        )

    if interval not in INTERVAL_SETTINGS:
        raise HTTPException(
            status_code=400,
            detail="Invalid interval"
        )

    settings = INTERVAL_SETTINGS[interval]

    try:
        ticker = yf.Ticker(symbol)

        data = ticker.history(
            period=settings["period"],
            interval=settings["interval"],
            auto_adjust=False
        )

        if data.empty:
            raise HTTPException(
                status_code=404,
                detail="No market data found"
            )

        candles = []

        for index, row in data.iterrows():

            if (
                row["Open"] is None
                or row["High"] is None
                or row["Low"] is None
                or row["Close"] is None
            ):
                continue

            if interval == "1d":
                time_value = index.strftime("%Y-%m-%d")
            else:
                time_value = int(index.timestamp())

            candles.append({
                "time": time_value,
                "open": float(row["Open"]),
                "high": float(row["High"]),
                "low": float(row["Low"]),
                "close": float(row["Close"]),
                "volume": int(row["Volume"]) if row["Volume"] else 0
            })

        return candles

    except HTTPException:
        raise

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Market data error: {str(exc)}"
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000
    )
