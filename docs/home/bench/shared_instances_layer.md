# Layer shared_instances (selectable, not in `all`): an exact name two remembered objects share is asked about

**What.** It turns on robot_agent's option `shared_instances` (robot_agent docs/options.md). No overlay data: it reads the robot's own object memory.
Turn it on with `HOMELOOP_D1_LAYERS=<all list>,shared_instances`. The hashes of all, d3 and d2 are unchanged (tests/home/bench/test_shared_instances_layer.py).

**Why (class C1 of the d5dev clarify analysis).** `seed_memory` (planners/robot_agent_adapter.py) writes a record with an `instance` id only when a name
means one object; a name shared by two objects with the same usual place stays as a BARE record ("keys" for the gray and the yellow keys). robot_agent's
`inventory_ask` and `ask_focus` took an object named exactly like a record as resolved, so the robot never asked which one: d5dev 000 and 024 (keys)
and 003 (medicine bottle: the wrong bottle handed over in all 4 cells, a false success). Pairs at different usual places lose the bare name, and there
the checks already ask.

**Trigger analysis (2026-11-17, no model call; the reader's first reply per episode, the rebuilt seed memories, robot_agent par/c1 7760043).**
Flagged: 12 of 12 C1 episodes (000, 003, 024 x 4 cells; all "asks": no request names the colour), 1 of 480 feasible episodes (ko_real 133: the
recogniser garbled "glasses" and the reader wrote "book"; the off run is a false success). 0 feasible successes flagged.

**Cache-only replay (2026-11-17, CPU, a copy of shared_cache_D5 plus each cell's own llm_cache; robot_agent 37c3446, symbolic_robot 788db6d).**
Arm `all` replayed: 600 of 600 episodes identical to the recorded `DEV_all_<cell>` (sim time included). Arm `all,shared_instances`: 586 of 600
identical to `all`; 14 changed, each first diverging at the option's own lab event, then stopped at a cache miss (status `replay_miss`; no outcome
is claimed for them): the 12 C1 episodes (the which-question was put: `asked` 1, at grounding, `at: canon`), ko_real 133 (canon and read-back fired;
the miss is the read-back's re-sample, before a question) and ko_real 094 (a re-sampled reading named "book" in a run that ended give_up; read-back,
`at: issues`; the first-reply analysis cannot see it). Of the 14, 6 were successes in `all` (000 x 4, 024 en_ideal / ko_ideal: right by luck,
1 of 2 keys), 4 false successes (003 x 4) and 1 more (133), 3 failures (024 en_real budget, 024 ko_real give_up, 094 give_up).

**Not measured yet (needs the reader live, GPU).** The answers to the new question and the outcomes of the 14 changed episodes (000, 003, 024 in the
four cells, 094 and 133 in ko_real): about 100 live calls (the `all` runs made 100 model calls in these 14 episodes). d5dev was used for development.
