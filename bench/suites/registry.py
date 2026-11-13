"""Suite registry: bench/suites/<domain>/<suite>. A suite module calls `register(Suite(...))` when imported."""
from __future__ import annotations

import importlib

from ..suite import Suite

_SUITES: dict = {}
MODULES = ("bench.suites.factory", "bench.suites.home.register")


def register(s: Suite) -> Suite:
    _SUITES[(s.domain, s.name)] = s
    return s


def load_all() -> None:
    for m in MODULES:
        importlib.import_module(m)


def get(domain: str, name: str) -> Suite:
    load_all()
    try:
        return _SUITES[(domain, name)]
    except KeyError:
        known = ", ".join(f"{d}/{n}" for d, n in sorted(_SUITES))
        raise KeyError(f"no suite {domain}/{name}; known: {known}") from None


def listing() -> list:
    load_all()
    return [(d, n, s.description) for (d, n), s in sorted(_SUITES.items())]
