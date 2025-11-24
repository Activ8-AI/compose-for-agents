#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: ./run_and_log.sh stacks/<stack>.yaml [persona] [role] [payload_json]" >&2
  exit 1
fi

STACK_FILE="$1"
PERSONA="${2:-kim}"
ROLE="${3:-advisor}"
PAYLOAD_JSON="${4:-{}}"

TS="$(date -u +%Y-%m-%d/%H%M%S)"
RUN_DIR="PreservationVault/runs/${TS}"
mkdir -p "${RUN_DIR}/outputs"

python3 codex_relay.py \
  --persona "${PERSONA}" \
  --role "${ROLE}" \
  --payload "${PAYLOAD_JSON}" \
  --stack-file "${STACK_FILE}" \
  --run-dir "${RUN_DIR}" > "${RUN_DIR}/relay.json"

python3 codex_logger.py \
  --run-dir "${RUN_DIR}" \
  --evaluation-schema "codex_evaluation.json" \
  --record-env

python3 codex_digest_report.py --vault "PreservationVault" --window-days 7

cp codex_evaluation.json "${RUN_DIR}/evaluation.schema.json"

git -C PreservationVault add .
git -C PreservationVault commit -m "Run ${TS}"
