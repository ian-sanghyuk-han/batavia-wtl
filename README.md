# Batavia Project — WTL (World Trade Lens)

WTL observes how the world's markets are causally connected, registers hypotheses, machine-grades them in public, and publishes the results. No trading, no brokerage links, no profit promises.

- **Live site**: https://ian-sanghyuk-han.github.io/batavia-wtl/
- **Source of truth**: [docs/BATAVIA-MASTER-HANDOFF-v2.md](docs/BATAVIA-MASTER-HANDOFF-v2.md)
- **Session invariants**: [CLAUDE.md](CLAUDE.md)

## Layout

| Path | Role |
|---|---|
| `/site` | Static frontend (GitHub Pages serves this directory) |
| `/site/data` | JSON outputs the frontend reads (written by `/pipeline`) |
| `/pipeline` | Python data pipelines, scheduled by GitHub Actions (P2) |
| `/lab` | Experiment notebooks — preregistration, backtests, grader (P3) |
| `/archive` | Verdict-page generator (P3) |
| `/content` | Blog post markdown mirror — WordPress is the venue, this repo is the vault |
| `/docs` | Handoff, charters, theory canon, logic ledger |

All interactive pages currently run on **simulated data** and are labeled MOCK/SIM/추정 per the guardrails. Labels are removed per-widget only when that widget goes live on real data.
