"""Backtest phase 2b: walk history, fire mechanized card triggers, grade
observation windows, emit fires + scorecard + fire-calendar.

Reads  : pipeline/backtest/history/*.csv (from fetch_history.py)
Writes : site/data/backtest/fires.jsonl     one row per graded fire
         site/data/backtest/scorecard.json  per-card n / hits / era & gate splits
         site/data/backtest/calendar.json   date -> [card ids]  (fire calendar)

All outputs are a RECONSTRUCTION (est.): post-hoc, machine-selected days.
They are published separately from the live preregistered record and the
two are never merged into one statistic.

Conventions (README.md): naive-surprise substitution where consensus
history is paid; hit = sign of target move over [fire, fire+hi] matches
the card's bias (or the named non-price flag); a card cannot re-fire
inside its own open window; era split at 2015-01-01.
"""
import os, io, csv, json, math, datetime, statistics

HERE = os.path.dirname(os.path.abspath(__file__))
HIST = os.path.join(HERE, "history")
OUTD = os.path.normpath(os.path.join(HERE, "..", "..", "site", "data", "backtest"))
os.makedirs(OUTD, exist_ok=True)

def D(s): return datetime.date.fromisoformat(s)
def add(d, n): return d + datetime.timedelta(days=n)

class S:
    """Date-sorted series with as-of lookup."""
    def __init__(self, name):
        self.name, self.d, self.v = name, [], []
        p = os.path.join(HIST, name + ".csv")
        if os.path.exists(p):
            for r in csv.DictReader(io.open(p, encoding="utf-8")):
                self.d.append(D(r["date"])); self.v.append(float(r["value"]))
    def ok(self): return len(self.d) > 10
    def _i(self, dt):                      # index of last obs <= dt
        lo, hi = 0, len(self.d) - 1
        if hi < 0 or dt < self.d[0]: return -1
        while lo < hi:
            m = (lo + hi + 1) // 2
            if self.d[m] <= dt: lo = m
            else: hi = m - 1
        return lo
    def asof(self, dt):
        i = self._i(dt); return None if i < 0 else self.v[i]
    def chg_obs(self, i, n):               # value change over n observations
        return None if i - n < 0 else self.v[i] - self.v[i - n]
    def ret_obs(self, i, n):
        if i - n < 0 or self.v[i - n] == 0: return None
        return self.v[i] / self.v[i - n] - 1
    def ret_cal(self, d0, d1):             # pct return between as-of values
        a, b = self.asof(d0), self.asof(d1)
        if a is None or b is None or a == 0: return None
        return b / a - 1
    def diff_cal(self, d0, d1):
        a, b = self.asof(d0), self.asof(d1)
        if a is None or b is None: return None
        return b - a

def load(*names): return {n: S(n) for n in names}

# ── shared inputs ────────────────────────────────────────────────────
SER = load(
 "fred_SAHMREALTIME","fred_IC4WSA","fred_CES0500000003","fred_OPHNFB",
 "fred_CPIAUCSL","fred_CPILFESL","fred_WPSFD4131","fred_T10YIE","fred_DCOILWTICO",
 "fred_DGS10","fred_DGS2","fred_EXPINF5YR","fred_T10Y2Y","fred_USREC","fred_DFII10",
 "fred_DFEDTARU","fred_UNRATE","fred_WALCL","fred_WTREGEN","fred_RRPONTSYD",
 "fred_SOFR","fred_IORB","fred_IOER","fred_BAMLH0A0HYM2","fred_RSXFS","fred_PAYEMS",
 "yh_SPY","yh_QQQ","yh_TLT","yh_XLY","yh_XLK","yh_XLE","yh_XME","yh_GC_F","yh_CL_F",
 "yh__VIX","yh__VIX3M","yh__GSPC","yh_SB_F","yh_UUP","yh_EEM","yh_HYG",
 "yh_XLF","yh_XLV","yh_XLI","yh_XLP","yh_XLB","yh_XLU","yh_BTC-USD","yh_BDRY",
 "noaa_ONI","bn_funding_BTC","cot_ES","cot_CL","cot_GC","cot_EC",
 "pw_hormuz","pw_suez","pw_panama")

