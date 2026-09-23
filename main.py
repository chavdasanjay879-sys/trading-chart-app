from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import yfinance as yf
import pandas as pd
import numpy as np


app = FastAPI(title="Professional Trading Platform")


# ============================================================
# ALLOWED SYMBOLS
# ============================================================

ALLOWED_SYMBOLS = {
    "RELIANCE.NS",
    "TCS.NS",
    "INFY.NS",
}


# ============================================================
# INTERVAL SETTINGS
# ============================================================

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


# ============================================================
# HOME
# ============================================================

@app.get("/")
async def root():

    return FileResponse("index.html")


# ============================================================
# GET CANDLES
# ============================================================

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

            except:

                continue


            if not all(
                np.isfinite(x)
                for x in [
                    open_price,
                    high_price,
                    low_price,
                    close_price
                ]
            ):

                continue


            if interval == "1d":

                time_value = index.strftime(
                    "%Y-%m-%d"
                )

            else:

                time_value = int(
                    index.timestamp()
                )


            volume_value = 0


            try:

                if pd.notna(row["Volume"]):

                    volume_value = int(
                        row["Volume"]
                    )

            except:

                volume_value = 0


            candles.append({

                "time": time_value,

                "open": open_price,

                "high": high_price,

                "low": low_price,

                "close": close_price,

                "volume": volume_value

            })


        return candles


    except HTTPException:

        raise


    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=f"Market data error: {str(exc)}"
        )


# ============================================================
# INDICATOR FUNCTIONS
# ============================================================

def calculate_ema(series, period):

    return series.ewm(
        span=period,
        adjust=False
    ).mean()


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


def calculate_vwap(data):

    typical_price = (
        data["High"] +
        data["Low"] +
        data["Close"]
    ) / 3


    volume = data["Volume"].fillna(0)


    cumulative_pv = (
        typical_price * volume
    ).cumsum()


    cumulative_volume = (
        volume.cumsum()
    )


    vwap = (
        cumulative_pv /
        cumulative_volume.replace(
            0,
            np.nan
        )
    )


    return vwap.fillna(
        data["Close"]
    )


# ============================================================
# SIGNAL ENGINE
# ============================================================

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


        if len(data) < 50:

            return {

                "symbol": symbol,

                "interval": interval,

                "signal": "NEUTRAL",

                "score": 0,

                "max_score": 5,

                "entry": None,

                "stop_loss": None,

                "target1": None,

                "target2": None,

                "reasons": [
                    "Not enough market data"
                ]

            }


        # ====================================================
        # INDICATORS
        # ====================================================

        close = data["Close"]


        ema20 = calculate_ema(
            close,
            20
        )


        ema50 = calculate_ema(
            close,
            50
        )


        rsi = calculate_rsi(
            close,
            14
        )


        vwap = calculate_vwap(
            data
        )


        latest_close = float(
            close.iloc[-1]
        )


        latest_ema20 = float(
            ema20.iloc[-1]
        )


        latest_ema50 = float(
            ema50.iloc[-1]
        )


        latest_rsi = float(
            rsi.iloc[-1]
        )


        latest_vwap = float(
            vwap.iloc[-1]
        )


        latest_volume = float(
            data["Volume"].iloc[-1]
        )


        avg_volume = float(
            data["Volume"]
            .rolling(20)
            .mean()
            .iloc[-1]
        )


        # ====================================================
        # SIGNAL SCORE
        # ====================================================

        buy_score = 0

        sell_score = 0

        reasons = []


        # ----------------------------------------------------
        # 1. PRICE VS EMA20
        # ----------------------------------------------------

        if latest_close > latest_ema20:

            buy_score += 1

            reasons.append(
                "Price above EMA 20"
            )

        else:

            sell_score += 1

            reasons.append(
                "Price below EMA 20"
            )


        # ----------------------------------------------------
        # 2. EMA20 VS EMA50
        # ----------------------------------------------------

        if latest_ema20 > latest_ema50:

            buy_score += 1

            reasons.append(
                "EMA 20 above EMA 50"
            )

        else:

            sell_score += 1

            reasons.append(
                "EMA 20 below EMA 50"
            )


        # ----------------------------------------------------
        # 3. RSI
        # ----------------------------------------------------

        if latest_rsi >= 50 and latest_rsi < 70:

            buy_score += 1

            reasons.append(
                f"RSI bullish ({latest_rsi:.1f})"
            )

        elif latest_rsi < 50:

            sell_score += 1

            reasons.append(
                f"RSI bearish ({latest_rsi:.1f})"
            )

        else:

            reasons.append(
                f"RSI high ({latest_rsi:.1f})"
            )


        # ----------------------------------------------------
        # 4. VWAP
        # ----------------------------------------------------

        if latest_close > latest_vwap:

            buy_score += 1

            reasons.append(
                "Price above VWAP"
            )

        else:

            sell_score += 1

            reasons.append(
                "Price below VWAP"
            )


        # ----------------------------------------------------
        # 5. VOLUME
        # ----------------------------------------------------

        if (
            avg_volume > 0
            and latest_volume > avg_volume
        ):

            if latest_close >= latest_ema20:

                buy_score += 1

                reasons.append(
                    "Volume confirmation"
                )

            else:

                sell_score += 1

                reasons.append(
                    "Volume confirms weakness"
                )

        else:

            reasons.append(
                "Volume confirmation weak"
            )


        # ====================================================
        # FINAL SIGNAL
        # ====================================================

        if buy_score >= 4:

            signal = "BUY"

        elif sell_score >= 4:

            signal = "SELL"

        else:

            signal = "NEUTRAL"


        # ====================================================
        # ENTRY / SL / TARGET
        # ====================================================

        entry = round(
            latest_close,
            2
        )


        atr_high = data["High"].diff()

        atr_low = data["Low"].diff().abs()

        atr_close = data["Close"].diff().abs()


        true_range = pd.concat(
            [
                data["High"] - data["Low"],
                atr_high.abs(),
                atr_low.abs()
            ],
            axis=1
        ).max(axis=1)


        atr = float(
            true_range
            .rolling(14)
            .mean()
            .iloc[-1]
        )


        if not np.isfinite(atr) or atr <= 0:

            atr = entry * 0.01


        if signal == "BUY":

            stop_loss = entry - (
                atr * 1.5
            )

            target1 = entry + (
                atr * 2
            )

            target2 = entry + (
                atr * 3
            )


        elif signal == "SELL":

            stop_loss = entry + (
                atr * 1.5
            )

            target1 = entry - (
                atr * 2
            )

            target2 = entry - (
                atr * 3
            )


        else:

            stop_loss = None

            target1 = None

            target2 = None


        # ====================================================
        # RESPONSE
        # ====================================================

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

            "stop_loss": (
                round(stop_loss, 2)
                if stop_loss is not None
                else None
            ),

            "target1": (
                round(target1, 2)
                if target1 is not None
                else None
            ),

            "target2": (
                round(target2, 2)
                if target2 is not None
                else None
            ),

            "indicators": {

                "ema20": round(
                    latest_ema20,
                    2
                ),

                "ema50": round(
                    latest_ema50,
                    2
                ),

                "rsi": round(
                    latest_rsi,
                    2
                ),

                "vwap": round(
                    latest_vwap,
                    2
                ),

                "volume": int(
                    latest_volume
                ),

                "average_volume": int(
                    avg_volume
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


# ============================================================
# START SERVER
# ============================================================

if __name__ == "__main__":

    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000
    )
