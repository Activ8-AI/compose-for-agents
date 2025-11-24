"""Weekly digest generator for Codex runs."""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List


def _load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    content = path.read_text(encoding="utf-8").strip()
    if not content:
        return {}
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return {}


def _collect_run_dirs(runs_dir: Path) -> List[Path]:
    if not runs_dir.exists():
        return []
    # Runs are stored as runs/YYYY-MM-DD/HHMMSS
    run_paths = [p for p in runs_dir.glob("*/*") if p.is_dir()]
    return sorted(run_paths)


def _parse_timestamp_from_path(path: Path) -> datetime:
    try:
        date_part = path.parent.name
        time_part = path.name
        combined = f"{date_part}T{time_part}"  # e.g. 2025-01-01T235959
        return datetime.strptime(combined, "%Y-%m-%dT%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)


def _score_run(relay_manifest: Dict[str, Any]) -> Dict[str, float]:
    invariants = relay_manifest.get("invariants", [])
    all_invariants_pass = all(item.get("passes", False) for item in invariants) if invariants else True
    agent_count = len(relay_manifest.get("execution", {}).get("agents", []))
    payload_density = len(json.dumps(relay_manifest.get("payload", {})))

    return {
        "charter_alignment": 1.0 if all_invariants_pass else 0.6,
        "clarity": min(1.0, 0.5 + agent_count * 0.2),
        "actionability": min(1.0, 0.4 + payload_density / 500.0),
        "compliance": 1.0 if relay_manifest.get("policies") else 0.8,
    }


def _aggregate_scores(per_run: List[Dict[str, Any]]) -> Dict[str, float]:
    if not per_run:
        return {}
    totals: Dict[str, float] = {}
    counts: Dict[str, int] = {}
    for run in per_run:
        for key, value in run["scores"].items():
            totals[key] = totals.get(key, 0.0) + value
            counts[key] = counts.get(key, 0) + 1
    return {key: round(totals[key] / counts[key], 3) for key in totals}


def build_digest(args: argparse.Namespace) -> Dict[str, Any]:
    vault_dir = Path(args.vault_dir)
    runs_dir = vault_dir / "runs"
    window_start = datetime.now(tz=timezone.utc) - timedelta(days=args.window_days)

    per_run_entries = []
    for run_dir in _collect_run_dirs(runs_dir):
        run_ts = _parse_timestamp_from_path(run_dir)
        if run_ts < window_start:
            continue
        relay_manifest = _load_json(run_dir / "relay.json")
        if not relay_manifest:
            continue
        scores = _score_run(relay_manifest)
        per_run_entries.append(
            {
                "run_path": str(run_dir.relative_to(vault_dir)),
                "timestamp": run_ts.isoformat(),
                "stack_id": relay_manifest.get("stack", {}).get("id"),
                "persona": relay_manifest.get("meta", {}).get("persona"),
                "scores": scores,
            }
        )

    digest = {
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "window_days": args.window_days,
        "runs_considered": len(per_run_entries),
        "average_scores": _aggregate_scores(per_run_entries),
        "runs": per_run_entries,
    }

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(digest, indent=2, sort_keys=True), encoding="utf-8")

    return digest


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Generate a digest report for recent Codex runs")
    parser.add_argument("--vault-dir", default="PreservationVault")
    parser.add_argument("--window-days", type=int, default=7)
    parser.add_argument("--output")
    args = parser.parse_args()

    digest = build_digest(args)
    print(json.dumps(digest, indent=2, sort_keys=True))


if __name__ == "__main__":
    _cli()
