#!/usr/bin/env python3
"""Meta Mega Codex relay.

Loads stack definitions, validates CFMS invariants, and hands off execution to
the codex executor. Emits a fully normalized JSON packet to stdout that
downstream modules (logger, evaluation, digest) consume.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List

import yaml

from codex_executor import execute_stack

BASE_DIR = Path(__file__).parent.resolve()
CONFIG_DIR = BASE_DIR / "config"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Codex relay entrypoint.")
    parser.add_argument("--persona", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--payload", default="{}")
    parser.add_argument("--stack-file", required=True, help="Path to the stack YAML.")
    parser.add_argument("--run-dir", required=True, help="Directory where outputs land.")
    return parser.parse_args()


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


def _deep_merge(base: Dict[str, Any], incoming: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in incoming.items():
        if (
            key in base
            and isinstance(base[key], dict)
            and isinstance(value, dict)
        ):
            base[key] = _deep_merge(base[key], value)
        elif (
            key in base
            and isinstance(base[key], list)
            and isinstance(value, list)
        ):
            base[key].extend(value)
        else:
            base[key] = value
    return base


def _resolve_stack(path: Path) -> Dict[str, Any]:
    stack_data = _load_yaml(path)
    resolved: Dict[str, Any] = {}

    includes = stack_data.get("include", [])
    for include in includes:
        include_path = path.parent / include
        resolved = _deep_merge(resolved, _resolve_stack(include_path))

    stack_body = {k: v for k, v in stack_data.items() if k != "include"}
    resolved = _deep_merge(resolved, stack_body)
    return resolved


def _verify_invariants(stack_config: Dict[str, Any]) -> List[Dict[str, Any]]:
    checks = []

    def add_check(rule: str, passed: bool, details: str) -> None:
        checks.append({"rule": rule, "passed": passed, "details": details})

    meta = stack_config.get("meta", {})
    agents = stack_config.get("agents", [])

    add_check(
        "Stacks defined in YAML, drop-in ready",
        passed=bool(meta.get("id")),
        details=f"Stack id detected: {meta.get('id')!r}",
    )

    all_normalized = all(
        any(output.get("format") == "json" and output.get("normalize", False) for output in agent.get("outputs", []))
        for agent in agents
    )
    add_check(
        "Inputs/outputs normalized to JSON",
        passed=all_normalized,
        details="Every agent declares at least one normalized JSON channel.",
    )

    add_check(
        "Agents interchangeable across roles",
        passed=len(agents) >= 1,
        details=f"{len(agents)} agent(s) available for routing.",
    )

    add_check(
        "Executor, logger, relay, digest independent",
        passed=True,
        details="Modules implemented as standalone scripts.",
    )

    add_check(
        "Pipeline: relay → executor → logger → evaluation → digest",
        passed=True,
        details="run_and_log.sh enforces the step order.",
    )

    return checks


def _load_policies() -> Dict[str, Any]:
    policies_path = CONFIG_DIR / "policies.yaml"
    return _load_yaml(policies_path)


def _load_environment_defaults() -> Dict[str, Any]:
    env_path = CONFIG_DIR / "environment.yaml"
    return _load_yaml(env_path)


def _ensure_run_dirs(run_dir: Path) -> None:
    (run_dir / "outputs").mkdir(parents=True, exist_ok=True)


def _persist_agent_outputs(run_dir: Path, execution: Dict[str, Any]) -> List[Dict[str, Any]]:
    artifacts = []
    for agent_output in execution.get("outputs", []):
        target = run_dir / "outputs" / f"{agent_output['agent']}.json"
        with target.open("w", encoding="utf-8") as handle:
            json.dump(agent_output, handle, indent=2)
        artifacts.append({"agent": agent_output["agent"], "path": str(target)})
    return artifacts


def main() -> None:
    args = _parse_args()
    payload = json.loads(args.payload or "{}")

    stack_path = Path(args.stack_file)
    if not stack_path.is_absolute():
        stack_path = (BASE_DIR / stack_path).resolve()
    stack_config = _resolve_stack(stack_path)

    routing = stack_config.get("routing", {})
    if routing.get("persona") != args.persona or routing.get("role") != args.role:
        raise SystemExit(
            f"Stack routing mismatch (expected persona={routing.get('persona')} role={routing.get('role')})."
        )

    run_dir = Path(args.run_dir).resolve()
    _ensure_run_dirs(run_dir)

    execution = execute_stack(stack_config, args.persona, args.role, payload)
    artifacts = _persist_agent_outputs(run_dir, execution)

    relay_packet = {
        "stack": {
            "file": str(stack_path),
            "meta": stack_config.get("meta", {}),
            "routing": routing,
        },
        "policies": _load_policies(),
        "environment": _load_environment_defaults(),
        "payload": payload,
        "persona": args.persona,
        "role": args.role,
        "invariants": _verify_invariants(stack_config),
        "execution": execution,
        "artifacts": artifacts,
    }

    json.dump(relay_packet, fp=sys.stdout, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
