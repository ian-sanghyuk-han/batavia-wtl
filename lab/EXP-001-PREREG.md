# EXP-001 — Fibonacci Retracement Levels: Preregistration

> Preregistered BEFORE running the analysis. The git commit hash of this file is the
> tamper-evidence: the rule below cannot be changed after seeing the results.
> Ledger linkage: Theory Core §5.8 (chart–statistics correspondence table, Fibonacci row);
> "공개 검증 과제 1호". Experiment order approved by the owner (Master Handoff §6.3).

## Hypothesis (H1, as the chartist community states it)
After a completed downswing in a broad equity index, the subsequent rebound's maximum
retracement ratio clusters at the Fibonacci levels 38.2% and 61.8% more than chance —
i.e., those levels act as special "support/resistance".

H0 (null): retracement ratios show no special concentration at 38.2%/61.8% relative to
equally-wide windows placed elsewhere in the retracement distribution.

## Population
- Instrument: S&P 500 (^GSPC), daily closes, 1985-01-01 through 2026-07-31 (yfinance).
- One market, one timeframe — scope is deliberately narrow; extensions (KOSPI, intraday)
  are future experiments, not post-hoc additions to this one.

## Swing definition (zigzag)
- Reversal threshold θ = 8% on closing prices.
- A pivot HIGH is confirmed when price falls ≥ θ from the running maximum since the last
  pivot LOW; a pivot LOW is confirmed when price rises ≥ θ from the running minimum since
  the last pivot HIGH. Pivots alternate.

## Measurement
For each completed sequence pivot-high H → pivot-low L → next pivot-high H2 (all confirmed):
- retracement ratio r = (H2 − L) / (H − L), capped at r ≤ 1.5; sample = all such r.

## Test statistic
- Fib windows: [0.382 ± 0.04] ∪ [0.618 ± 0.04] (two windows, total width 0.16).
- Observed statistic S_obs = share of sample r falling inside the fib windows.

## Null distribution & decision rule
- Bootstrap B = 2000: each draw places two non-overlapping windows of width 0.08 with
  centers drawn uniformly from [0.15, 1.00]; compute the covered share S_b of the same
  sample r.
- p-value = fraction of draws with S_b ≥ S_obs.
- Decision: if p < 0.05 → "clustering detected" (H1 survives this test).
  Otherwise → **candidate rejection**: Fibonacci levels are knowledge (anchoring folklore,
  Core §5.8), not an opportunity candidate. Either way the verdict is published.
- Costs are not applicable (no trading rule is being graded here); direction rule N/A.
- Zero human override: the script computes the verdict from the numbers above.

## Reproduce
`python lab/exp001_fibonacci.py` (deterministic seed 42).
