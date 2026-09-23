from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import yfinance as yf
import pandas as pd
import numpy as np
import uvicorn
import json
import math

app = FastAPI(title="Professional Trading Platform")


# ============================================================
# CONFIGURATION
# ============================================================

SYMBOLS = {
    "RELIANCE.NS": "RELIANCE",
    "TCS.NS": "TCS",
    "INFY.NS": "INFY",
}

TIMEFRAMES = {
    "5m": {
        "period": "5d",
        "interval": "5m",
    },
    "15m": {
        "period": "5d",
        "interval": "15m",
    },
    "1h": {
        "period": "1mo",
        "interval": "1h",
    },
    "1d": {
        "period": "1y",
        "interval": "1d",
    },
}


# ============================================================
# HTML FRONTEND
# ============================================================

HTML = r"""
<!DOCTYPE html>

<html>

<head>

<meta charset="UTF-8">

<meta name="viewport"
      content="width=device-width, initial-scale=1.0">

<title>Professional Trading Platform</title>

<script src="https://unpkg.com/lightweight-charts@4.1.3/dist/lightweight-charts.standalone.production.js"></script>

<style>

*{
    box-sizing:border-box;
}

html,body{
    margin:0;
    padding:0;
    width:100%;
    height:100%;
    overflow:hidden;
    background:#080c12;
    color:#e5e7eb;
    font-family:Arial,Helvetica,sans-serif;
}

body{
    display:flex;
    flex-direction:column;
}

/* ==========================================================
   TOP BAR
   ========================================================== */

.topbar{

    height:58px;

    background:#10151c;

    border-bottom:1px solid #252c36;

    display:flex;

    align-items:center;

    gap:8px;

    padding:0 12px;

    flex-shrink:0;

}

.logo{

    font-size:18px;

    font-weight:800;

    color:white;

    margin-right:8px;

    white-space:nowrap;

}

select,
button{

    background:#171d25;

    color:#dbe3ec;

    border:1px solid #303946;

    border-radius:5px;

    padding:8px 10px;

    font-size:12px;

    cursor:pointer;

}

button:hover{

    background:#222a34;

}

button.active{

    background:#2962ff;

    border-color:#2962ff;

    color:white;

}

select{

    outline:none;

}


/* ==========================================================
   MAIN
   ========================================================== */

.main{

    flex:1;

    display:flex;

    min-height:0;

}

.chart-area{

    position:relative;

    flex:1;

    min-width:0;

    background:#080c12;

}

#chart{

    position:absolute;

    inset:0;

}


/* ==========================================================
   RIGHT PANEL
   ========================================================== */

.sidebar{

    width:330px;

    background:#10151c;

    border-left:1px solid #252c36;

    overflow-y:auto;

    padding:12px;

}

.section{

    background:#151b23;

    border:1px solid #29323d;

    border-radius:7px;

    padding:12px;

    margin-bottom:10px;

}

.section-title{

    color:#ffffff;

    font-size:12px;

    font-weight:700;

    margin-bottom:10px;

    text-transform:uppercase;

}


/* ==========================================================
   INDICATORS
   ========================================================== */

.indicator-grid{

    display:grid;

    grid-template-columns:1fr 1fr;

    gap:6px;

}

.indicator-btn{

    text-align:left;

    font-size:11px;

    padding:8px;

    background:#11161d;

    border:1px solid #29323d;

}

.indicator-btn.on{

    background:#172642;

    border-color:#2962ff;

    color:#ffffff;

}


/* ==========================================================
   SIGNAL
   ========================================================== */

.signal{

    text-align:center;

    font-size:28px;

    font-weight:900;

    margin:8px 0 15px;

}

.buy{

    color:#22c55e;

}

.sell{

    color:#ef4444;

}

.neutral{

    color:#f59e0b;

}

.data-row{

    display:flex;

    justify-content:space-between;

    padding:6px 0;

    border-bottom:1px solid #222a34;

    font-size:12px;

}

.data-row span:first-child{

    color:#94a3b8;

}

.data-row span:last-child{

    color:white;

    font-weight:600;

}

.reasons{

    color:#cbd5e1;

    font-size:11px;

    line-height:1.7;

}

.warning{

    color:#64748b;

    font-size:9px;

    line-height:1.5;

    margin-top:10px;

}


/* ==========================================================
   CHART INFO
   ========================================================== */

.chart-info{

    position:absolute;

    top:10px;

    left:10px;

    z-index:10;

    background:rgba(8,12,18,.88);

    border:1px solid #29323d;

    border-radius:5px;

    padding:7px 9px;

    font-size:11px;

    color:#cbd5e1;

}


/* ==========================================================
   RESPONSIVE
   ========================================================== */

@media(max-width:900px){

    .sidebar{

        width:270px;

    }

    .logo{

        display:none;

    }

}

@media(max-width:700px){

    .main{

        flex-direction:column;

    }

    .sidebar{

        width:100%;

        height:320px;

    }

}

</style>

</head>


<body>


<!-- ========================================================
     TOP BAR
     ======================================================== -->

<div class="topbar">

<div class="logo">
PRO TRADING
</div>


<select id="symbol">

<option value="RELIANCE.NS">
RELIANCE
</option>

<option value="TCS.NS">
TCS
</option>

<option value="INFY.NS">
INFY
</option>

</select>


<button class="tf" data-tf="5m">
5m
</button>

<button class="tf" data-tf="15m">
15m
</button>

<button class="tf" data-tf="1h">
1H
</button>

<button class="tf active" data-tf="1d">
1D
</button>


<button id="fit">
Auto Fit
</button>

<button id="reset">
Reset
</button>

<button id="full">
Fullscreen
</button>


<button class="type active"
        data-type="candle">
Candle
</button>

<button class="type"
        data-type="line">
Line
</button>

<button class="type"
        data-type="area">
Area
</button>

</div>


<!-- ========================================================
     MAIN
     ======================================================== -->

<div class="main">


<div class="chart-area"
     id="chartArea">

<div id="chart"></div>

<div class="chart-info"
     id="chartInfo">
Loading...
</div>

</div>


<!-- ========================================================
     SIDEBAR
     ======================================================== -->

<div class="sidebar">


<!-- SIGNAL -->

<div class="section">

<div class="section-title">
Smart Signal Engine
</div>

<div id="signal"
     class="signal neutral">
LOADING
</div>

<div class="data-row">
<span>Score</span>
<span id="score">--</span>
</div>

<div class="data-row">
<span>Entry</span>
<span id="entry">--</span>
</div>

<div class="data-row">
<span>Stop Loss</span>
<span id="sl">--</span>
</div>

<div class="data-row">
<span>Target 1</span>
<span id="target1">--</span>
</div>

<div class="data-row">
<span>Target 2</span>
<span id="target2">--</span>
</div>

</div>


<!-- INDICATORS -->

<div class="section">

<div class="section-title">
Indicators
</div>

<div class="indicator-grid">

<button class="indicator-btn"
        data-indicator="ema9">
EMA 9
</button>

<button class="indicator-btn"
        data-indicator="ema20">
EMA 20
</button>

<button class="indicator-btn"
        data-indicator="ema50">
EMA 50
</button>

<button class="indicator-btn"
        data-indicator="ema200">
EMA 200
</button>

<button class="indicator-btn"
        data-indicator="sma20">
SMA 20
</button>

<button class="indicator-btn"
        data-indicator="sma50">
SMA 50
</button>

<button class="indicator-btn"
        data-indicator="sma200">
SMA 200
</button>

<button class="indicator-btn"
        data-indicator="vwap">
VWAP
</button>

<button class="indicator-btn"
        data-indicator="bb">
Bollinger
</button>

<button class="indicator-btn"
        data-indicator="supertrend">
Supertrend
</button>

<button class="indicator-btn"
        data-indicator="pivots">
Pivot Points
</button>

<button class="indicator-btn"
        data-indicator="volume">
Volume
</button>

</div>

</div>


<!-- INDICATOR VALUES -->

<div class="section">

<div class="section-title">
Indicator Values
</div>

<div class="data-row">
<span>EMA 20</span>
<span id="ema20Value">--</span>
</div>

<div class="data-row">
<span>EMA 50</span>
<span id="ema50Value">--</span>
</div>

<div class="data-row">
<span>RSI 14</span>
<span id="rsiValue">--</span>
</div>

<div class="data-row">
<span>MACD</span>
<span id="macdValue">--</span>
</div>

<div class="data-row">
<span>ATR</span>
<span id="atrValue">--</span>
</div>

<div class="data-row">
<span>Stochastic</span>
<span id="stochValue">--</span>
</div>

<div class="data-row">
<span>ADX</span>
<span id="adxValue">--</span>
</div>

<div class="data-row">
<span>VWAP</span>
<span id="vwapValue">--</span>
</div>

</div>


<!-- ANALYSIS -->

<div class="section">

<div class="section-title">
Analysis
</div>

<div id="reasons"
     class="reasons">
Loading...
</div>

<div class="warning">

This is an indicator-based analytical system.
Signals are not guaranteed profits and should
not be treated as financial advice.

</div>

</div>


</div>

</div>


<script>


// ==========================================================
// GLOBAL STATE
// ==========================================================

let chart;

let data = [];

let symbol = "RELIANCE.NS";

let timeframe = "1d";

let chartType = "candle";


const indicators = {

    ema9:false,

    ema20:false,

    ema50:false,

    ema200:false,

    sma20:false,

    sma50:false,

    sma200:false,

    vwap:false,

    bb:false,

    supertrend:false,

    pivots:false,

    volume:false

};


const series = {};


// ==========================================================
// CREATE CHART
// ==========================================================

function createChart(){

    chart =
        LightweightCharts.createChart(

            document.getElementById("chart"),

            {

                layout:{

                    background:{
                        color:"#080c12"
                    },

                    textColor:"#9ca3af"

                },

                grid:{

                    vertLines:{
                        color:"#151b23"
                    },

                    horzLines:{
                        color:"#151b23"
                    }

                },

                rightPriceScale:{

                    borderColor:"#29323d"

                },

                timeScale:{

                    borderColor:"#29323d",

                    timeVisible:true,

                    secondsVisible:false

                },

                crosshair:{

                    mode:
                        LightweightCharts
                        .CrosshairMode
                        .Normal

                }

            }

        );


    series.candle =
        chart.addCandlestickSeries({

            upColor:"#26a69a",

            downColor:"#ef5350",

            borderUpColor:"#26a69a",

            borderDownColor:"#ef5350",

            wickUpColor:"#26a69a",

            wickDownColor:"#ef5350"

        });


    series.line =
        chart.addLineSeries({

            color:"#3b82f6",

            lineWidth:2,

            visible:false

        });


    series.area =
        chart.addAreaSeries({

            lineColor:"#8b5cf6",

            topColor:
                "rgba(139,92,246,.35)",

            bottomColor:
                "rgba(139,92,246,.02)",

            lineWidth:2,

            visible:false

        });


    series.volume =
        chart.addHistogramSeries({

            priceFormat:{
                type:"volume"
            },

            priceScaleId:"volume"

        });


    chart.priceScale("volume")
        .applyOptions({

            scaleMargins:{
                top:.80,
                bottom:0
            }

        });


    const colors = {

        ema9:"#ffffff",

        ema20:"#f59e0b",

        ema50:"#ef4444",

        ema200:"#a855f7",

        sma20:"#22c55e",

        sma50:"#06b6d4",

        sma200:"#f97316",

        vwap:"#ec4899",

        supertrend:"#00e5ff",

        pivot:"#94a3b8"

    };


    for(
        const name of Object.keys(colors)
    ){

        series[name] =
            chart.addLineSeries({

                color:colors[name],

                lineWidth:
                    name === "ema200"
                    ? 2
                    : 1,

                visible:false

            });

    }


    series.bbUpper =
        chart.addLineSeries({

            color:"#64748b",

            lineWidth:1,

            visible:false

        });


    series.bbMiddle =
        chart.addLineSeries({

            color:"#94a3b8",

            lineWidth:1,

            visible:false

        });


    series.bbLower =
        chart.addLineSeries({

            color:"#64748b",

            lineWidth:1,

            visible:false

        });


    window.addEventListener(
        "resize",
        resize
    );

}


// ==========================================================
// RESIZE
// ==========================================================

function resize(){

    chart.applyOptions({

        width:
            document.getElementById("chart")
            .clientWidth,

        height:
            document.getElementById("chart")
            .clientHeight

    });

}


// ==========================================================
// EMA
// ==========================================================

function EMA(values, period){

    const out=[];

    const k =
        2/(period+1);

    let prev=null;

    for(let i=0;i<values.length;i++){

        if(prev===null){

            prev=values[i];

        }else{

            prev =
                values[i]*k
                +
                prev*(1-k);

        }

        out.push(prev);

    }

    return out;

}


// ==========================================================
// SMA
// ==========================================================

function SMA(values, period){

    const out=[];

    let sum=0;

    for(let i=0;i<values.length;i++){

        sum += values[i];

        if(i>=period){

            sum -= values[i-period];

        }

        if(i>=period-1){

            out.push(
                sum/period
            );

        }else{

            out.push(null);

        }

    }

    return out;

}


// ==========================================================
// RSI
// ==========================================================

function RSI(values, period=14){

    const out =
        new Array(values.length)
        .fill(null);

    let gains=0;

    let losses=0;

    for(
        let i=1;
        i<=period;
        i++
    ){

        const change =
            values[i]-values[i-1];

        if(change>=0){

            gains+=change;

        }else{

            losses-=change;

        }

    }

    let avgGain =
        gains/period;

    let avgLoss =
        losses/period;


    for(
        let i=period+1;
        i<values.length;
        i++
    ){

        const change =
            values[i]-values[i-1];

        const gain =
            Math.max(change,0);

        const loss =
            Math.max(-change,0);


        avgGain =
            (
                avgGain*(period-1)
                +gain
            )/period;


        avgLoss =
            (
                avgLoss*(period-1)
                +loss
            )/period;


        if(avgLoss===0){

            out[i]=100;

        }else{

            const rs =
                avgGain/avgLoss;

            out[i]=
                100-
                (100/(1+rs));

        }

    }

    return out;

}


// ==========================================================
// ATR
// ==========================================================

function ATR(candles,period=14){

    const tr=[];

    for(
        let i=0;
        i<candles.length;
        i++
    ){

        if(i===0){

            tr.push(
                candles[i].high
                -
                candles[i].low
            );

        }else{

            const h =
                candles[i].high;

            const l =
                candles[i].low;

            const pc =
                candles[i-1].close;


            tr.push(
                Math.max(

                    h-l,

                    Math.abs(h-pc),

                    Math.abs(l-pc)

                )
            );

        }

    }

    return SMA(
        tr,
        period
    );

}


// ==========================================================
// VWAP
// ==========================================================

function VWAP(candles){

    let pv=0;

    let volume=0;

    const out=[];

    for(
        const c of candles
    ){

        const typical =
            (
                c.high+
                c.low+
                c.close
            )/3;

        pv +=
            typical*c.volume;

        volume +=
            c.volume;


        out.push(
            volume
            ? pv/volume
            : c.close
        );

    }

    return out;

}


// ==========================================================
// BOLLINGER
// ==========================================================

function Bollinger(
    values,
    period=20,
    multiplier=2
){

    const upper =
        new Array(values.length)
        .fill(null);

    const middle =
        new Array(values.length)
        .fill(null);

    const lower =
        new Array(values.length)
        .fill(null);


    for(
        let i=period-1;
        i<values.length;
        i++
    ){

        const slice =
            values.slice(
                i-period+1,
                i+1
            );


        const mean =
            slice.reduce(
                (a,b)=>a+b,
                0
            )/period;


        const variance =
            slice.reduce(
                (sum,v)=>
                    sum+
                    Math.pow(
                        v-mean,
                        2
                    ),
                0
            )/period;


        const sd =
            Math.sqrt(
                variance
            );


        middle[i]=mean;

        upper[i]=
            mean+
            multiplier*sd;

        lower[i]=
            mean-
            multiplier*sd;

    }


    return {
        upper,
        middle,
        lower
    };

}


// ==========================================================
// MACD
// ==========================================================

function MACD(values){

    const ema12 =
        EMA(values,12);

    const ema26 =
        EMA(values,26);

    const macd =
        values.map(
            (_,i)=>
                ema12[i]-
                ema26[i]
        );

    const signal =
        EMA(
            macd,
            9
        );

    const histogram =
        macd.map(
            (v,i)=>
                v-signal[i]
        );


    return {
        macd,
        signal,
        histogram
    };

}


// ==========================================================
// STOCHASTIC
// ==========================================================

function Stochastic(
    candles,
    period=14
){

    const k =
        new Array(
            candles.length
        ).fill(null);

    for(
        let i=period-1;
        i<candles.length;
        i++
    ){

        let high=-Infinity;

        let low=Infinity;


        for(
            let j=i-period+1;
            j<=i;
            j++
        ){

            high =
                Math.max(
                    high,
                    candles[j].high
                );

            low =
                Math.min(
                    low,
                    candles[j].low
                );

        }


        k[i]=
            (
                (
                    candles[i].close-low
                )
                /
                (
                    high-low
                )
            )*100;

    }

    return k;

}


// ==========================================================
// ADX
// ==========================================================

function ADX(candles,period=14){

    const tr=[];

    const plusDM=[];

    const minusDM=[];


    for(
        let i=1;
        i<candles.length;
        i++
    ){

        const high =
            candles[i].high;

        const low =
            candles[i].low;

        const prevHigh =
            candles[i-1].high;

        const prevLow =
            candles[i-1].low;

        const prevClose =
            candles[i-1].close;


        tr.push(

            Math.max(

                high-low,

                Math.abs(
                    high-prevClose
                ),

                Math.abs(
                    low-prevClose
                )

            )

        );


        const up =
            high-prevHigh;

        const down =
            prevLow-low;


        plusDM.push(
            up>down && up>0
            ? up
            : 0
        );


        minusDM.push(
            down>up && down>0
            ? down
            : 0
        );

    }


    const atr =
        SMA(
            tr,
            period
        );


    const plus =
        SMA(
            plusDM,
            period
        );


    const minus =
        SMA(
            minusDM,
            period
        );


    const dx =
        new Array(
            candles.length
        ).fill(null);


    for(
        let i=0;
        i<atr.length;
        i++
    ){

        const index =
            i+period;


        if(
            atr[i] &&
            atr[i]!==0
        ){

            const pdi =
                100*
                (
                    plus[i]/
                    atr[i]
                );

            const mdi =
                100*
                (
                    minus[i]/
                    atr[i]
                );


            const denominator =
                pdi+mdi;


            if(
                denominator!==0
            ){

                dx[index]=
                    100*
                    Math.abs(
                        pdi-mdi
                    )/
                    denominator;

            }

        }

    }


    const adxValues =
        SMA(
            dx.map(
                x=>x===null
                    ? 0
                    : x
            ),
            period
        );


    return adxValues;

}


// ==========================================================
// SUPERTREND
// ==========================================================

function Supertrend(
    candles,
    period=10,
    multiplier=3
){

    const atr =
        ATR(
            candles,
            period
        );


    const result =
        new Array(
            candles.length
        ).fill(null);


    const direction =
        new Array(
            candles.length
        ).fill(1);


    for(
        let i=period;
        i<candles.length;
        i++
    ){

        const hl2 =
            (
                candles[i].high+
                candles[i].low
            )/2;


        const a =
            atr[i];


        if(
            a===null ||
            !Number.isFinite(a)
        ){

            continue;

        }


        const upper =
            hl2+
            multiplier*a;

        const lower =
            hl2-
            multiplier*a;


        if(
            candles[i].close>
            upper
        ){

            direction[i]=1;

        }else if(
            candles[i].close<
            lower
        ){

            direction[i]=-1;

        }else{

            direction[i]=
                direction[i-1];

        }


        result[i]=
            direction[i]===1
                ? lower
                : upper;

    }


    return {
        values:result,
        direction
    };

}


// ==========================================================
// PIVOTS
// ==========================================================

function PivotPoints(candles){

    if(candles.length<2){

        return {
            p:null,
            r1:null,
            r2:null,
            s1:null,
            s2:null
        };

    }


    const c =
        candles[
            candles.length-2
        ];


    const p =
        (
            c.high+
            c.low+
            c.close
        )/3;


    return {

        p,

        r1:
            2*p-c.low,

        r2:
            p+
            (c.high-c.low),

        s1:
            2*p-c.high,

        s2:
            p-
            (c.high-c.low)

    };

}


// ==========================================================
// CONVERT ARRAY TO LINE DATA
// ==========================================================

function lineData(values){

    const result=[];


    for(
        let i=0;
        i<values.length;
        i++
    ){

        if(
            values[i]!==null &&
            Number.isFinite(
                Number(values[i])
            )
        ){

            result.push({

                time:data[i].time,

                value:Number(
                    values[i]
                )

            });

        }

    }


    return result;

}


// ==========================================================
// DRAW EVERYTHING
// ==========================================================

function draw(){

    if(!data.length){

        return;

    }


    const closes =
        data.map(
            x=>x.close
        );


    // BASE CHART

    series.candle.setData(
        data
    );


    series.line.setData(

        data.map(
            x=>({

                time:x.time,

                value:x.close

            })
        )

    );


    series.area.setData(

        data.map(
            x=>({

                time:x.time,

                value:x.close

            })
        )

    );


    // VOLUME

    series.volume.setData(

        data.map(
            x=>({

                time:x.time,

                value:x.volume,

                color:
                    x.close>=x.open
                    ? "rgba(38,166,154,.45)"
                    : "rgba(239,83,80,.45)"

            })
        )

    );


    // EMA

    series.ema9.setData(
        lineData(
            EMA(closes,9)
        )
    );

    series.ema20.setData(
        lineData(
            EMA(closes,20)
        )
    );

    series.ema50.setData(
        lineData(
            EMA(closes,50)
        )
    );

    series.ema200.setData(
        lineData(
            EMA(closes,200)
        )
    );


    // SMA

    series.sma20.setData(
        lineData(
            SMA(closes,20)
        )
    );

    series.sma50.setData(
        lineData(
            SMA(closes,50)
        )
    );

    series.sma200.setData(
        lineData(
            SMA(closes,200)
        )
    );


    // VWAP

    series.vwap.setData(
        lineData(
            VWAP(data)
        )
    );


    // BOLLINGER

    const bb =
        Bollinger(
            closes,
            20,
            2
        );


    series.bbUpper.setData(
        lineData(bb.upper)
    );

    series.bbMiddle.setData(
        lineData(bb.middle)
    );

    series.bbLower.setData(
        lineData(bb.lower)
    );


    // SUPERTREND

    const st =
        Supertrend(
            data
        );


    series.supertrend.setData(
        lineData(
            st.values
        )
    );


    // PIVOT

    const pivot =
        PivotPoints(
            data
        );


    if(
        pivot.p!==null
    ){

        series.pivots.setData(

            data.map(
                x=>({

                    time:x.time,

                    value:pivot.p

                })
            )

        );

    }


    // VISIBILITY

    series.candle.applyOptions({

        visible:
            chartType==="candle"

    });


    series.line.applyOptions({

        visible:
            chartType==="line"

    });


    series.area.applyOptions({

        visible:
            chartType==="area"

    });


    series.volume.applyOptions({

        visible:
            indicators.volume

    });


    [
        "ema9",
        "ema20",
        "ema50",
        "ema200",
        "sma20",
        "sma50",
        "sma200",
        "vwap",
        "supertrend",
        "pivots"

    ].forEach(
        name=>{

            series[name].applyOptions({

                visible:
                    indicators[name]

            });

        }
    );


    series.bbUpper.applyOptions({

        visible:
            indicators.bb

    });


    series.bbMiddle.applyOptions({

        visible:
            indicators.bb

    });


    series.bbLower.applyOptions({

        visible:
            indicators.bb

    });


    chart.timeScale()
        .fitContent();

}


// ==========================================================
// LOAD DATA
// ==========================================================

async function loadData(){

    document.getElementById(
        "chartInfo"
    ).textContent =
        "Loading market data...";


    try{

        const response =
            await fetch(

                `/api/candles/${encodeURIComponent(symbol)}?interval=${timeframe}`

            );


        if(!response.ok){

            throw new Error(
                "Market data unavailable"
            );

        }


        data =
            await response.json();


        if(!data.length){

            throw new Error(
                "No data"
            );

        }


        draw();

        updateValues();

        await loadSignal();


        document.getElementById(
            "chartInfo"
        ).textContent =
            `${symbol} • ${timeframe.toUpperCase()} • ${data.length} candles`;

    }
    catch(error){

        console.error(error);

        document.getElementById(
            "chartInfo"
        ).textContent =
            error.message;

    }

}


// ==========================================================
// UPDATE INDICATOR VALUES
// ==========================================================

function updateValues(){

    const closes =
        data.map(
            x=>x.close
        );


    const ema20 =
        EMA(
            closes,
            20
        );

    const ema50 =
        EMA(
            closes,
            50
        );


    const rsi =
        RSI(
            closes,
            14
        );


    const macd =
        MACD(
            closes
        );


    const atr =
        ATR(
            data,
            14
        );


    const stoch =
        Stochastic(
            data
        );


    const adx =
        ADX(
            data
        );


    const vwap =
        VWAP(
            data
        );


    const last =
        data.length-1;


    document.getElementById(
        "ema20Value"
    ).textContent =
        ema20[last]
        ?.toFixed(2)
        || "--";


    document.getElementById(
        "ema50Value"
    ).textContent =
        ema50[last]
        ?.toFixed(2)
        || "--";


    document.getElementById(
        "rsiValue"
    ).textContent =
        rsi[last]!==null
        ? rsi[last].toFixed(2)
        : "--";


    document.getElementById(
        "macdValue"
    ).textContent =
        macd.macd[last]
        ?.toFixed(3)
        || "--";


    document.getElementById(
        "atrValue"
    ).textContent =
        atr[last]
        ?.toFixed(2)
        || "--";


    document.getElementById(
        "stochValue"
    ).textContent =
        stoch[last]!==null
        ? stoch[last].toFixed(2)
        : "--";


    document.getElementById(
        "adxValue"
    ).textContent =
        adx[last]
        ?.toFixed(2)
        || "--";


    document.getElementById(
        "vwapValue"
    ).textContent =
        vwap[last]
        ?.toFixed(2)
        || "--";

}


// ==========================================================
// SMART SIGNAL
// ==========================================================

async function loadSignal(){

    try{

        const response =
            await fetch(

                `/api/signal/${encodeURIComponent(symbol)}?interval=${timeframe}`

            );


        if(!response.ok){

            throw new Error(
                "Signal unavailable"
            );

        }


        const s =
            await response.json();


        const signal =
            document.getElementById(
                "signal"
            );


        signal.textContent =
            s.signal;


        signal.className =
            "signal "+
            (
                s.signal==="BUY"
                ?"buy"
                :
                s.signal==="SELL"
                ?"sell"
                :
                "neutral"
            );


        document.getElementById(
            "score"
        ).textContent =
            `${s.score}/${s.max_score}`;


        document.getElementById(
            "entry"
        ).textContent =
            s.entry!==null
            ? "₹"+Number(
                s.entry
            ).toFixed(2)
            : "--";


        document.getElementById(
            "sl"
        ).textContent =
            s.stop_loss!==null
            ? "₹"+Number(
                s.stop_loss
            ).toFixed(2)
            : "--";


        document.getElementById(
            "target1"
        ).textContent =
            s.target1!==null
            ? "₹"+Number(
                s.target1
            ).toFixed(2)
            : "--";


        document.getElementById(
            "target2"
        ).textContent =
            s.target2!==null
            ? "₹"+Number(
                s.target2
            ).toFixed(2)
            : "--";


        document.getElementById(
            "reasons"
        ).innerHTML =
            s.reasons
            .map(
                x=>`• ${x}`
            )
            .join("<br>");

    }
    catch(error){

        console.error(error);

        document.getElementById(
            "signal"
        ).textContent =
            "NEUTRAL";

        document.getElementById(
            "signal"
        ).className =
            "signal neutral";

        document.getElementById(
            "reasons"
        ).textContent =
            "Signal data unavailable.";

    }

}


// ==========================================================
// TIMEFRAME
// ==========================================================

document.querySelectorAll(
    ".tf"
).forEach(
    button=>{

        button.addEventListener(
            "click",
            async()=>{

                document
                .querySelectorAll(".tf")
                .forEach(
                    x=>
                    x.classList.remove(
                        "active"
                    )
                );


                button.classList.add(
                    "active"
                );


                timeframe =
                    button.dataset.tf;


                await loadData();

            }
        );

    }
);


// ==========================================================
// SYMBOL
// ==========================================================

document.getElementById(
    "symbol"
).addEventListener(
    "change",
    async event=>{

        symbol =
            event.target.value;

        await loadData();

    }
);


// ==========================================================
// INDICATOR BUTTONS
// ==========================================================

document.querySelectorAll(
    ".indicator-btn"
).forEach(
    button=>{

        button.addEventListener(
            "click",
            ()=>{

                const name =
                    button.dataset.indicator;


                indicators[name] =
                    !indicators[name];


                button.classList.toggle(
                    "on",
                    indicators[name]
                );


                draw();

            }
        );

    }
);


// ==========================================================
// CHART TYPE
// ==========================================================

document.querySelectorAll(
    ".type"
).forEach(
    button=>{

        button.addEventListener(
            "click",
            ()=>{

                document
                .querySelectorAll(".type")
                .forEach(
                    x=>
                    x.classList.remove(
                        "active"
                    )
                );


                button.classList.add(
                    "active"
                );


                chartType =
                    button.dataset.type;


                draw();

            }
        );

    }
);


// ==========================================================
// AUTO FIT
// ==========================================================

document.getElementById(
    "fit"
).addEventListener(
    "click",
    ()=>{

        chart.timeScale()
            .fitContent();

    }
);


// ==========================================================
// RESET
// ==========================================================

document.getElementById(
    "reset"
).addEventListener(
    "click",
    ()=>{

        chart.timeScale()
            .fitContent();

    }
);


// ==========================================================
// FULLSCREEN
// ==========================================================

document.getElementById(
    "full"
).addEventListener(
    "click",
    async()=>{

        const area =
            document.getElementById(
                "chartArea"
            );


        if(
            !document.fullscreenElement
        ){

            await area.requestFullscreen();

        }
        else{

            await document.exitFullscreen();

        }


        setTimeout(
            resize,
            300
        );

    }
);


// ==========================================================
// START
// ==========================================================

createChart();

resize();

loadData();

</script>

</body>

</html>
"""