def naive_sds(s, use_pct):
    """Surprise vs naive forecast: delta_t vs mean/sd of previous 12 deltas."""
    out = []                               # (obs_date, sds)
    dl = []
    for i in range(1, len(s.d)):
        d = (s.v[i]/s.v[i-1]-1) if use_pct else (s.v[i]-s.v[i-1])
        dl.append((s.d[i], d))
    for i in range(12, len(dl)):
        prev = [x[1] for x in dl[i-12:i]]
        sd = statistics.pstdev(prev)
        if sd > 0:
            out.append((dl[i][0], (dl[i][1] - statistics.fmean(prev)) / sd))
    return out

def first_friday_next_month(m):
    d = (m.replace(day=28) + datetime.timedelta(days=4)).replace(day=1)
    return d + datetime.timedelta(days=(4 - d.weekday()) % 7)
def rel_cpi(m):    return (m.replace(day=28)+datetime.timedelta(days=4)).replace(day=12)
def rel_ppi(m):    return (m.replace(day=28)+datetime.timedelta(days=4)).replace(day=13)
def rel_retail(m): return (m.replace(day=28)+datetime.timedelta(days=4)).replace(day=15)

def realized20(s, dt):
    i = s._i(dt)
    if i < 21: return None
    rs = [math.log(s.v[j]/s.v[j-1]) for j in range(i-19, i+1)]
    return statistics.pstdev(rs) * math.sqrt(252) * 100

def yoy(s, i):
    d0 = s.d[i] - datetime.timedelta(days=365)
    a = s.asof(d0)
    return None if not a else s.v[i]/a - 1

# convergence: avg |rho(60d)| of the 7-asset basket, weekly steps (2008+)
def conv_series():
    basket = [SER[k] for k in ("yh__GSPC","yh_TLT","yh_GC_F","yh_CL_F","yh_UUP","yh_EEM","yh_HYG")]
    spx = SER["yh__GSPC"]
    out = []
    for i in range(1300, len(spx.d), 5):
        dt = spx.d[i]
        rets = []
        for s in basket:
            j = s._i(dt)
            if j < 61: rets.append(None); continue
            rets.append([s.v[k]/s.v[k-1]-1 for k in range(j-59, j+1)])
        cs, n = 0.0, 0
        for a in range(len(rets)):
            for b in range(a+1, len(rets)):
                if rets[a] is None or rets[b] is None: continue
                try: c = statistics.correlation(rets[a], rets[b])
                except Exception: continue
                cs += abs(c); n += 1
        if n >= 10: out.append((dt, cs/n))
    return out

def hurst_series():
    spx = SER["yh__GSPC"]; out = []
    for i in range(140, len(spx.d), 21):
        w = [math.log(spx.v[j]/spx.v[j-1]) for j in range(i-119, i+1)]
        m = statistics.fmean(w); dev, cum, mx, mn = 0.0, 0.0, -1e9, 1e9
        for x in w:
            cum += x - m; mx = max(mx, cum); mn = min(mn, cum)
        sd = statistics.pstdev(w)
        if sd > 0 and mx > mn:
            out.append((spx.d[i], math.log((mx-mn)/sd) / math.log(120)))
    return out

CONV = conv_series()
HURST = hurst_series()
def state_at(series, dt):
    lo, hi, best = 0, len(series)-1, None
    for d, v in series:
        if d <= dt: best = v
        else: break
    return best

# ── generic grading ─────────────────────────────────────────────────
def grade(tgt, dt, hi):
    kind = tgt[0]
    if kind == "ret":
        r = SER[tgt[1]].ret_cal(dt, add(dt, hi)); return r, (None if r is None else r > 0)
    if kind == "diff":
        r = SER[tgt[1]].diff_cal(dt, add(dt, hi)); return r, (None if r is None else r > 0)
    if kind == "rel":
        a = SER[tgt[1]].ret_cal(dt, add(dt, hi)); b = SER[tgt[2]].ret_cal(dt, add(dt, hi))
        if a is None or b is None: return None, None
        return a - b, a - b > 0
    return None, None

FIRES, DEFER = [], {}
def emit(card, dt, note, w, tgt_label, direction, ret, hit):
    FIRES.append({"card": card, "date": dt.isoformat(), "note": note,
        "w": w, "tgt": tgt_label, "dir": direction,
        "ret": None if ret is None else round(ret, 5),
        "hit": hit,
        "conv": (lambda c: None if c is None else round(c, 3))(state_at(CONV, dt)),
        "H": (lambda h: None if h is None else round(h, 3))(state_at(HURST, dt))})

