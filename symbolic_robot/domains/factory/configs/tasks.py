"""robot_agent ENV of a floor: env_for(world). `ENV` is the floor named by $SYMBOLIC_FACTORY_FLOOR (default assembly_hall)."""
from __future__ import annotations

import os

from ..world import World, load_floor

DOCK_WORDS = ["charge", "charging", "charging station"]


def env_for(world: World, keep_lanes: bool = False) -> dict:
    env = {}
    for pid, p in sorted(world.places.items()):
        if p.kind == "lane" and not keep_lanes:        # a keep-out region of the map, not a place the robot goes to or searches (the engine searches every ENV place)
            continue
        zone = p.zone.replace("_", " ")
        aliases = [p.name, f"{p.name} in the {zone}", pid.split("@")[0].replace("_", " ")] + list(p.aliases)
        if pid == world.dock:
            aliases += DOCK_WORDS
        seen, al = set(), []
        for a in aliases:
            if a and a.lower() not in seen:
                seen.add(a.lower())
                al.append(a)
        entry = {"loc": {"x": p.pos[0], "y": p.pos[1], "rz": 0.0}, "height": 0.8, "default_mode": "front", "aliases": al,
                 "openable": p.openable, "surface": p.kind in ("surface", "bin") and p.slots > 0}
        if p.category:
            entry["category"] = p.category
        if p.kind == "lane" or pid == world.dock:       # keep-out region / charger: the engine's search must not pick them (ENV `search: false`)
            entry["search"] = False
        env[pid] = entry
    return env


# SYMBOLIC_FACTORY_KEEP_LANES=1 puts the lane on the map again: only to reproduce an engine finding (see docs/bench.md)
ENV = env_for(load_floor(os.environ.get("SYMBOLIC_FACTORY_FLOOR", "assembly_hall")), os.environ.get("SYMBOLIC_FACTORY_KEEP_LANES") == "1")