# ============================================================
# FRONTEND
# ============================================================

@app.get("/", response_class=HTMLResponse)
async def home():

    return HTML


# ============================================================
# MARKET DATA
# ============================================================

def get_market_data(symbol, timeframe):

    if symbol not in SYMBOLS:

        raise HTTPException(
            status_code=400,
            detail="Invalid symbol"
        )

    if timeframe not in TIMEFRAMES:

        raise HTTPException(
            status_code=400,
            detail="Invalid timeframe"
        )

    settings = TIMEFRAMES[timeframe]

    ticker = yf.Ticker(symbol)

    df = ticker.history(
        period=settings["period"],
        interval=settings["interval"],
        auto_adjust=False
    )

    if df.empty:

        raise HTTPException(
            status_code=404,
            detail="No market data found"
        )

    df = df.dropna(
        subset=[
            "Open",
            "High",
            "Low",
            "Close"
        ]
    )

    return df


# ============================================================
# CANDLES API
# ============================================================

@app.get("/api/candles/{symbol}")
async def candles(
    symbol: str,
    interval: str = "1d"
):

    df = get_market_data(
        symbol.upper(),
        interval
    )

    result = []

    for index, row in df.iterrows():

        if interval == "1d":

            time_value = index.strftime(
                "%Y-%m-%d"
            )

        else:

            time_value = int(
                index.timestamp()
            )


        volume = row["Volume"]

        if pd.isna(volume):

            volume = 0


        result.append({

            "time": time_value,

            "open": float(
                row["Open"]
            ),

            "high": float(
                row["High"]
            ),

            "low": float(
                row["Low"]
            ),

            "close": float(
                row["Close"]
            ),

            "volume": int(
                volume
            )

        })


    return result


