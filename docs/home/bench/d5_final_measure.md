# D5 final measure on d5fresh: design, committed before the run

Written 2026-11-18, before any d5fresh episode was run. d5fresh (300 tasks, sealed, see d5_sets.md) is measured ONCE for the two arms below. Nobody opens a task or a failure of it; only aggregate counts are printed. No fix, no layer change and no second look follow from it.

## Code (frozen for this measure)
- robot_agent: `live/no-ros` HEAD 181f353 (nothing pushed).
- symbolic_robot: `main` HEAD cc5ac29 (this document is the only later commit; docs/home/bench/lora.md is not part of it).
- embodiplan 4bfa87a. Model hl-understand-p3-s700 (not fine-tuned for this round), planner robot_agent:sage_s8n_ft_d1, seeds 1, cells EN/KO x real/ideal (1200 episodes per arm).
- The runs use an immutable snapshot of these commits (snapshot_run.sh) and one shared prompt cache with a lock for both arms (common random numbers: the discordant counts of the pair are not two independent runs).

## Arms
- **A (previous best):** `HOMELOOP_D1_LAYERS=all` (the 22 layers of D2 + D3 + D4).
- **B (final design):** `HOMELOOP_D1_LAYERS=precond_repair,gate_prune,dedupe_keep_end,goal_words,ask_focus,entity_cover,hazard,hw_wait,search_budget,lang_words,cond_extract,recipient_keep,plan_complete,ask_agree,name_recover,replan_block,release_near,hw_tries,plan_release,repair_sync,goal_ledger,answer_align,bt_goal,metal_microwave_ask,heard_check,shared_instances,bt_open_source,closed_can_ask`
  = the 22 layers of `all`, plus bt_goal, metal_microwave_ask (it brings the metal word rule), heard_check, shared_instances, bt_open_source, closed_can_ask (it contains the closed-can refusal).
- **Not in B (tried, kept as selectable layers, default off):** heat_safety (blind test failed), cond_answer and cond_schema (three rounds; a blind look gave a flat success count and 43 -> 38 false successes on 320 episodes, 13 wins and 13 losses; a first design was worse on another blind set), closed_can_microwave alone (contained in closed_can_ask), bt_goal_sage (not significant), single / drop_search (retired or not merged).

## Dev evidence for B (d5dev, 600 episodes; tuned on, so optimistic)
- all: 423 successes, 38 false successes. B: 450 successes, 17 false successes (live run). Five layers without bt_open_source / closed_can_ask: 445 / 18.
- closed_can_ask was measured only by replay and one live dev run (the one bare-can task); its Korean refusal sentence was not tested before that run.

## What counts as a result (set before the run)
- Primary: B against A, success per task x cell (1200 pairs), paired exact McNemar, alpha 0.05, two-sided; report n, successes of each arm, wins b, losses c, p.
- Secondary: false successes per arm (the benchmark's own false_success field); per cell and per language counts; counts by gold kind (feasible / clarify); status counts (give_up, budget, refuse).
- B is called better only if success is higher and the false successes are not higher. A negative or flat result is reported as measured, and is not a reason to change the arms.
- Known limits: one seed; the pairs share a cache; the sealed set was generated with the same generator family as d5dev; the arms were tuned on d5dev.
