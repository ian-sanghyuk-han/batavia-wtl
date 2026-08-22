# Daily market pipeline (P2 v2): FRED-first (official/licensed daily closes) + Yahoo fallback -> /site/data/market.json
# The frontend reads ONLY this JSON. Key comes from env FRED_API_KEY (never hardcoded).
import datetime
import json
import os
import urllib.request

import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "data", "market.json")

FRED_KEY = os.environ.get("FRED_API_KEY")


def fred_series(sid, n=10):
    url = (f"https://api.stlouisfed.org/fred/series/observations"
           f"?series_id={sid}&api_key={FRED_KEY}&file_type=json&sort_order=desc&limit={n}")
    with urllib.request.urlopen(url, timeout=30) as r:
        obs = json.load(r)["observations"]
    return [(o["date"], float(o["value"])) for o in obs if o["value"] not in (".", "")]


series = {}
extras = {}

# --- FRED: 2y yield (ticker) + HY OAS / net liquidity (later widgets) ---
if FRED_KEY:
    try:
        v = fred_series("DGS2")
        series["us2y"] = {"label": "미2년", "value": v[0][1], "prev": v[1][1],
                          "unit": "%", "delta_kind": "level", "asof": v[0][0]}
    except Exception as e:
        print("DGS2 fail:", e)
    try:
        hy = fred_series("BAMLH0A0HYM2")
        extras["hy_oas_pct"] = {"value": hy[0][1], "prev": hy[1][1], "asof": hy[0][0]}
        # EXP-003 재검용 HY OAS 이력 축적 — 원천이 2023+로 잘려 있어 우리가 직접 쌓는다
        hist_path = os.path.join(HERE, "..", "site", "data", "history", "hy_oas.csv")
        os.makedirs(os.path.dirname(hist_path), exist_ok=True)
        existing = set()
        if os.path.exists(hist_path):
            existing = {ln.split(",")[0] for ln in open(hist_path, encoding="utf-8")}
        with open(hist_path, "a", encoding="utf-8") as fp:
            for d_, v_ in sorted(hy, key=lambda x: x[0]):
                if d_ not in existing:
                    fp.write(f"{d_},{v_}\n")
    except Exception as e:
        print("HY OAS fail:", e)
    try:
        walcl = fred_series("WALCL", 5)       # millions USD, weekly
        rrp = fred_series("RRPONTSYD", 10)    # billions USD, daily
        tga = fred_series("WTREGEN", 10)      # millions USD, weekly
        extras["net_liquidity_bn"] = {
            "value": round(walcl[0][1] / 1000 - rrp[0][1] - tga[0][1] / 1000, 1),
            "formula": "WALCL - RRP - TGA (USD bn)", "asof": walcl[0][0]}
    except Exception as e:
        print("net liquidity fail:", e)
else:
    print("WARN: FRED_API_KEY missing - FRED series skipped")

# --- FRED daily closes for what FRED publishes (S&P 500, Nikkei 225, WTI, VIX, broad USD, BTC) ---
# Provenance upgrade: these six move off Yahoo to FRED-hosted official/licensed series.
FRED_TICKERS = {
    "spx":    ("SP500",      "S&P"),
    "nikkei": ("NIKKEI225",  "닛케이"),
    "vix":    ("VIXCLS",     "VIX"),
    "btc":    ("CBBTCUSD",   "BTC"),      # Coinbase BTC/USD daily close
}
# WTI (DCOILWTICO) and the broad dollar (DTWEXBGS) lag 3-7 days on FRED - too stale
# for a live ticker, so they stay on Yahoo until a fresher official feed exists.
if FRED_KEY:
    for key, (sid, label) in FRED_TICKERS.items():
        try:
            v = fred_series(sid, 6)
            series[key] = {"label": label, "value": round(v[0][1], 2), "prev": round(v[1][1], 2),
                           "unit": "", "delta_kind": "pct", "asof": v[0][0], "src": "FRED"}
        except Exception as e:
            print(key, "FRED fail:", e)

# --- Yahoo Finance: only the exchanges/commodities FRED does not publish (fallback for the rest) ---
# Index order = economic size (T1 tiers of the label system): US, CN, JP, DE, IN, UK, KR.
# The stage is global — no market is the protagonist.
TICKERS = {
    "spx":      ("^GSPC",     "S&P"),
    "shanghai": ("000001.SS", "상하이"),
    "nikkei":   ("^N225",     "닛케이"),
    "dax":      ("^GDAXI",    "DAX"),
    "sensex":   ("^BSESN",    "센섹스"),
    "ftse":     ("^FTSE",     "FTSE"),
    "kospi":    ("^KS11",     "KOSPI"),
    "dxy":      ("DX-Y.NYB",  "DXY"),
    "wti":      ("CL=F",      "WTI"),
    "copper":   ("HG=F",      "구리"),
    "vix":      ("^VIX",      "VIX"),
    "btc":      ("BTC-USD",   "BTC"),
}
data = yf.download([t[0] for t in TICKERS.values()], period="7d", interval="1d",
                   progress=False, group_by="ticker", threads=True, auto_adjust=True)
for key, (tk, label) in TICKERS.items():
    if key in series:          # FRED already delivered it
        continue
    try:
        closes = data[tk]["Close"].dropna()
        series[key] = {"label": label,
                       "value": round(float(closes.iloc[-1]), 2),
                       "prev": round(float(closes.iloc[-2]), 2),
                       "unit": "", "delta_kind": "pct",
                       "asof": str(closes.index[-1].date()), "src": "Yahoo"}
    except Exception as e:
        print(key, "fail:", e)

out = {
    "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "series": series,
    "extras": extras,
    "source": "FRED (S&P500 · Nikkei · VIX · BTC · rates · liquidity) + Yahoo Finance (DAX · FTSE · SENSEX · KOSPI · Shanghai · WTI · DXY · copper)",
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"market.json written: {len(series)} series, extras={list(extras)}")
