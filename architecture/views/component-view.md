# Component view

Source of truth: [`../DESIGN.md`](../DESIGN.md) (sections 2, 2.1, 3, 5, 6, 7, 10) and the ADRs in [`../decisions/`](../decisions/). Rendered copies for the report: `component-view.svg` / `.png`, `state-machine.svg` / `.png` (sources: `*.mmd` in this folder, rendered with `@mermaid-js/mermaid-cli@11.4.2`).

## 1. Components, tools and who calls whom

```mermaid
flowchart TB
  maint(["Maintainer<br/>write / maintain / admin"])

  subgraph GH["GitHub: vishesh312/tinydb"]
    direction LR
    subgraph UNTRUSTED["TRUST BOUNDARY: untrusted text"]
      issue["Issue N<br/>title, body, comments"]
    end
    events["Label autose / comment /autose<br/>/autose review on PR"]
    runner["Actions runner<br/>autose.yml + autose-round.yml<br/>concurrency: autose-N"]
    rest[("GitHub REST API + git remote")]
    subgraph STORES["GitHub-hosted state (durable)"]
      branch[("Branch autose/issue-N")]
      status[("Issue status comment<br/>marker autose:status")]
      prdoc[("PR: body pr.md<br/>+ trace comment")]
      prreview[("PR review review.md<br/>+ verdict label")]
    end
  end

  subgraph RUN["One Actions run: fixed DAG gate - build - round 1..3 - finalize"]
    direction LR
    subgraph JG["gate job | issues:write, pull-requests:read, contents:read"]
      gate["Gate (no LLM)<br/>collaborator permission check,<br/>reject bots and fork PRs,<br/>resolve canonical issue N"]
    end
    subgraph JB["build job S1-S5 | contents:write, pull-requests:write, issues:write"]
      orch["autose orchestrator (no LLM)<br/>state machine + checks<br/>ledger.jsonl, state.json, renders test_report.md<br/>Release S5 by template, 8 USD run cap"]
    end
    subgraph ROUND["autose-round.yml, rounds 1..3, if: previous verdict"]
      direction LR
      subgraph JR["rework job, rounds 2-3 | contents:write, pull-requests:write, issues:write"]
        orchR["autose rework<br/>re-enters routed stage, runs on to S5"]
      end
      subgraph JC["ci job | contents:read, statuses:write"]
        ci["Reusable CI on head SHA<br/>pytest, mypy, commit status"]
      end
      subgraph JV["review job | contents:read, issues:read, pull-requests:read"]
        direction TB
        prep["prepare step (token)<br/>writes issue text, trusted comments,<br/>git diff base...head to files"]
        subgraph JVA["agent step: NO-TOKEN BOUNDARY, persist-credentials:false"]
          rcli["claude -p --bare"]
          reviewer["Reviewer | Opus 5.5 | 2 USD<br/>Read, Grep, Glob, Write to probes dir<br/>Bash: pytest, python probe-dir/*, git diff/log/show"]
        end
      end
      subgraph JP["post-review job | pull-requests:write, issues:write"]
        post["Validate review.json, route,<br/>count send-backs, post COMMENT review"]
      end
    end
    subgraph JF["finalize job | issues:write, pull-requests:write"]
      fin["Final labels + status<br/>awaiting-human / failed"]
    end
  end

  subgraph AG["Builder agents: claude -p --bare, fresh context per call, no MCP, no Web, no GitHub token"]
    direction LR
    cli["claude CLI<br/>--json-schema, --max-budget-usd"]
    analyst["Analyst | Sonnet 5.5 | 0.75 USD<br/>Read, Grep, Glob"]
    judge["Judge | Haiku 5.5 | 0.05 USD<br/>no tools, single call"]
    architect["Architect | Sonnet 5.5 | 0.75 USD<br/>Read, Grep, Glob"]
    dev["Developer | Sonnet 5.5 | 1.50 USD<br/>Read, Grep, Glob, Edit, Write<br/>Bash: pytest, mypy, compileall, git diff/status"]
    tester["Tester | Sonnet 5.5 | 1.00 USD<br/>Read, Grep, Glob, Edit, Write<br/>Bash: pytest"]
  end

  ghcli["gh CLI + git<br/>deterministic steps only<br/>GITHUB_TOKEN"]
  anth(["Anthropic API"])
  art[("Workflow artifacts<br/>autose-issueN-rR<br/>spec, design, diff, test_report, ledger")]
  revart[("Review artifact<br/>autose-issueN-review-rK<br/>review.json")]

  maint -->|adds label / comments| events
  events -->|triggers| runner
  runner --> gate
  gate -->|authorised| orch
  orch -->|subprocess| cli
  orchR -->|subprocess| cli
  cli --> analyst & judge & architect & dev & tester
  cli -->|HTTPS| anth
  rcli --> reviewer
  rcli -->|HTTPS| anth

  gate --> ghcli
  orch --> ghcli
  orchR --> ghcli
  ci --> ghcli
  post --> ghcli
  fin --> ghcli
  ghcli -->|REST / push --force-with-lease| rest
  rest --> branch & status & prdoc & prreview

  issue -.->|fetched by gh, fenced as data| orch
  prep --> ghcli
  issue -.->|issue text + trusted comments| prep
  prep -.->|files only, fenced| rcli
  orch -->|upload| art
  art -->|download| orchR
  art -.-x|NOT downloaded| rcli
  branch -.->|checkout head SHA| ci
  branch -.->|checkout PR head| rcli
  orch -->|needs: PR open| ci
  ci -->|needs: success| rcli
  rcli -->|upload review.json| revart
  revart --> post
  revart -.->|previous round only, by exact name| rcli
  post -->|verdict output| orchR
  post --> fin

  classDef trust fill:#fff0f0,stroke:#c00,stroke-width:2px,stroke-dasharray:6 4
  classDef agent fill:#eef4ff,stroke:#3366cc
  classDef det fill:#f3f3f3,stroke:#555
  classDef store fill:#fffbe6,stroke:#b8860b
  classDef ext fill:#eaffea,stroke:#2e7d32
  class UNTRUSTED,JVA trust
  class analyst,judge,architect,dev,tester,reviewer agent
  class gate,orch,orchR,ci,post,fin,ghcli,cli,rcli,prep det
  class branch,status,prdoc,prreview,art,revart store
  class anth,rest ext
```

