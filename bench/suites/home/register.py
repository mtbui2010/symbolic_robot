"""Registers the `home` suites with the generic bench CLI: `python -m bench run --domain home --suite <sub> ARGS` calls the household
benchmark's own command line in this process (no subprocess, no second interpreter): `bench.suites.home.cli.main([<sub>, *ARGS])`.
`python -m bench.suites.home.cli <sub> ARGS` is the same thing without the generic front end.
The test split is refused here, as it always was (the benchmark's own CLI refuses it too); this module reads no split."""
from __future__ import annotations

import shlex

from ...suite import Suite
from .. import registry

SUBCOMMANDS = {
    "planners": "list the planners (needs no data and no LLM: a safe smoke test)",
    "run": "play tasks x seeds with a planner (pass --planner/--split/--limit/--profile/--seeds/--out ... through ARGS)",
    "compare": "paired McNemar test of two run folders (ARGS: DIR_A DIR_B)",
    "report": "re-render report.md of a run folder (ARGS: DIR)",
}


def command(sub: str, extra: list, out: str | None) -> list:
    """The argument list of the home CLI for one subcommand (refuses the test split; adds --out to `run` when absent)."""
    if "test" in [extra[i + 1] for i, x in enumerate(extra[:-1]) if x == "--split"] or any(x == "--split=test" for x in extra):
        raise SystemExit("refused: the test split is not run through this front end")
    cmd = [sub, *extra]
    if sub == "run" and out and "--out" not in extra:
        cmd += ["--out", out]
    return cmd


def delegate(a, extra: list) -> int:
    argv = command(a.suite, extra, a.out)
    print("household benchmark: python -m bench.suites.home.cli " + " ".join(shlex.quote(c) for c in argv), flush=True)
    if a.dry_run:
        return 0
    from .cli import main                          # imported late: the listing of suites needs none of the benchmark's modules
    return main(argv)


for _sub, _desc in SUBCOMMANDS.items():
    registry.register(Suite(domain="home", name=_sub, description=f"household benchmark, {_sub}: {_desc}", delegate=delegate))
