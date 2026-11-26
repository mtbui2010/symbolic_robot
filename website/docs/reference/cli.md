---
sources: [symbolic_robot/cli.py, symbolic_robot/__main__.py, bench/cli.py, bench/__main__.py, bench/suites/home/cli.py, bench/suites/home/register.py, symbolic_robot/domains/home/profiles/__main__.py, symbolic_robot/domains/home/selftest.py, symbolic_robot/domains/home/report.py, symbolic_robot/domains/home/consistency.py, bench/suites/home/failures.py, bench/suites/home/data/__main__.py, pyproject.toml]
verified_at: a5cc7a4943aa
---

# Command lines

!!! abstract "In this page"
    - Every command line of the repo: the engine (`python -m symbolic_robot`), the generic benchmark front end (`python -m bench`), the household benchmark (`python -m bench.suites.home.cli`) and the smaller tools that have a `main`.
    - Flags with defaults, exit codes, and real output of the offline commands.
    - Which command needs which optional package.

The commands in the first three sections are the ones you use. The last section lists the research and calibration tools in one table. For the Makefile wrappers see [Make targets](make-targets.md).

## Which command, which packages

| command | needs |
|---|---|
| `python -m symbolic_robot list` | pyyaml (the core dependency) |
| `python -m symbolic_robot run` | the `server` extra (fastapi, uvicorn) and robot_agent |
| `python -m bench ...` | the `bench` extra (`websockets`): `bench/cli.py` imports the runner, which imports it, so even `list` needs it |
| `python -m bench.suites.home.cli ...` | pyyaml; robot_agent only for the `robot_agent:*` planners |
| the tools of the last section | pyyaml |

`pyproject.toml` also declares a console script, `symbolic-robot`, which calls `symbolic_robot.cli:main`. It is the same program as `python -m symbolic_robot`. Python 3.10 or later.

## `python -m symbolic_robot`

Two subcommands ([cli.py](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/cli.py)). With none, argparse exits 2 (`the following arguments are required: cmd`).

`list` prints each registered domain, its worlds and its profiles. Real output:

```text
domains:
  factory    simulated factory floor: zones, benches, bins, a lockable cabinet, a forklift lane; floors/*.yaml
             floors: assembly_hall, small_workshop   (default assembly_hall)
             profiles: ideal, real, stress
  home       simulated household (the frozen household simulator): houses, rooms, furniture, a person; profiles ideal | real | stress
             houses: care_home_suite, couple_flat, family_house, korean_apt_59, korean_apt_84, senior_flat, shared_flat, studio_flat   (default senior_flat)
             profiles: ideal, real, stress
```

`run` serves a domain as the benchmark backend:

| flag | default | meaning |
|---|---|---|
| `--robot` | required | domain name |
| `--world` | the domain's default | floor or house |
| `--floor`, `--house` | none | aliases of `--world`; one per domain's world label |
| `--profile` | `real` | `ideal`, `real` or `stress` (not restricted by argparse; an unknown one fails in `build`) |
| `--seed` | `0` | episode seed |
| `--dialogue` | `human` | `human` or `sim` |
| `--ask-mode` | `headless` | the only accepted value |
| `--model` | the domain's default | local LLM for planner and reader |
| `--opt KEY=VALUE` | none | domain option for `make_episode`; repeatable; converted to int, float, bool, else text |
| `--run-dir` | `run_dir` | robot_agent's config folder |
| `--ollama-url` | `http://127.0.0.1:11434` | where the local LLM answers |
| `--host`, `--port` | `127.0.0.1`, `8091` | where uvicorn listens |

The flags are explained in [Server glue](../modules/server-and-cli.md). Exit codes, all run offline (the first two and the fourth in an environment without robot_agent):

| command | result | exit |
|---|---|---|
| `run --robot nope` | `cannot start: "unknown domain 'nope'; known: factory, home"` | 2 |
| `run --robot factory --profile bogus` | `cannot start: unknown profile 'bogus'; known: ideal, real, stress` | 2 |
| `run --robot home --house nope` | `cannot start: "unknown house 'nope' (have care_home_suite, ... studio_flat)"` | 2 |
| `run --robot factory` without robot_agent | traceback ending `ModuleNotFoundError: No module named 'robot_agent'` (F4) | 1 |
| `list --x` | `unrecognized arguments: --x` | 2 |

In the fourth case `build` has already written `<run-dir>/configs/locations/default/connections.json`; run here, it held one `llm` entry. See [Known pitfalls](known-pitfalls.md).

## `python -m bench`

Five subcommands ([bench/cli.py](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/cli.py)).

| subcommand | arguments | does |
|---|---|---|
| `list` | none | prints `domain/name: description` per suite |
| `run` | `--domain`, `--suite`, `--out` required | runs a suite (below) |
| `analyze` | `--domain`, `--suite`, `DIR` | runs the suite's analysis on a results folder; writes `summary.json` and `report.md` |
| `report` | `--domain`, `--suite`, `DIR...` | prints the suite's markdown tables |
| `verify` | `--domain`, `--suite`, `DIR` | checks `PROTOCOL_SHA256`; prints `protocol hash matches: DIR` or `protocol hash DOES NOT match (or is missing): DIR`; exit 0 or 1 |

