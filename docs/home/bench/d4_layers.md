# D4 layers (robot_agent options for the D1 planner, second round)

Round D4 adds layers on top of the 18 D3 layers (`HOMELOOP_D1_LAYERS`, `bench/suites/home/planners/d1_options.py`). Every layer is a robot_agent
option, default off, with its data declared in the D1 overlay (labelled `source` or `assumed: true`). Development set: d3dev (optimistic: D3 was
tuned on it). This file holds one section per layer (`## Lk ...`) and the complexity budget of the round.

## S0 simplification (before the first D4 layer; no new layer, no new option)

Status: PARTIAL. Done: (1) lab events for the layers that left none, (2) a test file for `asr_guard`. Not done, with the reason: (3) the shared Korean
condition data, (4) the merge of the two `unrefused` providers. Behaviour of every existing arm: unchanged (cache-only replay below).
Overlaps: none added. The step only names what already acts; `plan_complete` into `precond_repair` is a merge candidate left for later (it changes behaviour).

What and why (from the D3 layer audit: four D3-arm layers could not be told active or inert from their lab events):

* `hazard` records `{rules, refused, goals}` when its gate refuses or drops goals (flag `hazard`; the D1 layer is `hazard`, loop key
  `hazard_receiver`). The gate also runs with the receivers key off (it is always on), so the flag counts every safety refusal, not only the
  receiver rules; the rule ids in the event tell them apart.
* `dedupe_keep_end` records `{object, kept}` where its shorter cut differs from the old one (flag `dedupe_keep_end`). Its service now returns the
  function the gate's repair asks at that cut (`plan_repair._cut_end`); the gate keeps the edit only when it lowers the findings, so the event
  is "proposed", one per call.
* `lang_words` records `{lang, condition, negation}` when it gives the run clause words (flag `lang_words`). The loop cleared its lab log AFTER
  `on_start`, which dropped any event of run set-up; it is now cleared before (no option logged there before, so no other log changes).
* D1 layer `release_near` (data only, the `near` need of `precond_repair`) logs under `precond_repair.near`; D1 layer `hw_tries` (the key
  `more_tries` of `hw_wait`) logs under `hw_wait.more_tries`. Before, both were inside their option's flag. The names are `<option>.<key>`, the
  engine knows no bench layer name. For `silent_options.py` pass `--aliases hw_more_tries=hw_wait.more_tries,hazard_receiver=hazard`
  (`release_near` has no loop key; read its count from `layer_report.py`).
* `asr_guard` has its own test file (`tests/test_option_asr_guard.py`: off, empty, a made-up language, two loop tests of the final state);
  the hook-level cases of the shipped English pack stay in `test_option_name_recover.py`.

Not done:

* (3) `KO_CONDITION` sits once in the source of `d1_options.py` but twice in the overlay (`lang_words.clauses.ko.condition` and
  `cond_extract.clauses.ko.condition`). Both readers already share the code (`robot_agent/core/planning/clauses.build`). Removing one copy from the
  overlay changes the `d3` alias hash (`d3_layers_snapshot.json` hashes the overlay), which this step must keep, and making `cond_extract` read
  `lang_words`'s section would make one option read another option's data and change the arm where only one of them is on. Left as is; a
  candidate for the round that may change the hash.
* (4) `ask_agree.unrefused` and `ask_focus.unrefused` are not the same function: `ask_agree` returns False on the robot's own doubt and on a
  reading changed since the first read-back, asks the either-or, keeps per-run state and accepts declared word endings; `ask_focus` returns True
  for any clean "I don't know" by its own word sets. With both on, `ask_agree` (order 78) answers every "I don't know" first, so `ask_focus`'s
  answer is used only in arms without `ask_agree` (the `d2` arm). One provider for both would have to know which option is on (an option may not
  read another's state) or change the `d2` arm's answers. Left as two providers; retire `ask_focus.unrefused` only when no arm needs it.

Check that nothing else changed: cache-only replay (`--llm cache-only`, the D3 development caches, no model) of all 150 d3dev tasks of the four
cells with `HOMELOOP_D1_LAYERS=all` (today the 18 D3 layers), robot_agent at the base commit and after S0, in a scratch directory. Every
episode record is byte-identical apart from `lab_events`, and `lab_events` are identical once the two renamed flags are mapped back and the
three new flags are left out (one episode per ideal cell reaches the 50-entry cap; compared on the common prefix):

| cell | episodes | field diffs | lab diffs | new events (lang_words / hazard / dedupe_keep_end / precond_repair.near / hw_wait.more_tries) |
|---|---|---|---|---|
| en ideal | 150 | 0 | 0 | 150 / 4 / 0 / 52 / 0 |
| ko ideal | 150 | 0 | 0 | 150 / 5 / 3 / 41 / 0 |
| en real | 150 | 0 | 0 | 150 / 6 / 2 / 57 / 20 |
| ko real | 150 | 0 | 0 | 150 / 8 / 2 / 13 / 17 |

So none of the three is inert on d3dev: `hazard` and `dedupe_keep_end` act rarely, `lang_words` gives clause words in every run (whether
they change a reading is not an event).

Tests: robot_agent 2081 -> 2093 collected (dedupe_keep_end +1, lang_words +1 loop regression, hazard +3, precond_repair +1, asr_guard +6), all green;
golden untouched; `lint_arch` 0 new.

Limits: the events are instrumentation; `lab_log` keeps at most 50 entries per run, so in a very long run the new events can push later ones
out of the log (behaviour is not affected).

## L15 plan_release (class plan_missing_step, PROPOSALS P2a)

Status: PARTIAL - done: the option (next-release splice, fetch of the goal object the splice left without one, removal of an empty release whose place is served later), order after precond_repair and plan_complete, its D1 layer, tests (hook level and the real loop's final state), the offline gate below; missing: the Place -> put-in swap of the brief (left to the gate's op_action / op_putin on purpose, see Limits), a goal object the plan names in the plural ('keys' / 'key'), any flip measured (every target replay misses the prompt cache; it needs the GPU pilot), the paired P50 / DEV measure.
Overlaps: `plan_complete` (same hook `on_plan`, same question "is the held object's in-goal release missing before the Close", same kind of data `achieves: in`): its `_release` guard skips the splice when ANY later release exists, and changing it in place would change the d3 arm (the reference); `precond_repair` (`holding` need: Find / Pick of the one unpicked goal object): it cannot do the fetch here because in its replay the put-in skill is no release under the D1 data (PutIn declares no `achieves`), and declaring `achieves: in` there would also turn on its end-of-plan `_finish` (two changes in one arm); the gate operators `op_action` / `op_putin` (Place -> PutIn at the goal container), `op_fetch` (fetch before an empty release) and `op_hoist` (Close / Open moved) act on the planner's raw blocks (`plan_repair.repair` on `owned_plan`), not on the plan the options made, so they do not see the case (the L17 class). The option copies `_key_for` (third copy) and a one-hand replay (options may not import each other). Retire candidate after the D4 measure: `plan_complete._release` (the Close / Open splice), which this option covers for the Close.

What: the plan is replayed with one simulated hand (`robot_agent/options/plan_release.py`). At a Close of the place C that the held object X's `in` goal names, when X's NEXT release (the first
release step before another Pick) is not at C and the plan does not pick X again later (a staging put-down), the pack's `achieves: in` skill goes before the Close (after a MoveTo C when
the robot is elsewhere). The release that splice leaves with an empty hand at place Q: (a) the one goal object of Q (`on` / `in`, not a hand goal) that no step picks gets `Find, Pick` before
the MoveTo that leads to Q (fix `pick_step`); (b) when Q's one goal object has its only Pick AFTER that release and nothing is released after it (the plan ends holding it), that Find / Pick
is brought forward the same way (fix `pick_step`, no new step); (c) when every goal object of Q is picked and a later step releases at Q again, the empty release is removed (fix `removed`);
otherwise it stays (no guess: the last release of an unpicked `on` goal object is never deleted, two candidates are not chosen). A goal's object matches the plan's in other words through
the engine's `exec_integrity.lookup_object`.

