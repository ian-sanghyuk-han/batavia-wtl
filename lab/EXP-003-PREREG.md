# EXP-003 — Credit Leads Equities (the flagship card): Preregistration

> Preregistered BEFORE running. The git commit hash of this file freezes the rule.
> Ledger linkage: 크레딧 선행 — HY 급확대 (radar card family, core §2.6, grade A−,
> claimed lead 3–7 days). Experiment order #3 per Master Handoff §6.3.

## Hypothesis
H1: a sharp widening of the US high-yield credit spread precedes equity weakness —
after a signal day, the next 5 trading days of the S&P 500 average LOWER returns than
random days do.
H0: forward returns after credit-widening signals are no different from ordinary days.

## Data
- HY OAS: FRED BAMLH0A0HYM2, daily, full history (starts 1996-12-31) … 2026-07-31.
- Equity: S&P 500 (^GSPC) daily closes over the same span (yfinance).

## Signal definition (no lookahead)
On each OAS business day t with ≥ 257 prior observations:
- Δ5_t = OAS_t − OAS_{t−5} (percentage points).
- σ_t = standard deviation of {Δ5} over the TRAILING 252 OAS days (ending t−1).
- Signal if Δ5_t ≥ 1.5 · σ_t, with a 5-day cooldown (no signal counted if another
  signal occurred in the prior 5 OAS days).

## Outcome
- Entry = last ^GSPC close on or before t; exit = the 5th ^GSPC close after entry.
- Forward return r_t = ln(exit / entry). Days without 5 subsequent closes are dropped.

## Test
- Observed statistic: mean forward return over all signal days, m_sig.
- Null: B = 2000 draws (seed 42); each draw samples |signals| distinct eligible
  non-signal days uniformly and computes the mean forward return m_b.
- One-sided p = fraction of draws with m_b ≤ m_sig.
- Decision: p < 0.05 → CONFIRMED (credit widening carries 5-day downside information).
  Otherwise NOT CONFIRMED. Secondary descriptives (hit rate of negative forward return,
  median, worst) are reported but do not enter the decision. Zero human override.

## Reproduce
`python lab/exp003_credit.py` (seed 42)

---

## Amendment 1 — data availability (BEFORE any valid run; v1 run void)
Discovered on first execution: FRED now serves BAMLH0A0HYM2 only from 2023-08-21
(ICE licensing truncation) — the preregistered population (1996→) is unavailable, and
the resulting 6-signal run is VOID for lack of the specified population (recorded here
for transparency; its numbers are not a verdict).
Substitution, same rule otherwise: **BAA10Y** (Moody's Baa corporate yield minus 10-year
Treasury, FRED, daily, full history from 1986-01-02 … 2026-07-31). All thresholds,
cooldown, outcome, test and decision rule are unchanged. This amendment is committed
before the substituted run; both commit hashes appear on the verdict page.