# ============================================================
# BACKEND INDICATORS
# ============================================================

def backend_ema(series, period):

    return series.ewm(
        span=period,
        adjust=False
    ).mean()


def backend_rsi(series, period=14):

    delta = series.diff()

    gain = delta.clip(
        lower=0
    )

    loss = -delta.clip(
        upper=0
    )

    avg_gain = gain.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    avg_loss = loss.ewm(
        alpha=1 / period,
        adjust=False
    ).mean()

    rs = (
        avg_gain
        /
        avg_loss.replace(
            0,
            np.nan
        )
    )

    return (
        100 -
        (
            100 /
            (1 + rs)
        )
    ).fillna(50)


def backend_vwap(df):

    typical = (
        df["High"]
        +
        df["Low"]
        +
        df["Close"]
    ) / 3

    volume = df["Volume"].fillna(0)

    return (
        (typical * volume).cumsum()
        /
        volume.cumsum().replace(
            0,
            np.nan
        )
    ).fillna(
        df["Close"]
    )


def backend_atr(
    df,
    period=14
):

    previous = df["Close"].shift(1)

    tr = pd.concat(
        [

            df["High"] -
            df["Low"],

            (
                df["High"] -
                previous
            ).abs(),

            (
                df["Low"] -
                previous
            ).abs()

        ],
        axis=1
    ).max(axis=1)

    return tr.rolling(
        period
    ).mean()


