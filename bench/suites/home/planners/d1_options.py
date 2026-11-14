"""What the D1 planners (``sage_s8n_d1``, ``sage_s8n_ft_d1``) turn on in robot_agent, and the pack data those options read.

Kept apart from ``robot_agent_adapter.py`` (at its size limit). Every option here is OFF by default in robot_agent (a registered option,
``python -m robot_agent.core.options list``) and is switched on only for D1 through ``loop_options``; the data an option needs is declared as a
manifest overlay (the frozen mock-robot pack declares none), recorded in the run config as ``manifest_overlay`` with ``assumed: true``.

Failure classes (found on the D1 dev pilot, fixed as classes, never as tasks):

* ``search_per_object``: the search budget (``search_total``) was one count for the whole run, so the places a first object used up were
  charged to the second one.
* ``place_find``: a Find of a place the robot moves to (``MoveTo m, Find m, Open m``) is always absent and counted as a miss.
* ``reopen_on_miss``: a Find that misses right after an Open (a door opened only part way) closes and opens the container once, then looks
  again. The remedy ``[Close, Open]`` OVERLAPS the simulator (its partial-open state is cleared by a Close): read it as an ablation.
* ``end_state``: a ``go`` goal for the dock is made true (go there, Dock) before done, wherever the reader put it in the goal list. Like the
  remedy above it matches the simulator's ``docked()`` condition: read it as an ablation.
* ``object_words``: the goal's 'phone' and the plan's 'Pick cell phone' are one object for the goal checks.

Round D2 (one layer per failure class, each a robot_agent option, default off): ``LAYERS`` below. The environment variable ``HOMELOOP_D1_LAYERS`` picks
which layers D1 turns on: ``all`` (default; D2 layers + the D3 layers), ``d2`` (the ten D2 layers only), ``none`` (D1 exactly as in experiment D: the baseline arm) or a comma list of layer names. It is read when
this module is imported (the planner classes are built then); the layers on are recorded in the run config (``loop_options``) and in the overlay note.
"""

from __future__ import annotations

import copy
import os

# search legs, at most 6 places per search, no search second look (robot_agent: planner.search_legs / search_total / detector_miss_rate)
D1_SEARCH = {"search_legs": 1, "search_total": 6, "detector_miss_rate": 0}
# false-success class: the goal check believed one sighting that followed a miss (the camera sees what is not there). With robot_agent's
# option ``confirm_look`` (default off) a third look decides: believed only when the object is seen again (two sightings in a row).
D1_CONFIRM = {"confirm_look": "1"}
# the failure-class options of the 2026-11-13 round (all default off in robot_agent)
D1_CLASSES_D = {"search_per_object": "1", "place_find": "1", "reopen_on_miss": "1", "end_state": "1", "object_words": "1"}

LAYERS_ENV = "HOMELOOP_D1_LAYERS"
# D2 layers: name -> (loop options, pack data), in the order they were added. The data is the mock robot pack's own, with its source.
# Korean clause words, ASSUMED (general grammar, not measured). A condition is a predicate (stem: be / not be / do / become / open or closed / on or off)
# ending in a conditional (-(eu)myeon, -damyeon), up to three words of its own clause before it (none that ends a clause with a comma: the words before
# a comma are the previous clause's request), not followed by a request form ("... myeon dwae /
# johgesseo": that is the request, not a condition). A noun that only ends in "myeon" is no ending (stems are listed; bare "-ramyeon" is not).
# A negation is "-ji ma / -ji mal-go / -ji anh-" ("do not ...") or "malgo / ppaego / jeoehago" ("not that, except"); "ji mal-" is read only before
# go / a / ra, so a noun ending in "ji" before a word that starts with "mal" (a verb "to dry") stays.
KO_CONDITION = (r"(?:(?:만약|혹시)\s+)?(?:[^\s,;.!?]+\s+){0,3}\S*(?:(?:있|없|하|되|열려|닫혀|켜져|꺼져)(?:으)?면|[가-힣]다면)"
                r"(?![가-힣])(?!\s*(?:돼|되|좋겠|괜찮|충분))(?=\s|[,;.!?]|$)")
