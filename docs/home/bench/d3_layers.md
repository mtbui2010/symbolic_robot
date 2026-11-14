# D3: the task sets, and the layers L9..L12 on top of D2

D3 improves the engine (`robot_agent`, `embodiplan`) and the bench around the same model, `hl-understand-p3-s700`. There is no fine-tuning. Dev 0..999 is used up
(0..599 tuning, 600..699 exposed, 700..849 D2 development, 850..999 D2 held-out, measured once), so D3 has two new task sets made by the benchmark's own generator.
The layers of the round are described in the second part; the loop writes their notes and the pilot results here.

## The two sets

| set | tasks | worlds (`seed_state`) | looked at |
|---|---|---|---|
| `d3dev` | 150 | 30000..39999 | case by case: pilots, traces, class analysis |
| `d3fresh` | 150 | 40000..49999 | never per case; one aggregate measure at the very end (`measure_d3.sh ... --fresh-final`) |

Made by `bench/suites/home/gen/d3.py` (module doc has the rules), with the same families, checks and oracle test as the shipped data (`sample.PLAN`, the
oracle solves every task in the ideal profile) and the texts the generator's templates write (no LLM, no text written by a model; `source` is `template`).
The shipped dev texts are LLM paraphrases of templates, so the D3 wording is the templates' own (see Limits).

* Shares: the (structure, kind) shares of the shipped dev split, largest-remainder over 150. Structure: single 67 (44.7 %), sequence 16, with_context 15,
  conjunction 14, correction 12, ordered 10, conditional 8 (5.3 %), shared_object 8. Kind: d3dev feasible 123, clarify 20, refuse 7; d3fresh feasible 123,
  clarify 22, refuse 5 (the refuse identities are few; d3fresh is 2 refuse tasks short and the places went to single clarify). The dev split itself is single
  44.8 %, conditional 5.6 %, feasible 81.7 %, clarify 13.8 %, refuse 4.5 %.
* Worlds and houses: worlds above every shipped task (< 10000) and above both pools (10000.., 20000..); the six train houses (never the two test houses);
  no test-only template.
* Identities (house, goals, order; independent of the world seed): a D3 task repeats no identity of train, dev, `pool_train`, `pool_eval` (each generated
  under `PYTHONHASHSEED` 0, 1 and 2), nor of the other D3 set, nor one of its own set. Texts: the generator's exact and near-duplicate check against train and
  dev (and the template texts) and the other D3 set; `audit_sets.py` of the loop repeats it.
* The test split is never read. Whether a D3 task equals a test task by identity cannot be checked (the same generator and houses can make the same
  identity); the worlds never coincide (test worlds are < 10000), as in the data design A.1.
* The `split` field of a record is `dev` so that `run --tasks FILE` (default `--split dev`) keeps its tasks; the id (`hl-d3dev-NNNNNN`, `hl-d3fresh-NNNNNN`)
  and `meta.pool` name the set.

### Files and how to make them again

`d3dev.jsonl` is committed at `bench/suites/home/data/pools/d3dev.jsonl` (297 KB). `d3fresh.jsonl` is NOT in the repos: it sits in
`/media/keti/workdir/data/homeloop_d3_fresh/` (mode 600) so no agent reads a case by accident; the same command makes it again. The generator is deterministic only for a
fixed `PYTHONHASHSEED` (the shipped families iterate over sets); use 0.

```
PYTHONHASHSEED=h python -m bench.suites.home.gen.pool --name pool_train --out POOLS/hH           # h = 0, 1, 2
PYTHONHASHSEED=h python -m bench.suites.home.gen.pool --name pool_eval  --out POOLS/hH --other POOLS/hH/pool_train.jsonl
PYTHONHASHSEED=0 python -m bench.suites.home.gen.d3 --out bench/suites/home/data/pools --fresh-out SEALED --pools POOLS
```

