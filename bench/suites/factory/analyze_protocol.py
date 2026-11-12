"""Analysis of the protocol suite (docs/bench.md, protocol.md): arms A, B, C, A2 on the same tasks; the pre-registered win rule."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from ... import stats as A
from ...stats import compare, load, table  # noqa: F401


def verdict(rows: list) -> dict:
    """The pre-registered win rule: B (or C) beats A on more tasks than it loses on success-or-distance, and wrong-done does not increase."""
    out = {}
    for arm in ("B", "C"):
        c = compare(rows, arm, "A")
        w = c["combined"]
        wd = c["d_wrong_done"]["mean"]
        out[arm] = {"wins": w["wins"], "losses": w["losses"], "p": w["p"], "d_wrong_done": wd,
                    "beats_A": bool(w["wins"] > w["losses"] and wd <= 0)}
    out["rule_met"] = any(out[a]["beats_A"] for a in ("B", "C"))
    return out


def analyze(path: Path) -> dict:
    rows = load(path)
    tasks = json.loads(Path(path, "tasks.json").read_text())
    res = {"arms": table(rows, ["A", "B", "C", "A2"]), "vs_A": {a: compare(rows, a, "A") for a in ("B", "C", "A2")},
           "C_vs_B": compare(rows, "C", "B"), "verdict": verdict(rows), "by_policy": {}}
    for pol in ("knows", "unknown", "wrong", None):
        ids = {t["id"] for t in tasks if t.get("policy") == pol}
        if not ids:
            continue
        key = pol or "request_names_source"
        res["by_policy"][key] = {"tasks": len(ids), "arms": table(rows, ["A", "B", "C", "A2"], ids),
                                 "vs_A": {a: compare(rows, a, "A", ids) for a in ("B", "C", "A2")}}
    res["n_episodes"] = len(rows)
    return res


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("dir")
    a = ap.parse_args(argv)
    res = analyze(Path(a.dir))
    Path(a.dir, "summary.json").write_text(json.dumps(res, indent=1))
    print(json.dumps({"arms": res["arms"], "verdict": res["verdict"]}, indent=1))


if __name__ == "__main__":
    main()
