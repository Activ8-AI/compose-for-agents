# Meta Mega Codex — Charter Standard Execution

This document summarizes how the layered charter is implemented inside this repository. Each layer is declarative and references deterministic assets so the system can be audited or re-run at any time.

## Layer 1 — Charter Doctrine
- Sovereign boundaries, determinism, audit immutability, resilience, evidence coherence, and zero drift are encoded inside the domain policies plus the core runtime found under `charter_core/`.
- Every sweep produces append-only evidence with a SHA-256 integrity hash and is mirrored into `logs/` and `evidence/`.

## Layer 2 — Policies
- Domain policies: `activ8_domain_policy.json`, `lma_domain_policy.json`, `personal_domain_policy.json`
- Copilot policies: `activ8-ai-copilot.json`, `lma-copilot.json`, `personal-copilot.json`
- Use `from charter_core import load_policy_bundle` to fetch validated bundles.

## Layer 3 — Governors
- Policy-aware sweeps live in `activ8_governor.py`, `lma_governor.py`, and `personal_governor.py`.
- Universal routing is exposed via `mcp_governor_router.py --governor <name>`.

## Layer 4 — Resilience
- `resilient_governor_runner.py` fans out to all governors with retries/backoff.
- `watchdog.py` enforces freshness windows from the domain policies.
- `governor_evidence_aggregator.py` builds immutable JSON plus a dashboard.

## Layer 5 — Logging Spine
- `custodian_log_binder.py` writes append-only audit lines to `logs/custodian.log`.
- `genesis_trace.py` captures deterministic traces for replay.

## Layer 6 — Router
- `mcp_governor_router.py` dynamically imports the requested governor runner and executes it via a single invocation surface.

## Layer 7 — Workflows
- GitHub Actions pipelines:
  - `.github/workflows/activ8-governor-sweep.yml`
  - `.github/workflows/lma-governor-sweep.yml`
  - `.github/workflows/personal-governor-sweep.yml`
  - `.github/workflows/governor-watchdog.yml`
  - `.github/workflows/governor-evidence-aggregation.yml`
  - `.github/workflows/governor-failover.yml`
- All workflows pin `ubuntu-22.04`, `actions/checkout@v4.1.0`, and `actions/setup-python@v4.7.0` with pip caching wired to `charter_requirements.txt`.

## Layer 8 — Operations
### Local Commands
```bash
PAT_ACTIV8_AI=<token> python activ8_governor.py
PAT_LMA=<token> python lma_governor.py
PAT_PERSONAL=<token> python personal_governor.py
PAT_ACTIV8_AI=<token> PAT_LMA=<token> PAT_PERSONAL=<token> python resilient_governor_runner.py
python watchdog.py
python governor_evidence_aggregator.py
```

### Invocation Phrase
- “Charter On — Execute Meta Mega Codex.”
- “Run Governors — Activ8 AI, LMAOS, PERSONAL — Charter Standard Execution.”

## Evidence & Dashboards
- Raw evidence lives in `evidence/*.json` with an aggregated view at `evidence/governor_evidence.json`.
- The Markdown dashboard is published to `dashboard/governor_dashboard.md`.
- Operational state is tracked via `state/governor_state.json` for watchdog and failover routines.
