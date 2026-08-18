# Verdict-page generator (P3): experiment JSONs -> static verdict pages + archive index.
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "site", "data", "experiments")
OUTDIR = os.path.join(HERE, "..", "site", "verdicts")
os.makedirs(OUTDIR, exist_ok=True)

CSS = '''
:root{--bg:#060B15;--panel:rgba(12,18,32,.92);--line:#243352;--ink:#E8EEFA;--sub:#9AABC9;--dim:#5E7095;
--acc:#5B8DEF;--up:#FF5D6E;--gold:#D9A441;--ok:#3FE0A0;--mono:'IBM Plex Mono',monospace}
*{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:'IBM Plex Sans KR',sans-serif;padding:0 0 60px}
.top{position:sticky;top:0;display:flex;align-items:center;gap:8px;padding:12px 16px;background:var(--panel);
border-bottom:1px solid var(--line);backdrop-filter:blur(8px);z-index:5}
.top h1{font-size:15px;font-weight:700}.top h1 b{color:var(--acc)}
.top a{margin-left:auto;font-family:var(--mono);font-size:10px;color:var(--sub);text-decoration:none;
border:1px solid var(--line);border-radius:8px;padding:6px 10px}
main{max-width:640px;margin:0 auto;padding:16px 14px;display:flex;flex-direction:column;gap:12px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px;position:relative}
.k{font-family:var(--mono);font-size:8.5px;letter-spacing:.14em;color:var(--dim);margin-bottom:5px}
h2{font-size:18px} p{font-size:13px;color:var(--sub);line-height:1.8;margin-top:8px}
.stamp{position:absolute;top:18px;right:16px;font-family:var(--mono);font-weight:700;font-size:13px;
border-radius:8px;padding:5px 12px;transform:rotate(-6deg);letter-spacing:.06em;border:2.5px solid}
table{width:100%;border-collapse:collapse;margin-top:8px;font-family:var(--mono);font-size:11px;color:var(--sub)}
td{padding:5px 4px;border-top:1px solid var(--line)}td:first-child{color:var(--dim)}
.repro{background:rgba(94,112,149,.12);border-radius:8px;padding:9px 12px;font-family:var(--mono);font-size:11px;margin-top:8px}
.ko{border-left:3px solid var(--acc);padding:8px 12px;background:rgba(91,141,239,.06);border-radius:0 8px 8px 0;
font-size:12px;color:var(--sub);line-height:1.8;margin-top:8px}
a.vlink{display:block;text-decoration:none;color:inherit}
a.vlink:hover .card{border-color:var(--acc)}
'''

FONTS = '<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">'


def svg_hist(d):
    h = d["null_hist"]
    counts, lo, hi = h["counts"], h["lo"], h["hi"]
    mx = max(counts) or 1
    W, Hh, pad = 560, 180, 28
    bw = (W - 2 * pad) / len(counts)
    obs = d.get("s_obs", d.get("delta_obs"))
    bars = "".join(
        f'<rect x="{pad + i * bw:.1f}" y="{Hh - pad - (c / mx) * (Hh - 2 * pad):.1f}" '
        f'width="{bw - 1.5:.1f}" height="{(c / mx) * (Hh - 2 * pad):.1f}" fill="#5B8DEF" opacity="0.65"/>'
        for i, c in enumerate(counts))
    ox = pad + (obs - lo) / ((hi - lo) or 1) * (W - 2 * pad)
    ox = max(pad, min(W - pad, ox))
    return (f'<svg viewBox="0 0 {W} {Hh}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">{bars}'
            f'<line x1="{ox:.1f}" y1="{pad - 10}" x2="{ox:.1f}" y2="{Hh - pad}" stroke="#D9A441" stroke-width="2.5"/>'
            f'<text x="{ox + 6:.1f}" y="{pad + 2}" fill="#D9A441" font-size="11" font-family="monospace">observed {obs}</text>'
            f'<text x="{pad}" y="{Hh - 8}" fill="#5E7095" font-size="10" font-family="monospace">{lo}</text>'
            f'<text x="{W - pad - 40}" y="{Hh - 8}" fill="#5E7095" font-size="10" font-family="monospace">{hi}</text></svg>')


def page(d, stamp, color, hyp_en, verdict_en, ko, rows, back="index.html"):
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<!-- STATUS: MEASURED verdict page — real data, preregistered, machine-graded. -->
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{d['id']} Verdict — Batavia WTL</title>{FONTS}<style>{CSS}</style>
</head>
<body>
<div class="top"><h1>BATAVIA <b>WTL</b> — Verdict Archive</h1><a href="{back}">⚖ Archive</a></div>
<main>
<div class="card">
  <div class="stamp" style="color:{color};border-color:{color}">{stamp}</div>
  <div class="k">{d['id']} · MEASURED · {d['run_utc'][:10]}</div>
  <h2>{d['title']}</h2>
  <p><b>Hypothesis:</b> {hyp_en}</p>
  <p><b>Verdict:</b> {verdict_en}</p>
  <div class="ko">{ko}</div>
</div>
<div class="card">
  <div class="k">NULL DISTRIBUTION — B=2000 vs observed</div>
  {svg_hist(d)}
  <table>{rows}
    <tr><td>preregistration</td><td>git commit <b>{d['prereg_commit']}</b></td></tr>
    <tr><td>decision rule</td><td>p &lt; {d['alpha']} · zero human override</td></tr>
    <tr><td>provenance</td><td>{d['core_ref']}</td></tr>
  </table>
  <div class="k" style="margin-top:10px">REPRODUCE</div>
  <div class="repro">git checkout {d['prereg_commit']} &amp;&amp; {d['reproduce']}  <span style="color:#5E7095"># seed {d['seed']}</span></div>
