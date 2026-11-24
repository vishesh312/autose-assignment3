"""Regression tests for the hardening pass (independent audit of workflow/)."""
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import time
from pathlib import Path
from typing import Any

import pytest

from autose import checks, cli, config, github, pipeline, render, review
from autose.agent import FakeRunner


def _issue(fx: Path) -> pipeline.IssueInput:
    return cli.parse_issue_file(fx / "issue-42.md", None)


# ---- #3a run cap keeps the review reserve; #6 artifacts outside the working tree

def test_build_never_spends_the_review_reserve(tinydb_repo: Path, pop_fixture: Path, tmp_path: Path) -> None:
    p = pipeline.Pipeline(_issue(pop_fixture), tinydb_repo, tmp_path / "home", FakeRunner(pop_fixture), "python",
                          reserve_usd=config.review_reserve())
    p.state.cost_usd = 10.0 - 2.5 - 0.75 + 0.01  # one cent too much for the Analyst under the $2.50 reserve
    with pytest.raises(pipeline.Stop, match="review reserve"):
        p.requirements()
    assert "## Stop reason" in (p.dir / "spec.md").read_text()


def test_home_inside_repo_is_rejected(tinydb_repo: Path, pop_fixture: Path) -> None:
    with pytest.raises(ValueError, match="outside the working tree"):
        pipeline.Pipeline(_issue(pop_fixture), tinydb_repo, tinydb_repo / ".autose-home", FakeRunner(pop_fixture),
                          "python")


def test_review_dirs_must_be_separate(tmp_path: Path, pop_fixture: Path) -> None:
    inp = review.ReviewInput(42, "t", "b", [], "", "base", "head")
    repo = tmp_path / "repo"
    repo.mkdir()
    with pytest.raises(ValueError, match="outside the reviewed checkout"):
        review.run_review(inp, repo, repo / "out", FakeRunner(pop_fixture), tmp_path / "probes")
    with pytest.raises(ValueError, match="separate"):
        review.run_review(inp, repo, tmp_path / "out", FakeRunner(pop_fixture), tmp_path / "out" / "probes")


# ---- #3b / #14 re-ask needs budget and time; #7 invalid header

def test_reask_guard() -> None:
    assert review.can_reask(7.9, 2.0, 1200, None) is None
    assert "exceeds" in (review.can_reask(8.1, 2.0, 1200, None) or "")
    assert "job time" in (review.can_reask(0, 2.0, 1200, time.time() + 600) or "")


def test_invalid_review_when_no_budget_for_reask(tmp_path: Path, pop_fixture: Path) -> None:
    shutil.copyfile(pop_fixture / "script_review.json", pop_fixture / "script.json")
    inp = review.ReviewInput(42, "t", "b", [], "diff", "base", "head")
    repo = tmp_path / "repo"
    repo.mkdir()
    out = tmp_path / "out"
    meta = review.run_review(inp, repo, out, FakeRunner(pop_fixture), tmp_path / "probes", spent_usd=8.5)
    assert not meta["valid"] and any("no re-ask" in p for p in meta["problems"])
    md = (out / "review.md").read_text()
    assert "INVALID REVIEW (not an approval)" in md and "**APPROVE**" not in md
    d = review.decide_post(meta, json.loads((out / "review.json").read_text()), final=False, ci_result="success",
                           current_head="head")
    assert d.verdict == "awaiting-human" and d.route == "" and d.post


# ---- #5 index bypass and final gate

def test_commit_ignores_agent_staging_and_final_gate(tinydb_repo: Path, pop_fixture: Path, tmp_path: Path) -> None:
    p = pipeline.Pipeline(_issue(pop_fixture), tinydb_repo, tmp_path / "home", FakeRunner(pop_fixture), "python")
    p.state.base_sha = checks.git(tinydb_repo, "rev-parse", "HEAD").strip()
    subprocess.run(["git", "apply", str(pop_fixture / "impl_full.patch")], cwd=tinydb_repo, check=True)
    (tinydb_repo / "pyproject.toml").write_text("# hijacked\n")
    checks.git(tinydb_repo, "add", "pyproject.toml")  # what an agent with `git add` could do
    p.commit("autose: test")
    assert cli.final_gate(tinydb_repo, p.state.base_sha, 42) == []
    assert checks.committed_paths(tinydb_repo, p.state.base_sha) == ["tinydb/table.py"]
    checks.git(tinydb_repo, "-c", "user.name=x", "-c", "user.email=x@x", "commit", "-qam", "sneak")
    assert cli.final_gate(tinydb_repo, p.state.base_sha, 42) == ["pyproject.toml"]


