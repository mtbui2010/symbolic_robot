"""python -m bench {list, run, analyze, report, verify}"""
from __future__ import annotations

import argparse
import contextlib
import io
import sys
import time
from pathlib import Path

from . import orchestrate, protocol
from .campaign import run_campaign
from .suites import registry


def cmd_list(_a, _extra) -> int:
    print("suites (make bench ROBOT=<domain> SUITE=<name> [ARGS=...]):")
    for dom, name, desc in registry.listing():
        print(f"  {dom}/{name}: {desc}")
    return 0


def _env(items) -> dict:
    return dict(x.split("=", 1) for x in items)


def cmd_run(a, extra) -> int:
    suite = registry.get(a.domain, a.suite)
    if suite.delegate is not None:
        return suite.delegate(a, extra)
    if extra:
        print(f"unknown arguments for {suite.key}: {' '.join(extra)}", file=sys.stderr)
        return 2
    d = suite.defaults
    world, profile = a.world or d["world"], a.profile or d["profile"]
    out = Path(a.out)
    arms = a.arms.split(",") if a.arms else list(suite.default_arms)
    only = a.only.split(",") if a.only else (d.get("only", "").split(",") if d.get("only") else [])
    n_tasks, seeds = a.tasks or d["tasks"], a.seeds or d["seeds"]
    print(f"suite {suite.key}: world {world}, profile {profile}, tasks {n_tasks}, repeats {seeds}, arms {','.join(arms)}"
          f"{', only ' + ','.join(only) if only else ''}{', limit ' + str(a.limit) if a.limit else ''} -> {out}", flush=True)
    if a.dry_run:
        return 0
    protocol.register(out, suite.protocol, a.allow_protocol_change)
    args = [*suite.server_args, "--world", world, "--profile", profile, *(["--model", a.model] if a.model else [])]
    t0 = time.time()
    with orchestrate.server(a.python, a.domain, orchestrate.port_range(a.ports), out / "_server", args, {**suite.server_env, **_env(a.env)}) as base:
        print(f"server up on {base}", flush=True)
        new = run_campaign(suite, base, out, world, n_tasks, seeds, arms, a.seed0, d["task_seed"] if a.task_seed is None else a.task_seed,
                           profile, only, a.limit, a.allow_protocol_change)
    print(f"{new} new episodes in {time.time() - t0:.0f} s; server stopped", flush=True)
    return _analyze(suite, out)


def _analyze(suite, out: Path) -> int:
    if suite.analyze is None:
        return 0
    try:
        suite.analyze(out)
    except Exception as e:                      # noqa: BLE001 - a reduced run may lack arms the analysis compares
        print(f"analysis not computed ({type(e).__name__}: {e}); episodes.jsonl is complete", file=sys.stderr)
        return 0
    if suite.report is not None:
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            suite.report([str(out)])
        (out / "report.md").write_text(buf.getvalue())
    print(f"wrote {out / 'summary.json'}" + (f" and {out / 'report.md'}" if suite.report else ""))
    return 0


def cmd_analyze(a, _extra) -> int:
    return _analyze(registry.get(a.domain, a.suite), Path(a.dir))


def cmd_report(a, _extra) -> int:
    registry.get(a.domain, a.suite).report(a.dirs)
    return 0


def cmd_verify(a, _extra) -> int:
    suite = registry.get(a.domain, a.suite)
    ok = suite.protocol is not None and protocol.verify(Path(a.dir), suite.protocol)
    print(f"protocol hash {'matches' if ok else 'DOES NOT match (or is missing)'}: {a.dir}")
    return 0 if ok else 1


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m bench")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").set_defaults(fn=cmd_list)
    r = sub.add_parser("run", help="run a suite (starts and stops its own server on a free test port); unknown arguments go to a delegating suite")
    r.add_argument("--domain", required=True)
    r.add_argument("--suite", required=True)
    r.add_argument("--python", default=sys.executable, help="interpreter that has symbolic_robot's requirements (and the household benchmark for home)")
    r.add_argument("--ports", default="8120-8129", help="test ports to choose a free one from")
    r.add_argument("--out", required=True)
    r.add_argument("--world", default="")
    r.add_argument("--profile", default="")
    r.add_argument("--tasks", type=int, default=0, help="tasks (suites with policies: tasks per policy)")
    r.add_argument("--seeds", type=int, default=0)
    r.add_argument("--seed0", type=int, default=0)
    r.add_argument("--task-seed", type=int, default=None)
    r.add_argument("--arms", default="")
    r.add_argument("--only", default="", help="comma list of task ids")
    r.add_argument("--limit", type=int, default=0, help="stop after this many NEW episodes (pilot)")
    r.add_argument("--model", default="")
    r.add_argument("--env", action="append", default=[], metavar="KEY=VALUE", help="environment of the server (for example a different reader model)")
    r.add_argument("--dry-run", action="store_true", help="print what would run, start nothing")
    r.add_argument("--allow-protocol-change", action="store_true")
    r.set_defaults(fn=cmd_run)
    for name, fn in (("analyze", cmd_analyze), ("verify", cmd_verify)):
        p = sub.add_parser(name)
        p.add_argument("--domain", required=True)
        p.add_argument("--suite", required=True)
        p.add_argument("dir")
        p.set_defaults(fn=fn)
    p = sub.add_parser("report")
    p.add_argument("--domain", required=True)
    p.add_argument("--suite", required=True)
    p.add_argument("dirs", nargs="+")
    p.set_defaults(fn=cmd_report)
    a, extra = ap.parse_known_args(argv)
    return a.fn(a, extra)


if __name__ == "__main__":
    sys.exit(main())
