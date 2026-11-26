---
sources:
  - bench/cli.py
  - bench/suites/home/register.py
  - bench/suites/home/cli.py
  - bench/suites/home/runner.py
  - bench/suites/home/metrics.py
  - bench/suites/factory/__init__.py
  - Makefile
verified_at: a5cc7a4943aa
---

# Run a benchmark

!!! abstract "In this page"
    You run the household benchmark with two reference planners, `oracle` and `naive`, and compare them with a paired test. The guide ends with the McNemar block that `compare` prints. You also see how to preview a factory campaign without starting anything.
    The runs are 20-task smoke runs. They show how the commands behave and what the output looks like. They are not results and must not be quoted as such. The framework guide [Benchmark a planner](https://mtbui2010.github.io/robot_agent/guides/benchmark-a-planner/) covers the same ground in shorter form; this page goes further into the flags, the exit codes and the failure modes.

All commands ran offline on a copy of commit `a5cc7a4943aa` on 2026-11-19, from the root of the copy (see [Getting started](../start/getting-started.md)). You need `pyyaml` and `websockets`. No language model is used.

## Step 1: list what exists

```bash
python -m symbolic_robot list
python -m bench list
python -m bench run --domain home --suite planners
```

The three outputs are on [Getting started](../start/getting-started.md). The suites are two kinds. A **campaign suite** (the three `factory/...` ones) drives a planner through a running server and compares **arms**, named sets of run options. A **delegate suite** (the four `home/...` ones) is a program of its own, run in the same process: the front end hands it the command line ([the bench front end](../modules/bench-front-end.md), [glossary](../reference/glossary.md#delegate-suite)). To compare task planners use the household ones.

## Step 2: run the oracle

```text
$ python -m bench run --domain home --suite run --planner oracle --split dev --limit 20 --seeds 2 --profile real --out out/oracle
household benchmark: python -m bench.suites.home.cli run --planner oracle --split dev --limit 20 --seeds 2 --profile real --out out/oracle
[run] oracle 40 episodes in 0.9s wall -> out/oracle
{"false_success": 0.0, "goal_condition_success": 0.868421, "help_rate": 0.15, "n_episodes": 40, "n_error": 0, "rejection_rate": 1.0, "smoke": true, "success": 0.825, "success_ci95": [0.667847, 0.917035]}
```

The flags that matter, from `build_parser` ([household runner](../modules/home-runner.md) lists all of them):

| flag | default | meaning |
|---|---|---|
| `--planner` | required | a name from `planners`, or `package.module:Class` ([Add a planner](add-a-planner.md)) |
| `--split` | `dev` | `train`, `dev` or `test`; the front end refuses `test` |
| `--limit N` | all | the first N tasks of the split in file order: a prefix, marked `"smoke": true` |
| `--seeds K` | `1` | seeds 0 to K-1 for every task |
| `--profile` | `real` | `ideal`, `real` or `stress`: how often skills fail |
| `--out DIR` | required | the run folder |
| `--lang` | `en` | `en` or `ko` |
| `--llm` | none | an LLM address, `fake` (tests only) or `cache-only`; the reference planners need none |

The front end itself keeps six options (`--domain`, `--suite`, `--out`, `--python`, `--ports`, `--dry-run`) and hands every other one to the household command line. The first output line shows the command it built. You can call that command line yourself: `python -m bench.suites.home.cli run ...`. Through the front end the test split is refused; through the household command line directly it is not (see the failure table below).

The run wrote three files:

```text
$ ls out/oracle
episodes.jsonl  report.md  summary.json
```

[Read a result](read-a-result.md) explains them.

## Step 3: run the naive planner

```text
$ python -m bench run --domain home --suite run --planner naive --split dev --limit 20 --seeds 2 --profile real --out out/naive
household benchmark: python -m bench.suites.home.cli run --planner naive --split dev --limit 20 --seeds 2 --profile real --out out/naive
[run] naive 40 episodes in 0.7s wall -> out/naive
{"false_success": 0.025, "goal_condition_success": 0.710526, "help_rate": 0.0, "n_episodes": 40, "n_error": 0, "rejection_rate": 1.0, "smoke": true, "success": 0.625, "success_ci95": [0.450741, 0.771945]}
```

The oracle reads the true world and plans again after every call. The naive planner runs the oracle's first plan open loop, with no recovery and no questions. Both are **privileged planners**: they may read what an ordinary planner may not ([reference planners](../modules/reference-planners.md), [glossary](../reference/glossary.md#privileged-planner)). They bracket the range, they are not baselines to beat.

The same task and the same seed give the same random draws to both planners. This is what makes the next step sharp ([determinism](../learn/determinism.md)).

## Step 4: compare

```text
$ python -m bench run --domain home --suite compare out/oracle out/naive
household benchmark: python -m bench.suites.home.cli compare out/oracle out/naive
paired McNemar test on (task, seed): A = out/oracle  B = out/naive
| n_pairs | success A | success B | b (A ok, B fail) | c (A fail, B ok) | statistic | p | method |
|---|---|---|---|---|---|---|---|
| 40 | 0.8250 | 0.6250 | 8 | 0 | 0.0000 | 0.0078 | exact_binomial |

2 seeds per task: seeds of one task are correlated, so use the task-level tests below for claims (docs/metrics.md).
| test | n | statistic | p |
|---|---|---|---|
| McNemar on per-task majority (exact_binomial) | 20 tasks | 0.0000 | 0.0625 |
| task sign-flip permutation (10000 perms) | 20 tasks | 4.0000 | 0.0324 |
```

How to read it:

- `compare` pairs the episodes by (task, seed). Only pairs that differ matter: `b` = the oracle succeeded and the naive planner did not (8), `c` = the opposite (0). Pairs where both agree carry no information about a difference.
- The first test treats the 40 pairs as independent: p = 0.0078. But the 40 pairs are only 20 tasks, and two seeds of one task are alike. So `compare` adds two task-level tests and tells you to use them for claims. One counts a task as a success when the majority of its seeds succeeded (with 2 seeds, both): p = 0.0625. The other flips the sign of each task's difference at random, 10,000 times: p = 0.0324.
- The tests disagree about the 0.05 line. On a run this small, that is what you should expect. A real comparison needs many more tasks. The tests are explained in [Paired tests](../learn/paired-tests.md) and the code in [Metrics, report and compare](../modules/home-metrics-and-report.md).

**This block is what the guide ends with.** It is a smoke run: do not quote "oracle beats naive, p = 0.0078" from it.

## Step 5: check that a run repeats

Everything is seeded and no clock value is written to the result files, so the same command writes the same files. The oracle run was repeated into `out/oracle2` and the two folders compared:

```text
$ diff -r out/oracle out/oracle2 && echo IDENTICAL
IDENTICAL
```

The wall time goes to the error stream only. A run with a language model is not exactly repeatable unless its answers come from a cache; that was not run.

## Step 6: preview a campaign (not run)

A factory campaign needs a server, robot_agent and a language model. Its `--dry-run` needs none: it prints one plan line and returns before it hashes the protocol, starts a server or creates a folder.

```text
$ python -m bench run --domain factory --suite protocol --out out/f --dry-run --tasks 3 --seeds 1 --arms A,B
suite factory/protocol: world assembly_hall, profile real, tasks 3, repeats 1, arms A,B -> out/f
```

After this command `out/` held no `f`. The real run is `make bench ROBOT=factory SUITE=protocol ARGS="..."`, which adds `--out results/factory_protocol` for you ([Make targets](../reference/make-targets.md)). **Not run.** See [Factory suites](../modules/factory-suites.md) and [Campaign runner](../modules/campaign-runner.md) for what it would do.

The household suites take `--dry-run` too. With `--out out/newdry` it printed the command and the folder was not created.

## Common problems

| symptom | cause | what to do |
|---|---|---|
| `ModuleNotFoundError: No module named 'websockets'` | even `list` imports it | install the extra `bench` |
| `refused: the test split is not run through this front end`, exit 1 (both `--split test` and `--split=test`) | the front end refuses the test split | by design. Work on `dev` |
| `python -m bench.suites.home.cli run --split test` is not refused | current behaviour: `cmd_run` has no split check; the guard is in the front end, in `understand-eval` and in `tasks-file`. Recorded on the [household runner](../modules/home-runner.md) page, where it was run | go through `python -m bench`; do not read the test split outside the protocol |
| `planner saycan_like needs --llm URL or --llm fake`, exit 2, no folder | the planner needs a language model (56 of 58 names do) | give `--llm`, or use `oracle` or `naive` |
| exit 4, `40 of 40 episodes crashed (status error, ...); the scores are not a planner result` | more than 5 % of the episodes ended with status `error`; the files are written, but the scores are not a planner result. This message is the real one from a deliberately wrong planner that reads the hidden goal without being privileged: `PermissionError` in all 40 episodes | fix the planner ([Add a planner](add-a-planner.md)); read `errors_by_type` in `summary.json` |
| exit 3 and no `summary.json` | an `InfraError`: the language model failed or the planner's code could not be imported | fix the server or the import. An infrastructure failure never becomes a score of 0 |
| a traceback ending in `ModuleNotFoundError` and exit 1 for `--planner nosuchmod:X` | current behaviour: a `package.module:Class` with a module that cannot be imported raises in `planner_class` before the run starts. An unknown plain name is checked differently | check the module and class names |
| `unknown arguments for <suite>: ...`, exit 2 | an option the generic parser does not know, given to a campaign suite | use only the options the campaign parser knows (`--world`, `--profile`, `--tasks`, `--seeds`, `--seed0`, `--task-seed`, `--arms`, `--only`, `--limit`, `--model`, `--env`, `--dry-run`, `--allow-protocol-change`, `--python`, `--ports`, `--out`) |
| `--dry-run` prints a plan for an unknown arm (`--arms Z`) and exits 0 | arms are checked only when the campaign runs | check the arm names; a real run stops with `unknown arm(s)` before any episode |
| the success of a `--limit` run differs from a full run | a prefix is not a sample | use a full split, or the reweighted figure in `summary.json` ([Read a result](read-a-result.md)) |

## What was not run

| not run | why |
|---|---|
| any campaign (`factory/protocol`, `factory/messy`, `factory/messy_fix`), `make bench ROBOT=factory`, `analyze`, `report` and `verify` on factory results | they need a server, robot_agent and a language model |
| a full run (the whole `dev` split, more seeds, both languages) | the runs here are smoke runs of 40 episodes |
| any planner that needs a language model, `--llm cache-only` | no model was called |
| the `robot_agent:*` planners | robot_agent is not importable in the runs above ([robot_agent planners](../modules/robot-agent-planners.md)) |
| `make test` | `pytest` is not installed |

For scale: the one recorded pre-registered comparison of two arms (the file `docs/home/bench/d5_final_result.md`, measured 2026-11-18, 1,200 episodes per arm) reports 887 against 897 successes and a paired p value of 0.253. That aggregate does not come from any run on this page; see [Paired tests](../learn/paired-tests.md).

Next: [Read a result](read-a-result.md).
