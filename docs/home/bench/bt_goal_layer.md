# Layers bt_goal (policy A) and bt_goal_sage (policy B): goals run by declared trees with the engine's own recovery (selectable, not in `all`)

**What.** They turn on robot_agent's option `bt_goal` (robot_agent docs/bt_goal.md) with the trees `BT_ON`, `BT_IN`, `BT_OPEN`, `BT_CLOSE`, `BT_GO`,
`BT_SAY_AT` / `BT_SAY_HERE` and the menu `BT_MENU` of `d1_options.py` (built from the mock robot's own skills, shapes assumed; every MoveTo only when
the robot is not there; no deliver tree: WaitForUnload is only a handover alias here; no give tree: understand_give_kind is off in D1). A request whose goals are ALL of a kind with a tree runs
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

**Measure 3, 2026-11-17 (in + say trees; snapshot robot_agent 95b240b, symbolic_robot b5f9d10, embodiplan 4bfa87a; a COPY of shared_cache_D5,
misses live: 42 calls).** Tasks: the 61 of 150 d5dev tasks whose gold atoms are all on / in / open / closed / robot_at / said_to (the old 30 +
31 new: 26 with `in`, 6 with `said_to`, 3 more `open`, 1 `closed`), 4 cells; pilot P5 + P10 pre-registered, two class fixes before this run.

| cell | success SAGE / A / B | false success | LLM calls mean SAGE / A / B | sim time s SAGE / A | questions SAGE / A |
|---|---|---|---|---|---|
| en_real | 37 / 37 / 37 | 1 / 1 / 1 | 6.18 / 3.16 / 3.25 | 194 / 200 | 109 / 114 |
| en_ideal | 57 / 57 / 57 | 0 / 0 / 0 | 6.16 / 2.70 / 2.70 | 172 / 177 | 61 / 62 |
| ko_real | 37 / 37 / 37 | 2 / 2 / 2 | 9.56 / 6.74 / 7.08 | 182 / 192 | 127 / 134 |
| ko_ideal | 54 / 56 / 56 | 1 / 1 / 1 | 8.34 / 5.10 / 5.10 | 162 / 169 | 57 / 58 |

Paired vs SAGE: 2 wins (000111, 000141 ko_ideal: SAGE used up its replans / its LLM budget on the search, the trees ran the same engine search
with no planner call), 0 losses (exact McNemar p = 0.5). The old 30 keep their success and false success exactly. Trees claimed 239 of 244;
195 of 244 made the same robot calls as SAGE. B differs from A in 3 episodes (the SAGE-once step reached), no outcome changed.
