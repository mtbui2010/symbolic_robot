# D4 layers (robot_agent options for the D1 planner, second round)

Round D4 adds layers on top of the 18 D3 layers (`HOMELOOP_D1_LAYERS`, `bench/suites/home/planners/d1_options.py`). Every layer is a robot_agent
option, default off, with its data declared in the D1 overlay (labelled `source` or `assumed: true`). Development set: d3dev (optimistic: D3 was
tuned on it). This file holds one section per kept layer (`## Lk ...`), the seven deleted layers in `## Removed` and the complexity budget of the round.

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
covered at plan level by (b); one KO task is a reader error (its `in` goal read as `on`) and another KO task a hand goal: not this class. Expected gain (red team, rechecked): about +3 to 4 rows of 600 on
d3dev, about half on d4fresh, inside the noise of one run; judge the layer on "no harm" (no false-success rise), not on P50 McNemar.

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

Status: PARTIAL - done: the option (R1 `restore`: a go goal the F4.4 filter would drop is kept at the drop site when a heard word starts with a name of its place, and its unsaid issue and the heard word's object issue are settled; `named`: kept with no evidence and named by the engine's read-back; R4 `retract`: the engine's where-issue for a destination named only before a self-correction marker), the engine seam (service `goal_keep`, argument `keep_go` of `goal_fix.drop_invented`), its D1 layer (restore only), the open items for `partial_end` (`ledger_open`: since the review fix of round 1 only a drop with a weak cue of its place, a heard word with the name and a tail too long to restore, or the words ending in the name's last word cut short; a drop with no sign at all is the reader's own goal), `retract_markers` used only with its `source` / `assumed` label (review fix), tests (pure, hook level and the real loop's final state, among them the safety gate, cond_goal, a re-sample and a correction), the offline replay gate below (named turned off by it); missing: any measured flip (every changed episode misses the prompt cache at its next model call; it needs the GPU pilot), R4's firing on passing episodes (R4 stays off in D1; its two d3dev targets are below the three-task rule), the R2 shadow (not built: no registry-level shadow mechanism exists, the R2 firing rate can be counted offline from the caches; a general `shadow` key is a registry change of its own), L22 partial_end reading `ledger_open` (L22 is not built), L23 question_cap counting the R4 question (L23 is not built; the question goes through the engine's ask path), the paired P50 / DEV measure.
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

Status: PARTIAL - done: the core helpers (`names.reading_words`, `distinguishing`, `says`, `which_named`, `endings`, `speaker_words`), the option (`reask`: a yes or no to an either-or asked once more naming the options; `correction`: a correction that names one object leaves the other goals' earlier destination and source, with its `unsaid` issue settled so the read-back's re-sample keeps it), the key `distinct` of `ask_agree` (the read-back's either-or by distinguishing words; an object changed with its own `from` and words is one change), the phrase `q_pick_one` in the English and Korean packs (assumed), its D1 layer (reask and correction on, `ask_agree.distinct` off), a re-ask the question cap vetoes is neither announced nor logged as asked and its bare yes / no is taken back unresolved (engine service `drop_last_answer`; review fix of round 1: before it the reader picked a reading from the bare yes), tests (pure, hook level and the real loop's final state for reask and correction), the offline replay gate below; missing: any measured flip (every episode where it acted misses the prompt cache at its next model call; it needs the GPU pilot), `ask_agree.distinct` in D1 (the gate fired it on one passing and one failing episode of the same request: off by the red team's kill ratio until a pilot), the ask_loop rows that distinguishing words cannot reach (a Korean answer whose only word both readings share; the earlier reading is not the one the person meant; the ASR- and dialogue-specific rows), the correction target the gate did not fire on, a shadow mode (no registry-level shadow mechanism exists), L23 question_cap counting the re-ask (L23 not built; the re-ask goes through the engine's `ask_clarify`, so an engine count sees it), the paired P50 / DEV measure.
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

## drop_search and drop_search_goal (selectable layers, not in `all`; classes K4, K6, S2 of the D4 failure analysis)

