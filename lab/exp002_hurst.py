# EXP-002 — Hurst switch (Gate G3). Implements lab/EXP-002-PREREG.md EXACTLY.
# Prereg commit: e77b0315e9e5
# Output: /site/data/experiments/exp002.json (verdict computed by code, zero override)
import datetime
import json
import math
import os
import random

import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "data", "experiments", "exp002.json")
PREREG_COMMIT = "e77b0315e9e5"
SEED = 42
WIN = 120
NS = (15, 30, 60, 120)
HI, LO = 0.55, 0.45
HORIZON = 20
STRIDE = 5
BLOCK = 12
B = 2000

px = yf.download("^GSPC", start="1985-01-01", end="2026-08-01", interval="1d",
                 progress=False, auto_adjust=True)
closes = px["Close"]["^GSPC"] if hasattr(px["Close"], "columns") else px["Close"]
closes = closes.dropna()
vals = [float(v) for v in closes.tolist()]
rets = [math.log(vals[i] / vals[i - 1]) for i in range(1, len(vals))]

def rs_block(seg):
    m = sum(seg) / len(seg)
    dev, cum, mx, mn = 0.0, 0.0, -1e18, 1e18
    var = 0.0
    for x in seg:
        cum += x - m
        mx = max(mx, cum); mn = min(mn, cum)
        var += (x - m) ** 2
    sd = math.sqrt(var / len(seg))
    if sd == 0:
        return None
    return (mx - mn) / sd

def hurst(window):
    xs, ys = [], []
    for n in NS:
        k = len(window) // n
        vals_n = [rs_block(window[i * n:(i + 1) * n]) for i in range(k)]
        vals_n = [v for v in vals_n if v]
        if not vals_n:
            continue
        xs.append(math.log(n)); ys.append(math.log(sum(vals_n) / len(vals_n)))
    if len(xs) < 3:
        return None
    mx = sum(xs) / len(xs); my = sum(ys) / len(ys)
    num = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    den = sum((x - mx) ** 2 for x in xs)
    return num / den if den else None

# --- sampled days with H, continuation indicator ---
samples = []  # (label, C)
for t in range(WIN, len(rets) - HORIZON, STRIDE):
    if t - HORIZON + 1 < 1:
        continue
    h = hurst(rets[t - WIN:t])
    if h is None:
        continue
    past = sum(rets[t - HORIZON:t])
    futr = sum(rets[t:t + HORIZON])
    if past == 0 or futr == 0:
        continue
    c = 1 if (past > 0) == (futr > 0) else 0
    label = "HIGH" if h > HI else "LOW" if h < LO else "MID"
    samples.append((label, c))

hi_c = [c for l, c in samples if l == "HIGH"]
lo_c = [c for l, c in samples if l == "LOW"]
p_hi = sum(hi_c) / len(hi_c)
p_lo = sum(lo_c) / len(lo_c)
d_obs = p_hi - p_lo

# --- block permutation ---
random.seed(SEED)
labels = [l for l, _ in samples]
cs = [c for _, c in samples]
nblocks = math.ceil(len(labels) / BLOCK)
null = []
guard = 0
while len(null) < B and guard < B * 20:
    guard += 1
    order = list(range(nblocks))
    random.shuffle(order)
    perm = []
    for b in order:
        perm.extend(labels[b * BLOCK:(b + 1) * BLOCK])
    perm = perm[:len(cs)]
    h2 = [c for l, c in zip(perm, cs) if l == "HIGH"]
    l2 = [c for l, c in zip(perm, cs) if l == "LOW"]
    if not h2 or not l2:
        continue
    null.append(sum(h2) / len(h2) - sum(l2) / len(l2))
p_value = sum(1 for d in null if d >= d_obs) / len(null)

confirmed = p_value < 0.05
verdict = "G3 CONFIRMED at this horizon" if confirmed else \
          "NOT CONFIRMED — gate stays an estimate, β_g conservative"

lo_v, hi_v = min(null), max(null)
bins = 24
w = (hi_v - lo_v) / bins or 1
hist = [0] * bins
for d in null:
    hist[min(bins - 1, int((d - lo_v) / w))] += 1

out = {
    "id": "EXP-002",
    "title": "Hurst switch — does H(120) really separate trend and mean-reversion regimes?",
    "prereg_commit": PREREG_COMMIT,
    "run_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "population": f"^GSPC daily {closes.index[0].date()} … {closes.index[-1].date()} ({len(vals)} sessions)",
    "n_sampled": len(samples),
    "n_high": len(hi_c), "n_low": len(lo_c),
    "p_cont_high": round(p_hi, 4), "p_cont_low": round(p_lo, 4),
    "delta_obs": round(d_obs, 4),
    "p_value": round(p_value, 4), "alpha": 0.05,
    "confirmed": confirmed, "verdict": verdict,
    "seed": SEED,
    "null_hist": {"lo": round(lo_v, 4), "hi": round(hi_v, 4), "counts": hist},
    "reproduce": "python lab/exp002_hurst.py",
    "core_ref": "Gate G3 · Theory Core §5.9·8.2 · Ledger 3층",
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"EXP-002: sampled={len(samples)} (HIGH {len(hi_c)}, LOW {len(lo_c)})")
print(f"P(cont|HIGH)={p_hi:.4f} vs P(cont|LOW)={p_lo:.4f} → Δ={d_obs:.4f}, p={p_value:.4f}")
print(verdict)
