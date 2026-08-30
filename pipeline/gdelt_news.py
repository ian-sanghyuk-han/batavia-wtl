# GDELT 2.0 news pipeline v2 (P2-2): latest 15-min export -> /site/data/news.json
# v2: quality-outlet preference + fetches each kept article to extract the REAL
# headline and REAL publication time from meta tags (article:published_time / og:title).
# Impact scoring: |GoldsteinScale| + NumArticles + |AvgTone|. stdlib only.
import datetime
import io
import json
import os
import re
import urllib.request
import zipfile
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse

OUTLETS = {  # well-known outlets get pretty names; everything else shows its domain
    "reuters.com": "Reuters", "bloomberg.com": "Bloomberg", "apnews.com": "AP",
    "bbc.com": "BBC", "bbc.co.uk": "BBC", "cnn.com": "CNN", "nytimes.com": "NYT",
    "wsj.com": "WSJ", "ft.com": "FT", "cnbc.com": "CNBC", "aljazeera.com": "Al Jazeera",
    "theguardian.com": "Guardian", "afp.com": "AFP", "dw.com": "DW",
    "france24.com": "France 24", "channelnewsasia.com": "CNA", "scmp.com": "SCMP",
    "nikkei.com": "Nikkei", "asia.nikkei.com": "Nikkei Asia", "cbsnews.com": "CBS",
    "nbcnews.com": "NBC", "abcnews.go.com": "ABC", "npr.org": "NPR",
    "politico.com": "Politico", "axios.com": "Axios", "economist.com": "Economist",
    "yna.co.kr": "연합뉴스", "en.yna.co.kr": "연합뉴스", "chosun.com": "조선일보",
    "hankyung.com": "한국경제", "mk.co.kr": "매일경제", "koreaherald.com": "Korea Herald",
}
QUALITY = set(OUTLETS)  # 신뢰 매체 화이트리스트 — 이 도메인의 기사를 우선 채택

UA = {"User-Agent": "Mozilla/5.0 (compatible; BataviaWTL/0.1; +https://ian-sanghyuk-han.github.io/batavia-wtl/)"}
RE_PUBTIME = re.compile(
    r'<meta[^>]+(?:property|name)=["\'](?:article:published_time|pubdate|date|dc\.date|parsely-pub-date)["\'][^>]+content=["\']([^"\']+)["\']'
    r'|<meta[^>]+itemprop=["\']datePublished["\'][^>]+content=["\']([^"\']+)["\']'
    r'|"datePublished"\s*:\s*"([^"]+)"'
    r'|<time[^>]+datetime=["\']([^"\']+)["\']', re.I)
RE_TITLE = re.compile(
    r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']'
    r'|<title[^>]*>([^<]+)</title>', re.I)


def enrich(ev):
    """Fetch the article; extract real headline + publication time. Fail-safe."""
    try:
        req = urllib.request.Request(ev["url"], headers=UA)
        html = urllib.request.urlopen(req, timeout=8).read(400_000).decode("utf-8", errors="replace")
        m = RE_TITLE.search(html)
        if m:
            title = next(g for g in m.groups() if g)
            title = re.sub(r"\s+", " ", title).strip()
            title = re.sub(r"&#?\w+;", lambda x: {"&amp;": "&", "&quot;": '"', "&#39;": "'",
                                                   "&lt;": "<", "&gt;": ">"}.get(x.group(), ""), title)
            # English is the product's base locale: keep only Latin-script headlines
            # (Hangul / CJK / Arabic / Cyrillic / Thai / Devanagari titles fall back to
            # the English actor-based name built from the GDELT record)
            if 8 < len(title) < 200 and not NONLATIN.search(title):
                ev["name"] = title[:110]
        m = RE_PUBTIME.search(html)
        if m:
            raw = next(g for g in m.groups() if g)
            ev["ts_pub"] = raw.strip()[:32]
    except Exception:
        pass
    return ev

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "data", "news.json")

LASTUPDATE = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"
NONLATIN = re.compile(r"[Ѐ-ӿ؀-ۿऀ-ॿ฀-๿぀-ヿ㐀-鿿가-힣]")

