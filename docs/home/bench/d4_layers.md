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

## Complexity budget

Measured on robot_agent at base 64c7e72 (before S0) and after S0. Option lines: `robot_agent/options/*.py` without `__init__.py`.

Layers on: 18 (D3 arm `all`; before S0 18, after S0 18; loop option keys on 37, unchanged)
Option lines: 3190 in 28 modules (before S0 3174; +16: hazard +2, dedupe_keep_end +6, lang_words +2, precond_repair +6, hw_wait 0). Core: plan_repair.py +9, assist_loop.py 0
Hooks: 48 hooks and 22 services over 28 registered options (before S0 48 and 22): no hook or service added
Retired: none (S0 only instruments; the retire decision needs the paired D4 measure. Candidates named: release_near and hw_tries as separate layer entries, plan_complete into precond_repair, ask_focus.unrefused)
