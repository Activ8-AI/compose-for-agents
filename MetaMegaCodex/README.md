# Codex Runtime — Meta Mega Codex

A lightweight pipeline that enforces CFMS (Composable, Fungible, Modular,
Stackable) invariants for persona-oriented advisory runs. The runtime is
split across clearly scoped modules: relay, executor, logger, and digest
in addition to stack/policy configuration.

## Quickstart
1. `python3 -m venv .venv && source .venv/bin/activate`
2. `pip install -r requirements.txt`
3. `mkdir -p PreservationVault && touch PreservationVault/.gitkeep`
4. `git init PreservationVault && git -C PreservationVault commit --allow-empty -m "Vault init"`
5. `./run_and_log.sh stacks/kim_watson_stack.yaml kim advisor '{"topic":"charter"}'`

Each run emits artifacts under `PreservationVault/runs/<date>/<time>` and
updates a rolling digest at `PreservationVault/digest/latest.json`.

## Modules
- `codex_relay.py`: Resolves stacks (with include support), enforces
  invariants, calls the executor, and writes a manifest.
- `codex_executor.py`: Normalizes inputs/outputs, simulates agents, and
  returns deterministic JSON for interchangeability.
- `codex_logger.py`: Records relay metadata, policy scopes, and optional
  runtime fingerprints.
- `codex_digest_report.py`: Aggregates run scores over a configurable
  window (default 7 days) for the weekly digest requirement.

## Configuration
- `stacks/`: Persona stacks plus `_cfms_invariants.yaml` for shared
  enforcement expectations.
- `config/policies.yaml`: Module-specific policy scopes.
- `config/environment.yaml`: Base environment descriptors embedded in
  logs.

## Automation
- `run_and_log.sh`: Canonical pipeline entrypoint used both locally and
  by CI.
- `codex_gh_action.yml`: Example GitHub Actions workflow that executes
  on a 15-minute cron and pushes Vault updates upstream.
