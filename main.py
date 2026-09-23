from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import yfinance as yf

app = FastAPI()

def get_html_page():
    return chr(60) + "!DOCTYPE html" + chr(62) + chr(60) + "html" + chr(62) + chr(60) + "head" + chr(62) + chr(60) + "title" + chr(62) + "Trading Chart" + chr(60) + "/title" + chr(62) + chr(60) + "script src='https://unpkg.com/lightweight-charts/dist/lightweight-charts.standalone.production.js'" + chr(62) + chr(60) + "/script" + chr(62) + chr(60) + "/head" + chr(62) + chr(60) + "body style='background:#131722;color:#fff;margin:0;padding:20px;font-family:sans-serif;'" + chr(62) + chr(60) + "h2" + chr(62) + "Trading Chart Platform" + chr(60) + "/h2" + chr(60) + "select id='s' onchange='d()' style='padding:6px;background:#2a2e39;color:#fff;margin-bottom:12px;'" + chr(62) + chr(60) + "option value='RELIANCE.NS'" + chr(62) + "Reliance" + chr(60) + "/option" + chr(62) + chr(60) + "option value='TCS.NS'" + chr(62) + "TCS" + chr(60) + "/option" + chr(62) + chr(60) + "option value='INFY.NS'" + chr(62) + "Infosys" + chr(60) + "/option" + chr(62) + chr(60) + "/select" + chr(62) + chr(60) + "div id='c' style='width:100%;height:550px;'" + chr(62) + chr(60) + "/div" + chr(62) + chr(60) + "script" + chr(62) + "const chart=LightweightCharts.createChart(document.getElementById('c'),{layout:{background:{color:'#131722'},textColor:'#d1d4dc'}});const s=chart.addCandlestickSeries({upColor:'#26a69a',downColor:'#ef5350'});async function d(){const r=await fetch('/api/c/'+document.getElementById('s').value);const dt=await r.json();s.setData(dt);chart.timeScale().fitContent();}window.onresize=()=>chart.resize(window.innerWidth-40,550);d();" + chr(60) + "/script" + chr(62) + chr(60) + "/body" + chr(62) + chr(60) + "/html" + chr(62)

@app.get("/", response_class=HTMLResponse)
def home():
    return get_html_page()

@app.get("/api/c/{sym}")
def get_c(sym: str):
    df = yf.Ticker(sym).history(period="6mo", interval="1d")
    return [
        {
            "time": idx.strftime("%Y-%m-%d"),
            "open": round(float(r["Open"]), 2),
            "high": round(float(r["High"]), 2),
            "low": round(float(r["Low"]), 2),
            "close": round(float(r["Close"]), 2),
        }
        for idx, r in df.iterrows()
    ]
