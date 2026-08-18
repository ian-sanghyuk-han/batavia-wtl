# EXP-002 — Hurst Switch (Gate G3): Preregistration

> Preregistered BEFORE running. The git commit hash of this file freezes the rule.
> Ledger linkage: Gate G3 (H>0.55 → momentum-family cards P↑ / H<0.45 → contrarian-family P↑),
> L-MKT-006 vicinity; Theory Core §5.9 (Hurst) & §8.2. Experiment order #2 per Master Handoff §6.3.

## Hypothesis
H1: trend persistence is regime-dependent as the Hurst exponent claims — the probability
that the NEXT 20 trading days continue the sign of the PAST 20 trading days is higher on
days when H(120) > 0.55 than on days when H(120) < 0.45.
H0: no difference (H carries no regime information at this horizon).

## Population
S&P 500 (^GSPC) daily closes, 1985-01-01 … 2026-07-31 (yfinance). One market, one timeframe.

## Hurst estimation (fixed algorithm)
On each day t with ≥120 prior log-returns, take the window of the last 120 log-returns:
- For n ∈ {15, 30, 60, 120}: split the window into ⌊120/n⌋ consecutive blocks;
  per block compute R/S = (range of cumulative mean-deviations) / (block std, ddof=0,
  blocks with zero std are skipped); average across blocks → RS(n).
- H_t = OLS slope of ln RS(n) on ln n over the available n.

## Measurement
- Sampled days: every 5th trading day (stride 5) with valid H and full ±20-day returns.
- Continuation indicator C_t = 1 if sign(sum of log-returns t+1…t+20) equals
  sign(sum of log-returns t−19…t), else 0 (either sum exactly 0 → drop the day).
- Groups: HIGH = {H_t > 0.55}, LOW = {H_t < 0.45}; mid-band days are excluded.
- Observed statistic Δ_obs = mean(C | HIGH) − mean(C | LOW).

## Null distribution & decision rule
- Block permutation, B = 2000, seed 42: permute the HIGH/LOW/mid labels across the sampled
  sequence in contiguous blocks of 12 sampled points (≈60 trading days) — preserves label
  clustering; recompute Δ_b each draw (draws lacking either group are redrawn).
- One-sided p = fraction of draws with Δ_b ≥ Δ_obs.
- Decision: p < 0.05 → G3 CONFIRMED at this horizon (gate graduates toward "measured").
  Otherwise → NOT CONFIRMED: the gate stays an estimate and its β_g must remain conservative.
  Either verdict is published. Zero human override.

## Reproduce
`python lab/exp002_hurst.py` (seed 42)
