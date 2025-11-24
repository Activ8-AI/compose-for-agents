from __future__ import annotations

import json
from charter_core.governance import execute_governor

GOVERNOR_ID = "lma"
TOKEN_ENV = "PAT_LMA"
SWEEP_LABEL = "lma-governor-sweep"


def run() -> dict:
    return execute_governor(GOVERNOR_ID, TOKEN_ENV, sweep_label=SWEEP_LABEL)


if __name__ == "__main__":
    output = run()
    print(json.dumps(output, indent=2))