def run_simple(card, cand, tgt, direction, hi, wlo=0):
    """cand: sorted [(date, note)]; dedup inside own window; grade at fire+hi."""
    last = None
    for dt, note in cand:
        if last and (dt - last).days < hi: continue
        last = dt
        ret, up = grade(tgt, dt, hi)
        hit = None if up is None else (up if direction == "up" else (not up))
        emit(card, dt, note, [wlo, hi], tgt[1] if len(tgt) > 1 else "", direction, ret, hit)

def crossings(s, level, above=True, sep=30):
    out, prev, lastd = [], None, None
    for i in range(len(s.d)):
        v = s.v[i]
        crossed = prev is not None and ((v >= level > prev) if above else (v < level <= prev))
        if crossed and (lastd is None or (s.d[i]-lastd).days >= sep):
            out.append((s.d[i], f"{s.name}={v:.2f}")); lastd = s.d[i]
        prev = v
    return out

# ═════ card implementations ═════════════════════════════════════════
# GRO-005 retail naive surprise
c = [(rel_retail(d), f"naiveSDS={z:.2f}") for d, z in naive_sds(SER["fred_RSXFS"], True) if z > 1.0]
run_simple("L-GRO-005", c, ("ret", "yh_XLY"), "up", 3)
# EMP-001 Sahm
run_simple("L-EMP-001", crossings(SER["fred_SAHMREALTIME"], 0.50, True, 365),
           ("rel", "yh_TLT", "yh_SPY"), "up", 126)
# EMP-002 NFP naive surprise -> 2Y up on release day (close vs prior close)
c = [(first_friday_next_month(d), f"naiveSDS={z:.2f}") for d, z in naive_sds(SER["fred_PAYEMS"], False) if z > 1.0]
last = None
for dt, note in c:
    if last and (dt - last).days < 1: continue
    last = dt
    r = SER["fred_DGS2"].diff_cal(add(dt, -1), dt)
    hit = None if r is None else r > 0
    emit("L-EMP-002", dt, note, [0, 0], "fred_DGS2", "up", r, hit)
# EMP-003 claims 4wMA turn
s = SER["fred_IC4WSA"]; cand = []
for i in range(60, len(s.d)):
    lo = min(s.v[max(0, i-260):i])
    if s.v[i] >= 1.10 * lo and s.v[i-1] < 1.10 * min(s.v[max(0, i-261):i-1]):
        cand.append((s.d[i], f"4wMA {s.v[i]:.0f} vs low {lo:.0f}"))
run_simple("L-EMP-003", cand, ("rel", "yh_TLT", "yh_SPY"), "up", 63)
# EMP-004 wage-productivity gap (2 consecutive quarters)
w, pr = SER["fred_CES0500000003"], SER["fred_OPHNFB"]; cand, run = [], 0
for i in range(14, len(pr.d)):
    wy = yoy(w, w._i(pr.d[i])); py = yoy(pr, i)
    if wy is None or py is None: continue
    run = run + 1 if (wy - py) > 0.02 else 0
    if run == 2: cand.append((pr.d[i], f"gap={(wy-py)*100:.1f}pp x2q"))
run_simple("L-EMP-004", cand, ("ret", "yh_SPY"), "down", 252)
# INF-001 CPI naive surprise
c = [(rel_cpi(d), f"naiveSDS={z:.2f}") for d, z in naive_sds(SER["fred_CPIAUCSL"], True) if z > 1.0]
run_simple("L-INF-001", c, ("diff", "fred_DGS2"), "up", 3)
# INF-002 PPI->CPI pipeline
pp, cp = SER["fred_WPSFD4131"], SER["fred_CPILFESL"]; cand = []
for i in range(4, len(pp.d)):
    j = cp._i(pp.d[i])
    if j < 4: continue
    pa = (pp.v[i]/pp.v[i-3]) ** 4 - 1; ca = (cp.v[j]/cp.v[j-3]) ** 4 - 1
    if pa - ca > 0.015: cand.append((rel_ppi(pp.d[i]), f"gap={(pa-ca)*100:.1f}pp"))
