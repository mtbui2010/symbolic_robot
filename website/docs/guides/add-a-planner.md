---
sources:
  - bench/suites/home/planners/base.py
  - bench/suites/home/planners/__init__.py
  - bench/suites/home/env.py
  - bench/suites/home/runner.py
  - bench/suites/home/cli.py
verified_at: a5cc7a4943aa
---

# Add a planner

!!! abstract "In this page"
    You write two small planners outside the repository, run them on the household benchmark with `--planner module:Class`, and compare them against `oracle`. The first, `GiveUp`, is the floor planner of the framework guide [Benchmark a planner](https://mtbui2010.github.io/robot_agent/guides/benchmark-a-planner/); it was run again for this page. The second, `Walker`, is a `StepPlanner` that reads `obs.places`.
    The guide ends with a `compare` against `oracle`. All runs are 20-task smoke runs on a copy of commit `a5cc7a4943aa`, 2026-11-19, offline: they show that the plug-in works, they are not results. You need `pyyaml` and `websockets` ([Getting started](../start/getting-started.md)). No language model is used.

## What the benchmark asks of a planner

A planner is a class with a `name`, a `privileged` flag and a `run(env)` method:

```python
@runtime_checkable
class Planner(Protocol):
    name: str
    privileged: bool                     # True: may read env.truth (oracle, naive only)

    def run(self, env) -> None: ...
```

Source: [`planners/base.py` L31-L36](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/planners/base.py#L31-L36). `run(env)` plays one episode through an `EpisodeEnv` and ends it with `env.finish(status, say)`, where the status is `done`, `refuse` or `give_up`. The benchmark owns the world, the skills, the person, the budgets and the judge ([Planner interface](../modules/planner-interface.md), [Episode env and judge](../modules/episode-env-and-judge.md)).

Most planners do not write `run`. `StepPlanner` loops: observe, call your `act(obs)`, run the call it returns. You return a `ToolCall(skill, args)` or a `Finish(status, say, reason)`. `say` is what the robot tells the user; `reason` is a status note that is not said. The base class has `privileged = False` and `needs_llm = False`. `PlanPlanner` is the other shape: `plan(obs)` returns a list of calls and `run` executes it.

A plain name from the registry needs an entry in `planners/__init__.py`. A planner of your own does not: a name of the form `package.module:ClassName` is loaded with `importlib` at run time. See [Planners as plugins](../learn/planners-as-plugins.md) for why the benchmark is built this way.

## Step 1: the floor planner `GiveUp`

Save this as `giveup_planner.py` in a folder outside the copy, for example `plug/`:

```python
from bench.suites.home.env import Finish
from bench.suites.home.planners.base import StepPlanner


class GiveUp(StepPlanner):
    """A floor baseline: ends every episode at once with 'give_up'."""
    name = "giveup"
    description = "gives up at once"

    def act(self, obs):
        return Finish("give_up", reason="floor baseline")
```

Run it with the folder on `PYTHONPATH`, from the root of the copy:

```text
$ PYTHONPATH=plug python -m bench run --domain home --suite run --planner giveup_planner:GiveUp --split dev --limit 20 --seeds 2 --profile real --out out/GiveUp
household benchmark: python -m bench.suites.home.cli run --planner giveup_planner:GiveUp --split dev --limit 20 --seeds 2 --profile real --out out/GiveUp
[run] giveup_planner:GiveUp 40 episodes in 0.3s wall -> out/GiveUp
{"false_success": 0.0, "goal_condition_success": 0.070175, "help_rate": 0.0, "n_episodes": 40, "n_error": 0, "rejection_rate": 0.0, "smoke": true, "success": 0.0, "success_ci95": [0.0, 0.087622]}
```

Three things to see:

- The summary records the planner as the spec, `giveup_planner:GiveUp` (`make_planner` overwrites `name` with the name you asked for). The run folder is named by you.
- `give_up` is not the right status for a task that must be refused, so the rejection rate is 0.0. Success is 0.0: a floor.
- `goal_condition_success` is 0.07, not 0, so "gives up at once" does not score exactly zero on this measure. A floor shows what doing nothing scores.

## Step 2: a planner that reads `obs.places`

`env.observe()` gives your planner an `Observation`. Its `places` field is a tuple of `PlaceView` records (`id`, `name`, `room`, `kind`, `openable`, aliases), sorted by place id. It also has `people`, `memory` (what the robot expects to find where), `robot`, `last` (the last call's result), `step` (calls made so far), `calls_left` and `time_left_s`. The task text and the hidden goal are not for you: `task_text` is the instruction the robot heard, and the goal raises an error (step 3).

`Walker` drives to the first two places and then gives up. It is not a good planner. It shows how a planner reads the observation and builds calls:

```python
from bench.suites.home.env import Finish, ToolCall
from bench.suites.home.planners.base import StepPlanner


class Walker(StepPlanner):
    """Drives to the first two places of the house, then gives up. It reads only what the robot can see."""
    name = "walker"
    description = "visits two places, then gives up"

    def act(self, obs):
        if obs.step < 2 and obs.places:
            return ToolCall("move", {"target": obs.places[obs.step].id})
        return Finish("give_up", reason="walked, then stopped")
```

The skill `move` takes the argument `target`, a place id (the table of skills is in the prompts module, `TOOLS`; see [Home skills](../modules/home-skills.md)). Run it:

```text
$ PYTHONPATH=plug python -m bench run --domain home --suite run --planner walker_planner:Walker --split dev --limit 20 --seeds 2 --profile real --out out/Walker
household benchmark: python -m bench.suites.home.cli run --planner walker_planner:Walker --split dev --limit 20 --seeds 2 --profile real --out out/Walker
[run] walker_planner:Walker 40 episodes in 0.4s wall -> out/Walker
{"false_success": 0.0, "goal_condition_success": 0.052632, "help_rate": 0.0, "n_episodes": 40, "n_error": 0, "rejection_rate": 0.0, "smoke": true, "success": 0.05, "success_ci95": [0.008881, 0.236131]}
```

Two of 40 episodes succeeded (0.05). Counting the failed episodes with the script on [Read a result](read-a-result.md):

```text
38 of 40 episodes did not succeed
status: {'give_up': 38}
kind: {'feasible': 30, 'clarify': 6, 'refuse': 2}
failed call codes: {'hw_fault': 2, 'timeout': 2, 'blocked': 1}
```

Moving costs simulated time and can fail like any skill: the codes above are the simulator's failure codes, injected by the `real` profile ([glossary](../reference/glossary.md#failure-code)).

## Step 3: what a non-privileged planner may not read

A planner that is not privileged gets `None` from `env.truth`, and `env.goal` raises `PermissionError("the goal is hidden from non-privileged planners")` ([`env.py` L276-L290](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/env.py#L276-L290)). Do not set `privileged = True` to get around this: only `oracle`, `naive` and one diagnostic variant are privileged, and a number from your planner would stop being comparable with the others. Do not read the private attributes of the env either; the benchmark cannot stop you, but the record is then not comparable.

This is what a crash looks like. `Peeker` is wrong on purpose:

```python
class Peeker(StepPlanner):
    """Wrong on purpose: a non-privileged planner that reads the hidden goal."""
    name = "peeker"

    def act(self, obs):
        self.env.goal
        return Finish("done")
```

```text
$ PYTHONPATH=plug python -m bench run --domain home --suite run --planner peeker_planner:Peeker --split dev --limit 20 --seeds 2 --profile real --out out/Peeker
household benchmark: python -m bench.suites.home.cli run --planner peeker_planner:Peeker --split dev --limit 20 --seeds 2 --profile real --out out/Peeker
[run] peeker_planner:Peeker 40 episodes in 0.3s wall -> out/Peeker
40 of 40 episodes crashed (status error, {'PermissionError': 40}); the scores are not a planner result
{"false_success": 0.0, "goal_condition_success": 0.070175, "help_rate": 0.0, "n_episodes": 40, "n_error": 40, "rejection_rate": 0.0, "smoke": true, "success": 0.0, "success_ci95": [0.0, 0.087622]}
```

The exit status was 4. Any other exception in your planner is a failed episode with status `error`; the run goes on and the files are written. When more than 5 % of the episodes crash the command exits with 4 and says the scores are not a planner result. (Two exceptions stop the whole run instead: an `LLMError` and an `ImportError` raised while the episode runs end with exit 3 and no summary, so that an infrastructure failure never looks like a score of 0.)

## Step 4: compare against the oracle

```text
$ python -m bench run --domain home --suite compare out/oracle out/Walker
household benchmark: python -m bench.suites.home.cli compare out/oracle out/Walker
paired McNemar test on (task, seed): A = out/oracle  B = out/Walker
| n_pairs | success A | success B | b (A ok, B fail) | c (A fail, B ok) | statistic | p | method |
|---|---|---|---|---|---|---|---|
| 40 | 0.8250 | 0.0500 | 31 | 0 | 29.0323 | 0.0000 | chi2_continuity |

2 seeds per task: seeds of one task are correlated, so use the task-level tests below for claims (docs/metrics.md).
| test | n | statistic | p |
|---|---|---|---|
| McNemar on per-task majority (exact_binomial) | 20 tasks | 0.0000 | 0.0002 |
| task sign-flip permutation (10000 perms) | 20 tasks | 15.5000 | 0.0001 |
```

`out/oracle` is the run of [Run a benchmark](run-a-benchmark.md). Against `GiveUp` the same command gave 33 pairs where only the oracle succeeded, none the other way, statistic 31.0303, p printed as `0.0000` (`chi2_continuity`), and task-level p of 0.0001 for both tests. The oracle is a privileged reference, so "worse than the oracle" is the expected answer for every honest planner: the interesting comparison is against `naive`, or against another planner of the same kind. Read the block as on [Read a result](read-a-result.md) and [Run a benchmark](run-a-benchmark.md): this is a smoke run, not a result.

**The task works when:** `--planner giveup_planner:GiveUp` runs 40 episodes with exit 0 and `compare` against `oracle` prints the block above.

## Common problems

| symptom | cause | what to do |
|---|---|---|
| a traceback ending in `ModuleNotFoundError: No module named 'nosuchmod'`, exit 1 (run with `--planner nosuchmod:X`) | current behaviour: `planner_class` imports a spec's module without catching the error, before any episode | put your folder on `PYTHONPATH` and check the spec `package.module:Class` |
| `unknown planner ...` with the list of known names and the hint `or package.module:ClassName` | a name that is neither a registry key nor a spec (no colon) | write the spec with the colon |
| `planner <name> needs --llm URL or --llm fake`, exit 2 | your class has `needs_llm = True` and you gave no `--llm` | give `--llm`, or set `needs_llm = False` |
| the planner ran and never ended the episode | `StepPlanner` ends only when `act` returns a `Finish` or the budget is used up; a planner that returns without finishing is ended as `give_up` with reason `planner returned without finishing` | return a `Finish` |
| exit 4, scores not a planner result | more than 5 % of the episodes crashed | read `errors_by_type` in `summary.json`; often a `PermissionError` as in step 3 |
| two runs of your planner differ | something in your planner is not seeded | draw randomness from a fixed seed; the benchmark's own draws are seeded ([Determinism](../learn/determinism.md)). A language-model planner is exactly repeatable only from a cache |
| `robot_agent not importable (add it to PYTHONPATH)` | you asked for a `robot_agent:*` name | those need robot_agent; a spec of your own does not |

## What was not run

| not run | why |
|---|---|
| a planner that calls a language model (`needs_llm = True`, `ask_json`, `step_check`) | no model was called; see [LLM baselines](../modules/llm-baselines.md) |
| a `PlanPlanner` | only `StepPlanner` was run; its contract is read from the code ([Planner interface](../modules/planner-interface.md)) |
| a planner added to the registry in `planners/__init__.py` | not needed for a spec; not tried |
| a full run | 20-task smoke runs only |

Next: [Add a domain](add-a-domain.md).
