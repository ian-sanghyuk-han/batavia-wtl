# Event Card v0.1 pipeline (P2.5, charter M1): US CPI card -> /site/data/event_card.json
# Real: prior CPI (FRED), pre-pricing index (F1+F2 style: current 5d drift vs pre-CPI
# historical distribution), D+0 anchor volatility stats. Estimate (labeled): consensus
# (manual until a free aggregate is wired), beat/miss split (needs consensus history).
# Ledger: L-INF-001 "CPI 서프라이즈의 하루" (core 2.3, 7.1, grade B+).
import datetime
import json
import os
import urllib.request

import yfinance as yf

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "data", "event_card.json")
FRED_KEY = os.environ.get("FRED_API_KEY")

# --- next event (owner-confirmable; charter §0 recommends this pick) ---
EVENT = {
    "id": "CPI-2026-08",
    "name": "미국 CPI (2026년 8월분)",
    "release_kst": "2026-09-11 21:30",
    "release_et": "2026-09-11 08:30",
    "release_date": "2026-09-11",
    "consensus": None,  # 집계 전 — 수기 입력 예정 (무료 공개 전망 집계)
    "ledger": {"id": "L-INF-001", "name": "CPI 서프라이즈의 하루",
               "core": "코어 2.3·7.1", "grade": "B+", "p_n": "추정 (원장 v0 — 실측 채점 전)"},
}

# CPI release calendar, hand-entered from the BLS schedule (v1; ±1 day errors only
# shift the 5-day window by one session — method disclosed on the card).
CPI_DATES = [
    "2023-01-12", "2023-02-14", "2023-03-14", "2023-04-12", "2023-05-10", "2023-06-13",
    "2023-07-12", "2023-08-10", "2023-09-13", "2023-10-12", "2023-11-14", "2023-12-12",
    "2024-01-11", "2024-02-13", "2024-03-12", "2024-04-10", "2024-05-15", "2024-06-12",
    "2024-07-11", "2024-08-14", "2024-09-11", "2024-10-10", "2024-11-13", "2024-12-11",
    "2025-01-15", "2025-02-12", "2025-03-12", "2025-04-10", "2025-05-13", "2025-06-11",
    "2025-07-15", "2025-08-12", "2025-09-11", "2025-10-15", "2025-11-13", "2025-12-10",
    "2026-01-13", "2026-02-11", "2026-03-11", "2026-04-10", "2026-05-12", "2026-06-10",
    "2026-07-14", "2026-08-12",
]

# --- owner-entered consensus (manual until a free aggregate is wired) ---
try:
    manual = json.load(open(os.path.join(HERE, "events_manual.json"), encoding="utf-8"))
    mc = manual.get(EVENT["id"], {})
    if mc.get("consensus_mom") is not None or mc.get("consensus_yoy") is not None:
        parts = []
        if mc.get("consensus_yoy") is not None:
            parts.append(f"YoY +{mc['consensus_yoy']}%")
        if mc.get("consensus_mom") is not None:
            parts.append(f"MoM {'+' if mc['consensus_mom'] >= 0 else ''}{mc['consensus_mom']}%")
        EVENT["consensus"] = " · ".join(parts)
        EVENT["consensus_src"] = mc.get("source") or "수기 입력"
except Exception as e:
    print("manual consensus read fail:", e)

# --- CPI history from FRED (real): prior print + full MoM series for surprise classes ---
prior = {}
cpi_mom = {}  # "YYYY-MM" -> MoM %
if FRED_KEY:
    try:
        url = ("https://api.stlouisfed.org/fred/series/observations?series_id=CPIAUCSL"
               f"&api_key={FRED_KEY}&file_type=json&sort_order=asc"
               "&observation_start=2021-06-01")
        with urllib.request.urlopen(url, timeout=30) as r:
            obs = [o for o in json.load(r)["observations"] if o["value"] not in (".", "")]
        vals = [(o["date"][:7], float(o["value"])) for o in obs]  # oldest first
        for i in range(1, len(vals)):
            cpi_mom[vals[i][0]] = (vals[i][1] / vals[i - 1][1] - 1) * 100
        mom = (vals[-1][1] / vals[-2][1] - 1) * 100
        yoy = (vals[-1][1] / vals[-13][1] - 1) * 100
        prior = {"month": vals[-1][0], "mom": round(mom, 2), "yoy": round(yoy, 2),
                 "source": "FRED CPIAUCSL(실측)"}
    except Exception as e:
        print("prior CPI fail:", e)

