"""The arms of the factory suites: run options of the planning engine, sent with each run (they override the server's environment)."""
from __future__ import annotations

_NEW_OFF = {"ask_source_room": 0, "ask_source_clarify": 0, "ask_source_near": 0}      # sent explicitly: a server may set them on in its environment (a domain's planner_env may)

ARMS = {  # run options sent with each run (they override the environment): the three engine options under test
    "A":  {"ask_source": 1, "ask_source_reask": 0, "search_route_weight": 0, **_NEW_OFF},
    "B":  {"ask_source": 1, "ask_source_reask": 0, "search_route_weight": 0.3, **_NEW_OFF},
    "C":  {"ask_source": 1, "ask_source_reask": 1, "search_route_weight": 0.3, **_NEW_OFF},
    "A2": {"ask_source": 1, "ask_source_reask": 0, "search_route_weight": 0, **_NEW_OFF},   # A/A repeat: same setting, measures noise
    # messy-person protocol (messy.md): D = C plus the two later options
    "D":  {"ask_source": 1, "ask_source_reask": 1, "search_route_weight": 0.3, "relook": 1, "confirm_look": 1, **_NEW_OFF},
    # messy-fix re-run (messy_fix.md): E = D plus the three new keys of ask_source (a room answer is used, an unusable
    # answer is asked about once, a nearly-named place is confirmed)
    "E":  {"ask_source": 1, "ask_source_reask": 1, "search_route_weight": 0.3, "relook": 1, "confirm_look": 1,
           "ask_source_room": 1, "ask_source_clarify": 1, "ask_source_near": 1},
}
