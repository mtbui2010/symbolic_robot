"""The fixed scripted-call program behind tests/home/parity/home_calls.json.gz.

The baseline was recorded from the standalone household simulator package (tag sim-freeze-r19, HEAD ce47651) BEFORE it was merged into
this repository: 5 houses x 3 profiles x 2 seeds x 2 languages, to_json() of every result, the simulated clock and every object's place.
`python tests/home/parity/calls.py OUT.json` writes the same file from the current package (sorted keys), to compare with `gzip -dc`."""
from __future__ import annotations

import importlib
import json
import sys

HOUSES = ["senior_flat", "studio_flat", "couple_flat", "family_house", "korean_apt_59"]


def script(world):
    objs = sorted(world.objects.values(), key=lambda o: o.id)[:3]
    places = [p.id for p in world.places.values() if p.kind not in ("floor", "dock")]
    plan = [("look", {}), ("say", {"text": "hello", "lang": "en"}), ("pose", {})]
    for i, o in enumerate(objs):
        t = places[(i * 2 + 1) % len(places)]
        plan += [("move", {"target": o.at}), ("find", {"obj": o.id}), ("open", {"container": o.at}), ("pick", {"obj": o.id}),
                 ("grasp_check", {}), ("move", {"target": t}), ("place", {"target": t}), ("close", {"container": o.at}),
                 ("vlm_check", {"obj": o.id}), ("handover", {}), ("look", {})]
    plan += [("ask", {"question": "Where is the mug?", "lang": "en"}), ("wait", {"seconds": 2}), ("announce", {"text": "hi"}),
             ("dock", {}), ("nosuchskill", {})]
    return plan


def record(package: str = "symbolic_robot.domains.home") -> dict:
    pkg = importlib.import_module(package)
    out = {"houses": list(pkg.list_houses()), "profiles": list(importlib.import_module(package + ".profiles").list_profiles())}
    for house in HOUSES:
        for prof in ("ideal", "real", "stress"):
            for seed in (11, 12):
                for lang in ("en", "ko"):
                    ep = pkg.make_episode(house, 0, prof, seed, lang=lang, key="live")
                    res = [(s, ep.robot.call(s, **a).to_json()) for s, a in script(ep.world)]
                    out[f"{house}/{prof}/{seed}/{lang}"] = {"res": res, "clock": ep.clock.t,
                                                            "objs": {k: o.at for k, o in sorted(ep.world.objects.items())}}
    return out


if __name__ == "__main__":
    json.dump(record(), open(sys.argv[1], "w"), sort_keys=True, indent=0, default=str)
