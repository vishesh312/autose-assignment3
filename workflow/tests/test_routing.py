"""Routing table, caps, no-progress, reservation, post-review and gate decisions (DESIGN §2.1, §10, ADR-010)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

from autose import cli, config, pipeline, review
from autose.pipeline import Counters, Fingerprint, next_stage

FX = Path(__file__).parent / "fixtures" / "pop"


@pytest.mark.parametrize("stage,outcome,c,expected", [
    ("S1", "pass", Counters(), "S2"),
    ("S1", "fail", Counters(spec_attempts=1), "S1"),
    ("S1", "fail", Counters(spec_attempts=2), "stop"),
    ("S1", "blocking", Counters(spec_attempts=1), "needs-info"),
    ("S2", "fail", Counters(design_attempts=1), "S2"),
    ("S2", "fail", Counters(design_attempts=2), "stop"),
    ("S3", "fail", Counters(dev_attempts=1), "S3"),
    ("S3", "fail", Counters(dev_attempts=3), "S2"),
    ("S3", "fail", Counters(dev_attempts=3, design_revisits=1), "stop"),
    ("S3", "fail", Counters(dev_attempts=3, can_revisit_design=False), "stop"),
    ("S4", "suite_fail", Counters(dev_attempts=2), "S3"),
    ("S4", "suite_fail", Counters(dev_attempts=3), "S2"),
    ("S4", "tester_fail", Counters(tester_attempts=1), "S4"),
    ("S4", "tester_fail", Counters(tester_attempts=2), "stop"),
    ("S4", "contested", Counters(), "S4"),
    ("S4", "no_progress", Counters(dev_attempts=1), "S2"),
    ("S3", "no_progress", Counters(dev_attempts=1, design_revisits=1), "stop"),
    ("S4", "pass", Counters(), "S5"),
    ("S5", "fail", Counters(), "stop"),
])
def test_next_stage_table(stage: str, outcome: str, c: Counters, expected: str) -> None:
    assert next_stage(stage, outcome, c) == expected


def test_caps_match_design() -> None:
    assert (config.SPEC_ATTEMPTS, config.DESIGN_ATTEMPTS, config.DEV_ATTEMPTS, config.TESTER_ATTEMPTS,
            config.DESIGN_REVISITS, config.MAX_SEND_BACKS) == (2, 2, 3, 2, 1, 2)
    assert config.RUN_CAP_USD == 10.0


def test_no_progress() -> None:
    a = Fingerprint("h1", frozenset({"t1"}))
    assert not pipeline.no_progress(None, a)
    assert pipeline.no_progress(a, Fingerprint("h1", frozenset({"t2"})))      # same diff
    assert pipeline.no_progress(a, Fingerprint("h2", frozenset({"t1"})))      # same failing set
    assert not pipeline.no_progress(a, Fingerprint("h2", frozenset({"t2"})))
    assert not pipeline.no_progress(Fingerprint("h1"), Fingerprint("h2"))     # build failures: diff only


def test_rework_reservation() -> None:
    # ADR-015: the review reserve is one reviewer cap (2.00) + one verifier cap (0.50) = 2.50.
    assert config.review_reserve() == 2.5
    # S3 rework: developer 1.50 + tester 1.00 + review reserve 2.50 = 5.00 under $10
    assert pipeline.rework_affordable(5.0, "S3") == (True, 5.0)
    assert not pipeline.rework_affordable(5.1, "S3")[0]
    # S2 rework adds the architect (0.75): 5.75, so the first approach send-back still fits after a
    # typical $2.85 run (8.60 <= 10); the verifier cap costs every send-back $0.50 of headroom.
    assert pipeline.rework_affordable(4.25, "S2")[0] and not pipeline.rework_affordable(4.3, "S2")[0]
    assert pipeline.rework_affordable(2.85, "S2")[0]


def test_review_reserve_without_verification(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AUTOSE_VERIFY", "0")  # skipping verification gives the $0.50 back (pre-ADR-015 numbers)
    assert config.review_reserve() == 2.0 and pipeline.rework_affordable(5.5, "S3") == (True, 4.5)


def _rv(name: str) -> dict[str, Any]:
    return json.loads((FX / name).read_text())


def test_decide_post() -> None:
    ok = _rv("review_ok.json")
    meta = {"head_sha": "abc", "valid": True}
    assert review.decide_post(meta, ok, final=False, ci_result="failure", current_head="abc").verdict == "stopped"
    assert review.decide_post(meta, ok, final=False, ci_result="success", current_head="def").verdict == "stale"
    assert review.decide_post(None, None, final=False, ci_result="success", current_head="abc").verdict == \
        "awaiting-human"
    d = review.decide_post({**meta, "valid": False}, _rv("review_bad.json"), final=False, ci_result="success",
                           current_head="abc")
    assert d.verdict == "awaiting-human" and d.route == ""
    assert review.decide_post(meta, ok, final=False, ci_result="success", current_head="abc").verdict == "approve"
    cr = {**ok, "verdict": "changes_requested", "findings": [
        {"id": "F-1", "severity": "blocking", "category": "code", "file": "tinydb/table.py", "line": 1,
         "description": "d", "evidence": "e", "suggested_fix": "f"}]}
    d = review.decide_post(meta, cr, final=False, ci_result="success", current_head="abc")
    assert (d.verdict, d.route) == ("changes_requested", "S3")
    d = review.decide_post(meta, cr, final=True, ci_result="success", current_head="abc")
    assert (d.verdict, d.route) == ("final", "")


class FakeGH:
    def __init__(self, writers: set[str], prs: dict[int, dict[str, Any]] | None = None) -> None:
        self.writers, self.prs = writers, prs or {}

    def can_write(self, user: str) -> bool:
        return user in self.writers

    def pr(self, number: int) -> dict[str, Any]:
        return self.prs[number]


def _ev(sender: str = "alice", **kw: Any) -> dict[str, Any]:
    return {"sender": {"login": sender, "type": "User"}, **kw}


def test_gate_label_and_comment_on_issue() -> None:
    gh = FakeGH({"alice"})
    out = cli.decide_gate("issues", _ev(action="labeled", label={"name": "autose"}, issue={"number": 3}), gh)
    assert (out["proceed"], out["mode"], out["issue"]) == ("true", "full", "3")
    assert cli.decide_gate("issues", _ev(action="labeled", label={"name": "bug"}, issue={"number": 3}),
                           gh)["proceed"] == "false"
    out = cli.decide_gate("issue_comment", _ev(action="created", comment={"body": "/autose\nplease"},
                                               issue={"number": 3}), gh)
    assert out["mode"] == "full"
    assert cli.decide_gate("issue_comment", _ev(action="created", comment={"body": "nice /autose"},
                                                issue={"number": 3}), gh)["proceed"] == "false"
    assert cli.decide_gate("issue_comment", _ev("mallory", action="created", comment={"body": "/autose"},
                                                issue={"number": 3}), gh)["proceed"] == "false"
    bot = {"sender": {"login": "github-actions[bot]", "type": "Bot"}, "action": "created",
           "comment": {"body": "/autose"}, "issue": {"number": 3}}
    assert cli.decide_gate("issue_comment", bot, FakeGH({"github-actions[bot]"}))["reason"] == "bot sender"


def test_gate_on_pull_requests() -> None:
    prs = {
        10: {"isCrossRepository": False, "state": "OPEN", "headRefName": "autose/issue-3", "headRefOid": "h",
             "body": ""},
        11: {"isCrossRepository": True, "state": "OPEN", "headRefName": "x", "headRefOid": "h", "body": ""},
        12: {"isCrossRepository": False, "state": "OPEN", "headRefName": "seeded/a", "headRefOid": "s",
             "body": "Fixes #4"},
    }
    gh = FakeGH({"alice"}, prs)

    def comment(n: int, body: str) -> dict[str, str]:
        return cli.decide_gate("issue_comment", _ev(action="created", comment={"body": body},
                                                    issue={"number": n, "pull_request": {}}), gh)
    out = comment(10, "/autose")
    assert (out["mode"], out["issue"], out["pr"]) == ("review", "3", "10")  # canonical issue
    assert "forks" in comment(11, "/autose review")["reason"]
    out = comment(12, "/autose review")
    assert (out["mode"], out["issue"], out["pr"], out["head_sha"]) == ("review", "4", "12", "s")
    assert comment(12, "/autose")["proceed"] == "false"
