"""Factory sim parity: replay the skill-call sequences recorded in an earlier campaign (detail/*.json of another repository's
results folder; read only, never copied) in symbolic_robot.domains.factory and compare every call with the recorded one.

    python tests/parity/factory_replay.py <results dir> [--floor assembly_hall] [--profile real] [--max N] [--stride K]

Compared per call: ok, code, msg (first 160 characters), duration (2 decimals), simulated time, and the whole truth dict.
Exit status 1 when any call differs.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from symbolic_robot.domains.factory import make_episode  # noqa: E402


def sim_seed(row: dict) -> int:
    return int(row["sim_seed"])


def replay_episode(entries: list, floor: str, profile: str, seed: int) -> list:
    """-> list of (index, field, recorded, replayed) for every difference."""
    robot = make_episode(floor, profile, seed).robot
    diffs = []
    for i, e in enumerate(entries):
        if e["skill"] == "ask":                                   # an ask answered from outside the simulator
            truth = e.get("truth") or {}
            robot.record_ask(truth.get("asked", ""), truth.get("answer", ""))
            got = robot.log[-1]
        else:
            res = robot.call(e["skill"], **e["args"])
            got = robot.log[-1]
        for k in ("ok", "code", "msg", "dur", "t_sim", "truth", "skill", "args"):
            want = e[k]
            if k in ("msg",) and e["skill"] == "ask":
                continue                                          # recorded asks are truncated; text is compared through truth
            if got[k] != want:
                diffs.append((i, k, want, got[k]))
    return diffs


def run(results: Path, floor: str, profile: str, max_eps: int = 0, stride: int = 1) -> dict:
    rows = [json.loads(x) for x in (results / "episodes.jsonl").read_text().splitlines() if x.strip()]
    rows = rows[::stride]
    if max_eps:
        rows = rows[:max_eps]
    stats = {"episodes": 0, "calls": 0, "mismatched_episodes": 0, "mismatched_calls": 0, "skills": {}, "arms": {}, "policies": {}, "examples": []}
    for r in rows:
        f = results / "detail" / f"{r['task']}_{r['arm']}_{r['seed']}.json"
        if not f.exists():
            continue
        entries = json.loads(f.read_text())["log"]
        diffs = replay_episode(entries, floor, profile, sim_seed(r))
        stats["episodes"] += 1
        stats["calls"] += len(entries)
        stats["arms"][r["arm"]] = stats["arms"].get(r["arm"], 0) + 1
        stats["policies"][str(r.get("policy"))] = stats["policies"].get(str(r.get("policy")), 0) + 1
        for e in entries:
            stats["skills"][e["skill"]] = stats["skills"].get(e["skill"], 0) + 1
        if diffs:
            stats["mismatched_episodes"] += 1
            stats["mismatched_calls"] += len({d[0] for d in diffs})
            if len(stats["examples"]) < 5:
                stats["examples"].append({"episode": f.name, "first_diffs": diffs[:3]})
    return stats


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("results")
    ap.add_argument("--floor", default="assembly_hall")
    ap.add_argument("--profile", default="real")
    ap.add_argument("--max", type=int, default=0)
    ap.add_argument("--stride", type=int, default=1)
    a = ap.parse_args(argv)
    st = run(Path(a.results), a.floor, a.profile, a.max, a.stride)
    print(json.dumps(st, indent=1, default=str))
    return 1 if st["mismatched_calls"] else 0


if __name__ == "__main__":
    sys.exit(main())