run_simple("L-INF-002", cand, ("diff", "fred_DGS10"), "up", 63)
# INF-003 BEI jolt
s = SER["fred_T10YIE"]
cand = [(s.d[i], f"d20={s.chg_obs(i,20)*100:.0f}bp") for i in range(20, len(s.d)) if s.chg_obs(i, 20) > 0.20]
run_simple("L-INF-003", cand, ("ret", "yh_XLE"), "up", 14)
# INF-004 oil second ignition
s = SER["fred_DCOILWTICO"]
cand = [(s.d[i], f"60d={s.ret_obs(i,42)*100:.0f}%") for i in range(42, len(s.d))
        if (s.ret_obs(i, 42) or 0) >= 0.25]
run_simple("L-INF-004", cand, ("diff", "fred_DGS10"), "up", 42, 21)
# INF-005 expectations anchor slip (Cleveland 5y substitute)
run_simple("L-INF-005", crossings(SER["fred_EXPINF5YR"], 3.2, True, 180),
           ("diff", "fred_DGS2"), "up", 21)
# RAT-001 2s10s inversion -> NBER recession within 504d
rec = SER["fred_USREC"]
for dt, note in crossings(SER["fred_T10Y2Y"], 0.0, False, 365):
    hit = any(rec.d[i] > dt and rec.d[i] <= add(dt, 504) and rec.v[i] == 1
              for i in range(len(rec.d)))
    emit("L-RAT-001", dt, note, [126, 504], "USREC", "recession", None, hit)
# RAT-002 real rates & gold
s = SER["fred_DFII10"]
cand = [(s.d[i], f"d20={s.chg_obs(i,20)*100:.0f}bp") for i in range(20, len(s.d))
        if (s.chg_obs(i, 20) or 0) <= -0.30]
run_simple("L-RAT-002", cand, ("ret", "yh_GC_F"), "up", 28)
# RAT-003 rate speed
s = SER["fred_DGS10"]
cand = [(s.d[i], f"d20=+{s.chg_obs(i,20)*100:.0f}bp") for i in range(20, len(s.d))
        if (s.chg_obs(i, 20) or 0) >= 0.50]
run_simple("L-RAT-003", cand, ("ret", "yh_XLK"), "down", 14)
# RAT-005 first cut, branched
tar, un = SER["fred_DFEDTARU"], SER["fred_UNRATE"]; lastcut = None
for i in range(1, len(tar.d)):
    if tar.v[i] < tar.v[i-1]:
        if lastcut is None or (tar.d[i] - lastcut).days >= 180:
            u_now = un.asof(tar.d[i]); u_then = un.asof(add(tar.d[i], -180))
            if u_now is None or u_then is None: lastcut = tar.d[i]; continue
            recess = (u_now - u_then) > 0.5
            r = SER["yh_SPY"].ret_cal(tar.d[i], add(tar.d[i], 252))
            hit = None if r is None else ((r < 0) if recess else (r > 0))
            emit("L-RAT-005", tar.d[i],
                 f"first cut, {'recessionary' if recess else 'insurance'}",
                 [0, 252], "yh_SPY", "branch", r, hit)
        lastcut = tar.d[i]
# RAT-006 taylor gap sustained 6 months
cp, un, tar = SER["fred_CPILFESL"], SER["fred_UNRATE"], SER["fred_DFEDTARU"]
cand, run = [], 0
for i in range(13, len(cp.d)):
    pi = yoy(cp, i); u = un.asof(cp.d[i]); pol = tar.asof(cp.d[i])
    if None in (pi, u, pol): continue
    taylor = 0.5 + pi*100 + 0.5*(pi*100 - 2) + (4.4 - u)
    run = run + 1 if taylor - pol > 1.5 else 0
    if run == 6: cand.append((cp.d[i], f"gap>{1.5}pp x6m"))
run_simple("L-RAT-006", cand, ("diff", "fred_DGS10"), "up", 252)
# LIQ-001 net liquidity tide
wa, tg, rr = SER["fred_WALCL"], SER["fred_WTREGEN"], SER["fred_RRPONTSYD"]
nl = []
for i in range(len(wa.d)):
    t = tg.asof(wa.d[i]); r = rr.asof(wa.d[i]) or 0
    # units: WALCL & WTREGEN in $M, RRPONTSYD in $B -> net liquidity in $B
    if t is not None: nl.append((wa.d[i], wa.v[i]/1000 - t/1000 - r))
