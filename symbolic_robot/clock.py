"""Simulated time. `t` only moves when a skill reports a duration; nothing ever waits in real time."""
from __future__ import annotations


class SimClock:
    def __init__(self):
        self.t = 0.0

    def advance(self, dt: float) -> float:
        self.t += dt
        return self.t
