"""Static invariants of the workflow files (DESIGN §6 permissions, §10.1, §11; ADR-008 independence)."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

yaml = pytest.importorskip("yaml")
WF = Path(__file__).resolve().parents[1] / "github-workflows"


def load(name: str) -> dict[str, Any]:
    return yaml.safe_load((WF / name).read_text())


def test_workflow_level_permissions_are_empty() -> None:
    for name in ("autose.yml", "autose-round.yml", "ci.yml"):
        assert load(name)["permissions"] == {}, name


def test_job_permissions_match_design() -> None:
    jobs = load("autose.yml")["jobs"]
    assert jobs["gate"]["permissions"] == {"issues": "write", "pull-requests": "read", "contents": "read"}
    assert jobs["build"]["permissions"] == {"contents": "write", "pull-requests": "write", "issues": "write"}
    assert jobs["finalize"]["permissions"] == {"contents": "read", "issues": "write", "pull-requests": "write"}
    assert jobs["finalize"]["if"].startswith("always()")
    rjobs = load("autose-round.yml")["jobs"]
    assert rjobs["review"]["permissions"] == {"contents": "read", "issues": "read", "pull-requests": "read"}
    assert rjobs["post"]["permissions"] == {"contents": "read", "pull-requests": "write", "issues": "write"}
    assert rjobs["ci"]["permissions"] == {"contents": "read", "statuses": "write"}


def test_review_job_is_isolated() -> None:
    steps = load("autose-round.yml")["jobs"]["review"]["steps"]
    downloads = [s for s in steps if str(s.get("uses", "")).startswith("actions/download-artifact")]
    assert len(downloads) == 1 and "review-r${{ inputs.prev_round }}" in downloads[0]["with"]["name"]
    for s in steps:
        if str(s.get("uses", "")).startswith("actions/checkout"):
            assert s["with"]["persist-credentials"] is False
    agent = next(s for s in steps if s.get("name", "").startswith("Independent review"))
    assert "GH_TOKEN" not in agent["env"] and "GITHUB_TOKEN" not in agent["env"]
    assert "--no-github" in agent["run"]


def test_secrets_only_in_agent_steps_and_cli_pinned() -> None:
    text = (WF / "autose.yml").read_text() + (WF / "autose-round.yml").read_text()
    assert "@openai/codex@0.172.0" in text and "npm install -g @openai/codex\n" not in text
    assert "ANTHROPIC_API_KEY" not in text
    for name in ("autose.yml", "autose-round.yml"):
        for job_name, job in load(name)["jobs"].items():
            assert "CODEX_AUTH_JSON" not in str(job.get("env", {})), job_name
            for s in job.get("steps", []):
                env = str(s.get("env", {}))
                if "secrets.CODEX_AUTH_JSON }}" in env:  # the value itself, not the `!= ''` presence flag
                    # the credential only reaches tokenless agent/canary steps (ADR-005, ADR-014)
                    assert "GH_TOKEN" not in env and "GITHUB_TOKEN" not in env, (job_name, s.get("name"))
                    assert "codex-home" in s["run"], (job_name, s.get("name"))


def test_concurrency_groups() -> None:
    wf = load("autose.yml")
    group = wf["concurrency"]["group"]
    assert "autose-noop-" in group and "author_association" in group and wf["concurrency"]["cancel-in-progress"] is False
    for name, job in wf["jobs"].items():
        assert "concurrency" not in job, name  # job-level groups could cancel another run's pending rounds
    assert wf["jobs"]["round3"]["with"]["final"] is True


def _agent_jobs() -> list[tuple[str, dict[str, Any]]]:
    return [("build", load("autose.yml")["jobs"]["build"]), ("rework", load("autose-round.yml")["jobs"]["rework"]),
            ("review", load("autose-round.yml")["jobs"]["review"])]


def test_agent_steps_have_no_github_token_and_publish_steps_have_no_model_key() -> None:
    for name, job in _agent_jobs():
        for s in job["steps"]:
            env = s.get("env", {})
            if "ANTHROPIC_API_KEY" in env:
                assert "GH_TOKEN" not in env and "GITHUB_TOKEN" not in env, (name, s.get("name"))
            if "GH_TOKEN" in env:
                assert "ANTHROPIC_API_KEY" not in env, (name, s.get("name"))
    for name in ("build", "rework"):
        runs = " ".join(s.get("run", "") for s in dict(_agent_jobs())[name]["steps"])
        assert "--phase prepare" in runs and "--phase agent" in runs and "--phase publish" in runs


def test_sandbox_prerequisites_installed_in_every_agent_job() -> None:
    for name, job in _agent_jobs():
        steps = [s for s in job["steps"] if "bubblewrap" in s.get("run", "")]
        assert steps and steps[0]["if"] == "vars.AUTOSE_SANDBOX == '1'", name


def test_post_and_finalize_can_read_contents() -> None:
    assert load("autose-round.yml")["jobs"]["post"]["permissions"]["contents"] == "read"
    assert load("autose.yml")["jobs"]["finalize"]["permissions"]["contents"] == "read"
