"""The simulated floor: zones, places (surfaces, bins, containers, a forklift lane) and objects, loaded from floors/*.yaml.
No fact of any floor is in this file."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import yaml

FLOOR_DIR = Path(__file__).with_name("floors")
FLOORS = {"assembly_hall", "small_workshop"}


def list_floors() -> list:
    return sorted(p.stem for p in FLOOR_DIR.glob("*.yaml") if p.stem != "catalog")


def _singular(word: str) -> str:
    """'ties' -> 'tie', 'glasses' -> 'glass': a detector that names 'cable tie' sees 'cable ties'."""
    if len(word) > 3 and word.endswith("sses"):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith("ss"):
        return word[:-1]
    return word


def norm(s: str) -> str:
    """lower case singular words, '_' and '-' as spaces, a leading article dropped."""
    w = " ".join(_singular(x) for x in re.sub(r"[_\-]+", " ", str(s or "")).lower().split())
    for a in ("the ", "a ", "an "):
        if w.startswith(a):
            return w[len(a):]
    return w


@dataclass
class Place:
    id: str
    name: str
    zone: str
    pos: tuple
    kind: str = "surface"
    slots: int = 4
    locked: bool = False
    category: str = ""
    aliases: list = field(default_factory=list)

    @property
    def openable(self) -> bool:
        return self.kind == "container"

    @property
    def names(self) -> set:
        return {norm(self.name), norm(self.id), norm(self.id.split("@")[0])} | {norm(a) for a in self.aliases}


@dataclass
class Obj:
    id: str
    cls: str
    variant: str
    weight_kg: float
    hot: bool
    at: str                     # a place id, "robot", or "floor@<zone>" after a drop

    @property
    def label(self) -> str:
        return f"{self.variant} {self.cls}".strip()


class World:
    def __init__(self, data: dict, catalog: dict):
        self.catalog = catalog
        self.floor = data["floor"]
        self.dock = data["dock"]
        self.payload_kg = float(data.get("payload_kg", 5.0))
        self.zones = {z: (float(v["x"]), float(v["y"])) for z, v in data["zones"].items()}
        self.places: dict = {}
        for p in data["places"]:
            zone = p["id"].split("@")[1]
            self.places[p["id"]] = Place(p["id"], p["name"], zone, tuple(float(v) for v in p["pos"]), p.get("kind", "surface"),
                                         int(p.get("slots", 4)), bool(p.get("locked", False)), p.get("category", ""), list(p.get("aliases", [])))
        self.objects: dict = {}
        for o in data["objects"]:
            c = catalog[o["cls"]]
            self.objects[o["id"]] = Obj(o["id"], o["cls"], o.get("variant", ""), float(c.get("weight_kg", 0.5)), bool(c.get("hot", False)), o["at"])
        labels = [o.label for o in self.objects.values()]
        assert len(labels) == len(set(labels)), "object labels must be unique"
        assert self.dock in self.places
        for o in self.objects.values():
            assert o.at in self.places, f"{o.id} starts at an unknown place {o.at}"
        self.at = self.dock
        self.holding = None
        self.opened: set = set()

    # ---- geometry
    def pos_of(self, pid: str) -> tuple:
        if pid in self.places:
            return self.places[pid].pos
        zone = pid.split("@")[-1]
        return self.zones.get(zone, (0.0, 0.0))

    def dist(self, a: str, b: str) -> float:
        return math.dist(self.pos_of(a), self.pos_of(b))

    # ---- lookup by words
    def resolve_place(self, name: str):
        """-> a place id, a list of ids when ambiguous, or None."""
        if name in self.places:
            return name
        n = norm(name)
        hit = [p.id for p in self.places.values() if n in p.names]
        return hit[0] if len(hit) == 1 else (hit or None)

    def resolve_objects(self, name: str, among=None) -> list:
        """Object ids whose label contains every word of ``name`` (exact label first)."""
        n = norm(name)
        pool = [o for o in (among if among is not None else self.objects.values())]
        exact = [o.id for o in pool if norm(o.label) == n or o.id == name]
        if exact:
            return exact
        w = set(n.split())
        return [o.id for o in pool if w and w <= set(norm(o.label).split())]

    # ---- state
    def objects_at(self, pid: str) -> list:
        return [o for o in self.objects.values() if o.at == pid]

    def visible_at(self, pid: str) -> list:
        """What a camera at place ``pid`` can see: nothing inside a closed container."""
        p = self.places.get(pid)
        if p is not None and p.openable and pid not in self.opened:
            return []
        return self.objects_at(pid)

    def free_slots(self, pid: str) -> int:
        return self.places[pid].slots - len(self.objects_at(pid))

    def snapshot(self) -> dict:
        return {oid: {"cls": o.cls, "at": o.at, "label": o.label, "color": o.variant} for oid, o in self.objects.items()}


@lru_cache(maxsize=None)
def _read_yaml(path: str):
    """Parsed floor / catalog files (the World copies what it needs and never changes them)."""
    return yaml.safe_load(Path(path).read_text())


def load_floor(name: str) -> World:
    path = FLOOR_DIR / f"{name}.yaml"
    if not path.exists():
        raise ValueError(f"unknown floor {name!r}; known: {', '.join(list_floors())}")
    return World(_read_yaml(str(path)), _read_yaml(str(FLOOR_DIR / "catalog.yaml"))["classes"])
