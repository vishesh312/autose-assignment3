#!/usr/bin/env bash
# Open the 5 seeded reviewer-calibration PRs on the fork (vishesh312/tinydb).
#
# Usage:
#   experiment/seeded_prs/open_seeded_prs.sh <fork-checkout> [--issues 1:N1,2:N2,3:N3,4:N4,5:N5] [--only SP1,SP3] [--trigger-review]
#
#   <fork-checkout>   a clean clone of vishesh312/tinydb with push access (origin = the fork)
#   --issues          map experiment issue numbers (1..5) to the fork's GitHub issue numbers,
#                     used to fill {{ISSUE_REF}} in pr_body.md (default: N -> #N)
#   --only            open only the listed seeded PRs (default: all five)
#   --trigger-review  also post the maintainer comment "/autose review" on each new PR
#
# For each SPk it: creates branch seeded/SPk from origin/main, applies SPk/pr.diff, commits with
# the PR title as a single-line message, pushes, opens the PR with gh against the fork's main,
# and adds the label "seeded" (so humans can tell seeded PRs from real AutoSE PRs; titles stay
# realistic and carry no "[seeded]" prefix). It never touches upstream: every gh call passes
# --repo vishesh312/tinydb. It never merges.
set -euo pipefail

REPO_SLUG="vishesh312/tinydb"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

FORK="${1:?usage: $0 <fork-checkout> [--issues 1:N,...] [--only SP1,...] [--trigger-review]}"
shift
ISSUE_MAP=""
ONLY="SP1,SP2,SP3,SP4,SP5"
TRIGGER=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --issues) ISSUE_MAP="$2"; shift 2 ;;
    --only) ONLY="$2"; shift 2 ;;
    --trigger-review) TRIGGER=1; shift ;;
    *) echo "unknown argument: $1" >&2; exit 2 ;;
  esac
done

fork_issue() {  # experiment issue number -> fork issue number
  local n="$1" pair
  IFS=',' read -ra pairs <<< "$ISSUE_MAP"
  for pair in "${pairs[@]:-}"; do
    [[ "${pair%%:*}" == "$n" ]] && { echo "${pair##*:}"; return; }
  done
  echo "$n"
}

cd "$FORK"
if [[ -n "$(git status --porcelain)" ]]; then
  echo "error: $FORK has uncommitted changes" >&2; exit 1
fi
origin_url="$(git remote get-url origin)"
case "$origin_url" in
  *vishesh312/tinydb*) ;;
  *) echo "error: origin ($origin_url) is not the fork $REPO_SLUG" >&2; exit 1 ;;
esac
command -v gh >/dev/null || { echo "error: gh CLI not found" >&2; exit 1; }

git fetch origin main
gh label create seeded --repo "$REPO_SLUG" --color BFD4F2 \
  --description "Seeded reviewer-calibration PR with a known verdict (experiment E1)" --force

IFS=',' read -ra SPS <<< "$ONLY"
for sp in "${SPS[@]}"; do
  dir="$HERE/$sp"
  [[ -f "$dir/pr.diff" ]] || { echo "error: $dir/pr.diff missing" >&2; exit 1; }
  branch="seeded/$sp"
  title="$(head -n1 "$dir/pr_title.txt")"
  exp_issue="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1]))["issue"])' "$dir/label.json")"
  ref="#$(fork_issue "$exp_issue")"

  echo "=== $sp (issue $exp_issue -> $ref): $title"
  git checkout -B "$branch" origin/main
  git apply --index "$dir/pr.diff"
  git commit -q -m "$title"
  git push --force-with-lease -u origin "$branch"

  body="$(mktemp)"
  sed "s/{{ISSUE_REF}}/$ref/g" "$dir/pr_body.md" > "$body"

  existing="$(gh pr list --repo "$REPO_SLUG" --head "$branch" --state open --json number --jq '.[0].number // empty')"
  if [[ -n "$existing" ]]; then
    gh pr edit "$existing" --repo "$REPO_SLUG" --title "$title" --body-file "$body"
    pr="$existing"
  else
    url="$(gh pr create --repo "$REPO_SLUG" --base main --head "$branch" --title "$title" --body-file "$body")"
    pr="${url##*/}"
  fi
  rm -f "$body"
  gh pr edit "$pr" --repo "$REPO_SLUG" --add-label seeded
  echo "$sp -> https://github.com/$REPO_SLUG/pull/$pr"

  if [[ "$TRIGGER" == 1 ]]; then
    gh pr comment "$pr" --repo "$REPO_SLUG" --body "/autose review"
  fi
done

git checkout -q main 2>/dev/null || true
echo "done. Trigger a review on a PR with a maintainer comment: /autose review"