# ============================================================
# SMART SIGNAL
# ============================================================

@app.get("/api/signal/{symbol}")
async def signal(
    symbol: str,
    interval: str = "5m"
):

    df = get_market_data(
        symbol.upper(),
        interval
    )

    if len(df) < 50:

        raise HTTPException(
            status_code=400,
            detail="Not enough data"
        )


    close = df["Close"]


    ema20 = backend_ema(
        close,
        20
    )

    ema50 = backend_ema(
        close,
        50
    )

    rsi = backend_rsi(
        close,
        14
    )

    vwap = backend_vwap(
        df
    )

    atr = backend_atr(
        df,
        14
    )


    avg_volume = df["Volume"].rolling(
        20
    ).mean()


    price = float(close.iloc[-1])

    e20 = float(ema20.iloc[-1])

    e50 = float(ema50.iloc[-1])

    r = float(rsi.iloc[-1])

    v = float(vwap.iloc[-1])

    current_volume = float(df["Volume"].iloc[-1])

    average_volume = float(avg_volume.iloc[-1])


    atr_value = float(atr.iloc[-1])


    if not math.isfinite(
        atr_value
    ):

        atr_value = price * 0.01


    buy = 0

    sell = 0

    reasons = []


    # PRICE / EMA

    if price > e20:

        buy += 1

        reasons.append(
            "Price above EMA20"
        )

    else:

        sell += 1

        reasons.append(
            "Price below EMA20"
        )


    # EMA TREND

    if e20 > e50:

        buy += 1

        reasons.append(
            "EMA20 above EMA50"
        )

    else:

        sell += 1

        reasons.append(
            "EMA20 below EMA50"
        )


    # RSI

    if 50 <= r < 70:

        buy += 1

        reasons.append(
            f"RSI {r:.1f} bullish"
        )

    elif r < 50:

        sell += 1

        reasons.append(
            f"RSI {r:.1f} weak"
        )

    else:

        reasons.append(
            f"RSI {r:.1f} overbought"
        )


    # VWAP

    if price > v:

        buy += 1

        reasons.append(
            "Price above VWAP"
        )

    else:

        sell += 1

        reasons.append(
            "Price below VWAP"
        )


    # VOLUME

    if current_volume > average_volume:

        if price > e20:

            buy += 1

            reasons.append(
                "Above-average volume with bullish price"
            )

        else:

            sell += 1

            reasons.append(
                "Above-average volume with bearish price"
            )

    else:

        reasons.append(
            "Volume below average"
        )


    if buy >= 4:

        final_signal = "BUY"

    elif sell >= 4:

        final_signal = "SELL"

    else:

        final_signal = "NEUTRAL"


    entry = round(
        price,
        2
    )


    if final_signal == "BUY":

        stop = round(
            entry -
            1.5 * atr_value,
            2
        )

        target1 = round(
            entry +
            2 * atr_value,
            2
        )

        target2 = round(
            entry +
            3 * atr_value,
            2
        )

    elif final_signal == "SELL":

        stop = round(
            entry +
            1.5 * atr_value,
            2
        )

        target1 = round(
            entry -
            2 * atr_value,
            2
        )

        target2 = round(
            entry -
            3 * atr_value,
            2
        )

    else:

        stop = None

        target1 = None

        target2 = None


    return {

        "symbol": symbol,

        "interval": interval,

        "signal": final_signal,

        "score": max(
            buy,
            sell
        ),

        "max_score": 5,

        "buy_score": buy,

        "sell_score": sell,

        "entry": entry,

        "stop_loss": stop,

        "target1": target1,

        "target2": target2,

        "indicators": {

            "ema20": round(
                e20,
                2
            ),

            "ema50": round(
                e50,
                2
            ),

            "rsi": round(
                r,
                2
            ),

            "vwap": round(
                v,
                2
            ),

            "atr": round(
                atr_value,
                2
            ),

            "volume": int(
                current_volume
            ),

            "average_volume": int(
                average_volume
            )

        },

        "reasons": reasons

    }


# ============================================================
# SERVER
# ============================================================

if __name__ == "__main__":

    import os

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000))
    )
