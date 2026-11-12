"""Generate the task set of an experiment from a world description, by a seeded script (nothing is hand-picked).

Input (any domain): objects [{id, label, at}], places [{id, name, spoken}] (destinations: surfaces the robot may put things on),
true_where(obj) is `at`. Output: tasks with a request text, the object, the destination, the answer policy of the simulated person
('knows' | 'unknown' | 'wrong' for requests that name no source; None when the request names it) and the texts the person says.
"""
from __future__ import annotations

import random

POLICIES = ("knows", "unknown", "wrong")


def generate_tasks(objects: list, places: list, n: int, seed: int, given_every: int = 6, spoken_all: dict | None = None) -> list:
    rnd = random.Random(seed)
    spoken = {**(spoken_all or {}), **{p["id"]: p["spoken"] for p in places}}   # spoken_all: also the places an object may start in (containers)
    objs = sorted(objects, key=lambda o: o["id"])
    rnd.shuffle(objs)
    pairs, used = [], set()
    rounds = 0
    while len(pairs) < n and rounds < 10:
        for o in objs:
            if len(pairs) >= n:
                break
            dests = [p["id"] for p in places if p["id"] != o["at"] and (o["id"], p["id"]) not in used]
            if not dests:
                continue
            d = rnd.choice(sorted(dests))
            used.add((o["id"], d))
            pairs.append((o, d))
        rounds += 1
    tasks, n_ask = [], 0
    for i, (o, d) in enumerate(pairs):
        given = (i + 1) % given_every == 0
        t = {"id": f"t{i:02d}", "object": o["label"], "obj_id": o["id"], "dest": d, "true_place": o["at"],
             "kind": "given" if given else "ask", "policy": None,
             "dest_text": spoken[d], "true_text": spoken.get(o["at"], o["at"])}
        if given:
            t["prompt"] = f"Take the {o['label']} from {t['true_text']} to {spoken[d]}."
        else:
            t["policy"] = POLICIES[n_ask % 3]
            n_ask += 1
            t["prompt"] = f"Put the {o['label']} on {spoken[d]}."
            wrong = sorted(p["id"] for p in places if p["id"] not in (o["at"], d))
            w = rnd.choice(wrong)
            t["wrong_place"], t["wrong_text"] = w, spoken[w]
        tasks.append(t)
    return tasks