Why: the robot's own logs of the D3 arm on d3dev (gate findings; no simulator channel) show plans "Pick X, Close C (X's in place), MoveTo T, Place T" with a second goal at T. `plan_complete`
saw a later release (the mock robot's `put_down` role is Place, so a Place of anything counts) and did nothing; the gate's hoist then moved the Close after the wrong release and the run gave
up ("I could not make a plan that passes my checks"). The trigger is goal semantics (the held object, its `in` goal, a Close of that place); skills come from declared data, roles from
`planner.action_roles`; 0 extra model calls.

Data (D1 layer `plan_release`, `bench/suites/home/planners/d1_options.py`): `planner.options.plan_release.needs = {rules: {PutIn: {achieves: in}, Place: {achieves: on}, Handover: {achieves:
hand}}, assumed: true}` (the names and label of `plan_complete`'s data: the mock robot's own skills; its manifest effects name no goal) and the roles move / find / pick / close (the ones the
D3 layers already declare). Not the `precond_repair` data the brief named: that data declares no `achieves: in` skill (PutIn has only `holding` / `near`) and no service exposes it, so read
through it the option would be inert. An empty or unlabelled pack, no `pick` / `close` role, two hands or more: the plan is unchanged (`*_empty` tests).

Order: hook `on_plan` at 87, after `precond_repair` (85) and `plan_complete` (86), as the brief asks (repair first; the red team proposed 84 so that `precond_repair` would fetch, which it
cannot, see Overlaps). A Close one of them already completed holds nothing in the replay, so no step is added twice (test with the three options in three orders; a second pass over the result
is a no-op). Lab flag `plan_release` `{object, place, fix}` once per distinct edit in a run: the hook also runs inside the gate's score of every candidate plan, so without that the 50-entry lab
log would fill up. A lab event therefore means "edited a plan the gate scored", not "the run's plan changed" (ko ideal below).

Tests: `robot_agent/tests/test_option_plan_release.py`, 16 tests on a made-up pack (skills Stow / Drop / Offer, roles Walk / Spot / Grab / Shut / Ajar; objects gizmo / widget / sprocket / bolt):
`test_registered_and_off_by_default_the_loop_is_unchanged_off` (the real loop with precond_repair and plan_complete on: the gate gives up, nothing moves),
`test_two_hands_or_no_put_in_skill_or_no_roles_change_nothing_empty`, `test_empty_or_unlabelled_or_foreign_pack_data_does_nothing_empty`, `test_loop_final_state_holds_both_goals_with_the_option_on`
(the real AssistLoop with FakeLLM: the FINAL state has the gizmo in the closed drawer and the widget on the side table, one release each, run `success`), the class regression (`plan_complete`
leaves the plan alone, this option splices), next-release, put-in, pick-step, staging, removal, word-match and lab-flood cases. robot_agent tests 2093 -> 2109 (+16, and the architecture
test's entry for the new option). Bench: `tests/home/bench/test_d4_layers.py` (5 tests: the d3 alias equals f751d734... and d2 keeps 64b278b5..., all = d3 + D4 in build order and is the default,
none, plan_release alone on top of d3, labels). `tests/home/bench/test_d3_layers.py`: two assertions now read the D3 arm from the alias `d3` (all = d3 + D4); nothing else changed there.

Offline gate (no model): cache-only replays of all 150 d3dev tasks in the four cells with the D3 development caches, arm `d3` and arm `d3` + `plan_release`, in a scratch directory. The `d3`
replay reproduces the recorded D3 success in 150 / 150 episodes of every cell.

| cell | success d3 / +L15 | false success d3 / +L15 | episodes where it fired | of them passing in D3 | outcome changed where it did not fire |
|---|---|---|---|---|---|
| en ideal | 136 / 136 | 6 / 6 | 2 (removed, pick_step) | 0 | 0 |
| ko ideal | 141 / 141 | 5 / 5 | 2 (splice, splice) | 1: its event came from a gate candidate; the final plan and the outcome are identical | 0 |
| en real | 89 / 89 | 9 / 9 | 3 (splice, pick_step, pick_step) | 0 | 0 |
| ko real | 85 / 85 | 15 / 15 | 1 (pick_step) | 0 | 0 |

Where it changed the first plan the gate's round-0 findings fell (4 -> 1 on the two-object task, 4 -> 2 on the three-object task, 6 -> 4 on the two-container task); none rose. Every changed
failing episode then misses the cache (2 to 6 prompts: the gate's model edit, search ranking, replans), so no flip can be judged offline. The kill criterion (a passing episode whose outcome
changes, a rise of critical findings) is not met.

Limits: Close only (an Open while holding stays `plan_complete`'s and the gate's hoist). No Place -> put-in swap: the gate's `op_action` / `op_putin` do it, and `op_putin` also opens a closed
openable container; an option-made put-in into a closed container would leave a finding no operator repairs (red team). A goal object the plan names in the plural ('keys' for the goal 'key')
is not matched (`lookup_object` compares word sets; plural forms are language data, not added here). The plan shape "empty release before the fetch of its object, plan ends holding it" is now
covered at plan level by (b); KO 133 is a reader error (its `in` goal read as `on`) and KO 040 a hand goal: not this class. Expected gain (red team, rechecked): about +3 to 4 rows of 600 on
d3dev, about half on d4fresh, inside the noise of one run; judge the layer on "no harm" (no false-success rise), not on P50 McNemar.

## L16 effect_check (classes drop_recovery, grasp_misread, silent_drop; PROPOSALS P3a / P3b / P3c)

Status: PARTIAL - done: the option (sensor read after a failed declared release, three-valued engine reading through the service `hand_reading`, the floor of the release room first in the search of a released object), two general engine services (`hand_holds`, `let_go`), its D1 layer with sourced data, tests (hook level, engine reading, the real loop's final state), the offline gate below (no outcome changed, no passing episode touched); missing: any flip measured (every target replay that diverged misses the prompt cache at the refind's or the replan's next model call; it needs the GPU pilot), the paired P50 / DEV measure, P3d (heard_by; not built, by the red team's verdict and the brief).
Overlaps: the engine's own empty-hand path (`assist_loop._recover_place` and `_guard`: a sensor read, then `_refind_dropped`) covers only the literal Place / PutIn and reads a failed sensor call as "empty"; the option reuses it instead of copying it (service `let_go` calls `_refind_dropped`, `_holding` asks `hand_reading`), and `assist_loop.py` (at its size limit) changed by one line rewritten in place, so it cannot hold a new branch; `reach_delivery` (same hook `on_step_failed`, a hand-over that failed `unreachable` after a stale snapshot: asks where the person is) answers another question with other data and is not in the D1 arm; `reopen_on_miss` (`on_step_failed`, a Find after an Open) and `confirm_look` (`on_second_look`, a sighting after a miss) share hooks only; `ask_source` (`prefer_now` from a person's answer) shares the service only. None reads the hand sensor, so none could be extended without taking a second question. The floor head is declared data of this option while `_refind_dropped` still finds the floor by the engine's own head (`floor`); a merge candidate: the engine asks the option for the floor place.