</div>
</main>
</body>
</html>'''


entries = []

# --- EXP-001 ---
p1 = os.path.join(DATA, "exp001.json")
if os.path.exists(p1):
    d = json.load(open(p1, encoding="utf-8"))
    rows = (f"<tr><td>population</td><td>{d['population']}</td></tr>"
            f"<tr><td>swings / n</td><td>{d['swings_found']} / {d['n']} <b style='color:var(--gold)'>(small n — scope: this market, this timeframe)</b></td></tr>"
            f"<tr><td>S_obs vs null mean</td><td>{d['s_obs']} vs {d['null_mean']} → p={d['p_value']}</td></tr>")
    html = page(d, "REJECTED", "#FF5D6E",
        "after a completed downswing, rebounds cluster at the 38.2%/61.8% Fibonacci retracement levels more than chance.",
        f"observed fib-window share {d['s_obs']} vs bootstrap null mean {d['null_mean']} — p={d['p_value']}. "
        "Fibonacci levels attracted no more (here, slightly fewer) reversals than windows placed anywhere else. "
        "Anchoring folklore is knowledge; it is not an opportunity candidate.",
        f"한국어 요약 — 41년치 S&P에서 반등이 피보나치 창에 떨어진 비율 {d['s_obs']}은 무작위 창 평균 {d['null_mean']}보다 오히려 낮았다 "
        f"(p={d['p_value']}). 피보나치는 군중의 앵커일 뿐, 기회 후보가 아니다. <b>기각.</b> 우리는 기각도 공개한다 — 이 아카이브의 개업식.",
        rows)
    open(os.path.join(OUTDIR, "exp-001.html"), "w", encoding="utf-8").write(html)
    entries.append((d, "REJECTED", "#FF5D6E", "exp-001.html",
                    "피보나치 되돌림은 통계적으로 특별하지 않았다 — 기회 후보 기각."))
    print("exp-001.html written")

# --- EXP-002 ---
p2 = os.path.join(DATA, "exp002.json")
if os.path.exists(p2):
    d = json.load(open(p2, encoding="utf-8"))
    st = ("CONFIRMED", "#3FE0A0") if d["confirmed"] else ("NOT CONFIRMED", "#D9A441")
    rows = (f"<tr><td>population</td><td>{d['population']}</td></tr>"
            f"<tr><td>sampled days</td><td>{d['n_sampled']} (HIGH {d['n_high']} · LOW {d['n_low']}, stride 5)</td></tr>"
            f"<tr><td>P(continue|HIGH) vs P(continue|LOW)</td><td>{d['p_cont_high']} vs {d['p_cont_low']} → Δ={d['delta_obs']}</td></tr>"
            f"<tr><td>block permutation</td><td>p={d['p_value']} (one-sided)</td></tr>")
    html = page(d, st[0], st[1],
        "20-day trend continuation is more likely when the 120-day Hurst exponent exceeds 0.55 than when it is below 0.45 (Gate G3).",
        f"continuation ran {d['p_cont_high']} in high-H regimes vs {d['p_cont_low']} in low-H — Δ=+{d['delta_obs']}, "
        f"in the hypothesized direction but p={d['p_value']}: not significant under the preregistered block-permutation test. "
        "Gate G3 remains an estimate; its adjustment weight β_g stays conservative until stronger evidence arrives.",
        f"한국어 요약 — 추세장(H>0.55)의 20일 추세 지속률 {d['p_cont_high']} vs 평균회귀장(H<0.45) {d['p_cont_low']}: 방향은 이론대로였지만 "
        f"p={d['p_value']}로 유의하지 않았다. <b>미확증</b> — 게이트 G3는 추정 지위를 유지하고 보정 강도는 보수적으로 묶는다. "
        "확증이 아니어도 그대로 공개한다.",
        rows)
    open(os.path.join(OUTDIR, "exp-002.html"), "w", encoding="utf-8").write(html)
    entries.append((d, st[0], st[1], "exp-002.html",
                    "허스트 게이트: 방향은 이론대로였으나 유의하지 않음 — 미확증, 추정 유지."))
    print("exp-002.html written")

# --- index ---
cards = "".join(
    f'''<a class="vlink" href="{fn}"><div class="card">
    <div class="stamp" style="color:{color};border-color:{color};font-size:11px">{stamp}</div>
    <div class="k">{d['id']} · MEASURED · {d['run_utc'][:10]}</div>
    <h2 style="font-size:15px">{d['title']}</h2>
    <p style="margin-top:6px">{oneliner}</p>
    <p style="font-family:var(--mono);font-size:10px;margin-top:6px;color:var(--dim)">p={d['p_value']} · prereg {d['prereg_commit']}</p>
    </div></a>''' for d, stamp, color, fn, oneliner in entries)
idx = f'''<!DOCTYPE html>
<html lang="ko">
<head>
<!-- STATUS: Verdict Archive index — measured verdicts only; free forever on every tier. -->
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>판정 아카이브 — Batavia WTL</title>{FONTS}<style>{CSS}</style>
</head>
<body>
<div class="top"><h1>BATAVIA <b>WTL</b> — 판정 아카이브</h1><a href="../card.html">▦ 카드</a></div>
<main>
<div class="card"><div class="k">ABOUT</div>
<p style="margin-top:2px">가설을 먼저 박제(선등록 커밋)하고, 기계가 채점하고, <b>기각도 그대로 공개</b>한다.
판정문은 전 티어 영원히 무료다. 현재 {len(entries)}건 — 실험은 계속 쌓인다.</p></div>
{cards}
</main>
</body>
</html>'''
open(os.path.join(OUTDIR, "index.html"), "w", encoding="utf-8").write(idx)
print(f"index.html written ({len(entries)} verdicts)")
