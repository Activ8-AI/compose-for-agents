#!/usr/bin/env python3
"""Codex logger and evaluation stage."""

from __future__ import annotations

import argparse
import json
import platform
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict


def _iso_timestamp() -> str:
    return datetime.now(tz=timezone.utc).isoformat()


def _load_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _gather_environment() -> Dict[str, Any]:
    env = {
        "hostname": platform.node(),
        "platform": platform.platform(),
        "python": platform.python_version(),
    }
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            capture_output=True,
            text=True,
            check=True,
            cwd=Path(".").resolve(),
        )
        env["git_head"] = result.stdout.strip()
    except subprocess.CalledProcessError:
        env["git_head"] = "unknown"
    return env


def _load_evaluation_schema(path: Path) -> Dict[str, Any]:
    return _load_json(path)


def _evaluate(relay_packet: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    execution = relay_packet.get("execution", {})
    outputs = execution.get("outputs", [])
    insights = sum(len(o.get("content", {}).get("insights", [])) for o in outputs)
    actions = sum(len(o.get("content", {}).get("actions", [])) for o in outputs)
    invariants = relay_packet.get("invariants", [])
    invariants_pass_rate = (
        sum(1 for item in invariants if item.get("passed")) / max(1, len(invariants))
    )

    scores: Dict[str, float] = {
        "charter_alignment": 1.0
        if relay_packet.get("persona") == execution.get("persona")
        else 0.0,
        "clarity": min(1.0, 0.5 + 0.05 * insights),
        "actionability": min(1.0, 0.4 + 0.08 * actions),
        "compliance": round(invariants_pass_rate, 4),
    }

    weights = {c["key"]: c["weight"] for c in schema.get("criteria", [])}
    overall = sum(scores[key] * weights.get(key, 0) for key in scores)

    return {
        "generated_at": _iso_timestamp(),
        "criteria": scores,
        "overall_score": round(overall, 4),
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Codex logging + evaluation stage.")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument(
        "--evaluation-schema",
        default="codex_evaluation.json",
        help="Path to the evaluation schema JSON.",
    )
    parser.add_argument("--record-env", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    run_dir = Path(args.run_dir).resolve()
    relay_path = run_dir / "relay.json"
    relay_packet = _load_json(relay_path)
    schema = _load_evaluation_schema(Path(args.evaluation_schema))

    log_entry = {
        "logged_at": _iso_timestamp(),
        "persona": relay_packet.get("persona"),
        "role": relay_packet.get("role"),
        "stack": relay_packet.get("stack"),
        "artifacts": relay_packet.get("artifacts", []),
    }
    if args.record_env:
        log_entry["environment"] = _gather_environment()

    log_path = run_dir / "logger.json"
    with log_path.open("w", encoding="utf-8") as handle:
        json.dump(log_entry, handle, indent=2)

    evaluation_results = _evaluate(relay_packet, schema)
    evaluation_path = run_dir / "evaluation_results.json"
    with evaluation_path.open("w", encoding="utf-8") as handle:
        json.dump(evaluation_results, handle, indent=2)

    outputs_dir = run_dir / "outputs"
    outputs_dir.mkdir(exist_ok=True)
    with (outputs_dir / "evaluation_results.json").open("w", encoding="utf-8") as handle:
        json.dump(evaluation_results, handle, indent=2)


if __name__ == "__main__":
    main()
