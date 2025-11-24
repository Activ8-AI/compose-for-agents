"""Codex logger module.

Reads the relay manifest and records execution metadata plus environment
information in the PreservationVault run directory.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import yaml


def _load_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _load_policies(config_dir: Path) -> Dict[str, Any]:
    data = _load_yaml(config_dir / "policies.yaml")
    return data.get("policies", data)


def _load_environment(config_dir: Path) -> Dict[str, Any]:
    return _load_yaml(config_dir / "environment.yaml")


def _capture_runtime_snapshot() -> Dict[str, Any]:
    return {
        "python_version": platform.python_version(),
        "system": platform.system(),
        "release": platform.release(),
        "machine": platform.machine(),
    }


def log_run(args: argparse.Namespace) -> None:
    run_dir = Path(args.run_dir)
    if not run_dir.exists():
        raise FileNotFoundError(f"Run directory {run_dir} does not exist")
    relay_file = run_dir / args.relay_artifact
    relay_manifest = json.loads(relay_file.read_text(encoding="utf-8"))
    relay_raw = json.dumps(relay_manifest, sort_keys=True).encode("utf-8")

    config_dir = Path(args.config_dir)
    policies = _load_policies(config_dir)
    environment_cfg = _load_environment(config_dir)

    log_entry = {
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        "relay_artifact": args.relay_artifact,
        "relay_sha": hashlib.sha256(relay_raw).hexdigest(),
        "policies": policies.get("logger", []),
        "environment": environment_cfg.get("environment", {}),
        "stack_id": relay_manifest.get("stack", {}).get("id"),
        "persona": relay_manifest.get("meta", {}).get("persona"),
        "role": relay_manifest.get("meta", {}).get("role"),
    }

    if args.record_env:
        log_entry["runtime"] = _capture_runtime_snapshot()

    log_path = run_dir / "log.json"
    if log_path.exists():
        history = json.loads(log_path.read_text(encoding="utf-8"))
        if not isinstance(history, list):
            history = [history]
    else:
        history = []
    history.append(log_entry)
    log_path.write_text(json.dumps(history, indent=2, sort_keys=True), encoding="utf-8")


def _cli() -> None:
    parser = argparse.ArgumentParser(description="Record Codex relay logs")
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--config-dir", default="config")
    parser.add_argument("--relay-artifact", default="relay.json")
    parser.add_argument("--record-env", action="store_true")
    args = parser.parse_args()
    log_run(args)


if __name__ == "__main__":
    _cli()