# Market-relevance gate (P-pivot): scored on the REAL headline after enrichment.
# ECON boosts, GEOPOL boosts less; LOCAL (crime/accident/sport/celebrity) stories
# with no econ/geopol signal are dropped — a market lens, not a police blotter.
ECON_RX = re.compile(
    r"\btariff|\bsanction|\bopec\b|\b(?:crude|oil) (?:price|export|output|supply|market)|\bcrude\b"
    r"|\blng\b|gas price|\bpipeline\b|\brefinery\b|energy (?:price|crisis|market|deal)"
    r"|\bfed\b|federal reserve|\becb\b|\bboj\b|central bank|interest rate|rate (?:cut|hike|rise|decision)"
    r"|\binflation\b|\bcpi\b|\bppi\b|\bgdp\b|jobs report|\bpayroll|\bunemployment\b"
    r"|\bbond (?:market|yield|sale)|\byield(?:s)?\b|\btreasur(?:y|ies)\b|\bcurrenc|\bdevaluat"
    r"|\bdollar\b|\byuan\b|\brenminbi\b|\beurozone\b|\bforex\b"
    r"|\bexport(?:s|ers)?\b|\bimport(?:s|ers)?\b|trade (?:deal|war|talks|deficit|surplus|pact)"
    r"|\bshipping\b|\bfreight\b|port of |\bcanal\b|\bstrait\b|\bblockade\b|\bembargo\b|\bchokepoint"
    r"|\bsemiconductor|\bchipmaker|chip (?:ban|export|war|plant|sector|curb)|supply chain"
    r"|rare earth|\blithium\b|\bcopper\b|\bwheat\b|grain (?:deal|export|harvest|price|corridor)"
    r"|\bdebt\b|\bdefault\b|\bbailout\b|\bimf\b|stock market|\bstocks\b|\bequit(?:y|ies) market"
    r"|market(?:s)? (?:fall|fell|rall|drop|surge|plunge|tumble|slump)"
    r"|\brecession\b|\bstimulus\b|\bfiscal\b|budget (?:deficit|cut|bill|crisis)"
    r"|bank(?:ing)? (?:crisis|collapse|run)|\bcrypto|\bbitcoin\b", re.I)
GEOPOL_RX = re.compile(
    r"\bwar\b|\binvasion\b|\bmissile|drone (?:strike|attack)|air ?strike|strike(?:s)? on\b"
    r"|\bshelling\b|\bbombard|\boffensive\b|\bartillery\b|ammunition depot|\bnuclear\b"
    r"|\btroops\b|\bmilitary\b|\bceasefire\b|\bcoup\b|martial law|\belection|\bimpeach"
    r"|\bpresident\b|prime minister|\bparliament\b|\bkremlin\b|\bpentagon\b"
    r"|border (?:clash|dispute|closure)|\bmobiliz|\bannex|\boccupation\b|peace (?:deal|talks)"
    r"|\bnato\b|un security|\bsummit\b|\bhostage|\binsurgen|rebels? (?:seize|captur)"
    r"|\bflood(?:s|ing)?\b|\bearthquake\b|\btyphoon\b|\bhurricane\b|\bcyclone\b|\btsunami\b"
    r"|\bvolcan|\bwildfire|\bdrought\b|\blandslide\b|\bepidemic\b|\boutbreak\b", re.I)
LOCAL_RX = re.compile(
    r"\bmurder|\bhomicide\b|\bstabb|\bshooting\b|shot dead|\bgunman\b|\bmanhunt\b"
    r"|police (?:probe|investigat|appeal|hunt)|\barrest|\bsuspect\b|\bassault|\brape\b"
    r"|\brobbery\b|\bburglar|\bkidnap|\babduct|\binquest\b|\bcustody\b"
    r"|\bsentenced\b|\bjailed\b|court (?:hears|told)|charged with|\bcrash(?:es|ed)?\b|\bcollision\b"
    r"|\bdrown|house fire|missing (?:girl|boy|woman|man|teen)|\bshot\b"
    r"|road (?:accident|rage|crash)|traffic accident|bus (?:crash|plunge)|\btrain crash\b"
    r"|\bfootball\b|\bsoccer\b|premier league|champions league|cup (?:final|tie)|\btennis\b"
    r"|\bcricket\b|\brugby\b|\bolympic|\bathlete\b|\bcelebrit|\bsinger\b|\bmovie\b"
    r"|(?:film|adult|reality|tv|pop) star|festival lineup|\bconcert\b|\bbirth of\b|\bwedding\b", re.I)


def relevance(e):
    """0 = local noise, 1 = geopolitics, 2 = econ/markets, 3 = both."""
    text = f"{e['name']} {e.get('region','')}"
    r = (2 if ECON_RX.search(text) else 0) + (1 if GEOPOL_RX.search(text) else 0)
    if r == 0 and LOCAL_RX.search(text):
        return -1  # positively identified local noise -> drop
    return r

# CAMEO event root codes -> English labels (product base locale; clients localize via "code")
ROOT_EN = {
    "01": "public statement", "02": "appeal", "03": "intent to cooperate", "04": "talks",
    "05": "diplomatic cooperation", "06": "material cooperation", "07": "aid", "08": "concession",
    "09": "investigation", "10": "demand", "11": "disapproval", "12": "rejection",
    "13": "threat", "14": "protest", "15": "show of force", "16": "reduced relations",
    "17": "coercion", "18": "assault", "19": "fighting", "20": "mass violence",
}

txt = urllib.request.urlopen(LASTUPDATE, timeout=30).read().decode()
export_url = next(l.split()[2] for l in txt.strip().splitlines()
                  if l.split()[2].endswith(".export.CSV.zip"))
