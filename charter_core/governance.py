from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from typing import Any, Dict

from custodian_log_binder import CustodianLogBinder
from genesis_trace import GenesisTracer

from .paths import EVIDENCE_DIR, TIMESTAMP_FORMAT
from .policies import load_policy_bundle
from .state import load_state_snapshot, persist_state_snapshot

custodian_logger = CustodianLogBinder()
genesis_tracer = GenesisTracer()


def _hash_payload(payload: Dict[str, Any]) -> str:
    serialized = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def execute_governor(governor: str, token_env: str, sweep_label: str | None = None) -> Dict[str, Any]:
    token = os.getenv(token_env)
    if not token:
        raise EnvironmentError(
            f"Environment variable '{token_env}' required for {governor} governor."
        )

    bundle = load_policy_bundle(governor)
    timestamp = datetime.now(timezone.utc).strftime(TIMESTAMP_FORMAT)

    assessment = {
        "governor": governor,
        "timestamp_utc": timestamp,
        "policy_bundle_version": bundle.version,
        "sovereign_boundaries": bundle.domain_policy.get("sovereign_boundaries", []),
        "copilot_controls": bundle.copilot_policy.get("controls", []),
        "watchdogs": bundle.domain_policy.get("watchdogs", []),
        "determinism": bundle.domain_policy.get("determinism", {}),
        "sweep_label": sweep_label or "ad-hoc",
    }

    evidence = {
        "assessment": assessment,
        "domain_policy": bundle.domain_policy,
        "copilot_policy": bundle.copilot_policy,
    }
    integrity_hash = _hash_payload(evidence)
    evidence["integrity_hash"] = integrity_hash

    evidence_path = EVIDENCE_DIR / f"{governor}_{timestamp}.json"
    with evidence_path.open("w", encoding="utf-8") as handle:
        json.dump(evidence, handle, indent=2, sort_keys=True)
        handle.write("\n")

    custodian_logger.append(
        governor,
        {
            "action": "governor_sweep",
            "status": "success",
            "evidence_path": str(evidence_path.relative_to(EVIDENCE_DIR.parent)),
            "integrity_hash": integrity_hash,
        },
    )
    genesis_tracer.trace(
        governor,
        event="policy_bundle_loaded",
        payload={"bundle_version": bundle.version},
    )

    snapshot = load_state_snapshot()
    snapshot.setdefault("governors", {})
    snapshot["governors"][governor] = {
        "last_run_utc": timestamp,
        "last_integrity_hash": integrity_hash,
        "sweep_label": sweep_label or "ad-hoc",
    }
    persist_state_snapshot(snapshot)

    return {
        "governor": governor,
        "sweep_label": sweep_label or "ad-hoc",
        "timestamp_utc": timestamp,
        "evidence_path": str(evidence_path),
        "integrity_hash": integrity_hash,
    }
