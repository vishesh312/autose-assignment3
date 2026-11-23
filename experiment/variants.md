# Decision-experiment variants

The brief asks us to test two ADRs and to show the results side by side. We picked the two decisions that we were least sure of and that cost the most if we got them wrong:

- **E1** tests **ADR-008, reviewer independence.** If an independent reviewer catches no more than a "friendly" reviewer does, then the separate job, the different model and the hidden context buy us nothing except cost.
- **E2** tests **ADR-001, splitting the work.** We specifically test the split between the Developer and the Tester. If a single builder agent writes tests that are just as good, the extra agent only adds tokens and hand-off loss.

Each experiment changes exactly one decision. Everything else stays fixed: the repo commit, the issues, the frozen upstream artifacts, the harness version and the prompts of every other role.

## E1 — ADR-008: independent vs friendly reviewer

| | Variant A: independent (our design) | Variant B: friendly |
|---|---|---|
| Model | `claude-opus-5-5` | `claude-sonnet-5-5` (the same model as the builders) |
| Prompt | `prompts/reviewer.*`: adversarial; it derives expectations from the issue and must run probes | `prompts/reviewer_friendly.*`: neutral "review this PR" |
| Context | the issue + the diff + the repo at the PR head | the same, **plus** `spec.md`, `design.md`, `dev_notes.json` and `test_report.md` (the implementer's view) |
| Tools / permissions | the same in both variants (read, run pytest and python, write only to the probe dir) | the same |
| Output schema | `review.schema.json` | the same |

**Inputs.** The 5 seeded PRs in `seeded_prs/` all have known labels: one is correct, one misses an edge case, one takes the wrong approach, one has vacuous tests, and one has a subtle bug plus an injection aimed at the reviewer. The real AutoSE PRs are run as well, and their ground truth comes from the hidden tests. The seeded PRs carry no implementer artifacts, so for Variant B we write the minimal `spec.md` and `design.md` that a pipeline would have produced. That keeps the context difference realistic. These files are stored in `seeded_prs/<id>/friendly_context/`.

**Runs.** We do 1 run per PR per variant. If the budget allows, we add a second repetition of the seeded set, because LLM verdicts are noisy and n=5 is small. We report this as a threat to validity.

**Metrics** (stored in `results/results.csv`, with experiment `E1`):

- verdict correct (compared with the label)
- false approval (approves a defective PR)
- false rejection (requests changes on the correct PR)
- the seeded defect named in a blocking finding (yes/no, judged by us against the label)
- whether the reviewer obeyed the injection
- the number of probes it ran
- tokens and cost

**Command (local, no GitHub writes).** `python -m autose review-local --pr-dir experiment/seeded_prs/<id> --variant independent|friendly --repo <tinydb checkout>`

## E2 — ADR-001: separate Tester vs single Builder

| | Variant A: split (our design) | Variant B: single builder |
|---|---|---|
| Stage 3 | Developer (`prompts/developer.*`) | Builder (`prompts/builder.*`) implements the change **and** writes the tests in one context |
| Stage 4 | Tester (`prompts/tester.*`), a fresh context that sees only the ACs and the public API | (none: the Builder's tests are used) |
| Checks | identical: path allowlists, build, full suite, AC→test coverage, fails-on-base | identical (the single path allowlist covers `tinydb/**` plus the one test file) |
| Retry budget | 3 attempts | 3 attempts |
| Model | Sonnet 5.5 | Sonnet 5.5 |

**Inputs.** We use the 5 issues. **S1–S2 are frozen**, meaning both variants start from the same `spec.json` and `design.json`, captured from the real pipeline run for each issue. This removes the variance that the spec and design would otherwise add. The vague issue uses the spec produced after the maintainer's answer.

**Metrics:**

- the number of hidden acceptance tests that pass (the main measure of correctness)
- whether the pipeline's own S4 check passes
- whether the new tests fail on base
- **test–implementation collusion**: the number of generated tests that pass on the implementation but encode behaviour that the hidden tests contradict, judged by running the generated tests against the reference solution. A generated test that *fails on the reference fix* is evidence that the tests copied the implementation instead of the spec.
- attempts
- tokens and cost

**Command (local).** `python -m autose local --issue-file experiment/issues/issue-N.md --repo <fresh tinydb checkout> --stages 3-4 --freeze-dir results/frozen/issue-N --variant split|single`

## What would change our design

| Result | Action |
|---|---|
| E1: friendly ≈ independent on accuracy, and friendly is cheaper | Supersede ADR-008/ADR-006: keep the job isolation (it is a safety property) but use Sonnet for the reviewer |
| E1: independent makes more false rejections | Tune the severity rules in the reviewer prompt; record this in a new ADR |
| E2: single ≥ split on hidden tests, with no more collusion | Supersede ADR-001: merge the Developer and the Tester |
| E2: split clearly better on collusion or hidden tests | ADR-001 is confirmed, with the evidence added to it |
