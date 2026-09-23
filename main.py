from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
import yfinance as yf
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
def serve_home(request: Request):
    """ચાર્ટનું મુખ્ય HTML પેજ ખોલશે"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/candles/{symbol}")
def get_candles(symbol: str, timeframe: str = "1d"):
    """
    Yahoo Finance પરથી સ્ટોકનો ડેટા લાવીને
    TradingView લાઈબ્રેરીના ફોર્મેટ મુજબ (time, open, high, low, close) મોકલશે.
    ઉદાહરણ: RELIANCE.NS, NIFTY50.NS, TCS.NS
    """
    # 6 મહિનાનો ડેટા ડાઉનલોડ કરીએ
    ticker = yf.Ticker(symbol)
    df = ticker.history(period="6mo", interval=timeframe)

    candles = []
    for index, row in df.iterrows():
        # તારીખને YYYY-MM-DD ફોર્મેટમાં ફેરવો
        date_str = index.strftime('%Y-%m-%d')
        candles.append({
            "time": date_str,
            "open": round(float(row['Open']), 2),
            "high": round(float(row['High']), 2),
            "low": round(float(row['Low']), 2),
            "close": round(float(row['Close']), 2),
            "volume": int(row['Volume'])
        })

    return candles
