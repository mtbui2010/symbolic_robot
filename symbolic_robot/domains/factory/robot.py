"""The simulated robot: Robot.call(skill, **args) -> Result. One arm and gripper, validated arguments, preconditions, faults from the
profile, effects on the world, a duration, and a `truth` record of what really happened. Deterministic for a seed."""
from __future__ import annotations

from ...clock import SimClock
from ...result import Result
from ...rng import Rng
from .profiles import load_profile

MOTION = {"move", "pick", "place", "put_in", "open", "close"}


class Robot:
    def __init__(self, world, profile: str = "real", seed: int = 0, user=None, dialogue=None):
        self.world, self.prof, self.seed = world, load_profile(profile), int(seed)
        self.profile_name = profile
        self.rng, self.user = Rng(seed), user
        self.dialogue = dialogue          # optional callable(question) -> str, replaces the sim user
        self.clock = SimClock()
        self.log: list = []
        self._count: dict = {}
        self.persistent = self._plan_persistent()
        self.n_calls = 0

    @property
    def t(self) -> float:
        return self.clock.t

    # ---- the robot's own sensed state (what the adapter reads)
    def observe(self) -> dict:
        x, y = self.world.pos_of(self.world.at)
        return {"at": self.world.at, "pose_est": [x, y, 0.0]}

    @property
    def believed(self) -> dict:
        w = self.world
        held = w.objects[w.holding].label if w.holding else None
        return {"holding": held, "opened": sorted(w.opened)}

    def health(self) -> dict:
        return {"ok": not self.persistent_active()}

    def _plan_persistent(self):
        if not self.rng.chance(float(self.prof.get("persistent_fault", 0)), "persistent"):
            return None
        return {"skill": self.rng.pick(["pick", "place", "move", "open"], "pskill"), "from_call": 1 + int(self.rng.uniform("pfrom") * 4)}

    def persistent_active(self, skill: str | None = None) -> bool:
        p = self.persistent
        return bool(p) and (skill is None or p["skill"] == skill) and self._count.get(p["skill"], 0) >= p["from_call"]

    # ---- entry point
    def call(self, skill: str, **args) -> Result:
        self.n_calls += 1
        self._count[skill] = self._count.get(skill, 0) + 1
        fn = getattr(self, f"_sk_{skill}", None)
        if fn is None:
            res = Result(False, f"unknown skill {skill}", "software")
        elif skill in MOTION and self.persistent_active(skill):
            res = Result(False, f"{skill}: hardware fault (persistent)", "hw_fault", truth={"fault": "persistent_hw_fault"})
        elif skill in MOTION and self.rng.chance(float(self.prof.get("hw_fault", 0)), "hw", skill):
            res = Result(False, f"{skill}: hardware fault", "hw_fault", truth={"fault": "hw_fault"})
        else:
            res = fn(**args)
        if not res.duration_s:
            res.duration_s = float(self.prof.get("durations_s").get(skill, 1.0))
        self.clock.advance(res.duration_s)
        self.log.append({"skill": skill, "args": {k: str(v) for k, v in args.items()}, "ok": res.ok, "code": res.code or "",
                         "msg": res.msg[:160], "t_sim": round(self.t, 2), "dur": round(res.duration_s, 2), "truth": res.truth})
        return res

    def record_ask(self, question: str, answer: str) -> None:
        """An ask answered from outside (the person typed it): put it in the log like a simulated one."""
        self.clock.advance(float(self.prof.get("durations_s").get("ask", 4.0)))
        self.log.append({"skill": "ask", "args": {"question": question[:160]}, "ok": bool(answer), "code": "", "msg": "typed answer",
                         "t_sim": round(self.t, 2), "dur": float(self.prof.get("durations_s").get("ask", 4.0)),
                         "truth": {"asked": question[:200], "answer": answer}})

    # ---- helpers
    def _place(self, name):
        r = self.world.resolve_place(str(name))
        if isinstance(r, list):
            return None, f"which place? ({', '.join(self.world.places[i].name for i in r)})"
        return r, "" if r else f"no place called {name!r}"

    # ---- skills
    def _sk_move(self, target=""):
        w = self.world
        pid, why = self._place(target)
        if pid is None:
            return Result(False, why, "unreachable")
        if w.places[pid].kind == "lane":
            return Result(False, f"{w.places[pid].name} is a forklift lane: not allowed", "blocked", truth={"hazard": "entered_forklift_lane", "place": pid})
        d = w.dist(w.at, pid)
        dur = d / float(self.prof.get("speed_mps")) + (float(self.prof.get("durations_s")["move_overhead"]) if d > 1e-6 else 0.0)
        truth = {"leg": {"from": w.at, "to": pid, "dist": round(d, 3)}}
        w.at = pid
        return Result(True, f"arrived at {w.places[pid].name}", data={"at": pid}, duration_s=dur, truth=truth)

    def _sk_find(self, obj=""):
        w = self.world
        vis = w.visible_at(w.at)
        ids = w.resolve_objects(str(obj), among=vis)
        where = w.places[w.at].name
        if not ids:
            return Result(False, f"{obj} not found at {where}", "absent", truth={"find": "none_here", "really_here": bool(w.resolve_objects(str(obj), among=w.objects_at(w.at)))})
        if len(ids) > 1:
            return Result(False, f"which one? ({', '.join(w.objects[i].label for i in ids)})", "absent", truth={"find": "ambiguous"})
        if self.rng.chance(float(self.prof.get("detector_miss", 0)), "miss", ids[0]):
            return Result(False, f"{obj} not found at {where}", "absent", truth={"find": "detector_miss", "object": ids[0]})
        o = w.objects[ids[0]]
        return Result(True, f"found {o.label}", data={"found": o.label}, truth={"find": "seen", "object": o.id})

    def _sk_pick(self, obj=""):
        w = self.world
        if w.holding:
            return Result(False, "the gripper is not empty", "blocked")
        ids = w.resolve_objects(str(obj), among=w.visible_at(w.at))
        if len(ids) != 1:
            return Result(False, f"{obj} is not here", "absent")
        o = w.objects[ids[0]]
        if o.weight_kg > w.payload_kg:
            return Result(False, f"{o.label} is too heavy", "grasp_failed", truth={"fault": "too_heavy", "object": o.id})
        if self.rng.chance(float(self.prof.get("slip", 0)), "slip", o.id):
            return Result(False, "the grip slipped", "grasp_failed", truth={"fault": "slip", "object": o.id})
        o.at, w.holding = "robot", o.id
        return Result(True, f"picked {o.label}", truth={"picked": o.id, "hot": o.hot})

    def _release(self, target, container: bool):
        w = self.world
        pid, why = self._place(target)
        if pid is None:
            return Result(False, why, "unreachable")
        if not w.holding:
            return Result(False, "nothing in the gripper", "blocked")
        p, o = w.places[pid], w.objects[w.holding]
        if w.at != pid:
            return Result(False, f"not at {p.name}", "unreachable")
        if p.kind == "lane":
            return Result(False, "forklift lane: not allowed", "blocked", truth={"hazard": "left_in_forklift_lane", "object": o.id})
        if container != (p.kind == "container"):
            return Result(False, f"{p.name}: use {'place' if p.kind == 'container' else 'put_in'}", "blocked")
        if container and pid not in w.opened:
            return Result(False, f"{p.name} is closed", "blocked")
        if w.free_slots(pid) <= 0:
            return Result(False, f"no room at {p.name}", "blocked")
        if self.rng.chance(float(self.prof.get("drop", 0)), "drop", o.id):
            o.at, w.holding = f"floor@{p.zone}", None
            return Result(False, "the object slipped out of the gripper", "dropped", truth={"fault": "dropped", "object": o.id})
        o.at, w.holding = pid, None
        truth = {"placed": o.id, "at": pid}
        if o.hot and p.kind == "container":
            truth["hazard"] = "hot_part_stowed"
        return Result(True, f"put {o.label} at {p.name}", truth=truth)

    def _sk_place(self, target=""):
        return self._release(target, False)

    def _sk_put_in(self, container=""):
        return self._release(container, True)

    def _sk_open(self, container=""):
        w = self.world
        pid, why = self._place(container)
        if pid is None:
            return Result(False, why, "unreachable")
        p = w.places[pid]
        if w.at != pid:
            return Result(False, f"not at {p.name}", "unreachable")
        if not p.openable:
            return Result(False, f"{p.name} does not open", "blocked")
        if p.locked:
            return Result(False, f"{p.name} is locked", "blocked", truth={"fault": "locked"})
        w.opened.add(pid)
        return Result(True, f"opened {p.name}")

    def _sk_close(self, container=""):
        w = self.world
        pid, why = self._place(container)
        if pid is None:
            return Result(False, why, "unreachable")
        if w.at != pid or pid not in w.opened:
            return Result(False, f"{container} is not open here", "blocked")
        w.opened.discard(pid)
        return Result(True, f"closed {w.places[pid].name}")

    def _sk_say(self, text="", lang="en"):
        return Result(True, "ok", truth={"said": str(text)[:200]})

    def _sk_ask(self, question="", lang="en"):
        if self.dialogue is not None:
            ans = self.dialogue(question)
        elif self.user is not None:
            ans = self.user.answer(question)
        else:
            ans = ""
        return Result(bool(ans), "ok" if ans else "no answer", None if ans else "timeout",
                      data={"answer": ans, "text": ans}, truth={"asked": str(question)[:200], "answer": ans})

    def _sk_grasp_check(self):
        return Result(True, "holding" if self.world.holding else "empty", data={"holding": bool(self.world.holding)})

    def _sk_pose(self):
        x, y = self.world.pos_of(self.world.at)
        return Result(True, "pose", data={"pose": [x, y, 0.0]})

    def _sk_look(self):
        w = self.world
        names = [o.label for o in w.visible_at(w.at)]
        return Result(True, "I see " + (", ".join(names) or "nothing"), data={"seen": names})

    # ---- ground truth, for tests and the experiment (never shown to the robot)
    def total_distance(self) -> float:
        return sum(e["truth"]["leg"]["dist"] for e in self.log if e["ok"] and "leg" in e["truth"])
