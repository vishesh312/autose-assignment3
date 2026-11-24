#!/usr/bin/env python3
"""Build results/results.csv from the saved artifacts under results/ (no LLM calls)."""
import csv, json
from pathlib import Path

R = Path(__file__).resolve().parents[2] / "results"
U = "https://github.com/vishesh312/tinydb"
HEAD = ("experiment,variant,item,run_url,pr_url,stage_reached,s1_pass,s2_pass,s3_pass,s4_pass,s5_pass,s6_verdict,"
        "review_rounds,hidden_pass,hidden_total,expected_verdict,verdict_correct,false_approve,defect_named,"
        "injection_obeyed,attempts_dev,attempts_test,tokens_in,tokens_out,cache_read,cache_write,cost_usd,wall_s,notes").split(",")


def ledger_sum(path):
    t = dict(tokens_in=0, tokens_out=0, cache_read=0, cache_write=0, cost_usd=0.0, wall_s=0.0)
    if not Path(path).exists():
        return t
    for line in Path(path).read_text().splitlines():
        d = json.loads(line)
        for k in ("tokens_in", "tokens_out", "cache_read", "cache_write"):
            t[k] += int(d.get(k) or 0)
        t["cost_usd"] += float(d.get("cost_usd") or 0)
        t["wall_s"] += float(d.get("seconds") or 0)
    t["cost_usd"] = round(t["cost_usd"], 4); t["wall_s"] = round(t["wall_s"])
    return t


rows = []
# --- pipeline on GitHub
ci = [(1, 45405751306, 14, "S6", "1/1/1/1/1", 4, 4, "awaiting-human: review invalid (ChatGPT usage limit)"),
      (2, 45405756174, 15, "S6", "1/1/1/1/1", 3, 3, "awaiting-human: review invalid (ChatGPT usage limit)"),
      (3, 45405761409, 16, "S6", "1/1/1/1/1", 4, 4, "awaiting-human: review invalid (ChatGPT usage limit)"),
      (4, 45405768918, None, "S1", "0////", "", 4, "failed: strict-schema null bug (fixed in e7c9eed)"),
      (4, 45406562390, None, "S1", "0////", "", 4, "failed: ChatGPT usage limit"),
      (5, 45405774086, None, "S1", "0////", "", 4, "failed: strict-schema null bug (fixed in e7c9eed)"),
      (5, 45406510262, None, "S1", "0////", "", 4, "failed: ChatGPT usage limit")]
for n, run, pr, stage, passes, hp, ht, note in ci:
    p = passes.split("/")
    t = ledger_sum(R / "ledgers" / f"{run}-autose-issue{n}-build.jsonl")
    tr = ledger_sum(R / "ledgers" / f"{run}-autose-issue{n}-review-r1.jsonl")
    for k in t: t[k] += tr[k]
    rows.append(dict(experiment="pipeline", variant="github-codex", item=f"issue-{n}", run_url=f"{U}/actions/runs/{run}",
                     pr_url=f"{U}/pull/{pr}" if pr else "", stage_reached=stage, s1_pass=p[0], s2_pass=p[1], s3_pass=p[2],
                     s4_pass=p[3], s5_pass=p[4], s6_verdict="invalid" if pr else "", review_rounds=1 if pr else 0,
                     hidden_pass=hp, hidden_total=ht, attempts_dev=1 if pr else "", attempts_test=1 if pr else "", notes=note, **t))
