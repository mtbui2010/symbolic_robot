---
sources:
  - bench/suites/home/report.py
  - bench/suites/home/metrics.py
  - bench/suites/home/runner.py
  - bench/suites/home/env.py
  - bench/suites/home/cli.py
verified_at: a5cc7a4943aa
---

# Read a result

!!! abstract "In this page"
    You open the three files of a household run in the order that works: `report.md` from its Headline, then the `config` block of `summary.json`, then `episodes.jsonl` filtered on `success == false`. The guide ends with the oracle table and its interval explained: the interval is Wilson at an effective sample size, which makes it task-clustered.
    The folder is `out/oracle` from [Run a benchmark](run-a-benchmark.md): 20 tasks, 2 seeds, profile `real`, 40 episodes. It is a smoke run, so every number here shows how to read a file and is not a result. The page shows aggregates only: no task text, no goal and no per-task row.

## Step 1: `report.md`, from the Headline

The file starts with a title and a `## Config` table, then `## Headline`. Open it at the Headline:

```text
## Headline

| metric | value |
|---|---|
| episodes | 40 |
| success | 0.825 [0.668, 0.917] |
| goal-condition success (feasible + clarify) | 0.868 |
| false success (of all episodes) | 0.000 |
| false success given a claim | 0.000 |
| help rate | 0.150 |
| correct help rate | 1.000 |
| help recall (clarify) | 1.000 |
| rejection rate (refuse) | 1.000 |
| false rejection rate | 0.000 |
| subtask success (multi-subtask tasks) | 0.864 |
| LLM calls / episode | 0.00 |
| simulated time / episode (s) | 92.6 |
| skill calls / episode | 7.8 |
```

