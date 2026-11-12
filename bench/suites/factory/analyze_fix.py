"""Analysis of the messy-fix re-run (arms A, D, E on the failed tasks; docs/findings.md item 9).
python -m bench analyze factory messy_fix <dir>   (needs detail/ for the dialogue and the first move; writes summary.json)
Paired counts per task (measures averaged over the repeats), combined criterion as in analyze.py; descriptive only (a few tasks per group)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

from ... import stats as A
from .grounding import one

GROUPS = {"room_only": ["t02", "t09", "t16", "t23", "t30", "t37"], "vague": ["t03", "t10", "t17", "t24", "t31", "t38"],
          "silent_dots": ["t13", "t27", "t41"], "silent_empty": ["t06", "t20", "t34"], "partial_name": ["t40"],
          "knows": ["t00", "t07", "t14"], "wrong": ["t01", "t08", "t15"]}
GROUPS["failed_18"] = GROUPS["room_only"] + GROUPS["vague"] + GROUPS["silent_dots"] + GROUPS["silent_empty"]
PAIRS = (("E", "A"), ("D", "A"), ("E", "D"))


def extras(d: Path) -> dict:
    out: dict = {}
    for f in sorted(Path(d, "detail").glob("*.json")):
        det = json.loads(f.read_text())
        task, arm = f.stem.split("_")[0], f.stem.split("_")[1]
        g = one(det)
        qs = [x["q"] for x in det["dialog"]]
        out[(task, arm, int(f.stem.split("_")[2]))] = {
            "zone": g["zone"], "straight": g["straight"],
            "room_said": any("I will look in the" in str(e.get("say", "")) for e in det["events"]),
            "clarify_q": sum("Which room, or which piece" in q for q in qs), "did_you_mean": sum(q.startswith("Did you mean") for q in qs),
            "where_q": sum(q.startswith("Where is the") for q in qs), "retry_q": sum("couldn't find" in q for q in qs)}
    return out


def arm_row(rows, ex, arm, ids) -> dict:
    eps = [r for r in rows if r["arm"] == arm and r["task"] in ids]
    n = max(len(eps), 1)
    xs = [ex.get((r["task"], arm, r["seed"]), {}) for r in eps]
    s = lambda k: round(sum(bool(x.get(k)) for x in xs) / n, 2)       # noqa: E731
    return {"n": len(eps), "success": round(sum(r["success"] for r in eps) / n, 2), "wrong_done": sum(r["wrong_done"] for r in eps),
            "dist_m": round(sum(r["distance_m"] for r in eps) / n, 1), "questions": round(sum(r["questions"] for r in eps) / n, 2),
            "unusable": sum(r["unusable_answers"] for r in eps), "clarified": sum(r["clarified"] for r in eps),
            "clarify_asked": sum(x.get("clarify_q", 0) for x in xs), "did_you_mean": sum(x.get("did_you_mean", 0) for x in xs),
            "room_said": sum(bool(x.get("room_said")) for x in xs), "first_in_zone": s("zone"), "first_straight": s("straight")}


def analyze(d) -> dict:
    rows = A.load(Path(d))
    ex = extras(Path(d))
    out: dict = {}
    for g, ids in GROUPS.items():
        ids = set(ids)
        out[g] = {"tasks": len(ids), "arms": {a: arm_row(rows, ex, a, ids) for a in ("A", "D", "E")}, "paired": {}}
        for x, b in PAIRS:
            c = A.compare(rows, x, b, ids, ("success", "distance_m", "questions"))
            out[g]["paired"][f"{x}_vs_{b}"] = {"combined": c["combined"], "success_only": c["success_only"], "d_success": c["d_success"]["mean"],
                                               "d_distance": c["d_distance_m"]["mean"], "d_questions": c["d_questions"]["mean"]}
    return out


def main(d: str):
    out = analyze(d)
    Path(d, "summary.json").write_text(json.dumps(out, indent=1))
    for g, v in out.items():
        print(f"\n## {g} ({v['tasks']} tasks)")
        for a, r in v["arms"].items():
            print(f"  {a}: succ {r['success']} wd {r['wrong_done']} dist {r['dist_m']} q {r['questions']} unusable {r['unusable']} clar_asked {r['clarify_asked']} "
                  f"dym {r['did_you_mean']} room_said {r['room_said']} first_in_zone {r['first_in_zone']} straight {r['first_straight']}")
        for k, p in v["paired"].items():
            c = p["combined"]
            print(f"  {k}: W/L/T {c['wins']}/{c['losses']}/{c['ties']} p={c['p']} | success W/L {p['success_only']['wins']}/{p['success_only']['losses']} "
                  f"dS {p['d_success']:+} dDist {p['d_distance']:+} dQ {p['d_questions']:+}")


if __name__ == "__main__":
    main(sys.argv[1])
