# Verdict-page generator (P3): one experiment JSON -> one static verdict page.
# v1 supports EXP-001; the template generalizes as experiments accumulate.
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "site", "data", "experiments", "exp001.json")
OUTDIR = os.path.join(HERE, "..", "site", "verdicts")
os.makedirs(OUTDIR, exist_ok=True)

d = json.load(open(SRC, encoding="utf-8"))
rejected = d["p_value"] >= d["alpha"]
stamp = "REJECTED" if rejected else "DETECTED"
stamp_color = "#FF5D6E" if rejected else "#3FE0A0"

# null histogram -> SVG bars + observed marker
h = d["null_hist"]
counts, lo, hi = h["counts"], h["lo"], h["hi"]
mx = max(counts) or 1
W, Hh, pad = 560, 180, 28
bw = (W - 2 * pad) / len(counts)
bars = "".join(
    f'<rect x="{pad + i * bw:.1f}" y="{Hh - pad - (c / mx) * (Hh - 2 * pad):.1f}" '
    f'width="{bw - 1.5:.1f}" height="{(c / mx) * (Hh - 2 * pad):.1f}" fill="#5B8DEF" opacity="0.65"/>'
    for i, c in enumerate(counts))
obs_x = pad + (d["s_obs"] - lo) / ((hi - lo) or 1) * (W - 2 * pad)
obs_x = max(pad, min(W - pad, obs_x))
svg = f'''<svg viewBox="0 0 {W} {Hh}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">
<rect width="{W}" height="{Hh}" fill="none"/>{bars}
<line x1="{obs_x:.1f}" y1="{pad - 10}" x2="{obs_x:.1f}" y2="{Hh - pad}" stroke="#D9A441" stroke-width="2.5"/>
<text x="{obs_x + 6:.1f}" y="{pad + 2}" fill="#D9A441" font-size="11" font-family="monospace">observed {d['s_obs']}</text>
<text x="{pad}" y="{Hh - 8}" fill="#5E7095" font-size="10" font-family="monospace">{lo}</text>
<text x="{W - pad - 30}" y="{Hh - 8}" fill="#5E7095" font-size="10" font-family="monospace">{hi}</text>
</svg>'''

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<!-- STATUS: MEASURED verdict page — real data, preregistered, machine-graded. First real page of the Verification Archive. -->
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<title>{d['id']} Verdict — Batavia WTL</title>
<link href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans+KR:wght@400;600;700&family=IBM+Plex+Mono:wght@400;600&display=swap" rel="stylesheet">
<style>
:root{{--bg:#060B15;--panel:rgba(12,18,32,.92);--line:#243352;--ink:#E8EEFA;--sub:#9AABC9;--dim:#5E7095;
--acc:#5B8DEF;--up:#FF5D6E;--gold:#D9A441;--ok:#3FE0A0;--mono:'IBM Plex Mono',monospace}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{background:var(--bg);color:var(--ink);font-family:'IBM Plex Sans KR',sans-serif;padding:0 0 60px}}
.top{{position:sticky;top:0;display:flex;align-items:center;gap:8px;padding:12px 16px;background:var(--panel);
border-bottom:1px solid var(--line);backdrop-filter:blur(8px);z-index:5}}
.top h1{{font-size:15px;font-weight:700}}.top h1 b{{color:var(--acc)}}
.top a{{margin-left:auto;font-family:var(--mono);font-size:10px;color:var(--sub);text-decoration:none;
border:1px solid var(--line);border-radius:8px;padding:6px 10px}}
main{{max-width:640px;margin:0 auto;padding:16px 14px;display:flex;flex-direction:column;gap:12px}}
.card{{background:var(--panel);border:1px solid var(--line);border-radius:14px;padding:16px 18px;position:relative}}
.k{{font-family:var(--mono);font-size:8.5px;letter-spacing:.14em;color:var(--dim);margin-bottom:5px}}
h2{{font-size:18px}} p{{font-size:13px;color:var(--sub);line-height:1.8;margin-top:8px}}
.mono{{font-family:var(--mono);font-size:11px;color:var(--sub);line-height:1.9}}
.stamp{{position:absolute;top:18px;right:16px;font-family:var(--mono);font-weight:700;font-size:15px;
color:{stamp_color};border:2.5px solid {stamp_color};border-radius:8px;padding:5px 12px;transform:rotate(-6deg);letter-spacing:.08em}}
.big{{font-family:var(--mono);font-size:26px;font-weight:700}}
table{{width:100%;border-collapse:collapse;margin-top:8px;font-family:var(--mono);font-size:11px;color:var(--sub)}}
td{{padding:5px 4px;border-top:1px solid var(--line)}}td:first-child{{color:var(--dim)}}
.repro{{background:rgba(94,112,149,.12);border-radius:8px;padding:9px 12px;font-family:var(--mono);font-size:11px;margin-top:8px}}
.ko{{border-left:3px solid var(--acc);padding:8px 12px;background:rgba(91,141,239,.06);border-radius:0 8px 8px 0;font-size:12px;color:var(--sub);line-height:1.8;margin-top:8px}}
</style>
</head>
<body>
<div class="top"><h1>BATAVIA <b>WTL</b> — Verdict Archive</h1><a href="../card.html">▦ Event Card</a></div>
<main>
<div class="card">
  <div class="stamp">{stamp}</div>
  <div class="k">{d['id']} · MEASURED · {d['run_utc'][:10]}</div>
  <h2>{d['title']}</h2>
  <p><b>Hypothesis (as the chartist community states it):</b> after a completed downswing,
  rebounds cluster at the 38.2% / 61.8% retracement levels — the levels act as special support.</p>
  <p><b>Verdict:</b> the observed share of retracements ending inside the Fibonacci windows was
  <b>{d['s_obs']}</b> against a bootstrap null mean of <b>{d['null_mean']}</b> —
  p = <b>{d['p_value']}</b> (α = {d['alpha']}). Fibonacci levels attracted <i>no more</i> —
  in this sample, slightly fewer — reversals than windows placed anywhere else.
  Anchoring folklore is knowledge; it is not an opportunity candidate.</p>
  <div class="ko">한국어 요약 — 41년치 S&P 500에서 하락 스윙 뒤 반등이 피보나치 레벨(38.2%/61.8%)에서
  끝난 비율은 {d['s_obs']} — 아무 데나 놓은 창(평균 {d['null_mean']})보다 오히려 낮았다.
  p={d['p_value']}: 피보나치는 지식(군중의 앵커)일 뿐, 기회 후보가 아니다. <b>기각.</b>
  우리는 기각도 그대로 공개한다 — 이것이 이 아카이브의 개업식이다.</div>
</div>
<div class="card">
  <div class="k">NULL DISTRIBUTION — bootstrap B=2000 (same-width random windows) vs observed</div>
  {svg}
  <table>
    <tr><td>population</td><td>{d['population']}</td></tr>
    <tr><td>swings / retracements n</td><td>{d['swings_found']} / {d['n']} <b style="color:var(--gold)">(small n — verdict scope: this market, this timeframe)</b></td></tr>
    <tr><td>preregistration</td><td>git commit <b>{d['prereg_commit']}</b> · lab/EXP-001-PREREG.md</td></tr>
    <tr><td>decision rule</td><td>p &lt; {d['alpha']} → detected; else rejected · zero human override</td></tr>
    <tr><td>provenance</td><td>{d['core_ref']}</td></tr>
  </table>
  <div class="k" style="margin-top:10px">REPRODUCE</div>
  <div class="repro">git checkout {d['prereg_commit']} &amp;&amp; {d['reproduce']}  <span style="color:var(--dim)"># seed {d['seed']}</span></div>
</div>
</main>
</body>
</html>'''

open(os.path.join(OUTDIR, "exp-001.html"), "w", encoding="utf-8").write(page)
print("verdict page written: site/verdicts/exp-001.html")
