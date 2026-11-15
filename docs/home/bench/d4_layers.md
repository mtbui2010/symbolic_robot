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

## L19 answer_align (classes ask_loop, wrong_answer_accepted, correction_misapplied; PROPOSALS P5)

Status: PARTIAL - done: the core helpers (`names.reading_words`, `distinguishing`, `says`, `which_named`, `endings`, `speaker_words`), the option (`reask`: a yes or no to an either-or asked once more naming the options; `correction`: a correction that names one object leaves the other goals' earlier destination and source, with its `unsaid` issue settled so the read-back's re-sample keeps it), the key `distinct` of `ask_agree` (the read-back's either-or by distinguishing words; an object changed with its own `from` and words is one change), the phrase `q_pick_one` in the English and Korean packs (assumed), its D1 layer (reask and correction on, `ask_agree.distinct` off), tests (pure, hook level and the real loop's final state for reask and correction), the offline replay gate below; missing: any measured flip (every episode where it acted misses the prompt cache at its next model call; it needs the GPU pilot), `ask_agree.distinct` in D1 (the gate fired it on one passing and one failing episode of the same request: off by the red team's kill ratio until a pilot), the ask_loop rows that distinguishing words cannot reach (a Korean answer whose only word both readings share; the earlier reading is not the one the person meant; the ASR- and dialogue-specific rows), the correction target the gate did not fire on, a shadow mode (no registry-level shadow mechanism exists), L23 question_cap counting the re-ask (L23 not built; the re-ask goes through the engine's `ask_clarify`, so an engine count sees it), the paired P50 / DEV measure.
Overlaps: `ask_agree` (same question "which reading does the answer name", same data: the language packs' dialogue words): the read-back's either-or is extended there as the key `distinct` (same hook `on_goals`, same service `unrefused`), not copied; `reask` needs the hook `on_heard` (the reader's own either-or question, before the reader reads the answer), which ask_agree does not have, and `correction` acts on the reader's re-read after a correction, not on the read-back's answer; the frozen interface also names the layer `answer_align` with its own registered option and test file, so these two are its keys; `asr_guard` (same hook `on_heard`): another question (a garbled request is asked again), no shared data; the engine's own correction path (`_correction_edit` / `_patch_goals`: a correction that names a goal's destination edits that goal without a re-read): answer_align acts only when the engine re-read the task instead, and matches with the new core helper rather than a second parser; a merge candidate: the engine's correction edit choosing its goal by `names.which_named`; `dialog_agree.names_option` (the engine's either-or answer match, read by `which_one` and by ask_agree off): the same question by whole phrases; a merge candidate onto `names.distinguishing` once measured; `recipient_keep` and `dialog_converge._speaker_words` read the same pack key `grammar.speaker_forms` for other questions; `names.speaker_words` is a third reader of it (merge candidate: one core function); `goal_ledger` (`on_issues`): the same pattern (settle the `unsaid` issue of a goal the option kept), for another goal. Retired by this layer: none (candidates: ask_agree's whole-phrase `said()` once `distinct` is measured).

What (`robot_agent/options/answer_align.py`, hooks `on_heard`, `on_goals`, `on_issues`, order 8; core `names.py`: the readings' words; `ask_agree.py`: key `distinct`, helpers `object_change`, `_back`):
1. `reask` (on with the option): the robot's last question offered options (its declared `ask.options`, else the clause on each side of a pack's `grammar.sep_or`; a read-back is never one) and the answer holds a yes or no word of the packs and names none of the options by their distinguishing words: the reader would pick one from nothing (the class: a bare "yes, that one" to "the A or the B?" read as a choice, two false successes in the D3 logs). The robot asks ONCE per run "Which one do you mean: A or B?" (`q_pick_one`); an "I don't know" (service `unsure_leftover`), an answer with another word in another declared script than the options (it may name one in the person's own words), or a language with no phrase: nothing asked.
2. `correction` (on with the option): after a correction to the read-back the reader re-read the task; when the correction's words name exactly ONE object of the readings (its distinguishing words against every other object: the catalogue name, the person's own words `said` / `name_local` learnt from earlier readings, one declared particle or ending), each goal of another object that the new reading sent elsewhere gets its earlier destination and source back. None named, two named, or a result equal to the refused reading: nothing decided. The engine counts the restored place as `replaced` by the correction, so `on_issues` settles that goal's `unsaid` issue (else the read-back's two re-samples bring the misapplied reading back; found by the loop-final test).
3. `ask_agree.distinct` (default off; OFF in D1): the earlier value counts as said, and the either-or's answer names a reading, by distinguishing words (a phrase of shared words, "jar" against "teal jar", says nothing); an object changed with its own `from` / `said` / `name_local` is one change and a pick of the earlier object brings them back.
For a delivery to the person talking the readings' words hold a speaker marker matched by the speaker's own words (`grammar.speaker_forms` minus `speaker_forms_weak`; a one-letter form, a demonstrative too in Korean, only with an ending), never the robot's word for its addressee.

Why: the robot's logs of the D3 arm on d3dev: `ask_agree.said()` needs the whole catalogue name as a phrase (an answer naming the earlier reading by one word never got the either-or), a yes or no to an either-or was read as a choice, and a correction naming one object moved another object's goal too. No simulator or person channel: the rules read the robot's own questions, the person's words and the readings.

Data: none of its own; the language packs' words (`particles`, `grammar.noun_particles`, `dialogue_ext.polite_endings`, `grammar.speaker_forms` / `speaker_forms_weak`, `grammar.sep_or`, `dialogue.yes` / `no` / `fillers` / `polite`, `script.letters`) and the new phrase `speech.q_pick_one` (English and Korean, `assumed: true`). D1 layer `answer_align`: `{answer_align: 1}`, no overlay; the d3 alias keeps f751d734.... Empty: a pack with none of these words: nothing asked, nothing changed (`*_empty` test).

Tests: `robot_agent/tests/test_option_answer_align.py`, 19 tests on a made-up house (a den with a ledge and a crate, a loft with a rack and a nook, a speaker `pat`), made-up objects (jars, a tin box, a reed basket), a made-up agglutinative language `zq` (particle `-ka`, ending `-ra`, `mizuni` / `m` = to me) and a made-up script: `test_distinguish_*` (one word of a name, a shared word, a place alias, the read-back's either-or with `distinct`, an object changed with its place, a shared-word earlier name), `test_speaker_*`, `test_made_up_agglutinative_language_*`, `test_either_or_*` (once, read-back excluded, declared options, unsure, another script, the made-up language's phrase and none), `test_correction_*`, `test_answer_align_empty_pack_or_no_data_does_nothing_empty`, and through the real AssistLoop with a fake model: `test_loop_a_yes_to_the_either_or_is_asked_again_and_the_final_state_holds_the_jar_named`, `test_loop_answer_align_off_the_yes_is_read_as_a_pick_final_state_unchanged_off`, `test_correction_loop_final_the_object_the_correction_does_not_name_stays_where_it_was_said` (on and off). robot_agent tests 2157 -> 2177. Bench: `tests/home/bench/test_d4_layers.py` +1 (answer_align alone on top of d3: its option only, distinct off, no data, the d3 hash unchanged).

Offline gate (no model): cache-only replays of all 150 d3dev tasks in the four cells with the D3 development caches, in a scratch directory: arm `d3` (current code; equal to the L18 gate's d3 replay, which reproduces the recorded D3 outcomes) and arm `d3` + `answer_align` as in D1.

| cell | success d3 / +L19 | false success d3 / +L19 | episodes where it acted | outcome flips (determined) | passing episodes changed |
|---|---|---|---|---|---|
| en ideal | 136 / 135 | 6 / 6 | 1 reask: a bare "yes, that one" to a two-place either-or | a pass -> cache miss | 1 (the D3 arm read the yes as a pick, doubted it and asked "Where should I put ...?" next; the re-ask asks that choice one turn earlier) |
| ko ideal | 141 / 141 | 5 / 5 | 0 | none | none |
| en real | 89 / 88 | 9 / 8 | 3 reask: the same passing request as above, a false success (the yes / no target), a give-up (still a give-up) | FS -> cache miss; a pass -> cache miss | 1 (the same request) |
| ko real | 85 / 85 | 15 / 15 | 3 correction, all failing (two give-ups, one budget; one is a correction target) | none determined (all cache misses) | none (one passing record differs only in its cache-hit counter in the parallel run, not alone) |
| en / ko real with `distinct` on (not D1) | 89 / 88, 85 / 84 | 9 / 8, 15 / 15 | either-or asked on one request in both languages (EN give-up target, KO pass) | each -> cache miss | 1 (KO): kill ratio, so `distinct` stays off in D1 |

`reask` fired on two passing and two failing episodes (one passing request in two cells, against the false-success target and a give-up): by request 1 pass to 2 failures, by episode 2 to 2; it is kept on in D1 because in that passing request the robot itself doubted the pick and asked the same choice one turn later (the re-ask replaces that question), and its target is a false success. The coordinator may turn it off with `answer_align.reask: 0` if the episode ratio is the rule. The `distinct` replay first found two passing English episodes where the whole-phrase rule called a one-word name (said inside a longer name of another object) the earlier reading against a current longer name that holds the same word; with `distinct` the phrase rule is not used, and those two no longer fire.

Limits: a model-written question that holds the pack's "or" but is no either-or ("is it on the table, or should I look elsewhere?") gets one re-ask after a yes; the options of a question are the robot's English clauses, so in another script only a bare yes or no is re-asked; a correction that names its object only by a word the reader never put in `said` / `name_local` and the catalogue name does not hold decides nothing; the restore keeps the earlier source too, so a source the re-read corrected for the other object is lost; a one-letter speaker form with an ending can still be another word (the Korean first-person form with a topic particle, "as for me", in an answer).

## L23 question_cap (class "the robot keeps asking": every option bounds only its own questions; user decision: at most 3 per task, never the same question twice)

Status: PARTIAL - done: the option (a cap of questions per task counted by the run's own counters, a veto of a question whose normalised text was already put), the engine seam (service `ask_veto` asked by the engine services `ask` and `ask_clarify`, the options' way to ask; no option serving it = as before, golden green), its D1 layer (the cap 3 assumed, `no_repeat` on), tests (off, empty, cap, no_repeat, run-time data, the real loop's final state with made-up asking options); missing: the engine's own questions (read-back, the search's "where is it?", the pick / move help, which-one, `confirm_near`) are counted (`confirms`, `asked`) but never vetoed (`assist_loop.py` is at its size limit, and a vetoed read-back would mean acting on an unconfirmed reading: a safety question for the coordinator), a measured repeat rate (the episode rows hold no question text), any measured flip (needs the GPU pilot), the paired P50 / DEV measure.
Overlaps: the engine's `clarify_rounds` cap (`_ask_clarify`, the same counter `run.asked`): it bounds only the loop's clarify step, an option's `svc.ask` was never checked against it, and it ends the run "still unclear" instead of letting the option act; `_fresh_question` (engine): the same word-for-word repeat test, but only for clarify questions, and it re-words the question once instead of not asking; `dialog_converge.same_question` (near-same questions of the read-back loop, three content words): a looser test for the read-back, not reused because "the same normalised text" is the user's rule and a near-same match would veto a question that names another object; `ask_focus` (`max_confirms`, service `confirm_limit`): the same idea for read-backs only, on the read-back hook; extending it was possible (a new key) but its service is a read-back limit the engine turns into a failed run, and its hook `on_issues` is not on the ask path; `goal_ledger` / `ask_agree` / `name_recover` / `recipient_keep` / `goal_words` / `cond_extract`: each asks at most once per item and none sees the others' questions, which is the class itself. None of them is on the one place all options ask (`LoopServices.ask`), so the veto is one service there, not a branch in each asking option. Retired by this layer: none (candidate after the measure: `ask_focus.max_confirms` if the cap also gates read-backs one day).

What (`robot_agent/options/question_cap.py`, hook `on_start` (the task's record starts empty), service `ask_veto(run, question)`; core: `option_services.LoopServices.ask` and `.ask_clarify` ask the service first, +14 lines):
1. `cap` (data `max_questions`, per robot, `planner.options.question_cap.max_questions`, read again at run time; 0 or none = no cap): a question is not put when the run's `asked` (every clarify round and every option question, refunds included) plus `confirms` (the read-backs) already reach the cap.
2. `no_repeat` (key, legacy run option `question_cap_no_repeat`): a question whose normalised text (case folded, punctuation dropped, spaces collapsed; no word list of any language) was already put through the service in this task, or is a robot turn of the run's dialogue, is not put.
A vetoed `ask` returns '' (no answer: the asking option keeps what it has and the run acts); a vetoed `ask_clarify` decides nothing (the loop reads on). Lab flag `question_cap`: `{why: cap | repeat, asked}`.

Why: the D3 arm's own episode rows on d3dev (development set, optimistic): in the real profile 49 of 300 episodes put more than 3 questions to the person (21 EN, 28 KO) and 18 of them succeeded (37 %), against 156 of 251 (62 %) for the episodes with at most 3; in the ideal profile 4 of 300. This is a correlation (hard tasks get more questions), not a proof that the extra questions caused the failures; the cap and the no-repeat rule are the user's decision (BRIEF section 5), the red team's open item 4 (a global cap over P1 / P4 / P5 / W, `name_recover` and `ask_agree`). No simulator or person channel: the rule reads only the run's own counters and question texts.

Data: D1 layer `question_cap`: loop options `{question_cap: 1, question_cap_no_repeat: 1}`, overlay `planner.options.question_cap = {max_questions: 3, assumed: true}` (the user's number, not measured). An empty pack (no cap declared, `no_repeat` off) vetoes nothing.

Test: `robot_agent/tests/test_option_question_cap.py` (9 tests): `..._off` (registered default off; with the option off a made-up option's five questions, one of them twice, are all put and the run succeeds), `..._empty` (on with nothing declared, and another option's data: nothing vetoed), `test_cap_*` (the run's counters, run-time data, a bad value is no cap, a vetoed `ask` / `ask_clarify` is not put), `test_no_repeat_*`, and two loop..final tests through the real AssistLoop with made-up asking options registered in a test registry: one option stops at the cap and the robot puts the object at its goal; two options share one cap and one record (the regression shape of the class: off, five questions with one repeat; on, three distinct questions) and the run succeeds. Bench: `tests/home/bench/test_d4_layers.py::test_question_cap_alone_on_top_of_d3_adds_its_option_no_repeat_and_its_assumed_cap_only`.

Limits: the asking option has already yielded its `clarify` event when the veto falls (the event log shows a question the person never heard; the robot's Ask skill is not called, so the bench's own question count is right); `ask_agree` appends the vetoed either-or with an empty answer to the run's dialogue (its own code, unchanged); the count uses the engine's refunds (`asked` is lowered when an answer restates the request), so the person may hear one question more than the cap; the engine's own questions are not vetoed (see Status), so a task can still hear more than 3 questions when the engine asks them; normalising by text means a question re-worded by another option is not a repeat.

## L22 partial_end (class goal_dropped, "done with an item unresolved"; PROPOSALS I14, user decision "end partial")

Status: PARTIAL - done: the option (status `partial`, the `done` event's field `partial` {done, missing} and the language pack's phrase `say_partial` when the goals hold while an open request item is missing; an item the end state satisfies is not missing; a complete success never changes), the engine service `open_items(run)` (collects the `ledger_open` answers, no option reads another's state), the phrase in the language packs (en new `speech` block, ko), its D1 layer (no overlay data), tests (hook level, a made-up language, the real loop's final state on and off), the offline replay gate below (one false success of the class turned into an honest partial end, no passing episode touched); missing: open items of the engine's own paths are not served to `open_items` (a `request_coverage` part the person did not answer or that could not become a goal still ends done: that path is in `assist_loop.py`, at its size limit, and is not an option), the Korean sentence on the bench (no KO episode of d3dev fires; the unit test renders a made-up language from the robot's phrases, a Korean read-back phrase missing in the robot's i18n would send the sentence to the translator), the paired P50 / DEV measure.
Overlaps: `hazard` (same hook `on_goals_met`, the same kind of end sentence, "I did the rest, but I won't ..."): its sentence is about parts the safety rules refused, it keeps status `success` so the bench passes the declared refusals on (`note_declared_refusals` only for a done run), and it is an always-on option (the safety gate); adding open items there would give the safety option a second responsibility and turn it on for every robot, so this is a separate option ordered after it (hazard answers first; a run with both a refused part and an open item keeps hazard's sentence, see Limits); `goal_ledger` (L18): the data source, reused through its service `ledger_open` (it says nothing at the end, so the two never both speak); `request_coverage` (engine path, not an option: one model call asks about request parts with no goal before the run claims done): same question "is part of the request not done", but it ASKS and adds a goal, this one REPORTS what is left; extending it means growing `assist_loop.py`; `end_state` and `unapplied_change` (`on_final`, an end event of their own): they act on, or report on, the goals the run checked, not on items outside them. Retired by this layer: none.

What (`robot_agent/options/partial_end.py`, 95 lines, hook `on_goals_met` at order 96; core: `LoopServices.open_items(run)` = `Dispatcher.collect("ledger_open", run)`, +4 lines in
`option_services.py`, +1 line in `core/options/services.py`; `assist_loop.py` unchanged): at the end of a run whose goals were seen to hold, the open items (today the `go` goals `goal_ledger`'s filter
predicate let the F4.4 drop take with no evidence) that the end state does not satisfy (not one of the run's goals, not a `go` place the robot stands at, not an object the run put at its
place) are missing. With one missing, the run ends with status `partial` (not `success`: the API's `ok` is false, the adapter maps it to `give_up`), `msg` `partial: <missing goals>`,
the field `partial` and the phrase `say_partial` with the slots `done` and `missing` (the goals' read-back phrases in a row, `sep_then`). The robot's i18n wins over the language pack; a
language with no phrase says the English one through the translator; no phrase in any pack, no open item, or no done goal = the run ends as before. The `done` event's status vocabulary gains
`partial` (described in `robot_agent/api/events.py`).

Why: the robot's own logs of the D3 arm on d3dev (`filtered`, the end event): a request ending "... then go back to the <dock place>" whose last words the recogniser cut lost its go goal to the
engine's F4.4 filter, the read-back never named it, and the run said done (false success). L18 restores the goal when a heard word starts with the place's name; with no such word the goal stays
dropped and is served by `ledger_open`; this layer makes the end honest for that rest. No simulator or person channel: it reads the engine's own drop record and the end state.

Data: the phrase only, `say_partial` in `robot_agent/core/planning/lang/en.json` (the `speech` block L19 added; L22 was built beside L19 and brought its own block, joined into one at the merge) and `ko.json` (its `speech` block, label extended), both `assumed: true`. D1 layer
`partial_end`: `{partial_end: 1}`, no overlay; the d3 alias keeps f751d734.... It needs `goal_ledger` on (the only server of `ledger_open`); alone on top of d3 it is silent by construction.

Tests: `robot_agent/tests/test_option_partial_end.py`, 8 tests on a made-up house (a nook in a den with the alias roost, a mat and a ledge in a hall), made-up objects (gizmo, sprocket), a
made-up language `zq` (robot phrases only): `test_registered_default_off_and_the_service_answers_nothing_off`, `test_no_open_item_no_done_goal_no_phrase_does_nothing_empty`,
`test_partial_an_open_go_item_turns_the_end_into_partial`, `test_named_in_a_made_up_language_the_robot_phrase_names_done_and_missing_items`,
`test_complete_success_unchanged_when_the_end_state_satisfies_the_item`, and through the real AssistLoop with a fake model:
`test_partial_loop_final_a_go_goal_dropped_with_no_evidence_ends_partial_and_names_it` (the regression of the class: off, the gizmo is placed, the robot is not in the nook and the run says
success; on, status `partial`, the say names the placed gizmo as done and the nook as not done, no raw key), `test_complete_loop_final_a_restored_go_goal_is_a_success_said_as_before` (the same
say on and off), `test_partial_loop_final_without_the_ledger_nothing_is_reported_open_and_the_end_is_unchanged`. robot_agent tests 2157 -> 2166 (+8, and the architecture test's entry for
the new option). Bench: `tests/home/bench/test_d4_layers.py` +1 (partial_end alone on top of d3: its option only, no data, the d3 hash unchanged); its build-order assertion now reads "D4_LAYERS
in BUILD order" instead of "a prefix of BUILD", because the layers are built in separate trees and L19 / L23 are not in this one (the iface checker still demands the full order).

Offline gate (no model): cache-only replays of all 150 d3dev tasks in the four cells with the D3 development caches, in a scratch directory, from this tree: arm `l18` = the 18 d3 layers +
goal_ledger (as in D1) and arm `l22` = `l18` + partial_end. The option acts after the last model call, so every changed outcome is determined (no cache miss).

| cell | success l18 / l22 | false success l18 / l22 | episodes where it acted | outcome flips | passing episodes changed |
|---|---|---|---|---|---|
| en ideal | 136 / 136 | 6 / 6 | 0 | none | none |
| ko ideal | 141 / 141 | 5 / 5 | 0 | none | none |
| en real | 89 / 89 | 9 / 8 | 1: the cut sentence of the class ("... head back to your"), done -> partial, "Done: put the gray towel in the bathroom cabinet, then hand you the red snack bag. Not done: go to the main room charging dock." | FS -> not FS | none |
| ko real | 85 / 85 | 14 / 14 | 0 (the three dock slips are restored by L18; the other no-evidence drops end failed for other reasons or end at the place) | none | none |

Limits: it fires only where an option reports an open item (today one go-goal drop rule), so it may fire in fewer than three episodes and be retired (it stays as the honest end of L18's rest:
a safety-of-claim reason, no success lost on d3dev); a go goal the reader INVENTED and the filter dropped would now end `partial` (a false partial; none seen on d3dev); a run with a
safety-refused part and an open item keeps hazard's sentence and status `success`; the satisfied check is by the belief (`world.arrived`, `placed`), not by a new look.

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

## L24 close_opened (class container left open, e.g. a hand goal whose Close could not run while holding; user decision of BRIEF section 5)

Status: PARTIAL - done: the option (a hand-full Close of a container the plan opened goes after the release, a Close the plan left out is added, before the robot's next leg; an `open` goal keeps it open), its D1 layer (no data of its own), tests (hook level, the real loop's final state with a hand-over), the offline gate below (the evidence task flips to success, no determined flip of a passing episode); missing: a container opened BEFORE the plan the hook sees (a replan's suffix after the Open ran, or one opened by an earlier part of the run) is not closed, the outcome of three passing episodes whose replay now misses the cache (en ideal 129, ko ideal 129 and 143), the paired P50 / DEV measure.
Overlaps: `plan_repair.op_hoist` (engine, the gate's operator; same question "a Close with the hand full", same action-model code `hand_full`): it moves such a Close after the next release in the plan it edits (the planner's blocks), so it cannot see a release an option added (L17's class) and never adds a Close the plan left out; extending it would change the default path (golden), and a new behaviour must be a default-off option; a retire candidate for its Close half once this layer is measured. `plan_release` (same hook `on_plan`, a Close while holding): it puts the held object's own put-in before the Close of its `in` place, another question with other data (`achieves: in`), and its replay is its own one-hand replay of declared releases; this option replays with the engine's action model (as `repair_sync` and `replan_guard` do) and reads no `plan_release` data. `plan_complete` (`on_plan`, its `_release` Close / Open splice for an `in` goal) and `precond_repair` add missing releases, not Closes. `gate_prune` (`on_plan`, same roles data): it drops an Open / Close of what cannot be opened, the opposite question. `reopen_on_miss` (`on_step_failed`, the pack's [Close, Open] remedy after a Find miss): same pair of skills at run time, not read here. `plan_tidy.closes_only` (engine) already treats "closing what the plan opened" as the expected tail after the goals (F0.4): the option relies on it, so the gate keeps the added tail. `end_state` (`on_final`): the Close goes before the plan's own later steps, so the dock still comes last. The four-line replay (`replay`) repeats the pattern of `plan_repair._Ctx.sim` (private); a merge candidate: one engine helper "states along a plan" for `repair_sync`, `replan_guard` and this option. Retired by this layer: none.

What (`robot_agent/options/close_opened.py`, hooks `on_start` and `on_plan` at order 89, after `precond_repair` 85, `plan_complete` 86, `plan_release` 87, so the release they add is
seen): the grounded plan is replayed on the belief with the engine's action model and the robot's capabilities. For every container an Open step of the plan opens (the pack's `open` role;
not one open before the plan) that the replay leaves open and that no `open` goal names (by its ENV key or its name): a Close of it the model refuses with `hand_full` (one hand) is taken
out, and `MoveTo C` (when the robot is elsewhere) and `Close C` go in at the first point after the robot's last step at C where the hand is empty and the robot is between two legs (before
its next MoveTo, or at the plan's end), so every later step keeps its place. A plan whose hand never empties there is left alone (no guess). Lab flag `close_opened` `{container, fix}`
(`moved`, `added`), once per distinct edit in a run (the hook also runs inside the gate's score of every candidate).

Why: the robot's own logs of the D3 arm on d3dev (gate findings, plans in the prompt cache; no simulator channel) show a hand goal's plan "MoveTo C, Open C, Find X, Pick X, Close C" with
the hand-over added after it by `precond_repair` / `plan_complete`; the Close cannot run with the one hand full, the gate says "do it before the Pick" (impossible: X is inside) and the run
gave up (KO real 040 in D3), or the planner drops the Close and the robot ends with C open. The user decided (BRIEF section 5): close what was opened unless the goal says otherwise. 0 extra
model calls.

Data: none of its own. It reads the `open` / `close` / `move` roles of `planner.action_roles` (in D1: the variant's `ACTION_ROLES_OVERLAY` and the d3 layers `gate_prune`, `cond_extract`,
`plan_complete`, all `assumed`: the mock robot's own action names) and the hand count from the manifest's `capabilities` (one hand: `arms: 1`, `hands: [right]`). D1 layer `close_opened`:
`{close_opened: 1}`, no overlay; the d3 alias keeps f751d734.... Empty: no `open` / `close` role, roles naming actions the action model does not know, or no plan = unchanged (`*_empty`
test); no `move` role = a Close only where the robot already is; two hands = a Close while holding is fine and nothing moves.

Tests: `robot_agent/tests/test_option_close_opened.py`, 13 tests on made-up places (crate, hutch, bench, a person pal), objects (gizmo, widget, bolt) and a made-up hand-over action (Offer):
`test_registered_and_off_by_default_the_locker_is_left_open_off` (the real loop, option off: the gizmo is handed over and the locker stays open, the class),
`test_no_roles_foreign_roles_or_no_plan_do_nothing_empty`, `test_loop_final_the_locker_is_closed_after_the_hand_over` (the real AssistLoop with FakeLLM and a hand-over pack: FINAL state
gizmo with the person, hand empty, locker closed, run `success`, the last skills hand-over, move, close), `test_loop_final_a_goal_to_leave_the_locker_open_is_kept`, the class regression
(`test_close_added_regression_...`: a plan with no Close gets one after the release and before the next leg; a second pass changes nothing), the hand-full Close moved after the hand-over, a
Close right where the robot is after a put-in, the next-leg rule (`test_close_waits_for_the_next_leg_...`: the shape the offline gate found, every step of the result checked by the action
model), an `open` goal by key or name, a container closed already or open before the plan, no release after a hand-full Close, two hands, no move role, one lab event per edit. robot_agent
tests 2157 -> 2171 collected (+13, and the architecture test's entry for the new option). Bench: `tests/home/bench/test_d4_layers.py` +1 (close_opened alone on top of d3: its option only, no
data, the roles it reads declared, the d3 hash unchanged); the build-order assertion now asks the layers built so far to follow BUILD's order (layers are built in parallel worktrees; the
merged tree and the checker's iface part still ask for the whole order).

Offline gate (no model): cache-only replays of all 150 d3dev tasks in the four cells with the D3 development caches, arm `d3` and arm `d3` + `close_opened`, in a scratch directory. The `d3`
replay reproduces the recorded D3 success and false success of every cell (136 / 141 / 89 / 85; 6 / 5 / 9 / 15). A first version put the Close right after the release; the replay showed a
passing two-container plan (en ideal) turned into a gate give-up (the plan's own Close of the second container then ran away from it): fixed by the next-leg rule (test above) before these
numbers.

| cell | success d3 / +L24 | false success d3 / +L24 | episodes where it fired (passing in d3) | determined flips | now a cache miss |
|---|---|---|---|---|---|
| en ideal | 136 / 135 | 6 / 5 | 35 (28) | none | a pass (129), a false success (110) |
| ko ideal | 141 / 139 | 5 / 4 | 39 (34) | none | two passes (129, 143), a false success (110) |
| en real | 89 / 89 | 9 / 10 | 33 (14) | give-up -> false success (106: the gate had refused the plan; with the Close moved it certifies, and the plan hands the keys to the wrong person, a reader / planner error the give-up hid) | none |
| ko real | 85 / 86 | 15 / 15 | 37 (17) | give-up -> success (040, the evidence task: the Close moved after the hand-over, the gate certifies) | none |

It fires often (33 to 39 of 150 per cell): most plans that open a container to take something out never close it. Every passing episode it fired on and whose replay stays in the cache
keeps its outcome (90 of the 93 passing episodes it fired on; the other three miss the cache). The three passing episodes that now miss the cache (a container closed during a search leg changes the next replan prompt) and the two false successes that
miss cannot be judged offline. Judge the layer on the paired pilot: the one determined false-success rise (106) is a wrong-recipient plan the gate's give-up had hidden, not a step this option
wrote, but it counts.

Limits: a container opened before the plan the hook sees (a replan's suffix after the Open ran, one opened by an earlier part of the run) is not closed: the gate calls a Close of such a
container "no goal needs it; remove it" (critical), so the option leaves it; each added Close costs a MoveTo and a Close (sim time, one more skill that can fail in the real profile; a failed
Close goes through the normal recovery); the added Close is written only when the next step is a MoveTo or the plan ends, so a plan that ends at the person after the hand-over leaves the robot
at the container (the gate keeps that tail as `closes_only`); an `open` goal is the only "goal says otherwise" (a request worded otherwise, e.g. a fridge to air, is the reader's).

## L20 fault_ladder (classes hw_persistent, camera_persistent; PROPOSALS P4, cut down by the red team)

Status: PARTIAL - done: the engine hook `on_fault_stop` (the recovery policy's two stops share one tail that asks it first; no option = the same `done` event, golden green, `assist_loop.py` keeps its size), the option (after `hw_wait`'s wait and tries: one help question per run naming the device, one retry per run by a declared other skill only while health reads `ok` True and a hand step's sensor agrees with the belief, then a failed stop whose sentence names the device, the attempts and the steps done), the phrases `q_fault_help` / `say_fault_stop` (en, ko, assumed), its D1 layer (the mock robot's devices, sourced from its manifest, the pairing assumed; no alternative skill), 15 tests; missing: any measured effect (the cache-only replay cannot run it: the simulated person's answer to the new question is an uncached model call, see below; it needs the GPU pilot), the retry part on the bench (the mock robot declares no other skill, so it is inert there by design), whether the mock adapter fills `SkillResult.device` (if it does, its raw id is said instead of the declared name), the robot-side traces of the fault episodes (which stop branch ends each hw_persistent row), pick_faults and blocked_person (not targets: the engine's own pick help and `_recover_move` already ask there; one failure must not get two help questions), the paired P50 / DEV measure with help / help_correct and the time to stop reported apart from success.
Overlaps: `hw_wait` (same failure kinds, same point of the run: its services `recovery_rule` / `wait_schedule` / `more_tries` are asked by `_apply_policy` just before the stop; same data a wait cap and tries would be): it OWNS the growing wait, the cap and the tries (D1: schedule [2, 4, 8], tries 2 / 3, assumed; the D3 layer `hw_tries` is its key `more_tries`); this option has no wait or tries key and acts only once they are used up (the new hook fires at the stop, after hw_wait's answers), so the data is not duplicated. Not a key of hw_wait: hw_wait answers queries (no flow hook, it cannot ask or end the run) and the frozen interface names a registered option `fault_ladder`; one responsibility each (hw_wait: when to stop; fault_ladder: what to do at the stop). Taking hw faults at `on_step_failed` (before the policy) was rejected: it would take over from hw_wait and silence it. The engine's own pick help (`_recover_pick`, `pick_retries`) and move help (`_recover_move`, BLOCKED) ask for help on other codes: left alone, so no failure gets two help questions. `question_cap` (L23): the help question goes through the engine service `ask`, so the cap counts and may veto it (then no question, the stop sentence still comes). `effect_check` (L16, `on_step_failed` order 88, a failed release reads the hand sensor): runs first; this option reads the same engine service `hand_holds` only for its retry gate, no shared state. `partial_end` (L22, `on_goals_met`): never on the same run end (a fault stop is `failed`, the goals did not hold). Retired by this layer: none (the engine's fixed "something is wrong with my hardware" sentence stays the default path).

What (`robot_agent/options/fault_ladder.py`, 174 lines, hooks `on_start` and `on_fault_stop` at order 91; core: the hook in `core/options/spec.py` +1 line, `_apply_policy` rewritten in place with one stop tail, `assist_loop.py` 4210 lines by lint_arch as before): for `hw_fault` and `perception_unavailable` only (a rule with `retry_allowed` false, e-stop, cancel, software, never reaches the hook). (1) The device: the one the skill result reported (its declared name, else as reported), else the declared device of the failed skill; none = no question and the engine's stop. One question per run (`q_fault_help`, engine service `ask`, counted in `run.asked`; an "I don't know" answer is recorded, the question is never repeated). (2) One retry per run: the failed step keeps its action and gets the declared other skill (a concrete `skill` step in its place), only when the robot's health reads `ok` True now and, for a hand step (a skill whose declared pre / effects name `holding(` or `hand_empty`; an undeclared skill counts as one), the holding sensor gives a reading that agrees with the belief. (3) The stop: status `failed`, the deciding code and device, `say_fault_stop` with `device`, `tries` (the policy's count of that failure on that step, the retry included) and `done` (the steps done); the `msg` names the code, the device and the counts, never the health reading. Health is read only as the contract's `ok` field; any other value, a missing field or a failed read is unhealthy; no other field of the reading is read or said. Lab flag `fault_ladder` `{part: ask | alternative | stop}`.

Why: in the D3 arm on d3dev, the fault-class rows (hw_persistent 10, camera_persistent 2; the backlog after D3) end failed at the recovery policy's stop after the wait: either the unhealthy-robot stop, which says only "I have to stop: something is wrong with my hardware.", or the stop after the tries, which says the step's failure; neither asks for help or names the device, the attempts and what was done. Which branch ends each row is not confirmed (the episodes hold no robot-side event trace). A bounded wait, one help request, one alternative and an honest stop are generic robot policy; nothing of the simulator's fault schedule is read (the health value's per-device text is never parsed; the never_suffix test). All fault-class rows already have no false success, so the layer cannot lower false success; success is plausibly unchanged (the red team counted 24 of 29 help questions of D3 answered "not sure"); its effect shows in the judge's help fields, which are judge fields: the question wording was NOT tuned against them. The stay gate's reason, if it fires without a paired gain: an honest bounded stop (a safety-of-claim reason).

Data (D1 layer `fault_ladder`: `{fault_ladder: 1}` and `planner.options.fault_ladder.devices = FAULT_DEVICES`, `bench/suites/home/planners/d1_options.py`): the devices named by the mock robot manifest (`symbolic_robot/domains/home/configs/manifest.yaml`: description "one arm and gripper, a camera, a speaker and a microphone", `capabilities base: true`, the skill descriptions of look / vlm_check and grasp_check), `source` that file, `assumed: true` for the pairing of each skill with one device (move, dock: drive base; find, look, vlm_check: camera; pick, place, put_in, open, close, handover: arm; grasp_check: gripper sensor; say, announce: speaker; ask: microphone), English and Korean names. No `alternatives`: the manifest declares no second skill for any step, so none is made up. The phrases are the language packs' (`robot_agent/core/planning/lang/en.json`, `ko.json`, block `speech`, `assumed`). The `hw_wait` / `hw_tries` layers keep the wait and the tries. The d3 alias keeps f751d734....

Tests: `robot_agent/tests/test_option_fault_ladder.py`, 15 tests on made-up devices ("eye unit", "grip pad"), a made-up other skill `scan` and made-up per-device health texts: `test_registered_default_off_and_the_engine_stop_stands_off`, `test_an_empty_or_unlabelled_pack_does_nothing_empty`, through the real AssistLoop with a fake model: `test_loop_unhealthy_robot_final_failed_one_question_naming_the_device` (the regression of the class: failed, exactly one question, the stop names the device, the apple unmoved), `test_loop_help_yes_health_ok_and_a_declared_alternative_final_success_goal_held`, `test_alternative_only_when_health_reads_ok_true_and_none_declared_is_no_retry`, `test_ask_once_an_unsure_answer_is_not_asked_again`, `test_ask_once_capped_by_question_cap_no_question_the_stop_message_still_comes`, `test_stop_message_names_device_tries_and_steps_done_no_health_text_no_env_key`, `test_never_suffix_two_health_values_differing_only_in_a_made_up_suffix_give_the_same_run`, `test_rules_without_retry_are_never_laddered`, `test_hw_wait_tries_come_first_the_ladder_acts_when_they_are_used_up`, `test_partial_end_and_effect_check_on_the_fault_stop_is_failed_with_the_ladder_sentence`; pure: the hand-step gate of the retry, the sentence rendered in Korean, the data readers. robot_agent tests 2222 -> 2238 passed (+15, and the architecture test's entry for the new option). Bench: `tests/home/bench/test_d4_layers.py` +1 (fault_ladder alone on top of d3: its option and the labelled devices of the robot's own skills only, no alternative, hw_wait's wait and tries still on, the d3 hash unchanged).

Offline replay: not possible for this layer. The cache-only replay of d3dev (arm d3 + fault_ladder, en real and ko real, D3 development caches copied to a scratch directory) stops with `CacheMiss` in the simulated person's answer reader (`user_intent`): the new help question is a prompt the D3 caches never saw, and a miss there ends the whole replay, not one episode. This shows the option fires in the real cells (the only new prompt of the arm), and nothing more. The `d3` arm replayed from this tree (the refactor of `_apply_policy` with no option on the hook) reproduces the recorded D3 episodes exactly in en real and ko real: 150 of 150 each with the same skill calls (skill, ok, code, arguments), success, false success and questions (89 / 9 and 85 / 15). By construction, with the D1 data (no alternative skill) the option cannot change an episode's success or false success: it acts only where the engine ends the run failed, and the run then ends failed; what it changes is one more question to the person, the end sentence and the time to stop, which the pilot must report apart from success (help / help_correct are judge fields: the wording was not tuned on them).

Limits: the retry needs a declared other skill and a robot whose health reads `ok` True after the help; with the mock robot (no other skill) the ladder is one question and an honest stop; a reported device id that the pack does not name is said as reported (underscores as spaces), in English in a Korean sentence; the attempts are the policy's count for that step and kind, not every fault of the run; the engine's own silence handling may say the question once more ("Sorry, I didn't hear you") inside the one `ask`; the question is asked even when the person cannot reach the device (the answer is not parsed: only the robot's own health decides the retry).

## Complexity budget

Measured on robot_agent at base 64c7e72 (before S0), after S0, and after each D4 layer. Option lines: `robot_agent/options/*.py` without `__init__.py`.

Layers on: 28 (`all` = the 18 D3 layers + L15 plan_release + L16 effect_check + L17 repair_sync + L18 goal_ledger + L19 answer_align + L23 question_cap + L22 partial_end + L21 safety_profile + L20 fault_ladder + L24 close_opened; the `d3` alias keeps 18; the layers' loop options grow by eleven keys, `plan_release`, `effect_check`, `repair_sync`, `goal_ledger`, `answer_align`, `question_cap`, `question_cap_no_repeat`, `partial_end`, `safety_profile`, `fault_ladder`, `close_opened`)
Option lines: 4559 in 38 modules (L20 fault_ladder +174, core: hook on_fault_stop in core/options/spec.py +1, assist_loop.py 0 (_apply_policy rewritten in place with one stop tail), lang/en.json +2 and ko.json +2 (phrases q_fault_help, say_fault_stop); after L24 4385 in 37; L24 close_opened +101, no core change; after L21 4284 in 36; L21 safety_profile +65, hazard +4 (verdict asks safety_rule); after L22 4215 in 35; L22 partial_end +95; after L23 4120 in 34; L23 question_cap +77; after L19 4043 in 33; L19 answer_align +176, ask_agree +47 (key distinct); after L18 3820 in 32; L18 goal_ledger +161; after L17 3659 in 31; L17 repair_sync +134; after L16 3525 in 30; L16 effect_check +138; after L15 3387 in 29; after S0 3190 in 28; L15 plan_release +197; before S0 3174: hazard +2, dedupe_keep_end +6, lang_words +2, precond_repair +6, hw_wait 0). Core: plan_repair.py +9 (S0), assist_loop.py 0 (L16: one line rewritten in place; L17: two lines rewritten in place), option_services.py +19 and core/options/services.py +2 (L16: services hand_holds, let_go), plan_repair.py +21 (L17: arguments sync / finish_rest, the edit loop as the helper _edits), goal_fix.py +1 and assist_loop.py 0 (L18: argument keep_go of drop_invented, one call line rewritten in place), names.py +75 and the language packs en.json +5, ko.json +1 (L19: the readings' words, phrase q_pick_one), assist_loop.py 0 (L19), option_services.py +14 and assist_loop.py 0 (L23: service ask_veto asked first by the engine services ask and ask_clarify), option_services.py +4 and core/options/services.py +1 (L22: engine service open_items), lang/en.json +1 (L22: phrase say_partial, in the speech block L19 added) and ko.json +1, assist_loop.py 0 (L22), core/safety/profile.py +10, place_class.py +30, hazards.py +8, option_services.py +4, core/options/services.py +1 (L21: rule key within_m, near_class, service safety_rule)
Hooks: 65 hooks and 28 services over 38 registered options, 26 hook kinds (L20 +2 hooks: fault_ladder on_start, on_fault_stop, no service, +1 NEW hook kind on_fault_stop (decide, flow: the recovery policy's stop); after L24 63 and 28; L24 +2 hooks: close_opened on_start, on_plan, no service, no new hook kind; after L21 61 and 28; L21 +1 hook: safety_profile on_start, +1 service safety_rule, no new hook kind; after L22 60 and 27; L22 +1 hook: partial_end on_goals_met, no option service, +1 engine service open_items, no new hook kind; after L23 59 and 27; L23 +1 hook: question_cap on_start, +1 service ask_veto, no new hook kind; after L19 58 and 26; L19 +3 hooks: answer_align on_heard, on_goals, on_issues, no service, no new hook kind; after L18 55 and 26; L18 +1 hook: goal_ledger on_issues, +2 services goal_keep, ledger_open, no new hook kind; after L17 54 and 24; L17 +1 hook: repair_sync on_replan_findings, +1 service repair_kwargs, no new hook kind; after L16 53 and 23; L16 +3 hooks: effect_check on_start, on_step_failed, on_goal_check, +1 service hand_reading, no new hook kind; after L15 50 and 22; after S0 48 and 22; L15 +2: plan_release on_start, on_plan)
Retired: none yet (the retire decision needs the paired D4 measure. Candidates named: release_near and hw_tries as separate layer entries, plan_complete into precond_repair, ask_focus.unrefused, plan_complete._release once L15 is measured; the literal Place / PutIn empty-hand path of the engine and its floor head, once effect_check is measured; L15 plan_release's Close splice partly overlaps what repair_sync's second try now finds (a release an option added before a hand-full Close), to be judged on the paired measure; goal_ledger's `goal_keep` and goal_words' `goal_guard` are two answers at the same drop site, a merge candidate after the measure; goal_ledger's `named` and `retract` keys are off in D1 and retire with the layer if they stay unmeasured; ask_agree's whole-phrase `said()` once `distinct` is measured, and `distinct` itself if it stays off; `dialog_agree.names_option` and the engine's correction edit onto `names.distinguishing` / `which_named`; three readers of `grammar.speaker_forms` into one core function; L23 question_cap retires none, candidate after the measure: `ask_focus.max_confirms` if the cap also gates read-backs one day; L22 partial_end retires none; safety_profile once a robot's own safety.profile file carries within_m rules (hazard then reads them directly); the Close half of the gate's `op_hoist` once close_opened is measured; L20 fault_ladder retires none: hw_wait keeps the wait and the tries, the ladder only acts at the stop)
