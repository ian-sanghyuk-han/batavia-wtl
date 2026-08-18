# BATAVIA MASTER HANDOFF v2 — Single Source of Truth
> 2026-08-17 · This document supersedes and fully absorbs: BATAVIA-CLAUDE-CODE-HANDOFF.md (v1), HANDOFF-AMENDMENT-1.md, and BATAVIA-MASTER-SPEC-v3.md. None of those files ship with the final package. There are no amendments to apply on top of this document — everything below is stated as current truth.
> If any packaged file appears to conflict with this document, this document wins. Ask the owner when genuinely ambiguous.

---

## 0. To Claude Code — Working Contract

Your employer is **not a developer.** He is deep in financial theory and product vision, and new to code, terminals, and git. Therefore:

1. **All reports to the owner are in Korean**, in plain language, with an analogy attached to every technical term ("커밋했습니다 = 작업 저장 버튼을 눌렀습니다"). Documents and code are English; conversation is Korean.
2. Work in **small increments**. After every unit of work, report in three lines: what was done / where to verify it (URL or preview) / what comes next. Ask before any destructive change; create a backup branch first and say so.
3. The owner gives feedback by describing what he sees, attaching screenshots, and pasting console errors. Treat that as a complete bug report.
4. Never hardcode API keys. Use environment variables / GitHub Secrets, and when a key becomes necessary, request it once, clearly: which key, why, where to get it, and that it is free.
5. Honor every rule in §2 (language & legal guardrails) in all user-facing output.

### 0.5 First Session Protocol
On the very first session, in order:
1. Read this document end to end.
2. Reply (in Korean) with: a five-line summary of the project; the P0 task list (§9); what you need from the owner right now (GitHub account, FRED key).
3. Create **CLAUDE.md** at the repo root containing the invariants — §1 product hierarchy, §2 guardrails, §0 working contract — so every future session obeys them automatically without re-reading this whole file.
4. Wait for the owner's go, then execute P0.

---

## 1. Project Identity & Product Hierarchy

**Batavia Project** (proper noun, used on all artifacts) writes a theory of how the world's markets are causally connected, grades that theory against data in public, and sells the daily usefulness that falls out of it. Three pillars:

- **Theory canon** — `BATAVIA-PROJECT-THEORY-CORE.md` (3rd ed., Korean). Every number on every screen must trace back to a section of the core.
- **WTL (World Trade Lens)** — the public product. **No trading, no brokerage links, no profit promises.** It only: observes → registers hypotheses → machine-grades them → publishes the results.
- **HELM** — the owner's private auto-trading project. **Out of scope.** Keep its code and data fully separated from WTL.

### 1.1 Structure — one plot, two houses, one warehouse

Everything lives on one domain root (**one plot**), but as separate buildings that link to each other rather than fuse. This separation is deliberate: the blog and the product grow at different speeds and fail in different ways, and a product outage must never block publishing. Integrate later via links and shared accounts — never by welding them together up front.

**House A — the Blog** (`batavia.com`, WordPress, owner-managed via writing Room 1)
- English-canonical posts (Korean review copies for the owner). Ships NOW — it does not wait for any engineering phase.
- Monetization: AdSense + funnel to the WTL product. Content = the serialized narrative built on the Theory Core and the Ledger.

**House B — the WTL product** (`app.batavia.com`, built by Claude Code)
- Hierarchy inside this house, in priority order:
  1. **Event Card** — the front door; free on the web as the shop window (§6.1).
  2. **Morning Briefing** — the paywall moment; Telegram delivery, ESSENTIAL tier (§6.2, §7).
  3. **Globe Console** — the stage: landing wow, PRO control room, replay theater. Not the first SKU.
  4. **Logic Ledger** — the engine room (not public); single source of every probability (§6.5).
- Monetization: subscriptions only. **No ads inside the product.**

**The Warehouse — Verification Archive** (built later, at P3)
- The grading engine and verdict pages (§6.3). Linked FROM both houses; verdict pages free forever on every tier. Until it exists, neither house promises live grading links (§2.2).

### 1.2 The right to say nothing
Days without an edge get an explicit `no-card` (observation hold) state, which is itself recorded and graded. Competitors must always say something; our silence is bought with a scoreboard, and silent cards are what make speaking cards credible.

---

## 2. Language & Legal Guardrails (apply to ALL user-facing output)