| row | what it counts |
|---|---|
| success | episodes whose `success` is true, over all episodes. The judge reads the true world at the end; the planner's own claim never counts ([glossary](../reference/glossary.md#judge)) |
| goal-condition success | how many goal atoms hold, over the episodes of kind `feasible` or `clarify` |
| false success | the planner said `done` and the goal did not hold ([glossary](../reference/glossary.md#false-success)); once over all episodes, once over the episodes that claimed |
| help rate, correct help rate, help recall | how often it asked; how often the first question was warranted; how often it asked on a clarify task |
| rejection rate, false rejection rate | refused the tasks it had to refuse; refused tasks it should have done |

The definitions are in [Metrics, report and compare](../modules/home-metrics-and-report.md). The sections after the Headline break success down by kind, capability, ambiguity, structure, number of subtasks, house and language, then list failures by code with the recovery rate, safety counts and the status counts. The last section, "Failed episodes (first 10)", lists task ids and last calls: it is for you to read in your own copy.

One section of this run, to show the shape (the three kinds of the task set):

```text
## By kind

| label | n | success | 95 % CI |
|---|---|---|---|
| clarify | 6 | 0.833 | [0.436, 0.970] |
| feasible | 32 | 0.812 | [0.628, 0.917] |
| refuse | 2 | 1.000 | [0.342, 1.000] |
```

Read `n` before the rate. The 1.000 of kind `refuse` rests on 2 episodes, which is 1 task with 2 seeds, and its interval spans 0.34 to 1.00.

## Step 2: `summary.json`, the `config` block first

`summary.json` has 63 keys in a `--limit` run (61 in a full run). The same numbers as the report, as keys, plus `config`. Read `config` first, because it tells you what was run:

| key | value in this run | meaning |
|---|---|---|
| `planner` | `oracle` | the registry name or the `package.module:Class` spec |
| `split`, `limit`, `n_tasks` | `dev`, 20, 20 | which tasks |
| `seeds` | 2 | seeds 0 and 1 for every task |
| `profile` | `real` | the failure profile |
| `lang` | `en` | the language of the instruction |
| `data_sha` | `8d4d45894632e119` | first 16 hex digits of a SHA-256 over the task records the run used |
| `profile_sha` | `fe93eed0af9c981b12c4eef3eb18b3fab3df7dc776de60d16d8d3cb68c362ede` | identifies the profile values |
| `budgets` | 60 calls, 1,800 simulated seconds, 30 LLM calls | per episode |
| `llm`, `model`, `model_digest`, `planner_config` | `null` | no language model in this run |
| `user_classifier` | `rules` | how the simulated person's replies are classified |

The file has one more entry, `versions`. It holds version strings and `git describe --dirty` of the packages, so it differs between checkouts of the same code. Pass over it when you compare two folders. This page does not print it, because its key names are those of the earlier standalone packages.

Two runs with the same `data_sha`, `profile_sha`, planner and seeds play the same episodes. Compare only like with like: check these two hashes before you compare two folders.

The key `smoke` is `true` when you used `--limit` with fewer tasks than the split: the run is a **prefix** of the split, not a sample, and `summary.json` then also holds `success_reweighted` and `split_shares`. For the oracle run:

```text
smoke: True
success_reweighted: {'kind': 0.823812, 'n_subtasks': 0.826218}   (plain success: 0.825)
```

Treat a `smoke: true` run as a check of the setup. See [glossary](../reference/glossary.md#smoke-run).

## Step 3: `episodes.jsonl`, filtered on `success == false`

One line per episode, in task order, then seed order. The record has 55 keys. They include the task id, `seed`, `planner`, `profile`; labels (`kind`, `capability`, `ambiguity`, `house`, `structure`, `n_subtasks`); `status`, `success`, `claimed`, `false_success`, `gc` (the goal-condition fraction); `calls` (every skill call, with `skill`, `ok`, `code`, `dur`, `injected`, `t`); `failures`; the asking and refusal fields; `safety`; `llm_calls`; `sim_time_s`; `final_say`. See [Episode env and judge](../modules/episode-env-and-judge.md).

This script prints only counts, which is the right first look; it needs nothing but the standard library:

```python
import json, collections, sys
d = sys.argv[1]
eps = [json.loads(l) for l in open(d + "/episodes.jsonl")]
bad = [e for e in eps if not e["success"]]
print(len(bad), "of", len(eps), "episodes did not succeed")
print("status:", dict(collections.Counter(e["status"] for e in bad)))
print("kind:", dict(collections.Counter(e["kind"] for e in bad)))
print("failed call codes:", dict(collections.Counter(c["code"] for e in bad for c in e["calls"] if not c["ok"])))
```

```text
$ python read.py out/oracle
7 of 40 episodes did not succeed
status: {'give_up': 7}
kind: {'feasible': 6, 'clarify': 1}
failed call codes: {'hw_fault': 5, 'blocked': 1, 'unreachable': 2, 'grasp_failed': 2, 'absent': 1}
$ python read.py out/naive
15 of 40 episodes did not succeed
status: {'give_up': 14, 'done': 1}
kind: {'feasible': 11, 'clarify': 4}
failed call codes: {'grasp_failed': 1, 'hw_fault': 6, 'unreachable': 1, 'absent': 4, 'blocked': 2}
```

How to read this:

- The oracle's 7 failures all ended with `give_up`, and each had failed calls. The failure codes (`hw_fault`, `unreachable`, ...) are the simulator's declared faults, which the `real` profile injects ([glossary](../reference/glossary.md#failure-code)). The oracle retries and asks, and still gives up when the same call fails a third time.
- The naive planner has one `done` among its failures: a **false success**. It said `done` and the goal did not hold. That is the 0.025 of the naive run's output line (1 of 40).
- To find why one task failed, filter on its id in your copy and read its `calls` and `failures`. `python -m bench.suites.home.failures DIR` gives each failed episode a primary cause, "an analysis aid, not a score": check a sample by hand before you quote counts.

## The interval in the headline

The oracle row reads `success 0.825 [0.668, 0.917]`. The interval is the part people misread.

The framework guide calls it a Wilson interval. That is right, and the code refines it: the headline interval is a **Wilson interval at an effective sample size**, and so it is **task-clustered**. The reason: the 40 episodes are 20 tasks times 2 seeds, and the two seeds of one task are not independent (same task, same house, same goal). A plain Wilson interval for 33 of 40 treats them as 40 independent trials, and is a little too narrow. So the summary estimates how alike the episodes of one task are (the intraclass correlation, `icc`), turns it into a design effect (`design_effect`) and divides: `n_eff = n / design_effect`. The Wilson interval is then computed with `n_eff` in place of `n`. The plain one is kept as `success_ci95_episode` ([glossary: Wilson interval](../reference/glossary.md#wilson-interval), [effective sample size](../reference/glossary.md#effective-sample-size), [design effect](../reference/glossary.md#design-effect)).

The values from the two `summary.json` files:

| planner | successes | `success_ci95` (headline, clustered) | `n_eff` | `icc` | `design_effect` | `success_ci95_episode` (plain Wilson) |
|---|---|---|---|---|---|---|
| oracle | 33 of 40 | [0.667847, 0.917035] | 34.503817 | 0.159292 | 1.159292 | [0.6805, 0.912546] |
| naive | 25 of 40 | [0.450741, 0.771945] | 31.319149 | 0.277174 | 1.277174 | [0.470324, 0.75777] |

The clustered interval is a little wider on both sides. With one seed per task `design_effect` is 1.0 and the two intervals are equal. The more the seeds of a task agree, the wider the headline interval. Quote the clustered one, and say that it is clustered. The code is in [Metrics, report and compare](../modules/home-metrics-and-report.md#the-headline-interval-wilson-task-clustered). To judge whether two planners differ, do not compare two intervals by eye: use a paired test ([Run a benchmark](run-a-benchmark.md), [Paired tests](../learn/paired-tests.md)).

**The oracle table of this page, read in one sentence:** on 20 dev tasks, 2 seeds, profile `real`, the oracle succeeded in 33 of 40 episodes, 0.825 with a task-clustered 95 % interval of 0.668 to 0.917, and none of it should be quoted as a result because it is a smoke run.

## Common problems

| symptom | cause | what to do |
|---|---|---|
| `success_ci95` differs from a plain Wilson interval | it is task-clustered, by design | read `success_ci95_episode` for the plain one |
| a rate of 1.0 or 0.0 on a small run | a tiny denominator (the oracle run has 2 `refuse` episodes) | read `n` before the rate |
| `success` differs from what a full run gives | a `--limit` run is a prefix in file order | use the whole split, or `success_reweighted` |
| `success_reweighted` has a `None` | a stratum of the full split has no episode in the prefix | run more tasks |
| two `summary.json` of the same code differ | `config.versions` holds `git describe --dirty` | compare `episodes.jsonl`, or leave `versions` out |
| `python -m bench run --domain home --suite report DIR` changed a file | it re-renders `DIR/report.md` and overwrites it | copy the folder first if you need the old report |
| `compare --json`: the key `a` holds a string, `b` a number | `a` and `b_dir` hold the two folder names; `b` is the discordant count | read `b_dir` for the second folder |
| exit 4 and a message that the scores are not a planner result | more than 5 % of the episodes crashed | read `errors_by_type`; do not quote the scores |

## What was not run

| not run | why |
|---|---|
| the files of a full run, a `--lang ko` run, a language-model run | smoke runs only; no model |
| factory result folders (`summary.json` and `report.md` of a campaign, `detail/`) | no campaign was run; see [Campaign statistics](../modules/campaign-statistics.md) |
| the "Failed episodes" section and any per-task look | it holds task ids and last calls; read it in your own copy |

Next: [Add a planner](add-a-planner.md).
