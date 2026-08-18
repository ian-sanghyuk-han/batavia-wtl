# Event Card auto-grading engine (charter M2): deterministic checkpoint grades,
# ±0.1% direction rule, zero human override. -> /site/data/grading.json
# Until the target event (CPI 2026-09-11) passes, runs a REHEARSAL on the previous
# CPI (2026-08-12) to prove the machine works — clearly labeled, not a track record.
import datetime
import json
import os
import urllib.request

import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "data", "grading.json")
FRED_KEY = os.environ.get("FRED_API_KEY")

TARGET_ID = "CPI-2026-08"
TARGET_RELEASE_UTC = datetime.datetime(2026, 9, 11, 12, 30, tzinfo=datetime.timezone.utc)
REHEARSAL_RELEASE_UTC = datetime.datetime(2026, 8, 12, 12, 30, tzinfo=datetime.timezone.utc)

DIR_TH = 0.1   # ±0.1% direction rule (§6.3)
BP_TH = 1.0    # 2y neutral band ±1bp


def sign_pct(x, th=DIR_TH):
    return "상승" if x > th else "하락" if x < -th else "중립"


def fred_map(sid, start="2026-06-01"):
    url = (f"https://api.stlouisfed.org/fred/series/observations?series_id={sid}"
           f"&api_key={FRED_KEY}&file_type=json&sort_order=asc&observation_start={start}")
    with urllib.request.urlopen(url, timeout=30) as r:
        obs = json.load(r)["observations"]
    return {o["date"]: float(o["value"]) for o in obs if o["value"] not in (".", "")}


