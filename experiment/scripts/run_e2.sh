#!/usr/bin/env bash
# E2 (ADR-001): stages 3-4 from frozen spec+design, split (Developer+Tester) vs single (Builder).
# usage: run_e2.sh <clean tinydb repo> <python of tinydb venv> <frozen root with issue-N/{spec,design}.json> <out root> [issues...]
set -euo pipefail
REPO=$1; PY=$2; FROZEN=$3; OUT=$4; shift 4
ISSUES=${*:-1 2 3 4 5}
HERE=$(cd "$(dirname "$0")/../.." && pwd)
mkdir -p "$OUT"
for n in $ISSUES; do
  for v in split single; do
    wt="$OUT/wt-$n-$v"
    git -C "$REPO" worktree remove --force "$wt" 2>/dev/null || true
    git -C "$REPO" worktree add -q --detach "$wt" HEAD
    ( cd "$HERE/workflow" && "${AUTOSE_WF_PY:-python3}" -m autose --home "$OUT/home-$v" --python "$PY" \
        local --issue-file "$HERE/experiment/issues/issue-$n.md" --issue "$n" --repo "$wt" --stages 3-4 \
        --freeze-dir "$FROZEN/issue-$n" --variant "$v" > "$OUT/e2-$n-$v.json" 2> "$OUT/e2-$n-$v.log" \
      || echo "nonzero $n $v" >> "$OUT/nonzero.txt" ) &
  done
done
wait
echo "E2 runs done: $OUT (score each worktree with experiment/scripts/score.py)"
