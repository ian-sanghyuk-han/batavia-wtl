"""Backtest phase 2a: download every free series named in triage.json
into pipeline/backtest/history/ as date,value CSVs (one file per series).

Sources: FRED (env FRED_API_KEY), Yahoo daily history, NOAA ONI,
Binance funding (2019+), CFTC COT annual files, IMF PortWatch (best-effort).
Each fetcher fails soft: a missing feed skips its cards, never the run.
Raw history is NOT committed (see .gitignore) - rerun this script to refresh.
"""
import os, io, csv, json, time, zipfile, datetime
import requests

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "history")
os.makedirs(OUT, exist_ok=True)
UA = {"User-Agent": "Mozilla/5.0 (BataviaBacktest/1.0)"}

def save(name, rows):
    rows = [(d, v) for d, v in rows if v is not None]
    rows.sort()
    with io.open(os.path.join(OUT, name + ".csv"), "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f); w.writerow(["date", "value"]); w.writerows(rows)
    print(f"  {name}: {len(rows)} rows")

# ── FRED ─────────────────────────────────────────────────────────────
FRED = ["SAHMREALTIME","IC4WSA","CES0500000003","OPHNFB","CPIAUCSL","CPILFESL",
        "WPSFD4131","T10YIE","DCOILWTICO","DGS10","DGS2","EXPINF5YR","T10Y2Y",
        "USREC","DFII10","DFEDTARU","UNRATE","WALCL","WTREGEN","RRPONTSYD",
        "SOFR","IORB","IOER","BAMLH0A0HYM2","RSXFS","PAYEMS"]

def fetch_fred():
    key = os.environ.get("FRED_API_KEY")
    if not key:
        print("FRED: no key, skipped"); return
    for sid in FRED:
        try:
            r = requests.get("https://api.stlouisfed.org/fred/series/observations",
                params={"series_id": sid, "api_key": key, "file_type": "json",
                        "observation_start": "1990-01-01"}, timeout=30)
            obs = r.json().get("observations", [])
            save("fred_" + sid, [(o["date"], float(o["value"]))
                                 for o in obs if o["value"] not in (".", "")])
            time.sleep(0.4)
        except Exception as e:
            print(f"  fred {sid} FAILED: {e}")

# ── Yahoo daily closes ───────────────────────────────────────────────
YAHOO = ["GC=F","CL=F","SPY","QQQ","TLT","XLY","XME","ACWI","BTC-USD","KRBN","BDRY",
         "^VIX","^VIX3M","^GSPC","SB=F","CC=F","UUP","EEM","HYG","XLK","XLE","XLF",
         "XLV","XLI","XLP","XLB","XLU"]

def fetch_yahoo():
    for t in YAHOO:
        try:
            r = requests.get(f"https://query1.finance.yahoo.com/v8/finance/chart/{t}",
                params={"range": "30y", "interval": "1d"}, headers=UA, timeout=30)
            j = r.json()["chart"]["result"][0]
            ts = j["timestamp"]; cl = j["indicators"]["quote"][0]["close"]
            rows = [(datetime.datetime.utcfromtimestamp(s).strftime("%Y-%m-%d"), c)
                    for s, c in zip(ts, cl) if c is not None]
            save("yh_" + t.replace("^","_").replace("=","_"), rows)
            time.sleep(0.6)
        except Exception as e:
            print(f"  yahoo {t} FAILED: {e}")

# ── NOAA ONI (ENSO) ─────────────────────────────────────────────────
def fetch_oni():
    try:
        r = requests.get("https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
                         headers=UA, timeout=30)
        SEAS = {"DJF":1,"JFM":2,"FMA":3,"MAM":4,"AMJ":5,"MJJ":6,
                "JJA":7,"JAS":8,"ASO":9,"SON":10,"OND":11,"NDJ":12}
        rows = []
        for ln in r.text.splitlines()[1:]:
            p = ln.split()
            if len(p) >= 4 and p[0] in SEAS:
                rows.append((f"{p[1]}-{SEAS[p[0]]:02d}-01", float(p[3])))
        save("noaa_ONI", rows)
    except Exception as e:
        print(f"  ONI FAILED: {e}")

# ── Binance BTC perp funding (2019+) ────────────────────────────────
def fetch_funding():
    try:
        rows, start = [], 1568102400000  # 2019-09-10
        for _ in range(40):
            r = requests.get("https://fapi.binance.com/fapi/v1/fundingRate",
                params={"symbol": "BTCUSDT", "startTime": start, "limit": 1000},
                headers=UA, timeout=30)
            js = r.json()
            if not isinstance(js, list) or not js: break
            for o in js:
                rows.append((datetime.datetime.utcfromtimestamp(o["fundingTime"]/1000)
                             .strftime("%Y-%m-%d"), float(o["fundingRate"])))
            start = js[-1]["fundingTime"] + 1
            if len(js) < 1000: break
            time.sleep(0.3)
        # daily sum of the (usually 3) 8h rates
        day = {}
        for d, v in rows: day[d] = day.get(d, 0.0) + v
        save("bn_funding_BTC", sorted(day.items()))
    except Exception as e:
        print(f"  funding FAILED: {e}")

# ── CFTC COT (legacy futures-only, net large-spec) ──────────────────
COT_MKT = {"ES": "S&P 500", "CL": "CRUDE OIL, LIGHT", "GC": "GOLD", "EC": "EURO FX"}

def fetch_cot():
    net = {k: [] for k in COT_MKT}
    for yr in range(2006, datetime.date.today().year + 1):
        try:
            r = requests.get(f"https://www.cftc.gov/files/dea/history/deacot{yr}.zip",
                             headers=UA, timeout=60)
            z = zipfile.ZipFile(io.BytesIO(r.content))
            txt = z.read(z.namelist()[0]).decode("latin-1")
            for row in csv.reader(io.StringIO(txt)):
                if len(row) < 12: continue
                name, date = row[0].upper(), row[2]
                try:
                    lng, sht = float(row[8]), float(row[9])
                except Exception:
                    continue
                for k, pat in COT_MKT.items():
                    if pat in name and "CONSOLIDATED" not in name:
                        net[k].append((date, lng - sht)); break
            time.sleep(0.4)
        except Exception as e:
            print(f"  cot {yr} FAILED: {e}")
    for k, rows in net.items():
        if rows: save("cot_" + k, rows)

# ── IMF PortWatch chokepoint transit (best effort) ──────────────────
def fetch_portwatch():
    base = ("https://services9.arcgis.com/weJ1QsnbMYJlCHdG/arcgis/rest/services/"
            "Daily_Chokepoints_Data/FeatureServer/0/query")
    CHOKE = {"Strait of Hormuz": "hormuz", "Suez Canal": "suez", "Panama Canal": "panama"}
    try:
        for pnm, nm in CHOKE.items():
            rows, offset = [], 0
            while True:
                r = requests.get(base, params={
                    "where": f"portname='{pnm}'", "outFields": "date,n_total",
                    "f": "json", "resultOffset": offset, "resultRecordCount": 2000},
                    headers=UA, timeout=45)
                fs = r.json().get("features", [])
                if not fs: break
                for f0 in fs:
                    a = f0["attributes"]
                    d = a["date"]
                    if isinstance(d, (int, float)):
                        d = datetime.datetime.utcfromtimestamp(d/1000).strftime("%Y-%m-%d")
                    rows.append((str(d)[:10], float(a["n_total"])))
                offset += len(fs)  # server caps page size; stop only on an empty page
                time.sleep(0.2)
            if rows: save("pw_" + nm, rows)
            else: print(f"  portwatch {nm}: empty")
    except Exception as e:
        print(f"  portwatch FAILED: {e}")

# ── FOMC scheduled-meeting decision days (Fed website, official) ────
MONTHS = {m: i+1 for i, m in enumerate(["January","February","March","April","May","June",
          "July","August","September","October","November","December"])}

def fetch_fomc():
    import re
    rows = []
    # historical per-year pages (scheduled Meetings only; skip conference calls)
    for yr in range(2000, 2022):
        try:
            r = requests.get(f"https://www.federalreserve.gov/monetarypolicy/"
                             f"fomchistorical{yr}.htm", headers=UA, timeout=30)
            if r.status_code != 200: continue
            for h in re.findall(r"<h5[^>]*>(.*?)</h5>", r.text):
                m = re.match(r"([A-Za-z]+)(?:/([A-Za-z]+))?\s+(\d+)(?:-(\d+))?\s+Meeting", h)
                if not m: continue
                mon = MONTHS.get(m.group(2) or m.group(1))
                day = int(m.group(4) or m.group(3))
                if mon: rows.append((f"{yr}-{mon:02d}-{day:02d}", 1.0))
            time.sleep(0.3)
        except Exception as e:
            print(f"  fomc {yr} FAILED: {e}")
    # recent years live on the calendars page, one panel per year
    try:
        r = requests.get("https://www.federalreserve.gov/monetarypolicy/fomccalendars.htm",
                         headers=UA, timeout=30)
        import re as _re
        for blk_yr, blk in _re.findall(r"(\d{4}) FOMC Meetings(.*?)(?=\d{4} FOMC Meetings|$)",
                                       r.text, _re.S):
            for mon_s, day_s in _re.findall(
                r'fomc-meeting__month[^>]*>\s*(?:<strong>)?([A-Za-z/]+)(?:</strong>)?\s*<'
                r'.*?fomc-meeting__date[^>]*>([^<]+)<', blk, _re.S):
                mon = MONTHS.get(mon_s.split("/")[-1])
                d = _re.findall(r"\d+", day_s)
                if mon and d:
                    rows.append((f"{blk_yr}-{mon:02d}-{int(d[-1]):02d}", 1.0))
    except Exception as e:
        print(f"  fomc calendars FAILED: {e}")
    rows = sorted(set(rows))
    save("manual_fomc", rows)

# ── EIA crude stocks (needs free key: env EIA_API_KEY) ──────────────
def fetch_eia():
    key = os.environ.get("EIA_API_KEY")
    if not key:
        print("EIA: no EIA_API_KEY - skipped (PHY-005 stays deferred)"); return
    try:
        r = requests.get("https://api.eia.gov/v2/seriesid/PET.WCESTUS1.W",
                         params={"api_key": key}, timeout=45)
        data = r.json()["response"]["data"]
        save("eia_WCESTUS1", [(o["period"], float(o["value"])) for o in data])
    except Exception as e:
        print(f"  eia FAILED: {e}")

if __name__ == "__main__":
    print("fetching FRED...");   fetch_fred()
    print("fetching Yahoo...");  fetch_yahoo()
    print("fetching ONI...");    fetch_oni()
    print("fetching funding..."); fetch_funding()
    print("fetching COT...");    fetch_cot()
    print("fetching PortWatch..."); fetch_portwatch()
    print("fetching FOMC dates..."); fetch_fomc()
    print("fetching EIA...");       fetch_eia()
    print("done ->", OUT)
