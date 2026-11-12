"""Paired statistics of a campaign: the task is the unit, each measure is averaged over the task's repeats, arms are compared on the same
tasks. Exact two-sided sign test (ties dropped), 95 % bootstrap interval of paired differences, and the combined success-then-distance criterion."""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

MEASURES = ("success", "wrong_done", "distance_m", "questions", "t_sim")
DIST_TOL_ABS, DIST_TOL_REL = 0.5, 0.05       # a distance difference smaller than max(0.5 m, 5 % of the baseline's) is a tie
BOOT, BOOT_SEED = 10000, 0


def load(path: Path) -> list:
    return [json.loads(x) for x in Path(path, "episodes.jsonl").read_text().splitlines() if x.strip()]


def per_task(rows: list, arm: str, measure: str, tasks=None) -> dict:
    acc: dict = {}
    for r in rows:
        if r["arm"] == arm and (tasks is None or r["task"] in tasks):
            acc.setdefault(r["task"], []).append(float(r[measure] if r[measure] is not None else 0.0))
    return {t: sum(v) / len(v) for t, v in acc.items()}


def sign_test(wins: int, losses: int) -> float:
    """Exact two-sided binomial p (ties dropped)."""
    n = wins + losses
    if n == 0:
        return 1.0
    k = min(wins, losses)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n
    return min(1.0, 2 * p)


def boot_ci(diffs: list) -> tuple:
    if not diffs:
        return (0.0, 0.0, 0.0)
    rnd = random.Random(BOOT_SEED)
    n = len(diffs)
    means = sorted(sum(rnd.choice(diffs) for _ in range(n)) / n for _ in range(BOOT))
    return (sum(diffs) / n, means[int(0.025 * BOOT)], means[int(0.975 * BOOT) - 1])


def compare(rows: list, arm: str, base: str, tasks=None, measures=MEASURES) -> dict:
    """arm vs base on the tasks both have. Combined criterion per task: success first, then distance (with a tie band)."""
    out: dict = {}
    s_a, s_b = per_task(rows, arm, "success", tasks), per_task(rows, base, "success", tasks)
    d_a, d_b = per_task(rows, arm, "distance_m", tasks), per_task(rows, base, "distance_m", tasks)
    common = sorted(set(s_a) & set(s_b))
    win = loss = tie = sw = sl = dw = dl = 0
    for t in common:
        ds = s_a[t] - s_b[t]
        sw, sl = sw + (ds > 0), sl + (ds < 0)
        tol = max(DIST_TOL_ABS, DIST_TOL_REL * d_b[t])
        dd = d_a[t] - d_b[t]
        dw, dl = dw + (dd < -tol), dl + (dd > tol)
        if ds > 0:
            win += 1
        elif ds < 0:
            loss += 1
        elif dd < -tol:
            win += 1
        elif dd > tol:
            loss += 1
        else:
            tie += 1
    out["n_tasks"] = len(common)
    out["combined"] = {"wins": win, "losses": loss, "ties": tie, "p": round(sign_test(win, loss), 4)}
    out["success_only"] = {"wins": sw, "losses": sl, "p": round(sign_test(sw, sl), 4)}
    out["distance_only"] = {"wins": dw, "losses": dl, "p": round(sign_test(dw, dl), 4)}
    for m in measures:
        a, b = per_task(rows, arm, m, tasks), per_task(rows, base, m, tasks)
        mean, lo, hi = boot_ci([a[t] - b[t] for t in common])
        out[f"d_{m}"] = {"mean": round(mean, 4), "ci95": [round(lo, 4), round(hi, 4)]}
    both = [t for t in common if s_a[t] == 1.0 and s_b[t] == 1.0]            # distance where both arms succeeded in every seed
    mean, lo, hi = boot_ci([d_a[t] - d_b[t] for t in both])
    out["d_distance_both_success"] = {"n": len(both), "mean": round(mean, 3), "ci95": [round(lo, 3), round(hi, 3)]}
    return out


def table(rows: list, arms, tasks=None) -> dict:
    t = {}
    for arm in arms:
        eps = [r for r in rows if r["arm"] == arm and (tasks is None or r["task"] in tasks)]
        if not eps:
            continue
        n = len(eps)
        t[arm] = {"episodes": n, "success": round(sum(r["success"] for r in eps) / n, 3), "wrong_done": round(sum(r["wrong_done"] for r in eps) / n, 3),
                  "distance_m": round(sum(r["distance_m"] for r in eps) / n, 2), "questions": round(sum(r["questions"] for r in eps) / n, 2),
                  "t_sim": round(sum(r["t_sim"] or 0 for r in eps) / n, 1), "wall_s": round(sum(r["wall_s"] for r in eps) / n, 1),
                  "timeouts": sum(r["timeout"] for r in eps), "no_done_event": sum(r["status"] == "none" for r in eps)}
    return t