`list` prints the seven suites (real output in [Make targets](make-targets.md) and [The bench front end](../modules/bench-front-end.md)).

### `run` for a campaign suite (factory)

| flag | default | meaning |
|---|---|---|
| `--python` | the current interpreter | interpreter that starts the server |
| `--ports` | `8120-8129` | test ports; the first free one is used |
| `--world`, `--profile` | the suite's | override the suite's defaults (factory: `assembly_hall`, `real`) |
| `--tasks` | suite default (36) | tasks; for suites with policies, tasks per policy |
| `--seeds` | suite default (2) | repeats per task |
| `--seed0` | `0` | first repeat number |
| `--task-seed` | suite default (7) | seed of the task generator |
| `--arms` | suite default | comma list of arms |
| `--only` | none | comma list of task ids |
| `--limit` | `0` | stop after this many NEW episodes (a pilot) |
| `--model` | none | model for the server |
| `--env KEY=VALUE` | none | environment of the server; repeatable |
| `--dry-run` | off | print the plan line, start nothing |
| `--allow-protocol-change` | off | accept a changed protocol file and keep the old hash |

An unknown extra argument stops with `unknown arguments for <suite>: ...` and exit 2. A real dry run, which creates nothing:

```text
$ python -m bench run --domain factory --suite protocol --out out/x --arms Z --dry-run
suite factory/protocol: world assembly_hall, profile real, tasks 36, repeats 2, arms Z -> out/x
```

