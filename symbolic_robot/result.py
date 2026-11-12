"""What one skill call returns. `truth` holds what really happened in the simulation; the robot never sees it."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Result:
    ok: bool
    msg: str = ""
    code: str | None = None                 # a robot_agent FailureCode value when ok is False
    data: dict = field(default_factory=dict)
    duration_s: float = 0.0
    truth: dict = field(default_factory=dict)

    def to_legacy(self) -> dict:
        """The dict robot_agent skill functions return: {isdone, msg, code?, **data}."""
        out = {"isdone": self.ok, "msg": self.msg}
        if self.code:
            out["code"] = self.code
        out.update(self.data)
        return out
