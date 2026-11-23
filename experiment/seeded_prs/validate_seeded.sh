#!/usr/bin/env bash
# Validate one seeded PR in a SCRATCH clone of tinydb at edff96a (with .venv). Destructive for that clone:
# it hard-resets to edff96a and cleans untracked files (except .venv) before and after.
#
# Usage: experiment/seeded_prs/validate_seeded.sh <scratch-tinydb-clone> SPk
set -u
R="$(cd "$1" && pwd)"; SP="$2"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HT="$HERE/../hidden_tests"
D="$HERE/$SP/pr.diff"
N="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["issue"])' "$HERE/$SP/label.json")"
PY="$R/.venv/bin/python"; T="tests/test_autose_issue_$N.py"
cd "$R"
git reset -q --hard edff96a; git clean -qfdx -e .venv
echo "## $SP (issue $N): apply"; git apply --check "$D" && git apply "$D" && echo "applies cleanly"
echo "## existing suite (excluding $T)"; $PY -m pytest -q -p no:cacheprovider -o addopts="" --ignore="$T" tests 2>&1 | tail -1
echo "## full suite with repo pytest.ini (incl. new tests)"; $PY -m pytest -q -p no:cacheprovider 2>&1 | tail -1
echo "## mypy tinydb tests"; $PY -m mypy tinydb tests 2>&1 | tail -1
echo "## own tests"; $PY -m pytest -q -p no:cacheprovider -o addopts="" "$T" 2>&1 | tail -1
echo "## hidden tests"; PYTHONPATH="$R" $PY -m pytest -q -rA -p no:cacheprovider -o addopts="" "$HT/test_issue_$N.py" 2>&1 | grep -E "^(PASSED|FAILED|ERROR)|passed|failed"
echo "## own tests on base (tinydb/ reverted to edff96a)"; git checkout -q edff96a -- tinydb
$PY -m pytest -q -rA -p no:cacheprovider -o addopts="" "$T" 2>&1 | grep -E "^(PASSED|FAILED|ERROR)|passed|failed"
git reset -q --hard edff96a; git clean -qfdx -e .venv
