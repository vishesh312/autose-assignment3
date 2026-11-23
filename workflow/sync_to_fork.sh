#!/usr/bin/env bash
# Copy the AutoSE source of truth (this repo's workflow/) into a local checkout of the fork.
#
#   workflow/autose, prompts, skills (schemas live in autose/schemas) -> <fork>/.autose/
#   workflow/github-workflows/*.yml                                   -> <fork>/.github/workflows/
#
# Removes upstream ci-workflow.yml and publish-workflow.yml (ci.yml replaces the former; the
# latter must never run in the fork). Does not commit or push: review the diff, then commit.
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "usage: $0 <path-to-local-fork-checkout>" >&2
  exit 2
fi
FORK="$(cd "$1" && pwd)"
SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ ! -d "$FORK/.git" ]]; then
  echo "error: $FORK is not a git checkout" >&2
  exit 1
fi
if [[ ! -f "$FORK/tinydb/__init__.py" ]]; then
  echo "error: $FORK does not look like the tinydb fork" >&2
  exit 1
fi

rm -rf "$FORK/.autose"
mkdir -p "$FORK/.autose" "$FORK/.github/workflows"
rsync -a --exclude '__pycache__' --exclude '*.pyc' "$SRC/autose" "$FORK/.autose/"
rsync -a "$SRC/prompts" "$FORK/.autose/"
rsync -a "$SRC/skills" "$FORK/.autose/"
cp "$SRC"/github-workflows/*.yml "$FORK/.github/workflows/"
rm -f "$FORK/.github/workflows/ci-workflow.yml" "$FORK/.github/workflows/publish-workflow.yml"

echo "Synced into $FORK:"
git -C "$FORK" status --short -- .autose .github