- **Banned as directives to users** (Korean product surface): 매수, 매도, 손절, 청산, 목표가, 진입 신호. Signals are expressed only as three-state observations: 긍정적 / 중립 / 부정적 관찰 ("positive / neutral / negative observation").
- **Descriptive market history is allowed**: "외국인 순매수" (an indicator's name), "캐리 청산", "강제 청산의 자기강화", quoted phrases like "현금 외 전부 매도". The test: *does the sentence instruct the user to act?* Instruction → banned. Description → allowed.
- **Simulated-data labeling**: every widget not yet fed by real data carries a MOCK/SIM/추정 label. Remove the label only per-widget, at the moment that widget goes live on real data.
- **Verdict pages are free forever** on every tier.
- **Before any payment feature ships**, the owner must confirm the Korean 유사투자자문업 (quasi-investment-advisory) legal review is done. Ask him explicitly at P5.
- Every quantitative claim carries provenance: core section number and/or Ledger card ID with sample size n.
- The stage is global. Korea is the first "local lens," not the design center.

### 2.2 Blog grading-claims policy (until the Warehouse exists)
Posts cite provenance (Ledger card IDs, sample size n, literature) — that is citation, always allowed. But until the grading archive ships at P3: no live "see the scoreboard" links, no preregistration hashes printed in posts, no promises of graded results that cannot yet be clicked. The "this blog gets graded" identity survives as **forward-looking stance** — the About page and occasional lines may say grading is coming — and once the archive is live, grading links are retrofitted into already-published posts (they are markdown; this is cheap).

### 2.1 Language architecture
- **Code, schemas, commits, engineering docs**: English.
- **Product UI**: English as the base locale (`en`), with `ko-KR` as the first localization. Build i18n from day one (simple JSON string tables are fine).
- **Editorial content** (book, blog, verdict prose): **English first.** The blog and all published prose target a global audience; English is the canonical publication language. Korean versions are the owner's review-and-comprehension layer only — generated on demand, never the canonical edition.
- **Reports to the owner**: Korean, always. (Korean's role in this project: the owner's review language, not a publication default.)
- Migration note: the existing canon files were drafted in Korean. Producing English canonical editions is scheduled work, not an afterthought: THEORY-CORE English 3rd-edition sync, an English adaptation of the book, and every new blog post written in English from day one with a Korean review copy for the owner.

---

## 3. Package Inventory & Honest State of Each File

The final package (`batavia-final/`) contains, besides this document:

| File | What it is | What it does NOT yet reflect |
|---|---|---|
| `batavia-project-globe.html` | Globe console — complete interactive design spec (~956 lines, pure canvas). Features: 3D orthographic + 2D toggle, hand-drawn continents (replace with TopoJSON), line taxonomy with LAYERS panel (capital=arc, air cargo=high arc, sea=surface lines with sailing ships, info/carry=dashed), 5-level news ripples + cascade ignition + 17 opportunity notes, chokepoint blockade (ships queue at Hormuz), center-top 3-column lens, live opportunity radar (6 cards, live EV formula + scramble/sweep/scanline "Jarvis" effects, EV re-sorting), replays 2008 & 2020 (0.5–4× speed, day-by-day date interpolation, era gauges with "선행 적중 ✓" stamps), home anchor, themes, reduced-motion. All data simulated. | The Event Card product (§6.1) does not exist here at all — it is a new build. The globe is the stage, not the front door. |
| `archive_mock_v0_2.html` | Verification archive, one infinite page: HISTORY / BACKTESTS / REPORT / LIVE / SCOREBOARD (league of 11 logics, equity curve with bootstrap band and drawdown shading, pain ledger). All figures are estimates. | Event-card grading history; real data. |
| `batavia-scoreboard-mock.html` | Standalone scoreboard component (sharing/embedding). | Same as above. |
| `wtl_v1_1.html` + `WTL-MASTER-BLUEPRINT.md` | Earlier WTL product mock + blueprint. Still valid for archive/verdict UI language. | Written before the Event-Card-first hierarchy; where hierarchy is implied, §1.1 wins. |
| `batavia-system-map.html` / `-live.html` | Theory chapter-1 map (static / animated). | — |
| `BATAVIA-PROJECT-THEORY-CORE.md` (KO) | Theory canon, 3rd ed. (Korean source) | English canonical edition pending — sync task. |
| `BATAVIA-PROJECT-GIANTS.md` (KO) | Academic lineage & evidence grades. | English edition pending. |
| `BATAVIA-LOGIC-LEDGER-v1.md` (KO) | The 67-card logic ledger (52 base + 12 interaction + 3 gates), formula library F1–F14, statuses including `no-card`. | Estimates awaiting real grading; English edition pending (IDs/formulas are language-neutral). |
| `세계는-어떻게-연결되어-움직이는가-증보판.md` + `.docx` | The popular book (Korean source manuscript) + A4 print edition with blog appendices. | English adaptation pending — English is the publication language. |
| `블로그-연재-기획.md` (KO) | Blog serialization plan (KO). | Posts themselves ship in English; plan is the owner's reference. |
| `batavia-업데이트노트-선박데이터-구독설계.md` (KO) | AIS data scope notes + original 3-tier sketch (superseded by §7 but kept for the AIS section). | Tier table superseded by §7. |
| `클로드코드-첫걸음-가이드.md` + `.docx` (KO) | The owner's own manual (glossary, git-in-3-minutes). Not instructions for you. | — |
| `00-README-매니페스트.md` (KO) | Package manifest for the owner. | — |

Each HTML file carries a status banner comment at the top of `<head>` declaring exactly this. Historical versions (globe v1–v3, wtl v0.x, macro-atlas series, old specs) were intentionally excluded from the package; if you ever need UI inspiration for "always-moving P&L" feels, ask the owner for the macro-atlas lineage.

---

## 4. Data Sources & API Checklist

Principle: keyless & free first. All keyed sources below have free tiers. Store keys in GitHub Secrets; reference via env.

| Priority | Source | Use | Key | Cost |
|---|---|---|---|---|
| P0 | FRED | rates, HY OAS, net liquidity (WALCL−RRP−TGA), macro | **yes** | free |
| P0 | yfinance (python lib) | prices: indices, FX, commodities, equities | no | free |
| P0 | Stooq | long index history CSV backup | no | free |
| P0 | CFTC COT | weekly positioning | no | free |
| P1 | GDELT 2.0 | global news events + geo (15-min) → globe epicenters, event feed | no | free |
| P1 | aisstream.io | live AIS ships (position, type, destination, draught) | **yes** | free |
| P1 | Open-Meteo | weather/climate for lenses & cold-snap card | no | free |
| P1 | Binance public | crypto prices, funding rates | no | free |
| P1 | world-atlas (TopoJSON) | real coastlines/borders replacing hand-drawn shapes | no | free |
| P2 | EIA | energy inventories | yes | free |
| P2 | Bank of Korea ECOS | Korea local lens | yes | free |
| P2 | UN Comtrade | trade volumes → edge weights | limited | free |
| later | Kpler / MarineTraffic commercial | cargo/shipper inference | yes | **paid** — post-revenue |

Ask the owner: at P0 → GitHub account + FRED key. At P1 → aisstream key. At P5 → Supabase/payments decisions + legal-review confirmation.

Note: CME FedWatch implied probabilities are not freely ingestible — proxy rate-cut odds with 2-year yield moves.

---

## 5. Target Architecture

```
GitHub repository
 ├─ /site          static frontend (mockups ported, then modularized; PWA; i18n en/ko)
 ├─ /pipeline      Python (pandas): scheduled by GitHub Actions
 │       daily: prices/macro · 15-min: GDELT · snapshot: AIS
 │       output → /site/data/*.json   (the frontend reads ONLY these JSONs)
 ├─ /lab           experiment notebooks (preregistration, backtests, grader)
 ├─ /archive       verdict-page generator → static pages
 └─ /site/data/replays/*.json   replay scenarios as data (§6.4)
Deploy: GitHub Pages (free; fixes the iPhone file-preview problem).
Domain plan (one plot, two houses): `batavia.com` = the blog (WordPress, owner-managed) · `app.batavia.com` = the WTL product (this repo, GitHub Pages) · the grading archive mounts under the app (or `archive.batavia.com`) at P3. Blog post markdown sources are mirrored into `/content` in this repo for portability and the possible future migration — WordPress is the venue, the repo is the vault.
Later: Supabase (auth, tiers, grading DB in Postgres; start local SQLite), payments after legal review.
Metaphor the owner knows: HTML/TS = face, Python = brain, SQL = memory, you = the plumber.
```

Frontend stack: keep the pure-canvas globe initially; TypeScript + a light framework only when modularization demands it. Codebase English throughout.

---

## 6. Product Specifications

### 6.1 Event Card — the front door (first public SKU)
One card per upcoming event. Anatomy (top to bottom):

1. **Header**: event name, release timestamp (KST + ET), consensus vs prior, Ledger card ID + n in the footer of every card.
2. **Pre-pricing index (선반영 지수)**: how much the market has already moved ahead of the release. Definition: z-standardized pre-event drift — last 5 trading days' moves of the relevant assets (2y yield, DXY, KOSPI/SPX, sector) vs the historical *pre-event median* of past releases of the same type; render as 0–100 with a phrase (e.g., 68 "상당 부분 반영"). Formula family: F1 (surprise standardization) + F2 (z-scores) from the Ledger.
3. **Conditional scenarios**: beat / inline / miss × [historical average reaction → **pre-pricing-adjusted** reaction] for D+0 and D+1 of the anchor asset (e.g., beat: −0.8% → −0.4%). Adjustment uses the pre-pricing index and the Ledger gate formula.
4. **The asymmetry sentence**: one plain sentence stating which side is crowded (e.g., "The market already leans beat; confirmation surprises no one — even inline reads as relief."). This sentence is the card's soul: more useful than a direction call, and fully inside the advisory-law boundary.
5. **Three checkpoints**: e.g., 21:45 release · 22:30 settle · next 09:05 KRX open — objective moments for the reader to check their own judgment. No action verbs ever.
6. **Auto-grading**: after the event, the three checkpoints are graded automatically (±0.1% direction rule, costs noted where relevant) and stamped onto the same card; graded cards accumulate into the Archive.
7. **`no-card` days** (§1.2) are published as a one-line entry and count toward the track record.
8. **Demotion rule**: a card type's displayed hit rates come from the Ledger; regime gates adjust them via `P′ = clip(P + Σβ_g·(g − ḡ), 0.45, 0.85)`. Repeated misses demote the card (grade arrows on the scoreboard).

Three screens define v0.1 (acceptance = charter M1–M3): ① the average card (web, free) ② the expanded detail view ③ the morning briefing message. Data engineering is honest-easy: pre-pricing and conditional stats are recomputation over price history + event lists already in the P0 pipeline.

### 6.2 Morning Briefing (ESSENTIAL)
The day's card(s) compressed to six lines, sent via Telegram bot — **English by default**, per-locale versions (ko) later; delivery time localized per market (v0.1 starts 07:30 KST): event & time / pre-pricing one-liner / scenario table in two lines / asymmetry sentence / checkpoints / archive link. Web stays free; **delivery is what's paid for.**

### 6.3 Verification Archive & Scoreboard
- Schema: `experiments(id, hypothesis, prereg_commit, population, horizon, rule, status)` / `signals(exp_id, fired_at, target, expected_direction, threshold)` / `verdicts(signal_id, graded_at, realized, cost, hit)` / `league` (view).
- Preregistration = a git commit hash printed on the verdict page. Grading: horizons 60min (statements) / 1d + 60d drift (earnings) / 5d (policy); direction threshold ±0.1%; cost 0.08% per signal; zero human override.
- Experiment order (owner-approved): ① EXP-001 Fibonacci (candidate rejection — the honesty grand opening) ② Hurst switch ③ Credit lead ④ FOMC drift ⑤ the 30-year re-grading expedition (HISTORY goes real).
- Verdict-page generator: one experiment → one static page (null-distribution chart + stamp + reproduce command), templated from `archive_mock_v0_2.html`. Verdict prose is English (canonical); Korean review copies for the owner on demand. The scoreboard league is a query over `verdicts`; mock estimates get replaced cell by cell.

### 6.4 Globe Console
Keep the existing feature set (see §3 table). Engineering priorities: TopoJSON geography; mobile touch (drag/pinch, collapsible HUD); PWA; then the **3-second visibility rules** —
- Live: headline banner (top severity event or calm-regime sentence) · bottom delta ticker strip (6–8 gauges) · idle auto-tour · 24h catch-up card on load.
- Replay: draggable scrubber with chapter markers · one-line narration captions · real-price mini-chart running in parallel (post-P2) · end-of-replay "what led what" summary table · optional grading-stamp quiz mode.
- MOCK→real mapping: news/epicenters←GDELT · ships←aisstream (tanker/container filter) · regime w & convergence←computed per core §5.2 · radar card numbers←FRED+derived, results←grading DB · lens KPIs←yfinance/FRED/ECOS · weather←Open-Meteo · edge weights←Comtrade+CAR.
- Replay backlog (scenarios are DATA, not code — `/site/data/replays/*.json` with `events[]`, `gauges[]` keyframes, `sources[]`; keyframes must come from measured data): 1997 Asia, 2000 dot-com, 2010–12 eurozone, 2013 taper tantrum, 2015 CNY, 2016 Brexit, 2018 Volmageddon, 2022 inflation year, 2023 SVB, 2024-08-05 yen-carry day.

### 6.5 Logic Ledger
`BATAVIA-LOGIC-LEDGER-v1.md`: 52 base cards (10 categories) + 12 preregistered interaction cards + 3 regime gates (w, convergence C, Hurst H) + formula library F1–F14. Card statuses: `estimate → preregistered → live-grading → measured`, plus `no-card` (observation hold). Cards failing the EV inequality (F6) remain "knowledge," never "opportunity candidates." 1:1 mapping everywhere: one card = one blog post = one radar candidate = one grading row. The Ledger is the only place probabilities live; every surface reads from it.

---

## 7. Subscriptions & Accounts

| | Visitor | Free member | **ESSENTIAL** (revenue core) | PRO (console) | DESK |
|---|---|---|---|---|---|
| Substance | web cards | all cards + delayed map + weekly digest | **morning briefing delivery (Telegram)** + card deep view + alerts | real-time globe, full radar, full replays incl. quiz mode | API/CSV/webhooks, custom |
| Price feel | free | free (signup) | ~ price of two coffees / month — volume product | ₩10–20k/mo | ₩100k+/mo/seat |
| Verdicts | free | free | free | free | free |

Monetization split across the plot: blog = AdSense + funnel; the WTL product = subscriptions only, ad-free. Auth: Supabase magic-link (no passwords). Payments (Stripe or Toss) only after the legal review is confirmed. The signup reward alone must feel generous (delay cut + all cards + weekly digest): the ladder is habit → delivery → console.

---

## 8. Visibility Doctrine (applies to everything)
A first-time visitor must know within 3 seconds: what is happening, where, and what changed. Color/size = intensity, one consistent grammar. Numbers always carry provenance (core §, Ledger ID, n). Show pain the same size as gain (drawdowns beside returns). Mobile-first checks on every ship. Respect `prefers-reduced-motion`.

---

## 9. Roadmap (each phase ends with an owner-verifiable sentence)

- **P0 Launch**: repo → port package files → GitHub Pages live. ✅ "The globe spins in iPhone Safari at a real URL."
- **P1 Hull**: TopoJSON, mobile touch + HUD folding, PWA, perf pass, visibility phase 1 (headline banner, delta ticker, replay scrubber). ✅ "It runs from a home-screen icon on real coastlines under my fingers."
- **P2 Blood**: pipelines (FRED/yfinance/GDELT/AIS/Open-Meteo → JSON); replace MOCK per §6.4 mapping widget by widget; replay real-price mini-charts. ✅ "The news is today's news and the ships are real ships."
- **P2.5 Event Card v0.1 — FIRST PUBLIC SKU**: one card for the next CPI or FOMC (pre-pricing + scenarios + asymmetry + checkpoints) → auto-graded after release. ✅ "I see the card the day before, and the same card stamped the day after."
- **P3 The Judge**: grading engine (§6.3), run EXP-001, publish the first measured verdict; archive goes real. ✅ "A verdict page with a real stamp, no 추정 ribbon."
- **P4 The Theater**: replay format migration + new scenarios in backlog order (measured keyframes only) + summary cards + quiz mode. ✅ "I watch 1997 at 2× and read 'what led what' at the end."
- **P5 Boarding Pass**: Supabase auth, tier gates, ESSENTIAL Telegram bot, weekly digest. Payments only after legal confirmation. ✅ "Logging in unlocks my briefing."
- **P6 Operations**: pipeline failure alerts, cost report, backups. Blog-side work in this phase: retrofit grading links into published posts once the Warehouse is live (§2.2); optionally migrate the blog under the app roof if widget embedding demands it. English canonical editions of the theory core and book are tracked here. (The blog itself launches at day one on WordPress — it is not gated by any phase.)

---

## 10. Working Culture
Korean commit messages are fine; PR descriptions in Korean for the owner. This document is alive — when a major decision changes, update it (and CLAUDE.md) in the same commit, and never reintroduce an amendment-file pattern: consolidate in place.

*— This is the whole ship. Put it in the water.*
