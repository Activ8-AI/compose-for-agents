from __future__ import annotations

import json
from datetime import datetime, timezone, timedelta
from typing import Dict, List

from charter_core import load_policy_bundle, load_state_snapshot, TIMESTAMP_FORMAT
from custodian_log_binder import CustodianLogBinder

WATCHDOG_GOVERNORS = ["activ8", "lma", "personal"]


def _parse_timestamp(value: str) -> datetime:
    return datetime.strptime(value, TIMESTAMP_FORMAT).replace(tzinfo=timezone.utc)


def run_watchdog() -> Dict[str, List[str]]:
    snapshot = load_state_snapshot()
    custodian = CustodianLogBinder()

    stale_governors: List[str] = []
    missing_governors: List[str] = []

    now = datetime.now(timezone.utc)
    for governor in WATCHDOG_GOVERNORS:
        bundle = load_policy_bundle(governor)
        watchdog_cfg = bundle.domain_policy.get("watchdogs", [{}])[0]
        max_minutes = watchdog_cfg.get("max_staleness_minutes", 60)
        max_delta = timedelta(minutes=max_minutes)

        governor_state = snapshot.get("governors", {}).get(governor)
        if not governor_state:
            missing_governors.append(governor)
            continue

        last_run = governor_state.get("last_run_utc")
        if not last_run:
            missing_governors.append(governor)
            continue

        age = now - _parse_timestamp(last_run)
        if age > max_delta:
            stale_governors.append(governor)

    status = {
        "stale": stale_governors,
        "missing": missing_governors,
    }

    custodian.append(
        "watchdog",
        {
            "action": "health_check",
            "status": "degraded" if (stale_governors or missing_governors) else "healthy",
            "details": status,
        },
    )

    if stale_governors or missing_governors:
        raise RuntimeError(
            f"Watchdog detected issues. Stale: {stale_governors}, Missing: {missing_governors}"
        )

    return status


if __name__ == "__main__":
    result = run_watchdog()
    print(json.dumps(result, indent=2))
