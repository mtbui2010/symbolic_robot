"""A messy simulated person: answer scripts generated from a world's own names (docs/EXPERIMENT_MESSY.md). Domain-neutral and English only:
the only inputs are the place records a domain hands over, {place id: {"names": [name, alias...], "zone": "<room or zone name>"}}.
A script is the list of answers the person gives to the 1st, 2nd, ... where-question about the object (the last one repeats).
Each answer is {"text", "grounded"}; grounded says what the text names: "place" (a real place), "partial" (a place by a changed name), "room" (only a room
or zone), "none" (nothing). Wording and edits are written here for this repo; no rule, phrase list or probability of any benchmark is used."""
from __future__ import annotations

import random

from .tasks_gen import generate_tasks

NEW_POLICIES = ("room_only", "vague", "mind_change", "partial_name", "silent")
POLICIES = ("knows", "wrong") + NEW_POLICIES           # knows / wrong: the references (the old policies, answered by runner.answer_for as before)
VARIANTS = ("alias", "abbrev", "typo", "drop_word")    # partial_name edits, in rotation

ROOM_ONLY = ("It is somewhere in the {zone}.", "Somewhere in the {zone}, I think.", "It should be in the {zone}, I am not sure where exactly.", "Look in the {zone}.")
ROOM_AGAIN = ("As I said, somewhere in the {zone}.", "Still the {zone}, that is all I know.")
VAGUE = ("Over there.", "Hmm, around here somewhere.", "I do not remember, somewhere on the side.")
VAGUE_HEAD = ("I am not sure, maybe near the {heads}.", "Maybe by the {heads}, I cannot say.")
VAGUE_AGAIN = ("I told you, I am not sure.", "Sorry, I really do not remember.")
WRONG_FIRST = ("It is on {place}.", "I left it on {place}.")
CHANGE = ("No wait, it is on {place}.", "Oh no, I was wrong, it is on {place}.")
PARTIAL = ("It is on {name}", "Look by {name}", "Should be near {name}")      # the full stop is added after the name (an abbreviation brings its own)
SILENT = ("", "...")
SECOND = ("Sorry. It is on {place}.", "Let me think... it is on {place}.")


def plural(word: str) -> str:
    w = word.strip()
    if w.endswith("s"):
        return w
    return w + ("es" if w.endswith(("x", "ch", "sh")) else "s")


def head_word(name: str) -> str:
    """The last word of a name that is made of letters ('parts rack A' -> 'rack' is not guessed: the last letters-only word is used, 'bench 1' -> 'bench')."""
    ws = [w for w in name.split() if w.isalpha() and len(w) > 1]
    return ws[-1] if ws else name.split()[-1]


def _end(sentence: str) -> str:
    return sentence if sentence.endswith(".") else sentence + "."


def _matches(tokens: list, info: dict, skip: str) -> int:
    """How many other places have a name that contains all these words (how ambiguous a shortened name is)."""
    n = 0
    for pid, p in info.items():
        if pid != skip and any(set(tokens) <= set(nm.lower().split()) for nm in p["names"]):
            n += 1
    return n


