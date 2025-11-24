#!/usr/bin/env python3
"""Generate weekly digests from PreservationVault runs."""

from __future__ import annotations

import argparse
import json
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Produce weekly codex digests.")
    parser.add_argument("--vault", default="PreservationVault")
    parser.add_argument("--window-days", type=int, default=7)
    return parser.parse_args()


def _iter_run_dirs(vault: Path) -> List[Path]:
    runs_root = vault / "runs"
    if not runs_root.exists():
        return []
    return sorted(runs_root.glob("*/*"))


def _parse_run_timestamp(run_path: Path) -> datetime | None:
    try:
        day = run_path.parent.name
        time_str = run_path.name
        return datetime.strptime(f"{day}/{time_str}", "%Y-%m-%d/%H%M%S").replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _load_evaluation(run_path: Path) -> Dict[str, Any] | None:
    evaluation_file = run_path / "evaluation_results.json"
    if not evaluation_file.exists():
        return None
    with evaluation_file.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _aggregate(runs: List[Dict[str, Any]]) -> Dict[str, float]:
    if not runs:
        return {}
    totals: Dict[str, float] = defaultdict(float)
    for entry in runs:
        for key, value in entry["evaluation"]["criteria"].items():
            totals[key] += value
    count = len(runs)
    return {key: round(value / count, 4) for key, value in totals.items()}


def _write_digest(vault: Path, week_key: str, entries: List[Dict[str, Any]]) -> None:
    digest_dir = vault / "digests"
    digest_dir.mkdir(parents=True, exist_ok=True)
    digest_path = digest_dir / f"{week_key}.json"
    digest_data = {
        "week": week_key,
        "generated_at": datetime.now(tz=timezone.utc).isoformat(),
        "run_count": len(entries),
        "average_scores": _aggregate(entries),
        "runs": entries,
    }
    with digest_path.open("w", encoding="utf-8") as handle:
        json.dump(digest_data, handle, indent=2)


def main() -> None:
    args = _parse_args()
    vault = Path(args.vault).resolve()
    cutoff = datetime.now(tz=timezone.utc) - timedelta(days=args.window_days)

    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for run_path in _iter_run_dirs(vault):
        run_ts = _parse_run_timestamp(run_path)
        if run_ts is None or run_ts < cutoff:
            continue
        evaluation = _load_evaluation(run_path)
        if not evaluation:
            continue
        iso = run_ts.isocalendar()
        week_key = f"{iso.year}-W{iso.week:02d}"
        grouped[week_key].append(
            {
                "run_id": f"{run_path.parent.name}/{run_path.name}",
                "timestamp": run_ts.isoformat(),
                "evaluation": evaluation,
                "overall_score": evaluation.get("overall_score"),
            }
        )

    for week_key, entries in grouped.items():
        _write_digest(vault, week_key, entries)


if __name__ == "__main__":
    main()
