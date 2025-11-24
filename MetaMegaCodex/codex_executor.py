"""Codex executor module.

Responsible for taking a resolved stack definition plus a normalized
payload and generating deterministic, JSON-normalized agent outputs. The
implementation is intentionally lightweight so it can run inside CI
pipelines without external dependencies beyond PyYAML.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List

import yaml


def _normalize_json(data: Any) -> Any:
    """Return data that round-trips through JSON for deterministic output."""
    return json.loads(json.dumps(data, sort_keys=True))


@dataclass
class ExecutionResult:
    stack_id: str
    stack_version: str
    persona: str
    role: str
    agents: List[Dict[str, Any]]
    payload: Dict[str, Any]
    provenance: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "stack_id": self.stack_id,
            "stack_version": self.stack_version,
            "persona": self.persona,
            "role": self.role,
            "payload": self.payload,
            "agents": self.agents,
            "provenance": self.provenance,
        }


class CodexExecutor:
    """Executes a stack deterministically using simple persona heuristics."""

    def __init__(self, policies: Dict[str, Any] | None = None) -> None:
        self.policies = policies or {}

    def run(self, stack: Dict[str, Any], payload: Dict[str, Any], *, persona: str, role: str) -> ExecutionResult:
        normalized_payload = _normalize_json(payload)
        agents_cfg = stack.get("agents", [])
        agents_output = [self._run_agent(agent_cfg, normalized_payload, persona, role) for agent_cfg in agents_cfg]

        provenance_seed = json.dumps(
            {
                "stack": stack.get("meta", {}).get("id", "unknown"),
                "payload": normalized_payload,
                "persona": persona,
                "role": role,
            },
            sort_keys=True,
        ).encode("utf-8")
        provenance_hash = hashlib.sha256(provenance_seed).hexdigest()

        provenance = {
            "generated_at": datetime.now(tz=timezone.utc).isoformat(),
            "normalization": "json",
            "policies": self.policies.get("executor", []),
            "hash": provenance_hash,
        }

        meta = stack.get("meta", {})
        return ExecutionResult(
            stack_id=meta.get("id", "unknown"),
            stack_version=meta.get("version", "0.0.0"),
            persona=persona,
            role=role,
            agents=agents_output,
            payload=normalized_payload,
            provenance=provenance,
        )

    def _run_agent(self, agent_cfg: Dict[str, Any], payload: Dict[str, Any], persona: str, role: str) -> Dict[str, Any]:
        agent_seed = json.dumps({"agent": agent_cfg.get("name"), "payload": payload}, sort_keys=True).encode("utf-8")
        payload_digest = hashlib.sha256(agent_seed).hexdigest()
        summary = (
            f"{agent_cfg.get('name')} ({agent_cfg.get('model')}) processed persona '{persona}' "
            f"in role '{role}' using payload digest {payload_digest[:8]}"
        )
        return {
            "name": agent_cfg.get("name"),
            "model": agent_cfg.get("model"),
            "status": "completed",
            "summary": summary,
            "payload_digest": payload_digest,
            "echo": payload,
            "interchangeable": True,
        }


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Run the Codex executor manually")
    parser.add_argument("--stack-file", required=True)
    parser.add_argument("--payload", default="{}", help="JSON payload for the stack")
    parser.add_argument("--persona", required=True)
    parser.add_argument("--role", required=True)
    args = parser.parse_args()

    with open(args.stack_file, "r", encoding="utf-8") as handle:
        stack = yaml.safe_load(handle)

    payload = json.loads(args.payload)
    executor = CodexExecutor()
    result = executor.run(stack, payload, persona=args.persona, role=args.role)
    print(json.dumps(result.to_dict(), indent=2, sort_keys=True))


if __name__ == "__main__":
    _cli()
