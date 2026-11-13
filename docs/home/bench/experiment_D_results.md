# Experiment D: results (one run, protocol `experiment_D.md`, sha256 in `experiment_D.sha256`)

Run once per cell, no change after the first episode, no episode redone. All four runs finished with `n_error` 0. Planner `robot_agent:sage_s8n_ft_d1`, one model `hl-understand-p3-s700`, tasks `hl-dev-000600..699`, seed 0. Raw files: `results/home_D/` (not committed: `results/` is ignored).

| cell | planner success | 95% CI | false success | oracle | naive |
|---|---|---|---|---|---|
| EN, profile real | 55 / 100 | 0.45 - 0.64 | 5 | 88 | 55 |
| KO, profile real | 48 / 100 | 0.38 - 0.58 | 8 | 88 | 55 |
| EN, profile ideal | 82 / 100 | 0.73 - 0.88 | 3 | 100 | 95 |
| KO, profile ideal | 75 / 100 | 0.66 - 0.82 | 7 | 100 | 95 |

`naive` is a privileged open-loop reference (it knows the true start state), not a fair baseline for a planner that reads language.

## What the numbers say
* The planner is clearly below the oracle in every cell and does **not** beat the naive reference: equal in EN real (18 wins, 18 losses on the same tasks), below it in KO real (18 wins, 25 losses) and in both ideal cells (5 wins, 18 losses; 3 wins, 23 losses).
* The pilot on dev 0..49 (34 to 38 of 50, oracle 40 of 50) was optimistic: those ids were used to tune. On fresh ids the gap to the oracle is larger.
* KO is lower than EN in all cells (48 vs 55 and 75 vs 82). The KO translator is the reader model, not the pack's 30B model; this may explain part of it. Not tested.
* False success is 3 to 8 per 100 (the pilot had 1 per 50).

## Where it fails (descriptive, nothing changed)
* Profile ideal has no injected fault, yet the planner fails 18 (EN) and 25 (KO) of 100 while the oracle fails none. In these failures no unrecovered failure code is recorded, and the runs are short (mean 8.2 calls in EN against 21.6 for the successes): the planner gives up early (14 of 18 in EN, 17 of 25 in KO end in `give_up`). The failures sit in understanding, asking and plan checking, not in the world.
* Profile real: the oracle also fails 8 (EN) and 9 (KO), injected faults it cannot recover. The planner fails 37 and 43 more. 57 of the 100 EN tasks have a corrupted heard instruction (ASR noise) and 28 of the 45 failures are among them.
* Several of the known weaknesses listed in the protocol appear (a person who answers wrongly or stays silent, hardware faults, a silent drop followed by a phantom detection). The share of each class on this slice has not been counted.

## Limits of this report
* One seed, one planner, 100 tasks per cell; intervals are wide (about 10 points).
* No ablation of the options was run, so what each option contributes is unknown.
* The failures were not traced task by task; the breakdown above uses the recorded status, failure codes and call counts only.
