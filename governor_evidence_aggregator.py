from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from charter_core.paths import DASHBOARD_DIR, EVIDENCE_DIR
from custodian_log_binder import CustodianLogBinder

AGGREGATED_JSON = EVIDENCE_DIR / "governor_evidence.json"
DASHBOARD_MD = DASHBOARD_DIR / "governor_dashboard.md"


def _collect_evidence_files() -> List[Path]:
    return sorted(EVIDENCE_DIR.glob("*.json"))


def _summarize(record: Dict) -> Dict[str, str]:
    assessment = record.get("assessment", {})
    return {
        "governor": assessment.get("governor"),
        "timestamp_utc": assessment.get("timestamp_utc"),
        "integrity_hash": record.get("integrity_hash"),
        "bundle_version": assessment.get("policy_bundle_version"),
    }


def aggregate() -> Dict[str, List[Dict[str, str]]]:
    custodian = CustodianLogBinder()
    summaries: List[Dict[str, str]] = []

    for evidence_file in _collect_evidence_files():
        if evidence_file.name == AGGREGATED_JSON.name:
            continue
        with evidence_file.open("r", encoding="utf-8") as handle:
            record = json.load(handle)
        summaries.append(_summarize(record))

    payload = {"entries": summaries}
    with AGGREGATED_JSON.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write("\n")

    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Governor Evidence Dashboard",
        "",
        "| Governor | Timestamp (UTC) | Bundle Version | Integrity Hash |",
        "| --- | --- | --- | --- |",
    ]
    for entry in summaries:
        lines.append(
            f"| {entry['governor']} | {entry['timestamp_utc']} | {entry['bundle_version']} | `{entry['integrity_hash']}` |"
        )
    DASHBOARD_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")

    custodian.append(
        "aggregator",
        {
            "action": "aggregate_evidence",
            "status": "success",
            "entries": len(summaries),
            "dashboard": str(DASHBOARD_MD.relative_to(DASHBOARD_MD.parent.parent)),
        },
    )

    return payload


if __name__ == "__main__":
    result = aggregate()
    print(json.dumps(result, indent=2))