The unknown arm `Z` is accepted here (F8); a real run stops with `unknown arm(s) ['Z'] for factory/protocol; known: A, B, C, A2` before any episode ([campaign.py:23-25](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/campaign.py#L23-L25)). An unknown suite is not caught: `python -m bench run --domain factory --suite nope` ends in a `KeyError` traceback (message `no suite factory/nope; known: ...`), exit 1.

A real run prints the plan line, `server up on <host:port>`, one progress line per episode, `<n> new episodes in <s> s; server stopped`, then runs the analysis. It is [Campaign runner](../modules/campaign-runner.md). Not run here: it needs the server.

### `run` for a delegate suite (household)

For `--suite planners|run|compare|report` with `--domain home`, only `--domain`, `--suite`, `--out`, `--python`, `--ports` and `--dry-run` belong to the front end. Everything else goes unchanged to the household command line, in the same process ([The bench front end](../modules/bench-front-end.md)). The front end prints the equivalent command first. If the arguments contain `--split test` or `--split=test`, it stops with `refused: the test split is not run through this front end` and exit 1. For `run` it adds `--out` when you gave none.

```text
$ python -m bench run --domain home --suite run --planner oracle --split dev --limit 20 --out out/h --dry-run
household benchmark: python -m bench.suites.home.cli run --planner oracle --split dev --limit 20 --out out/h
```

(Same output shape as the `make bench` dry run in [Make targets](make-targets.md), where `--out` came from the Makefile.)

## `python -m bench.suites.home.cli`

The household benchmark's own command line ([cli.py](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/cli.py#L395-L561)). Through the front end only `planners`, `run`, `compare` and `report` are reachable. Calling the module directly reaches all of them. Do not read its `--help` text on this site: the program description in the code uses the earlier standalone package's name.

| subcommand | what it does | main arguments |
|---|---|---|
| `planners` | lists the registered planners; needs no data and no LLM | none |
| `run` | plays tasks times seeds with one planner; writes the three run files | see below |
| `aa-check` | runs one configuration twice on a shared cache and requires identical episodes where every prompt hit the cache | the `run` flags; needs `--shared-cache`; `--concurrent` |
| `compare` | paired McNemar test of two run folders, plus task-level tests when there are several seeds | `DIR_A DIR_B`, `--json` |
| `merge` | merges `DIR/shard<K>/` runs into `DIR` | `DIR` |
| `prompt` | prints the first prompt a `robot_agent:sage` planner builds for a task (with the fake LLM) | `TASK_ID`, `--planner`, `--split`, `--full` |
| `understand-eval` | scores robot_agent's understanding step only; refuses `--split test` | `--planner`, `--split` (default `train`), `--text clean|asr|both`, `--out` |
| `report` | re-renders `DIR/report.md` and prints it | `DIR` |
| `show` | prints one task | `TASK_ID`, `--tasks` |
| `tasks-file` | writes the packaged records of a split to a JSONL for `run --tasks`; refuses `--split test` | `--split`, `--ids`, `--limit`, `--out` |
| `rescore` | adds the part split to a recorded run, offline | `OLD --out` |
| `rescore-diff` | compares a run with its rerun; exit 4 when anything outside the refusal fields moved | `OLD NEW`, `--subset` |
| `calibrate-knowno` | the conformal threshold for the KnowNo-style planner | `--llm` required, `--epsilon` |
| `live-smoke` | live smoke runs into `results/live_smoke/...` | `--llm` required |

`show` and `tasks-file` print task data: do not publish their output.

### `run` flags

| flag | default | meaning |
|---|---|---|
| `--planner` | required | registered name or `package.module:Class` |
| `--split` | `dev` | `train`, `dev` or `test` (the test split is refused only by the front end: F7) |
| `--limit` | all | first N tasks; the run is a smoke run |
| `--profile` | `real` | `ideal`, `real`, `stress` |
| `--seeds` | `1` | seeds `0..N-1` |
| `--lang` | `en` | `en` or `ko` |
| `--llm` | none | server URL, `fake`, or `cache-only` |
| `--model` | the domain's default model | model name sent to the server |
| `--out` | required | run folder |
| `--workers` | `1` | processes |
| `--tasks`, `--allow-stale` | none, off | a task file; accept one that differs from the packaged data |
| `--set` | none | `KEY=V[,KEY=V]` profile overrides |
| `--shard` | none | `K/N` |
| `--shared-cache`, `--cache-lock`, `--replicate` | none | a prompt cache shared by paired LLM runs |
| `--max-calls`, `--max-sim-time-s`, `--max-llm-calls` | 60, 1800, 30 | episode budgets |

Exit codes of `run` ([Household runner](../modules/home-runner.md)): 0 finished with at most 5 % crashed episodes; 2 unknown planner, bad `--shard`, unavailable planner, refused shared cache, stale task file; 3 `InfraError`; 4 more than 5 % of episodes ended with status `error`. A real offline run of the first one:

```text
$ python -m bench run --domain home --suite run --planner oracle --split dev --limit 20 --seeds 2 --profile real --out out/oracle
household benchmark: python -m bench.suites.home.cli run --planner oracle --split dev --limit 20 --seeds 2 --profile real --out out/oracle
[run] oracle 40 episodes in 0.9s wall -> out/oracle
{"false_success": 0.0, "goal_condition_success": 0.868421, "help_rate": 0.15, "n_episodes": 40, "n_error": 0, "rejection_rate": 1.0, "smoke": true, "success": 0.825, "success_ci95": [0.667847, 0.917035]}
```

This is a smoke run (20 tasks, 2 seeds), not a result. The same run is explained in [Household runner](../modules/home-runner.md).

## Other tools with a `main`

Run each with `python -m <module>`. All are deterministic or read-only unless noted; none needs a server.

| module | arguments | does |
|---|---|---|
| `symbolic_robot.domains.home.profiles` | `validate [--strict]`, `show NAME`, `list`, `consistency [--n N] [--seed S] [--strict]` | checks the household profile files; prints a resolved profile as JSON; lists names; checks simulated rates against the profile |
| `symbolic_robot.domains.home.selftest` | `--seed`, `--episodes`, `--profile`, `--out FILE` | writes a JSONL trace of skill calls on random houses; same arguments, byte-identical file |
| `symbolic_robot.domains.home.report` | `hw-rates`, `oracle-mix`, `okrobot`, `asr-share` | calibration reports |
| `symbolic_robot.domains.home.consistency` | `--strict`, `--n`, `--seed` | the consistency check on its own |
| `symbolic_robot.domains.home.realism` | `--strict` | prints the realism rules report as JSON |
| `bench.suites.home.failures` | `DIR... [--json] [--examples N]` | the primary cause of each failed episode (its examples list task ids: do not publish them) |
| `bench.suites.home.data` | `generate`, `paraphrase`, `resplit`, `validate`, `stats`, `realism`, `quality`, `delivery`, `datasheet`, `tellfix`, `kofix` | task data generation and checks: [Task data](../modules/task-data.md). `generate`, `paraphrase`, `quality` write or need an LLM |
| `bench.suites.factory.analyze_protocol`, `analyze_messy`, `analyze_fix` | `DIR` | the analyses behind `python -m bench analyze` |
| `bench.suites.factory.report_protocol`, `report_messy` | `DIR...` | the tables behind `python -m bench report` |
| `bench.suites.factory.probe`, `grounding` | `DIR_A DIR_B [repeat]`, `DIR` | post-hoc looks at factory results; `grounding` needs `detail/` |
| `bench.suites.home.sim_user_audit`, `user_intent`, `tools.exp_tables`, `gen.d3`, `gen.pool`, `tools.lora.*` | | research scaffolding for data and user-model work; not part of a benchmark run |

Run offline: `profiles list` printed `ideal`, `real`, `stress`; `profiles validate` ended `== profiles validate: 0 rule(s) failed, 0 warning(s)`; `selftest --seed 0 --episodes 2 --profile real --out <file>` wrote 52 lines. Not run: `consistency` (20,000 calls per parameter), `data` subcommands, the factory analyses (they need results folders from a campaign) and the research tools.

Next: [sim_command ops](sim-command.md), [Result files](result-files.md), [Run a benchmark](../guides/run-a-benchmark.md).
