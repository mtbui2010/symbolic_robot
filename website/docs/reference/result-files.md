---
sources: [bench/campaign.py, bench/runner.py, bench/protocol.py, bench/cli.py, bench/orchestrate.py, bench/suites/factory/__init__.py, bench/suites/factory/analyze_protocol.py, bench/suites/home/runner.py, bench/suites/home/env.py, bench/suites/home/metrics.py, bench/suites/home/report.py, bench/suites/home/cli.py, bench/suites/home/rescore.py, symbolic_robot/server.py, Makefile]
verified_at: a5cc7a4943aa
---

# Result files

!!! abstract "In this page"
    - Every file a run writes, in which folder, by which command, and what is in it.
    - The field names of the episode record of each benchmark, and the top-level keys of each `summary.json`.
    - What is private: run folders can contain task text and the robot's words. This page shows field names only, never values from task data or from recorded runs.

Two kinds of run exist, and their folders differ. A **factory campaign** plays arms against a running server and appends to one file as it goes. A **household run** plays tasks in process and writes all its files at the end. The how-to is in [Read a result](../guides/read-a-result.md); the statistics behind the numbers are in [Campaign statistics](../modules/campaign-statistics.md) and [Metrics, report and compare](../modules/home-metrics-and-report.md).

!!! warning "Treat run folders as data"
    A household `episodes.jsonl` holds the heard instruction and what the robot said (`instruction_heard`, `final_say`, `refusal_texts`); a factory `detail/` file holds the dialogue and the task. They come from the task data, which is licensed for research use only. Publish aggregates, not records.

## Where results go

| command | folder |
|---|---|
| `make bench ROBOT=<domain> SUITE=<name>` | `results/<domain>_<suite>/` (git ignores everything under `results/` except two recorded household folders) |
| `python -m bench run --out DIR` | `DIR` |
| `python -m bench.suites.home.cli run --out DIR` | `DIR` |
| `make run` | the server's own files in `run/` (below) |

## Factory campaign folder

Written by `python -m bench run --domain factory --suite <name> --out DIR`.

| file | written when | content |
|---|---|---|
| `PROTOCOL_SHA256` | before the first episode | one line: the SHA-256 of the suite's protocol file, two spaces, the file's name. A later run into the folder refuses a changed protocol file |
| `tasks.json` | before the first episode | the generated task list (a JSON array). Each task has the keys `id`, `object`, `obj_id`, `dest`, `true_place`, `kind`, `policy`, `dest_text`, `true_text`, `prompt`, `wrong_place`, `wrong_text` |
| `episodes.jsonl` | after each episode (appended) | one line per episode; the keys are below. A rerun skips every (task, arm, repeat) already in it |
| `detail/<task>_<arm>_<repeat>.json` | after each episode | the full detail of one episode: keys `dialog`, `log`, `events`, `world_start`, `world_end`, `task` |
| `summary.json` | after the analysis | the analysis of the suite (below) |
| `report.md` | after the analysis | markdown tables made from `summary.json` |
| `_server/server-<port>.log` | during the run | the output of the server the front end started |
| `_server/site-<port>/` | during the run | robot_agent's config folder for that server, with `configs/locations/default/connections.json` |

`analyze` and `report` can be run again later on the same folder: `python -m bench analyze --domain factory --suite <name> DIR` rewrites `summary.json` and `report.md`. If the analysis cannot be computed (a reduced run lacks an arm it compares), the front end prints `analysis not computed (...); episodes.jsonl is complete` and writes neither. Two post-hoc tools write one more file each: `grounding.json` (needs `detail/`) and `probe.json`.

### Fields of a factory episode (`episodes.jsonl`)

| field | meaning |
|---|---|
| `domain`, `task`, `arm`, `seed`, `sim_seed`, `policy`, `kind` | identity: the suite's domain, the task id, the arm, the repeat number, the simulator seed of this (task, repeat) and the task's answer policy and kind |
| `status` | the engine's final status, or `none` when no `done` event arrived |
| `success` | true when the object is at the destination in the true world |
| `claimed_done` | the engine's `done` event had status `success` |
| `wrong_done` | claimed done, but the truth says no |
| `distance_m` | metres travelled: the sum of the legs of successful moves |
| `questions`, `q_source` | questions answered; how many were where-questions |
| `unusable_answers`, `clarified` | answers that name no place (messy policies); of those, how many were followed by another where-question |
| `t_sim`, `wall_s`, `n_events` | simulated seconds, wall seconds, number of events |
| `faults` | names of the simulator's injected faults in the call log |
| `timeout`, `engine_msg` | the 420 s limit was hit; the first 200 characters of the engine's message |

`wall_s` is wall-clock time and differs from run to run; the rest follows from the seed, the arm and the model.

### Top-level keys of a factory `summary.json`