KO_NEGATION = (r"(?:[^\s,;.!?]+\s+)?\S*(?:지\s*(?:마(?:세요|시오|라|요)?|말(?:고|아\S*|라)|않\S*)|말고|빼고|제외하고)(?=\s|[,;.!?]|$)")
# Korean condition words the D2 clause above does not read (a sighting or a negation as the condition: "...-boi-myeon", "...-ani-myeon / -ani-ramyeon"), ASSUMED, read only by the
# D3 layer cond_extract (its own declared clauses, never the lang_words ones: the D2 data is unchanged).
KO_COND_MORE = r"(?:(?:만약|혹시)\s+)?(?:[^\s,;.!?]+\s+){0,3}\S*(?:보이|아니|아니라)면(?![가-힣])(?=\s|[,;.!?]|$)"
# the extraction call of cond_extract (prompt language, ASSUMED text): the request, the reader's numbered goals, one JSON of the option's fixed schema
COND_PROMPT = ("A household robot request may hold a condition: something is to be done only if an object is (or is not) at a place, and perhaps something else otherwise.\n"
               "Request: {request}\nThe goals already read from it, numbered:\n{goals}\n"
               "Answer in JSON. conditional: true only when the request really makes a goal depend on whether an object is at a place, else false with empty lists. "
               "object and at: the object and the place the condition looks at, in the words of the request. present: true when the condition holds if the object IS at that "
               "place, false when it holds if the object is NOT there. if_goals: the numbers of the goals to do when the condition holds. else_goals: the numbers of the goals to "
               "do when it does not hold (the 'otherwise' part). drop: the numbers of goals that only restate the condition and are no request. A number is in at most one list; "
               "leave a goal out of all lists when it is to be done in every case. unsure: true when you cannot tell.")


