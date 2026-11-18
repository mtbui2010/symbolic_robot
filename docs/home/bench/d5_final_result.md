# D5 final measure on d5fresh: result (one look, aggregates only)

Measured 2026-11-18 (11:30 to about 14:50 KST) with the design and criteria of [d5_final_measure.md](d5_final_measure.md) (committed 3f40ed4, before any episode ran). Code: robot_agent 181f353, symbolic_robot cc5ac29, embodiplan 4bfa87a; model hl-understand-p3-s700; seeds 1; cells EN/KO x real/ideal; 300 tasks x 4 cells = 1200 episodes per arm; one shared prompt cache with a lock for both arms. d5fresh (sha256 6e13fcfc...) was not opened at task level: only the counts below were printed. No fix or layer change followed from it.

| | A: HOMELOOP_D1_LAYERS=all | B: final layer list |
|---|---|---|
| success | 887 / 1200 | 897 / 1200 |
| false success | 54 | 39 |
| status done / give_up / budget | 941 / 218 / 41 | 936 / 223 / 41 |
| success per cell (en_real, en_ideal, ko_real, ko_ideal) | 175, 277, 162, 273 | 170, 282, 164, 281 |
| false success per cell | 14, 5, 30, 5 | 11, 3, 23, 2 |
| gold feasible (1028 episodes): success / false success | 767 / 38 | 769 / 30 |
| gold clarify (172 episodes): success / false success | 120 / 16 | 128 / 9 |

Paired, per task x cell: B wins 36, loses 26; exact two-sided McNemar p = 0.253. Wins / losses by cell: en_real 7 / 12, en_ideal 9 / 4, ko_real 8 / 6, ko_ideal 12 / 4.

## Reading
- By the rule written before the run (B is better only if success is higher and false successes are not higher) B qualifies. The primary test (alpha 0.05) is NOT significant: the direction is right, an increase of success is not proven.
- The false successes fell from 54 to 39 (28 %) in every cell. This was not tested separately; the pairs share a cache, so a p value would be a rough estimate.
- The d5dev gain (423 -> 450 successes, p < 0.0001) did not repeat at that size: d5dev was tuned on, so it was optimistic.
- en_real went down (175 -> 170). The cause is unknown and was not looked at (no task-level reading of d5fresh).
- Limits: one seed; arms tuned on d5dev; the sealed set is from the same generator family as d5dev; false success here is the benchmark's own field.

## Not in B (tried, kept as selectable layers, default off)
heat_safety, cond_answer, cond_schema (blind sets: first design worse; third design flat success, false successes 43 -> 38, 13 wins and 13 losses), bt_goal_sage, closed_can_microwave alone.
