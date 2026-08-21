# Daily observation archive -> site/data/history/days.jsonl
# One line per day: regime, market closes, event prepricing, top news.
# This is the REAL-data food for the future replay (replaces curated scripts).
import datetime
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "site", "data")


def load(name):
    try:
        return json.load(open(os.path.join(DATA, name), encoding="utf-8"))
    except Exception:
        return {}


mkt = load("market.json")
rg = load("regime.json")
ev = load("event_card.json")
news = load("news.json")

today = (rg.get("conv") or {}).get("asof") or datetime.date.today().isoformat()
row = {
    "d": today,
    "conv": (rg.get("conv") or {}).get("value"),
    "w": (rg.get("w") or {}).get("value"),
    "mkt": {k: {"v": v.get("value"), "p": v.get("prev")}
            for k, v in (mkt.get("series") or {}).items()},
    "event": (ev.get("event") or {}).get("id"),
    "prepricing": (ev.get("prepricing") or {}).get("index"),
    "news": [{"n": e.get("name", "")[:90], "la": e.get("la"), "lo": e.get("lo"),
              "sev": e.get("sev"), "tone": e.get("tone")}
             for e in (news.get("events") or [])[:5]],
}

path = os.path.join(DATA, "history", "days.jsonl")
os.makedirs(os.path.dirname(path), exist_ok=True)
rows = {}
if os.path.exists(path):
    for ln in open(path, encoding="utf-8"):
        try:
            rows[json.loads(ln)["d"]] = ln.rstrip("\n")
        except Exception:
            pass
rows[today] = json.dumps(row, ensure_ascii=False, separators=(",", ":"))
with open(path, "w", encoding="utf-8") as fp:
    for d in sorted(rows):
        fp.write(rows[d] + "\n")
print(f"days.jsonl: {len(rows)} days archived")
