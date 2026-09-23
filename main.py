from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import yfinance as yf
import pandas as pd
import numpy as np

app = FastAPI(title="Professional Trading Platform")


# =========================================================
# SYMBOLS
# =========================================================

ALLOWED_SYMBOLS = {
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
}


# =========================================================
# TIMEFRAME SETTINGS
# =========================================================

INTERVAL_SETTINGS = {
    "1d": {
        "period": "1mo",
        "interval": "1d"
    },
    "1h": {
        "period": "1mo",
        "interval": "1h"
    },
    "15m": {
        "period": "5d",
        "interval": "15m"
    },
    "5m": {
        "period": "5d",
        "interval": "5m"
    },
}


# =========================================================
# HOME
# =========================================================

@app.get("/")
async def root():
    return FileResponse("index.html")


# =========================================================
# EMA
# =========================================================

def calculate_ema(series, period):
    return series.ewm(
        span=period,
        adjust=False
    ).mean()


# =========================================================
# SMA
# =========================================================

def calculate_sma(series, period):
    return series.rolling(
        window=period
    ).mean()


# =========================================================
# RSI
# =========================================================

def calculate_rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(lower=0)

    loss = -delta.clip(upper=0)

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    rs = avg_gain / avg_loss.replace(
        0,
        np.nan
    )

    rsi = 100 - (
        100 / (1 + rs)
    )

    return rsi.fillna(50)


# =========================================================
# VWAP
# =========================================================

def calculate_vwap(data):

    typical_price = (
        data["High"]
        + data["Low"]
        + data["Close"]
    ) / 3

    volume = data["Volume"].fillna(0)

    cumulative_pv = (
        typical_price * volume
    ).cumsum()

    cumulative_volume = (
        volume.cumsum()
    )

    vwap = (
        cumulative_pv
        / cumulative_volume.replace(
            0,
            np.nan
        )
    )

    return vwap.fillna(
        data["Close"]
    )


# =========================================================
# ATR
# =========================================================

def calculate_atr(data, period=14):

    previous_close = data["Close"].shift(1)

    tr1 = (
        data["High"]
        - data["Low"]
    )

    tr2 = (
        data["High"]
        - previous_close
    ).abs()

    tr3 = (
        data["Low"]
        - previous_close
    ).abs()

    true_range = pd.concat(
        [tr1, tr2, tr3],
        axis=1
    ).max(axis=1)

    atr = true_range.rolling(
        period
    ).mean()

    return atr


# =========================================================
# CANDLE API
# =========================================================

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

            try:

                open_price = float(row["Open"])
                high_price = float(row["High"])
                low_price = float(row["Low"])
                close_price = float(row["Close"])

            except (
                TypeError,
                ValueError
            ):
                continue

            if not all(
                np.isfinite([
                    open_price,
                    high_price,
                    low_price,
                    close_price
                ])
            ):
                continue

            volume = row.get(
                "Volume",
                0
            )

            if pd.isna(volume):
                volume = 0

            if interval == "1d":

                time_value = index.strftime(
                    "%Y-%m-%d"
                )

            else:

                time_value = int(
                    index.timestamp()
                )

            candles.append({

                "time": time_value,

                "open": open_price,

                "high": high_price,

                "low": low_price,

                "close": close_price,

                "volume": int(volume)

            })

        return candles

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Market data error: {str(exc)}"
        )


# =========================================================
# SMART SIGNAL API
# =========================================================

