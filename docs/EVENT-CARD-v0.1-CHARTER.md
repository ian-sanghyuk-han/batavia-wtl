# Event Card v0.1 — Charter for Claude Code
> Handoff document. Nothing here is invented — every requirement below is derived directly from `BATAVIA-MASTER-HANDOFF-v2.md` §6.1 (Event Card) and §6.2 (Morning Briefing). Where this charter is silent, that document governs. Cite section numbers back to it in any follow-up question.

---

## 0. Scope & position in the product

- Event Card is the **front door** of House B (the WTL product) — the first public SKU, shipping at roadmap phase **P2.5** (§9).
- Priority order inside House B: **Event Card → Morning Briefing → Globe Console → Logic Ledger** (§1.1).
- Out of scope for this charter: Globe Console engineering (§6.4), the Verification Archive / Warehouse build (§6.3 — arrives at P3), HELM (never — out of scope for this entire project room).
- Target event for v0.1 (recommended, pending owner confirmation): **US CPI, August 2026 data, release September 11, 2026, 08:30 ET / 21:30 KST.** Rationale in the accompanying room discussion. If the owner overrides this pick, everything below still applies unchanged — only the specific numbers on the card change.

---

## 1. Non-negotiable guardrails (apply to every screen below) — §2

- **Three-state language only**: 긍정적 / 중립적 / 부정적 관찰 (positive / neutral / negative observation). Never 매수, 매도, 손절, 청산, 목표가, 진입 신호, and never an imperative verb telling the user what to do.
- **The test for any sentence**: does it instruct the user to act? → banned. Does it describe what the market/data did? → allowed.
- **Provenance on every quantitative claim**: Ledger card ID + sample size n, and/or Theory Core section number.
- **SIM/MOCK/추정 labeling**: any widget or number not yet backed by real data must carry the label. Remove it only per-widget, at the moment that specific widget goes live on real data.
- **Verdicts are free forever**, on every tier — never paywalled, including inside ESSENTIAL.
- **Auto-grading ≠ the Warehouse**: the per-card stamp described in §2 below is a lightweight, deterministic checkpoint grade. It is NOT the full Verification Archive league table (§6.3), which is P3 scope. Do not imply a scoreboard/league exists before P3.

---

## 2. Screen M1 — The Average Card (web, free)
*Source: §6.1 anatomy points 1–5, 7.*

Must render:
1. **Header** — event name, release timestamp in both KST and ET, consensus figure, prior figure, and — in the card footer — the Ledger card ID + n.
2. **Pre-pricing index (0–100 + phrase)** — z-standardized pre-event drift of the relevant assets over the last 5 trading days vs. the historical pre-event median for this release type. Formula: F1 (surprise standardization) + F2 (z-score), both from the Ledger.
3. **Conditional scenario row** — beat / inline / miss → historical average reaction → pre-pricing-adjusted reaction, for D+0 and D+1 of the anchor asset.
4. **The asymmetry sentence** — exactly one plain sentence naming which side is crowded. This is the card's single most important line; it must stand on its own if everything else were cut.
5. **Three checkpoints** as objective clock times (release / settle / next local open) — no action verb attached to any of them.
6. **`no-card` state** — if the day has no qualifying event, render a one-line entry. This is not an error state; it is a first-class, gradeable state (§1.2).

**Acceptance criteria (M1):**
- [ ] Zero hits on the banned-word scan (§2 list); the single declared 계좌 exception does not apply on this surface.
- [ ] Every number on the card resolves in ≤1 tap to its Ledger card ID / core section (ⓘ interaction pattern).
- [ ] MOCK/SIM/추정 label present on any not-yet-real widget.
- [ ] No direction word ("buy/sell/target") anywhere, including inside the asymmetry sentence.
- [ ] `no-card` day renders at equal visual weight to a normal card in the feed — not hidden, not shrunk.

---

## 3. Screen M2 — Expanded Detail View
*Source: §6.1 anatomy points 6, 8, plus the deeper math implied by points 2–3.*

In addition to everything in M1:
6. **Auto-grading stamp** — after the event, each of the three checkpoints is graded automatically (±0.1% direction rule; note costs where the Ledger specifies them) and stamped onto this same card. Graded cards accumulate toward the card-type's displayed hit rate.
7. **Demotion visibility** — the displayed hit rate for this card type comes from the Ledger; if a regime gate applies (w, convergence C, Hurst H), show the adjusted `P′ = clip(P + Σβ_g·(g − ḡ), 0.45, 0.85)` next to the raw Ledger P, with a one-line note of which gate fired.
8. **Full derivation trail** — which 5 assets and which window fed the pre-pricing index, and the historical pre-event median it was compared against. Available on demand; not required on first paint.

**Acceptance criteria (M2):**
- [ ] A repeated miss visibly moves the card type's displayed rate, and a grade-arrow (↓) appears if it crosses the demotion threshold (§6.1 point 8).
- [ ] Any regime-gate adjustment is shown as a delta from raw P, never silently baked in.
- [ ] Every figure on this screen resolves to a Ledger card ID + n — no orphan numbers.
- [ ] No scoreboard/league language reserved for the P3 Warehouse appears here (§2.2 boundary respected as a matter of house style, even though this is product surface, not blog).

---

## 4. Screen M3 — Morning Briefing message
*Source: §6.2, verbatim structure.*

Six lines, in order:
1. Event & time
2. Pre-pricing one-liner
3–4. Scenario table compressed to two lines
5. The asymmetry sentence (unchanged from M1)
6. Checkpoints
\+ Archive link (always present, free)

Delivery mechanics:
- Channel: Telegram bot.
- Default locale: **English**; `ko` follows later as a localization (§2.1) — do not block v0.1 on Korean copy.
- Delivery time localized per market; v0.1 starts at **07:30 KST**.
- The web card stays free; **delivery** is the paid ESSENTIAL feature — not the content itself.

**Acceptance criteria (M3):**
- [ ] Message is exactly six lines + archive link — no more, no less structurally.
- [ ] Same guardrail scan as M1 (banned words, no imperative).
- [ ] Successfully sent at 07:30 KST in a test run for a KST-relevant event.
- [ ] Archive link resolves (even to a "verdict pending" placeholder) rather than 404s.

---

## 5. Data engineering note
*Source: §6.1 closing line.*

Pre-pricing and conditional-scenario statistics are a recomputation over price history + the event/consensus list already expected in the P0 pipeline (§4: FRED, yfinance, Stooq, CFTC COT — all keyless or free-tier). **No new data source category is required to ship M1–M3.** Do not introduce a paid source to hit v0.1.

---

## 6. Definition of done

Per §6.1: *"Three screens define v0.1 (acceptance = charter M1–M3)."* This charter is satisfied when **one real event** produces all three screens, each passing its own checklist above, end to end: card visible the day before → the same card stamped the day after.

---
*Derived from BATAVIA-MASTER-HANDOFF-v2.md §1.1, §1.2, §2, §2.1, §2.2, §6.1, §6.2. Conflicts resolve in favor of that document.*
