# Layers bt_goal (policy A) and bt_goal_sage (policy B): goals run by declared trees with the engine's own recovery (selectable, not in `all`)

**What.** They turn on robot_agent's option `bt_goal` (robot_agent docs/bt_goal.md) with the trees `BT_ON`, `BT_OPEN`, `BT_CLOSE`, `BT_GO` and the
menu `BT_MENU` of `d1_options.py` (built from the mock robot's own skills, shapes assumed). A request whose goals are ALL of a kind with a tree runs
by the trees (each step with the engine's own ladder: retry, wait schedule, search legs, its help question; no plan call); any other goal: SAGE
plans the whole run. A tree with no way left: `bt_goal` asks once (menu) or stops; `bt_goal_sage` hands the remaining goals to SAGE once.
Turn on with `HOMELOOP_D1_LAYERS=<all list>,bt_goal` (or `,bt_goal_sage`). The hashes of all, d3, d2 are unchanged (test_bt_goal_layer.py).

**Measure 2026-11-17 (d5dev = dev set, optimistic; snapshot robot_agent 257c165, symbolic_robot e8b51fc, embodiplan 4bfa87a; a COPY of
shared_cache_D5, cache-only replay, misses live: 23 live calls).** Tasks: the 30 of 150 d5dev tasks whose gold goals are all on / open / go
(24 on, 5 go, 1 open), 4 cells. SAGE = the existing `DEV_all_<cell>` episodes (a replay of `all` at this snapshot gives the same 120 results).

| cell | success SAGE / A / B | false success | LLM calls mean SAGE / A | sim time s SAGE / A | questions SAGE / A |
|---|---|---|---|---|---|
| en_real | 19 / 19 / 19 | 1 / 1 / 1 | 5.27 / 2.90 | 185 / 195 | 47 / 49 |
| en_ideal | 28 / 28 / 28 | 0 / 0 / 0 | 5.13 / 2.43 | 156 / 165 | 25 / 26 |
| ko_real | 20 / 20 / 20 | 1 / 1 / 1 | 8.57 / 6.50 | 188 / 190 | 59 / 60 |
| ko_ideal | 27 / 27 / 27 | 1 / 1 / 1 | 7.63 / 5.00 | 165 / 165 | 27 / 27 |

Paired vs SAGE: 0 wins, 0 losses in every cell (exact McNemar p = 1; common random numbers: not independent runs). The trees claimed 118 of
120 episodes; 91 of 120 made the same robot calls as SAGE. B made the same runs as A: the policy's last step (stop / SAGE) was never reached
(29 trees went on from a place the person named to the engine's own where-question, 2 from the menu answer, 8 runs ended by the engine's own
ladder stop as with SAGE, 8 gave a correction back to the engine). Before the correction fix one pilot episode was lost (the tree finished the
old goal). A tree that fails with an object in a closed source container looks once before it opens (one extra Find; SAGE plans the Open first).