chg = [(nl[i][0], nl[i][1]-nl[i-4][1]) for i in range(4, len(nl))]
cand = []
for i in range(52, len(chg)):
    win = [x[1] for x in chg[i-52:i]]
    sd = statistics.pstdev(win)
    if sd > 0 and (chg[i][1]-statistics.fmean(win))/sd > 1.0:
        cand.append((chg[i][0], f"4w dNL z>+1"))
run_simple("L-LIQ-001", cand, ("ret", "yh_QQQ"), "up", 28, 7)
# LIQ-002 RRP drawdown
cand = []
for i in range(20, len(rr.d)):
    if rr.v[i-20] < 100: continue
    if rr.v[i]/rr.v[i-20]-1 <= -0.15:
        t0, t1 = tg.asof(rr.d[i-20]), tg.asof(rr.d[i])
        if t0 and t1 and t1/t0-1 >= 0.15: continue
        cand.append((rr.d[i], f"RRP 4w {100*(rr.v[i]/rr.v[i-20]-1):.0f}%"))
run_simple("L-LIQ-002", cand, ("ret", "yh_SPY"), "up", 28, 7)
# LIQ-003 SOFR spike (IORB stitched with IOER pre-2021)
so, io_, ie = SER["fred_SOFR"], SER["fred_IORB"], SER["fred_IOER"]
cand = []
for i in range(len(so.d)):
    base = io_.asof(so.d[i]) or ie.asof(so.d[i])
    if base is not None and so.v[i] - base > 0.10:
        cand.append((so.d[i], f"SOFR-adm=+{(so.v[i]-base)*100:.0f}bp"))
run_simple("L-LIQ-003", cand, ("ret", "yh_SPY"), "down", 7)
# POS-001 COT extremes (contrarian), per market
for mkt, tgt, in [("cot_ES", ("ret","yh_SPY")), ("cot_CL", ("ret","yh_CL_F")),
                  ("cot_GC", ("ret","yh_GC_F")), ("cot_EC", ("ret","yh_UUP"))]:
    s = SER[mkt]; cand = []
    for i in range(156, len(s.d)):
        win = s.v[i-156:i]; sd = statistics.pstdev(win)
        if sd == 0: continue
        z = (s.v[i]-statistics.fmean(win))/sd
        if abs(z) > 2: cand.append((s.d[i], f"{mkt[4:]} z={z:+.1f}"))
    last = None
    for dt, note in cand:
        if last and (dt-last).days < 56: continue
        last = dt
        z = float(note.split("=")[1])
        contrarian_down = z > 0 if mkt != "cot_EC" else z < 0
        r, up = grade(tgt, dt, 56)
        hit = None if up is None else ((not up) if contrarian_down else up)
        emit("L-POS-001", dt, note, [7, 56], tgt[1], "contrarian", r, hit)
# POS-002 funding extremes
s = SER["bn_funding_BTC"]; cand = []
for i in range(len(s.d)):
    ann = s.v[i] * 365
    if ann > 0.5 or ann < -0.2: cand.append((s.d[i], f"funding ann={ann*100:.0f}%"))
last = None
for dt, note in cand:
    if last and (dt-last).days < 21: continue
    last = dt
    pos = float(note.split("=")[1].rstrip("%")) > 0
    r, up = grade(("ret","yh_BTC-USD"), dt, 21)
    hit = None if up is None else ((not up) if pos else up)
    emit("L-POS-002", dt, note, [3, 21], "yh_BTC-USD", "contrarian", r, hit)
# PHY-002 BDI proxy
s = SER["yh_BDRY"]
cand = [(s.d[i], f"20d=+{s.ret_obs(i,20)*100:.0f}%") for i in range(20, len(s.d))
        if (s.ret_obs(i, 20) or 0) >= 0.30]
run_simple("L-PHY-002", cand, ("ret", "yh_XME"), "up", 42, 14)
# PHY-004 chokepoint transit collapse
for nm in ("pw_hormuz", "pw_suez", "pw_panama"):
    s = SER[nm]
    if not s.ok(): continue
    cand = []
    for i in range(90, len(s.d)):
        w7 = statistics.fmean(s.v[i-6:i+1]); w90 = statistics.fmean(s.v[i-89:i+1])
        if w90 > 0 and w7 <= 0.8 * w90:
            cand.append((s.d[i], f"{nm[3:]} 7d/90d={w7/w90:.2f}"))
    run_simple("L-PHY-004", cand, ("ret", "yh_CL_F"), "up", 28)