| file | sha256 |
|---|---|
| d3dev.jsonl | b5163df9edce0a05b12802f97e13e86660cab745b23a749db7c4a8df15452284 |
| d3fresh.jsonl | 966c692083e0cf845ca90ff86735ab10cbd3aab351a9ce5ff1183810b41bff0d |
| pool_train.jsonl h0 / h1 / h2 | 3edfcf70bee1a1bc427763707aee4b3ecd651e257d54ba82e46b37a6fe987ee9 / bd8ae5228351e3f858080a15a59f44c38864874b0aac24453f19fc5932ed9d96 / d5ccf17632da3fb0c0ef0e6ac0f7f86c1bb9e1b98e97b568be580b71c6950353 |
| pool_eval.jsonl h0 / h1 / h2 | eeb115c5f50b800326997edd686b078c3721096df07f6c7af2d5f1c19b273a11 / 8b12a6cce386129e87c6871d96b258f070975ec58299df851bc61eb81c6dbf51 / 09f22a576f94a77c6f1daa8fd948c8250313d69cc1bdb20011c88bb3bea7875f |

### Reference runs (no LLM: `--llm fake`, CPU, one seed)

`python -m bench.suites.home.cli run --tasks bench/suites/home/data/pools/d3dev.jsonl --planner {oracle,naive} --llm fake --profile {ideal,real} --lang {en,ko} --out ...`

| set | planner | ideal | real | false success (ideal / real) |
|---|---|---|---|---|
| d3dev | oracle | 1.000 | 0.860 | 0 / 0 |
| d3dev | naive | 0.960 | 0.467 | 0 / 0.013 |
| d3fresh | oracle | 1.000 | 0.853 | 0 / 0 |
| d3fresh | naive | 0.973 | 0.440 | 0 / 0.020 |

(EN and KO are the same: the fake LLM and these planners read the gold goals.) For comparison, on dev 600..699 (experiment D) the oracle was 100 / 88 and naive 95 / 55.

### Limits

* The wording is the generator's templates. The reader was trained on train texts that are templates and paraphrases; about 88-91 % of the English word 4-grams
  of D3 texts occur in train / dev texts (template phrases), so the reader is probably less challenged than on paraphrased dev texts. Compare arms within D3, not with the D2 numbers.
* 150 tasks per set: a difference of fewer than about 12 tasks (8 points) in a cell is inside the noise of one run (paired McNemar says it exactly).
* The generator's own `validate` passes on the sets except its dataset-level share check (refuse 4.0 %, navigate 4.0 % are under 5 % in a 150-task set).

## Layers (D3)

Written by the loop, one section per layer (what, why, data, tests, limits), then the pilot results.

## L9 cond_extract: a conditional request is read as plain goals

