# EXP-003 — Credit leads equities. Implements lab/EXP-003-PREREG.md EXACTLY.
# Prereg commit: a4ec46105699
# Output: /site/data/experiments/exp003.json (verdict computed by code, zero override)
import datetime
import json
import math
import os
import random
import urllib.request

import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "data", "experiments", "exp003.json")
PREREG_COMMIT = "a4ec46105699 + amend ea8b825034ed"
SEED = 42
K_SIGMA = 1.5
TRAIL = 252
COOLDOWN = 5
FWD = 5
B = 2000
FRED_KEY = os.environ.get("FRED_API_KEY")

url = ("https://api.stlouisfed.org/fred/series/observations?series_id=BAA10Y"
       f"&api_key={FRED_KEY}&file_type=json&sort_order=asc&limit=100000"
       "&observation_end=2026-07-31")  # Amendment 1: BAA10Y full history (1986~)
with urllib.request.urlopen(url, timeout=60) as r:
    obs = json.load(r)["observations"]
oas = [(o["date"], float(o["value"])) for o in obs if o["value"] not in (".", "")]

px = yf.download("^GSPC", start="1996-01-01", end="2026-08-01", interval="1d",
                 progress=False, auto_adjust=True)
closes = px["Close"]["^GSPC"] if hasattr(px["Close"], "columns") else px["Close"]
closes = closes.dropna()
spx_dates = [str(d.date()) for d in closes.index]
spx_vals = [float(v) for v in closes.tolist()]

def fwd_return(date):
    """entry = last SPX close ≤ date; exit = 5th close after entry."""
    import bisect
    i = bisect.bisect_right(spx_dates, date) - 1
    if i < 0 or i + FWD >= len(spx_vals):
        return None
    return math.log(spx_vals[i + FWD] / spx_vals[i])

d5 = {}
for i in range(5, len(oas)):
    d5[i] = oas[i][1] - oas[i - 5][1]

signals, eligible = [], []
last_sig_i = -99
for i in range(5 + TRAIL, len(oas)):
    window = [d5[j] for j in range(i - TRAIL, i) if j in d5]
    if len(window) < TRAIL * 0.9:
        continue
    m = sum(window) / len(window)
    sd = math.sqrt(sum((x - m) ** 2 for x in window) / len(window))
    if sd == 0:
        continue
    r = fwd_return(oas[i][0])
    if r is None:
        continue
    is_sig = d5[i] >= K_SIGMA * sd
    if is_sig and i - last_sig_i <= COOLDOWN:
        last_sig_i = i
        continue  # 쿨다운 — 연속 신호 중복 계산 방지 (eligible에서도 제외)
    if is_sig:
        last_sig_i = i
        signals.append((oas[i][0], round(d5[i], 3), r))
    else:
        eligible.append(r)

m_sig = sum(s[2] for s in signals) / len(signals)
neg = sum(1 for s in signals if s[2] < 0)

random.seed(SEED)
null = []
for _ in range(B):
    draw = random.sample(eligible, len(signals))
    null.append(sum(draw) / len(draw))
p_value = sum(1 for m in null if m <= m_sig) / len(null)
m_null = sum(null) / len(null)

confirmed = p_value < 0.05
verdict = "CONFIRMED — credit widening carries 5-day downside information" if confirmed \
    else "NOT CONFIRMED"

lo_v, hi_v = min(null + [m_sig]), max(null + [m_sig])
bins = 24
w = (hi_v - lo_v) / bins or 1
hist = [0] * bins
for m in null:
    hist[min(bins - 1, int((m - lo_v) / w))] += 1

out = {
    "id": "EXP-003",
    "title": "Credit leads equities — does a HY-spread shock predict weak weeks?",
    "prereg_commit": PREREG_COMMIT,
    "run_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "population": f"Baa−10Y spread BAA10Y (FRED) {oas[0][0]} … {oas[-1][0]} · ^GSPC forward 5d",
    "n_signals": len(signals), "n_eligible": len(eligible),
    "mean_fwd_signal_pct": round(m_sig * 100, 3),
    "mean_fwd_null_pct": round(m_null * 100, 3),
    "hit_rate_neg": round(neg / len(signals), 3),
    "worst_pct": round(min(s[2] for s in signals) * 100, 2),
    "delta_obs": round((m_sig - m_null) * 100, 3),
    "s_obs": round(m_sig * 100, 3),
    "p_value": round(p_value, 4), "alpha": 0.05,
    "confirmed": confirmed, "verdict": verdict,
    "seed": SEED,
    "recent_signals": [{"date": s[0], "d5": s[1], "fwd_pct": round(s[2] * 100, 2)}
                        for s in signals[-5:]],
    "null_hist": {"lo": round(lo_v * 100, 3), "hi": round(hi_v * 100, 3), "counts": hist},
    "reproduce": "python lab/exp003_credit.py",
    "core_ref": "코어 2.6 (크레딧 선행) · 원장 크레딧 카드군 (A−)",
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"EXP-003: signals={len(signals)}, eligible={len(eligible)}")
print(f"mean fwd 5d after signal = {m_sig*100:.3f}% vs null {m_null*100:.3f}% "
      f"(hit neg {neg}/{len(signals)}) → p={p_value:.4f}")
print(verdict)