def variant_of(pid: str, info: dict, rnd: random.Random, kind: str) -> tuple:
    """A changed name of place `pid`, made from its own names by one simple edit. -> (text, kind, n other places the new name could also mean).
    A kind that does not apply to this name (no alias, one-word name) falls to the next kind in VARIANTS order."""
    names = info[pid]["names"]
    base = names[0]
    words = base.split()
    for k in VARIANTS[VARIANTS.index(kind):] + VARIANTS[:VARIANTS.index(kind)]:
        if k == "alias" and len(names) > 1:
            return rnd.choice(names[1:]), "alias", 0
        if k == "abbrev" and len(words) > 1:
            i = max(range(len(words)), key=lambda j: len(words[j]))
            w = words[i]
            cut = max(3, round(len(w) * 0.6))
            if len(w) > cut + 1 and not any(ch.isdigit() for ch in w):
                return " ".join(words[:i] + [w[:cut] + "."] + words[i + 1:]), "abbrev", 0
        if k == "typo":
            i = max(range(len(words)), key=lambda j: len(words[j]))
            w = words[i]
            if len(w) >= 4 and not any(ch.isdigit() for ch in w):
                spots = [q for q in range(1, len(w) - 2) if w[q] != w[q + 1]]
                if spots:
                    q = rnd.choice(spots)
                    w2 = w[:q] + w[q + 1] + w[q] + w[q + 2:]           # swap two inner neighbouring letters
                    return " ".join(words[:i] + [w2] + words[i + 1:]), "typo", 0
        if k == "drop_word" and len(words) > 1:
            opts = [words[1:], words[:-1]]
            opts.sort(key=lambda t: _matches([x.lower() for x in t], info, pid))
            return " ".join(opts[0]), "drop_word", _matches([x.lower() for x in opts[0]], info, pid)
    return base, "plain", 0                                           # nothing to edit: the plain name (counted as a variant that did not apply)


def script_for(policy: str, t: dict, info: dict, rnd: random.Random, idx: int) -> tuple:
    """-> (script, extra task fields). t: a task with true_place, true_text, wrong_text; idx: the task's rank inside its policy."""
    p = info[t["true_place"]]
    place, zone = t["true_text"], p["zone"]
    heads = plural(head_word(p["names"][0]))
    extra: dict = {}
    if policy == "room_only":
        return [{"text": ROOM_ONLY[idx % len(ROOM_ONLY)].format(zone=zone), "grounded": "room"},
                {"text": ROOM_AGAIN[idx % len(ROOM_AGAIN)].format(zone=zone), "grounded": "room"}], {"zone_text": zone}
    if policy == "vague":
        first = VAGUE[idx % len(VAGUE)] if idx % 2 == 0 else VAGUE_HEAD[(idx // 2) % len(VAGUE_HEAD)].format(heads=heads)
        return [{"text": first, "grounded": "none"}, {"text": VAGUE_AGAIN[idx % len(VAGUE_AGAIN)], "grounded": "none"}], {}
    if policy == "mind_change":
        return [{"text": WRONG_FIRST[idx % 2].format(place=t["wrong_text"]), "grounded": "place"},
                {"text": CHANGE[idx % 2].format(place=place), "grounded": "place"}], {}
    if policy == "partial_name":
        text, kind, amb = variant_of(t["true_place"], info, rnd, VARIANTS[idx % len(VARIANTS)])
        extra = {"variant_text": text, "variant_kind": kind, "variant_ambiguous": amb}
        return [{"text": _end(PARTIAL[idx % len(PARTIAL)].format(name="the " + text)), "grounded": "partial"},
                {"text": f"It is on {place}.", "grounded": "place"}], extra
    if policy == "silent":
        return [{"text": SILENT[idx % 2], "grounded": "none"}, {"text": SECOND[idx % 2].format(place=place), "grounded": "place"}], {}
    raise ValueError(policy)


def messy_tasks(objects: list, places: list, info: dict, n_per_policy: int, seed: int, spoken_all: dict) -> list:
    """Tasks "Put the X on D." (no source), the answer policies in rotation, n_per_policy of each of POLICIES. Same pairing as tasks_gen.generate_tasks.
    objects whose true place has no name of its own in `info` are dropped by the caller."""
    n = n_per_policy * len(POLICIES)
    base = generate_tasks(objects, places, n, seed, given_every=10 ** 9, spoken_all=spoken_all)
    rnd = random.Random(seed * 7919 + 1)
    count = {p: 0 for p in POLICIES}
    out = []
    for i, t in enumerate(base):
        pol = POLICIES[i % len(POLICIES)]
        t["policy"] = pol
        if pol in NEW_POLICIES:
            t["script"], extra = script_for(pol, t, info, rnd, count[pol])
            t.update(extra)
        count[pol] += 1
        out.append(t)
    return out