### Legend

| Notation | Meaning |
|---|---|
| Large boxes with a header (`gate job`, `build job`, ...) | One GitHub Actions job (its own runner). The header lists the job's `GITHUB_TOKEN` permissions. |
| `autose-round.yml` box | Reusable workflow called up to 3 times (rounds 1..3), each gated by `if:` on the previous round's `verdict`. `rework` only exists in rounds 2 and 3. |
| Blue rectangles | LLM agents (`claude -p --bare`), annotated with role, model and per-call `--max-budget-usd` cap, and the `--tools` / Bash allowlist. |
| Grey rectangles | Deterministic code (no LLM): gate, orchestrator, CI, post-review, finalize, `gh`/`git`, the `claude` CLI process. |
| Cylinders | Data stores (workflow artifacts, branch, status comment, PR body/trace comment, PR review). |
| Green | External services (Anthropic API, GitHub REST API / git remote). |
| Red dashed box | Trust boundary: (a) untrusted issue text, (b) the review job's agent step, which has no token in its environment, no write permission and no build artifacts (only files written by the prepare step and its own previous `review.json`). |
| Solid arrow | Call / control (subprocess, HTTP, `needs:`). |
| Dotted arrow | Data flow only (text that is read, a checkout). |
| Dotted arrow ending in `x` | Deliberately absent flow (the review job never downloads the build artifacts `autose-issueN-rR`). |

Key properties the diagram shows:

