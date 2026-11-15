# D4: the stay gate on d3dev and the design of the sealed measure on d4fresh (written and committed BEFORE the sealed run)

## 1. What the development measures on d3dev showed (150 tasks x EN/KO x real/ideal = 600 episodes per arm, seed 0, shared prompt cache)

Optimistic set (the D3 round and the layers were developed on it). The pairs share one prompt cache, so a discordant count is not two independent runs.

| Arm (on top of the 18 D3 layers) | Success /600 | False success | Won / lost vs D3 | p (McNemar, exact) |
|---|---|---|---|---|
| D3 | 451 | 35 | | |
| all 11 D4 layers | 456 | 32 | 9 / 4 | 0.27 |
| group A: plan_release, effect_check, repair_sync, close_opened | 454 | 34 | 7 / 4 | 0.55 |
| group B: goal_ledger, answer_align, question_cap, partial_end, else_ask | 453 | 33 | 2 / 0 | 0.50 |
| group C: safety_profile, fault_ladder | 451 | 35 | 0 / 0 | 1.0 |
| plan_release + effect_check + repair_sync | 457 | 34 | 9 / 3 | 0.15 |
| plan_release alone | 453 | 35 | 2 / 0 | 0.50 |
| effect_check alone | 451 | 35 | 0 / 0 | 1.0 |
| repair_sync alone | 455 | 34 | 7 / 3 | 0.34 |
| group A without close_opened (= the three above) | 457 | 34 | | |
| group A with close_opened | 454 | 34 | close_opened loses 3 (three `conjunction` tasks that close `drawer@main`: give up / budget) and wins none | |
| **candidate: plan_release, repair_sync, goal_ledger, answer_align** | **459** | **32** | **11 / 3** | **0.057** |

Stay gate (fail-loop section 3b): a layer stays in `all` only with a paired contribution above zero (not just not negative) and fired in at least 3 episodes, or a written safety reason. The candidate was chosen on these same 600 episodes, so its +8 is optimistic.
Kept: plan_release, repair_sync, goal_ledger, answer_align. Retired from `all` (code stays, default off, still selectable by name): effect_check, fault_ladder, safety_profile, partial_end, question_cap, else_ask (no outcome changed on d3dev) and close_opened (harmful on d3dev: -3, +0). The retire is not yet done in the code; see section 3.

## 2. Design of the sealed measure (once)

* Question: does the candidate arm beat the D3 arm on a set neither was developed on?
* Arms (names as `measure_d4.sh` resolves them; both on `hl-understand-p3-s700`, no fine-tuning): reference `base_d3` (`HOMELOOP_D1_LAYERS=d3`, the 18 D3 layers, hash f751d73417c6... checked by verify_arm.py) and `d3+L15,L17,L18,L19` (the 18 D3 layers + plan_release, repair_sync, goal_ledger, answer_align, in the build order of the layer list).
* Cells: EN and KO x real and ideal, 150 tasks each, seed 0, one run per arm and cell. 600 episodes per arm.
* Set: `d4fresh.jsonl`, 150 tasks, sha256 019651b6826704a0f34e38cf4d89f2cad57d1d104358521a18efb7525c71b4d3, world seeds 50006..59963 (generator `gen/d3.py`, gen-seed 2027), kept in /media/keti/workdir/data/homeloop_d4_fresh (directory mode 700, file 600). It has no identity or near-text overlap with train, dev, d3dev, d3fresh (audit_d4.py, 31 PASS, 0 FAIL). Nobody opens the set or its episode rows; only aggregates are printed.
* Code: an immutable snapshot of the three repos at the commit of this file (snapshot_run.sh make; refuses a dirty tree; modules verified to load from the snapshot); its manifest is kept next to the results.
* Prompt cache: a NEW, empty shared cache for the sealed set, lock mode (`--shared-cache --cache-lock`), `base_d3` runs first.
* Rules: one run per arm and cell; nothing is changed after the first episode; an aborted run restarts from the same episode file and the cause is reported; nothing is fixed from the sealed set; fresh_final_d4.log keeps one line per arm.
* Reported: success, false success, calls per task, paired McNemar per cell and in total (aggregates only), silent options, what is not known. The discordant counts are not two independent runs (shared cache).
* What would count as a result: the paired total on d4fresh. A gain below the noise is reported as "no measurable gain". No layer is kept or dropped from this measure.

## 3. After the measure
The retire of the seven layers is made in `d1_options.py` (a RETIRED set left out of `all`, still selectable by name), with the criterion in check.sh (iface: all = d3 + the kept D4 layers) corrected openly, with a comment and a backup. The d2 and d3 aliases keep their hashes.
