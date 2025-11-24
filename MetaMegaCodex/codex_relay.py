"""Codex relay orchestrator.

Loads persona stacks, enforces CFMS invariants, invokes the executor,
then emits a normalized relay manifest to STDOUT.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from codex_executor import CodexExecutor

RELAY_VERSION = "1.0.0"


def _load_yaml(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    return data


def _deep_merge(target: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(target.get(key), dict):
            target[key] = _deep_merge(dict(target[key]), value)
        else:
            target[key] = value
    return target


class StackResolver:
    def __init__(self, stacks_dir: Path):
        self.stacks_dir = stacks_dir

    def find_by_route(self, persona: str, role: str) -> Path:
        for path in self.stacks_dir.glob("*.yaml"):
            data = _load_yaml(path)
            route = data.get("routing", {})
            if route.get("persona") == persona and route.get("role") == role:
                return path
        raise FileNotFoundError(f"No stack matches persona={persona} role={role}")

    def load(self, stack_path: Path) -> Dict[str, Any]:
        stack_data = _load_yaml(stack_path)
        includes = stack_data.get("include", [])
        resolved: Dict[str, Any] = {}
        for include in includes:
            include_path = self.stacks_dir / include
            include_data = _load_yaml(include_path)
            resolved = _deep_merge(resolved, include_data)
        stack_without_include = dict(stack_data)
        stack_without_include.pop("include", None)
        resolved = _deep_merge(resolved, stack_without_include)
        return resolved


def _load_policies(config_dir: Path) -> Dict[str, Any]:
    policies_path = config_dir / "policies.yaml"
    if not policies_path.exists():
        return {}
    data = _load_yaml(policies_path)
    return data.get("policies", data)


def _evaluate_invariants(stack: Dict[str, Any]) -> List[Dict[str, Any]]:
    invariants = stack.get("cfms_invariants", {})
    evaluation = []
    for dimension, payload in invariants.items():
        enforcement = payload.get("enforcement", [])
        evaluation.append(
            {
                "dimension": dimension,
                "passes": bool(enforcement),
                "enforcement": enforcement,
            }
        )
    return evaluation


def _normalize_payload(payload: str) -> Dict[str, Any]:
    data = json.loads(payload or "{}")
    if not isinstance(data, dict):
        raise ValueError("Payload must be a JSON object")
    return json.loads(json.dumps(data, sort_keys=True))


def relay(args: argparse.Namespace) -> Dict[str, Any]:
    stacks_dir = Path(args.stacks_dir)
    config_dir = Path(args.config_dir)
    run_dir = Path(args.run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    outputs_dir = run_dir / "outputs"
    outputs_dir.mkdir(parents=True, exist_ok=True)

    resolver = StackResolver(stacks_dir)
    if args.stack_file:
        stack_path = Path(args.stack_file)
    elif args.stack_id:
        candidate = stacks_dir / f"{args.stack_id}.yaml"
        if not candidate.exists():
            raise FileNotFoundError(f"Stack file {candidate} not found")
        stack_path = candidate
    else:
        stack_path = resolver.find_by_route(args.persona, args.role)

    resolved_stack = resolver.load(stack_path)
    policies = _load_policies(config_dir)

    payload = _normalize_payload(args.payload)

    executor = CodexExecutor(policies=policies)
    execution = executor.run(resolved_stack, payload, persona=args.persona, role=args.role)

    relay_manifest = {
        "meta": {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "persona": args.persona,
            "role": args.role,
            "relay_version": RELAY_VERSION,
            "run_dir": str(run_dir),
        },
        "stack": {
            "id": execution.stack_id,
            "version": execution.stack_version,
            "purpose": resolved_stack.get("meta", {}).get("purpose"),
        },
        "policies": policies.get("relay", []),
        "payload": execution.payload,
        "execution": execution.to_dict(),
        "invariants": _evaluate_invariants(resolved_stack),
    }

    # Persist helpful artifacts for downstream modules.
    (outputs_dir / "executor.json").write_text(json.dumps(execution.to_dict(), indent=2, sort_keys=True), encoding="utf-8")
    (run_dir / "stack.resolved.yaml").write_text(yaml.safe_dump(resolved_stack, sort_keys=False), encoding="utf-8")

    return relay_manifest


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Run the Codex relay")
    parser.add_argument("--persona", required=True)
    parser.add_argument("--role", required=True)
    parser.add_argument("--payload", default="{}", help="JSON payload")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--stacks-dir", default="stacks")
    parser.add_argument("--config-dir", default="config")
    parser.add_argument("--stack-id")
    parser.add_argument("--stack-file")
    args = parser.parse_args()

    manifest = relay(args)
    print(json.dumps(manifest, indent=2, sort_keys=True))


if __name__ == "__main__":
    _cli()
