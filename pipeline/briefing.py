# Morning Briefing generator (charter M3): six lines + archive link, English default.
# Writes /site/data/briefing.json always; sends via Telegram only when
# TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID env vars exist (GitHub Secrets).
import datetime
import json
import os
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
CARD = os.path.join(HERE, "..", "site", "data", "event_card.json")
OUT = os.path.join(HERE, "..", "site", "data", "briefing.json")
ARCHIVE = "https://ian-sanghyuk-han.github.io/batavia-wtl/card.html"

d = json.load(open(CARD, encoding="utf-8"))
ev, pp = d["event"], d.get("prepricing", {})
sc = (d.get("scenarios") or {}).get("classes", {})
idx, lean = pp.get("index"), pp.get("lean")

rel = datetime.datetime.strptime(ev["release_kst"], "%Y-%m-%d %H:%M")
days = (rel.date() - datetime.date.today()).days
dday = f"D-{days}" if days > 0 else ("D-DAY" if days == 0 else f"D+{-days}")

phrase_en = ("lightly priced" if (idx or 0) < 30 else "partially priced"
             if (idx or 0) < 60 else "largely priced" if (idx or 0) < 80 else "possibly over-priced")

if idx is None:
    asym = "Positioning read unavailable — asymmetry call withheld."
elif lean == "hot" and idx >= 60:
    asym = "The market is already braced for a hot print — confirmation surprises no one; a cool surprise is the bigger shock."
elif lean == "cool" and idx >= 60:
    asym = "The market already leans cool — confirmation reads as no news; a hot surprise is the bigger shock."
elif idx < 30:
    asym = "Positioning is light — either surprise still has room to move prices."
else:
    asym = "Crowding is moderate — the size of the surprise, not its direction, will set the reaction."

def cls(k):
    c = sc.get(k)
    return f"D0 {'+' if c['d0']>=0 else ''}{c['d0']}%, 2y {'+' if c['r2_bp']>=0 else ''}{c['r2_bp']}bp" if c else "n/a"

n_total = sum(c["n"] for c in sc.values() if c)
lines = [
    f"US CPI — Aug 2026 data · {ev['release_kst']} KST / {ev['release_et'].split()[1]} ET ({dday})",
    f"Pre-pricing {idx}/100 ({phrase_en}) · positioning leans {lean}",
    f"Hot print: {cls('hot')} · Inline: {cls('inline')} (S&P hist avg)",
    f"Cool print: {cls('cool')} · n={n_total}, naive-benchmark basis",
    asym,
    "Checkpoints: 21:30 KST release · 22:30 settle · next KRX open 09:05",
]
text = "\n".join(lines) + f"\nArchive: {ARCHIVE}"

out = {"generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
       "event_id": ev["id"], "lines": lines, "archive": ARCHIVE, "text": text,
       "sent": False, "note": "Telegram 발송은 봇 토큰 연결 후 (웹 카드는 무료 — 유료는 '배달'이다 §6.2)"}

tok, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
if tok and chat:
    try:
        body = urllib.parse.urlencode({"chat_id": chat, "text": text,
                                       "disable_web_page_preview": "true"}).encode()
        req = urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage", data=body)
        with urllib.request.urlopen(req, timeout=30) as r:
            ok = json.load(r).get("ok", False)
        out["sent"] = bool(ok)
        print("telegram sent:", ok)
    except Exception as e:
        print("telegram send fail:", e)
else:
    print("telegram env absent — message generated only")

json.dump(out, open(OUT, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
print(f"briefing.json written ({len(lines)} lines)")
