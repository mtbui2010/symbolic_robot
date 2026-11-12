"""Post-hoc descriptive look at where the robot went first (NOT part of the pre-registered measures; messy.md).
python -m bench analyze factory messy --grounding <dir>   (needs detail/, which is not committed; writes grounding.json)
first move = the first successful `move` target that is not the task's destination; "straight" = it is the true place; "same zone" = it is in the
true place's zone/room (the part of the place id after '@'); "visited" = the true place is among the moves at all; "asked again" = 2+ where-questions."""
from __future__ import annotations

import json
import sys
from collections import defaultdict
from pathlib import Path


def zone(pid: str) -> str:
    return pid.split("@")[-1]


def one(det: dict) -> dict:
    t = det["task"]
    moves = [(l.get("args") or {}).get("target") for l in det["log"] if l.get("skill") == "move" and l.get("ok")]
    cand = [m for m in moves if m and m != t["dest"]]
    first = cand[0] if cand else None
    return {"first": first, "straight": first == t["true_place"], "zone": bool(first) and zone(first) == zone(t["true_place"]),
            "visited": t["true_place"] in moves, "asked_again": sum(1 for d in det["dialog"] if d["kind"] == "source") >= 2}


def main(d: str):
    acc: dict = defaultdict(lambda: defaultdict(list))
    for f in sorted(Path(d, "detail").glob("*.json")):
        det = json.loads(f.read_text())
        t = det["task"]
        arm = f.stem.split("_")[1]
        acc[t["policy"]][arm].append(one(det))
    out = {}
    for pol, arms in acc.items():
        out[pol] = {arm: {k: round(sum(r[k] for r in rs) / len(rs), 3) for k in ("straight", "zone", "visited", "asked_again")} | {"episodes": len(rs)} for arm, rs in sorted(arms.items())}
    Path(d, "grounding.json").write_text(json.dumps(out, indent=1))
    for pol, arms in out.items():
        print(pol, {a: (v["straight"], v["zone"], v["visited"], v["asked_again"]) for a, v in arms.items()})


if __name__ == "__main__":
    main(sys.argv[1])
