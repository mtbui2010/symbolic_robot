---
sources:
  - pyproject.toml
  - README.md
  - Makefile
  - symbolic_robot/cli.py
  - bench/cli.py
  - bench/runner.py
  - bench/suites/home/register.py
verified_at: a5cc7a4943aa
---

# Getting started

!!! abstract "In this page"
    - What you need to install, and what each extra is for.
    - How to get a clean copy of the code with `git archive`, and how to run the two listing commands, `python -m symbolic_robot list` and `python -m bench list`.
    - A first run: one planner, 20 tasks, 2 seeds, about a second. It is a smoke run, not a result.
    - What fails when a package is missing, with the real error text.

Everything below was run offline on a copy of commit `a5cc7a4943aa`, on 2026-11-19. No package was installed, no server was started and no language model was called.

## What you need

| You want to | You need |
|---|---|
| list the domains, build a world, run a domain in your own script | Python 3.10 or later and `pyyaml` (the only hard dependency) |
| use `python -m bench` (every suite, even `list`) | the extra `bench`: the package `websockets` |
| run the reference planners `oracle` and `naive` on the household benchmark | the two lines above; no language model |
| serve a domain to robot_agent (`python -m symbolic_robot run`, `make run`, a factory campaign) | the extra `server` (`fastapi`, `uvicorn`), and [robot_agent](https://mtbui2010.github.io/robot_agent/) importable |
| run a planner that needs a language model (the four published-style baselines, the robot_agent planners) | a language model address for `--llm`; the robot_agent planners also need robot_agent |
| run the test suite (`make test`) | the extra `test`: `pytest` |

The task data of the household benchmark is licensed for research use only. This site never shows a task. See [Task data](../modules/task-data.md) and [Versions and licences](../reference/versions-and-licences.md) before you use or share it.

The extras are declared in `pyproject.toml`: `server = ["fastapi", "uvicorn"]`, `bench = ["websockets"]`, `test = ["pytest"]`. A normal install is `pip install -e ".[bench]"`. The steps below do not install anything: they run from the root of the copy, where `python -m` finds the packages `symbolic_robot` and `bench` in the current folder.

## Step 1: get a copy

```bash
mkdir scratch && git archive a5cc7a4943aa | tar -x -C scratch
cd scratch
```

Run this inside a clone. `git archive` writes the files of that commit and nothing else: no `.git`, no run folders, no results. Work in the copy and nothing in your clone changes.

Two warnings from the runs for this page:

- `python -m symbolic_robot run ...` creates a folder `run_dir` in the current folder before it fails (see the common problems below). That is one more reason to work in a scratch copy.
- Result folders are written where you point `--out`. Use `out/...` inside the copy.

## Step 2: list the domains

```text
$ python -m symbolic_robot list
domains:
  factory    simulated factory floor: zones, benches, bins, a lockable cabinet, a forklift lane; floors/*.yaml
             floors: assembly_hall, small_workshop   (default assembly_hall)
             profiles: ideal, real, stress
  home       simulated household (the frozen household simulator): houses, rooms, furniture, a person; profiles ideal | real | stress
             houses: care_home_suite, couple_flat, family_house, korean_apt_59, korean_apt_84, senior_flat, shared_flat, studio_flat   (default senior_flat)
             profiles: ideal, real, stress
```

A **domain** is one simulated world with its robot ([domain protocol](../modules/domain-protocol.md)). The word before each colon in "floors:" and "houses:" is that domain's name for a world. A **profile** is a set of failure rates: `ideal` has none, `real` is declared, `stress` is harsher ([glossary](../reference/glossary.md#profile)). This command needs only `pyyaml`.

## Step 3: list the suites

A **suite** is one benchmark you can run by name ([glossary](../reference/glossary.md#suite)). `python -m bench list` shows them:

```text
$ python -m bench list
suites (make bench ROBOT=<domain> SUITE=<name> [ARGS=...]):
  factory/messy: a messy person (room only, vague, mind change, partial name, silent), arms A C D A2, 6 tasks per policy x 2 repeats (336 episodes)
  factory/messy_fix: repair check of three ask_source keys on the failed messy tasks, arms A E D (150 episodes)
  factory/protocol: three engine options, arms A B C A2, 36 tasks x 2 repeats (288 episodes), scripted person knows|unknown|wrong
  home/compare: household benchmark, compare: paired McNemar test of two run folders (ARGS: DIR_A DIR_B)
  home/planners: household benchmark, planners: list the planners (needs no data and no LLM: a safe smoke test)
  home/report: household benchmark, report: re-render report.md of a run folder (ARGS: DIR)
  home/run: household benchmark, run: play tasks x seeds with a planner (pass --planner/--split/--limit/--profile/--seeds/--out ... through ARGS)
```

Without the `bench` extra, even this command fails. This is the real end of the error, on an interpreter that has `pyyaml` and no `websockets`:

```text
$ python -m bench list
  ...
    from .runner import run_episode
  File ".../bench/runner.py", line 11, in <module>
    import websockets
ModuleNotFoundError: No module named 'websockets'
```

`bench/cli.py` imports the campaign code, which imports `websockets`, whether or not you run a campaign. The fix is `pip install websockets` (the extra `bench`). The front end is described in [the bench front end](../modules/bench-front-end.md).

## Step 4: list the planners

```text
$ python -m bench run --domain home --suite planners
household benchmark: python -m bench.suites.home.cli planners
oracle  privileged reference: re-solves from the true world after every call; retries, waits, asks for help
naive  privileged ablation: the oracle's start-state plan, open loop, no recovery or asking
saycan_like  after SayCan (Ahn et al. 2022): LLM picks one affordance-filtered call per step by index
inner_monologue_like  after Inner Monologue (Huang et al. 2022): step-wise LLM with result and scene feedback
progprompt_like  after ProgPrompt (Singh et al. 2022): one LLM-written program with assert/recover lines
knowno_like  after KnowNo (Ren et al. 2023): conformal prediction set over interpretations, asks when > 1
...
```

The first line is printed by the front end, the rest by the household command line. In the real output each name and its description are separated by a tab; two spaces stand for it here. There are 58 names; the list above stops after the six that do not need robot_agent. The other 52 start with `robot_agent:`. Two of the 58 (`oracle` and `naive`) need no language model: they are **privileged planners**, which may read the true world, so they are references and not planners to beat ([planner interface](../modules/planner-interface.md)).

## Step 5: a first run

```text
$ python -m bench run --domain home --suite run --planner oracle --split dev --limit 20 --seeds 2 --profile real --out out/oracle
household benchmark: python -m bench.suites.home.cli run --planner oracle --split dev --limit 20 --seeds 2 --profile real --out out/oracle
[run] oracle 40 episodes in 0.9s wall -> out/oracle
{"false_success": 0.0, "goal_condition_success": 0.868421, "help_rate": 0.15, "n_episodes": 40, "n_error": 0, "rejection_rate": 1.0, "smoke": true, "success": 0.825, "success_ci95": [0.667847, 0.917035]}
```

What it did: it played the first 20 tasks of the `dev` split, each with seeds 0 and 1, under the `real` profile, with the `oracle` planner: 40 **episodes** (one task played once with one seed). It wrote three files to `out/oracle`:

```text
$ ls out/oracle
episodes.jsonl  report.md  summary.json
```

!!! warning "A smoke run, not a result"
    20 tasks and 2 seeds say little about a planner. The key `"smoke": true` marks a run that used `--limit` with fewer tasks than the split ([glossary](../reference/glossary.md#smoke-run)). The wall time (0.9 s here) changes from run to run; every other value is the same each time. Use this run to check your setup, not to quote a score.

Where to go from here:

| next | page |
|---|---|
| compare two planners and read the paired test | [Run a benchmark](../guides/run-a-benchmark.md) |
| understand the three files | [Read a result](../guides/read-a-result.md) |
| test your own planner, domain or suite | [Add a planner](../guides/add-a-planner.md), [Add a domain](../guides/add-a-domain.md), [Add a suite](../guides/add-a-suite.md) |
| the ideas behind it | [How it works](../how-it-works/index.md) |

## Common problems

| symptom | cause | fix |
|---|---|---|
| `ModuleNotFoundError: No module named 'websockets'` on `python -m bench list` | `bench/cli.py` imports `websockets` through the campaign code | install the extra `bench` |
| `python -m symbolic_robot list` prints `factory    not loadable: ModuleNotFoundError: No module named 'yaml'` and then the home line without its houses (run on an interpreter without `pyyaml`) | `pyyaml` is not installed; a domain that cannot be imported is listed as `not loadable` and the command goes on | `pip install pyyaml` |
| `python -m symbolic_robot run --robot factory` ends with `ModuleNotFoundError: No module named 'robot_agent'`, exit 1, and leaves a `run_dir` folder | current behaviour: the command builds its folders first and imports robot_agent last (finding F4) | `run` serves a domain to robot_agent; install robot_agent or do not use `run`. `list` and the household reference planners do not need it ([server and CLI](../modules/server-and-cli.md)) |
| a planner other than `oracle` or `naive` stops with `planner <name> needs --llm URL or --llm fake` | it needs a language model | give `--llm`, or use `oracle` and `naive` |
| `refused: the test split is not run through this front end` | `--split test` is refused by the front end | by design: work on `dev` ([benchmark protocol](../learn/benchmark-protocol.md)) |

## What was not run

| not run | why |
|---|---|
| `pip install -e .` and the extras | nothing was installed; the commands ran from the copy's root |
| `make list`, `make test`, `make run`, `make bench` | `make test` needs `pytest`; the others need the same setup as the commands above or a server. See [Make targets](../reference/make-targets.md) |
| the server, any campaign, any planner that needs a language model | they need robot_agent, a server and a model |