# PHY-006 El Nino
run_simple("L-PHY-006", crossings(SER["noaa_ONI"], 1.0, True, 300),
           ("ret", "yh_SB_F"), "up", 189, 21)
# MKT-001 convergence alarm
cand, prev, lastd = [], None, None
for d, v in CONV:
    if prev is not None and v >= 0.55 > prev and (lastd is None or (d-lastd).days >= 28):
        cand.append((d, f"avg|rho|={v:.2f}")); lastd = d
    prev = v
run_simple("L-MKT-001", cand, ("ret", "yh_SPY"), "down", 28)
# MKT-002 credit leads - PROXY: FRED serves ICE HY OAS only ~3y back
# (licensing truncation), so credit stress = HYG underperforming IEF
# by 4%+ over 20 obs (2007+). Substitution stated in scorecard notes.
hyg, ief = SER["yh_HYG"], SER["yh_TLT"]
cand = []
for i in range(20, len(hyg.d)):
    j = ief._i(hyg.d[i])
    if j < 20: continue
    rel = (hyg.v[i]/hyg.v[i-20]) - (ief.v[j]/ief.v[j-20])
    if rel <= -0.04:
        cand.append((hyg.d[i], f"HYG-TLT 20d={rel*100:.1f}%"))
run_simple("L-MKT-002", cand, ("ret", "yh_SPY"), "down", 42)
# MKT-003 VIX backwardation
v, v3 = SER["yh__VIX"], SER["yh__VIX3M"]; cand = []
prevb = False
for i in range(len(v.d)):
    b3 = v3.asof(v.d[i])
    if b3 is None: continue
    b = v.v[i] > b3
    if b and not prevb: cand.append((v.d[i], f"VIX {v.v[i]:.0f} > 3M {b3:.0f}"))
    prevb = b
run_simple("L-MKT-003", cand, ("ret", "yh_SPY"), "down", 14)
# MKT-006 sector momentum 12-1 (monthly cross-section, 9 sectors)
SEC = ["yh_XLK","yh_XLE","yh_XLF","yh_XLV","yh_XLI","yh_XLP","yh_XLY","yh_XLB","yh_XLU"]
spy = SER["yh_SPY"]; monthly = [spy.d[i] for i in range(len(spy.d)-1)
                                if spy.d[i].month != spy.d[i+1].month]
for dt in monthly:
    if dt.year < 2000: continue
    scores = []
    for k in SEC:
        s = SER[k]
        r13 = s.ret_cal(add(dt, -390), add(dt, -30))
        if r13 is not None: scores.append((r13, k))
    if len(scores) < 9: continue
    scores.sort(reverse=True)
    top = [k for _, k in scores[:3]]; bot = [k for _, k in scores[-3:]]
    rt = [SER[k].ret_cal(dt, add(dt, 63)) for k in top]
    rb = [SER[k].ret_cal(dt, add(dt, 63)) for k in bot]
    if None in rt or None in rb: continue
    spread = statistics.fmean(rt) - statistics.fmean(rb)
    emit("L-MKT-006", dt, f"top:{','.join(t[3:] for t in top)}",
         [21, 63], "sector 12-1 L/S", "up", spread, spread > 0)
# MKT-007 volatility premium (monthly harvest test)
for dt in monthly:
    iv = v.asof(dt); rv = realized20(SER["yh__GSPC"], dt)
    if iv is None or rv is None or iv - rv <= 4: continue
    rv_fwd = realized20(SER["yh__GSPC"], add(dt, 30))
    if rv_fwd is None: continue
    emit("L-MKT-007", dt, f"IV-RV={iv-rv:.1f}p", [21, 21], "IV vs fwd RV",
         "harvest", round(iv - rv_fwd, 2), iv > rv_fwd)
# EVT-001 FOMC pre-drift (official meeting dates scraped from the Fed)
fomc = S("manual_fomc")
spyS = SER["yh_SPY"]
for i in range(len(fomc.d)):
    T = fomc.d[i]
    if T > datetime.date.today(): break
    r = spyS.ret_cal(add(T, -2), add(T, -1))     # the pre-announcement drift day
    if r is None: continue
    emit("L-EVT-001", add(T, -1), f"FOMC {T.isoformat()}", [0, 1], "yh_SPY", "up", r, r > 0)
