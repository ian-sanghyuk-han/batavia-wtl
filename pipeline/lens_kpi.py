# Region lens KPI pipeline (P2-4): per-node representative index -> /site/data/lens.json
# Real: index level, day change %, 30d spark closes. (Policy rate / GDP stay estimates for now.)
import datetime
import json
import os

import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "data", "lens.json")

NODE_IDX = {  # node id -> (yahoo symbol, display label)
    "NY":  ("^GSPC",     "S&P 500"),
    "CHI": ("ES=F",      "CME S&P 선물"),
    "SP":  ("^BVSP",     "Bovespa"),
    "LDN": ("^FTSE",     "FTSE 100"),
    "FRA": ("^GDAXI",    "DAX"),
    "PAR": ("^FCHI",     "CAC 40"),
    "RYD": ("^TASI.SR",  "Tadawul"),
    "MUM": ("^NSEI",     "Nifty 50"),
    "SIN": ("^STI",      "STI"),
    "HKG": ("^HSI",      "항셍"),
    "SHA": ("000001.SS", "상하이종합"),
    "SEL": ("^KS11",     "코스피"),
    "TYO": ("^N225",     "닛케이 225"),
    "SYD": ("^AXJO",     "ASX 200"),
}

data = yf.download([v[0] for v in NODE_IDX.values()], period="60d", interval="1d",
                   progress=False, group_by="ticker", threads=True, auto_adjust=True)

nodes = {}
for nid, (tk, label) in NODE_IDX.items():
    try:
        closes = data[tk]["Close"].dropna().tail(30)
        if len(closes) < 5:
            raise ValueError("too few closes")
        chg = (float(closes.iloc[-1]) / float(closes.iloc[-2]) - 1) * 100
        nodes[nid] = {
            "label": label,
            "value": round(float(closes.iloc[-1]), 2),
            "chg_pct": round(chg, 2),
            "spark": [round(float(v), 2) for v in closes.tolist()],
            "asof": str(closes.index[-1].date()),
        }
    except Exception as e:
        print(nid, "fail:", e)

out = {
    "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "nodes": nodes,
    "source": "Yahoo Finance (free)",
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"lens.json written: {len(nodes)}/{len(NODE_IDX)} nodes")
