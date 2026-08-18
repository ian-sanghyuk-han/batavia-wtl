# GDELT 2.0 news pipeline (P2-2): latest 15-min export -> /site/data/news.json
# Impact scoring: |GoldsteinScale| (event intensity) + NumArticles (coverage) + |AvgTone|.
# stdlib only — no extra deps needed in CI.
import datetime
import io
import json
import os
import urllib.request
import zipfile
from urllib.parse import urlparse

OUTLETS = {  # well-known outlets get pretty names; everything else shows its domain
    "reuters.com": "Reuters", "bloomberg.com": "Bloomberg", "apnews.com": "AP",
    "bbc.com": "BBC", "bbc.co.uk": "BBC", "cnn.com": "CNN", "nytimes.com": "NYT",
    "wsj.com": "WSJ", "ft.com": "FT", "cnbc.com": "CNBC", "aljazeera.com": "Al Jazeera",
    "theguardian.com": "Guardian", "afp.com": "AFP", "dw.com": "DW",
    "yna.co.kr": "연합뉴스", "chosun.com": "조선일보", "hankyung.com": "한국경제",
    "mk.co.kr": "매일경제", "koreaherald.com": "Korea Herald",
}

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "site", "data", "news.json")

LASTUPDATE = "http://data.gdeltproject.org/gdeltv2/lastupdate.txt"

# CAMEO event root codes -> Korean labels
ROOT_KO = {
    "01": "공식 성명", "02": "호소·요청", "03": "협력 의사", "04": "협의·회담",
    "05": "외교 협력", "06": "물질 협력", "07": "원조 제공", "08": "양보·완화",
    "09": "조사·수사", "10": "요구", "11": "비난·불승인", "12": "거부",
    "13": "위협", "14": "시위", "15": "무력 과시", "16": "관계 축소",
    "17": "강압", "18": "폭행·공격", "19": "전투", "20": "대량 폭력",
}

txt = urllib.request.urlopen(LASTUPDATE, timeout=30).read().decode()
export_url = next(l.split()[2] for l in txt.strip().splitlines()
                  if l.split()[2].endswith(".export.CSV.zip"))
raw = urllib.request.urlopen(export_url, timeout=120).read()
z = zipfile.ZipFile(io.BytesIO(raw))
lines = z.read(z.namelist()[0]).decode("utf-8", errors="replace").splitlines()

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
    label = ROOT_KO.get(root, "이벤트")
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

# 임팩트 순 상위 40건만 — 큰 뉴스가 크게, 조용한 시간엔 조용하게
events.sort(key=lambda e: (e["sev"], e["arts"]), reverse=True)
events = events[:40]

out = {
    "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
    "batch": export_url.rsplit("/", 1)[-1].split(".")[0],
    "source": "GDELT 2.0 export (15-min, free)",
    "events": events,
}
os.makedirs(os.path.dirname(OUT), exist_ok=True)
json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"news.json written: {len(events)} events, batch={out['batch']}, "
      f"sev5={sum(1 for e in events if e['sev']==5)}, sev4={sum(1 for e in events if e['sev']==4)}")
