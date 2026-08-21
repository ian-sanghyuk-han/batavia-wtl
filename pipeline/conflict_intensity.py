# Conflict-report density from our own GDELT feed -> site/data/conflicts-auto.json
# Accumulates per-country daily counts of conflict-coded news (CAMEO 18/19/20 + 13/14)
# over a rolling 14-day window; emits auto hotspots with intensity 1-5.
# No key required — upgrade path: UCDP candidate API (needs free x-ucdp-access-token).
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "site", "data")
HIST = os.path.join(DATA, "history", "conflict_days.json")
OUT = os.path.join(DATA, "conflicts-auto.json")

CODES = {"13", "14", "18", "19", "20"}
WINDOW = 14
MIN_N = 3          # 14일 누적 최소 보도 수
MAX_SPOTS = 20

try:
    news = json.load(open(os.path.join(DATA, "news.json"), encoding="utf-8"))
except Exception:
    news = {}

today = datetime.date.today().isoformat()
hist = {}
if os.path.exists(HIST):
    try:
        hist = json.load(open(HIST, encoding="utf-8"))
    except Exception:
        hist = {}

day = hist.setdefault(today, {})
seen = set(day.get("_ids", []))
for e in news.get("events", []):
    if e.get("code") not in CODES:
        continue
    eid = str(e.get("id"))
    if eid in seen:
        continue
    seen.add(eid)
    region = e.get("region") or ""
    country = region.split(",")[-1].strip() or "Unknown"
    c = day.setdefault(country, {"n": 0, "sev": 0, "la": 0.0, "lo": 0.0})
    c["n"] += 1
    c["sev"] += e.get("sev") or 0
    c["la"] += e.get("la") or 0.0
    c["lo"] += e.get("lo") or 0.0
day["_ids"] = sorted(seen)[-4000:]

# rolling window trim
cut = (datetime.date.today() - datetime.timedelta(days=WINDOW)).isoformat()
hist = {d: v for d, v in hist.items() if d >= cut}
os.makedirs(os.path.dirname(HIST), exist_ok=True)
json.dump(hist, open(HIST, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))

# aggregate window
agg = {}
for d, per in hist.items():
    for country, c in per.items():
        if country == "_ids":
            continue
        a = agg.setdefault(country, {"n": 0, "sev": 0, "la": 0.0, "lo": 0.0})
        a["n"] += c["n"]
        a["sev"] += c["sev"]
        a["la"] += c["la"]
        a["lo"] += c["lo"]

spots = []
for country, a in agg.items():
    if a["n"] < MIN_N or country in ("Unknown", ""):
        continue
    n = a["n"]
    intensity = 1 if n < 5 else 2 if n < 10 else 3 if n < 20 else 4 if n < 40 else 5
    spots.append({
        "country": country,
        "hot": [round(a["la"] / n, 2), round(a["lo"] / n, 2)],
        "n": n,
        "sev_avg": round(a["sev"] / n, 1),
        "intensity": intensity,
    })
spots.sort(key=lambda s: -s["n"])
spots = spots[:MAX_SPOTS]

out = {
    "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "label": f"분쟁 보도 밀집 · GDELT {WINDOW}일 누적 · 자동",
    "window_days": WINDOW,
    "spots": spots,
}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"conflicts-auto.json: {len(spots)} hotspots from {len(hist)} days")