def grade(release_utc, label):
    rel_date = release_utc.date().isoformat()
    g = {"label": label, "release_utc": release_utc.isoformat(), "checkpoints": [], "verdicts": []}

    # --- C1/C2: ES=F futures 15m around release (cash market closed at 08:30 ET) ---
    try:
        es = yf.download("ES=F", period="55d", interval="15m", progress=False, auto_adjust=True)
        closes = es["Close"]["ES=F"] if hasattr(es["Close"], "columns") else es["Close"]
        closes = closes.dropna()
        t0 = closes.index.asof(release_utc)
        t1 = closes.index.asof(release_utc + datetime.timedelta(minutes=30))
        t2 = closes.index.asof(release_utc + datetime.timedelta(minutes=60))
        p0, p1, p2 = float(closes[t0]), float(closes[t1]), float(closes[t2])
        m1 = (p1 / p0 - 1) * 100
        m2 = (p2 / p0 - 1) * 100
        g["checkpoints"].append({"name": "C1 발표 직후 30분 (S&P 선물)", "move_pct": round(m1, 2),
                                 "dir": sign_pct(m1), "src": "ES=F 15m"})
        g["checkpoints"].append({"name": "C2 발표 후 60분 정착 (S&P 선물)", "move_pct": round(m2, 2),
                                 "dir": sign_pct(m2), "src": "ES=F 15m"})
    except Exception as e:
        g["checkpoints"].append({"name": "C1/C2", "error": f"선물 인트라데이 데이터 없음 ({e})"})

    # --- C3: next KRX session open vs prior close ---
    try:
        ks = yf.download("^KS11", period="60d", interval="1d", progress=False, auto_adjust=True)
        opens = ks["Open"]["^KS11"] if hasattr(ks["Open"], "columns") else ks["Open"]
        closes_k = ks["Close"]["^KS11"] if hasattr(ks["Close"], "columns") else ks["Close"]
        after = [d for d in opens.dropna().index if d.date() > release_utc.date()]
        d_next = after[0]
        prior = [d for d in closes_k.dropna().index if d < d_next][-1]
        m3 = (float(opens[d_next]) / float(closes_k[prior]) - 1) * 100
        g["checkpoints"].append({"name": f"C3 익일 KRX 개장 ({d_next.date()})", "move_pct": round(m3, 2),
                                 "dir": sign_pct(m3), "src": "^KS11 open"})
    except Exception as e:
        g["checkpoints"].append({"name": "C3", "error": f"KRX 데이터 없음 ({e})"})

    # --- actual CPI class vs naive benchmark (same rule as the card's scenario table) ---
    actual_cls = None
    try:
        cpi = fred_map("CPIAUCSL", "2024-06-01")
        months = sorted(cpi)
        mom = {months[i]: (cpi[months[i]] / cpi[months[i - 1]] - 1) * 100 for i in range(1, len(months))}
        rel_month = release_utc.date().replace(day=1)
        reported = (rel_month - datetime.timedelta(days=1)).replace(day=1).isoformat()
        mkeys = sorted(k for k in mom if k < reported)[-12:]
        naive = sorted(mom[k] for k in mkeys)[len(mkeys) // 2]
        sup = mom[reported] - naive
        actual_cls = "상방" if sup > 0.05 else "하방" if sup < -0.05 else "부합"
        g["actual"] = {"reported_month": reported[:7], "mom": round(mom[reported], 2),
                       "naive_expectation": round(naive, 2), "surprise": round(sup, 3),
                       "class": actual_cls}
    except Exception as e:
        g["actual"] = {"error": str(e)}

    # --- verdicts: card's historical class stats vs realized moves ---
    try:
        card = json.load(open(os.path.join(HERE, "..", "site", "data", "event_card.json"), encoding="utf-8"))
        cls_map = {"상방": "hot", "부합": "inline", "하방": "cool"}
        sc = card.get("scenarios", {}).get("classes", {})
        hist = sc.get(cls_map.get(actual_cls, ""), None)
        spx = yf.download("^GSPC", period="60d", interval="1d", progress=False, auto_adjust=True)
        sc_close = spx["Close"]["^GSPC"] if hasattr(spx["Close"], "columns") else spx["Close"]
        sc_close = sc_close.dropna()
        dts = [d for d in sc_close.index if d.date() <= release_utc.date()]
        d0_real = (float(sc_close[dts[-1]]) / float(sc_close[dts[-2]]) - 1) * 100 \
            if dts and dts[-1].date() == release_utc.date() else None
        if hist and d0_real is not None:
            hit = "적중 ✓" if (sign_pct(hist["d0"]) == sign_pct(d0_real)) else \
                  ("중립 —" if sign_pct(d0_real) == "중립" else "불일치 ✗")
            g["verdicts"].append({"name": "판정 A — 기준자산 D+0 방향 (과거 동급 평균 대비)",
                                  "expected": f"{'+' if hist['d0']>=0 else ''}{hist['d0']}% (n={hist['n']})",
                                  "realized": f"{'+' if d0_real>=0 else ''}{round(d0_real,2)}%",
                                  "verdict": hit})
        dgs2 = fred_map("DGS2")
        ds2 = sorted(d for d in dgs2 if d <= rel_date)
        if hist and hist.get("r2_bp") is not None and len(ds2) >= 2 and ds2[-1] == rel_date:
            bp_real = (dgs2[ds2[-1]] - dgs2[ds2[-2]]) * 100
            exp_s = "상승" if hist["r2_bp"] > BP_TH else "하락" if hist["r2_bp"] < -BP_TH else "중립"
            rea_s = "상승" if bp_real > BP_TH else "하락" if bp_real < -BP_TH else "중립"
            hit = "적중 ✓" if exp_s == rea_s else ("중립 —" if rea_s == "중립" else "불일치 ✗")
            g["verdicts"].append({"name": "판정 B — 미 2년 금리 방향",
                                  "expected": f"{'+' if hist['r2_bp']>=0 else ''}{hist['r2_bp']}bp",
                                  "realized": f"{'+' if bp_real>=0 else ''}{round(bp_real,1)}bp",
                                  "verdict": hit})
    except Exception as e:
        g["verdicts"].append({"name": "판정", "error": str(e)})
    return g


now = datetime.datetime.now(datetime.timezone.utc)
out = {
    "updated_utc": now.isoformat(timespec="seconds"),
    "event_id": TARGET_ID,
    "rules": f"방향 판정 ±{DIR_TH}% (금리 ±{BP_TH}bp) · 사람 개입 0 · 데이터: ES=F 15분봉·^KS11·FRED",
    "status": "graded" if now > TARGET_RELEASE_UTC + datetime.timedelta(hours=2) else "pending",
}
if out["status"] == "graded":
    out["live"] = grade(TARGET_RELEASE_UTC, "본 카드 채점 — CPI 2026-09-11")
else:
    out["rehearsal"] = grade(REHEARSAL_RELEASE_UTC,
                             "시운전 — 지난 CPI(2026-08-12) 소급 채점 · 트랙레코드 아님")
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"grading.json written: status={out['status']}")
