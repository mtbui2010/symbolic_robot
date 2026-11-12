"""Domain registry: built-in domains (loaded lazily, so a missing optional package only disables its own domain) plus plug-ins
declared in the entry point group `symbolic_robot.domains` (name = "module:attr", attr a BaseDomain subclass or instance)."""
from __future__ import annotations

import importlib
from importlib import metadata

from .domain import BaseDomain

GROUP = "symbolic_robot.domains"
BUILTIN = {"factory": "symbolic_robot.domains.factory:Factory", "home": "symbolic_robot.domains.home:Home"}
_extra: dict = {}
_cache: dict = {}


def register(name: str, target) -> None:
    """Register a domain class/instance, or a "module:attr" string, under `name` (tests, local plug-ins)."""
    _extra[name] = target
    _cache.pop(name, None)


def _entry_points() -> dict:
    try:
        eps = metadata.entry_points(group=GROUP)
    except TypeError:                                     # python < 3.10
        eps = metadata.entry_points().get(GROUP, [])
    return {e.name: e.value for e in eps}


def names() -> list:
    return sorted({**BUILTIN, **_entry_points(), **_extra})


def get(name: str) -> BaseDomain:
    if name in _cache:
        return _cache[name]
    target = {**BUILTIN, **_entry_points(), **_extra}.get(name)
    if target is None:
        raise KeyError(f"unknown domain {name!r}; known: {', '.join(names())}")
    if isinstance(target, str):
        mod, _, attr = target.partition(":")
        target = getattr(importlib.import_module(mod), attr)
    dom = target() if isinstance(target, type) else target
    _cache[name] = dom
    return dom


def world_labels() -> list:
    """The `world_label` of every domain that can be loaded (for the CLI flags)."""
    out = set()
    for n in names():
        try:
            out.add(get(n).world_label)
        except Exception:                                 # noqa: BLE001 - a broken plug-in must not break the CLI
            pass
    return sorted(out)