# EVT-003 OPEC prisoner's dilemma (curated event table, sources in CSV)
op = os.path.join(HERE, "manual_opec.csv")
if os.path.exists(op):
    for row in csv.DictReader(io.open(op, encoding="utf-8")):
        dt = D(row["date"]); direction = "down" if row["type"] == "bear" else "up"
        r, up = grade(("ret", "yh_CL_F"), dt, 5)
        hit = None if up is None else (up if direction == "up" else (not up))
        emit("L-EVT-003", dt, row["type"] + ": " + row["event"][:46], [0, 5], "yh_CL_F",
             direction, r, hit)
# PHY-005 inventory floor (activates when EIA_API_KEY fetched the series)
eia = S("eia_WCESTUS1")
if eia.ok():
    cand = []
    for i in range(260, len(eia.d)):
        woy = eia.d[i].isocalendar()[1]
        band = [eia.v[j] for j in range(max(0, i-52*5), i)
                if abs(eia.d[j].isocalendar()[1] - woy) <= 2]
        if band and eia.v[i] < min(band):
            cand.append((eia.d[i], f"stocks below 5y band"))
    run_simple("L-PHY-005", cand, ("ret", "yh_CL_F"), "up", 28)
# EVT-004 election uncertainty (US presidential)
ELEC = ["2000-11-07","2004-11-02","2008-11-04","2012-11-06","2016-11-08","2020-11-03","2024-11-05"]
for e in ELEC:
    ed = D(e); fire = add(ed, -60)
    pre = [v.asof(add(fire, -k)) for k in range(0, 10)]
    near = [v.asof(add(ed, -k)) for k in range(0, 10)]
    pre = [x for x in pre if x]; near = [x for x in near if x]
    if not pre or not near: continue
    emit("L-EVT-004", fire, f"election {e}", [0, 60], "^VIX",
         "up", round(statistics.fmean(near)-statistics.fmean(pre), 2),
         statistics.fmean(near) > statistics.fmean(pre))

DEFER = {
 "deferred_in_phase2": {
   "L-GRO-006": "GDPNow vintage xlsx parsing",
   "L-LIQ-005": "multi-country M2 aggregate assembly",
   "L-POS-003": "CBOE put/call history endpoint unstable",
   "L-POS-004": "ICI flow scrape",
   "L-PHY-001": "NOAA degree-day harvest + KRBN short history",
   "L-PHY-005": "code ready - activates once the free EIA_API_KEY is set"},
 "substitutions_note": {
   "L-MKT-002": "FRED serves ICE HY OAS only ~3y back (licensing); stress proxied as HYG underperforming TLT by 4%+/20 obs",
   "L-EMP-002/L-INF-001/L-GRO-005": "surprise vs naive forecast (no free consensus history); release dates approximated",
   "L-INF-005": "Cleveland Fed 5y expected inflation instead of Michigan 5y",
   "L-MKT-006": "cross-section at sector-ETF level (9 sectors)",
   "L-PHY-002": "BDRY ETF proxy (2018+) instead of licensed Baltic index"},
 "blocked_by_data": ["L-GRO-001","L-GRO-002","L-GRO-003","L-GRO-004",
   "L-RAT-004","L-LIQ-004","L-PHY-003","L-MKT-004","L-EVT-002","L-EVT-005"]}

# ── series-lite: weekly gauge pack for the free-replay stage ────────
def _weekly_dates():
    d, out = D("1998-01-05"), []
    end = datetime.date.today()
    while d <= end: out.append(d); d = add(d, 7)
    return out

def _pack(fn):
    out = []
    for d in _weekly_dates():
        v = fn(d)
        if v is not None: out.append([d.isoformat(), round(v, 3)])
    return out

hyg, tlt = SER["yh_HYG"], SER["yh_TLT"]
def _credit(d):
    i, j = hyg._i(d), tlt._i(d)
    if i < 20 or j < 20: return None
    return ((hyg.v[i]/hyg.v[i-20]) - (tlt.v[j]/tlt.v[j-20])) * 100
def _series_chg(s, n, mul):
    def f(d):
        i = s._i(d)
        return None if i < n else (s.v[i]-s.v[i-n]) * mul
    return f
