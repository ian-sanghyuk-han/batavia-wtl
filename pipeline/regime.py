# Regime gauges pipeline (P2-3): convergence C (core 5.1-5.2, measured) and
# market state w (ESTIMATE v1 - no canonical estimator in the core, so a transparent
# composite: 0.45*VIX 1y-percentile + 0.35*HY-OAS 1y-percentile + 0.20*C).
# Output: /site/data/regime.json
import datetime
import json
import os
import urllib.request

import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "data", "regime.json")
FRED_KEY = os.environ.get("FRED_API_KEY")

BASKET = {  # cross-asset pairs for avg |rho| — equities/FX/commodities/crypto
    "spx": "^GSPC", "kospi": "^KS11", "dxy": "DX-Y.NYB",
    "wti": "CL=F", "copper": "HG=F", "gold": "GC=F", "btc": "BTC-USD",
}
WINDOW = 60  # core 5.1: rolling window convention

data = yf.download(list(BASKET.values()) + ["^VIX"], period="1y", interval="1d",
                   progress=False, group_by="ticker", threads=True, auto_adjust=True)

closes = {}
for key, tk in BASKET.items():
    try:
        closes[key] = data[tk]["Close"].dropna()
    except Exception as e:
        print(key, "fail:", e)

import pandas as pd  # comes with yfinance

px = pd.DataFrame(closes).ffill().dropna()
rets = px.pct_change().dropna().tail(WINDOW)
corr = rets.corr().abs()
n = len(corr)
pairs = [corr.iloc[i, j] for i in range(n) for j in range(i + 1, n)]
conv = float(sum(pairs) / len(pairs))
conv_asof = str(rets.index[-1].date())

# --- w estimate components ---
def pctl(series_vals, latest):
    vals = [v for v in series_vals if v == v]
    return sum(1 for v in vals if v <= latest) / len(vals)

vix = data["^VIX"]["Close"].dropna()
vix_pct = pctl(vix.tolist(), float(vix.iloc[-1]))

hy_pct = None
if FRED_KEY:
    try:
        url = ("https://api.stlouisfed.org/fred/series/observations?series_id=BAMLH0A0HYM2"
               f"&api_key={FRED_KEY}&file_type=json&sort_order=desc&limit=260")
        with urllib.request.urlopen(url, timeout=30) as r:
            obs = json.load(r)["observations"]
        hy = [float(o["value"]) for o in obs if o["value"] not in (".", "")]
        hy_pct = pctl(hy, hy[0])
    except Exception as e:
        print("HY fail:", e)

if hy_pct is None:
    w = max(0.0, min(1.0, 0.6 * vix_pct + 0.4 * conv))
    method = "estimate v1b = 0.60*VIXpct(1y) + 0.40*C (HY unavailable)"
else:
    w = max(0.0, min(1.0, 0.45 * vix_pct + 0.35 * hy_pct + 0.20 * conv))
    method = "estimate v1 = 0.45*VIXpct(1y) + 0.35*HYOASpct(1y) + 0.20*C"

out = {
    "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "conv": {"value": round(conv, 3), "window": WINDOW, "basket": list(BASKET),
             "asof": conv_asof, "provenance": "core 5.1-5.2 (avg |rho|, all pairs)",
             "thresholds": {"tension": 0.38, "alert": 0.55}},
    "w": {"value": round(w, 3), "method": method, "label": "추정",
          "components": {"vix_pct": round(vix_pct, 3), "hy_pct": round(hy_pct, 3) if hy_pct is not None else None,
                          "conv": round(conv, 3)}},
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# Accumulate conv history (one row per asof date) — feeds the regime chip sparkline.
hist_path = os.path.join(os.path.dirname(OUT), "history", "conv.csv")
os.makedirs(os.path.dirname(hist_path), exist_ok=True)
rows = {}
if os.path.exists(hist_path):
    for ln in open(hist_path, encoding="utf-8"):
        parts = ln.strip().split(",")
        if len(parts) == 2:
            rows[parts[0]] = parts[1]
rows[conv_asof] = f"{conv:.3f}"
with open(hist_path, "w", encoding="utf-8") as fp:
    for d_ in sorted(rows):
        fp.write(f"{d_},{rows[d_]}\n")

print(f"regime.json written: conv={conv:.3f} ({conv_asof}), w={w:.3f} [{method}]")
