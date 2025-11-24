#!/usr/bin/env bash
set -euo pipefail

STACK_PATH="${1:?Usage: ./run_and_log.sh stacks/<stack>.yaml <persona> <role> [payload-json]}"
PERSONA="${2:?Persona required}"
ROLE="${3:?Role required}"
DEFAULT_PAYLOAD="{}"
PAYLOAD="${4:-$DEFAULT_PAYLOAD}"

TS="$(date -u +%Y-%m-%d/%H%M%S)"
RUN_DIR="PreservationVault/runs/${TS}"
mkdir -p "${RUN_DIR}/outputs"

python3 codex_relay.py \
  --persona "${PERSONA}" \
  --role "${ROLE}" \
  --payload "${PAYLOAD}" \
  --stacks-dir "$(dirname "${STACK_PATH}")" \
  --stack-file "${STACK_PATH}" \
  --config-dir "config" \
  --run-dir "${RUN_DIR}" \
  > "${RUN_DIR}/relay.json"

python3 codex_logger.py --run-dir "${RUN_DIR}" --config-dir "config" --record-env
cp codex_evaluation.json "${RUN_DIR}/evaluation.json"
python3 codex_digest_report.py --vault-dir PreservationVault --output PreservationVault/digest/latest.json >/dev/null

if [ -d "PreservationVault/.git" ]; then
  git -C PreservationVault add .
  git -C PreservationVault commit -m "Run ${TS}" || true
fi
