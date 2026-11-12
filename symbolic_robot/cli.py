"""python -m symbolic_robot {run, list}"""
from __future__ import annotations

import argparse
import sys

from . import registry


def _opt(text: str):
    k, _, v = text.partition("=")
    for conv in (int, float):
        try:
            return k, conv(v)
        except ValueError:
            pass
    return k, {"true": True, "false": False}.get(v.lower(), v)


def cmd_list(_a) -> int:
    print("domains:")
    for n in registry.names():
        try:
            d = registry.get(n)
            why = d.available()
        except Exception as e:                   # noqa: BLE001
            print(f"  {n:10s} not loadable: {type(e).__name__}: {e}")
            continue
        if why:
            print(f"  {n:10s} not available: {why}")
            continue
        print(f"  {n:10s} {d.description}")
        print(f"             {d.world_label}s: {', '.join(d.worlds())}   (default {d.default_world()})")
        print(f"             profiles: {', '.join(d.profiles())}")
    return 0


def cmd_run(a) -> int:
    try:
        from . import server
    except ImportError as e:
        print(f"cannot import the server glue: {e}", file=sys.stderr)
        return 2
    world = a.world or next((getattr(a, k) for k in registry.world_labels() if getattr(a, k, None)), None)
    opts = dict(_opt(x) for x in a.opt)
    try:
        app, _live = server.build(a.robot, world, a.profile, a.seed, a.run_dir, a.ask_mode, a.dialogue, a.model,
                                  a.ollama_url, opts)
    except (RuntimeError, KeyError, ValueError) as e:
        print(f"cannot start: {e}", file=sys.stderr)
        return 2
    import uvicorn
    uvicorn.run(app, host=a.host, port=a.port, log_level="warning")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m symbolic_robot")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="domains, worlds, profiles").set_defaults(fn=cmd_list)
    r = sub.add_parser("run", help="serve a domain as the benchmark backend through robot_agent's API")
    r.add_argument("--robot", required=True, help="domain name (python -m symbolic_robot list)")
    r.add_argument("--world", default=None, help="floor / house / ... (default: the domain's)")
    for label in registry.world_labels():
        r.add_argument(f"--{label}", default=None, help=f"alias of --world ({label})")
    r.add_argument("--profile", default="real")
    r.add_argument("--seed", type=int, default=0)
    r.add_argument("--dialogue", choices=["human", "sim"], default="human", help="who answers the robot's questions: the person or the simulated user")
    r.add_argument("--ask-mode", choices=["headless"], default="headless",
                   help="how the person answers: headless (the benchmark's script posts the answer to /agent/listen/<id>); the only mode")
    r.add_argument("--model", default=None, help="local LLM served for planner and reader (default: the domain's)")
    r.add_argument("--opt", action="append", default=[], metavar="KEY=VALUE", help="a domain option for make_episode (repeatable)")
    r.add_argument("--run-dir", default="run_dir")
    r.add_argument("--ollama-url", default="http://127.0.0.1:11434")
    r.add_argument("--host", default="127.0.0.1")
    r.add_argument("--port", type=int, default=8091)
    r.set_defaults(fn=cmd_run)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