**What.** 6 independent tasks in 13 rows of the D2 analysis carry a condition ("if X is at P, do A, otherwise B"; the shapes are the generator's templates). The reader (`hl-understand-p3-s700`) has no `when` field
and turns the request into plain goals: both branches, or the condition's object as a goal. None of the 8 conditional tasks was understood; the passes were luck (the object was already at the destination, was picked up and put back).
`cond_goal` (D2 era) can decide a condition by looking, but only if the reader writes `when`, which this reader cannot.

**Fix.** Option `cond_extract` (default off, `robot_agent/options/cond_extract.py`, hook `on_goals` at order 15, before `cond_goal` at 20; new general service `ask_model`: one JSON call to the planner's model, no repair, stoppable, in the run's budget).
When the request (as said, and its English reading when there is one) holds a condition word of its language (language pack `patterns.condition` plus the robot pack's `planner.options.cond_extract.clauses`, labelled `source` or `assumed: true`),
ONE extra call is made with the pack's prompt: the request and the reader's numbered goals. The answer (fixed JSON schema: conditional, object, at, present, if_goals, else_goals, drop, unsure) is turned into the `when` field of
`cond_goal` on the goals of each branch (the else branch gets the opposite `present`); goals that only state the condition are dropped (listed in `run.filtered`); other goals stay unconditional. `cond_goal` then goes to the place,
looks, keeps the matching branch and asks once when unsure. Without a keyword, a prompt, goals, or when a goal already has `when`: zero extra calls. Non-JSON, `conditional` false, bad or clashing indexes, no object or no branch goal: goals unchanged.
Real but unclear (the model says unsure, or the place is missing or unknown to the robot): one question (pack text `q_unclear`); a place the robot knows in the answer completes the condition, any other answer leaves the reader's goals. No guess.
Once per run: a re-read after a clarification does not call again.

**D1.** `HOMELOOP_D1_LAYERS`: layer `cond_extract` (the first D3 layer of `all`) = loop options `cond_extract` and `cond_goal`, WITHOUT `cond_goal.prompt` (the reader's schema and prompt are unchanged). ASSUMED pack data in the overlay: the extraction
prompt, the two questions of `cond_goal` (where to look, is it there; nothing is said), and the Korean condition words the D2 clause misses (a sighting, a negation: `KO_COND_MORE`; the English words are the language pack's). The `d2` alias is unchanged
(hash `64b278b5...`, test `test_d2_alias_is_exactly_the_ten_d2_layers_and_equals_the_d2_overlay`).
**Tests.** robot_agent `tests/test_option_cond_extract.py` (made-up objects, two made-up languages with declared words, `*_off`, `*_empty`, `*one_call*`, `*unsure*`, `*no_keyword*`, invalid output, a run through the loop with `cond_goal` in which an object already at
the goal place stays unmoved and one elsewhere is moved); bench `tests/home/bench/test_d3_layers.py` (the layer alone on top of d2, the Korean words).
**Limits.** The extraction is read by the planner's model, not the fine-tuned reader: its quality on the Korean requests is for the pilot. A branch the reader did not read as a goal is not recovered (that branch then does nothing: the safe side).
"The condition's object is a goal" is repaired only when the model lists it in `drop`. A clash or a missing field is not asked about (a place cannot complete it). The simulated person's answer to `q_unclear` / `q_unsure` is not known here.
**It never ran (found after the first D3 runs, fixed 2026-11-15).** 0 extraction calls in the four D3 caches and 0 `cond_extract` lab flags in 600 episodes, with 8 of 150 d3dev tasks conditional. Cause: robot_agent resolves the option keys once, when `AssistLoop` is built (`assist_loop.py` `_resolve_options_cfg`), and the adapter merges the overlay into the loop's manifest only after that (`_make_loop`); it refreshed the understand and role-model keys but not the options. So `cond_extract` was on with an empty `prompt` and returned before its call; `q_unclear`, the Korean `clauses` and `cond_goal`'s `q_where` / `q_unsure` were empty too. The D2 options with overlay data (`precond_repair`, `hw_wait`, `search_budget`, `lang_words`) and `replan_guard` read their key again from the manifest when it was empty, so they were not inert (the refresh gives them the same value). Fix: robot_agent `refresh_options(loop, run_options)` (resolve the keys again against the manifest now; the engine never calls it), called by the adapter after the overlay (the file did not grow). For every other variant the resolved keys are identical (no option data in their overlays). Tests: robot_agent `tests/test_option_refresh.py` (every registered key merged after the build reaches its option, a made-up option) and the loop-level `cond_extract` tests with the prompt only in the manifest; bench `tests/home/bench/test_d3_overlay_refresh.py` (the D1 planner with the D1 pack data and the fake LLM: one `cond_extract` flag on a made-up conditional sentence, none without a condition word; a variant without option data resolves as before).

## L10 recipient_keep: the recipient of a hand-over is lost after grounding

**What.** The engine rule `goal_fix.shared_listener` (robot_agent `core/planning/goal_fix.py`, called from `assist_loop.py` after grounding) moved the recipient of a delivery
to the speaker whenever that person is also the listener of a message and the words name them once. The reader had the recipient right ("bring him the phone", "bring the mug over to X and tell him",
"bring my husband the keys, and let him know": the pronoun is not a mention), the rule handed the object to the speaker, the hand-over "succeeded" and the check said done (a false success). In the D2
analysis the rule fired in 5 of 150 Korean ideal episodes and all 5 failed; 6 independent tasks in 4 cells carry the class (EN and KO real).

**Fix.** Option `recipient_keep` (default off, `robot_agent/options/recipient_keep.py`): the engine asks the service `shared_listener` first. The recipient moves to the speaker only when the words hold a
speaker-recipient word of the language packs (`lexicon.RECIPIENT`, the robot's `recipient_words`) that is itself a first-person word (`lexicon.FIRST_PERSON`), and the person is named once. A delivery verb or
"here" alone is not evidence (the shipped English list holds "bring", "give", "here"; they say nothing about who gets the object). A second mention keeps the named person; no evidence keeps the reader's
recipient. Evidence with two mentions is the one case where the two readings disagree: one question with the existing "I can read that two ways" phrase, only when no answer was given yet
(key `ask_when_unsure`). Without first-person data in the packs the recipient always stays.

**D1.** `HOMELOOP_D1_LAYERS`: `d2` (the ten D2 layers; hash `64b278b5...` as in D2), `all` (default) = d2 + `recipient_keep`; the layer has no pack data of its own. Test: `tests/home/bench/test_d3_layers.py`.
**Tests.** robot_agent `tests/test_option_recipient_keep.py` (made-up people, made-up language `zq`, `*_off`, `*_empty`, a `give` run through the loop).
**Limits.** The Korean cases whose recipient the speech recognizer garbled ("husband" heard as another word) are not recovered here: the reader drops the recipient itself (class `asr_loss`, layer L11);
a case where the reader gives no recipient at all is not repaired (no guess). A word like "my" before the person's name is not read as evidence.

**Same round, two D2-layer bugs.** (1) `hw_wait` ignored its declared `tries`: after one wait round an unhealthy robot stopped the run (`assist_loop._apply_policy`). New service `hw_wait.more_tries`: while the declared tries
are left the step runs again; the schedule values are untouched. Test in `tests/test_option_hw_wait.py`. (2) The accounting of `retry.py` (the `injected` flag of the last attempt only) is NOT fixed here:
`bench/suites/home/retry.py` is in the checker's protected list and outside the brief's edit list; the coordinator decides (see the round report).

## L11 name_recover (+ asr_guard): the speech recogniser loses or garbles part of the request

**What.** Speech recognition turns an object name into other characters, drops a word, or hands over nothing. In D2 held-out analysis 44 of 74 EN real failures had a garbled instruction (class `asr_loss`, 14 independent tasks).
Three parts, two options:

* `name_recover` (hook `on_goals`): a goal object that is not in the robot's object catalogue (object memory, `limits.objects`) takes the ONE catalogue name within a strict distance (`near_distance`; keys `max_edits` 2,
  `max_ratio` 0.34, `min_len` 4 units, all assumed). The unit is the pack's: characters, or the letters inside a syllable when the language pack declares `asr.distance_unit: "jamo"` (Korean). Two or more near names: one
  question "Did you mean A or B?" and only an answer naming exactly one decides; none near: nothing happens. A name in the catalogue, a name that is whole words of one (or holds one), a place, a person and a `say` goal are never changed.
* `asr_guard` (new hook `on_heard`, before the reader): an EMPTY request asks to repeat WITHOUT calling the reader (the reader had invented an either-or question about nothing); a HOLE (language-pack data `asr.hole`: an article
  or possessive directly followed by a function word or the end of the request) asks to repeat once.
* Korean matching: the names are compared as whole words (`names.occurrences`), so `충전` is not found inside `충전 케이블`, and `서랍` / `책` are not matched with `서랍장` / `책장`: the distance rule gives a short name no fuzzy match
  and a name that is part of a catalogue name no replacement.

**Not fixed, said plainly.** (1) A word that SOUNDS like the object but is spelled in another script or language cannot be recovered by character distance, and is not claimed. (2) The pack's `object_and` pattern
(`lang/ko.json`, `patterns.object_and`) still splits a noun that begins with `과` (과자) in the engine's own `ko_object_issues`; changing the shipped pattern changes the default path for Korean, so it is left as it is and
reported to the coordinator (a bounded pattern behind an option key is the next step if R1 on d3dev shows the class). (3) Garbles beyond the limit and cross-word merges stay as the reader gave them.

**D1.** `HOMELOOP_D1_LAYERS`: layer `name_recover` turns on `name_recover` and `asr_guard`; no overlay data (the pack data is in robot_agent's language packs, labelled assumed). `d2` alias unchanged (hash `64b278b5...`).
**Tests.** robot_agent `tests/test_option_name_recover.py` (14: made-up catalogue, a made-up script `zq`, `*_off`, `*_empty`, `ambiguous`, a loop-level empty request); bench `tests/home/bench/test_d3_layers.py::test_name_recover_alone_on_top_of_d2_*`.
**Limits.** Strict by design: a real new object whose name is a slip away from a catalogue name would be replaced (read back before the robot moves); the limits are assumed and are not tuned on any set.

## L13 plan_complete: the plan stops short of a step its goal needs

**What.** Three classes of one family (12 independent tasks in 4 cells, from the D2 analysis of the class `plan_missing_step`, plus the sub-classes `end_goal_order`, `handover_no_approach` and `gate_unrepaired`):
(a) the plan picks an object and then closes (opens) the place the goal puts it in, with no put-in between; no operator added the release because the pack declared no skill that ends an `in` goal.
(b) The end-of-plan completion of `precond_repair` appends the delivery after the final go-home steps, so the home goal no longer holds, and a hand goal is handed over at the dock without moving to the person.
(c) A speech whose listener is elsewhere: the step is said from across the room, or names the listener instead of the message.

**Fix.** Option `plan_complete` (default off, `robot_agent/options/plan_complete.py`, hook `on_plan` after `precond_repair`), from declared pack data `planner.options.plan_complete.needs` (`achieves` in / hand, `near`):
a release is spliced before the Close (after the Open) of the held object's `in` goal place, after a move there; steps after the final go-home block (the pack's `planner.end_state`) go in front of it, a hand-over of a hand goal gets the move to
the person first; a speech with `near` gets the move to the say goal's listener, and a step that names the listener says the goal's message. `precond_repair` is not changed (the D2 layer behaves as in D2).

**D1.** `HOMELOOP_D1_LAYERS`: not in `all` (frozen interface; reach it with a comma list on top of d2); the data (the put-in ends an `in` goal, the hand-over a hand goal and needs the person near, the speech needs its listener near, the roles
open / close / say / pick) is declared in the D1 overlay with `assumed: true` (the mock robot's skill names; not a simulator rule). The `d2` alias is unchanged (hash `64b278b5...`).
**Tests.** robot_agent `tests/test_option_plan_complete.py` (made-up skills, `*_off`, `*_empty`, a run through the loop); bench `tests/home/bench/test_d3_layers.py`.
**Limits.** An `in` goal whose plan has no Close / Open of its place and ends holding the object is not completed (no step shows where the release belongs); a closed container is not opened for the put-in;
with no `end_state` data the order of the plan is kept (only the approach is added). Two say goals and a step that names no listener are not guessed.

## L14 ask_agree: ask loops and answers accepted although they contradict the person

**What.** Three classes of the read-back dialogue (14 independent tasks in the D2 analysis, classes `ask_loop` and `wrong_answer_accepted`):
(a) the "I don't know" check of `ask_focus` (rule 3) reads only the top-level `answer_unsure` key of the language pack and whole tokens of the answer; a language that keeps the phrases under `dialogue_ext`
(or inflects the verb: the answer minus the phrase leaves an ending piece) never matches, so the answer is read as a refusal and the robot asks again.
(b) A bare "no" (a slip or noise) followed by the person's restatement that reads the same goals as the refused reading: the engine asks "which part is wrong?" and stops on the second time.
(c) An "I don't know" that keeps a reading in which an earlier value of the person was changed by a later answer (the run ends a success with the wrong value).

**Why not only (a).** The red team showed that fixing (a) alone makes things worse: wherever rule 3 fires it has a bad record (it keeps readings that carried the robot's own doubt or that a later answer changed). So the
fix is a new option in front of `ask_focus`, which vetoes those cases, and `ask_focus` itself (a D2 layer) is not edited: the `base_d2` arm behaves as in D2.

**Fix.** Option `ask_agree` (default off, `robot_agent/options/ask_agree.py`; service `unrefused`, order 78 before `ask_focus`; hooks `on_goals`, `on_issues`):
1. an "I don't know" stands only when its leftover words (after `unsure_leftover`) are fillers, first-person words, whole words of an unsure phrase (both keys), or such a word with ONE declared ending
(`dialogue_ext.polite_endings`, `patterns.answer_tail`); a no-word or any other word is a refusal; the read-back must not have carried the robot's own doubt (`run.unsure`) and no answer may have changed the reading since its first read-back.
2. (b) after a refusal that was a bare no, a restatement that reads the same goals sets `allow_repeat` once: the reading is read back one more time as a yes / no question and only a yes acts (a restatement alone is no
agreement, as `dialog_agree` says). Silence or another no stops as before. Not after "no, the X"; not when the engine's two read-backs are used up.
3. (c) when the reading changed exactly one value of one goal and the person had said the earlier value, the "I don't know" asks once, naming both readings (a declared choice); the named one decides, the earlier one
is read back again (`run.patched` and `allow_repeat`); a plain yes or no picks nothing.

**D1.** `HOMELOOP_D1_LAYERS`: not in `all` (the frozen interface allows only cond_extract, recipient_keep, name_recover, replan_block after the D2 ten): switch it on with a comma list (`<the ten D2 layers>,ask_agree`); the layer has no pack data of its own. The `d2` alias is unchanged (hash `64b278b5...`, test `test_d2_alias_is_exactly_the_ten_d2_layers_and_equals_the_d2_overlay`).
**Tests.** robot_agent `tests/test_option_ask_agree.py` (a made-up agglutinative language `zq`, a refusal followed by a restatement, the either-or case, `*_off`, `*_empty`, two runs through the loop); bench `tests/home/bench/test_d3_layers.py`.
**Limits.** The upside on d3dev is small (a few tasks that need a fresh yes, a few false successes removed); the pilot gate's false-success count is the criterion. A garbled phrase that no pack phrase matches ("not sure" spelled in a dialect form)
stays a refusal; the either-or needs the earlier value named in the person's words and declared options (a free-text question has none). The simulated person's answer to the added yes / no question is not known here. `check.sh` `iface`
lists the layers allowed after the D2 ones (cond_extract, recipient_keep, name_recover, replan_block); `plan_complete` and `ask_agree` are therefore kept out of `all` (comma list only) until the coordinator extends that list.

## L12 replan_block: the replan repairs the wrong block, or runs a suffix the rules reject

**What.** Three faults of one family (about 11 independent tasks in the D2 analysis; the effect size is small, about 2-4 points per cell, inside the noise of one 150-task run):
(a) `embodiplan` SAGE `_failed_block_index` picks the block by the NUMBER of completed steps. The completed list holds steps the robot added (search steps, a look, repair inserts) and lacks steps it dropped,
so the repair lands in a later or an earlier block, and with all steps done it repairs the last block again (the robot repeats a Say).
(b) After a mid-run change of the goals the engine asked for a suffix repair with the unchanged task and the old sub-goals: the model repaired the old block and delivered the old object.
(c) A replan suffix whose own critical findings (a release with an empty hand, a release away from its place) were recorded ran anyway; only unbindable steps stopped it.

**Fix.** (a) embodiplan key `replan_block_fix` (bool, default False; embodiplan commit `ad3183a`, files `embodiplan/sage.py`, `tests/test_sage_failed_block.py`, `CHANGELOG.md`, `docs/usage.md`): with True the completed steps are lined up with the plan's
own steps by (action, object head) and the failed step is the first plan step after them; a failed step that is no plan step, or all steps done, gives the global replan (never a repair of the last block, never an empty suffix).
`replan(subgoals=)` plans the rest afresh for given sub-goals. (b) and (c) are one robot_agent option `replan_guard` (default off, `robot_agent/options/replan_guard.py`; hooks `on_planner_kwargs` (passes the key through
one general channel and the backend whitelist), `on_goal_replan` (sub-goals rebuilt from the new goals via service `subgoals`, the task text from the new goals), `on_replan_findings` (declared critical action-model codes of the
suffix simulated from the belief now join the engine's findings: the one existing refine sees them, and if they remain the run ends uncertified)). Each part has its own key (`block_fix`, `goal_rebuild`, `critical_refine`).
The red team's remarks were applied: no count-only fix (it cannot know which steps were added), no rebuild through `generate_plan` (it would bring the index fault back), the findings come from declared action-model codes, not from
the English text of the checker.

**D1.** `HOMELOOP_D1_LAYERS`: layer `replan_block` (the last of `all`) = loop option `replan_guard` plus the overlay data `planner.options.replan_guard.critical` (`assumed: true`: two action-model codes). The `d2` alias is unchanged
(hash `64b278b5...`, test `test_d2_alias_is_exactly_the_ten_d2_layers_and_equals_the_d2_overlay`). To ablate the three parts, set `replan_guard.block_fix`, `replan_guard.goal_rebuild` or `replan_guard.critical_refine` to 0 as run options.
**Tests.** embodiplan `tests/test_sage_failed_block.py` (12 tests: `*_off`, `*_empty`, forward and backward drift, grounded names, stale owners, no repeat); robot_agent `tests/test_option_replan_guard.py` (13 tests: `*_off`, `*_empty`, the key reaches the
planner, a goal change mid-run, a critical suffix through the one refine); bench `tests/home/bench/test_d3_layers.py`.
**Limits.** The wrong-recipient finding has no action-model code and is not covered. The alignment is greedy: an added step equal to a later plan step can take its place. The refine uses one replan of the run's `max_replans` and one LLM
call; a suffix that stays critical after it ends the run, which can end a run that would have recovered (the kill criterion is an offline replay of stored suffixes on d3dev, not done here). A rebuild after a goal change doubles the work only
when the repair fails afterwards. Whether the layer helps is for the pilot (paired, false-success count not higher).

**Fix round 2 (after the d3dev DEV pair, `d3` against `base_d2`).** Class: part (c) ended runs that D2 passed. The guard fired in 30 of the 600 D3 rows and stopped 27 (0 successes), 9 of them D2 successes.
In all 9 the finding was a real defect of the suffix (a release `Place X` without its MoveTo, an empty-hand repeat `PutIn P` after `PutIn P`), but the engine's own run-time check (`_guard` / `_precondition`,
`verify.symbolic_check`) refuses that step before it moves and replans, or the step was never reached (the Find before it failed and the next replan fixed it). The one refine never removed the finding
(the model returned the same block; the repeated release is not in the model's reply, it comes from the appended future blocks or the engine's repair). Change (robot_agent `replan_guard`, two parts on with
the option, commit `61c4dca`): `guarded_run`: a finding that the run-time check refuses itself only steers the one refine (added when a refine follows, service `replan_round`); a refined suffix with only such
findings RUNS (lab `part: guarded`), and the uncertified end stays for findings that check cannot catch. `release_dedupe` (hook `on_plan`): an empty-hand release that the action model refuses and that repeats
the plan's last release at the same place is dropped (no action name in the code). Data (this layer): `precond_repair`'s `near` need of `Place` / `PutIn`, SOURCED from the mock robot manifest
(`skills[].pre` `arrived(?inputs)` of `place` / `put_in`), so the D2 layer `precond_repair` (its `on_plan` runs on a replan's suffix too) inserts the missing MoveTo before the refine is needed; with
`replan_block` on it also applies to first plans. The `d2` alias is unchanged (test `test_replan_block_declares_the_near_need_of_the_releases_with_a_source_and_leaves_d2_data_as_it_was`).
Tests: robot_agent `tests/test_option_replan_guard.py` (24: the wrong-place release after a Find of an absent object runs and a normal replan follows; the same release reached sends no release to the robot and one
replan follows; `[Pick X, PutIn P, PutIn P]` loses the repeat; `guarded_run` / `release_dedupe` off give the old end). Ablate: run options `replan_guard.guarded_run=0`, `replan_guard.release_dedupe=0`.
Limits: a guarded finding that is never refused at run time because the belief there differs from the simulation is the guard's own case (the replan follows a failure instead). Not measured: no run on d3dev after this change.

## Layer hw_tries: honour the declared hw_wait tries after an unhealthy wait

**What.** Commit 7e3c476 of robot_agent had changed the D2 layer `hw_wait` itself (an unhealthy robot after a wait no longer stopped the run while declared tries were left), so `base_d2` did not behave as D2. The behaviour is now the
`hw_wait` key `more_tries` (default False), and the layer `hw_tries` (loop option `hw_more_tries`) switches it on. `hw_wait` alone is as in D2.
**D1.** Not in `all` (the frozen interface lists four layers); reach it with a comma list on top of d2. The coordinator decides whether the interface grows. Test: `test_hw_tries_alone_on_top_of_d2...` in `tests/home/bench/test_d3_layers.py`; robot_agent `tests/test_option_hw_wait.py`.