Status: SELECTABLE, NOT MEASURED - done: robot_agent option `drop_search` (default off, merged 2026-11-16 with the table-driven recovery ladder), D1 entries `drop_search` and `drop_search_goal` (key `goal_check`), tests; missing: any paired measure (the replan after `goal_check` is a model call, so a cache-only replay cannot score it), so neither is in `all`.
Overlaps: the engine's DROPPED rule (`_refind_dropped`: only the room the robot stands in, only for code `dropped`) and the deleted L16 `effect_check` (91bbced: the same hand-sensor read, current room only, 0 of 600 changed); `drop_search` reuses the engine's REFIND rung (service `refind_on`) instead of a second search. Retired by it: none (candidate: the DROPPED rule's room choice, once measured).
What (`robot_agent/options/drop_search.py`, hooks `on_step_failed`, `on_goal_missed`; engine services `hand_sensor`, `let_go`, `refind_on`): a failed hand-over while the belief holds an object and the hand sensor READS empty (a sensor call failed for a device reason is no reading): the belief lets go and the REFIND rung looks on the floor places of the person's room, then the rooms passed since the Pick, then the Pick's place, once per object; key `goal_check`: an object this run put at its goal place that the end check misses gets one look at that room's floor, and the replan reason names the goal and the floor.
Why: a hand-over that failed with an empty hand was repeated as is until "the same failure thrice", and an object lost after a release was never looked for on a floor (the engine's REFIND knows only the room of the place it stands at).
Data: `planner.options.drop_search.floors` `{head, source | assumed}`, the head of the map's floor places; the D1 overlay declares `head: floor`, `assumed: true` (the robot's ENV lists a `floor@<room>` place per room, brief section 5); `drop_search_goal` also declares the pack's `move` role. None or no label: nothing.
Tests: `robot_agent/tests/test_option_drop_search.py` (8: `_off`, `_empty`, sensor reading, floor order, two loop-final tests on a made-up house); the ladder: `tests/test_step_ladder.py` (7). Bench: `tests/home/bench/test_d4_layers.py` +1 (both selectable only, labelled, all / d3 / d2 hashes unchanged).
Ladder (same merge, no new layer): the Pick / MoveTo / release recovery ladders read the declared table (`contract.recovery`, mixin `core/planning/step_ladder.py`); a cache-only replay of d3dev, arm `all`, four cells, was identical in 600 of 600 episodes, 0 misses, before and after (re-proved on the merged trees).
Limits: the floor-place head is assumed, not read from the map's schema; a hand sensor that only reports through the Pick check reads nothing elsewhere; one look per object.

## Removed

Decided by the stay gate on d3dev (`d4_measure.md` section 1: 150 tasks x EN/KO x real/ideal = 600 episodes per arm, seed 0, shared prompt cache; optimistic, the layers
were developed on it). A layer stays in `all` only with a paired gain above zero that fired in at least 3 episodes, or a written safety reason. The seven layers below were
retired from `all` on 2026-11-15 (symbolic_robot 3c7d671) and DELETED the same day, with the user's approval: their robot_agent options, tests, language-pack data and the
engine support only they used (hook `on_fault_stop`, services `ask_veto`, `questions_put`, `drop_last_answer`, `hand_reading`, `hand_holds`, `let_go`, `open_items`,
`safety_rule`, goal_ledger's `ledger_open`, the profile key `within_m`), their D1 entries (`LAYERS`, the overlay data `FIRE_CLEARANCE`, `FAULT_DEVICES`) and their bench tests.
Their sections (what, why, tests, offline gates, limits) are in this file's git history (symbolic_robot efdd8d8); each option's code is in robot_agent git history (commit below).
`all` is unchanged by the deletion (its hash, the same as `d3` + the four kept layers by name, is pinned in `test_d4_layers.py`); `d3` and `d2` keep f751d734..., 64b278b5....

| layer | option (robot_agent commit) | class | reason (d3dev, paired with D3) | offline gate before the measure (d3dev, cache-only, four cells) |
|---|---|---|---|---|
| L16 | `effect_check` (91bbced) | drop_recovery, grasp_misread, silent_drop | no outcome changed (alone: 451 = D3, 0 won / 0 lost) | success and false success equal to D3 in every cell (136 / 141 / 89 / 85; 6 / 5 / 9 / 15), no passing episode changed |
| L20 | `fault_ladder` (0e4a112) | hw_persistent, camera_persistent | no outcome changed (group C with safety_profile: 0 / 0) | not possible (its help question misses the D3 caches in the person's answer reader) |
| L21 | `safety_profile` (e329a71) | hazard_unrefused, hazard_missed (one family) | no outcome changed (group C: 0 / 0); the mock robot declares no fire-clearance data of its own, the profile came only from the D1 overlay | profile in force in 150 episodes per cell, a rule fired in 0, no outcome changed |
| L22 | `partial_end` (ac322b9) | goal_dropped ("done with an item unresolved") | no outcome changed (`d4_measure.md` section 1; group B won 2 / lost 0, and the kept arm, without this layer, has the same two more wins over plan_release + effect_check + repair_sync) | acted in 1 episode (en real: false success 9 -> 8), no passing episode changed |
| L23 | `question_cap` (2ab4c9c) | the robot keeps asking | no outcome changed (same evidence as L22) | (D3 rows, real profile: 49 of 300 episodes put more than 3 questions, 18 of them succeeded) |
| L24 | `close_opened` (9fa2ecc) | container left open | harmful: lost 3 tasks (three `conjunction` tasks that close a drawer: give up / budget), won 0 | fired in 33 to 39 of 150 per cell; success 136 / 135, 141 / 139, 89 / 89, 85 / 86; false success 6 / 5, 5 / 4, 9 / 10, 15 / 15 |
| L25 | `else_ask` (47eeb14) | conditional (else clause served by no goal) | no outcome changed (same evidence as L22) | an estimate from the texts and the D3 lab events, not a replay (one task of eight would ask) |

Kept in `all` (in the build order): L15 `plan_release`, L17 `repair_sync`, L18 `goal_ledger`, L19 `answer_align`. On d3dev the kept arm had 459 of 600 (D3 451),
false success 32 (D3 35), 11 won / 3 lost, p 0.057; it was chosen on those same episodes, so that gain is optimistic. The sealed measure on d4fresh (once, aggregates only,
design committed before it in `d4_measure.md`) confirmed it: D3 + the four kept layers against D3, success 0.702 -> 0.722 over 600 episodes, 12 tasks won and 0 lost,
McNemar exact p 0.0005 (the two arms share one prompt cache, so they are not two independent runs), false success 32 -> 31. `all` is exactly that measured arm
(`test_all_is_the_arm_the_sealed_measure_ran_d3_plus_the_kept_layers_by_name`).

## Complexity budget

2026-11-16, after the merge of par/ladder (robot_agent b414b36 and the fix ddb4f08, symbolic_robot b8b6e31; `budget.py all` and `budget.py drop_search_goal`): under `all` nothing
changed (22 layers, 41 loop keys, 29 options on in 29 modules, 3680 option lines, 51 hooks, 24 services; hashes all 78f601bf, d3 f751d734, d2 64b278b5 unchanged).
In the tree: 36 modules, 4556 option lines, 63 hooks, 24 option services, 29 hook kinds over 36 registered options (before: 35 / 4429 / 61 / 24 / 28; drop_search
+127 lines, 2 hooks `on_step_failed`, `on_goal_missed`; new hook kind `on_goal_missed`). Engine services +3 (`hand_sensor`, `let_go`, `refind_on`; option_services.py
280 -> 301, core/options/services.py 38 -> 41); assist_loop.py 4209 -> 4083 (the Pick / MoveTo / release ladders moved to the new step_ladder.py, 174 lines, read from
the declared table; its two help sentences in speech.py, +3, where the sim's question-parser test anchors on them); engine and contract +239 / -144 lines; arch wiring ratchet cfg_keys 65 -> 62, cfg_branches 64 -> 59. Retired: none new.

2026-11-16, after the merges of reach_check, trace and ask_next (robot_agent e9a99a9, recomputed with `budget.py all` and the method below): under `all` nothing
changed (22 layers, 41 loop keys, 29 options on in 29 modules, 3680 option lines, 51 hooks, 24 services; the three are selectable, not in `all`; hashes all 78f601bf,
d3 f751d734, d2 64b278b5 unchanged). In the tree: 35 modules, 4429 option lines, 61 hooks, 24 option services, 28 hook kinds over 35 registered options (before:
32 / 3930 / 55 / 24 / 25; reach_check +105 lines, 1 hook `on_step`; trace +206, 4 hooks `on_start`, `on_event`, `on_lab`, `on_step_failed`; ask_next +188, 1 hook
`on_ask_help`). New hook kinds: `on_event`, `on_lab`, `on_ask_help`. Engine services +4 (`llm_calls`, `retry_here`, `told_at`, `search_on`; option_services.py 245 -> 280);
engine (core and observe) +130 / -17 lines since 80e266c; assist_loop.py 4209 lines (the hook calls are rewrites in place). Retired: none new.

After the deletion (2026-11-15, recomputed from the tree with the method below, robot_agent e7caf61): the seven retired layers and the engine support only they
used are deleted (`## Removed`); `all` is the same arm as before the deletion (same hash).

Layers on: 22 under `all` (the 18 D3 layers + L15 plan_release, L17 repair_sync, L18 goal_ledger, L19 answer_align; loop option keys on 41, D3 37; registered
options on 29 of 32, D3 25).
Option lines: 3680 in the 29 modules on under `all` (D3 arm: 2987 in 25, hazard -4: its query of `safety_rule`; the kept four: plan_release 197, repair_sync 134,
goal_ledger 174 (-6: `ledger_open`), answer_align 188 (-10: its branch for a vetoed re-ask)). In the tree: 3930 in 32 modules (before the deletion 4744 in 39: -794 for
the seven modules, -20 above). Engine since the retire (robot_agent/core and api): +45 / -168 lines; option_services.py 308 -> 245 and core/options/services.py 44 -> 38,
both equal to base 64c7e72 again; core/safety and docs/safety.md back to 64c7e72 (no `within_m`); assist_loop.py 4209 lines, as before (the D4 lines there were rewrites in
place; `_apply_policy`, `_holding`, the ask counters are back to their base form, the kept `goal_keep`, `repair_kwargs` and `lab_log` lines stay); spec.py one hook kind
less; lang en.json and ko.json 5 lines less each. robot_agent in all: +100 / -2619 lines (options -836, tests -1507, engine -168, docs and CHANGELOG -108).
Hooks: 51 hooks and 24 services of the 29 options on under `all` (D3 arm: 44 and 22). In the tree: 55 hooks and 24 services over 32 registered options, 25 hook kinds
(before the deletion: 66, 28, 39, 26). Gone: the seven options' 11 hooks, the option services `hand_reading`, `ask_veto`, `safety_rule` and goal_ledger's `ledger_open`,
the hook kind `on_fault_stop`, the engine services `questions_put`, `drop_last_answer`, `hand_holds`, `let_go`, `open_items`, `safety_rule`.
Retired: 7, deleted on 2026-11-15 (section `## Removed`: effect_check, fault_ladder, safety_profile, partial_end, question_cap, close_opened, else_ask). Candidates
left (not done): goal_ledger's lab rule `open` (it marked partial_end's open items; now only a log line), and the candidates named in the record below that do not
involve a deleted layer.

Recorded before the deletion (as written after the retire, robot_agent 2b2ba67; each line marked with a dash):

Measured on robot_agent at base 64c7e72 (before S0), after S0, and after each D4 layer. Option lines: `robot_agent/options/*.py` without `__init__.py`.
After the retire (2026-11-15, recomputed from the tree, robot_agent 2b2ba67): the arm's loop options (`SageS8nFtD1Planner.loop_options`) and overlay are resolved
against the registry (`robot_agent.core.options.config.resolve`); an option counts as on when its `enabled` key resolves true (or it has none: `hazard`, always on).

- Layers on: 22 under `all` after the retire (the 18 D3 layers + L15 plan_release, L17 repair_sync, L18 goal_ledger, L19 answer_align; loop option keys on 41, D3 37;
registered options on 29 (D3 25), the seven retired off). Before the retire: 29 (`all` = the 18 D3 layers + L15 plan_release + L16 effect_check + L17 repair_sync + L18 goal_ledger + L19 answer_align + L23 question_cap + L22 partial_end + L21 safety_profile + L20 fault_ladder + L24 close_opened + L25 else_ask; the `d3` alias keeps 18; the layers' loop options grow by twelve keys, `plan_release`, `effect_check`, `repair_sync`, `goal_ledger`, `answer_align`, `question_cap`, `question_cap_no_repeat`, `partial_end`, `safety_profile`, `fault_ladder`, `close_opened`, `else_ask`; recomputed on the merged tree after wave 2)
- Option lines: 3700 in the 29 modules on under `all` after the retire (D3 arm: 2991 in 25; the kept four add plan_release 197, repair_sync 134, goal_ledger 180,
answer_align 198 = 709; the seven retired, 794 lines, no longer run: effect_check 137, fault_ladder 171, safety_profile 64, partial_end 95, question_cap 83, close_opened 101,
else_ask 143; with all eleven on: 4494 in 36). In the tree: 4744 in 39 modules, unchanged (nothing deleted). Before the retire: 4744 in 39 modules (after the review fixes of round 1: answer_align +22, goal_ledger +19, question_cap +6, else_ask +4, effect_check -1, fault_ladder -3, safety_profile -1; core option_services.py +23 and core/options/services.py +2 (engine services questions_put, drop_last_answer; ask / ask_clarify take a `vetoed` result), assist_loop.py 0 (the question counter: three lines rewritten in place); before them 4698 in 39 (merged tree after wave 2, L20 and L25 built in parallel from the tree after L24; L25 else_ask +139, no core code change, language packs en.json +2, ko.json +2 (patterns.otherwise, speech.q_else); after L20 4559 in 38; L20 fault_ladder +174, core: hook on_fault_stop in core/options/spec.py +1, assist_loop.py 0 (_apply_policy rewritten in place with one stop tail), lang/en.json +2 and ko.json +2 (phrases q_fault_help, say_fault_stop); after L24 4385 in 37; L24 close_opened +101, no core change; after L21 4284 in 36; L21 safety_profile +65, hazard +4 (verdict asks safety_rule); after L22 4215 in 35; L22 partial_end +95; after L23 4120 in 34; L23 question_cap +77; after L19 4043 in 33; L19 answer_align +176, ask_agree +47 (key distinct); after L18 3820 in 32; L18 goal_ledger +161; after L17 3659 in 31; L17 repair_sync +134; after L16 3525 in 30; L16 effect_check +138; after L15 3387 in 29; after S0 3190 in 28; L15 plan_release +197; before S0 3174: hazard +2, dedupe_keep_end +6, lang_words +2, precond_repair +6, hw_wait 0). Core: plan_repair.py +9 (S0), assist_loop.py 0 (L16: one line rewritten in place; L17: two lines rewritten in place), option_services.py +19 and core/options/services.py +2 (L16: services hand_holds, let_go), plan_repair.py +21 (L17: arguments sync / finish_rest, the edit loop as the helper _edits), goal_fix.py +1 and assist_loop.py 0 (L18: argument keep_go of drop_invented, one call line rewritten in place), names.py +75 and the language packs en.json +5, ko.json +1 (L19: the readings' words, phrase q_pick_one), assist_loop.py 0 (L19), option_services.py +14 and assist_loop.py 0 (L23: service ask_veto asked first by the engine services ask and ask_clarify), option_services.py +4 and core/options/services.py +1 (L22: engine service open_items), lang/en.json +1 (L22: phrase say_partial, in the speech block L19 added) and ko.json +1, assist_loop.py 0 (L22), core/safety/profile.py +10, place_class.py +30, hazards.py +8, option_services.py +4, core/options/services.py +1 (L21: rule key within_m, near_class, service safety_rule)
- Hooks: 51 hooks and 25 services of the 29 options on under `all` after the retire (D3 arm: 44 and 22; the kept four add 7 hooks, plan_release 2, repair_sync 1,
goal_ledger 1, answer_align 3, and 3 services; with all eleven on: 62 and 28). In the tree: 66 hooks and 28 services over 39 registered options, unchanged. Before the retire:
66 hooks and 28 services over 39 registered options, 26 hook kinds (merged tree after wave 2; L25 +1 hook: else_ask on_goals, no service, no new hook kind; after L20 65 and 28; L20 +2 hooks: fault_ladder on_start, on_fault_stop, no service, +1 NEW hook kind on_fault_stop (decide, flow: the recovery policy's stop); after L24 63 and 28; L24 +2 hooks: close_opened on_start, on_plan, no service, no new hook kind; after L21 61 and 28; L21 +1 hook: safety_profile on_start, +1 service safety_rule, no new hook kind; after L22 60 and 27; L22 +1 hook: partial_end on_goals_met, no option service, +1 engine service open_items, no new hook kind; after L23 59 and 27; L23 +1 hook: question_cap on_start, +1 service ask_veto, no new hook kind; after L19 58 and 26; L19 +3 hooks: answer_align on_heard, on_goals, on_issues, no service, no new hook kind; after L18 55 and 26; L18 +1 hook: goal_ledger on_issues, +2 services goal_keep, ledger_open, no new hook kind; after L17 54 and 24; L17 +1 hook: repair_sync on_replan_findings, +1 service repair_kwargs, no new hook kind; after L16 53 and 23; L16 +3 hooks: effect_check on_start, on_step_failed, on_goal_check, +1 service hand_reading, no new hook kind; after L15 50 and 22; after S0 48 and 22; L15 +2: plan_release on_start, on_plan)
- Retired: 7 from `all` (section `## Retired`: effect_check, fault_ladder, safety_profile, partial_end, question_cap, close_opened, else_ask; code kept, default off,
selectable by name). Before the retire: none yet (the retire decision needs the paired D4 measure. Candidates named: release_near and hw_tries as separate layer entries, plan_complete into precond_repair, ask_focus.unrefused, plan_complete._release once L15 is measured; the literal Place / PutIn empty-hand path of the engine and its floor head, once effect_check is measured; L15 plan_release's Close splice partly overlaps what repair_sync's second try now finds (a release an option added before a hand-full Close), to be judged on the paired measure; goal_ledger's `goal_keep` and goal_words' `goal_guard` are two answers at the same drop site, a merge candidate after the measure; goal_ledger's `named` and `retract` keys are off in D1 and retire with the layer if they stay unmeasured; ask_agree's whole-phrase `said()` once `distinct` is measured, and `distinct` itself if it stays off; `dialog_agree.names_option` and the engine's correction edit onto `names.distinguishing` / `which_named`; three readers of `grammar.speaker_forms` into one core function; L23 question_cap retires none, candidate after the measure: `ask_focus.max_confirms` if the cap also gates read-backs one day; L22 partial_end retires none; safety_profile once a robot's own safety.profile file carries within_m rules (hazard then reads them directly); the Close half of the gate's `op_hoist` once close_opened is measured; L20 fault_ladder retires none: hw_wait keeps the wait and the tries, the ladder only acts at the stop; L25 else_ask retires none (its Overlaps line names a fifth reader of the object catalogue, a merge candidate for one core catalogue helper))
