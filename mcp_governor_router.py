from __future__ import annotations

import importlib
import json
from typing import Callable, Dict

ROUTES: Dict[str, str] = {
    "activ8": "activ8_governor",
    "lma": "lma_governor",
    "personal": "personal_governor",
}


def _resolve_runner(governor: str) -> Callable[[], dict]:
    module_name = ROUTES.get(governor.lower())
    if not module_name:
        raise ValueError(f"Unsupported governor '{governor}'.")
    module = importlib.import_module(module_name)
    if not hasattr(module, "run"):
        raise AttributeError(f"Module '{module_name}' is missing a run() function.")
    return getattr(module, "run")


def route(governor: str) -> dict:
    runner = _resolve_runner(governor)
    return runner()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Route to a specific governor runner.")
    parser.add_argument("--governor", required=True, choices=sorted(ROUTES.keys()))
    args = parser.parse_args()

    output = route(args.governor)
    print(json.dumps(output, indent=2))
