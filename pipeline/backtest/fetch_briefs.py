"""Backtest: per-fire-day news briefs from Wikipedia (CC BY-SA 4.0, attribution kept).

For every unique fire date in site/data/backtest/fires.jsonl:
  2003+  -> Portal:Current events/<YYYY Month D> (daily page)
  <2003  -> the year article (e.g. "2001"), bullets dated that day
Bullets are cleaned of wiki markup, scored for market relevance, and the
top 4 are kept. Output: site/data/backtest/briefs.json (resumable).
"""
import os, io, re, json, time, datetime, requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUTD = os.path.normpath(os.path.join(HERE, "..", "..", "site", "data", "backtest"))
OUT = os.path.join(OUTD, "briefs.json")
UA = {"User-Agent": "BataviaObservatory/1.0 (contact: ian.sanghyuk.han@gmail.com) backtest briefs"}
API = "https://en.wikipedia.org/w/api.php"
MONTHS = ["January","February","March","April","May","June","July","August",
          "September","October","November","December"]
KEY = re.compile(r"econom|bank|market|stock|oil|opec|fed\b|federal reserve|central bank|rate|"
                 r"inflation|recession|default|debt|bailout|crisis|war\b|attack|invasion|missile|"
                 r"election|referendum|tariff|sanction|earthquake|hurricane|pandemic|lockdown|"
                 r"treasury|dollar|euro|yuan|bond|imf|ecb|boj|bank of|gdp|unemploy|strike|coup|"
                 r"ceasefire|pipeline|tanker|canal|strait|blockade|nuclear|treaty|summit|trade|"
                 r"export|shipping|port\b|supply|yield|plunge|surge|crash|rally|bankrupt|collapse|"
                 r"stimulus|quantitative|hike|cut\b|shutdown|ceiling|downgrade", re.I)

def wikitext(page):
    r = requests.get(API, params={"action": "parse", "page": page, "prop": "wikitext",
                                  "format": "json", "formatversion": 2}, headers=UA, timeout=30)
    return r.json().get("parse", {}).get("wikitext")

def clean(s):
    s = re.sub(r"<!--.*?-->", "", s, flags=re.S)
    s = re.sub(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", "", s, flags=re.S)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]*)\]\]", r"\1", s)
    s = re.sub(r"\[https?://[^\s\]]+(?:\s[^\]]*)?\]", "", s)
    s = re.sub(r"'{2,}", "", s)
    s = re.sub(r"<[^>]+>", "", s)
    s = re.sub(r"\s+", " ", s).strip(" :–-*;")
    return s

def bullets(wt):
    out = []
    for ln in wt.splitlines():
        if not ln.startswith("*"): continue
        t = clean(ln.lstrip("*"))
        if len(t) < 25 or t.lower().startswith(("see also", "category")): continue
        out.append(t)
    return out

FIN = re.compile(r"bankrupt|bailout|default|downgrade|crash|plummet|plunge|surge|rally|record|"
                 r"stock|market|bond|yield|rate|fed\b|federal reserve|central bank|ecb|boj|imf|"
                 r"inflation|recession|gdp|unemploy|debt|ceiling|treasury|dollar|euro|yuan|oil|opec|"
                 r"tariff|sanction|stimulus|quantitative|hike|shutdown|bank\b|banks\b|tanker|canal|strait", re.I)
GEO = re.compile(r"war\b|attack|invasion|missile|election|referendum|earthquake|hurricane|pandemic|"
                 r"lockdown|strike|coup|ceasefire|blockade|nuclear|treaty|summit|trade|export|pipeline", re.I)

def score(t):
    sc = 3*len(FIN.findall(t)) + len(GEO.findall(t))
    if t.rstrip().endswith(('.', '!', '?')): sc += 2      # a sentence, not a topic-link header
    if len(t) < 60 and not t.rstrip().endswith('.'): sc -= 3  # bare topic headers sink
    return sc

def pick(lines, n=4):
    scored = sorted(((score(t), -i, t) for i, t in enumerate(lines)), reverse=True)
    keep = [t for _, _, t in scored[:n]]
    return [t if len(t) <= 200 else t[:197] + "…" for t in keep]

def daily(d):
    wt = wikitext(f"Portal:Current events/{d.year} {MONTHS[d.month-1]} {d.day}")
    return bullets(wt) if wt else None

YEAR_CACHE = {}
def from_year_article(d):
    if d.year not in YEAR_CACHE:
        YEAR_CACHE[d.year] = wikitext(str(d.year)) or ""
    wt = YEAR_CACHE[d.year]
    # the date must LEAD the bullet ("* [[November 1]] - ..."), not merely appear inside it
    lead = re.compile(r"^\*+\s*(?:\[\[)?" + re.escape(f"{MONTHS[d.month-1]} {d.day}")
                      + r"(?:\]\])?\s*[–—-]")
    return [clean(ln.lstrip("*")) for ln in wt.splitlines() if lead.match(ln)]

def main():
    fires = [json.loads(l) for l in io.open(os.path.join(OUTD, "fires.jsonl"), encoding="utf-8")]
    dates = sorted({f["date"] for f in fires if f["date"] >= "1998-01-01"})
    briefs = json.load(io.open(OUT, encoding="utf-8")) if os.path.exists(OUT) else {}
    briefs.setdefault("_meta", {"source": "Wikipedia — Portal:Current events / year articles",
        "license": "CC BY-SA 4.0", "attribution": "Text from Wikipedia, CC BY-SA 4.0",
        "note": "market-relevance ranked, max 4 lines per day, reconstructed context only"})
    todo = [d for d in dates if d not in briefs]
    print(f"{len(dates)} fire days, {len(todo)} to fetch")
    for k, ds in enumerate(todo):
        d = datetime.date.fromisoformat(ds)
        try:
            lines = daily(d) if d.year >= 2003 else None
            src = "daily"
            if not lines:
                lines = from_year_article(d); src = "year"
            briefs[ds] = {"src": src, "lines": pick(lines)} if lines else {"src": "none", "lines": []}
        except Exception as e:
            briefs[ds] = {"src": "error", "lines": []}
            print("  ", ds, "ERR", e)
        if k % 50 == 0:
            io.open(OUT, "w", encoding="utf-8").write(json.dumps(briefs, ensure_ascii=False))
            print(f"  {k}/{len(todo)} {ds} [{briefs[ds]['src']}] {briefs[ds]['lines'][:1]}")
        time.sleep(0.12)
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(briefs, ensure_ascii=False))
    n = sum(1 for k, v in briefs.items() if k != "_meta" and v["lines"])
    print(f"done: {n} days with briefs -> {OUT}")

def fill_neighbors(span=2):
    """Second pass: pre-2003 days with no dated bullet borrow the nearest dated
    bullet within +/-span days from the year article (labeled src=year±k)."""
    briefs = json.load(io.open(OUT, encoding="utf-8"))
    n = 0
    for ds, v in list(briefs.items()):
        if ds == "_meta" or v.get("lines") or ds >= "2003-01-01": continue
        d = datetime.date.fromisoformat(ds)
        for k in (1, -1, 2, -2)[:span*2]:
            lines = from_year_article(d + datetime.timedelta(days=k))
            if lines:
                briefs[ds] = {"src": f"year{k:+d}", "lines": pick(lines)}; n += 1; break
    io.open(OUT, "w", encoding="utf-8").write(json.dumps(briefs, ensure_ascii=False))
    print(f"neighbors filled: {n}")

if __name__ == "__main__":
    import sys
    if "--fill-neighbors" in sys.argv: fill_neighbors()
    else: main()