LAYERS = {
    "precond_repair": ({"precond_repair": "1"},
                       {"planner": {"action_roles": {"pick": "Pick"},
                                    "options": {"precond_repair": {"needs": {
                                        "rules": {"Pick": {"hand_free": True}, "Place": {"holding": True, "achieves": "on"},
                                                  "PutIn": {"holding": True}, "Handover": {"holding": True, "achieves": "hand"}},
                                        "source": "mock robot manifest, skills[].pre (hand_empty(), not hand_empty()); achieves: assumed (the manifest "
                                                  "effects name no goal; a put-down ends an on goal, a hand-over a hand goal)"}}}}}),
    # gate_prune: an Open / Close of a place the ENV declares not openable (explicit openable false) is dropped. Data: the roles of the mock robot's own
    # open / close actions, ASSUMED (names of its skills); without them the option does nothing.
    "gate_prune": ({"gate_prune": "1"}, {"planner": {"action_roles": {"open": "Open", "close": "Close"}}}),
    # dedupe_keep_end: the gate's removal of a repeated fetch keeps the way home after it. No pack data.
    "dedupe_keep_end": ({"dedupe_keep_end": "1"}, {}),
    # no pack data: it reads the robot's own object memory and limits (whole words, catalogue first)
    "goal_words": ({"goal_words": "1"}, {}),
    # no pack data: the world is the robot's object memory and limits; the phrases of "I don't know" are the language packs' own
    "ask_focus": ({"ask_focus": "1"}, {}),
    # no pack data: the names are the robot's object catalogue (object memory, limits.objects), read against the request's words
    "entity_cover": ({"entity_cover": "1"}, {}),
    # the receiver rules (hazard.receivers) are the mock robot's own safety profile (manifest safety.profile, household.yaml): no overlay data
    "hazard": ({"hazard_receiver": "1"}, {}),
    # hw_wait: the wait schedule and tries per failure kind. ASSUMED numbers (the mock robot's spec sheet declares none): a camera that is down and a
    # device fault get the same doubling backoff as the base wait, with tries; a kind not named here keeps the policy table. Not a simulator rule.
    "hw_wait": ({"hw_wait": "1"},
                {"planner": {"options": {"hw_wait": {"kinds": {
                    "perception_unavailable": {"schedule_s": [2, 4, 8], "tries": 3, "action": "wait_health"},
                    "hw_fault": {"schedule_s": [2, 4, 8], "tries": 2, "action": "wait_health"},
                    "assumed": True}}}}}),
    # search_budget: looks per object and the stop probability, ASSUMED numbers (about 8 looks, stop under about 10%; the brief's, not tuned), ask once. The
    # layer also turns reopen_on_miss OFF: its remedy [Close, Open] mirrors the simulator's partial-open state and cost 56-74 commands with no gain on the
    # ideal profile; the option is already once per container and pack-declared, so there is nothing left to narrow. (Not a simulator rule.)
    "search_budget": ({"search_budget": "1", "reopen_on_miss": "0"},
                      {"planner": {"options": {"search_budget": {"budget": {
                          "looks_per_object": 8, "stop_probability": 0.1, "ask": "once", "assumed": True}}}}}),
    # lang_words: condition and negation words per language. English is the pack's own (robot_agent lang/en.json); Korean has no clause data in the pack, so
    # the layer declares it here, ASSUMED (general grammar: a conditional ending on the last words of a clause, a "not / except" ending), not measured.
    "lang_words": ({"lang_words": "1"},
                   {"planner": {"options": {"lang_words": {"clauses": {"ko": {
                       "condition": KO_CONDITION,
                       "negation": KO_NEGATION,
                       "assumed": True}}}}}}),
    # --- D3 layers (on top of the ten D2 layers above, in the order cond_extract, recipient_keep, name_recover, replan_block; the ones that exist) ---
    # cond_extract (L9): a request with a condition word gets ONE extra model call that splits it into condition / goals-if / goals-else; cond_goal (without its
    # ``prompt`` key: the reader's schema and prompt stay) goes to the place, looks and keeps the branch that matches. ASSUMED data: the extraction prompt, the Korean words
    # above (the English ones are the language pack's), the two questions (where to look, is it there), the move role of the mock robot's own skill. No sentence is said.
    "cond_extract": ({"cond_extract": "1", "cond_goal": "1"},
                     {"planner": {"action_roles": {"move": "MoveTo"},
                                  "options": {"cond_extract": {"prompt": COND_PROMPT, "q_unclear": "Where should I look for the {object}?",
                                                               "clauses": {"ko": {"condition": [KO_CONDITION, KO_COND_MORE], "assumed": True}}},
                                              "cond_goal": {"q_where": "Where should I look for the {object}?", "q_unsure": "Is the {object} at the {place}?"}}}}),
    # recipient_keep: a delivery's recipient moves to the speaker only on first-person evidence of the language packs. No pack data of its own.
    "recipient_keep": ({"recipient_keep": "1"}, {}),
    # plan_complete: a plan that stops short of the step its goal needs. ASSUMED data (names of the mock robot's own skills and what they end / need, not
    # simulator rules): a put-in ends an ``in`` goal, a hand-over ends a hand goal and needs the person near, a speech needs its listener near; the roles of
    # its open / close / speech / pick actions. The way home is the ``end_state`` data above.
    "plan_complete": ({"plan_complete": "1"},
                      {"planner": {"action_roles": {"open": "Open", "close": "Close", "say": "Say", "pick": "Pick"},
                                   "options": {"plan_complete": {"needs": {
                                       "rules": {"PutIn": {"achieves": "in"}, "Handover": {"achieves": "hand", "near": True}, "Say": {"near": True}},
                                       "assumed": True}}}}}),
    # ask_agree: the read-back dialogue (one more yes / no after a bare no and the same request; an "I don't know" keeps only a clean reading; an either-or when a
    # value changed). No pack data of its own: the words are the language packs' (fillers, first-person words, unsure phrases and their declared endings).
    "ask_agree": ({"ask_agree": "1"}, {}),
    # name_recover (L11): an object name the speech recogniser garbled takes the one near name of the object catalogue (two near names: asked), and asr_guard asks to repeat
    # an empty request or one with a hole (an article directly followed by a function word) without calling the reader. No pack data here: the limits are option keys with
    # their assumed defaults, the hole and distance-unit data are in the language packs (robot_agent lang/*.json, key ``asr``, labelled assumed).
    "name_recover": ({"name_recover": "1", "asr_guard": "1"}, {}),
    # replan_block: a replan repairs the right block (embodiplan SAGE key replan_block_fix, passed through the option), a goal change replans for sub-goals rebuilt
    # from the new goals, a replan suffix with a critical rule finding goes through the one refine. ASSUMED data: the action-model codes counted critical in a
    # suffix (a release with an empty hand, a release away from its place); not a simulator rule.
    "replan_block": ({"replan_guard": "1"},
                     {"planner": {"options": {"replan_guard": {"critical": {
                         "codes": ["place_without_holding", "place_wrong_location"], "assumed": True}}}}}),
}
D2_LAYERS = ("precond_repair", "gate_prune", "dedupe_keep_end", "goal_words", "ask_focus", "entity_cover", "hazard", "hw_wait", "search_budget", "lang_words")


