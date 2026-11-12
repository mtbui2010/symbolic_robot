"""Deterministic draws, no wall clock, no Python hash(). Two schemes, both SHA-256 based:

* `Rng`: a draw depends on (seed, a key, the n-th time that key was asked), not on the order of other calls, so two runs with the
  same seed see the same fault at the same event even when their plans differ.
* `CallDraws`: one fixed vector of `n_slots` uniforms per skill call, keyed by (seed, skill, arguments, n-th call with these
  arguments); each rule of a skill reads its own slot.
"""
from __future__ import annotations

import hashlib
import json
import random


class Rng:
    def __init__(self, seed: int):
        self.seed = int(seed)
        self._n: dict = {}

    def uniform(self, *key) -> float:
        k = "|".join(str(x) for x in key)
        n = self._n[k] = self._n.get(k, 0) + 1
        h = hashlib.sha256(f"{self.seed}|{k}|{n}".encode()).digest()
        return int.from_bytes(h[:8], "big") / 2 ** 64

    def chance(self, p: float, *key) -> bool:
        return p > 0 and self.uniform(*key) < p

    def pick(self, seq, *key):
        seq = list(seq)
        return seq[min(len(seq) - 1, int(self.uniform(*key) * len(seq)))] if seq else None


def derive_seed(*parts) -> int:
    return int.from_bytes(hashlib.sha256("|".join(map(str, parts)).encode("utf-8")).digest()[:8], "big")


def canon_args(args: dict) -> str:
    """Stable text of a call's arguments (sorted keys; callback-like entries dropped)."""
    clean = {k: v for k, v in sorted((args or {}).items()) if k not in ("node", "wait", "log_fn")}
    return json.dumps(clean, sort_keys=True, default=str, ensure_ascii=False)


class CallDraws:
    """`begin(skill, args)` -> Draw with `.u` (n_slots uniforms in [0, 1)) and `.attempt(k)` (the vector of the k-th internal attempt)."""

    def __init__(self, seed: int, n_slots: int = 16):
        self.seed, self.n_slots = int(seed), n_slots
        self._nth: dict = {}

    def begin(self, skill: str, args: dict) -> "Draw":
        key = (skill, canon_args(args))
        n = self._nth[key] = self._nth.get(key, 0) + 1
        return Draw(self, skill, key[1], n)

    def reset(self) -> None:
        self._nth.clear()


class Draw:
    def __init__(self, owner: CallDraws, skill: str, args: str, n: int):
        self.owner, self.skill, self.args, self.n = owner, skill, args, n
        self.u = self._vec(0)

    def _vec(self, attempt: int) -> list:
        rng = random.Random(derive_seed(self.owner.seed, self.skill, self.args, self.n, attempt))
        return [rng.random() for _ in range(self.owner.n_slots)]

    def attempt(self, k: int) -> list:
        return self.u if k == 0 else self._vec(k)
