#!/usr/bin/env bash
# E1 (ADR-008): review the 5 seeded PRs locally with each reviewer arm. Subscription-backed (ADR-014).
#   arms: independent (codex gpt-6-astra, adversarial, issue-only)
#         friendly    (codex gpt-6.1-sol = builder model, neutral prompt, + implementer context)
#         xvendor     (agy Claude Opus 4.6, independent prompt) - cross-vendor independence
# usage: run_e1.sh <tinydb checkout> <python of tinydb venv> <out root> [arm...] [--rep N]
set -euo pipefail
REPO=$1; PY=$2; OUT=$3; shift 3
ARMS=${*:-independent friendly xvendor}
HERE=$(cd "$(dirname "$0")/../.." && pwd)
cd "$HERE/workflow"
for arm in $ARMS; do
  variant=independent; envs=()
  case $arm in
    friendly) variant=friendly ;;
    xvendor)  envs=(AUTOSE_BACKEND_REVIEWER=agy AUTOSE_BACKEND_VERIFIER=agy) ;;
  esac
  for sp in "$HERE"/experiment/seeded_prs/SP*/; do
    id=$(basename "$sp")
    ( env ${envs[@]+"${envs[@]}"} "${AUTOSE_WF_PY:-python3}" -m autose --home "$OUT/$arm" --python "$PY" \
        review-local --pr-dir "$sp" --repo "$REPO" --variant "$variant" > "$OUT/$arm-$id.json" 2> "$OUT/$arm-$id.log" \
      || echo "FAILED $arm $id" >> "$OUT/failures.txt" ) &
  done
  wait
done
echo "E1 done: $OUT"
