"""Run a campaign: every (task, repeat, arm) of a suite against a running server. Arms are interleaved per task (the order rotates with
the task index) so drift hits every arm equally. Results are appended to episodes.jsonl (one line per episode, resumable) and the full
detail of each episode is kept in detail/<task>_<arm>_<repeat>.json."""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import protocol
from .runner import run_episode


def run_campaign(suite, base: str, out: Path, world: str, n_tasks: int, seeds: int, arms, seed0: int = 0, task_seed: int = 7,
                 profile: str = "real", only=(), limit: int = 0, allow_protocol_change: bool = False) -> int:
    """-> number of new episodes. `limit` stops after that many new episodes (a pilot)."""
    out = Path(out)
    (out / "detail").mkdir(parents=True, exist_ok=True)
    protocol.register(out, suite.protocol, allow_protocol_change)
    tasks = suite.tasks(world, n_tasks, task_seed)
    (out / "tasks.json").write_text(json.dumps(tasks, indent=1))
    arms = list(arms)
    bad = [a for a in arms if a not in suite.arms]
    if bad:
        raise SystemExit(f"unknown arm(s) {bad} for {suite.key}; known: {', '.join(suite.arms)}")
    log = out / "episodes.jsonl"
    done = {(r["task"], r["arm"], r["seed"]) for r in map(json.loads, log.read_text().splitlines())} if log.exists() else set()
    new = 0
    for i, t in enumerate(tasks):
        if only and t["id"] not in set(only):
            continue
        for seed in range(seed0, seed0 + seeds):
            order = arms[i % len(arms):] + arms[:i % len(arms)]
            for arm in order:
                if (t["id"], arm, seed) in done:
                    continue
                if limit and new >= limit:
                    return new
                r = run_episode(suite, base, t, arm, seed, profile)
                (out / "detail" / f"{t['id']}_{arm}_{seed}.json").write_text(json.dumps(r.pop("_detail"), default=str))
                with open(log, "a") as f:
                    f.write(json.dumps(r) + "\n")
                new += 1
                print(f"{time.strftime('%H:%M:%S')} {t['id']} {arm} s{seed} {t['kind']}/{t['policy']}: {r['status']} ok={r['success']} wrong_done={r['wrong_done']} "
                      f"dist={r['distance_m']} q={r['questions']} wall={r['wall_s']}s", flush=True)
    return new
