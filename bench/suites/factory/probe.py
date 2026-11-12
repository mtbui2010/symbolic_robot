"""Generalisation probe: the same tasks, arm A, one repeat, two readers. python -m bench.suites.factory.probe <dir_lora> <dir_stock> [repeat]
Compares what the reader understood (the first `understand` event against the task's object, destination and source) and the outcome."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from ...stats import load
from symbolic_robot.domains.factory.world import norm


def _goals(events: list) -> list:
    u = next((e for e in events if e.get("event") == "understand"), None)
    g = (u or {}).get("goals") or []
    return g if isinstance(g, list) else []


def _matches(task: dict, g: dict) -> bool:
    words = set(norm(task["object"]).split())
    return (g.get("type") in ("on", "in") and words <= set(norm(g.get("object", "")).split()) and g.get("to") == task["dest"]
            and (g.get("from", "") == (task["true_place"] if task["kind"] == "given" else "")))


def reader_ok(task: dict, events: list) -> bool:
    """Exactly one goal and it is the task's (object, destination, and source only when the request names it)."""
    goals = _goals(events)
    return len(goals) == 1 and _matches(task, goals[0])


def goal_present(task: dict, events: list) -> bool:
    """The task's goal is among the understood goals (an extra goal does not count against it)."""
    return any(_matches(task, g) for g in _goals(events))


def stats(d: Path, repeat: int) -> dict:
    rows = [r for r in load(d) if r["arm"] == "A" and r["seed"] == repeat]
    out = {"episodes": len(rows), "success": 0, "reader_ok": 0, "goal_present": 0, "no_goal": 0, "clear": 0, "distance": 0.0, "questions": 0}
    for r in rows:
        det = json.loads(Path(d, "detail", f"{r['task']}_{r['arm']}_{r['seed']}.json").read_text())
        out["success"] += r["success"]
        out["reader_ok"] += reader_ok(det["task"], det["events"])
        out["goal_present"] += goal_present(det["task"], det["events"])
        out["no_goal"] += not _goals(det["events"])
        out["clear"] += any(e.get("event") == "understand" and e.get("status") == "clear" for e in det["events"])
        out["distance"] += r["distance_m"]
        out["questions"] += r["questions"]
    n = max(1, len(rows))
    return {k: (round(v / n, 3) if k != "episodes" else v) for k, v in out.items()}


def main(argv):
    rep = int(argv[2]) if len(argv) > 2 else 0
    res = {"lora": stats(Path(argv[0]), rep), "stock": stats(Path(argv[1]), rep)}
    print(json.dumps(res, indent=1))
    Path(argv[1], "probe.json").write_text(json.dumps(res, indent=1))


if __name__ == "__main__":
    main(sys.argv[1:])
