"""Analysis of the messy suite (messy.md): arms A, C, D, A2 over the answer policies of a messy simulated person. Reuses the sign test,
bootstrap and combined criterion of bench.stats; unit = the task, measures averaged over the repeats."""
from __future__ import annotations

import argparse
import json
import re
from collections import Counter
from pathlib import Path

from ... import stats as A

MEASURES = ("success", "wrong_done", "distance_m", "questions", "unusable_answers", "clarified")
ARMS = ["A", "C", "D", "A2"]
NEW = ("room_only", "vague", "mind_change", "partial_name", "silent")
POLICIES = ("knows", "wrong") + NEW
FAIL_CLASSES = (("grip or place fault", r"place failed|slipped|\bfell\b|dropped|pick failed"), ("search gave up", r"could not find"),
                ("goals do not hold", r"goals do not hold"), ("asked then stopped", r"\bask|answer|question|clarif|\bsay\b"))


def fail_class(r: dict) -> str:
    if r["success"]:
        return "success"
    if r["timeout"]:
        return "timeout"
    if r["status"] == "none":
        return "no done event"
    msg = (r.get("engine_msg") or "").lower()
    for name, rx in FAIL_CLASSES:
        if re.search(rx, msg):
            return name
    return "other"


def placement_fault(r: dict) -> bool:
    return (not r["success"]) and any(f in ("fall", "dropped") for f in r.get("faults", []))


def table(rows: list, tasks=None) -> dict:
    out = A.table(rows, ARMS, tasks)
    for arm, v in out.items():
        eps = [r for r in rows if r["arm"] == arm and (tasks is None or r["task"] in tasks)]
        u = sum(r["unusable_answers"] for r in eps)
        c = sum(r["clarified"] for r in eps)
        v.update({"unusable_answers": u, "clarified": c, "clarify_rate": round(c / u, 3) if u else None,
                  "fail_classes": dict(Counter(fail_class(r) for r in eps if not r["success"])),
                  "failed_after_placement_fault": sum(placement_fault(r) for r in eps)})
    return out


def compare(rows: list, arm: str, base: str, tasks=None) -> dict:
    return A.compare(rows, arm, base, tasks, MEASURES)


def verdict(rows: list) -> dict:
    out = {}
    noise = compare(rows, "A2", "A")["combined"]
    out["noise_wins_minus_losses"] = abs(noise["wins"] - noise["losses"])
    for arm in ("C", "D"):
        c = compare(rows, arm, "A")
        w, wd = c["combined"], c["d_wrong_done"]["mean"]
        out[arm] = {"wins": w["wins"], "losses": w["losses"], "p": w["p"], "d_wrong_done": wd, "beats_A": bool(w["wins"] > w["losses"] and wd <= 0),
                    "above_noise": bool(w["wins"] - w["losses"] > out["noise_wins_minus_losses"])}
    out["rule_met"] = any(out[a]["beats_A"] for a in ("C", "D"))
    return out


def policy_claim(c: dict) -> bool:
    w = c["combined"]
    return bool(w["wins"] > w["losses"] and w["p"] < 0.05)


def analyze(path: Path) -> dict:
    rows = A.load(path)
    tasks = json.loads(Path(path, "tasks.json").read_text())
    new_ids = {t["id"] for t in tasks if t["policy"] in NEW}
    res = {"arms": table(rows), "vs_A": {a: compare(rows, a, "A") for a in ("C", "D", "A2")}, "D_vs_C": compare(rows, "D", "C"), "verdict": verdict(rows),
           "messy_subset": {"tasks": len(new_ids), "arms": table(rows, new_ids), "vs_A": {a: compare(rows, a, "A", new_ids) for a in ("C", "D", "A2")},
                            "D_vs_C": compare(rows, "D", "C", new_ids)}, "by_policy": {}}
    for pol in POLICIES:
        ids = {t["id"] for t in tasks if t["policy"] == pol}
        if ids:
            vs = {a: compare(rows, a, "A", ids) for a in ("C", "D", "A2")}
            res["by_policy"][pol] = {"tasks": len(ids), "arms": table(rows, ids), "vs_A": vs, "policy_level_win": {a: policy_claim(vs[a]) for a in ("C", "D")}}
    kinds = {}
    for t in tasks:
        if t["policy"] == "partial_name":
            kinds[t["id"]] = t.get("variant_kind")
    res["partial_name_by_variant"] = {}
    for k in sorted(set(kinds.values())):
        ids = {t for t, v in kinds.items() if v == k}
        res["partial_name_by_variant"][k] = {"tasks": sorted(ids), "arms": {a: v["success"] for a, v in table(rows, ids).items()}}
    res["n_episodes"] = len(rows)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    a = ap.parse_args(argv)
    res = analyze(Path(a.dir))
    Path(a.dir, "summary.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({"arms": {k: {x: y for x, y in v.items() if x != "fail_classes"} for k, v in res["arms"].items()}, "verdict": res["verdict"]}, indent=1))


if __name__ == "__main__":
    main()
