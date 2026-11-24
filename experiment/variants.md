# Decision-experiment variants

The brief asks us to test two ADRs and to show the results side by side. We picked the two decisions that we were least sure of and that cost the most if we got them wrong:

- **E1** tests **ADR-008, reviewer independence.** If an independent reviewer catches no more than a "friendly" reviewer does, then the separate job, the different model and the hidden context buy us nothing except cost.
- **E2** tests **ADR-001, splitting the work.** We specifically test the split between the Developer and the Tester. If a single builder agent writes tests that are just as good, the extra agent only adds tokens and hand-off loss.

Each experiment changes exactly one decision. Everything else stays fixed: the repo commit, the issues, the frozen upstream artifacts, the harness version and the prompts of every other role.

## E1 — ADR-008: independent vs friendly (vs cross-vendor) reviewer

Since ADR-014 all agents run on subscriptions (Codex CLI with a ChatGPT login; Antigravity CLI `agy` with a Google login), so E1 has **three arms**. The first two are the original A/B comparison; the third was added because ADR-014 made the reviewer and the builders models from the same vendor, and ADR-014 names "friendly ≈ independent" as the sign that a same-vendor model difference is not independent enough.

| | `independent` (our design, variant A) | `friendly` (variant B) | `xvendor` (cross-vendor control) |
|---|---|---|---|
| Backend / model | Codex, `gpt-6-astra` | Codex, `gpt-6.1-sol` (the builders' model) | `agy`, Claude Opus 4.6 (`claude-opus-4-6-thinking`) |
| Prompt | `prompts/reviewer.*`: adversarial; derives expectations from the issue and must run probes | `prompts/reviewer_friendly.*`: neutral "review this PR" | `prompts/reviewer.*` (same as independent) |
| Context | the issue + the diff + the repo at the PR head | the same, **plus** `spec.md`, `design.md`, `dev_notes.json` and `test_report.md` (the implementer's view) | the same as independent |
| Verifier (ADR-015) | `gpt-6-astra` (Codex) | `gpt-6-astra` (Codex) | Claude Opus 4.6 (`agy`) |
| Tools / permissions | the same in every arm: read the repo, run pytest and python, write only to the probe dir (Codex: `workspace-write` sandbox, no network; `agy`: `--sandbox`, which does **not** block network) | the same | the same, except network (see the threats below) |
| Output schema | `review.schema.json` | the same | the same |

`independent` vs `friendly` changes three things at once (model, prompt, context): it tests ADR-008 as a package, as originally planned. `independent` vs `xvendor` changes only the model and vendor, so it isolates the "different model" part of ADR-008.

**Inputs.** The 5 seeded PRs in `seeded_prs/` all have known labels: one is correct, one misses an edge case, one takes the wrong approach, one has vacuous tests, and one has a subtle bug plus an injection aimed at the reviewer. The seeded PRs carry no implementer artifacts, so for the friendly arm we wrote the minimal `spec.md`, `design.md`, `dev_notes.json` and `test_report.md` that a pipeline would have produced. That keeps the context difference realistic. These files are stored in `seeded_prs/<id>/friendly_context/`. Real AutoSE PRs are added as inputs when they exist; their ground truth comes from the hidden tests.

**Runs.** 1 local run per PR per arm; if quota allows, the set is repeated into a separate out root, because LLM verdicts are noisy and n=5 is small. We report this as a threat to validity.

**Two verdicts per run.** Verification is on (`AUTOSE_VERIFY=1`, the default), so each run records the reviewer's own verdict (`reviewer_verdict`, from `review_raw.json`) and the verdict after the verification pass (`verdict`). The reviewer verdict is the primary E1 measure, since it is the reviewer that the arms vary; the post-verification verdict shows what the pipeline would have posted. Note that the friendly arm's verifier is `gpt-6-astra`, so its post-verification verdict is not a pure "friendly" result.

**Metrics** (stored in `results/results.csv`, with experiment `E1`):

- verdict correct (compared with the label), for both the reviewer verdict and the post-verification verdict
- false approval (approves a defective PR)
- false rejection (requests changes on the correct PR)
- the seeded defect named in an `important` finding (yes/no, judged by us against the label)
- findings dropped by the verifier, and whether any dropped finding matched the seeded defect
- whether the reviewer obeyed the injection
- the number of probes it ran (`checks_performed`)
- tokens, and notional list-price-equivalent cost (ADR-014)

**Commands (local, no GitHub writes).** All arms run with `autose review-local` on the same pinned harness, so the comparison is paired:

```bash
# all arms on all 5 seeded PRs (arms in parallel per PR); outputs <out>/<arm>-SP<k>.json + logs
experiment/scripts/run_e1.sh <tinydb checkout> <python of tinydb venv> <out root> [independent friendly xvendor]

# one arm by hand
cd workflow && python -m autose --home <out>/independent --python <py> review-local \
  --pr-dir ../experiment/seeded_prs/SP1 --repo <tinydb checkout> --variant independent   # or: friendly
# xvendor = the independent variant with the reviewer and verifier on agy:
AUTOSE_BACKEND_REVIEWER=agy AUTOSE_BACKEND_VERIFIER=agy python -m autose ... review-local ... --variant independent
```

**Additionally on GitHub (independent arm only).** The 5 seeded PRs are opened as real same-repo PRs on the fork ([#7–#11](https://github.com/vishesh312/tinydb/pulls?q=label%3Aseeded)) and reviewed by the real workflow with `/autose review`, to show our reviewer working end to end. These runs are linked in `results/runs.md`; the side-by-side E1 comparison uses only the paired local runs.

**Threats specific to the arms.** `agy`'s sandbox does not block network (ADR-014), so the xvendor reviewer could in principle fetch things the others cannot; seeded PRs need no network, and we check the logs for network use. The three arms also differ in harness (Codex vs Antigravity), not only in model.

## E2 — ADR-001: separate Tester vs single Builder

| | Variant A: split (our design) | Variant B: single builder |
|---|---|---|
| Stage 3 | Developer (`prompts/developer.*`) | Builder (`prompts/builder.*`) implements the change **and** writes the tests in one context |
| Stage 4 | Tester (`prompts/tester.*`), a fresh context that sees only the ACs and the public API | (none: the Builder's tests are used) |
| Checks | identical: path allowlists, build, full suite, AC→test coverage, fails-on-base | identical (the single path allowlist covers `tinydb/**` plus the one test file) |
| Retry budget | 3 attempts | 3 attempts |
| Per-call cap (notional $) | Developer $1.50, Tester $1.00 | Builder $2.50 |
| Model | `gpt-6.1-sol` (Codex) | `gpt-6.1-sol` (Codex) |

**Inputs.** We use the 5 issues. **S1–S2 are frozen**, meaning both variants start from the same `spec.json` and `design.json`, captured from the real pipeline run for each issue. This removes the variance that the spec and design would otherwise add. The vague issue uses the spec produced after the maintainer's answer.

**Metrics:**

- the number of hidden acceptance tests that pass (the main measure of correctness)
- whether the pipeline's own S4 check passes
- whether the new tests fail on base
- **test–implementation collusion**: the number of generated tests that pass on the implementation but encode behaviour that the hidden tests contradict, judged by running the generated tests against the reference solution. A generated test that *fails on the reference fix* is evidence that the tests copied the implementation instead of the spec.
- attempts
- tokens and cost

**Commands (local).**

```bash
# 1. capture frozen S1-S2 per issue (from the real pipeline run, or locally):
cd workflow && python -m autose --home <frozen-run> --python <py> local \
  --issue-file ../experiment/issues/issue-N.md --repo <fresh tinydb checkout> --stages 1-2
# 2. both variants on all issues, each in its own git worktree of a clean tinydb (in parallel):
experiment/scripts/run_e2.sh <clean tinydb repo> <python of tinydb venv> <frozen root with issue-N/{spec,design}.json> <out root> [issues...]
#    (one by hand: python -m autose local --issue-file ... --repo <worktree> --stages 3-4 --freeze-dir <frozen>/issue-N --variant split|single)
# 3. score a worktree against the hidden tests and the reference fix (prints JSON):
python3 experiment/scripts/score.py N <out root>/wt-N-<split|single> <clean tinydb repo> <python of tinydb venv>
```

`score.py` reports `hidden_passed`/`hidden_total` and, for the collusion measure, `gen_fail_on_reference`: the number of generated tests that fail when run against the reference fix.

## What would change our design

| Result | Action |
|---|---|
| E1: friendly ≈ independent on accuracy, and friendly is cheaper | Supersede ADR-008/ADR-006: keep the job isolation (it is a safety property) but use the builder model for the reviewer |
| E1: xvendor clearly better than independent | A same-vendor model difference is not independent enough: make the cross-vendor reviewer the default where its sandbox allows (ADR-014's stated trigger) |
| E1: the verifier drops findings that match a seeded defect | Raise the `REJECTED` bar or make verification advisory (ADR-015's stated trigger) |
| E1: independent makes more false rejections | Tune the severity rules in the reviewer prompt; record this in a new ADR |
| E2: single ≥ split on hidden tests, with no more collusion | Supersede ADR-001: merge the Developer and the Tester |
| E2: split clearly better on collusion or hidden tests | ADR-001 is confirmed, with the evidence added to it |
