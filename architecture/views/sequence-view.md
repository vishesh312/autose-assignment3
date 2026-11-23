# Sequence view

> **PLANNED sequence (pre-implementation). Will be replaced by the sequence of a real run with run/PR links once runs exist.**

Source of truth: [`../DESIGN.md`](../DESIGN.md) (sections 2, 3, 4, 5). Rendered copies: `sequence-view.svg` / `.png` (source `sequence-view.mmd`).

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

  Note over B: S1 Requirements
  B->>GH: gh issue view N (title, body, write-access comments)
  B->>AN: fenced issue text + A1 skill
  AN-->>B: spec.json
  B->>J: acceptance criteria only
  J-->>B: judge.json (all testable)
  Note over B: schema, AC shape, judge, no blocking question: PASS
  B->>GH: update status comment

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

  Note over B: S5 Release (deterministic)
  B->>GH: push autose/issue-N (force-with-lease), open PR, trace comment
  B->>GH: upload artifacts autose-issueN-r1, update status comment
  B->>C: needs: build (head SHA)
  C->>GH: commit status success
  C->>R: needs: ci success

  Note over R: round 1, fresh runner, no artifacts, no token
  R->>R: checkout PR head, git diff base...head, run probes
  R->>P: review.json artifact
  P->>GH: COMMENT review header REQUEST_CHANGES, label review-changes-requested

  alt changes requested and send_backs below 2 (here: code finding, send-back 1)
    P->>B: verdict output, route = S3 (rework job, round 2)
    B->>D: fresh context, code findings
    D-->>B: revised diff
    B->>T: re-run S4 from spec
    T-->>B: tests + test_map.json
    Note over B: S3 and S4 checks PASS
    B->>GH: force-push, update PR body and trace comment
    B->>C: head SHA
    C->>GH: commit status success
    C->>R: needs: ci success
    R->>R: review again with own round-1 findings
    R->>P: review.json (approve, checks_performed not empty)
    P->>GH: COMMENT review header APPROVE, label review-approved
  else send_backs already 2
    Note over P: review is final, no further routing
  end

  P->>F: verdict
  F->>GH: label autose:awaiting-human, final status comment
  GH-->>M: notification: reviewed PR waiting
  Note over M: human decides merge or close (bot never merges)
```

Notes on the planned run:

- Steps 3-5: the gate checks the sender through the collaborators API and creates the sticky status comment. Later steps edit it in place.
- Steps 8-11: the Analyst sees the fenced issue; the Judge sees only the AC list. The orchestrator, not an agent, decides the S1 check.
- Developer retry loop: every attempt starts from a fresh context and receives only the failing test ids plus assertion output truncated to 4 KB. The no-progress detector compares the diff hash and failing test set with the previous attempt.
- S5 Release is deterministic: no agent pushes or opens the PR.
- Review job: fresh runner, `contents: read`, no token in the agent environment, no build artifacts. It sees the raw issue, `git diff base...head`, the PR head checkout and (in round 2) its own round-1 findings.
- Send-back: post-review emits `verdict` and the route; the round-2 `rework` job re-enters at S3 and re-runs every later stage up to S5, then CI and review run again. After 2 send-backs the next review is final.
- The verdict is posted as a `COMMENT` review (a `GITHUB_TOKEN`-opened PR cannot be approved by the same identity) with the verdict in its header and a verdict label. The bot never merges.

## Real run (to be filled)

Run: _Actions run link_ · Issue: _link_ · PR: _link_ · Review: _link_

| step | timestamp | job | artifact | link |
|---|---|---|---|---|
| 1 | | gate | status comment | |
| 2 | | build | `spec.md`, `spec.json`, `judge.json` | |
| 3 | | build | `design.md`, `design.json` | |
| 4 | | build | `diff.patch`, `dev_notes.json` | |
| 5 | | build | `tests/test_autose_issue_<N>.py`, `test_map.json`, `test_report.md` | |
| 6 | | build | `pr.md`, PR link, trace comment | |
| 7 | | ci | commit status | |
| 8 | | review | `review.json` | |
| 9 | | post-review | `review.md` (PR review) | |
| ... | | rework / ci / review / post-review | | |
| n | | finalize | final label + status comment | |
