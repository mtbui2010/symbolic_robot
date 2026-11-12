"""Profiles: the robot's own fault and duration parameters, one YAML file per profile (<domain>/profiles/<name>.yaml).

    profile: real
    derive:                              # optional: profiles computed from this one when they have no file of their own
      stress: {scale: 3.0}               # probabilities x3, capped at 1
    params:
      slip: {kind: prob, value: 0.05, source: "<where the number comes from>", note: "<what it means>"}

Kinds: `prob` and `prob_map` are probabilities (the `ideal` profile sets them to 0 when it has no file: no failures; a parameter that
is a probability of recovering after a failure, not of failing, says `ideal: keep` and is left alone by `ideal` and `stress`);
`split` (shares of failure codes), `range` (a [low, high] drawn uniformly), `number`, `map` are kept as they are.
Every parameter needs a value and a source label. Nothing here knows any robot.
"""
from __future__ import annotations

import copy
from pathlib import Path

import yaml

PROB_KINDS = ("prob", "prob_map")


class Profile:
    def __init__(self, name: str, params: dict, derive: dict | None = None):
        self.name, self.params, self.derive = name, params, derive or {}

    def get(self, key: str, default=None):
        try:
            return self.params[key]["value"]
        except KeyError:
            if default is not None:
                return default
            raise KeyError(f"profile {self.name!r} has no parameter {key!r}") from None

    def by(self, key: str, label: str):
        """The entry `label` of a map-valued parameter (a probability by clutter, by class ...)."""
        return self.get(key)[label]

    def uniform(self, key: str, u: float) -> float:
        """A value in the [low, high] range parameter `key` from the uniform u."""
        a, b = self.get(key)
        return float(a) + (float(b) - float(a)) * u

    def choose(self, key: str, u: float) -> str:
        """A label from a `split` parameter (shares per label): inverse CDF over the sorted labels."""
        split, acc = self.get(key), 0.0
        for k in sorted(split):
            acc += float(split[k])
            if u < acc:
                return k
        return sorted(split)[-1]

    def source(self, key: str) -> str:
        return str(self.params[key].get("source", ""))

    def keys(self) -> list:
        return list(self.params)

    def with_overrides(self, **kv) -> "Profile":
        p = copy.deepcopy(self.params)
        for k, v in kv.items():
            p[k]["value"] = v
        return Profile(self.name, p, self.derive)


def _map(value, fn):
    return {k: fn(v) for k, v in value.items()} if isinstance(value, dict) else fn(value)


def derived(real: "Profile", name: str) -> "Profile":
    """`ideal`: every probability 0. Other names: only when real declares `derive.<name>.scale`."""
    params = copy.deepcopy(real.params)
    if name == "ideal":
        fn = lambda v: 0.0                                           # noqa: E731
        note = "ideal profile: failure switched off"
    else:
        scale = float((real.derive.get(name) or {}).get("scale", 0))
        if scale <= 0:
            raise KeyError(name)
        fn = lambda v: min(1.0, float(v) * scale)                    # noqa: E731
        note = f"{name} profile: probabilities of real x{scale:g}, capped at 1"
    for p in params.values():
        if p.get("kind") in PROB_KINDS and p.get("ideal") != "keep":
            p["value"] = _map(p["value"], fn)
            p["source"] = f"{note} (real: {p.get('source', '')})"
    return Profile(name, params, real.derive)


def available(profile_dir: Path) -> list:
    names = {p.stem for p in Path(profile_dir).glob("*.yaml")}
    real = _read(Path(profile_dir) / "real.yaml") if "real" in names else None
    if real is not None:
        names |= {"ideal"} | set(real.derive)
    return sorted(names)


def _read(f: Path) -> Profile:
    data = yaml.safe_load(f.read_text()) or {}
    params = data.get("params") or {}
    for k, v in params.items():
        if "value" not in v or not v.get("source"):
            raise ValueError(f"{f.name}: parameter {k} needs a value and a source label")
    return Profile(str(data.get("profile", f.stem)), params, data.get("derive") or {})


def load(profile_dir: Path, name: str = "real") -> Profile:
    f = Path(profile_dir) / f"{name}.yaml"
    if f.exists():
        return _read(f)
    real = Path(profile_dir) / "real.yaml"
    if real.exists():
        try:
            return derived(_read(real), name)
        except KeyError:
            pass
    raise ValueError(f"unknown profile {name!r}; known: {', '.join(available(profile_dir))}")
