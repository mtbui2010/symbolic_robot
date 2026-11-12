"""The `home` domain: a thin wrapper over the frozen `homeloop_robot` package (imported, never copied or modified).

It exposes that package's houses and episodes through the domain protocol, so the generic server, backend and sim_command handler
serve them. If `homeloop_robot` is not installed the domain reports "not available" and everything else works.
The robot_agent pack is `homeloop_robot` itself (its own configs/); nothing of it is duplicated here.
"""
from __future__ import annotations

import dataclasses
import importlib
import math

from ...domain import BaseDomain

NO_SUCH_OBJECT = ": no such object"       # the simulator's wording when an object does not exist in its world


class _AsARobotWouldSay:
    """Proxy of the episode's robot: a failure text drops the simulator's ': no such object' (a real robot can only say it did not
    find the object). Code, data and everything else are unchanged."""

    def __init__(self, robot):
        self._r = robot

    def call(self, skill, /, **args):
        res = self._r.call(skill, **args)
        msg = str(getattr(res, "msg", "") or "")
        return res if NO_SUCH_OBJECT not in msg else dataclasses.replace(res, msg=msg.replace(NO_SUCH_OBJECT, ""))

    def __getattr__(self, name):
        return getattr(self._r, name)


class Home(BaseDomain):
    name = "home"
    description = "simulated household (frozen homeloop_robot package): houses, rooms, furniture, a person; profiles ideal | real | stress"
    pack = "homeloop_robot"
    world_label = "house"
    default_model = "hl-understand-p3-s700"
    live_opts = {"realistic_msgs": True}     # the server hides the simulator's wording; make_episode itself is the package's, unchanged

    def _pkg(self):
        return importlib.import_module("homeloop_robot")

    def available(self):
        try:
            self._pkg()
        except ImportError:
            return "homeloop_robot is not installed (pip install -e <path to the frozen homeloop_robot>)"
        return None

    def worlds(self) -> list:
        return list(self._pkg().list_houses()) if self.available() is None else []

    def default_world(self) -> str:
        return "senior_flat"

    def profiles(self) -> list:
        return list(importlib.import_module("homeloop_robot.profiles").list_profiles()) if self.available() is None else []

    def make_episode(self, world, profile, seed, seed_state=0, lang="en", key="live", realistic_msgs=False, **opts):
        ep = self._pkg().make_episode(world, int(seed_state), profile, int(seed), lang=lang, key=key)
        if realistic_msgs:
            ep.robot = _AsARobotWouldSay(ep.robot)
        return ep

    def clock_t(self, ep) -> float:
        return float(ep.clock.t)

    def pose(self, ep) -> tuple:
        x, y, yaw = ep.world.robot.pose
        return (x, y, math.radians(yaw))

    def view(self, ep) -> dict:
        w = ep.world
        return {"objects": {oid: {"cls": o.cls, "at": o.at, "color": (o.attrs or {}).get("color")} for oid, o in w.objects.items()},
                "people": {pid: {"x": p.pos[0], "y": p.pos[1]} for pid, p in w.people.items()},
                "robot": {"holding": getattr(w.robot, "holding", None)}}

    def env(self, ep):
        return importlib.import_module("homeloop_robot.configs.tasks").env_for(ep.world)

    def planner_env(self) -> dict:
        return {"ASK_SOURCE": "1", "INPUT_PIVOT": "both", "TRANSLATE_RETRY": "1", "ASK_SOURCE_REASK": "1", "ASK_SOURCE_ROOM": "1",
                "ASK_SOURCE_CLARIFY": "1", "ASK_SOURCE_NEAR": "1", "SEARCH_ROUTE_WEIGHT": "0.3"}

    def install_pack(self, live) -> None:
        importlib.import_module("homeloop_robot.configs.backend").set_backend(live)

    def op_move_object(self, ep, oid, place):
        w = ep.world
        if oid not in w.objects or place not in w.places:
            return {"ok": False, "msg": f"no object {oid!r} or no place {place!r}"}
        if getattr(w.robot, "holding", None) == oid:
            w.robot.holding = None
        w.objects[oid].at = place
        return {"ok": True, "msg": f"{oid} is now at {place}"}

    def op_spawn(self, ep, cls, place, color="", obj_id="", **kw):
        from homeloop_robot.world import Obj
        w = ep.world
        if place not in w.places:
            return {"ok": False, "msg": f"unknown place {place!r}; places: {', '.join(sorted(w.places))}"}
        if w.free_slots(place) <= 0:
            return {"ok": False, "msg": f"{place} is full"}
        oid, n = str(obj_id or ""), 1
        while not oid:
            oid = f"{cls}_{n}" if f"{cls}_{n}" not in w.objects else ""
            n += 1
        if oid in w.objects:
            return {"ok": False, "msg": f"object id {oid!r} already exists"}
        w.objects[oid] = Obj(id=oid, cls=cls, attrs={"color": color} if color else {}, at=place,
                             inside=w.places[place].kind == "container", alt=[])
        return {"ok": True, "msg": f"{oid} is now at {place}", "id": oid, "at": place}