def test_ignored_files_are_still_seen(tinydb_repo: Path) -> None:
    base = checks.git(tinydb_repo, "rev-parse", "HEAD").strip()
    (tinydb_repo / ".git" / "info").mkdir(exist_ok=True)
    (tinydb_repo / ".git" / "info" / "exclude").write_text("hidden.py\n")
    (tinydb_repo / "hidden.py").write_text("x = 1\n")
    assert "hidden.py" in checks.dirty_paths(tinydb_repo, base)


def test_git_hooks_are_disabled(tinydb_repo: Path, tmp_path: Path) -> None:
    hook = tinydb_repo / ".git" / "hooks" / "pre-commit"
    marker = tmp_path / "hook-ran"
    hook.write_text(f"#!/bin/sh\ntouch {marker}\n")
    hook.chmod(hook.stat().st_mode | stat.S_IEXEC)
    (tinydb_repo / "tinydb" / "x.py").write_text("y = 1\n")
    checks.git(tinydb_repo, "add", "tinydb/x.py")
    checks.git(tinydb_repo, "-c", "user.name=x", "-c", "user.email=x@x", "commit", "-qm", "x")
    assert not marker.exists()


def test_check_subprocesses_get_a_scrubbed_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    for k in ("GH_TOKEN", "GITHUB_OUTPUT", "ACTIONS_RUNTIME_TOKEN"):
        monkeypatch.setenv(k, "secret")
    code, out = checks.run(["env"], tmp_path)
    assert code == 0 and "secret" not in out


# ---- #4 agent step offline, refuses a token

def test_build_agent_phase_offline(tinydb_repo: Path, tinydb_python: str, pop_fixture: Path, tmp_path: Path,
                                   monkeypatch: pytest.MonkeyPatch) -> None:
    home = tmp_path / "home"
    inp = home / "issue-42" / "input"
    inp.mkdir(parents=True)
    issue = _issue(pop_fixture)
    (inp / "issue.json").write_text(json.dumps({"number": 42, "title": issue.title, "body": issue.body,
                                                "maintainer_comments": []}))
    (inp / "branch.json").write_text(json.dumps({"exists": False, "human_commits": []}))
    argv = ["--home", str(home), "--python", tinydb_python, "--fake", str(pop_fixture), "build", "--phase", "agent",
            "--issue", "42", "--repo-dir", str(tinydb_repo)]
    monkeypatch.setenv("GH_TOKEN", "x")
    with pytest.raises(SystemExit, match="refusing"):
        cli.main(argv)
    monkeypatch.delenv("GH_TOKEN")
    assert cli.main(argv) == 0
    state = json.loads((home / "issue-42" / "state.json").read_text())
    assert state["status"] == "tests-passed" and state["head_sha"]
    assert checks.git(tinydb_repo, "rev-parse", "--abbrev-ref", "HEAD").strip() == "autose/issue-42"
    assert cli.final_gate(tinydb_repo, state["base_sha"], 42) == []
    assert checks.committed_paths(tinydb_repo, state["base_sha"]) == ["tests/test_autose_issue_42.py",
                                                                      "tinydb/table.py"]


def test_human_commits_stop_the_agent_step(tinydb_repo: Path, pop_fixture: Path, tmp_path: Path) -> None:
    home = tmp_path / "home"
    inp = home / "issue-42" / "input"
    inp.mkdir(parents=True)
    (inp / "issue.json").write_text(json.dumps({"number": 42, "title": "t", "body": "b", "maintainer_comments": []}))
    (inp / "branch.json").write_text(json.dumps({"exists": True, "human_commits": ["abc12345 by alice"]}))
    cli.main(["--home", str(home), "--fake", str(pop_fixture), "build", "--phase", "agent", "--issue", "42",
              "--repo-dir", str(tinydb_repo)])
    state = json.loads((home / "issue-42" / "state.json").read_text())
    assert state["status"] == "stopped" and "not authored by the bot" in state["stop_reason"]


# ---- #11 design reset before the Architect; #16 kept tests that stop failing on base

def test_design_revisit_resets_before_architect(tinydb_repo: Path, pop_fixture: Path, tmp_path: Path,
                                                monkeypatch: pytest.MonkeyPatch) -> None:
    p = pipeline.Pipeline(_issue(pop_fixture), tinydb_repo, tmp_path / "home", FakeRunner(pop_fixture), "python")
    p.state.base_sha = checks.git(tinydb_repo, "rev-parse", "HEAD").strip()
    shutil.copyfile(pop_fixture / "spec.json", p.dir / "spec.json")
    (p.dir / "design.md").write_text("old design")
    subprocess.run(["git", "apply", str(pop_fixture / "impl_buggy.patch")], cwd=tinydb_repo, check=True)
    seen: list[list[str]] = []
    monkeypatch.setattr(p, "design", lambda spec, loop="": seen.append(checks.dirty_paths(tinydb_repo, p.state.base_sha)))
    p.revisit_design(json.loads((pop_fixture / "spec.json").read_text()), "tests failed")
    assert seen == [[]]


