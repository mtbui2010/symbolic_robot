"""The server-side backend: wraps a domain's episode so the world can be replaced between runs, every call is logged with its truth,
and the device-agent interface robot_agent's GET /agent/<name>/get expects is served. Nothing waits in real time.
Anything not defined here is the inner robot's (observe, health, believed, world ...), so a pack's skills use it as the robot."""
from __future__ import annotations

import threading
import time


class LiveBackend:
    def __init__(self, domain, world: str, profile: str, seed: int = 0, **opts):
        self.domain = domain
        self.kw = {"world": world, "profile": profile, "seed": int(seed), **opts}
        self.lock = threading.RLock()
        self.busy = ""
        self.log: list = []
        self.on_new_world = None                   # called(backend) after the world was replaced (the server refreshes ENV)
        self._new_episode()

    # ---- episode
    def _new_episode(self) -> None:
        self.episode = self.domain.make_episode(**self.kw)
        self.inner = self.domain.robot(self.episode)
        self.busy, self.log = "", []

    def reset(self, **kw) -> None:
        """A fresh episode. kw (profile, seed, world, or any domain option) updates what the next episodes are made from."""
        with self.lock:
            changed = kw.get("world") not in (None, self.kw["world"])
            self.kw.update({k: v for k, v in kw.items() if v is not None})
            self._new_episode()
        if changed and self.on_new_world:
            self.on_new_world(self)

    def __getattr__(self, name):
        if name in ("inner", "episode", "domain"):
            raise AttributeError(name)
        return getattr(self.inner, name)

    # ---- skill calls
    def call(self, skill: str, **args):
        d, ep = self.domain, self.episode
        self.busy = skill
        try:
            with self.lock:
                res = self.inner.call(skill, **args)
            dur = float(getattr(res, "duration_s", 0.0) or 0.0)
        finally:
            self.busy = ""
        self.log.append({"t_wall": time.time(), "skill": skill, "args": {k: str(v) for k, v in args.items()}, "ok": bool(res.ok),
                         "code": str(getattr(res, "code", None) or ""), "msg": str(res.msg)[:160], "t_sim": d.clock_t(ep), "dur": dur,
                         "truth": getattr(res, "truth", None) or {}})
        return res

    def record_ask(self, question: str, answer: str) -> None:
        """An ask answered from outside (a person typed or said it): put it in the log like a simulated one."""
        fn = getattr(self.inner, "record_ask", None)
        if fn is not None:
            fn(question, answer)
        else:
            self.log.append({"t_wall": time.time(), "skill": "ask", "args": {"question": question[:160]}, "ok": bool(answer), "code": "",
                             "msg": "typed answer", "t_sim": self.domain.clock_t(self.episode), "dur": 0.0,
                             "truth": {"asked": question[:200], "answer": answer}})

    # ---- views
    def snapshot(self) -> dict:
        x, y, yaw = self.domain.pose(self.episode)
        view = self.domain.view(self.episode).get("robot", {})
        return {**view, "x": round(x, 3), "y": round(y, 3), "yaw": round(yaw, 4), "busy": self.busy,
                "t_sim": round(self.domain.clock_t(self.episode), 2)}

    def world_view(self) -> dict:
        view = self.domain.view(self.episode)
        log = self.domain.call_log(self.episode)
        return {**view, "robot": self.snapshot(), "log": list(self.log if log is None else log),
                "profile": self.kw["profile"], "seed": self.kw["seed"], "world": self.kw["world"]}