# --- price history for pre-pricing (real) ---
def fred_hist(sid, n=900):
    url = (f"https://api.stlouisfed.org/fred/series/observations?series_id={sid}"
           f"&api_key={FRED_KEY}&file_type=json&sort_order=asc&limit={n}"
           f"&observation_start=2022-10-01")
    with urllib.request.urlopen(url, timeout=30) as r:
        obs = json.load(r)["observations"]
    return {o["date"]: float(o["value"]) for o in obs if o["value"] not in (".", "")}

ydata = yf.download(["DX-Y.NYB", "^GSPC"], period="4y", interval="1d",
                    progress=False, group_by="ticker", threads=True, auto_adjust=True)

series = {}
if FRED_KEY:
    try:
        series["us2y"] = ("미 2년 금리", fred_hist("DGS2"), "level")   # %p diff
        series["us10y"] = ("미 10년 금리", fred_hist("DGS10"), "level")
    except Exception as e:
        print("FRED hist fail:", e)
for key, tk, label in [("dxy", "DX-Y.NYB", "달러 DXY"), ("spx", "^GSPC", "S&P 500")]:
    try:
        c = ydata[tk]["Close"].dropna()
        series[key] = (label, {str(d.date()): float(v) for d, v in c.items()}, "pct")
    except Exception as e:
        print(key, "fail:", e)

def drift5(dates_map, end_date, kind):
    """5-trading-day move ending on/before end_date. level -> diff(%p), pct -> %."""
    ds = sorted(d for d in dates_map if d <= end_date)
    if len(ds) < 6:
        return None
    a, b = dates_map[ds[-6]], dates_map[ds[-1]]
    return (b - a) if kind == "level" else (b / a - 1) * 100

