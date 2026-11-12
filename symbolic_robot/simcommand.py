"""The generic `sim_command` handler: the ops a test or benchmark script sends to any domain.

Message shape {"cmd": ...} -> {"ok", "msg", ..., "isdone"}. Ops: state, truth, reset, load, move_object, spawn. An op the domain
does not support answers ok=false with a message; nothing else happens.
"""
from __future__ import annotations


class SimCommands:
    def __init__(self, live, on_new_world=None):
        self.live, self.domain = live, live.domain
        self.on_new_world = on_new_world          # called(what) -> list of erased files; the server forgets the robot's memory

    @property
    def ep(self):
        return self.live.episode

    def handle(self, cmd: dict) -> dict:
        fn = getattr(self, f"op_{cmd.get('cmd')}", None)
        if fn is None:
            return {"ok": False, "isdone": False, "msg": f"unknown cmd {cmd.get('cmd')!r}"}
        with self.live.lock:
            try:
                out = fn(cmd)
            except Exception as e:                # noqa: BLE001 - never kill the agent thread
                out = {"ok": False, "msg": f"{type(e).__name__}: {e}"}
        out["isdone"] = bool(out.get("ok"))
        return out

    def _forget(self, cmd: dict) -> list:
        if self.on_new_world is None or str(cmd.get("forget", True)).lower() in ("0", "false", "no", "off"):
            return []
        return list(self.on_new_world() or [])

    def _unsupported(self, op: str) -> dict:
        return {"ok": False, "msg": f"{op} is not supported by domain {self.domain.name!r}"}

    # ---- ops
    def op_state(self, cmd):
        """Objects (body, name, cls, at ...), the catalog of classes, the worlds, the profile and the seed."""
        v = self.domain.view(self.ep)
        objects = [{"body": oid, "name": oid, **o} for oid, o in v.get("objects", {}).items()]
        classes = sorted({o["cls"] for o in v.get("objects", {}).values() if o.get("cls")})
        return {"ok": True, "symbolic": True, "domain": self.domain.name, "world": self.live.kw["world"], "worlds": self.domain.worlds(),
                "scenes": sorted(set(self.domain.worlds()) | set(self.domain.scenes(self.ep))), "objects": objects,
                "catalog": {"objects": classes}, "profile": self.live.kw["profile"], "seed": self.live.kw["seed"]}

    def op_truth(self, cmd):
        wv = self.live.world_view()
        return {"ok": True, **{k: v for k, v in wv.items() if k != "log"}, "busy": self.live.busy, "log": wv["log"][-int(cmd.get("last", 50)):]}

    def op_reset(self, cmd):
        what = cmd.get("what", "all")
        if what not in ("objects", "robot", "all"):
            return {"ok": False, "msg": f"reset what={what!r}: use objects, robot or all"}
        prof = cmd.get("profile")
        if prof and prof not in self.domain.profiles():
            return {"ok": False, "msg": f"unknown profile {prof!r} (have: {', '.join(self.domain.profiles())})"}
        self.live.reset(profile=prof, seed=None if cmd.get("seed") is None else int(cmd["seed"]))
        forgot = self._forget(cmd)
        return {"ok": True, "msg": f"reset (a new episode)" + (f"; memory erased: {', '.join(forgot)}" if forgot else "")}

    def op_load(self, cmd):
        name = str(cmd.get("name") or "")
        if name in self.domain.worlds():
            self.live.reset(world=name)
            forgot = self._forget(cmd)
            return {"ok": True, "msg": f"world {name}" + (", memory erased" if forgot else "")}
        out = self.domain.op_load(self.ep, name)
        return out if out is not None else {"ok": False, "msg": f"no world or scene {name!r} (worlds: {', '.join(self.domain.worlds())})"}

    def op_move_object(self, cmd):
        oid = cmd.get("body") or cmd.get("name")
        place = cmd.get("place")
        if not oid or not place:
            return {"ok": False, "msg": "move_object needs body (or name) and place"}
        out = self.domain.op_move_object(self.ep, str(oid), str(place))
        return out if out is not None else self._unsupported("move_object")

    def op_spawn(self, cmd):
        cls = str(cmd.get("cls") or cmd.get("name") or "").strip()
        place = str(cmd.get("place") or cmd.get("surface") or "").strip()
        if not cls or not place:
            return {"ok": False, "msg": "spawn needs cls and place, e.g. {cls: 'mug', place: '<place id>'}"}
        extra = {k: v for k, v in cmd.items() if k not in ("cmd", "cls", "name", "place", "surface")}
        out = self.domain.op_spawn(self.ep, cls, place, **extra)
        return out if out is not None else self._unsupported("spawn")
