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

## Complexity budget

Measured on robot_agent at base 64c7e72 (before S0), after S0, and after each D4 layer. Option lines: `robot_agent/options/*.py` without `__init__.py`.

Layers on: 19 (`all` = the 18 D3 layers + L15 plan_release; the `d3` alias keeps 18; the layers' loop options grow by one key, `plan_release`)
Option lines: 3387 in 29 modules (after S0 3190 in 28; L15 plan_release +197; before S0 3174: hazard +2, dedupe_keep_end +6, lang_words +2, precond_repair +6, hw_wait 0). Core: plan_repair.py +9 (S0), assist_loop.py 0
Hooks: 50 hooks and 22 services over 29 registered options (after S0 48 and 22; L15 +2: plan_release on_start, on_plan; no service, no new hook kind)
Retired: none yet (the retire decision needs the paired D4 measure. Candidates named: release_near and hw_tries as separate layer entries, plan_complete into precond_repair, ask_focus.unrefused, plan_complete._release once L15 is measured)