What (`robot_agent/options/effect_check.py`, hooks `on_start`, `on_step_failed`, `on_goal_check` at order 88, service `hand_reading`):
1. A step whose action the data declares a release (Place, PutIn and the hand-over) FAILED while the belief holds an object, and the declared sensor is the robot's holding
   sensor (`RobotView.holding_sensor`, the sensor that verifies its Pick): the sensor is read once (engine service `hand_holds`: True / False / None). Empty: engine service
   `let_go` (a 'dropped' sighting, the belief lets go, then the engine's own DROPPED refind: `_refind_dropped`, the room's floor place in the map, Find, Pick, back to the
   step, the contract's retry cap); NEXT when the refind steps were spliced in, else None with the belief synchronised. Holding or cannot be read: None, the belief keeps the
   object. The failure code is never read as "the hand is empty" (a failed hand-over more often means the person did not take it).
2. Service `hand_reading(skill, raw, default)`: the engine's `_holding` asks it (the same line, rewritten: `query("hand_reading", ..., default=bool(isdone))`, so with no
   option on the reading is `isdone` as before). For the declared sensor, a result that failed with a declared "cannot read" code returns the caller's default, not False.
3. `on_goal_check` of an object this run released at a place (`run.placed`): the one place of that room whose head is the declared floor name goes first in the search for
   the object (`prefer_now`); when the check misses it at its place, the next look is that floor. Never a verdict; the event `floor_armed` says the search was armed.

Why: the robot's own logs of the D3 arm on d3dev (step codes and sensor readings, no simulator channel) show (a) a hand-over that fails `grasp_failed` and is retried as is,
three or four times, while the belief still holds the object (the empty-hand check runs only before the literal Place / PutIn, `assist_loop.py:3526`); (b) a grasp sensor
read that failed `hw_fault` taken as "empty" (`_holding` returns `bool(isdone)`), after which the robot searched for the object in its own hand; (c) a release that reported
success with the object missed at its place by the goal check and searched for elsewhere; the robot's map lists a `floor@<room>` place for every room (the red team's finding
3: the search prompts list them). The reaction of each is generic physics (an object let go falls near where it was let go; a sensor that cannot answer has not said "empty").
The red team rejected reading `grasp_failed` as "empty" (P3b as first written) and the speech listeners field (P3d); neither is read.

Data (D1 layer `effect_check`, `bench/suites/home/planners/d1_options.py`): `planner.options.effect_check.effects = {sensor: {skill: grasp_check, unknown: [hw_fault, software]},
releases: [Place, PutIn, Handover], floor: floor, source: ...}`. SOURCED: the mock robot manifest's `grasp_check` ("isdone = something is held", errors hw_fault and software),
the verify `{sensor grasp_check, expect false}` of its place / put_in / handover skills; the floor head is the ENV's `floor@<room>` place names. No label, a sensor that is
not the robot's holding sensor, no releases, no floor head, two floor places in one room: that part does nothing (`*_empty` tests).

Tests: `robot_agent/tests/test_option_effect_check.py`, 12 tests on made-up packs (sensors palm_probe / grip_eye, releases Gift / Drop / Stash, floor heads ground / floor;
a made-up flat with rooms den / attic and a person pal): `test_sensor_reads_empty_after_a_failed_release_the_belief_lets_go_and_the_refind_runs`,
`test_sensor_reading_is_three_valued_and_only_for_the_declared_holding_sensor`, `test_no_grasp_inference_a_failed_hand_over_with_the_object_in_hand_or_an_unread_sensor_keeps_holding`,
`test_no_heard_by_a_speech_result_with_listeners_is_never_read`, `test_floor_of_the_room_where_the_run_released_the_object_comes_first_in_its_search`,
`test_empty_or_unlabelled_or_foreign_pack_data_does_nothing_empty`, `test_engine_services_default_path_unchanged_off` (`_holding` with no option: a fault reads empty, as before),
`test_registered_default_off_a_hand_over_with_an_empty_hand_is_retried_as_is_off`, `test_loop_final_hand_over_after_the_sensor_read_empty_the_gizmo_is_found_on_the_floor_and_handed`
(the real AssistLoop: the gizmo fell on the way, the hand-over failed once, FINAL: handed to pal, run `success`), `test_loop_final_silent_drop_the_floor_of_the_release_room_is_the_first_look_and_the_widget_ends_on_the_shelf`
(the put-down reported success and the widget fell; the first look after the miss is the den floor, FINAL: on the shelf, `success`), its `_off` twin, and the engine reading with the
option on (a fault keeps the caller's default). robot_agent tests 2110 -> 2123 (+12, and the architecture test's entry for the new option). Bench: `tests/home/bench/test_d4_layers.py` +1 (effect_check alone on top of d3: its option, its
sourced data only, the d3 hash unchanged).

Offline gate (no model): cache-only replays of all 150 d3dev tasks in the four cells with the D3 development caches, arm `d3` and arm `d3` + `effect_check`, in a scratch directory.
The `d3` replay reproduces the recorded D3 success and false success of every cell.

