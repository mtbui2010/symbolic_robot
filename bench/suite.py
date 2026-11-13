"""What a benchmark suite is: data and a few hooks, registered by name under a domain (bench/suites/<domain>/<suite>)."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


@dataclass
class Suite:
    domain: str
    name: str
    description: str
    # ---- campaign suites (a planner is driven through the API, arms compared on the same tasks)
    arms: dict = field(default_factory=dict)            # arm -> run options sent with each run
    default_arms: tuple = ()
    tasks: Optional[Callable] = None                    # (world, n, task_seed) -> list of task dicts
    answer: Optional[Callable] = None                   # (task, question, n_where) -> (text, kind, grounded): the simulated person
    distance: Optional[Callable] = None                 # (call log) -> metres travelled
    analyze: Optional[Callable] = None                  # (results dir) -> summary dict (also written to summary.json)
    report: Optional[Callable] = None                   # (list of results dirs) -> prints markdown tables
    protocol: Optional[Path] = None                     # the pre-registered protocol file (its sha256 is recorded with the results)
    defaults: dict = field(default_factory=lambda: {"tasks": 36, "seeds": 2, "task_seed": 7, "profile": "real", "world": ""})
    server_args: tuple = ()                             # extra arguments of `python -m symbolic_robot run`
    server_env: dict = field(default_factory=dict)      # environment of the server (the baseline arm's options)
    # ---- a suite whose commands are its own program (the home suites: run in this process through its own CLI)
    delegate: Optional[Callable] = None                 # (args namespace, extra args list) -> exit status

    @property
    def key(self) -> str:
        return f"{self.domain}/{self.name}"