def test_kept_tests_failing_fob_go_back_to_tester(tinydb_repo: Path, tinydb_python: str, pop_fixture: Path,
                                                  tmp_path: Path) -> None:
    home = tmp_path / "home"
    assert cli.main(["--home", str(home), "--python", tinydb_python, "--fake", str(pop_fixture), "local",
                     "--issue-file", str(pop_fixture / "issue-42.md"), "--repo", str(tinydb_repo)]) == 0
    shutil.copyfile(pop_fixture / "vacuous_tests.py.txt", tinydb_repo / config.tester_file(42))
    (pop_fixture / "script.json").write_text(json.dumps({
        "developer": [{"output": "dev2.json", "write": {"tinydb/autose_extra.py": "extra_module.py.txt"}}],
        "tester": [{"output": "test_map.json", "write": {"tests/test_autose_issue_42.py": "issue42_tests.py.txt"}}]}))
    runner = FakeRunner(pop_fixture)
    p = pipeline.Pipeline(_issue(pop_fixture), tinydb_repo, home, runner, tinydb_python)
    rv = json.loads((pop_fixture / "review_ok.json").read_text())
    p.run_rework("S3", rv)
    assert [c.role.name for c in runner.calls] == ["developer", "tester"]
    assert "kept tests failed" in runner.calls[1].task and p.state.status == "tests-passed"


# ---- #9 permission lookups fail loudly; #18 bot-only sticky comment with append-only timeline

class _GH(github.GitHub):
    def __init__(self, responses: dict[str, Any]) -> None:
        super().__init__("o/r")
        self.responses = responses
        self.calls: list[tuple[str, Any]] = []

    def api(self, path: str, *args: str, input_json: Any = None) -> Any:
        self.calls.append((path, input_json))
        r = self.responses.get(path)
        if isinstance(r, Exception):
            raise r
        return r

    def api_paginated(self, path: str) -> list[Any]:
        return self.responses.get(path, [])


def test_permission_only_404_means_none() -> None:
    gh = _GH({"repos/o/r/collaborators/a/permission": github.GitHubError("HTTP 404: Not Found"),
              "repos/o/r/collaborators/b/permission": github.GitHubError("HTTP 502: Bad Gateway")})
    assert gh.permission("a") == "none"
    with pytest.raises(github.GitHubError):
        gh.permission("b")


def test_status_comment_is_bot_only_and_append_only() -> None:
    bot = {"login": config.BOT_NAME, "type": "Bot"}
    old = render.status_comment(github.STATUS_MARKER, 7, "running", ["- 10:00 build: started"], pr_url="http://pr/1")
    comments = [{"id": 1, "user": {"login": "mallory", "type": "User"}, "body": github.STATUS_MARKER + " fake"},
                {"id": 2, "user": bot, "body": old}]
    gh = _GH({"repos/o/r/issues/7/comments": comments})
    cli.update_status(gh, 7, "awaiting-human", ["- 10:05 round 1: review approve", "- 10:00 build: started"])
    path, payload = gh.calls[-1]
    assert path == "repos/o/r/issues/comments/2"
    body = payload["body"]
    assert body.count("10:00 build: started") == 1 and "10:05 round 1" in body
    assert body.index("10:00") < body.index("10:05") and "PR: http://pr/1" in body and "awaiting-human" in body


# ---- #19 the canary goes through the production argv builder

def test_canary_uses_production_argv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    log = tmp_path / "argv.jsonl"
    stub = tmp_path / "claude"
    stub.write_text(f"""#!/usr/bin/env python3
import json, sys
sys.stdin.read()
open({str(log)!r}, "a").write(json.dumps(sys.argv[1:]) + "\\n")
print(json.dumps({{"subtype": "success", "structured_output": {{"answer": "4"}}, "total_cost_usd": 0.001}}))
""")
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("AUTOSE_CLAUDE", str(stub))
    monkeypatch.setenv("AUTOSE_BACKEND", "claude")
    assert cli.main(["--home", str(tmp_path / "home"), "canary"]) == 0
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(calls) == 2
    for argv in calls:
        for flag in ("--bare", "--restricted", "--strict-mcp-config", "--max-turns", "--append-system-prompt-file",
                     "--json-schema", "--permission-mode"):
            assert flag in argv
        assert argv[argv.index("--max-turns") + 1] == "2"
    assert os.path.exists(tmp_path / "home" / "canary.json")