| cell | success d3 / +L16 | false success d3 / +L16 | release events (reading) | episodes whose record changed | of them passing in D3 | new cache misses (unknown) |
|---|---|---|---|---|---|---|
| en ideal | 136 / 136 | 6 / 6 | holding 4 | 2 (one extra sensor read per failed release) | 0 | 0 |
| ko ideal | 141 / 141 | 5 / 5 | holding 1 | 1 (extra read) | 0 | 0 |
| en real | 89 / 89 | 9 / 9 | empty 6, holding 3, unreadable 1 | 8 | 0 | 4: three failed hand-overs now read empty and refind (the D3 run retried the hand-over 3 to 4 times), one sensor fault kept the object, which was then put down and the run went on to the next object |
| ko real | 85 / 85 | 15 / 15 | empty 6, unknown 2, holding 4, unreadable 1 | 7 | 0 | 3 (the same hand-over shape) |

In every changed episode the first divergence is the sensor read or what the belief does right after a read (the P3 offline criterion), never a repeated hand-over; a passing episode where a release read empty (en real) kept
an identical record: the engine's own empty-hand path made the same steps. `floor_armed` was written in 52 to 105 episodes per cell, most of them passing, with no change of
any record: it arms the search only. The kill criterion (a passing episode changed and then failing, a false-success rise) is not met. Expected gain (red team): about +1.5 to 4
rows of 600 on d3dev if the refind's search finds the object; inside the noise of one run; judge the layer on "no harm".

Limits: a sensor that stays faulty leaves the belief as it was (KO real: four hand-overs retried with a faulty sensor, as in D3, plus one read each, 0.5 s of sim time per read). Each
failed declared release costs one more sensor read. The refind after an empty hand is the engine's (its floor head, its retry cap of one per object); the silent-drop part only
orders a search that the replan starts, so a plan that never looks for the object again is not helped. A second robot hand is not modelled (the sensor answers for one hand).

## L17 repair_sync (classes gate_repair_blind, replan_ignores_gate; PROPOSALS P2b)

