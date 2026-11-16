# Layer bt_goal (selectable, not in `all`; prototype): an `on` goal run by a declared behaviour tree, not a SAGE plan

**What.** It turns on robot_agent's option `bt_goal` (robot_agent docs/bt_goal.md) with the overlay tree `BT_ON` of `d1_options.py`: placed already?
else (holding it? else hand free, MoveTo its place, Find, Pick twice, then the ask_next menu once and Find + Pick), MoveTo the destination, Place,
placed?, a reply. Built from the mock robot's own manifest skills (move / find / pick / place / ask); the shape is assumed. Any goal in the request
that is not an `on` goal with a known source place: SAGE plans the whole run. Turn it on with `HOMELOOP_D1_LAYERS=<all list>,bt_goal`; the hashes of
all, d3 and d2 are unchanged (tests/home/bench/test_bt_goal_layer.py).

**Behaviour test (pre-registered 2026-11-17, 5 d5dev episodes, `all` vs `all + bt_goal`, one snapshot: robot_agent 0a8a7e8, symbolic_robot a77b739,
embodiplan 4bfa87a; cache-only replay of a copy of shared_cache_D5, then the 3 episodes with misses live on the local reader, 22 new calls).**

| episode | success A / B | LLM calls A / B | robot calls A / B | what the tree did |
|---|---|---|---|---|
| 000114 en_ideal, 1 goal | yes / yes | 2 / 1 | 11 / 11 | ran the goal; same skill calls |
| 000119 en_real, 2 goals | yes / yes | 6 / 4 | 24 / 24 | ran both goals in order; same skill calls |
| 000002 ko_real, blocked move | yes / yes | 10 / 16 | 14 / 14 | first MoveTo blocked, the tree has no move retry: failed, SAGE replanned from scratch |
| 000143 ko_real, 2 goals, hw_fault | yes / yes | 7 / 14 | 30 / 30 | Place hw_fault, no wait in the tree: failed, SAGE replanned |
| 000095 ko_ideal, search | yes / yes | 8 / 10 | 25 / 28 | object not at the remembered place: failed, two extra looks, SAGE searched |

Five episodes show behaviour, not rates. The ask menu was never reached (no pick failed). The reply is an event `say`, not a robot Say skill, so the
simulated person never hears it. Reading: the tree saves the plan calls only when nothing fails; a failed tree costs MORE calls than the plan it
replaced (the replan decomposes from scratch). Not in `all`; a larger measure would need trees with move / hardware retries and a search leaf first.
