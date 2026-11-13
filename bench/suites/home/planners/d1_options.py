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
"""

from __future__ import annotations

import copy

# search legs, at most 6 places per search, no search second look (robot_agent: planner.search_legs / search_total / detector_miss_rate)
D1_SEARCH = {"search_legs": 1, "search_total": 6, "detector_miss_rate": 0}
# false-success class: the goal check believed one sighting that followed a miss (the camera sees what is not there). With robot_agent's
# option ``confirm_look`` (default off) a third look decides: believed only when the object is seen again (two sightings in a row).
D1_CONFIRM = {"confirm_look": "1"}
# the failure-class options of the 2026-11-13 round (all default off in robot_agent)
D1_CLASSES = {"search_per_object": "1", "place_find": "1", "reopen_on_miss": "1", "end_state": "1", "object_words": "1"}

# the pack data those options read. ASSUMED: the mock robot's own action names (find, open, close, dock), not tuned values.
D1_DATA = {"planner": {"action_roles": {"find": "Find"},
                       "recovery": {"reopen_on_miss": ["Close", "Open"]},
                       "end_state": {"places": ["dock"], "action": "Dock"}},
           "note": "assumed: D1 failure-class data (the find role, reopen_on_miss [Close, Open], end_state dock + Dock); the last two match "
                   "the mock robot's partial-open and docked() rules, read them as an ablation"}


def _merge(base: dict, add: dict) -> dict:
    out = dict(base or {})
    for k, v in add.items():
        out[k] = _merge(out.get(k) or {}, v) if isinstance(v, dict) else copy.deepcopy(v)
    return out


def d1_overlay(base: dict, translate_model: str) -> dict:
    """``base`` (the variant's overlay) with this reader as translator and the D1 data merged key by key."""
    out = _merge(base, {"planner": {**D1_DATA["planner"], "translate_model": translate_model}})
    return {**out, "assumed": True, "note": str(base.get("note", "")) + "; " + D1_DATA["note"]}