def _series_ret(s, n):
    def f(d):
        i = s._i(d)
        return None if i < n or s.v[i-n] == 0 else (s.v[i]/s.v[i-n]-1)*100
    return f
_nlmap = dict((x[0], x[1]) for x in nl)
_nld = sorted(_nlmap)
def _netliq4w(d):
    ks = [k for k in _nld if k <= d]
    if len(ks) < 5: return None
    return _nlmap[ks[-1]] - _nlmap[ks[-5]]

LITE = {
 "conv":  {"label":"Convergence — avg |ρ|","label_ko":"수렴도 — 평균 |ρ|","unit":"","dec":2,
           "th":0.55,"dir":"ge","data":[[d.isoformat(),round(v,3)] for d,v in CONV]},
 "credit":{"label":"Credit — HYG vs TLT 20d","label_ko":"크레딧 — HYG-TLT 20일","unit":"%","dec":1,
           "th":-4.0,"dir":"le","data":_pack(_credit)},
 "vix":   {"label":"Fear — VIX","label_ko":"공포 — VIX","unit":"","dec":1,
           "th":30,"dir":"ge","data":_pack(lambda d: SER["yh__VIX"].asof(d))},
 "wti60": {"label":"Oil — 60d change","label_ko":"유가 — 60일 변화","unit":"%","dec":1,
           "th":25,"dir":"ge","data":_pack(_series_ret(SER["fred_DCOILWTICO"], 42))},
 "y10":   {"label":"10Y — 20d change","label_ko":"미10년 — 20일 변화","unit":"bp","dec":0,
           "th":50,"dir":"ge","data":_pack(_series_chg(SER["fred_DGS10"], 20, 100))},
 "netliq":{"label":"Net liquidity — 4w Δ","label_ko":"순유동성 — 4주 Δ","unit":"$B","dec":0,
           "th":0,"dir":"ge","data":_pack(_netliq4w)},
}
with io.open(os.path.join(OUTD, "series-lite.json"), "w", encoding="utf-8") as f:
    json.dump(LITE, f, ensure_ascii=False)

# ── outputs ─────────────────────────────────────────────────────────
FIRES.sort(key=lambda r: (r["date"], r["card"]))
with io.open(os.path.join(OUTD, "fires.jsonl"), "w", encoding="utf-8") as f:
    for r in FIRES: f.write(json.dumps(r, ensure_ascii=False) + "\n")

cards = {}
for r in FIRES:
    c0 = cards.setdefault(r["card"], {"n":0,"hits":0,"graded":0,
        "era":{"pre2015":[0,0],"post2015":[0,0]},
        "gate":{"conv_hi":[0,0],"conv_lo":[0,0]}})
    c0["n"] += 1
    if r["hit"] is not None:
        c0["graded"] += 1; c0["hits"] += 1 if r["hit"] else 0
        era = "pre2015" if r["date"] < "2015-01-01" else "post2015"
        c0["era"][era][0] += 1; c0["era"][era][1] += 1 if r["hit"] else 0
        if r["conv"] is not None:
            g = "conv_hi" if r["conv"] >= 0.55 else "conv_lo"
            c0["gate"][g][0] += 1; c0["gate"][g][1] += 1 if r["hit"] else 0
for cid, c0 in cards.items():
    c0["rate"] = round(c0["hits"]/c0["graded"], 3) if c0["graded"] else None

score = {"generated": datetime.date.today().isoformat(),
         "label": "reconstructed backtest (est.) - separate from live preregistered grading",
         "conventions": "see pipeline/backtest/README.md",
         "cards": cards, **DEFER}
with io.open(os.path.join(OUTD, "scorecard.json"), "w", encoding="utf-8") as f:
    json.dump(score, f, ensure_ascii=False, indent=1)

cal = {}
for r in FIRES: cal.setdefault(r["date"], []).append(r["card"])
with io.open(os.path.join(OUTD, "calendar.json"), "w", encoding="utf-8") as f:
    json.dump(cal, f, ensure_ascii=False)

print(f"fires: {len(FIRES)} rows across {len(cards)} cards -> {OUTD}")
for cid in sorted(cards):
    c0 = cards[cid]
    print(f"  {cid}: n={c0['graded']}/{c0['n']} hit={c0['rate']}")
