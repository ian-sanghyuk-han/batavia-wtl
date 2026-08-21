# UCDP conflict intensity -> site/data/conflicts-ucdp.json
# Academic-grade armed-conflict events (Uppsala Conflict Data Program).
# Requires env UCDP_TOKEN (free; requested by email per ucdp.uu.se/apidocs).
# Gracefully skips when the token is absent so the workflow can ship before the token arrives.
import datetime
import json
import os
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "data", "conflicts-ucdp.json")

TOKEN = os.environ.get("UCDP_TOKEN")
if not TOKEN:
    print("UCDP_TOKEN missing - skip (GDELT density layer keeps running)")
    raise SystemExit(0)

BASE = "https://ucdpapi.pcr.uu.se/api"
WINDOW_DAYS = 120
MAX_PAGES = 6
PAGESIZE = 1000


def get(url):
    req = urllib.request.Request(url, headers={"x-ucdp-access-token": TOKEN})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


# Candidate monthly releases live under the SAME 'gedevents' resource with
# version strings YY.0.M (verified live: gedevents/26.0.7 = July-2026 events).
# Walk the last few months and merge; each monthly release is small (~2k events).
today = datetime.date.today()
versions = []
y, m = today.year, today.month
for _ in range(5):
    versions.append(f"{y % 100}.0.{m}")
    m -= 1
    if m == 0:
        y, m = y - 1, 12

cut = (today - datetime.timedelta(days=WINDOW_DAYS)).isoformat()
events = []
seen_ids = set()
used_versions = []
for ver in versions:
    try:
        first = get(f"{BASE}/gedevents/{ver}?pagesize={PAGESIZE}")
    except Exception:
        continue
    used_versions.append(ver)
    rows = first.get("Result") or []
    total_pages = min(MAX_PAGES, ((first.get("TotalCount") or 0) + PAGESIZE - 1) // PAGESIZE)
    for page in range(1, total_pages):
        try:
            d = get(f"{BASE}/gedevents/{ver}?pagesize={PAGESIZE}&page={page}")
            rows.extend(d.get("Result") or [])
        except Exception as e:
            print("page fail:", ver, page, e)
            break
    for e in rows:
        if e.get("id") in seen_ids:
            continue
        seen_ids.add(e.get("id"))
        events.append(e)

if not used_versions:
    print("no reachable UCDP candidate version - skip")
    raise SystemExit(0)
ver = "+".join(used_versions)
res = "gedevents(candidate)"

agg = {}
used = 0
for e in events:
    ds = str(e.get("date_start") or "")[:10]
    if ds and ds < cut:
        continue
    country = e.get("country") or "Unknown"
    la, lo = e.get("latitude"), e.get("longitude")
    deaths = e.get("best") or 0
    if la is None or lo is None:
        continue
    used += 1
    a = agg.setdefault(country, {"n": 0, "deaths": 0, "la": 0.0, "lo": 0.0})
    a["n"] += 1
    a["deaths"] += deaths
    a["la"] += la
    a["lo"] += lo

spots = []
for country, a in agg.items():
    d = a["deaths"]
    intensity = 1 if d < 10 else 2 if d < 50 else 3 if d < 200 else 4 if d < 1000 else 5
    spots.append({
        "country": country,
        "hot": [round(a["la"] / a["n"], 2), round(a["lo"] / a["n"], 2)],
        "n": a["n"],
        "deaths": d,
        "intensity": intensity,
    })
spots.sort(key=lambda s: -s["deaths"])
spots = spots[:25]

out = {
    "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "label": f"UCDP {res} {ver} · 최근 {WINDOW_DAYS}일 · 사망자 기반 · 자동",
    "source": "Uppsala Conflict Data Program (ucdp.uu.se)",
    "spots": spots,
}
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"conflicts-ucdp.json: {len(spots)} spots from {used} events ({res} {ver})")