@app.get("/api/signal/{symbol}")
async def get_signal(
    symbol: str,
    interval: str = "5m"
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

        data = data.dropna(
            subset=[
                "Open",
                "High",
                "Low",
                "Close"
            ]
        )

        if len(data) < 50:

            raise HTTPException(
                status_code=400,
                detail="Not enough market data for signal"
            )

        # -------------------------------------------------
        # INDICATORS
        # -------------------------------------------------

        data["EMA20"] = calculate_ema(
            data["Close"],
            20
        )

        data["EMA50"] = calculate_ema(
            data["Close"],
            50
        )

        data["RSI"] = calculate_rsi(
            data["Close"],
            14
        )

        data["VWAP"] = calculate_vwap(
            data
        )

        data["ATR"] = calculate_atr(
            data,
            14
        )

        data["AVG_VOLUME"] = (
            data["Volume"]
            .rolling(20)
            .mean()
        )

        latest = data.iloc[-1]

        price = float(
            latest["Close"]
        )

        ema20 = float(
            latest["EMA20"]
        )

        ema50 = float(
            latest["EMA50"]
        )

        rsi = float(
            latest["RSI"]
        )

        vwap = float(
            latest["VWAP"]
        )

        volume = float(
            latest["Volume"]
        )

        average_volume = float(
            latest["AVG_VOLUME"]
        ) if not pd.isna(
            latest["AVG_VOLUME"]
        ) else volume

        atr = float(
            latest["ATR"]
        ) if not pd.isna(
            latest["ATR"]
        ) else price * 0.01

        # -------------------------------------------------
        # SCORE
        # -------------------------------------------------

        buy_score = 0
        sell_score = 0

        reasons = []

        # 1. PRICE vs EMA20

        if price > ema20:

            buy_score += 1

            reasons.append(
                "Price is above EMA20 → bullish"
            )

        else:

            sell_score += 1

            reasons.append(
                "Price is below EMA20 → bearish"
            )

        # 2. EMA20 vs EMA50

        if ema20 > ema50:

            buy_score += 1

            reasons.append(
                "EMA20 is above EMA50 → bullish trend"
            )

        else:

            sell_score += 1

            reasons.append(
                "EMA20 is below EMA50 → bearish trend"
            )

        # 3. RSI

        if rsi >= 50 and rsi < 70:

            buy_score += 1

            reasons.append(
                f"RSI {rsi:.1f} → bullish momentum"
            )

        elif rsi < 50:

            sell_score += 1

            reasons.append(
                f"RSI {rsi:.1f} → weak momentum"
            )

        elif rsi >= 70:

            reasons.append(
                f"RSI {rsi:.1f} → overbought zone"
            )

        # 4. VWAP

        if price > vwap:

            buy_score += 1

            reasons.append(
                "Price is above VWAP → bullish"
            )

        else:

            sell_score += 1

            reasons.append(
                "Price is below VWAP → bearish"
            )

        # 5. VOLUME

        if volume > average_volume:

            if price > ema20:

                buy_score += 1

                reasons.append(
                    "Volume is above average with bullish price action"
                )

            else:

                sell_score += 1

                reasons.append(
                    "Volume is above average with bearish price action"
                )

        else:

            reasons.append(
                "Volume is below average"
            )

        # -------------------------------------------------
        # FINAL SIGNAL
        # -------------------------------------------------

        if buy_score >= 4:

            signal = "BUY"

        elif sell_score >= 4:

            signal = "SELL"

        else:

            signal = "NEUTRAL"

        # -------------------------------------------------
        # ENTRY / SL / TARGETS
        # -------------------------------------------------

        entry = round(
            price,
            2
        )

        stop_loss = None
        target1 = None
        target2 = None

        if signal == "BUY":

            stop_loss = round(
                entry - (1.5 * atr),
                2
            )

            target1 = round(
                entry + (2 * atr),
                2
            )

            target2 = round(
                entry + (3 * atr),
                2
            )

        elif signal == "SELL":

            stop_loss = round(
                entry + (1.5 * atr),
                2
            )

            target1 = round(
                entry - (2 * atr),
                2
            )

            target2 = round(
                entry - (3 * atr),
                2
            )

        # -------------------------------------------------
        # RESPONSE
        # -------------------------------------------------

        return {

            "symbol": symbol,

            "interval": interval,

            "signal": signal,

            "score": max(
                buy_score,
                sell_score
            ),

            "max_score": 5,

            "buy_score": buy_score,

            "sell_score": sell_score,

            "entry": entry,

            "stop_loss": stop_loss,

            "target1": target1,

            "target2": target2,

            "indicators": {

                "ema20": round(
                    ema20,
                    2
                ),

                "ema50": round(
                    ema50,
                    2
                ),

                "rsi": round(
                    rsi,
                    2
                ),

                "vwap": round(
                    vwap,
                    2
                ),

                "volume": int(
                    volume
                ),

                "average_volume": int(
                    average_volume
                )

            },

            "reasons": reasons

        }

    except HTTPException:

        raise

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Signal calculation error: {str(exc)}"
        )


# =========================================================
# RUN SERVER
# =========================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )
