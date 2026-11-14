# D2 layers: root-cause fixes of the D1 planner, one failure class at a time

Each layer is one robot_agent option (default off), turned on for `sage_s8n_d1` / `sage_s8n_ft_d1` only through `bench/suites/home/planners/d1_options.py`.
The environment variable `HOMELOOP_D1_LAYERS` picks the layers: `all` (default), `none` (D1 exactly as in experiment D, the baseline arm) or a comma list
of option names. It is read when the module is imported; the layers on are in the run config (`loop_options`) and in the overlay note (`assumed: true`).
Pilot rounds and measured results are written here by the coordinator.

## L1 `precond_repair`: a plan with a missing step

- What: a plan that lacks a step its next skill needs (a hand-over with an empty hand, a Pick with a full hand, a skill away from its object) gets the
  Find / Pick, the put-down or the MoveTo before the gate sees it. The plan is replayed on the belief now; nothing is inserted when the need is already met.
- Why: the gate rejects such a plan (`gate_strict`) and the run gives up; this was the largest class of failures (29% in D).
- Data: the pack declares the needs, `planner.options.precond_repair.needs = {rules: {<Action>: {holding, hand_free, near}}, source}` and the roles
  `move`, `find`, `pick`, `put_down`. D1 declares them from the mock robot's own manifest (`skills[].pre`): Pick needs a free hand; Place, PutIn and
  Handover need a held object. `near` is supported but not declared for D1 (the gate's own `insert` operator already adds the MoveTo). Open / Close with a
  full hand are left to the gate's `hoist` operator (putting the object down early could end in a closed container). No data, no label, unknown skills,
  a role not declared: the plan is unchanged (fail open). No guess: two candidate objects, or no goal for the held one, insert nothing.
- Tests: `robot_agent/tests/test_option_precond_repair.py` (made-up skills Offer / Grab / Chirp: missing pick, free hand, approach, already true, unknown
  skill, ambiguity, empty and unlabelled data, default path unchanged; a loop-level run on and off) and `tests/home/bench/test_d1_classes.py` (the switch,
  `none` equals D's options and overlay).
- `gate_complete` (existing, default off, never tried): tried on and off in tests. On its own it did not rescue a plan with a missing step (the plan
  still failed), and with `precond_repair` on the outcome was the same on and off. It is not switched on for D1. A pilot measure on dev 700..849 is the
  coordinator's (no GPU here); this verdict is from synthetic plans only.
- Limits: the option inserts steps only for the declared needs; the Find / Pick of an object is placed before the approach to the person, and the gate's
  own operators place it at the right source. It does not repair a plan whose goals are wrong (L2..L4).