# one 15-min batch is sparse off-hours: merge the last 8 batches (2 h of events)
latest = datetime.datetime.strptime(export_url.rsplit("/", 1)[-1].split(".")[0], "%Y%m%d%H%M%S")
lines = []
for i in range(8):
    ts = (latest - datetime.timedelta(minutes=15 * i)).strftime("%Y%m%d%H%M%S")
    url = f"http://data.gdeltproject.org/gdeltv2/{ts}.export.CSV.zip"
    try:
        raw = urllib.request.urlopen(url, timeout=60).read()
        z = zipfile.ZipFile(io.BytesIO(raw))
        lines += z.read(z.namelist()[0]).decode("utf-8", errors="replace").splitlines()
    except Exception:
        continue

events, seen = [], set()
for line in lines:
    f = line.split("\t")
    if len(f) < 61:
        continue
    try:
        la, lo = f[56], f[57]
        if not la or not lo:
            continue
        la, lo = float(la), float(lo)
        goldstein = float(f[30] or 0)
        arts = int(f[33] or 0)
        tone = float(f[34] or 0)
    except ValueError:
        continue
    if arts < 5:
        continue  # 잔뉴스 컷
    root = f[28]
    region = f[52] or f[7] or "?"
    actor = (f[6] or f[16] or f[53] or "").title()
    key = (round(la, 1), round(lo, 1), root)
    if key in seen:
        continue
    seen.add(key)
    # impact score 0..1 -> sev 1..5
    score = min(1.0, abs(goldstein) / 10) * 0.5 + min(1.0, arts / 60) * 0.35 \
        + min(1.0, abs(tone) / 10) * 0.15
    sev = max(1, min(5, 1 + round(score * 4)))
    label = ROOT_EN.get(root, "event")
    name = f"{actor + ' — ' if actor else ''}{label}"
    dom = urlparse(f[60]).netloc.lower()
    dom = dom[4:] if dom.startswith("www.") else dom
    events.append({
        "id": f[0], "ts": f[59],
        "la": round(la, 2), "lo": round(lo, 2),
        "name": name[:60], "region": region[:40],
        "sev": sev, "tone": round(tone, 1), "arts": arts,
        "code": root, "url": f[60][:300],
        "src": OUTLETS.get(dom, dom[:24]),
    })

# 신뢰 매체 우선: 화이트리스트 도메인 기사 먼저, 부족하면 고임팩트 일반 매체로 보충
quality = [e for e in events if urlparse(e["url"]).netloc.lower().removeprefix("www.") in QUALITY]
others = [e for e in events if e not in quality]
for pool in (quality, others):
    pool.sort(key=lambda e: (e["sev"], e["arts"]), reverse=True)
# keep a wide candidate pool: relevance is judged on the REAL headline, post-enrich
events = (quality + others)[:60]

# 기사 원문에서 실제 헤드라인·발행 시각 추출 (병렬, 실패 시 CAMEO 라벨 유지)
with ThreadPoolExecutor(max_workers=8) as ex:
    events = list(ex.map(enrich, events))

# 발행 시각이 72시간보다 오래된 재탕 기사는 제외 (신선도 필터)
def too_old(e):
    raw = e.get("ts_pub")
    if not raw:
        return False
    try:
        t = datetime.datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if t.tzinfo is None:
            t = t.replace(tzinfo=datetime.timezone.utc)
        return (datetime.datetime.now(datetime.timezone.utc) - t).total_seconds() > 72 * 3600
    except Exception:
        return False
events = [e for e in events if not too_old(e)]
# 같은 기사(URL) 중복 제거 — 한 기사가 여러 지점 이벤트로 잡히는 경우 최고 임팩트 1건만
seen_urls, uniq = set(), []
for e in events:
    k = e["url"] or e["name"]
    if k in seen_urls:
        continue
    seen_urls.add(k)
    uniq.append(e)
events = uniq
# relevance gate on real headlines: drop local noise, rank market stories first;
# unclassified stories need real coverage (arts) to stay. Refill only if starved.
for e in events:
    e["rel"] = relevance(e)
dropped = [e for e in events if e["rel"] < 0 or (e["rel"] == 0 and e["arts"] < 12)]
kept = [e for e in events if e not in dropped]
kept.sort(key=lambda e: (e["rel"], e["sev"], e["arts"]), reverse=True)
if len(kept) < 8:  # a quiet batch may refill, but only with high-impact non-noise
    dropped.sort(key=lambda e: (e["sev"], e["arts"]), reverse=True)
    kept += [e for e in dropped if e["rel"] >= 1 and e["sev"] >= 4][:8 - len(kept)]
for e in kept:
    e["rel"] = max(0, e["rel"])
events = kept[:25]
enriched = sum(1 for e in events if e.get("ts_pub"))

out = {
    "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "batch": export_url.rsplit("/", 1)[-1].split(".")[0],
    "source": "GDELT 2.0 export (15-min, free)",
    "events": events,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"news.json written: {len(events)} events (quality={len([e for e in events if e['src'] in OUTLETS.values()])}, "
      f"enriched={enriched}, dropped_local={len(dropped)}), batch={out['batch']}, "
      f"rel2+={sum(1 for e in events if e['rel']>=2)}, rel1={sum(1 for e in events if e['rel']==1)}, "
      f"sev5={sum(1 for e in events if e['sev']==5)}, sev4={sum(1 for e in events if e['sev']==4)}")
