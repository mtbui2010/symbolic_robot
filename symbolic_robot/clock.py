"""Simulated time. `t` only moves when a skill reports a duration; `speedup` sets how long the live server really waits."""
from __future__ import annotations

import time


class SimClock:
    def __init__(self, speedup: float = 0.0, max_wall_s: float = 12.0):
        self.t = 0.0
        self.speedup, self.max_wall_s = float(speedup or 0.0), float(max_wall_s)

    def advance(self, dt: float) -> float:
        self.t += dt
        return self.t

    def wall_for(self, dt: float) -> float:
        """Real seconds to wait for `dt` simulated seconds (0 when speedup is 0)."""
        return min(self.max_wall_s, dt / self.speedup) if self.speedup > 0 and dt > 0 else 0.0

    def pace(self, dt: float, cancel=lambda: False, slice_s: float = 0.1) -> None:
        left = self.wall_for(dt)
        while left > 0 and not cancel():
            step = min(slice_s, left)
            time.sleep(step)
            left -= step
