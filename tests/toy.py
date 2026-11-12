"""A toy domain written only against the public protocol: it shows (and tests) that a new domain needs no change in the core."""
from __future__ import annotations

from symbolic_robot.clock import SimClock
from symbolic_robot.domain import BaseDomain
from symbolic_robot.result import Result
from symbolic_robot.rng import Rng


class ToyRobot:
    def __init__(self, p_fail, seed):
        self.p_fail, self.rng, self.clock, self.at = p_fail, Rng(seed), SimClock(), "a"
        self.items = {"cup": "a"}

    @property
    def t(self):
        return self.clock.t

    def call(self, skill, **args):
        if self.rng.chance(self.p_fail, "fail", skill):
            res = Result(False, "failed", "hw_fault", duration_s=1.0, truth={"fault": "toy"})
        else:
            if skill == "go":
                self.at = args["to"]
            res = Result(True, "ok", duration_s=2.0)
        self.clock.advance(res.duration_s)
        return res


class ToyEpisode:
    def __init__(self, world, profile, seed):
        self.world = world
        self.robot = ToyRobot(0.0 if profile == "ideal" else 0.5, seed)


class Toy(BaseDomain):
    name = "toy"
    description = "two places and a cup"
    world_label = "room"

    def worlds(self):
        return ["small", "big"]

    def profiles(self):
        return ["ideal", "real"]

    def make_episode(self, world, profile, seed, **opts):
        return ToyEpisode(world, profile, seed)

    def pose(self, ep):
        return ({"a": 0.0, "b": 3.0}[ep.robot.at], 0.0, 0.0)

    def view(self, ep):
        return {"objects": {k: {"cls": k, "at": v} for k, v in ep.robot.items.items()}, "robot": {"at": ep.robot.at}}

    def op_move_object(self, ep, oid, place):
        ep.robot.items[oid] = place
        return {"ok": True, "msg": f"{oid} is now at {place}"}
