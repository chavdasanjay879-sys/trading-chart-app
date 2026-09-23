from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import yfinance as yf

app = FastAPI()


@app.get("/")
async def root():
    return FileResponse("index.html")


@app.get("/api/candles/{symbol}")
async def get_candles(symbol: str):
    allowed_symbols = {
        "RELIANCE.NS",
        "TCS.NS",
        "INFY.NS",
    }

    if symbol not in allowed_symbols:
        raise HTTPException(status_code=400, detail="Invalid symbol")

    try:
        ticker = yf.Ticker(symbol)
        data = ticker.history(period="1mo", interval="1d", auto_adjust=False)

        if data.empty:
            raise HTTPException(
                status_code=404,
                detail="No candle data found for the selected symbol",
            )

        candles = []

        for index, row in data.iterrows():
            candles.append(
                {
                    "time": index.strftime("%Y-%m-%d"),
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": float(row["Close"]),
                }
            )

        return candles

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch candle data: {str(exc)}",
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
