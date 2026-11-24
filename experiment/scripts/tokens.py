#!/usr/bin/env python3
"""Sum ledger.jsonl files into the tables of results/tokens.md.

usage: tokens.py <kind>:<item>:<ledger path> [...]
  kind = pipeline | E1 | E2 | canary. Prints two markdown tables (per role+model, per run).
Costs are notional list-price equivalents (ADR-014). The subscription bills no per-token price.
"""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path

FIELDS = ("tokens_in", "tokens_out", "cache_read", "cache_write", "cost_usd")


def load(path: Path) -> list[dict]:
    rows = []
    for line in path.read_text().splitlines():
        try:
            d = json.loads(line)
        except json.JSONDecodeError:
            continue
        # count only real agent calls (they carry a model and tokens)
        if d.get("model") and (d.get("tokens_in") or d.get("tokens_out") or d.get("cost_usd")):
            rows.append(d)
    return rows


def main() -> None:
    per_role: dict[tuple, dict] = defaultdict(lambda: defaultdict(float))
    per_run = []
    total: dict[str, float] = defaultdict(float)
    for spec in sys.argv[1:]:
        kind, item, path = spec.split(":", 2)
        rows = load(Path(path))
        run = defaultdict(float)
        for d in rows:
            key = (d.get("actor") or d.get("role") or "?", d["model"], kind)
            per_role[key]["calls"] += 1
            run["calls"] += 1
            total["calls"] += 1
            for f in FIELDS:
                v = float(d.get(f) or 0)
                per_role[key][f] += v
                run[f] += v
                total[f] += v
        per_run.append((item, kind, path, run))
    fmt = lambda r: " | ".join([str(int(r["calls"]))] + [f"{int(r[f]):,}" for f in FIELDS[:4]] + [f"{r['cost_usd']:.2f}"])
    print("| Role | Model | Kind | Calls | tokens_in | tokens_out | cache_read | cache_write | notional $ |")
    print("|---|---|---|---|---|---|---|---|---|")
    for (role, model, kind), r in sorted(per_role.items()):
        print(f"| {role} | {model} | {kind} | {fmt(r)} |")
    print(f"| **Total** | | | {fmt(total)} |")
    print()
    print("| Run (item) | Kind | Ledger | Calls | tokens_in | tokens_out | cache_read | cache_write | notional $ |")
    print("|---|---|---|---|---|---|---|---|---|")
    for item, kind, path, r in per_run:
        print(f"| {item} | {kind} | `{path}` | {fmt(r)} |")


if __name__ == "__main__":
    main()
