"""End-to-end FakeRunner runs of ``autose local`` (E2) and ``autose review-local`` (E1) on a tinydb copy.

The 'add Table.pop' fixture exercises S1 -> S4: the first Developer attempt is buggy, the
Tester's AC-2 test fails, the orchestrator routes back to S3 with the failing id, the
second attempt passes the suite, mypy and the fails-on-base check.
"""
from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from autose import cli


def _run(argv: list[str]) -> int:
    return cli.main(argv)


def test_local_split_full_path_with_retry(tinydb_repo: Path, tinydb_python: str, pop_fixture: Path,
                                          tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    calls: list = []
    real = cli.make_runner

    def recording(fake: str | None):  # keep a handle on the FakeRunner to inspect hand-offs
        r = real(fake)
        calls.append(r)
        return r
    monkeypatch.setattr(cli, "make_runner", recording)
    home = tmp_path / "home"
    rc = _run(["--home", str(home), "--python", tinydb_python, "--fake", str(pop_fixture), "local",
               "--issue-file", str(pop_fixture / "issue-42.md"), "--repo", str(tinydb_repo), "--stages", "1-4"])
    d = home / "issue-42"
    summary = json.loads((d / "summary.json").read_text())
    assert rc == 0, summary
    assert summary["status"] == "tests-passed"
    assert summary["attempts"]["S3"] == 2 and summary["attempts"]["S4"] == 1
    for name in ("spec.md", "spec.json", "judge.json", "design.md", "design.json", "diff.patch",
                 "dev_notes.json", "test_map.json", "test_report.md", "ledger.jsonl", "state.json"):
        assert (d / name).exists(), name
    assert "def pop" in (d / "diff.patch").read_text()
    report = (d / "test_report.md").read_text()
    assert "fail on base" in report and "test_ac2_pop_missing_id_raises_keyerror" in report

    runner = calls[0]
    by_role = {}
    for c in runner.calls:
        by_role.setdefault(c.role.name, []).append(c.task)
    # S1 saw the untrusted issue, single-pass templating kept "{{DIFF}}" literal and the fence intact
    assert "{{DIFF}}" in by_role["analyst"][0] and by_role["analyst"][0].count("</untrusted_issue>") == 1
    # retry context carries the failing test id to the second Developer attempt (DESIGN §4)
    assert "test_ac2_pop_missing_id_raises_keyerror" in by_role["developer"][1]
    assert by_role["developer"][0].count("<retry_context>\n\n</retry_context>") == 1
    # the Tester never sees the Developer's notes or the raw issue (ADR-003)
    assert "DEVNOTE-SECRET" not in by_role["tester"][0] and "dict.pop" not in by_role["tester"][0]
    assert "dict.pop" not in by_role["developer"][0]  # write-capable agents never see the raw issue

    events = [json.loads(line) for line in (d / "ledger.jsonl").read_text().splitlines()]
    assert any(e["event"] == "route" and "-> S3" in e["reason"] for e in events)
    assert all("cache_write" in e for e in events)
    state = json.loads((d / "state.json").read_text())
    assert state["cost_usd"] == pytest.approx(0.2 + 0.01 + 0.2 + 0.5 + 0.5 + 0.3)


def test_local_single_builder_from_frozen(tinydb_repo: Path, tinydb_python: str, pop_fixture: Path,
                                          tmp_path: Path) -> None:
    shutil.copyfile(pop_fixture / "script_single.json", pop_fixture / "script.json")
    home = tmp_path / "home"
    rc = _run(["--home", str(home), "--python", tinydb_python, "--fake", str(pop_fixture), "local",
               "--issue-file", str(pop_fixture / "issue-42.md"), "--repo", str(tinydb_repo), "--stages", "3-4",
               "--freeze-dir", str(pop_fixture), "--variant", "single"])
    summary = json.loads((home / "issue-42" / "summary.json").read_text())
    assert rc == 0 and summary["status"] == "tests-passed" and summary["attempts"]["S3"] == 1


def test_local_stops_when_tests_never_pass(tinydb_repo: Path, tinydb_python: str, pop_fixture: Path,
                                           tmp_path: Path) -> None:
    """Frozen design, buggy implementation twice: the same failing set triggers no-progress -> stop."""
    script = json.loads((pop_fixture / "script.json").read_text())
    script["developer"] = [{"output": "dev1.json", "patch": "impl_buggy.patch"},
                           {"output": "dev1.json", "write": {"tinydb/__init__.py": "issue-42.md"}}]
    (pop_fixture / "script.json").write_text(json.dumps(script))
    # second attempt breaks the package -> S3 build failure; third would be needed but no-progress/caps apply
    home = tmp_path / "home"
    rc = _run(["--home", str(home), "--python", tinydb_python, "--fake", str(pop_fixture), "local",
               "--issue-file", str(pop_fixture / "issue-42.md"), "--repo", str(tinydb_repo), "--stages", "3-4",
               "--freeze-dir", str(pop_fixture)])
    d = home / "issue-42"
    summary = json.loads((d / "summary.json").read_text())
    assert rc == 1 and summary["status"] == "stopped"
    assert "## Stop reason" in (d / "test_report.md").read_text()


def test_review_local_reasks_invalid_then_accepts(tinydb_repo: Path, tinydb_python: str, pop_fixture: Path,
                                                  tmp_path: Path) -> None:
    shutil.copyfile(pop_fixture / "script_review.json", pop_fixture / "script.json")
    pr_dir = tmp_path / "seeded-1"
    pr_dir.mkdir()
    shutil.copyfile(pop_fixture / "issue-42.md", pr_dir / "issue.md")
    (pr_dir / "diff.patch").write_text((pop_fixture / "impl_full.patch").read_text()
                                       + (pop_fixture / "tests.patch").read_text())
    (pr_dir / "friendly_context").mkdir()
    (pr_dir / "friendly_context" / "spec.md").write_text("FRIENDLY-SPEC")
    home = tmp_path / "home"
    base = ["--home", str(home), "--python", tinydb_python, "--fake", str(pop_fixture), "review-local",
            "--pr-dir", str(pr_dir), "--repo", str(tinydb_repo), "--issue", "42"]
    assert _run(base) == 0
    out = home / "review-local" / "seeded-1-independent"
    meta = json.loads((out / "review_meta.json").read_text())
    assert meta["valid"] and meta["variant"] == "independent"
    assert "APPROVE" in (out / "review.md").read_text()
    tasks = sorted((out / "logs").glob("*.task.md"))
    assert len(tasks) == 2 and "rejected by the orchestrator" in tasks[1].read_text()
    assert "FRIENDLY-SPEC" not in tasks[0].read_text()
    assert "def pop" in tasks[0].read_text()  # the diff reached the reviewer
    # the user's checkout is untouched and the throwaway worktree is gone
    assert (tinydb_repo / "tinydb" / "table.py").read_text().count("def pop") == 0
    assert _run(base + ["--variant", "friendly"]) == 0
    ftask = next((home / "review-local" / "seeded-1-friendly" / "logs").glob("*.task.md")).read_text()
    assert "FRIENDLY-SPEC" in ftask


def test_rework_routes_after_review(tinydb_repo: Path, tinydb_python: str, pop_fixture: Path,
                                    tmp_path: Path) -> None:
    """Send-backs (ADR-013): S3 keeps the Tester's tests; S4 asks the Tester to revise them."""
    from autose import pipeline
    from autose.agent import FakeRunner

    home = tmp_path / "home"
    assert _run(["--home", str(home), "--python", tinydb_python, "--fake", str(pop_fixture), "local",
                 "--issue-file", str(pop_fixture / "issue-42.md"), "--repo", str(tinydb_repo)]) == 0
    review = json.loads((pop_fixture / "review_ok.json").read_text())
    review.update(verdict="changes_requested", findings=[
        {"id": "F-1", "severity": "blocking", "category": "code", "file": "tinydb/table.py", "line": 430,
         "description": "CODE-FINDING", "evidence": "probe output", "suggested_fix": "fix"}])
    (pop_fixture / "script.json").write_text(json.dumps({
        "developer": [{"output": "dev2.json", "write": {"tinydb/autose_extra.py": "extra_module.py.txt"}}],
        "tester": [{"output": "test_map.json", "write": {"tests/test_autose_issue_42.py": "issue42_tests.py.txt"}}]}))
    runner = FakeRunner(pop_fixture)
    issue = cli.parse_issue_file(pop_fixture / "issue-42.md", None)
    p = pipeline.Pipeline(issue, tinydb_repo, home, runner, tinydb_python)
    p.run_rework("S3", review)
    assert [c.role.name for c in runner.calls] == ["developer"]
    assert "CODE-FINDING" in runner.calls[0].task
    assert p.state.status == "tests-passed" and p.state.send_backs == 1 and p.state.round == 1
    review["findings"][0].update(category="tests", description="TESTS-FINDING")
    p.run_rework("S4", review)
    assert [c.role.name for c in runner.calls] == ["developer", "tester"]
    assert "TESTS-FINDING" in runner.calls[1].task and p.state.send_backs == 2
