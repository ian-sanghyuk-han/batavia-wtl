# CLAUDE.md — Batavia Project Invariants

> Source of truth: `docs/BATAVIA-MASTER-HANDOFF-v2.md` (2026-08-17).
> This file distills its invariants (§0 working contract, §1 product hierarchy, §2 guardrails)
> so every session obeys them without re-reading the full handoff. If they conflict, the
> Master Handoff wins. Never reintroduce amendment files — consolidate changes in place,
> updating the handoff and this file in the same commit.

## Working Contract (§0)

The owner is **not a developer** — deep in financial theory and product vision, new to code, terminals, and git.

1. **All reports to the owner are in Korean**, plain language, with an everyday analogy for every technical term ("커밋했습니다 = 작업 저장 버튼을 눌렀습니다"). Documents and code are English; conversation is Korean.
2. Work in **small increments**. After every unit of work, report in three lines: what was done / where to verify it (URL or preview) / what comes next.
3. **Ask before any destructive change**; create a backup branch first and say so.
4. The owner gives feedback as descriptions, screenshots, and pasted console errors — treat that as a complete bug report.
5. **Never hardcode API keys.** Use environment variables / GitHub Secrets. When a key becomes necessary, request it once, clearly: which key, why, where to get it, and that it is free.
6. Honor every guardrail below in all user-facing output.

## Product Hierarchy (§1)

**Batavia Project** writes a theory of how the world's markets are causally connected, grades that theory against data in public, and sells the daily usefulness that falls out of it.

- **Theory canon** — `BATAVIA-PROJECT-THEORY-CORE.md`. Every number on every screen must trace back to a section of the core.
- **WTL (World Trade Lens)** — the public product. **No trading, no brokerage links, no profit promises.** It only: observes → registers hypotheses → machine-grades them → publishes results.
- **HELM** — the owner's private auto-trading project. **Out of scope.** Keep its code and data fully separated from WTL.

### Structure — one plot, two houses, one warehouse (§1.1)

One domain root, separate buildings that link, never fuse. A product outage must never block publishing.

- **House A — Blog** (`batavia.com`, WordPress, owner-managed). English-canonical posts; ships NOW, gated by no phase. Monetization: AdSense + funnel to WTL.
- **House B — WTL product** (`app.batavia.com`, this repo, built by Claude Code). Priority order inside:
  1. **Event Card** — the front door; free on the web (§6.1).
  2. **Morning Briefing** — the paywall moment; Telegram delivery, ESSENTIAL tier (§6.2, §7).
  3. **Globe Console** — the stage; not the first SKU.
  4. **Logic Ledger** — the engine room (not public); the ONLY place probabilities live; every surface reads from it (§6.5).
  - Monetization: subscriptions only. **No ads inside the product.**
- **Warehouse — Verification Archive** (P3). Verdict pages free forever on every tier. Until it exists, neither house promises live grading links.

### The right to say nothing (§1.2)
Days without an edge get an explicit `no-card` (observation hold) state — itself recorded and graded.

## Language & Legal Guardrails (§2) — apply to ALL user-facing output

- **Banned as directives to users** (Korean product surface): 매수, 매도, 손절, 청산, 목표가, 진입 신호. Signals are three-state observations only: 긍정적 / 중립 / 부정적 관찰.
- **Descriptive market history is allowed** ("외국인 순매수", "캐리 청산", quoted phrases). The test: *does the sentence instruct the user to act?* Instruction → banned. Description → allowed. No action verbs, ever, on product surfaces.
- **Simulated-data labeling**: every widget not yet fed by real data carries a MOCK/SIM/추정 label. Remove per-widget only when that widget goes live on real data.
- **Verdict pages are free forever** on every tier.
- **Before any payment feature ships**, the owner must confirm the Korean 유사투자자문업 (quasi-investment-advisory) legal review is done. Ask explicitly at P5.
- Every quantitative claim carries provenance: core section number and/or Ledger card ID with sample size n.
- The stage is global. Korea is the first "local lens," not the design center.

### Blog grading-claims policy until the Warehouse exists (§2.2)
Citing provenance (Ledger IDs, n, literature) is always allowed. Until the grading archive ships at P3: no live scoreboard links, no preregistration hashes in posts, no promises of clickable graded results. "This blog gets graded" survives only as forward-looking stance; once the archive is live, retrofit grading links into published posts.

### Language architecture (§2.1)
- Code, schemas, commits, engineering docs: **English**. (Korean commit messages/PR descriptions for the owner are fine per §10.)
- Product UI: English base locale (`en`), `ko-KR` first localization; i18n from day one.
- Editorial content (book, blog, verdict prose): **English first** — canonical. Korean versions are the owner's review layer only, generated on demand.
- Reports to the owner: **Korean, always.**
