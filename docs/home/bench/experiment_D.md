# Experiment D: the HomeLoop benchmark with the new setup, one clean run

Written before the first episode of the run. Its sha256 is in `results/home_D/PROTOCOL_SHA256`, committed with this file BEFORE the run. The file must not change afterwards (a change needs a new file name and a new hash). Simulation only: no real robot, a scripted person.

## Question
How well does one planner, `robot_agent:sage_s8n_ft_d1`, do on HomeLoop tasks it was not tuned on, in English and Korean, with the simulator's faults on and off?

## What is run (everything fixed here)
* **Planner:** `robot_agent:sage_s8n_ft_d1`, one model for every LLM call (reader, planner, translator): `hl-understand-p3-s700` (Ollama digest `17e2bd3b44ac119b...`, Ollama 0.34.1), `--model hl-understand-p3-s700`. The pack's own 30B translator is not available on this machine and is replaced by this model (the user's decision). Only one model is loaded.
* **Code:** `symbolic_robot` commit `c689bd8` (bench, simulator, task data); `robot_agent` commit `76dfd3b1892131b83a23c6d73cc5f24a12356316` (branch live/no-ros); `embodiplan` commit `33660ef165d9c8421b2332f1963360dd001afa3a`. All trees clean. The simulator is frozen (not edited in this work).
* **Setup of the planner (D1):** options of `sage_s8n` (no relook), plus: `search_legs` 1, `search_total` 6, `detector_miss_rate` 0, `confirm_look`, `search_per_object`, `place_find`, `reopen_on_miss`, `end_state`, `object_words`; each safe-to-repeat skill is tried up to 2 times inside the skill (`skill_attempts` 2, not counted in the planner's call budget; simulated time is counted). The full list and the pack data (`assumed: true`) are in `bench/suites/home/planners/d1_options.py` and recorded in each run's `summary.json` config.
* **Tasks:** split `dev`, ids `hl-dev-000600` to `hl-dev-000699` (100 tasks). `dev.jsonl` sha256 `a78c902ee1756352a33368b4c26b9971c015a0948e4a6fd64a94f144f34495b2`. These ids were chosen because no earlier planner run or tuning used dev 600..999 (earlier rounds used dev 0..599; dev 200..299 had been part of "dev 0..299"). The pilot rounds of this work used dev 0..49 only. The test split is not read.
* **Cells (4), seed 0, one run each:** EN and KO, each with profile `real` (faults on: the "noise on" cell) and profile `ideal` (faults off). Order: EN real, KO real, EN ideal, KO ideal.
* **Reference rows (no LLM):** `oracle` and `naive` on the same ids, languages and profiles.
* **Command:** `python -m bench.suites.home.cli run --planner robot_agent:sage_s8n_ft_d1 --model hl-understand-p3-s700 --tasks <tasks file> --lang {en,ko} --profile {real,ideal} --seeds 1 --llm http://127.0.0.1:11434 --out results/home_D/<cell>`, the tasks file made with `tasks-file --split dev --ids 600..699`.
* **Budgets:** the bench defaults (60 calls, simulated time and LLM call caps as in `summary.json`).

## Rules of the run
* One run per cell. No second look at results to change anything, no retry of a finished episode, no change of code, options, prompts or tasks after the first episode.
* A run that aborts without writing a summary (an infrastructure error such as the model server being unreachable) is started again from the same episode file; the cause is written in the report. Episodes already written are not redone.
* Failures are classified with the oracle on the same ids (the oracle failing means an injected fault no planner can recover). No scoring rule or simulator is changed to improve a number.

## What is reported
For every cell: success (the simulator's truth, not the robot's claim), false success, goal-condition success, calls, with 95% intervals; the oracle and naive rows next to it; the list of failed tasks with the oracle result for each; the failure codes. EN against KO and real against ideal are paired on the same ids.

## Known weaknesses stated before the run (not fixed, expected to show)
* Conditional requests ("if X is on the table bring it, else Y") have no goal type; they are read as two plain goals.
* A simulated person that answers "I don't know" or stays silent to a confirmation can end the run.
* Two simulator faults on top of each other (a silent drop at place, then a phantom detection at find) can give a false success.
* An unrecoverable injected hardware fault ends the run (the oracle fails these too).
* `reopen_on_miss` and `end_state` mirror rules of this simulator (a half-open container needs Close then Open; `docked()` is a goal). They are declared pack data with `assumed: true` and must be read as an ablation, not as a general result.
* The pilots (dev 0..49, 34 to 38 of 50 against oracle 40 of 50) were not all-correct; the rest were documented weaknesses and fault cases the oracle also fails.
* The KO translator is the reader model, not the pack's 30B model; the KO numbers may be lower for that reason.
* Earlier D1 results (before the retry moved into the skill and before the new options) are not comparable.

## Pilot record (dev 0..49, for the record; not results)
EN 33, 34, 34 and KO 38, 38 of 50 across the rounds; false success 1 of 50 each time (task 25: a silent drop at place followed by a phantom detection). Fixes made from the pilots: simulated clock in the search memory, action vocabulary, object renaming, conditional clause, object matching by words, translator, retry inside the skill, and the five options above.
