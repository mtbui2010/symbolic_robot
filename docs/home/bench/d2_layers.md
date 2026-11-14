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
- Pilot P5 (dev 700..849, KO ideal, one task with two goals: put a bowl in the fridge, hand over a mug), both arms failed with `give_up` ("I could not
  make a plan that passes my checks"; `gate_strict` per_goal_repair kept False twice). Root cause (traced by replaying the cached plan): the planner's plan
  for the hand goal ended at `Pick mug, MoveTo <spot within reach>`, with no Handover. The gate's `action` operator only renames an existing release, and
  `insert` / `hoist` / `dedupe` do not add one; `complete` (`gate_complete`) is off; `precond_repair` only added steps that the NEXT skill needs, and the
  plan had no next skill. The bowl goal was repaired by the gate's per-goal repair; the mug goal was left with one critical finding.
  Class: a plan that stops before the step that achieves its goal (end-of-plan completion). Fix: the rule key `achieves` (on / in / hand) in the same data;
  the replay ends holding the object of a goal nobody released, so the pack's skill is appended (D1 data, `assumed`: Place achieves on, Handover achieves
  hand; the manifest effects name no goal). Tests: `test_end_of_plan_*` (made-up skills, no hl-dev id). Replay of the case: the gate now certifies the plan
  (13 steps ending in `Handover`); the later LLM calls of the run are cache misses (a replay limit), so the final outcome is the coordinator's to rerun.
- Limits: the option inserts steps only for the declared needs; the Find / Pick of an object is placed before the approach to the person, and the gate's
  own operators place it at the right source. It does not repair a plan whose goals are wrong (L2..L4).

## L2 `goal_words`: the goal filter compares whole words

- What: the filter that drops "invented" goals (a move goal whose object is an ENV place) compares whole words. A name is a place only when it equals the
  head or an alias of exactly one ENV key. A name the robot knows as an object (its object memory, the manifest `limits.objects` names) is an object and
  its goal is kept; when that name is also a place, the person is asked once which one they mean. An object named by two or more move goals keeps the
  receiver of each (the receiver repairs skip it).
- Why: the old match took "book" inside "bookshelf" and an object that is the alias of a place (a charger of a dock) for the place, dropped the goal and
  the run asked again or did nothing; a delivery of a shared object went to another person.
- Data: none. D1 turns the option on and declares no pack data (empty layer data).
- Tests: `robot_agent/tests/test_option_goal_words.py` (made-up lampshelf / lamp, a pail that is the alias of a rack: substring non-match, whole-word
  match, catalogue first, ambiguity asked once and the two answers, shared receiver, off, empty, a loop-level run on and off) and
  `tests/home/bench/test_d1_classes.py` (the layer in the switch).
- Limits: the catalogue is what the robot has seen or declares in `limits.objects`; an object it has never seen that is also a place name is still read as
  the place. "Shared" means one object named by two or more move goals; other kinds of sharing are not covered.

## L3 `ask_focus`: purposeful questions

