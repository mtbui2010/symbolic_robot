"""The live backend: wraps a domain's episode so the world can be replaced between runs, every call is logged with its truth,
motion takes (scaled) wall time, and the device-agent interface robot_agent's GET /agent/<name>/get expects is served.
Anything not defined here is the inner robot's (observe, health, believed, world ...), so a pack's skills use it as the robot."""
from __future__ import annotations

import math
import threading
import time

from .clock import SimClock


def _point_at(pts, s):
    """(x, y, heading_rad) at arc length s along the polyline pts."""
    acc = 0.0
    for a, b in zip(pts, pts[1:]):
        seg = math.dist(a, b)
        if seg > 1e-9 and acc + seg >= s:
            t = (s - acc) / seg
            return a[0] + t * (b[0] - a[0]), a[1] + t * (b[1] - a[1]), math.atan2(b[1] - a[1], b[0] - a[0])
        acc += seg
    a, b = (pts[-2], pts[-1]) if len(pts) > 1 else (pts[0], pts[0])
    return b[0], b[1], (math.atan2(b[1] - a[1], b[0] - a[0]) if a != b else 0.0)


class LiveBackend:
    def __init__(self, domain, world: str, profile: str, seed: int = 0, speedup: float = 0.0, hz: float = 15.0, **opts):
        self.domain = domain
        self.kw = {"world": world, "profile": profile, "seed": int(seed), **opts}
        self.pacer = SimClock(speedup)
        self.hz = hz
        self.lock = threading.RLock()
        self.busy = ""
        self.log: list = []
        self.on_new_world = None                   # called(backend) after the world was replaced (the server refreshes ENV and MAP)
        self._new_episode()

    # ---- episode
    def _new_episode(self) -> None:
        self.episode = self.domain.make_episode(**self.kw)
        self.inner = self.domain.robot(self.episode)
        x, y, yaw = self.domain.pose(self.episode)
        self._disp = (x, y, yaw)
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
        start = d.pose(ep)
        self.busy = skill
        try:
            with self.lock:
                res = self.inner.call(skill, **args)
            dur = float(getattr(res, "duration_s", 0.0) or 0.0)
            end = d.pose(ep)
            pts = d.path(ep, start[:2], end[:2]) if math.dist(start[:2], end[:2]) > 1e-6 else None
            if pts and self.pacer.speedup > 0:
                self._replay(pts, end[2], self.pacer.wall_for(dur))
            else:
                self.pacer.pace(dur)
                self._disp = end
        finally:
            self.busy = ""
        self.log.append({"t_wall": time.time(), "skill": skill, "args": {k: str(v) for k, v in args.items()}, "ok": bool(res.ok),
                         "code": str(getattr(res, "code", None) or ""), "msg": str(res.msg)[:160], "t_sim": d.clock_t(ep), "dur": dur,
                         "truth": getattr(res, "truth", None) or {}})
        return res

    def _replay(self, pts, yaw_end, real_s):
        length = sum(math.dist(a, b) for a, b in zip(pts, pts[1:]))
        n = max(1, int(real_s * self.hz))
        for i in range(1, n + 1):
            self._disp = _point_at(pts, length * i / n)
            time.sleep(real_s / n)
        self._disp = (pts[-1][0], pts[-1][1], yaw_end)

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
        x, y, yaw = self._disp
        view = self.domain.view(self.episode).get("robot", {})
        return {**view, "x": round(x, 3), "y": round(y, 3), "yaw": round(yaw, 4), "busy": self.busy,
                "t_sim": round(self.domain.clock_t(self.episode), 2)}

    def world_view(self) -> dict:
        view = self.domain.view(self.episode)
        log = self.domain.call_log(self.episode)
        return {**view, "robot": self.snapshot(), "log": list(self.log if log is None else log),
                "profile": self.kw["profile"], "seed": self.kw["seed"], "world": self.kw["world"]}