- **Only deterministic code talks to GitHub.** Every GitHub call goes `job step -> gh CLI / git (GITHUB_TOKEN) -> GitHub REST / remote`. No agent has an edge to GitHub; agent processes do not get `GH_TOKEN`/`GITHUB_TOKEN`, `actions/checkout` uses `persist-credentials: false`, and no agent has MCP, WebFetch or WebSearch.
- **Only the `claude` CLI talks to the model provider.** The path is `orchestrator -> claude CLI (subprocess) -> Anthropic API`. The Judge also goes through this path, as a single call with no tools.
- **Untrusted text** (issue title, body, comments) enters in two places only, both read-only and fenced as data: the Analyst (through the orchestrator) and the Reviewer (through files written by the review job's prepare step, for comparison only). Write-capable agents (Developer, Tester) see only derived artifacts.
- **The review job is isolated.** It runs on a fresh runner with read-only permissions (`contents`, `issues`, `pull-requests`). A *prepare* step uses the token to write the issue text, trusted comments and `git diff base...head` to files; the *agent* step then runs with no token in its environment and reads only those files plus the PR head checkout. The only artifact it downloads is its own previous round's `review.json` (`autose-issueN-review-rK`, fetched by exact name); it never downloads `autose-issueN-rR`.

### Component table

| Component | Responsibility | Tools / permissions | Talks to |
|---|---|---|---|
| Maintainer | Triggers a run (label `autose`, `/autose`, `/autose review`); makes the final merge/close decision | write/maintain/admin on the fork | GitHub UI |
| GitHub issue / PR / labels / comments | Trigger events; untrusted input; human-visible state | — | Actions runner (events) |
| Actions runner (`autose.yml`, `autose-round.yml`) | Runs the fixed job DAG gate, build, round 1..3, finalize; `concurrency: autose-<N>`, `cancel-in-progress: false` | timeouts: build 60 min, review 30 min, CI 15 min | All jobs |
| gate job | Authorises the sender (collaborators API, not only `author_association`), ignores bots, rejects comments on PRs from forks, resolves the canonical issue number, creates the status comment | `issues: write`, `pull-requests: read`, `contents: read` | `gh` -> GitHub REST |
| build job: `autose` orchestrator | Deterministic state machine for S1-S5; runs every check; writes `ledger.jsonl` and `state.json`; renders `test_report.md` from pytest results, `test_map.json` and fails-on-base results; enforces the $8 run cap; performs S5 Release from templates; uploads workflow artifacts | `contents: write`, `pull-requests: write`, `issues: write` | `claude` CLI (subprocess), `gh`/`git`, workflow artifacts |
| rework job (rounds 2-3) | Same orchestrator, re-entering at the stage the reviewer routed to and running on to S5 | `contents: write`, `pull-requests: write`, `issues: write` | `claude` CLI, `gh`/`git`, workflow artifacts (download) |
| ci job | Reusable CI on the head SHA (because pushes made with `GITHUB_TOKEN` do not trigger workflows); posts a commit status | `contents: read`, `statuses: write` | `gh` -> commit status; branch checkout |
| review job | Prepare step (with token) writes issue text, trusted comments and `git diff` to files; agent step (no token) runs the Reviewer on the PR head checkout; uploads `review.json` as `autose-issue<N>-review-r<k>` | `contents: read`, `issues: read`, `pull-requests: read`; no token in the agent step's env; downloads only the previous round's review artifact | prepare: `gh` -> GitHub REST; agent: `claude` CLI -> Anthropic API |
| post-review job | Validates `review.json` (re-asks once if invalid), computes the route, counts send-backs, posts a `COMMENT` review with the verdict in the header, applies the verdict label, outputs `verdict` | `pull-requests: write`, `issues: write` | `gh` -> GitHub REST |
| finalize job | Applies the final label (`autose:awaiting-human` / `autose:failed`) and writes the final status comment | `issues: write`, `pull-requests: write` | `gh` -> GitHub REST |
| `claude` CLI | Headless harness: `claude -p --bare --no-session-persistence --model <m> --tools ... --allowedTools ... --max-budget-usd <cap> --output-format json --json-schema <schema>`; 20 min subprocess timeout | `ANTHROPIC_API_KEY` only | Anthropic API |
| Analyst | S1: issue -> `spec.json` (A1 `requirements-spec` skill + issue adapter) | Sonnet 5.5, medium effort, $0.75; Read, Grep, Glob (read-only) | orchestrator (via structured output) |
| Judge | S1: rates each AC as testable or not | Haiku 5.5, low effort, $0.05; no tools, single call | orchestrator |
| Architect | S2: `spec.md` + `ARCHITECTURE.md` -> `design.json` | Sonnet 5.5, medium effort, $0.75; Read, Grep, Glob | orchestrator |
| Developer | S3: edits `tinydb/**` following the design; writes `dev_notes.json` | Sonnet 5.5, high effort, $1.50; Read, Grep, Glob, Edit, Write, Bash(`python -m pytest*`, `python -m mypy*`, `python -m compileall*`, `git diff*`, `git status*`) | orchestrator (working tree) |
| Tester | S4: writes `tests/test_autose_issue_<N>.py` and `test_map.json` from the ACs and the public API section | Sonnet 5.5, medium effort, $1.00; Read, Grep, Glob, Edit, Write, Bash(`python -m pytest*`) | orchestrator (working tree) |
| Reviewer | S6: adversarial review from the issue + diff + repo at the PR head -> `review.json` | Opus 5.5, high effort, $2.00; Read, Grep, Glob, Write (only `$RUNNER_TEMP/review-probes/`), Bash(`python -m pytest *`, `python <probe-dir>/*`, `git diff *`, `git log *`, `git show *`) | review job (structured output) |
| `gh` CLI + `git` | The only GitHub client; used by deterministic steps only | job's `GITHUB_TOKEN` | GitHub REST API, git remote |
| Anthropic API | Model inference | provider-side hard spend limit | — |
| Workflow artifacts `autose-issue<N>-r<round>` | State between jobs in one run (spec, design, diff, test report, ledger, state) | upload/download-artifact | build/rework (up), rework (down); review job: not downloaded |
| Review artifact `autose-issue<N>-review-r<k>` | `review.json` of round k | upload/download-artifact | review job (up; next round's review job down, by exact name), post-review (down) |
| Branch `autose/issue-<N>` | The code under review; force-pushed with lease | — | ci, review (checkout) |
| Issue status comment (`<!-- autose:status -->`) | Sticky, edited-in-place stage table with links | — | humans |
| PR body (`pr.md`) + trace comment | PR description from template; spec/design/test report in collapsed sections | — | humans (not the Reviewer) |
| PR review (`review.md`) + label | Reviewer verdict as `COMMENT` review; `autose:review-approved` / `autose:review-changes-requested` | — | humans |

## 2. In-job state machine (orchestrator)

`next_stage = f(stage, check_result, counters)`; every transition is appended to `ledger.jsonl`. S1-S5 run inside the build job (or a rework job); CI and S6 run in the round jobs, and the route chosen by post-review re-enters the state machine in the next round's rework job.

```mermaid
flowchart TD
  start(["Gate passed"]) --> S1

  S1["S1 Requirements<br/>Analyst + Judge"]
  S2["S2 Design<br/>Architect"]
  S3["S3 Implementation<br/>Developer"]
  S4["S4 Testing<br/>Tester + full suite"]
  ESC{"design revisit<br/>unused?<br/>(max 1)"}
  S5["S5 Release<br/>deterministic: push, PR, trace"]
  CI["CI job<br/>reusable workflow"]
  S6["S6 Review<br/>Reviewer, separate job"]
  ROUTE{"send_backs &lt; 2?"}

  NI(["STOP: needs-info<br/>questions posted,<br/>label autose:needs-info"])
  FAIL(["STOP: failed<br/>Stop reason in artifact,<br/>label autose:failed"])
  HUMAN(["STOP: awaiting-human<br/>human merges or closes"])

  S1 -->|check pass| S2
  S1 -->|blocking open question| NI
  S1 -->|check fail, spec attempts &lt; 2:<br/>retry with reasons| S1
  S1 -->|check fail, 2 attempts used| FAIL

  S2 -->|check pass| S3
  S2 -->|check fail, design attempts &lt; 2:<br/>retry with checker output| S2
  S2 -->|check fail, 2 attempts used| FAIL

  S3 -->|builds| S4
  S3 -->|check fail, Developer attempts &lt; 3:<br/>retry with check output| S3
  S3 -->|3 Developer attempts used,<br/>or no progress| ESC

  S4 -->|suite pass, every AC covered,<br/>at least 1 new test fails on base| S5
  S4 -->|Tester check fail, Tester attempts &lt; 2:<br/>retry with checker output| S4
  S4 -->|Tester check fail, 2 attempts used| FAIL
  S4 -->|suite fails, Developer attempts &lt; 3:<br/>failing ids + output| S3
  S4 -->|suite fails, 3 Developer attempts used,<br/>or no progress| ESC
  ESC -->|yes: failure_summary.md,<br/>new design resets Dev/Tester counters| S2
  ESC -->|no| FAIL

  S5 -->|push / PR fails:<br/>retry once after 10 s| S5
  S5 -->|fails again| FAIL
  S5 -->|PR OPEN| CI
  CI -->|success| S6
  CI -->|failure: stop,<br/>CI log link in pr.md| FAIL

  S6 -->|invalid review:<br/>re-ask once| S6
  S6 -->|approve| HUMAN
  S6 -->|changes_requested,<br/>or invalid twice| ROUTE
  ROUTE -->|yes, approach: new design,<br/>Tester regenerates tests,<br/>design revisit not used| S2
  ROUTE -->|yes, code: tests kept,<br/>suite + fails-on-base re-run| S3
  ROUTE -->|yes, tests: Tester<br/>revises its file| S4
  ROUTE -->|no: final review posted| HUMAN

  BUDGET["Any stage: 8 USD run cap<br/>or job timeout reached"] -.-> FAIL

  classDef stop fill:#fff0f0,stroke:#c00
  classDef human fill:#eaffea,stroke:#2e7d32
  classDef stage fill:#eef4ff,stroke:#3366cc
  classDef det fill:#f3f3f3,stroke:#555
  class NI,FAIL stop
  class HUMAN human
  class S1,S2,S3,S4,S6 stage
  class S5,CI,ESC,ROUTE,BUDGET det
```

Every edge follows the routing table in DESIGN.md section 2.1 ("every failed check has exactly one route"). Caps: 2 spec attempts, 2 design attempts, 3 Developer attempts and 2 Tester attempts per design, 1 in-build design revisit, 2 review send-backs, $8 per run, 20 min per agent call. A new design (from the revisit or from an `approach` send-back) resets the Developer and Tester counters; an `approach` send-back does not use the in-build design revisit. "No progress" means the same diff hash **or** the same failing test set as the previous attempt, and is treated as if the Developer attempts were exhausted.
