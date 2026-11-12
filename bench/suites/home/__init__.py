"""Suites of the `home` domain: delegation to the separate benchmark package that belongs to the frozen household simulator
(`homeloop_bench`, its own repository and CLI). Nothing of it is imported or moved here: `python -m bench run --domain home --suite <sub>`
runs `python -m homeloop_bench.cli <sub> ARGS` with the given interpreter and passes the arguments through.
The test split and the development ids 200..299 are not read by this wrapper: `--split test` is refused here (the benchmark refuses it too)."""
from __future__ import annotations

import shlex
import subprocess
import sys

from ...suite import Suite
from .. import registry

CLI = ("-m", "homeloop_bench.cli")
SUBCOMMANDS = {
    "planners": "list the planners (needs no data and no LLM: a safe smoke test)",
    "run": "play tasks x seeds with a planner (pass --planner/--split/--limit/--profile/--seeds/--out ... through ARGS)",
    "compare": "paired McNemar test of two run folders (ARGS: DIR_A DIR_B)",
    "report": "re-render report.md of a run folder (ARGS: DIR)",
}


def command(python: str, sub: str, extra: list, out: str | None) -> list:
    if "test" in [extra[i + 1] for i, x in enumerate(extra[:-1]) if x == "--split"] or any(x == "--split=test" for x in extra):
        raise SystemExit("refused: the test split is not run through this wrapper")
    cmd = [python, *CLI, sub, *extra]
    if sub == "run" and out and "--out" not in extra:
        cmd += ["--out", out]
    return cmd


def delegate(a, extra: list) -> int:
    cmd = command(a.python, a.suite, extra, a.out)
    print("delegating to the household benchmark (its own CLI):\n  " + " ".join(shlex.quote(c) for c in cmd), flush=True)
    if a.dry_run:
        return 0
    return subprocess.call(cmd)


for _sub, _desc in SUBCOMMANDS.items():
    registry.register(Suite(domain="home", name=_sub, description=f"homeloop_bench {_sub}: {_desc}", delegate=delegate))
