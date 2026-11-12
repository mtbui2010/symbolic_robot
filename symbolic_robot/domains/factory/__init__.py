"""The `factory` domain: a small data-driven simulated factory floor (floors/*.yaml), one arm and gripper, fault profiles.
Python holds the engine only; every fact of a floor, an object class or a fault rate is in a YAML file."""
from __future__ import annotations


from ...domain import BaseDomain
from .episode import Episode, make_episode  # noqa: F401
from .profiles import list_profiles
from .world import Obj, list_floors


class Factory(BaseDomain):
    name = "factory"
    description = "simulated factory floor: zones, benches, bins, a lockable cabinet, a forklift lane; floors/*.yaml"
    pack = "symbolic_robot.domains.factory"
    world_label = "floor"
    default_model = "hl-understand-p3-s700"

    def worlds(self) -> list:
        return list_floors()

    def default_world(self) -> str:
        return "assembly_hall"

    def profiles(self) -> list:
        return list_profiles()

    def make_episode(self, world, profile, seed, policy=None, target="", **opts):
        return make_episode(world, profile, int(seed), policy, target)

    def pose(self, ep) -> tuple:
        x, y = ep.world.pos_of(ep.world.at)
        return (x, y, 0.0)

    def view(self, ep) -> dict:
        w = ep.world
        return {"objects": w.snapshot(), "robot": {"at": w.at, "holding": w.holding}, "floor": ep.floor}

    def call_log(self, ep):
        return ep.robot.log

    def env(self, ep):
        from .configs.tasks import env_for
        return env_for(ep.world)

    def planner_env(self) -> dict:
        return {"ASK_SOURCE": "1", "ASK_SOURCE_REASK": "1", "SEARCH_ROUTE_WEIGHT": "0.3"}

    def sim_user_opts(self) -> dict:
        return {"policy": "knows"}

    def install_pack(self, live) -> None:
        from .configs.backend import set_backend
        set_backend(live)

    def op_move_object(self, ep, oid, place):
        w = ep.world
        pid = w.resolve_place(place)
        if oid not in w.objects or not isinstance(pid, str):
            return {"ok": False, "msg": f"no object {oid!r} or no single place {place!r}"}
        if w.holding == oid:
            w.holding = None
        w.objects[oid].at = pid
        return {"ok": True, "msg": f"{oid} is now at {pid}"}

    def op_spawn(self, ep, cls, place, variant="", **kw):
        w = ep.world
        pid = w.resolve_place(place)
        if cls not in w.catalog or not isinstance(pid, str):
            return {"ok": False, "msg": f"unknown class {cls!r} (classes: {', '.join(sorted(w.catalog))}) or no single place {place!r}"}
        n = 1
        while f"{cls}_{n}" in w.objects:
            n += 1
        c = w.catalog[cls]
        o = Obj(f"{cls}_{n}", cls, str(variant), float(c.get("weight_kg", 0.5)), bool(c.get("hot", False)), pid)
        if any(x.label == o.label for x in w.objects.values()):
            return {"ok": False, "msg": f"an object named {o.label!r} exists: give a variant"}
        if w.free_slots(pid) <= 0:
            return {"ok": False, "msg": f"{pid} is full"}
        w.objects[o.id] = o
        return {"ok": True, "msg": f"{o.id} is now at {pid}", "id": o.id, "at": pid}