| suite | keys |
|---|---|
| `protocol` | `arms`, `vs_A`, `C_vs_B`, `verdict`, `by_policy`, `n_episodes` |
| `messy` | `arms`, `vs_A`, `D_vs_C`, `verdict`, `by_policy`, `partial_name_by_variant`, `n_episodes` |
| `messy_fix` | written by `analyze_fix`; its own keys, descriptive only |

`arms` has per arm: `episodes`, `success`, `wrong_done`, `distance_m`, `questions`, `t_sim`, `wall_s`, `timeouts`, `no_done_event`. Each `vs_A` entry has `n_tasks`, `combined` (`wins`, `losses`, `ties`, `p`), `success_only`, `distance_only`, one `d_<measure>` entry per measure with `mean` and `ci95`, and `d_distance_both_success`. `verdict` carries the pre-registered rule: per arm `wins`, `losses`, `p`, `d_wrong_done`, `beats_A`, and `rule_met` ([Campaign statistics](../modules/campaign-statistics.md)). Not run here: no campaign was run, so these keys come from reading `analyze_protocol.py` and `stats.py`.

## Household run folder

Written by `python -m bench.suites.home.cli run --out DIR` (or `python -m bench run --domain home --suite run`). All three files are written at the end with sorted keys, compact separators and floats rounded to six decimals. No wall-clock value is in them, so the same arguments give byte-identical files. Real listing of an offline smoke run:

```text
$ ls out/oracle
episodes.jsonl  report.md  summary.json
```

| file | content |
|---|---|
| `episodes.jsonl` | one line per episode, in task order then seed order |
| `summary.json` | 63 keys for a `--limit` (smoke) run, 61 for a full-split run, and a `config` block |
| `report.md` | a readable report: title, Config, Headline, the `By ...` breakdowns, Parts of the requests, Failures and recovery, Safety, Status counts, and the first ten failed episodes (which lists task ids: do not publish that section). The title names the earlier standalone benchmark, not this repo |

More files appear for some options:

| file or folder | made by |
|---|---|
| `llm_cache/*.jsonl` | a run with an LLM server URL: the prompt cache that `--llm cache-only` replays |
| `shard<K>/`, with `shard.json` | `run --shard K/N`: that shard's three files and a description of it |
| the three files, `llm_cache/`, in `DIR` | `merge DIR`: merges the shards; `config.merged_shards` records how many |
| `aa_1/`, `aa_2/` | `aa-check --out DIR`: the two passes of the A/A self-check |
| `rescore.json`, plus the three files | `rescore OLD --out NEW` |
| `diff.json` | `rescore-diff OLD NEW --out FILE` |
| `records.jsonl`, `summary.json`, `report.md`, `llm_cache/` | `understand-eval --out DIR`: the reading-only evaluation |
| `<root>/<planner>__<model>__<lang>/` | `live-smoke`, default root `results/live_smoke` |

### Fields of a household episode (`episodes.jsonl`)

The record has 55 keys in the smoke run (it can also hold `error`, `error_msg`, `llm_cache` and keys of planner variants). In groups ([The environment and the judge](../modules/episode-env-and-judge.md)):

| group | keys |
|---|---|
| identity | `task_id`, `seed`, `planner`, `profile`, `lang` |
| copied task labels | `kind`, `capability`, `ambiguity`, `house`, `source`, `structure`, `n_subtasks`, `mixed_kind` |
| outcome | `status`, `success`, `claimed`, `false_success`, `gc`, `goal_atoms`, `goal_changed`, `subtask_correct`, `order_ok` |
| the calls | `calls`, `failures`, `n_calls`, `sim_time_s` |
| asking | `asked`, `help`, `help_correct` |
| refusals | `refused`, `partial_refusals`, `unmatched_refusals`, `refusal_texts`, `refusals`, `misread_refusals`, `subtask_kinds`, `subtask_outcome` |
| hazards and safety | `semantic_violations`, `safety` |
| LLM use | `llm_calls`, `llm_budget_hit`, `llm_calls_translate` |
| heard and said | `instruction_heard`, `final_say`, `finish_reason`, `dialog_paths`, `dialog_not_in_lang`, `say_not_in_lang`, `final_say_not_in_lang`, `final_say_raw_ids`, `dialog_raw_ids`, `dialog_raw_id_utterances` |
| delivery and events | `delivery`, `delivery_atoms`, `events` |

Each entry of `calls` has `args`, `code`, `dur`, `event`, `injected`, `k`, `ok`, `skill`, `t`; a call to `ask` adds `answer`, `reply_kind` and `intent`.

### Keys of a household `summary.json`

Run offline on the oracle smoke run (20 dev tasks, 2 seeds, `real`): 63 keys. In groups ([Metrics, report and compare](../modules/home-metrics-and-report.md)):

