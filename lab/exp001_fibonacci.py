# EXP-001 — Fibonacci retracement test. Implements lab/EXP-001-PREREG.md EXACTLY.
# Prereg commit: 0cd4b2db34ed (verify: git log -- lab/EXP-001-PREREG.md)
# Output: /site/data/experiments/exp001.json  (verdict computed by code, zero override)
import datetime
import json
import os
import random

import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "data", "experiments", "exp001.json")
PREREG_COMMIT = "0cd4b2db34ed"
SEED = 42
THETA = 0.08
FIBS = (0.382, 0.618)
HALF = 0.04
B = 2000

px = yf.download("^GSPC", start="1985-01-01", end="2026-08-01", interval="1d",
                 progress=False, auto_adjust=True)
closes = px["Close"]["^GSPC"] if hasattr(px["Close"], "columns") else px["Close"]
closes = closes.dropna()
dates = [str(d.date()) for d in closes.index]
vals = [float(v) for v in closes.tolist()]

# --- zigzag pivots (θ=8%, closes) ---
pivots = []  # (index, price, 'H'|'L')
mode = None  # looking for confirmation of 'H' or 'L'
ext_i, ext_p = 0, vals[0]
for i, p in enumerate(vals):
    if mode in (None, "H"):  # tracking running max; confirm HIGH on ≥θ fall
        if p > ext_p:
            ext_i, ext_p = i, p
        elif p <= ext_p * (1 - THETA):
            pivots.append((ext_i, ext_p, "H"))
            mode = "L"
            ext_i, ext_p = i, p
            continue
    if mode == "L":  # tracking running min; confirm LOW on ≥θ rise
        if p < ext_p:
            ext_i, ext_p = i, p
        elif p >= ext_p * (1 + THETA):
            pivots.append((ext_i, ext_p, "L"))
            mode = "H"
            ext_i, ext_p = i, p
    elif mode is None:
        mode = "H" if p >= vals[0] else "H"

# --- retracement ratios r = (H2−L)/(H−L) for H→L→H2 ---
rs = []
for k in range(len(pivots) - 2):
    (i1, p1, t1), (i2, p2, t2), (i3, p3, t3) = pivots[k], pivots[k + 1], pivots[k + 2]
    if t1 == "H" and t2 == "L" and t3 == "H" and p1 > p2:
        r = (p3 - p2) / (p1 - p2)
        rs.append(min(r, 1.5))

def share_in(rlist, centers, half=HALF):
    n = 0
    for r in rlist:
        if any(abs(r - c) <= half for c in centers):
            n += 1
    return n / len(rlist)

s_obs = share_in(rs, FIBS)

random.seed(SEED)
null = []
while len(null) < B:
    c1 = random.uniform(0.15, 1.0)
    c2 = random.uniform(0.15, 1.0)
    if abs(c1 - c2) < 2 * HALF:  # non-overlapping windows
        continue
    null.append(share_in(rs, (c1, c2)))
p_value = sum(1 for s in null if s >= s_obs) / len(null)

verdict = "CLUSTERING DETECTED (H1 survives)" if p_value < 0.05 else \
          "REJECTED as opportunity candidate"

# histogram of null for the verdict-page chart
lo, hi = min(null), max(null)
bins = 24
width = (hi - lo) / bins or 1
hist = [0] * bins
for s in null:
    hist[min(bins - 1, int((s - lo) / width))] += 1

out = {
    "id": "EXP-001",
    "title": "Fibonacci retracement levels — special or folklore?",
    "prereg_commit": PREREG_COMMIT,
    "run_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "population": f"^GSPC daily closes {dates[0]} … {dates[-1]} ({len(vals)} sessions)",
    "swings_found": len(pivots),
    "n": len(rs),
    "s_obs": round(s_obs, 4),
    "null_mean": round(sum(null) / len(null), 4),
    "null_max": round(hi, 4),
    "p_value": round(p_value, 4),
    "alpha": 0.05,
    "verdict": verdict,
    "seed": SEED,
    "null_hist": {"lo": round(lo, 4), "hi": round(hi, 4), "counts": hist},
    "reproduce": "python lab/exp001_fibonacci.py",
    "core_ref": "Theory Core §5.8 · 공개 검증 과제 1호",
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"EXP-001: n={len(rs)} retracements from {len(pivots)} pivots")
print(f"S_obs={s_obs:.4f} vs null mean={out['null_mean']} → p={p_value:.4f} → {verdict}")
