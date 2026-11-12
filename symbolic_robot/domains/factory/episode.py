"""make_episode(floor, profile, seed) -> Episode(world, robot)."""
from __future__ import annotations

from dataclasses import dataclass

from .robot import Robot
from .user import SimUser
from .world import World, load_floor


@dataclass
class Episode:
    world: World
    robot: Robot
    floor: str
    profile: str
    seed: int

    @property
    def clock(self):
        return self.robot.clock

    @property
    def t(self) -> float:
        return self.robot.t


def make_episode(floor: str = "assembly_hall", profile: str = "real", seed: int = 0, policy: str | None = None, target: str = "") -> Episode:
    world = load_floor(floor)
    user = SimUser(world, policy, seed, target) if policy else None
    return Episode(world, Robot(world, profile, seed, user), floor, profile, seed)
