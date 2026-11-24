"""Offline tests for the subscription backends (ADR-014): no real CLI is called."""
from __future__ import annotations

import json
import stat
from pathlib import Path

import jsonschema
import pytest

from autose import agent, backends, config

SCHEMA = {"type": "object", "properties": {"a": {"type": "integer"}, "note": {"type": "string"}},
          "required": ["a"], "additionalProperties": False}


def test_strict_schema_makes_optional_fields_nullable_and_required() -> None:
    s = backends._strict(SCHEMA)
    assert s["required"] == ["a", "note"] and s["properties"]["note"]["type"] == ["string", "null"]
    jsonschema.validate({"a": 1, "note": None}, s)
    # every real schema survives the transform and stays a valid JSON schema
    for f in config.SCHEMAS_DIR.glob("*.schema.json"):
        jsonschema.Draft202012Validator.check_schema(backends._strict(json.loads(f.read_text())))


def test_parse_codex_events_success_usage_and_nulls_dropped() -> None:
    events = "\n".join(json.dumps(e) for e in [
        {"type": "thread.started"},
        {"type": "item.completed", "item": {"type": "command_execution", "command": "ls"}},
        {"type": "item.completed", "item": {"type": "agent_message", "text": '{"a": 3, "note": null}'}},
        {"type": "turn.completed", "usage": {"input_tokens": 1000, "cached_input_tokens": 400,
                                             "output_tokens": 50, "reasoning_output_tokens": 10}},
    ])
    env = backends.parse_codex_events(events, "", "gpt-6.1-sol")
    res = agent.parse_envelope(env, SCHEMA, model="gpt-6.1-sol")
    assert res.ok and res.output == {"a": 3}
    assert (res.tokens_in, res.cache_read, res.tokens_out, res.num_turns) == (600, 400, 60, 1)
    assert res.cost_usd == pytest.approx((600 * 2.5 + 400 * 0.25 + 60 * 15) / 1e6)


def test_parse_codex_events_failure_is_error() -> None:
    env = backends.parse_codex_events(json.dumps({"type": "turn.failed", "error": {"message": "usage limit"}}), "", "m")
    res = agent.parse_envelope(env, SCHEMA, fallback_cost=1.0)
    assert not res.ok and "usage limit" in (res.error or "")
    assert backends.parse_codex_events("", "", "m")["is_error"]  # no completed turn


def test_parse_agy_envelope() -> None:
    raw = {"status": "SUCCESS", "response": '{"a":1}', "num_turns": 2, "structured_output": {"a": 1},
           "duration_seconds": 3.5, "usage": {"input_tokens": 100, "output_tokens": 5, "thinking_tokens": 5,
                                              "cache_read_tokens": 900}}
    res = agent.parse_envelope(backends.parse_agy_envelope(json.dumps(raw), "claude-opus-4-6-thinking"), SCHEMA)
    assert res.ok and res.output == {"a": 1} and res.tokens_out == 10 and res.cache_read == 900
    bad = backends.parse_agy_envelope(json.dumps({"status": "ERROR", "response": "boom"}), "m")
    assert bad["is_error"]
    assert backends.parse_agy_envelope("not json", "m", 2, "err")["subtype"] == "error_unparseable"


def _codex_stub(tmp_path: Path) -> Path:
    log = tmp_path / "argv.json"
    stub = tmp_path / "codex"
    stub.write_text(f"""#!/usr/bin/env python3
import json, os, sys
args = sys.argv[1:]
stdin = sys.stdin.read()
json.dump({{"argv": args, "stdin": stdin, "env": dict(os.environ)}}, open({str(log)!r}, "w"))
open(args[args.index("-o") + 1], "w").write('{{"a": 7}}')
print(json.dumps({{"type": "turn.completed", "usage": {{"input_tokens": 10, "output_tokens": 2}}}}))
""")
    stub.chmod(stub.stat().st_mode | stat.S_IEXEC)
    return stub


@pytest.mark.parametrize("role_name,sandbox", [("architect", "read-only"), ("developer", "workspace-write")])
def test_codex_runner_argv(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, role_name: str, sandbox: str) -> None:
    monkeypatch.setenv("GH_TOKEN", "secret")
    stub = _codex_stub(tmp_path)
    role = config.role(role_name)
    call = agent.AgentCall(role=role, system_prompt="SYS <x>", task="TASK", schema=SCHEMA, cwd=tmp_path,
                           log_dir=tmp_path / "logs", label="c", add_dirs=["/probe"])
    res = agent.run_agent(backends.CodexRunner(str(stub)), call)
    seen = json.loads((tmp_path / "argv.json").read_text())
    argv = seen["argv"]
    assert res.ok and res.output == {"a": 7}
    assert argv[0] == "exec" and argv[-1] == "-" and seen["stdin"] == "TASK" and "TASK" not in argv
    assert argv[argv.index("-s") + 1] == sandbox and argv[argv.index("-m") + 1] == role.model
    for flag in ("--ephemeral", "--ignore-user-config", "--ignore-rules", "--output-schema", "--json"):
        assert flag in argv
    assert "project_doc_max_bytes=0" in argv and "approval_policy=never" in argv
    assert 'developer_instructions="SYS <x>"' in argv
    assert argv[argv.index("--add-dir") + 1] == "/probe"
    assert "GH_TOKEN" not in seen["env"]


def test_routing_runner_dispatches_per_role(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    seen: list[str] = []

    class Rec:
        def __init__(self, name: str) -> None:
            self.name = name

        def invoke(self, call: agent.AgentCall) -> dict:
            seen.append(self.name)
            return {"subtype": "success", "structured_output": {"a": 1}}

    monkeypatch.setenv("AUTOSE_BACKEND", "codex")
    monkeypatch.setenv("AUTOSE_BACKEND_REVIEWER", "agy")
    r = backends.RoutingRunner({"codex": Rec("codex"), "agy": Rec("agy")})
    for name in ("developer", "reviewer"):
        call = agent.AgentCall(role=config.role(name), system_prompt="", task="", schema=SCHEMA, cwd=tmp_path,
                               log_dir=tmp_path, label=name)
        assert agent.run_agent(r, call).ok
    assert seen == ["codex", "agy"]