- What: four rules on the read-back. (1) No confirmation of an object noun that is a place the robot knows (head or alias, whole words) or a word of another
  field of a goal (a tool, a surface reached by other words). (2) When a move goal's object fits two or more objects of the world (object memory and
  `limits.objects`, none named exactly like it), the read-back asks "Which X do you mean: A or B?", whatever the reader's label said. (3) An "I don't know" to
  "Is that right?" leaves the reading standing and does not start the correction path. (4) The read-back rounds are bounded by the key `max_confirms`
  (default 3; the engine's own cap is 2, plus one after a correction).
- Why: the D dialogs asked for confirmation of things the plan already had, did not ask when the world held two matching objects, treated "I don't know"
  as "no" (then asked what to do instead, again), and could go round several times.
- Data: none. The phrases of "I don't know" are the language packs' and the robot pack's (`answer_unsure`); no data = the answer is read as before.
  D1 turns the option on and declares no pack data (empty layer data).
- Tests: `robot_agent/tests/test_option_ask_focus.py` (made-up loft with a stool, a rack with the alias hanger, red / blue mugs: each rule, exact name,
  whole words, off, empty, two loop-level runs on and off) and `tests/home/bench/test_d1_classes.py` (the layer in the switch).
- Limits: rule 2 reads names only (a goal object that is a description of the world's objects by words); two objects that differ only in place are not
  told apart. Rule 3 keeps the reading when the person says "I don't know" to a read-back: a misheard reading is then not caught by that answer.
  Rounds of other questions (where is it, which part) keep their own limits.

## L4 `entity_cover`: every object noun of the request is a goal or a stated reason for dropping

- What: a name of the object catalogue (object memory and `limits.objects`) that the request says (whole words, the last may be a plural), that no goal's
  object holds (either way round; a say goal's message counts) and that is not a place the robot knows adds an `object` issue, so the read-back asks about it once.
  A note of the dropped goal (`run.filtered`) rides along as the reason; key `ask_reasoned` (default on). For a non-English request the language layer's trusted
  English reading is used (service `request_english`); no reading, nothing is added.
- Why: in multi-object requests the understanding kept one clause and the run ended "done"; the engine's own noun check only sees a noun after a determiner in
  object position, so a bare noun in a list went unasked.
- Data: none. D1 turns the option on and declares no pack data (empty layer data).
- Tests: `robot_agent/tests/test_option_entity_cover.py` (made-up kettle / lamp / mugs / ladle: all covered, one dropped, dropped with a reason, unknown noun,
  places, message goals, foreign language through the service, off, empty, a loop run on and off) and `tests/home/bench/test_d1_classes.py` (the layer in the switch).
- Limits: a drop the person meant (a negation: "not the lamp") is also asked about while `ask_reasoned` is on; the pilots decide whether the key stays on. Names the
  catalogue lacks are not seen; a catalogue name that is a part of a longer description is matched as whole words only.

## L5 `hazard` key `receivers`: a product is not handed to a receiver the pack's rule names

- What: the existing robot_agent option `hazard` has the key `receivers` (legacy `hazard_receiver`, default off). On, the profile rules that carry
  `enabled_by: hazard.receivers` refuse a product x receiver pair (the receiver is the goal's destination or `near_person`, classed from the ENV person entry's names).
  The layer name in `HOMELOOP_D1_LAYERS` is `hazard`; D1 sets the loop option `hazard_receiver`. No engine change.
- Why: requests that hand a hazardous product to a vulnerable person were carried out, because the rule is off unless asked for.
- Data: the mock robot's own safety profile (`manifest safety.profile`, `configs/safety/household.yaml`, rule `chem_child`, `assumed`); the layer adds no overlay data.
  A robot with no profile, or a profile with no receiver rule, gets no refusal (fail open).
- Tests: `robot_agent/tests/test_option_hazard_receivers.py` (made-up "glim" product and "tiny one" receiver: refused, both sides needed, off, no profile or no rule,
  foreign words) and `tests/home/bench/test_d1_classes.py` (the layer in the switch).
- Limits: it refuses by words, so a receiver whose entry has no matching name is not classed. A refusal on a task the judge expects done would cost a success: the pilots
  (false-success and success counts, paired) decide whether the layer stays on.

## L6 `hw_wait`: the wait after a hardware fault is the pack's, per failure kind

- What: robot_agent's wait after a failure was one schedule (`planner.recovery.wait`, 2+4+8 s) for every kind, with the policy table's retry counts
  (a hardware fault: one health check, then stop). With the option on, the pack declares per failure code the schedule, the number of tries and the
  first answer (`planner.options.hw_wait.kinds`). An empty schedule sends no wait command (the pack says waiting does not help that kind), which is how the
  redundant commands go. A kind with no entry keeps the engine's schedule and the policy table.
- Why: 34 of the 140 failures in D were hardware stops, ended by the single health check or by the fixed wait running out.
- Data: D1 declares two kinds, `perception_unavailable` and `hw_fault`: `schedule_s [2, 4, 8]`, tries 3 and 2, action `wait_health`, `assumed: true`
  (the mock robot's spec sheet declares none; the numbers are the base wait's backoff, not a simulator rule and not tuned). Layer off (`none`): no data, the overlay of D.
- Tests: `robot_agent/tests/test_option_hw_wait.py` (own schedule used, empty and foreign data keep 2+4+8, a kind without data, an empty schedule sends no
  wait, tries decide when the run stops, bad entries, off; run through AssistLoop) and `tests/home/bench/test_d1_classes.py` (the switch, `none` equals D).
- Limits: the schedule is read where `wait_on_robot` runs the wait, so it needs that option and a declared `recovery.wait` action (both in the D1 base). A
  fault that is not cleared by waiting still ends the run after the tries. Whether the tries and schedule help is for the pilots to measure (paired, dev 700..849).

## L7 `search_budget`: a search budget per object, a stop by probability, ask once

- What: robot_agent's search had one count (`search_total`) for the run, no stop by how likely the unvisited places still are, and an unasked or twice-asked
  where-question. With the option on, the pack declares `looks_per_object`, `stop_probability` and `ask` (`planner.options.search_budget.budget`). The looks
  counted for an object are the places searched for it; the search is over when its looks are used up or the belief's share on the places not yet looked at is
  under the stop probability; then the person is asked once, the answer is looked at, and a further miss (or "I don't know") ends the run naming the places
  looked at. An "I don't know" given earlier does not repeat the question and does not end the search while looks are left.
- Why: exec and budget failures (20 of 140 in D) and the commands spent searching; the second object of a request started with the first one's looks used.
- Data: D1 declares about 8 looks, stop under 10%, ask once, `assumed: true` (the brief's figures, not tuned, not a simulator rule). Layer off (`none`): no data, the overlay of D.
- `reopen_on_miss`: left OFF when this layer is on (`reopen_on_miss: "0"`). Its remedy `[Close, Open]` mirrors the simulator's partial-open state (an ablation
  by its own note) and cost 56-74 commands with no gain on the ideal profile. The option is already pack-declared and once per container, so there was nothing
  to narrow further. `none` keeps it on, as in D.
- Tests: `robot_agent/tests/test_option_search_budget.py` (per-object budget, declared looks replace `search_total` and the run reports, stop on low remaining
  probability, ask once then stop, `ask: never`, "I don't know" goes on alone, empty and foreign data, off; through AssistLoop) and
  `tests/home/bench/test_d1_classes.py` (the switch, `none` equals D, reopen_on_miss off only when the layer is on).
- Limits: needs search legs (a search without them keeps `search_max`). With `ask_help` off the question is not asked. The remaining share is the belief's, so an
  uninformed belief stops only when most places are used. Whether it helps is for the pilots to measure (paired, dev 700..849); the layer stays on only if the
  paired result is not worse and false successes do not rise.

## L8 `lang_words`: clause words as language-pack data

- What: the words that open a condition ("if the drawer is open") or a negation ("do not touch the mug") were English regexes in the engine
  (`understand._COND`, `_NEG`). With the option on, robot_agent reads `patterns.condition` and `patterns.negation` of the run's language pack (and of the prompt
  language's) through `core/planning/clauses.py`; the object coverage, the destination repair and the negation filter use them. The recipient words and the
  correction markers were pack data already.
- Why: the KO gap. A reading that is not English took no clause out of the request, so the object of a condition could become a goal. The shipped English pack holds the former
  regexes, so English reads the same. Korean has no clause data in the shipped pack (a Hangul literal in robot_agent's engine tree is barred by the checker),
  so the D1 layer declares it in the robot pack overlay (`planner.options.lang_words.clauses.ko`, assumed: general grammar, not measured).
- Data: `lang/en.json` (patterns) and the Korean overlay above, `assumed: true`; only when the layer is on. Layer off (`none`): no option, no data, the engine's own reading.
- Tests: `robot_agent/tests/test_option_lang_words.py` (a language invented in the test, one kind only, empty data, robot-pack words, the shipped English pack equal to the old
  reading, off, through AssistLoop) and `tests/home/bench/test_d1_classes.py` (the switch, `none` equals D, the Korean data on a Korean request).
- Limits: most clause checks read the ENGLISH reading of a translated request (`Heard.english`), where the English pack already worked; the Korean data matters
  for an untranslated Korean text only. Whether it helps is for the pilots to measure. The two KO data errors found on the way (tasks 629 and 643) are in
  `data_issues_ko.md`; they are not changed.

## Fixes after the round-1 review (class, not item)

- L8 Korean data (`d1_options.KO_CONDITION`, `KO_NEGATION`, assumed): the condition is a predicate stem (be, not be, do, become, open, closed, on, off) plus a conditional ending, up to
  three words of its own clause, never followed by a request form ("... myeon dwae / johgesseo"); a noun that only ends like one (screen, instant noodles) stays; the negation reads
  "ji ma / ji mal-go|a|ra / ji anh-" only, so a noun ending in "ji" before a verb that starts with "mal" (to dry) stays. Test: `tests/home/bench/test_d1_ko_clauses.py`.
- L2 `goal_words`: an answer can drop the goal when the place is headed like the object (it is told apart by its room, alias or extra head words). L2, L3, L4: articles and plurals are the language
  pack's (`articles`, `plural_rules`), none declared = nothing stripped. L3: an "I don't know" that carries a no or a correction is a refusal. L4: only a name the request handles counts
  (not in a condition, a negation, or as a landmark or tool); runs before `ask_focus`. L6, L7, L8: pack data with no label is not used.
