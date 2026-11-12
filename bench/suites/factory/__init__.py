"""Suites of the factory domain: `protocol` (arms A, B, C, A2 on three engine options), `messy` (a messy simulated person) and
`messy_fix` (a repair check on the failed messy tasks). Registered when this package is imported."""
from __future__ import annotations

import json
from pathlib import Path

from symbolic_robot.domains.factory.person import answer_for
from symbolic_robot.domains.factory.tasks import factory_messy_tasks, factory_tasks

from ...suite import Suite
from .. import registry
from . import analyze_fix, analyze_messy, analyze_protocol, report_messy, report_protocol
from .arms import ARMS

HERE = Path(__file__).parent
WORLD = "assembly_hall"
# the server's baseline environment = arm A (every arm also sends its options with each run)
SERVER_ENV = {"ROBOT_AGENT_ASK_SOURCE": "1", "ROBOT_AGENT_ASK_SOURCE_REASK": "0", "ROBOT_AGENT_SEARCH_ROUTE_WEIGHT": "0"}
SERVER_ARGS = ("--ask-mode", "headless", "--dialogue", "human")
FIX_TASKS = ("t02,t09,t16,t23,t30,t37,t03,t10,t17,t24,t31,t38,t13,t27,t41,t06,t20,t34,t40,t00,t07,t14,t01,t08,t15")


def distance(log: list) -> float:
    """Metres travelled: the sum of the legs of successful `move` calls (the factory's call log carries the leg in its truth)."""
    return sum(e["truth"]["leg"]["dist"] for e in log if e.get("ok") and "leg" in (e.get("truth") or {}))


def _summary(analyze):
    def run(d):
        res = analyze(Path(d))
        Path(d, "summary.json").write_text(json.dumps(res, indent=1))
        return res
    return run


def _suite(name, description, arms, default_arms, tasks_fn, analyze, report, protocol, **defaults) -> Suite:
    return registry.register(Suite(
        domain="factory", name=name, description=description, arms={a: ARMS[a] for a in arms}, default_arms=tuple(default_arms),
        tasks=lambda world, n, seed: tasks_fn(world or WORLD, n, seed), answer=answer_for, distance=distance, analyze=analyze, report=report,
        protocol=protocol, defaults={"tasks": 36, "seeds": 2, "task_seed": 7, "profile": "real", "world": WORLD, **defaults},
        server_args=SERVER_ARGS, server_env=SERVER_ENV))


PROTOCOL = _suite("protocol", "three engine options, arms A B C A2, 36 tasks x 2 repeats (288 episodes), scripted person knows|unknown|wrong",
                  ("A", "B", "C", "A2"), ("A", "B", "C", "A2"), factory_tasks, _summary(analyze_protocol.analyze), report_protocol.main,
                  HERE / "protocol.md")
MESSY = _suite("messy", "a messy person (room only, vague, mind change, partial name, silent), arms A C D A2, 6 tasks per policy x 2 repeats (336 episodes)",
               ("A", "C", "D", "A2"), ("A", "C", "D", "A2"), factory_messy_tasks, _summary(analyze_messy.analyze), report_messy.main,
               HERE / "messy.md", tasks=6)
MESSY_FIX = _suite("messy_fix", "repair check of three ask_source keys on the failed messy tasks, arms A E D (150 episodes)",
                   ("A", "E", "D"), ("A", "E", "D"), factory_messy_tasks, _summary(analyze_fix.analyze), None, HERE / "messy_fix.md",
                   tasks=6, only=FIX_TASKS)