| group | keys |
|---|---|
| size and the success interval | `n_episodes`, `n_tasks`, `success`, `success_ci95`, `success_ci95_episode`, `design_effect`, `icc`, `n_eff` |
| crashes | `n_error`, `error_rate`, `errors_by_type` |
| claims | `give_up_rate`, `goal_condition_success`, `false_success`, `false_success_given_claim`, `claim_rate` |
| failures | `failures_by_code`, `recovery_rate_by_code` |
| asking | `help_rate`, `correct_help_rate`, `help_recall` |
| refusals | `rejection_rate`, `false_rejection_rate`, `partial_rejection_rate`, `refuse_parts`, `feasible_parts`, `misread_refusals`, `n_episodes_without` |
| safety | `safety_violations`, `severe_violations`, `protective_stops`, `semantic_violations`, `semantic_by_code`, `min_separation_m`, `min_separation_p5_m` |
| LLM use and dialog | `llm_calls_mean`, `llm_calls_translate_mean`, `llm_budget_hit_rate`, `dialog_paths`, `dialog_not_in_lang`, `final_say_not_in_lang`, `say_not_in_lang`, `final_say_raw_ids`, `dialog_raw_ids`, `dialog_raw_id_utterances` |
| cost | `time_mean_s`, `calls_mean` |
| status | `status_counts`, `subtask_success` |
| breakdowns | `by_kind`, `by_capability`, `by_ambiguity`, `by_lang`, `by_house`, `by_structure`, `by_n_subtasks`, `by_delivery` |
| delivery | `delivery_atoms`, `delivery_mode` |
| prefix run | `smoke`, `success_reweighted`, `split_shares` |
| settings | `config` |

The `config` block has `budgets`, `data_sha`, `lang`, `limit`, `llm`, `model`, `model_digest`, `n_tasks`, `planner`, `planner_config`, `profile`, `profile_sha`, `seeds`, `split`, `user_classifier` and `versions`. `versions` holds version strings and `git describe --dirty` of the packages used, and the key names of its entries are those of the earlier standalone packages, so this site does not list them. It makes `summary.json` differ between checkouts of the same code. `data_sha` is the first 16 hex digits of a SHA-256 over the task records the run used; `profile_sha` identifies the profile values.

`success_ci95` is the task-clustered Wilson interval; `success_ci95_episode` is the plain Wilson interval of the episodes ([Metrics, report and compare](../modules/home-metrics-and-report.md)).

## Files of the server

| file | by | content |
|---|---|---|
| `<run-dir>/configs/locations/default/connections.json` | `python -m symbolic_robot run` (`seed_connections`) | a JSON array of connection entries; ours is one `llm` entry named `ollama_local` when a model is set. Existing entries are kept, an entry of the same name is replaced |
| `run/server-<PORT>.log`, `run/.server-<PORT>.pid`, `run/site-<PORT>/` | `make run` | the log, the pid file, and the `--run-dir` given to the server |
| robot_agent's memory files (`object_memory.*.json`, `grace_memory.*.jsonl`, `world_state.*.json`) | robot_agent, in its common folder | the robot's memory of the world; `reset_world` and the sim ops `reset` and `load` erase them unless told to keep them |

`connections.json` is written before robot_agent is imported, so it exists even when the start fails with a missing robot_agent (F4 in [Known pitfalls](known-pitfalls.md)); run offline, that case left a file holding one `llm` entry.

## Other files

| file | by | content |
|---|---|---|
| a JSONL trace | `python -m symbolic_robot.domains.home.selftest --out FILE` | one line per skill call, then one summary line per episode; the same arguments give a byte-identical file. A run of 2 episodes wrote 52 lines |
| `data/quality/*.json`, `tasks/*.jsonl` | `python -m bench.suites.home.data ...` | task data and reports derived from it: not described here ([Task data](../modules/task-data.md)) |

## Edge cases

| symptom | cause | what to do |
|---|---|---|
| `summary.json` differs between two checkouts | `config.versions` holds `git describe --dirty` | compare `episodes.jsonl`, or leave `versions` out |
| a household run folder has no `summary.json` | the run ended with `InfraError` (exit 3) | fix the server or the import and run again |
| scores printed, exit 4 | more than 5 % of episodes ended with status `error` | read `errors_by_type`; the scores are not a planner result |
| a factory rerun adds no line | every (task, arm, repeat) is already in `episodes.jsonl` | use a new folder for a fresh run |
| `summary.json` has `"smoke": true` | the run used `--limit`, a prefix of the task file | do not quote it as a result |
| `report` overwrote a file | it rewrites `report.md` in the run folder | copy the folder first |

Next: [Read a result](../guides/read-a-result.md), [Known pitfalls](known-pitfalls.md).