today = datetime.date.today().isoformat()
pre = {}
for key, (label, m, kind) in series.items():
    hist = []
    for rd in CPI_DATES:
        day_before = (datetime.date.fromisoformat(rd) - datetime.timedelta(days=1)).isoformat()
        v = drift5(m, day_before, kind)
        if v is not None:
            hist.append(v)
    cur = drift5(m, today, kind)
    if cur is None or len(hist) < 10:
        continue
    srt = sorted(abs(h) for h in hist)
    pctl = sum(1 for h in srt if h <= abs(cur)) / len(srt)
    med = sorted(hist)[len(hist) // 2]
    pre[key] = {"label": label, "cur": round(cur, 2), "hist_median": round(med, 2),
                "pctl": round(pctl, 3), "n": len(hist), "unit": "%p" if kind == "level" else "%"}

index = round(100 * sum(v["pctl"] for v in pre.values()) / len(pre)) if pre else None
phrase = (None if index is None else
          "반영 미미" if index < 30 else "일부 반영" if index < 60 else
          "상당 부분 반영" if index < 80 else "과반영 의심")

# directional lean (descriptive only): rates/dollar down + stocks up = leaning "cool CPI"
lean_votes = 0
if "us2y" in pre:
    lean_votes += -1 if pre["us2y"]["cur"] < pre["us2y"]["hist_median"] else 1
if "dxy" in pre:
    lean_votes += -1 if pre["dxy"]["cur"] < pre["dxy"]["hist_median"] else 1
if "spx" in pre:
    lean_votes += -1 if pre["spx"]["cur"] > pre["spx"]["hist_median"] else 1
lean = "cool" if lean_votes <= -2 else "hot" if lean_votes >= 2 else "balanced"

if index is None:
    asym = "데이터 수집 전 — 비대칭 판단 보류."
elif lean == "cool" and index >= 60:
    asym = "시장은 이미 '물가 둔화' 쪽으로 상당히 기울어 있다 — 예상 부합은 안도가 아니라 무반응에 가깝고, 상방 서프라이즈 쪽이 더 놀라운 자리다."
elif lean == "hot" and index >= 60:
    asym = "시장은 이미 '물가 상방' 쪽에 대비하고 있다 — 확인은 놀랍지 않고, 둔화 서프라이즈 쪽이 더 놀라운 자리다."
elif index < 30:
    asym = "쏠림이 아직 얕다 — 어느 쪽 서프라이즈든 반응할 여지가 남아 있는 자리다."
else:
    asym = "쏠림은 중간 수준 — 서프라이즈의 방향보다 크기가 반응을 결정할 자리다."

# D+0 anchor (S&P 500) reaction stats on past CPI days (real, no consensus needed)
d0 = None
try:
    spx_map = series["spx"][1]
    moves = []
    for rd in CPI_DATES:
        ds = sorted(d for d in spx_map if d <= rd)
        if len(ds) < 2 or ds[-1] != rd:
            continue
        moves.append((spx_map[ds[-1]] / spx_map[ds[-2]] - 1) * 100)
    if moves:
        up = sum(1 for x in moves if x > 0)
        d0 = {"n": len(moves), "avg_abs": round(sum(abs(x) for x in moves) / len(moves), 2),
              "up": up, "down": len(moves) - up,
              "max_up": round(max(moves), 2), "max_down": round(min(moves), 2)}
except Exception as e:
    print("d0 fail:", e)

# --- Conditional scenarios (REAL, naive-benchmark basis): each past release classified
# 상방/부합/하방 by (actual MoM − median of prior 12 MoM), threshold ±0.05%p (F1 스타일).
# When true consensus history arrives, the basis upgrades — method is disclosed on the card.
scenarios = None
try:
    spx_map = series["spx"][1]
    us2_map = series.get("us2y", (None, {}, None))[1]
    def month_before(ym):
        y, m = int(ym[:4]), int(ym[5:7])
        return f"{y-1}-12" if m == 1 else f"{y}-{m-1:02d}"
    classes = {"hot": [], "inline": [], "cool": []}
    for rd in CPI_DATES:
        reported = month_before(rd[:7])  # release reports the previous month
        if reported not in cpi_mom:
            continue
        hist12 = []
        mth = month_before(reported)
        while len(hist12) < 12 and mth in cpi_mom:
            hist12.append(cpi_mom[mth])
            mth = month_before(mth)
        if len(hist12) < 8:
            continue
        naive = sorted(hist12)[len(hist12) // 2]
        sup = cpi_mom[reported] - naive
        cls = "hot" if sup > 0.05 else "cool" if sup < -0.05 else "inline"
        ds = sorted(d for d in spx_map if d <= rd)
        if len(ds) < 2 or ds[-1] != rd:
            continue
        d0m = (spx_map[ds[-1]] / spx_map[ds[-2]] - 1) * 100
        after = sorted(d for d in spx_map if d > rd)
        d1m = (spx_map[after[0]] / spx_map[ds[-1]] - 1) * 100 if after else None
        r2 = None
        ds2 = sorted(d for d in us2_map if d <= rd)
        if len(ds2) >= 2 and ds2[-1] == rd:
            r2 = us2_map[ds2[-1]] - us2_map[ds2[-2]]
        classes[cls].append((d0m, d1m, r2))
    def agg(rows):
        if not rows:
            return None
        d0s = [r[0] for r in rows]
        d1s = [r[1] for r in rows if r[1] is not None]
        r2s = [r[2] for r in rows if r[2] is not None]
        return {"n": len(rows),
                "d0": round(sum(d0s) / len(d0s), 2),
                "d1": round(sum(d1s) / len(d1s), 2) if d1s else None,
                "r2_bp": round(sum(r2s) / len(r2s) * 100, 1) if r2s else None}
    scenarios = {"basis": "기대 기준: 직전 12개월 MoM 중앙값(나이브 벤치마크) · 문턱 ±0.05%p — 합의 이력 연결 시 업그레이드",
                 "adj_note": "조정 반응(추정) = 과거 평균 × (1 − 선반영지수/100) · 조정식 v1",
                 "classes": {k: agg(v) for k, v in classes.items()}}
except Exception as e:
    print("scenarios fail:", e)

out = {
    "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "today": today,
    "no_card_today": today != EVENT["release_date"],
    "event": EVENT,
    "prior": prior,
    "prepricing": {"index": index, "phrase": phrase, "assets": pre,
                   "method": "각 자산의 최근 5거래일 변동 크기가 과거 CPI 직전 5일 분포에서 갖는 백분위의 평균 (F1+F2 · 발표일 캘린더 수기 v1)",
                   "lean": lean},
    "asymmetry": asym,
    "d0_anchor": d0,
    "scenarios": scenarios,
    "checkpoints": ["21:30 KST — 발표", "22:30 KST — 초기 반응 정착 확인", "익일 09:05 KST — KRX 개장 반응"],
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"event_card.json written: index={index} ({phrase}), lean={lean}, "
      f"assets={list(pre)}, d0_n={d0 and d0['n']}")