Status: PARTIAL - done: the option (a second try of the gate's repair from the blocks lined up with the plan the options made, kept only when it certifies the plan; the suffix operator `finish` passes over a goal that holds in the belief; the finding `release_off_goal` on a replan's suffix), its D1 layer (no data), tests (hook level, the pure repair, the real loop's final state for the gate, the suffix repair and the finding's refine), the offline gate below; missing: any measured flip of the gate targets (the target that the second try certifies, and every changed failing episode, miss the prompt cache at a later model call; it needs the GPU pilot), the outcome of the three passing episodes whose replay now misses the cache (see the table), a block replan after a kept second try tested with the real SAGE planner (the tests use a block double), the `on_plan(on_plan(x)) == on_plan(x)` check of every on_plan option under `all` (only plan_release / precond_repair / plan_complete are checked, in L15's tests), the paired P50 / DEV measure.
Overlaps: `replan_guard` (same hook `on_replan_findings`, same question "does the suffix carry a critical finding"): its `critical_refine` counts only action-model codes the pack declares (`planner.options.replan_guard.critical`, part of the frozen d3 overlay), while `release_off_goal` is a goal-level relation no action-model rule emits; adding it there means either a new code in the D3 data (the d3 hash) or a path in replan_guard that bypasses its own data gate, so it is a key of this option instead (one responsibility per key: `off_goal`, can be ablated); `dedupe_keep_end` / `reach_delivery` (services read by the same `plan_repair.repair` call): they change one operator's rule, not the plan the operators see, so the new arguments go through one more service of the same kind (`repair_kwargs`) instead of a new hook; embodiplan's `replan_block_fix` lines completed steps up with the blocks (`_step_key`, `_common_len`, `sage.py`) to find a failed block: same idea, other package and question (the engine may not import the planner), so the alignment here is a 15-line LCS on (action, object) of steps that the same `ground` produced (no name normalisation needed); `_goals_hold` (engine, the end check): `finish_rest`'s "holds in the belief" repeats its two-line `on` / `in` rule (`placed[object] == to`, hand not holding it) because no service exposes it; a merge candidate: an engine service `goal_holds(run, goal)`. The op_finish fix itself is the red team's (`return None` at the first untouched goal, `plan_repair.py`), not a new operator.

What (`robot_agent/options/repair_sync.py`, hook `on_replan_findings` at order 91, service `repair_kwargs(run)`; core `plan_repair.repair(sync=, finish_rest=)`):
1. `gate_sync`: the gate's symbolic repair builds its plan from the planner's sub-goal blocks (`owned_plan`), but the gate scores the plan after the `on_plan` options and the tidy. When the repair
   of the blocks leaves a critical finding, the operators run again from the same start on the blocks lined up with the scored plan (LCS on (action, object): a step of the blocks keeps its block,
   an added step joins the block of the step before it, a step the plan dropped is gone); that result is kept, and written into the blocks, only when it certifies the plan (`synced` in the plan's
   `repaired_by_op`), else the first result stands. The rule "second try only, certified only" comes from the offline gate: run first (the first version), the lined-up plan stopped the dedupe of a
   plan of repeated fetches (the options, re-applied by the score, spliced their release into the repeat) and three passing episodes gave up.
2. `finish_rest`: the suffix operator `finish` gave up at the FIRST `on` / `in` goal the suffix neither holds nor lets go of; the goal check of the suffix starts from nothing, so in a multi-goal run
   that is usually a goal done before the replan, and the pending goal behind it kept its wrong put-down. Now a goal that holds in the belief (`run.placed[object] == to`, the hand not holding it) is
   passed over; any other untouched goal still ends the search (a version that passed over every untouched goal changed a passing correction episode in the offline gate).
3. `off_goal`: a replan's suffix, replayed from the belief with the action model, whose LAST release of an `on` / `in` goal's object (a step that empties the hand; a later Pick of it = a staging
   put-down, not counted) is at another place than the goal's gets the finding `release_off_goal: step i 'A P', goal place of X: T`, so the engine's one refine is told; if it remains, the run ends
   uncertified (the engine's rule). It runs after the suffix repair, so it is the fallback when `finish` could not fix the suffix. Two hands or more: no finding.

Why: the robot's own gate traces and replan suffixes of the D3 arm on d3dev (no simulator channel): a first plan "Pick X, Close C (hand full), [an option appends: MoveTo T, Place T]" where the hoist
found no release in the blocks and the run gave up; replan suffixes that put the held goal object down at another goal's place while `finish` gave up at a goal already done. The fix is plan structure and
goal semantics only; no pack data, 0 extra model calls (the refine of part 3 is the engine's existing one). The FS reduction of the episode where the off-goal put-down was a liquid on a desk comes from
the judge's violation rule, not from the class, and is not counted as evidence for it (red team).

Data: none (D1 layer `repair_sync`: `{repair_sync: 1}`, no overlay; the d3 alias keeps f751d734...). Empty: a planner without blocks (nothing to line up), no goals, an empty suffix, two hands,
all parts off: unchanged (`*_empty` tests).

Tests: `robot_agent/tests/test_option_repair_sync.py`, 14 tests on made-up objects (gizmo, widget, sprocket), places of a made-up yard and the test house: `test_registered_and_off_by_default_the_gate_cannot_repair_the_option_step_off`
(the real loop, option off: the gate gives up, nothing moves), `test_gate_loop_final_the_close_goes_after_the_option_release_and_the_gizmo_is_delivered` (the real AssistLoop with a block planner and
`precond_repair` appending the delivery: FINAL gizmo on the table, drawer closed, one release, run `success`, no model edit), `test_gate_planner_without_blocks_is_left_to_the_old_repair_empty`,
`test_release_off_goal_two_hands_or_no_goals_or_parts_off_do_nothing_empty`, `test_release_off_goal_suffix_off_runs_and_leaves_the_gizmo_on_the_wrong_table_off`,
`test_release_off_goal_loop_final_finish_passes_the_done_goal_and_the_gizmo_ends_in_the_drawer` (a pick fails twice, the scripted suffix puts the gizmo on the widget's table; FINAL gizmo in the
drawer, `success`, one replan), `test_release_off_goal_loop_final_the_finding_reaches_the_refine_and_a_wrong_suffix_never_runs` (finish off: the refine is told `release_off_goal`; a right refine
ends `success`, a wrong one never runs), the alignment, the second-try rule (`test_gate_second_try_only_when_the_blocks_repair_leaves_a_finding_and_kept_only_when_it_certifies`, the regression
of the offline finding), the finish rule with done / not done in the belief, the finding with staging and goal-place cases. robot_agent tests 2123 -> 2138 (+14, and the architecture test's entry
for the new option). Bench: `tests/home/bench/test_d4_layers.py` +1 (repair_sync alone on top of d3: its option, no data, the d3 hash unchanged).

Offline gate (no model): cache-only replays of all 150 d3dev tasks in the four cells with the D3 development caches, arm `d3` + `repair_sync`, in a scratch directory, compared with L16's `d3`
replays (which reproduce the recorded D3 success and false success).

| cell | success d3 / +L17 | false success d3 / +L17 | episodes where it acted (sync tried / done_goal / off_goal events) | outcome flips (determined) | passing episodes changed |
|---|---|---|---|---|---|
| en ideal | 136 / 137 | 6 / 5 | 22 (18 / 25 / 2 events) | the off-goal suffix one: FS -> success | none |
| ko ideal | 141 / 141 | 5 / 4 | 23 (12 / 25 / 1) | the same task: FS -> success; a budget end -> success (second try certified) | 3: one now misses the cache after off_goal's refine (the suffix put the held mug in at the person's spot; D3 ran it, it failed physically and a replan saved it), one misses after a certified plan whose inserted Find is at the wrong place, one same outcome |
| en real | 89 / 89 | 9 / 10 | 17 (15 / 17 / 1) | a gate give-up -> FALSE success: the second try certified the plan of a misread hand goal (the reader gave the keys to the speaker instead of the person named in a corrupted instruction); the gate's failure had hidden the reader error | none |
| ko real | 85 / 85 | 15 / 15 | 18 (10 / 15 / 3) | a gate give-up -> success (second try certified) | 1: the same off_goal episode as ko ideal (misses the cache) |

Totals over 600 cells: success 451 -> 452 determined, false success 35 -> 34; 12 episodes now end in a cache miss (3 of them passing in D3: the off_goal episode in both ko cells and the
certified-plan one above; the other 9 failing in D3), so the real effect is unknown until the pilot. No plan's critical count rose (an edit is kept only when it lowers it, and the second try only when it certifies).
The first-version replay (operators on the lined-up plan from the start) is the evidence for the second-try rule: 3 passing episodes gave up there, 0 now.

Limits: the second try may certify a plan the LLM edit would have rebuilt better (the en real false success above: a reader error the gate's give-up had hidden); `off_goal` turns an off-goal suffix
into one refine and, if it stays, an uncertified end (a new stop on runs that a later physical failure and replan used to save; ablate with `repair_sync.off_goal=0`); a step an option added joins the
block before it, so a later block replan of the next goal does not see it (a block replan regenerates its own steps and the options add theirs again in the score); steps the tidy removed are gone
from the blocks once a second try is kept. Expected gain (red team, after the offline gate): about +1 to +3 rows of 600, inside the noise of one run; judge the layer on "no harm" (P50 false success).

## L18 goal_ledger (class goal_dropped, part of asr_loss; PROPOSALS P1, R1 limited and R4 apart, no R2)

Status: PARTIAL - done: the option (R1 `restore`: a go goal the F4.4 filter would drop is kept at the drop site when a heard word starts with a name of its place, and its unsaid issue and the heard word's object issue are settled; `named`: kept with no evidence and named by the engine's read-back; R4 `retract`: the engine's where-issue for a destination named only before a self-correction marker), the engine seam (service `goal_keep`, argument `keep_go` of `goal_fix.drop_invented`), its D1 layer (restore only), tests (pure, hook level and the real loop's final state, among them the safety gate, cond_goal, a re-sample and a correction), the offline replay gate below (named turned off by it); missing: any measured flip (every changed episode misses the prompt cache at its next model call; it needs the GPU pilot), R4's firing on passing episodes (R4 stays off in D1; its two d3dev targets are below the three-task rule), the R2 shadow (not built: no registry-level shadow mechanism exists, the R2 firing rate can be counted offline from the caches; a general `shadow` key is a registry change of its own), L22 partial_end reading `ledger_open` (L22 is not built), L23 question_cap counting the R4 question (L23 is not built; the question goes through the engine's ask path), the paired P50 / DEV measure.
Overlaps: `goal_words` (same seam: its service `goal_guard` already plugs into `drop_invented` through `places.guard` and answers the whole-word question for `on` / `in` goals' objects): extending its Guard with a go-goal rule was possible, but the frozen interface names the layer `goal_ledger` with its own test file, `goal_guard` is a first-answer query of the D3 arm's option (its answer object would carry a second responsibility), and R4 is not a filter question; a merge candidate after the measure: one "filter guard" service for both; `name_recover` (same hook `on_issues`, same pattern "settle the issue of a word the option explained"): it re-grounds a garbled OBJECT name against the catalogue and asks "Did you mean"; goal_ledger never asks and works on PLACE names of go goals, so nothing is shared but the pattern; `entity_cover` (`_taken_back`: a catalogue object named before a self-correction marker is not asked about): the same marker idea for objects, inverted (it removes an issue, R4 adds one for a destination); R4 reuses the core's `understand._drop_corrected` with the pack's markers instead of entity_cover's or a new parser; `hazard` (the gate): reused, not duplicated (the kept goal reaches its `on_goals` at order 10; the `safety_gate` service is not needed); `ask_agree` (`veto_own_doubt`): `named` relies on it, nothing added; `partial_end` (L22): the end sentence about an open item is L22's; goal_ledger says nothing at the end and serves `ledger_open(run)`, so two options never both say "I left out X". Retired by this layer: none.

What (`robot_agent/options/goal_ledger.py`, hook `on_issues` at order 22, services `goal_keep(run, goals)`, `ledger_open(run)`; core: `goal_fix.drop_invented(..., keep_go=None)`, one call line in
`assist_loop._ground_understood` rewritten in place to pass the service's answer):
1. `restore` (on with the option): F4.4 drops a `go` goal whose place is not an exact mention of the words while other goals remain. At that drop site the predicate keeps it when a heard word
   STARTS with a name (ENV head or alias) of its place and that name's last word is at least `min_share` (0.5, the option's assumed default) of the word: a slip at the end of the word. A name
   inside a word ("reroost") or a small part of a long word ("roosterhouse") is no evidence (no letter distance: a jamo or edit distance would fit one synthetic noise model, red team finding 6).
   `on_issues` then removes the kept goal's `unsaid` issue and the object issue of the heard word itself (the engine's own object check asks "Did you mean the <alias>?" about a garbled word that
   follows an article), so the goal is restored with no question and no re-sample. Kept at the drop site, it keeps its position, passes the safety gate (`hazard`, order 10), `cond_goal` (its
   `when`) and `go_steps` as a said goal would, and every re-sample of the read-back keeps it again (a restore in a later `on_goals` hook would be thrown away by the re-sample and skip those steps).
   Only F4.4's go drops are seen: goals dropped by `goal_filter`, `go_steps`, `cond_goal`, `drop_echo_say` never reach the predicate.
2. `named` (default off; OFF in D1): a goal with no such word is kept too; its `unsaid` issue stays, the read-back's re-sample runs (two model calls), and the engine's read-back names it with the
   robot's doubt ("I am not sure I understood (you did not say the ...)"). No new phrase and no new question (`issue_question` asks nothing for a goal with no object). Side effects: it uses the
   run's `issue_asked`, and with `ask_agree` an "I don't know" to that read-back is a refusal.
3. `retract` (default off; OFF in D1): an `on` / `in` goal whose destination the words name only in a mention a self-correction marker takes back (`understand._drop_corrected`; the pack's markers,
   or the option's `retract_markers` per language, manifest data labelled, read again at run time), when words follow the marker and they name no place or object of another goal, gets the
   engine's `unsaid` issue with its object, so the read-back asks the engine's own "Where should I put the X?". The pack's `ko.json` markers are not edited (the D3 arm reads them).
No "Did you mean X?" is ever added (user decision: no R2).

Why: the robot's own logs of the D3 arm on d3dev (understand events, `filtered`): in the real profile F4.4 dropped a go goal six times, every time the reader's go-to-the-dock goal of a request
ending "... then go back to the <dock place>" whose last word the recogniser garbled (a Korean word with a slip at its end; an English sentence cut before the place); the run ended done without
it (two false successes). `filtered` held no go drop in any ideal log. No simulator or person channel: the rule reads the engine's filter and the heard words. The class rests on one ending of the
task generator (all observed drops), so the layer is judged on its false-success rows and its firing precision, not on the score (red team: about +0.6 row from R1, below what a paired test sees).

Data: none for R1 (the place names are the robot's ENV); `min_share` is the option's assumed default; `retract_markers` none in D1 (R4 off). D1 layer `goal_ledger`: `{goal_ledger: 1}`, no
overlay; the d3 alias keeps f751d734.... Empty: no name heard, no marker, a language with no markers, no ENV aliases: nothing kept, nothing added (`*_empty` test); the open item is served by
`ledger_open`.

Tests: `robot_agent/tests/test_option_goal_ledger.py`, 18 tests on a made-up house (a nook in a den with the alias roost, a vask in a zon with the alias kruvo), made-up objects (gizmo, widget),
a made-up language `zq`: `test_registered_default_off_and_the_filter_drops_as_before_off`, `test_no_name_heard_no_marker_no_data_does_nothing_empty`, the restore rule (position kept first and last,
short-alias and share decoys, the issues settled, the made-up language, a go_steps drop never brought back), `named`, `retract` (nothing after the marker, another goal after it, the place said
again, a polite marker, the option's narrower list, the made-up language), and through the real AssistLoop with a fake model: `test_restore_loop_final_the_robot_ends_in_the_nook_with_no_question`,
`test_no_did_you_mean_loop_final_off_asks_about_the_garbled_word_on_asks_nothing` (off: the engine's object check asks "Did you mean the roost?"; on: no clarify event at all),
`test_named_loop_final_the_read_back_names_the_nook_with_the_doubt_and_a_yes_reaches_it`, `test_restore_loop_final_a_re_sample_for_another_issue_keeps_the_go_goal` (the first reading misses an
object: the two re-samples agree on a set with the kept go goal; off: they drop it), `test_safety_gate_loop_final_a_restored_go_goal_meets_the_hazard_gate_and_is_refused` (a made-up profile with
`checks: [go]` and a rule forbidding the nook: the restored goal is refused, the rest is done and the refusal said), `test_restore_loop_final_cond_goal_still_decides_a_kept_go_goal_with_a_condition`,
`test_retract_loop_final_the_where_question_is_asked_and_the_answer_places_the_gizmo`, `test_named_loop_final_a_correction_that_removes_the_go_goal_is_not_undone`. robot_agent tests 2134 -> 2153 (+18,
and the architecture test's entry for the new option). Bench: `tests/home/bench/test_d4_layers.py` +1 (goal_ledger alone on top of d3: its option only, named and retract off, no data, the d3 hash unchanged).

Offline gate (no model): cache-only replays of all 150 d3dev tasks in the four cells with the D3 development caches, in a scratch directory: arm `d3` with the current code (it reproduces every
recorded D3 outcome and status, 600 of 600, so the 174 real passes replay identically) and arm `d3` + `goal_ledger`.

| cell | success d3 / +L18 | false success d3 / +L18 | episodes where it acted (restore / named events) | outcome flips (determined) | passing episodes changed |
|---|---|---|---|---|---|
| en ideal | 136 / 136 | 6 / 6 | 0 | none | none |
| ko ideal | 141 / 141 | 5 / 5 | 0 | none | none |
| en real, restore + named | 89 / 89 | 9 / 8 | 1 (0 / 4): the cut sentence, named | FS -> cache miss | none |
| ko real, restore + named | 85 / 84 | 15 / 14 | 7 (7 / 7): restore in 3 failing; named in 2 failing and 2 PASSING (one unchanged, one now a cache miss after the read-back) | FS -> cache miss; a pass -> cache miss | 1 |
| en real, restore only (D1) | 89 / 89 | 9 / 9 | 0 | none | none |
| ko real, restore only (D1) | 85 / 85 | 15 / 14 | 3 (7 / 0): the three failing episodes whose heard word starts with the dock alias | FS -> cache miss (the garbled-dock false success); a give-up -> cache miss; one unchanged (search budget later) | none |

`named` fired on as many passing as failing KO real episodes (2 and 2; the red team's kill line wants failures at least twice the passes), so the D1 layer keeps `restore` only. The alias-at-start
rule caught the three Korean slips the red team expected (a dock alias followed by one or two extra syllables); the two others need a letter distance and stay out on purpose. The real effect of
every change is unknown until the pilot (the restored goal changes the next planning call).

Limits: one ending of the task generator is the whole evidence, so the layer may fire in fewer than three episodes and be retired; `min_share` 0.5 lets a real word that starts with a short alias
count ("docking" for "dock"); a heard word that starts with the alias but means something else ("charge it" for a dock alias "charge") keeps a go goal the reader invented to that place (it would
need the reader to invent it first); `named` costs two re-sample calls and a read-back turn per firing; R4's markers may be polite words in a language whose pack lists them (the option's own list
narrows them); the restore makes the engine's object check silent about the heard word, so a garbled word that was ALSO an object name is no longer asked about.

## L21 safety_profile (classes hazard_unrefused, hazard_missed: three d3dev tasks of ONE family; user decision: hazard as cited data)

Status: PARTIAL - done: the mechanism (a safety profile declared as the robot's data in `planner.options.safety_profile.profile`, a map distance `within_m` in the core profile schema, the hazard gate asking the option's rules through the service `safety_rule`), its D1 layer with ONE cited rule (US Fire Administration, Heating Fire Safety: anything that can burn at least 3 feet = 0.91 m from fireplaces, wood stoves, radiators, space heaters, candles), tests (pure, hook level, the decoy table, the real loop's final state), the offline replay below; missing: a verified clearance source for cooking appliances (stove / cooktop / hob, oven, toaster, kettle, iron, microwave stay without a rule: BRIEF section 12 found none), and the heat source of all three d3dev hazard tasks is a kitchen stove, so these tasks are expected to stay unrefused with this data; the paired P50 / DEV measure.
Overlaps: `hazard` (same hook `on_goals`, same question "does a safety rule forbid this goal", same kind of data: a profile of classes and rules): NOT duplicated, extended: hazard's gate stays the only gate (refusal of the whole request, drop of a part with its end sentence, the `refusals` record, the `forbids` service the read-back asks, the `safety_gate` re-run), and its `verdict` asks the new service `safety_rule` after its own rules (4 lines; no answer = the old verdict, golden green); the rule engine is the core's (`find_rule`, the profile loader and validator), extended by one general rule key `within_m` and the matcher `near_class` (the map relation), not copied. A key of hazard instead of a new option was the first choice, but the frozen interface (BRIEF section 4) names a registered option `safety_profile` with its own data section, and hazard's data is the manifest's `safety.profile` file of the frozen mock-robot pack (its household.yaml is under `symbolic_robot/`, which may not change), so the rules need a section the D1 overlay can declare; `hazard.receivers` (a key of hazard, same engine) stays as it is. Merge candidate: once a robot's own profile file can carry `within_m` rules, the `safety_profile` option is not needed (hazard reads them directly from `safety.profile`) and can be retired. `safety.refusal_marks` / `typed_refusal`, `ask_agree` (`unrefused`): readers of a refusal, untouched.

What (`robot_agent/options/safety_profile.py`, hook `on_start` at order 11, service `safety_rule(goal, places)`; core `core/safety/profile.py` (`Rule.within_m`, validated: a number >= 0 on a
rule with `places`), `core/safety/place_class.py` (`near_class`), `core/safety/hazards.py` (a place rule fires also on a place near a place of its classes), engine service `safety_rule`
(`option_services.py`, `core/options/services.py`); `options/hazard.py` `verdict` asks it): the option reads its profile again from the manifest at each run start and when asked (data that arrives after
the loop was built counts), loads it with the core loader (an error = EMPTY and a lab event: fail open), and answers the first rule that fires. A rule with `within_m` forbids the goal's place
when the place is of the rule's class (by its names, as every profile rule) or lies LESS than `within_m` metres from a place of that class on the robot's map (ENV `loc` x / y; same room when both
keys name one; persons and places with no `loc` take no part). The refusal is hazard's sentence with the rule's `say` (pack data, prompt language, said in the person's language by the loop as
every profile rule; no literal in the option).

Why: in the D3 arm on d3dev, three tasks of one generator family (EN / KO, ideal and real: 3 + 3 rows, all false successes) asked to put an ignition source on the kitchen stove; option `hazard`
had nothing to refuse because the robot's profile held no fire rule (PROPOSALS section 6, decision of the user: a rule as DATA of the robot with an external cited source, default empty, with an
over-refusal check). No simulator or generator channel: the rule is the cited page's, its classes are the page's, and the words of "anything that can burn" are general vocabulary (assumed).

Data (D1 layer `safety_profile`: `{safety_profile: 1}` and `planner.options.safety_profile.profile = FIRE_CLEARANCE`, `bench/suites/home/planners/d1_options.py`): source
"US Fire Administration (FEMA), Heating Fire Safety, page reviewed 2023-05", https://www.usfa.fema.gov/prevention/home-fires/prevent-fires/heating, quote "Keep anything that can burn at least 3
feet from all heat sources including fireplaces, wood stoves, radiators, space heaters or candles." (opened and quoted by the coordinator, BRIEF section 12). Place class `heat_source` (provenance:
that source; English words of the five classes, Korean words their translations), hazard class `can_burn` (words assumed, EN and KO: paper, books, cardboard, cloth, towels, curtains, wood,
matches, lighters, aerosols ...), rule `burnable_near_heat` (`within_m` 0.91, provenance: that source). The candle page (12 inches) is subsumed by the 3 feet of the heating page and not used. No
rule for cooking appliances (the bench test asserts that no heat-source word matches stove, gas stove, oven, cooktop, hob, toaster, kettle, iron, microwave). The option's own default carries no
rule (`profile` = {}); the d3 alias keeps f751d734....

Tests: `robot_agent/tests/test_option_safety_profile.py`, 13 tests on a made-up pack (a made-up language `xx`, things that "flare": flimmer, pappel; a "glow source": glowbox, ember stand; a rule
1 m with a made-up leaflet of 2031): `test_safety_profile_off_by_default_and_the_gate_does_not_see_its_rules_off`, `test_safety_profile_no_profile_an_empty_one_or_a_foreign_one_forbids_nothing_empty`,
`test_refuse_a_flarable_thing_on_a_glow_source_and_near_one_within_m`, `test_over_refusal_decoy_table_nothing_else_is_refused` (a non-flarable thing next to the glow source, a flarable one 3 m
away, one in the next room near on the map, one handed to a person standing near it, one to a place with no position), `test_source_a_rule_cites_a_declared_source_or_the_whole_profile_is_refused_and_forbids_nothing`,
`test_within_m_must_be_a_distance_of_a_place_rule`, `test_near_class_measures_on_the_map_in_the_same_room_and_fails_open`, `test_refuse_the_whole_request_or_drop_the_part_through_the_hazard_gate`
(the regression shaped like the class), `test_hazard_rules_off_turns_the_declared_rules_off_too_off`, `test_hazard_without_the_service_keeps_its_old_answer_off`, and through the real AssistLoop with a
fake model: `test_loop_final_refuses_the_flarable_thing_near_the_glow_source_and_leaves_it_where_it_was` (refused, the object unmoved, the rule's sentence said, `refusals` names the rule),
`test_loop_final_off_the_same_request_is_carried_out_as_before_off`, `test_loop_final_over_refusal_decoys_both_are_carried_out`. robot_agent tests 2153 -> 2167 (+13, and the architecture
test's entry for the new option). Bench: `tests/home/bench/test_d4_layers.py` +1 (safety_profile alone on top of d3: its option and a cited profile only, no rule for uncited heat sources, the d3
hash unchanged); its build-order assertion now reads "the built D4 layers in build order" (a subsequence) instead of "a prefix of the build order", because the layers are built in parallel worktrees.

Offline replay (no model): cache-only replays of all 150 d3dev tasks in the four cells with the D3 development caches (copied to a scratch directory), arm `d3` + `safety_profile`
(the L21 worktree code), compared with the recorded D3 episodes:

| cell | success d3 / +L21 | false success d3 / +L21 | episodes where the profile was in force (lab `loaded`) | episodes where a rule fired | outcome changes |
|---|---|---|---|---|---|
| en ideal | 136 / 136 | 6 / 6 | 150 | 0 | none |
| ko ideal | 141 / 141 | 5 / 5 | 150 | 0 | none |
| en real | 89 / 89 | 9 / 9 | 150 | 0 | none |
| ko real | 85 / 85 | 15 / 15 | 150 | 0 | none |

The data reaches the option in every episode (not inert by wiring), and the cited rule refuses nothing on d3dev: no over-refusal there, and no gain either (the three hazard tasks are
about a cooking stove, which the cited page does not cover). The layer stays on only as a safety rule (the stay gate's "written safety reason"); its effect on the hazard family is zero until a
source for cooking appliances is verified. Report the hazard family apart from the rest (three tasks share it).

Limits: the three d3dev tasks of the family put an ignition source on a cooking stove, for which no verified source was found, so the layer is expected not to change them (the class stays
open until a source for cooking appliances is opened and quoted); place positions are points (the centre of a piece of furniture), so "less than 0.91 m" between two centres misses a gap measured
between edges and may also call two large pieces near; a place of the heat-source class is known by its names only (no `category` or device data); the `can_burn` words are an assumed list, so a
thing not on it is never refused and a word on it may name a thing that does not burn (a "wooden" toy is refused near a radiator, as the cited page would want); the rule needs the robot's ENV
`loc`, so a robot without positions gets only the "on the heat source itself" part; the Korean heat-source words are translations of the cited classes.

## Complexity budget

Measured on robot_agent at base 64c7e72 (before S0), after S0, and after each D4 layer. Option lines: `robot_agent/options/*.py` without `__init__.py`.

Layers on: 23 (`all` = the 18 D3 layers + L15 plan_release + L16 effect_check + L17 repair_sync + L18 goal_ledger + L21 safety_profile (built in parallel with L22-L24: each worktree counts its own); the `d3` alias keeps 18; the layers' loop options grow by five keys, `plan_release`, `effect_check`, `repair_sync`, `goal_ledger`, `safety_profile`)
Option lines: 3889 in 33 modules (L21 safety_profile +65, hazard +4 (verdict asks safety_rule); after L18 3820 in 32; L18 goal_ledger +161; after L17 3659 in 31; L17 repair_sync +134; after L16 3525 in 30; L16 effect_check +138; after L15 3387 in 29; after S0 3190 in 28; L15 plan_release +197; before S0 3174: hazard +2, dedupe_keep_end +6, lang_words +2, precond_repair +6, hw_wait 0). Core: plan_repair.py +9 (S0), assist_loop.py 0 (L16: one line rewritten in place; L17: two lines rewritten in place), option_services.py +19 and core/options/services.py +2 (L16: services hand_holds, let_go), plan_repair.py +21 (L17: arguments sync / finish_rest, the edit loop as the helper _edits), goal_fix.py +1 and assist_loop.py 0 (L18: argument keep_go of drop_invented, one call line rewritten in place), core/safety/profile.py +10, place_class.py +30, hazards.py +8, option_services.py +4, core/options/services.py +1 (L21: rule key within_m, near_class, service safety_rule)
Hooks: 56 hooks and 27 services over 33 registered options (L21 +1 hook: safety_profile on_start, +1 service safety_rule, no new hook kind; after L18 55 and 26; L18 +1 hook: goal_ledger on_issues, +2 services goal_keep, ledger_open, no new hook kind; after L17 54 and 24; L17 +1 hook: repair_sync on_replan_findings, +1 service repair_kwargs, no new hook kind; after L16 53 and 23; L16 +3 hooks: effect_check on_start, on_step_failed, on_goal_check, +1 service hand_reading, no new hook kind; after L15 50 and 22; after S0 48 and 22; L15 +2: plan_release on_start, on_plan)
Retired: none yet (the retire decision needs the paired D4 measure. Candidates named: release_near and hw_tries as separate layer entries, plan_complete into precond_repair, ask_focus.unrefused, plan_complete._release once L15 is measured; the literal Place / PutIn empty-hand path of the engine and its floor head, once effect_check is measured; L15 plan_release's Close splice partly overlaps what repair_sync's second try now finds (a release an option added before a hand-full Close), to be judged on the paired measure; goal_ledger's `goal_keep` and goal_words' `goal_guard` are two answers at the same drop site, a merge candidate after the measure; goal_ledger's `named` and `retract` keys are off in D1 and retire with the layer if they stay unmeasured; safety_profile once a robot's own safety.profile file carries within_m rules (hazard then reads them directly))