def selected_layers(environ=None) -> tuple:
    """The layers that are on: ``all`` (unset too: the D2 layers, then the D3 layers that exist), ``d2`` (exactly the ten D2 layers), ``none``, or a
    comma list of names of ``LAYERS``; an unknown name is an error."""
    raw = ((environ if environ is not None else os.environ).get(LAYERS_ENV) or "all").strip().lower()
    if raw == "all":
        return tuple(LAYERS)
    if raw == "d2":
        return D2_LAYERS
    names = [n.strip() for n in raw.split(",") if n.strip()] if raw != "none" else []
    bad = [n for n in names if n not in LAYERS]
    if bad:
        raise ValueError(f"{LAYERS_ENV}: unknown layer {bad} (known: {sorted(LAYERS)}, all, d2, none)")
    return tuple(n for n in LAYERS if n in names)


def layer_options(environ=None) -> dict:
    """The loop options of the layers that are on."""
    return {k: v for n in selected_layers(environ) for k, v in LAYERS[n][0].items()}


# the pack data those options read. ASSUMED: the mock robot's own action names (find, open, close, dock), not tuned values.
D1_DATA = {"planner": {"action_roles": {"find": "Find"},
                       "recovery": {"reopen_on_miss": ["Close", "Open"]},
                       "end_state": {"places": ["dock"], "action": "Dock"}},
           "note": "assumed: D1 failure-class data (the find role, reopen_on_miss [Close, Open], end_state dock + Dock); the last two match "
                   "the mock robot's partial-open and docked() rules, read them as an ablation"}


D1_CLASSES = {**D1_CLASSES_D, **layer_options()}          # D's options + the layers that are on (HOMELOOP_D1_LAYERS)


def _merge(base: dict, add: dict) -> dict:
    out = dict(base or {})
    for k, v in add.items():
        out[k] = _merge(out.get(k) or {}, v) if isinstance(v, dict) else copy.deepcopy(v)
    return out


def d1_overlay(base: dict, translate_model: str, environ=None) -> dict:
    """``base`` (the variant's overlay) with this reader as translator, the D1 data and the data of the layers that are on, merged key by key."""
    on = selected_layers(environ)
    out = _merge(base, {"planner": {**D1_DATA["planner"], "translate_model": translate_model}})
    for n in on:
        out = _merge(out, LAYERS[n][1])
    note = str(base.get("note", "")) + "; " + D1_DATA["note"]
    if on:
        note += "; assumed: D2 layers on (" + LAYERS_ENV + "): " + ", ".join(on) + ", data from the mock robot manifest"
    return {**out, "assumed": True, "note": note}
