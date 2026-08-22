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