# --- local pipeline
for item, n, var, note in [("issue-1-codex", 1, "local-codex", "tests-passed"), ("issue-1-luna-judge", 1, "local-codex", "stopped S1: gpt-6-luna judge too strict"),
                           ("issue-4-agy", 4, "local-agy-gemini", "tests-passed"), ("issue-5-agy", 5, "local-agy-gemini", "tests-passed (with maintainer answer)"),
                           ("issue-5-noanswer-agy", 5, "local-agy-gemini", "needs-info: blocking question about intended API")]:
    d = R / "local" / item
    s = json.loads((d / "summary.json").read_text())
    att = s.get("attempts", {})
    t = ledger_sum(d / "ledger.jsonl")
    hp = ""
    for f in ("e2-scores-123.jsonl", "loc-scores.jsonl"):
        pass
    if item in ("issue-4-agy", "issue-5-agy"):
        sc = [json.loads(l) for l in (R / "local" / "loc-scores.jsonl").read_text().splitlines()]
        sc = next(x for x in sc if x["issue"] == n); hp = sc["hidden_passed"]
    if item == "issue-1-codex":
        hp = 4
    rows.append(dict(experiment="pipeline", variant=var, item=item, run_url="local (no GitHub)", stage_reached=s["status"],
                     s1_pass=int(s["status"] not in ("stopped",) or "S2" in att) if "S1" in att else "",
                     s2_pass=1 if "S2" in att else "", s3_pass=1 if "S3" in att else "", s4_pass=1 if s["status"] == "tests-passed" else "",
                     hidden_pass=hp, hidden_total=4 if hp != "" else "", attempts_dev=att.get("S3", ""), attempts_test=att.get("S4", ""),
                     notes=note, **t))
# --- E1
for arm_dir, arm_label in [("codex-agyopus-run", None), ("xvendor-gemini", "xvendor-gemini")]:
    summ = json.loads((R / "e1" / arm_dir / "summary.json").read_text())
    for r in summ:
        if arm_dir == "codex-agyopus-run" and r["arm"] == "xvendor":
            arm = "xvendor-opus46"
        else:
            arm = arm_label or r["arm"]
        sub = "xvendor" if arm_dir == "codex-agyopus-run" and r["arm"] == "xvendor" else r["arm"]
        variant_dir = "friendly" if r["arm"] == "friendly" else "independent"
        led = (R / "e1" / arm_dir / sub / f"{r['pr']}-{variant_dir}" / "ledger.jsonl") if arm_dir == "codex-agyopus-run" else (R / "e1" / arm_dir / f"{r['pr']}-independent" / "ledger.jsonl")
        t = ledger_sum(led)
        invalid = r["final_verdict"] is None
        rows.append(dict(experiment="E1", variant=arm, item=r["pr"], run_url="local (no GitHub)", s6_verdict=r["final_verdict"] or "invalid",
                         expected_verdict=r["expected"], verdict_correct="" if invalid else int(r["correct_final"]),
                         false_approve="" if invalid else int(r["false_approval"]),
                         injection_obeyed=("" if invalid else int(r["obeyed_injection"])) if r["injection_seeded"] else "",
                         notes=("invalid: provider quota exhausted" if invalid else f"reviewer={r['reviewer_verdict']}; blocking={r['n_blocking']}; probes={r['probes']}; verify={r['verify']}"
                                + ("; injection noticed" if r["injection_noticed"] else "")), **t))
# --- E2
scores = [json.loads(l) for l in (R / "e2" / "scores.jsonl").read_text().splitlines()]
for sc in scores:
    n = sc["issue"]; v = sc["worktree"].rsplit("-", 1)[-1]
    d = R / "e2" / f"issue-{n}-{v}"
    s = json.loads((d / "run.json").read_text()) if (d / "run.json").exists() else json.loads((d / "summary.json").read_text())
    t = ledger_sum(d / "ledger.jsonl")
    rows.append(dict(experiment="E2", variant=v, item=f"issue-{n}", run_url="local (no GitHub)", stage_reached=s["status"],
                     s3_pass=1, s4_pass=int(s["status"] == "tests-passed"), hidden_pass=sc["hidden_passed"], hidden_total=sc["hidden_total"],
                     attempts_dev=s["attempts"].get("S3", ""), attempts_test=s["attempts"].get("S4", ""),
                     notes=f"agy gemini-3.8-flash-high; generated tests={sc['gen_tests']}; fail on reference fix={sc['gen_fail_on_reference']}", **t))
with open(R / "results.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=HEAD); w.writeheader()
    for r in rows:
        w.writerow({k: r.get(k, "") for k in HEAD})
print(len(rows), "rows")
