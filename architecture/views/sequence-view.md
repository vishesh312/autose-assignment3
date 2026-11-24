# Sequence view

> **PLANNED sequence (pre-implementation). Will be replaced by the sequence of a real run with run/PR links once runs exist.**

Source of truth: [`../DESIGN.md`](../DESIGN.md) (sections 2, 2.1, 3, 4, 5, 6). Rendered copies: `sequence-view.svg` / `.png` (source `sequence-view.mmd`).

This shows one full-pipeline run triggered by the label `autose`, including one test-failure retry inside S3/S4 and one review send-back (a `code` finding, routed to S3), so that both loop levels are visible: the in-job loop run by the orchestrator, and the cross-job loop run through the `autose-round.yml` rounds. The `build job (orchestrator)` lifeline also stands for the round-2 `rework` job, which runs the same orchestrator code.

```mermaid
sequenceDiagram
  autonumber
  actor M as Maintainer
  participant GH as GitHub
  participant G as gate job
  participant B as build job (orchestrator)
  participant AN as Analyst
  participant J as Judge
  participant AR as Architect
  participant D as Developer
  participant T as Tester
  participant C as CI job
  participant R as review job (Reviewer)
  participant P as post-review
  participant F as finalize

  M->>GH: add label autose to issue N
  GH->>G: issues.labeled event
  G->>GH: gh api collaborators permission of sender
  GH-->>G: write
  G->>GH: create status comment (queued)
  G->>B: needs: gate, canonical issue N

  B->>GH: prepare step (token): issue, write-access comments, branch facts to files
  Note over B: agent step: NO token, S1-S4 offline, every agent is codex exec in the Codex sandbox (network off)
  Note over B: S1 Requirements
  B->>AN: fenced issue text + A1 skill
  AN-->>B: spec.json
  B->>J: acceptance criteria only
  J-->>B: judge.json (all testable)
  Note over B: schema, AC shape, judge, no blocking question: PASS

  Note over B: S2 Design
  B->>AR: spec.md + ARCHITECTURE.md
  AR-->>B: design.json
  Note over B: paths exist, AST symbols, AC coverage, allowlist: PASS

  Note over B: S3 Implementation (attempt 1)
  B->>D: design.md + spec.md
  D-->>B: working tree edits + dev_notes.json
  Note over B: allowlist, compileall, import, mypy: PASS

  Note over B: S4 Testing
  B->>T: ACs + Public API / test hooks section
  T-->>B: tests/test_autose_issue_N.py + test_map.json
  Note over B: full suite: 2 new tests FAIL

  loop Developer retry (at most 3 attempts per design)
    B->>D: fresh context, failing test ids + 4 KB assertion output
    D-->>B: revised diff + dev_notes.json
    Note over B: S3 check PASS, no-progress check (diff hash, failing set) OK
    Note over B: full suite PASS, AC coverage OK, new tests fail on base: S4 PASS
  end
  B->>B: render test_report.md, local commit, upload artifacts autose-issueN-r1

  Note over B: publish step (token): S5 Release, deterministic
  B->>B: final path gate: git diff --name-only --no-renames base HEAD within allowlist: PASS
  B->>GH: push autose/issue-N (force-with-lease), open PR, trace comment, labels, status
  B->>C: needs: build (head SHA, spent_usd as a number)
  C->>GH: commit status success
  C->>R: needs: ci success

  Note over R: round 1, fresh runner, no build artifacts
  R->>GH: prepare step (token): issue text, trusted comments, git diff to files
  Note over R: agent step, no token in env
  R->>R: Reviewer reads files + PR head checkout, runs probes
  R->>R: Verifier (fresh read-only call) re-checks the important code finding: CONFIRMED
  R->>P: upload autose-issueN-review-r1 (review.json)
  P->>GH: COMMENT review header REQUEST_CHANGES, label review-changes-requested

  alt changes requested and send_backs below 2 (here: code finding, send-back 1)
    P->>B: verdict output, route = S3 (rework job, round 2)
    B->>GH: prepare step (token): issue, comments, branch facts, download autose-issueN-review-r1
    Note over B: agent step (no token): reservation check, spent + Developer + Tester caps + one Reviewer and one Verifier cap within 10 USD: OK
    B->>D: fresh context, code findings
    D-->>B: revised diff
    Note over B: S4 for a code finding: Tester not called, existing tests kept
    Note over B: suite + fails-on-base re-run PASS, test_report.md re-rendered
    Note over B: publish step (token): final path gate PASS
    B->>GH: force-push with lease, update PR body and trace comment
    B->>C: head SHA
    C->>GH: commit status success
    C->>R: needs: ci success
    R->>GH: prepare step: issue, comments, new diff to files, download autose-issueN-review-r1
    R->>R: agent step (no token) reviews again with own round-1 findings
    R->>P: upload autose-issueN-review-r2 (approve, checks_performed not empty)
    P->>GH: COMMENT review header APPROVE, label review-approved
  else send_backs already 2, or rework plus Reviewer and Verifier caps would exceed 10 USD
    Note over P: last review stands, no further routing
  else review still invalid after one re-ask
    Note over P: posted under INVALID REVIEW (not an approval), no category to route on
  end

  P->>F: verdict
  F->>GH: label autose:awaiting-human, final status comment
  GH-->>M: notification: reviewed PR waiting
  Note over M: human decides merge or close (bot never merges)
```

