"""The domain protocol: what a domain gives the core. `BaseDomain` holds safe defaults, so a domain overrides only what it has;
a hook it does not override does nothing (the feature that needs it is simply absent).

An *episode* is whatever `make_episode` returns. The core only touches it through the hooks below and through its robot,
which must offer `call(skill, **args)` returning an object with ok, msg, code, data, duration_s, truth.
"""
from __future__ import annotations

from typing import Any


class BaseDomain:
    name = ""
    description = ""
    pack = ""                    # importable robot_agent pack (<pack>.configs.{adapter,skills_config,tasks,manifest.yaml})
    world_label = "world"        # what this domain calls its worlds: floor, house ... (a CLI flag --<label> is accepted)
    default_model = ""           # name of the local LLM served for planner / reader; empty: no LLM connection is written
    default_speedup = 0.0        # simulated seconds per real second for a live server (0 = do not wait)
    live_opts: dict = {}         # episode options a live server applies unless the caller gives them (never used by make_episode itself)

    # ---- catalogue
    def available(self) -> str | None:
        """None when usable, else the reason it is not (a missing optional package ...)."""
        return None

    def worlds(self) -> list:
        return []

    def default_world(self) -> str:
        w = self.worlds()
        return w[0] if w else ""

    def profiles(self) -> list:
        return []

    # ---- episodes
    def make_episode(self, world: str, profile: str, seed: int, **opts) -> Any:
        raise NotImplementedError(f"domain {self.name!r} cannot build episodes")

    def robot(self, ep) -> Any:
        return ep.robot

    def clock_t(self, ep) -> float:
        return float(getattr(self.robot(ep), "t", 0.0))

    def pose(self, ep) -> tuple:
        """(x, y, yaw_rad) of the robot."""
        return (0.0, 0.0, 0.0)

    def view(self, ep) -> dict:
        """{"objects": {id: {cls, at, ...}}, "robot": {...}}: the simulation truth, for GET /agent/sim_world/get."""
        return {"objects": {}, "robot": {}}

    def call_log(self, ep) -> list | None:
        """The log of calls with their truth when the robot keeps one; None: the live backend keeps its own."""
        return None

    # ---- what the server publishes
    def layout(self, ep) -> dict:
        """{"places": [{id, name, pos:[x,y], kind}], "regions": [{name, rect:[x0,y0,x1,y1]}], "doors": [{at:[x,y], width}],
        "labels": [{text, pos}]} for the map picture; empty: no picture."""
        return {}

    def env(self, ep) -> dict | None:
        """The planner's ENV for this world (robot_agent tasks.ENV); None: the pack's own."""
        return None

    def path(self, ep, a: tuple, b: tuple) -> list | None:
        """Waypoints from a to b when the world knows a route (the live pose follows it); None: a straight jump."""
        return None

    def planner_env(self) -> dict:
        """Environment defaults for the planner (names without the ROBOT_AGENT_ prefix)."""
        return {}

    def sim_user_opts(self) -> dict:
        """make_episode options that turn the simulated person on (for `--dialogue sim`)."""
        return {}

    def speech_lang(self, text: str, lang: str | None) -> str:
        """The language tag the browser voice should use for `text`."""
        return lang or "en"

    def install_pack(self, live) -> None:
        """Hand the live backend to the pack's skill functions (the pack's set_backend)."""

    # ---- sim_command ops; return a dict {ok, msg, ...} or None when this domain does not support the op
    def op_move_object(self, ep, oid: str, place: str) -> dict | None:
        return None

    def op_spawn(self, ep, cls: str, place: str, **kw) -> dict | None:
        return None

    def op_load(self, ep, name: str) -> dict | None:
        return None

    def scenes(self, ep) -> list:
        return []
