"""The simulated person, used by `--dialogue sim` and by tests. It answers from the sim's truth by an answer policy:
knows (the true place), unknown ("I do not know."), wrong (a real place where the object is not; the true place when asked again).
The experiment runner has its own copy of the policy because it answers through the HTTP API, from outside the server."""
from __future__ import annotations

import re

from ...rng import Rng

DONT_KNOW = "I do not know."


class SimUser:
    def __init__(self, world, policy: str = "knows", seed: int = 0, target: str = ""):
        self.world, self.policy, self.target, self.rng = world, policy, target, Rng(seed)
        self.asked = 0

    def _target_of(self, question: str) -> str:
        if self.target:
            return self.target
        q = str(question).lower()
        hit = [o.label for o in self.world.objects.values() if o.label.lower() in q]
        return max(hit, key=len) if hit else ""

    def _true_place(self) -> str | None:
        ids = self.world.resolve_objects(self.target)
        return self.world.objects[ids[0]].at if ids else None

    def _wrong_place(self, true: str) -> str:
        cands = sorted(p.id for p in self.world.places.values() if p.kind in ("surface", "bin") and p.id != true and p.slots > 0)
        return self.rng.pick(cands, "wrong", self.target) or true

    def answer(self, question: str) -> str:
        q = str(question).lower()
        if "where" not in q:
            return "Yes."
        self.asked += 1
        self.target = self._target_of(question)
        true = self._true_place()
        if true is None or self.policy == "unknown":
            return DONT_KNOW
        name = lambda pid: "the " + self.world.places[pid].name   # noqa: E731
        if self.policy == "wrong" and self.asked == 1:
            return f"I think it is at {name(self._wrong_place(true))}."
        return f"It is at {name(true)}."


def question_kind(q: str) -> str:
    """'source' for 'Where is the X?', 'dest' for 'where should I put/bring ...', 'other' otherwise (wording tests only)."""
    s = q.lower()
    if re.search(r"where (should|do you want|shall).*(put|bring|take|place|go)|where to", s):
        return "dest"
    return "source" if "where" in s else "other"