Notes on the planned run (routes follow DESIGN.md section 2.1):

- Steps 3-5: the gate checks the sender through the collaborators API and creates the sticky status comment. Later steps edit it in place.
- Step 7: the build job's *prepare* step (token) writes the issue, trusted comments and branch facts to files. The *agent* step that follows has **no GitHub token**: the orchestrator runs S1-S4 offline and ends with a local commit. Every agent runs as `codex exec` in the Codex sandbox with network off and no repo instructions or MCP loaded (ADR-014).
- Steps 8-11: the Analyst sees the fenced issue (from the prepare step's files); the Judge sees only the AC list. The orchestrator, not an agent, decides the S1 check.
- Developer retry loop: a suite failure goes back to S3 and uses one of the 3 Developer attempts for this design. Every attempt starts from a fresh context and receives only the failing test ids plus assertion output truncated to 4 KB. If the diff hash or the failing test set repeats, the orchestrator treats the attempts as exhausted and goes to the design revisit (if unused) or stops.
- `test_report.md` is rendered by the orchestrator, not written by the Tester.
- S5 Release is deterministic and runs in the *publish* step (token): the final path gate `git diff --name-only --no-renames <base> HEAD` must stay within the allowlist before anything is pushed, then push with lease, PR, trace comment, labels and status. No agent pushes or opens the PR. The build job passes its spend to the round as a plain number (`spent_usd`). A failing push/PR call is retried once after 10 s; a CI failure stops the run with the CI log linked in `pr.md`.
- Review job: fresh runner with read-only permissions. A prepare step (with the token) writes the issue text, trusted comments and `git diff base...head` to files; the agent step has no token and reads only those files, the PR head checkout and, from round 2, its own previous `review.json` (`autose-issueN-review-r1`). It never downloads the build artifacts. After a valid review, each `important` finding is re-checked by a separate read-only Verifier call that sees only that finding, the issue, the diff and the code (ADR-015); a `REJECTED` finding is shown under "Dropped by verification" and does not route. It re-asks an invalid review only if `spent_usd` plus one Reviewer cap fits the $10 run cap; post-review discards a review whose SHA is no longer the PR head.
- Send-back: post-review emits `verdict` and the route (only `important` findings that survived verification route). The round-2 `rework` job has the same prepare / agent (no token) / publish split; its prepare step downloads the review that routed it, and its agent step first checks the reservation rule (the rework only starts if one Reviewer cap plus one Verifier cap still fits under the run cap after it, otherwise the last review stands). For a `code` finding it re-enters at S3; S4 keeps the existing tests and only re-runs the suite and the fails-on-base check (an `approach` finding would instead go to S2 and the Tester would regenerate its tests; a `tests` finding would go to S4). Then S5, CI and review run again. After 2 send-backs the next review is final.
- The verdict is posted as a `COMMENT` review (a `GITHUB_TOKEN`-opened PR cannot be approved by the same identity) with the verdict in its header and a verdict label. A review that is still invalid after one re-ask is posted under "INVALID REVIEW (not an approval)" and the run ends `awaiting-human`. The bot never merges.

## Real run (to be filled)

Run: _Actions run link_ · Issue: _link_ · PR: _link_ · Review: _link_

| step | timestamp | job | artifact | link |
|---|---|---|---|---|
| 1 | | gate | status comment | |
| 2 | | build | `spec.md`, `spec.json`, `judge.json` | |
| 3 | | build | `design.md`, `design.json` | |
| 4 | | build | `diff.patch`, `dev_notes.json` | |
| 5 | | build | `tests/test_autose_issue_<N>.py`, `test_map.json`, `test_report.md` (orchestrator-rendered) | |
| 6 | | build | `pr.md`, PR link, trace comment | |
| 7 | | ci | commit status | |
| 8 | | review | `review.json` (`autose-issueN-review-r1`) | |
| 9 | | post-review | `review.md` (PR review) | |
| ... | | rework / ci / review / post-review | | |
| n | | finalize | final label + status comment | |
