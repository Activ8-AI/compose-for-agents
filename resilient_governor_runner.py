from __future__ import annotations

import json
import time
from typing import Dict, List, Tuple

from charter_core.governance import execute_governor

GOVERNOR_MATRIX: List[Tuple[str, str, str]] = [
    ("activ8", "PAT_ACTIV8_AI", "resilient-failover"),
    ("lma", "PAT_LMA", "resilient-failover"),
    ("personal", "PAT_PERSONAL", "resilient-failover"),
]

MAX_ATTEMPTS = 3
BASE_DELAY_SECONDS = 5


def _run_with_backoff(governor: str, token_env: str, sweep_label: str) -> Dict[str, str]:
    attempt = 0
    while attempt < MAX_ATTEMPTS:
        try:
            return execute_governor(governor, token_env, sweep_label=sweep_label)
        except Exception as _exc:  # noqa: BLE001 - intentional catch for resilience
            attempt += 1
            if attempt >= MAX_ATTEMPTS:
                raise
            delay = BASE_DELAY_SECONDS * attempt
            time.sleep(delay)


def run_all() -> List[Dict[str, str]]:
    results = []
    for governor, token_env, sweep_label in GOVERNOR_MATRIX:
        results.append(_run_with_backoff(governor, token_env, sweep_label))
    return results


if __name__ == "__main__":
    outputs = run_all()
    print(json.dumps(outputs, indent=2))
