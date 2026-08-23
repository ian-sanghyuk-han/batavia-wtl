# Backtest pipeline

Turns the ledger's IF→THEN cards into a machine-run historical record:
fire days, graded observation windows, per-card hit rates with n — and,
as the product surface, a "fire calendar" (GitHub-grass heatmap of days
when cards fired, each day clickable into a replay).

Everything here is labeled **추정/estimate** on every published surface:
it is a historical reconstruction run AFTER the fact, kept strictly
separate from the live preregistered grading record (§2 of the handoff).
The two must never be summed into one statistic.

## Phases

1. **Triage** (`triage.json`, done) — every base card classified:
   - `ready` 25 · `partial` 13 (with stated substitutions) · `blocked` 10
     (named blockers; parked until a feed exists).
   - Interactions become testable automatically when their components are;
     gates (regime w / convergence C / Hurst H) enter as conditioning
     variables so hit rates can be reported gate-on vs gate-off.
2. **Harvest + skeleton** — `fetch_history.py` downloads every series in
   triage.json into `data/history/backtest/` (committed once, refreshed
   rarely); `run_backtest.py` walks the calendar day by day, evaluates
   each ready/partial trigger, opens observation windows, grades them,
   and writes `fires.jsonl` (one row per fire: card, date, values,
   window, verdict) plus `scorecard.json` (per card: n, hit rate, era
   splits).
3. **Surfaces** — fire-calendar heatmap page (click a day → replay it),
   scorecard badges on ledger cards ("history: n=37, 64% · est."),
   both reading the phase-2 outputs.

## Conventions (binding for phase 2)

- **Units (protocol 1.4)**: every window is in **trading days** (weekdays),
  repo-wide, via `tadd()/tdays()`. The 2026-08-23 unit audit converted
  windows that had been written in calendar days (x5/7): INF-001 3->2,
  INF-003 14->10, RAT-002 28->20, RAT-003 14->10, LIQ-001 [7,28]->[5,20],
  LIQ-002 [7,28]->[5,20], LIQ-003 7->5, POS-001 [7,56]->[5,40],
  POS-002 [3,21]->[2,15], PHY-002 [14,42]->[10,30], PHY-004 28->20,
  PHY-005 28->20, MKT-001 28->20, MKT-002 42->30, MKT-003 14->10,
  EVT-003 5->4, GRO-006 7->5, EVT-004 label 60->42. Month-denominated
  windows (21/42/63/126/189/252/504) were already trading days and are
  now *executed* as such (previously the code stepped calendar days, so
  e.g. RAT-001's 504 ran as 16.5 months instead of 24).
- **Two verdict columns, published side by side, never overwritten
  (protocol 1.6)**: `hit` = legacy sign-only rule; `hit01` = the inherited
  Handoff 6.3 rule, *signed move of the anchor beyond +/-0.1% in the biased
  direction*. For rate anchors the 0.1% is relative to the level at fire.
  Flag/classification/harvest verdicts (RAT-001, RAT-005 branch, MKT-007)
  copy the sign verdict into `hit01` because no price band applies.
- **Three-state decision (recorded 2026-08-23)**: a move inside the
  +/-0.1% band is **NULL - excluded from n** (`nulls01` counts them), not
  a miss. Rationale: the band marks "no information", and the live 6.3
  rule already treats an in-band move as a neutral observation rather
  than a wrong one; counting it as a miss would make P depend on the
  volatility regime instead of on direction. Applied uniformly to every
  card; scorecard exposes `graded01 / hits01 / rate01 / nulls01`.
- **Frequency table (protocol 1.7)**: `frequency.json` — per card: class
  (E/S/R), fires, window, fires_per_year, median gap; per year: distinct
  days with >=1 and >=2 fires.

- **surprise_naive**: where the card's original trigger compares a
  release to consensus (paid history), the backtest substitutes
  "actual vs naive forecast (12m trailing mean change), in trailing
  sigma" — stated on the card and in the methodology page.
- **observe**: hit = sign of target return over the stated lag window
  matches the card's biased direction (or the named non-price flag,
  e.g. NBER recession for L-RAT-001).
- **fire_dedup**: a card cannot re-fire while its own window is open.
- **era splits**: report pre/post 2015 where the card alleges decay
  (e.g. L-EVT-001).
- **manual event tables** (OPEC outcomes, election dates, FOMC dates)
  live in this directory as CSVs with sources cited per row.

## Free sources used

FRED (key: `FRED_API_KEY`), Yahoo daily history, EIA open data, NOAA
ONI/degree days, CFTC COT archives, IMF PortWatch (chokepoints, 2019+),
Binance funding history (2019+), CBOE put/call CSVs, ICI weekly flows,
Atlanta Fed GDPNow vintages.
