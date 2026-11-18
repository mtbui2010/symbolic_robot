---
sources:
  - bench/suite.py
  - bench/suites/registry.py
  - bench/suites/factory/__init__.py
  - bench/cli.py
  - bench/protocol.py
  - bench/campaign.py
  - tests/test_bench.py
verified_at: a5cc7a4943aa
---

# Add a suite

!!! abstract "In this page"
    You write a campaign suite for a domain: a `Suite(...)` with `tasks`, `answer`, `distance`, `analyze`, a `protocol` file and `delegate=None`. You register its module, preview it with `--dry-run`, check its protocol hash, and see it in `python -m bench list`.
    The suite here is a small one for the pantry domain of [Add a domain](add-a-domain.md). Its hooks were called offline, and `list`, `--dry-run` and `verify` were run, on a copy of commit `a5cc7a4943aa`, 2026-11-19. **A full campaign was not run**: it starts a server and needs robot_agent and a language model. You need `pyyaml` and `websockets`.

A **campaign suite** drives a planner through a running server and compares **arms**, named sets of run options, on the same tasks. A **delegate suite** is a program of its own and fills only `delegate`; the household entries are of that kind ([the bench front end](../modules/bench-front-end.md), [glossary](../reference/glossary.md#suite)). This guide writes the first kind, with `delegate=None`. The factory suites are the worked example ([Factory suites](../modules/factory-suites.md)).

## Step 1: write the protocol file first

A campaign suite has a pre-registered protocol: a text file, written before the first episode. Its SHA-256 is written to `PROTOCOL_SHA256` in the results folder at the start of the first run, and a later run into that folder refuses a changed protocol ([glossary](../reference/glossary.md#pre-registration)). Write the question, the tasks, the arms and the decision rule. `pantry_suite.md`:

```text
# Pantry suite: protocol (written before the first episode)

Question: does the arm "B" fetch the cup on more tasks than the arm "A"?
Tasks: 4, generated from the seed. Repeats: 2. Arms: A, B.
Decision rule: B counts as better only if it wins more tasks than it loses.
```

## Step 2: write the hooks and the `Suite`

The fields of `Suite` are on [the bench front end](../modules/bench-front-end.md#suite-data-plus-hooks). The ones a campaign suite fills:

| field | what you give | in the example |
|---|---|---|
| `domain`, `name`, `description` | the key `domain/name` and the line `list` prints | `pantry`, `fetch` |
| `arms`, `default_arms` | arm name to the run options sent with each run; the arms used when `--arms` is empty | `A` and `B` |
| `tasks` | `(world, n, task_seed)` gives a list of task dicts, each with `id`, `prompt`, `kind`, `obj_id`, `dest`; `policy` is optional | four tasks, seed-independent |
| `answer` | the simulated person: `(task, question, n_where)` gives `(text, kind, grounded)` | always "It is on shelf a." |
| `distance` | the call log gives the metres travelled | counts successful `go` calls (a stand-in) |
| `analyze` | a results folder gives a summary dict; it must be able to run on a reduced run | counts the lines of `episodes.jsonl` |
| `report` | folders give markdown tables (optional; `messy_fix` has none) | none |
| `protocol` | the path of the protocol file | `pantry_suite.md` |
| `defaults` | `tasks`, `seeds`, `task_seed`, `profile`, `world` | 4, 2, 7, `real`, `small` |
| `server_args`, `server_env` | extra arguments and environment of the server the front end starts | none |

The factory suites fill the same fields through one helper, `_suite` ([`bench/suites/factory/__init__.py` L37-L43](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/factory/__init__.py#L37-L43)):

```python
def _suite(name, description, arms, default_arms, tasks_fn, analyze, report, protocol, **defaults) -> Suite:
    return registry.register(Suite(
        domain="factory", name=name, description=description, arms={a: ARMS[a] for a in arms}, default_arms=tuple(default_arms),
        tasks=lambda world, n, seed: tasks_fn(world or WORLD, n, seed), answer=answer_for, distance=distance, analyze=analyze, report=report,
        protocol=protocol, defaults={"tasks": 36, "seeds": 2, "task_seed": 7, "profile": "real", "world": WORLD, **defaults},
        server_args=SERVER_ARGS, server_env=SERVER_ENV))
```

The pantry suite, `pantry_suite.py`:

```python
"""A tiny campaign suite for the pantry domain."""
from pathlib import Path

from bench.suite import Suite
from bench.suites import registry

HERE = Path(__file__).parent


def tasks(world, n, seed):
    return [{"id": f"t{i:02d}", "prompt": "Bring the cup to shelf b.", "kind": "fetch", "policy": "knows",
             "obj_id": "cup", "dest": "b"} for i in range(n)]


def answer(task, question, n_where):
    return "It is on shelf a.", "source", "a"       # (text, kind, grounded)


def distance(log):
    return float(sum(1 for e in log if e.get("ok") and e.get("skill") == "go"))


def analyze(out):
    n = len((Path(out) / "episodes.jsonl").read_text().splitlines())
    return {"episodes": n}


registry.register(Suite(
    domain="pantry", name="fetch", description="fetch the cup: arms A and B, 4 tasks x 2 repeats (16 episodes)",
    arms={"A": {"ask_source": 0}, "B": {"ask_source": 1}}, default_arms=("A", "B"),
    tasks=tasks, answer=answer, distance=distance, analyze=analyze, protocol=HERE / "pantry_suite.md",
    defaults={"tasks": 4, "seeds": 2, "task_seed": 7, "profile": "real", "world": "small"}))
```

This is a skeleton to show the hooks. It is not a sensible benchmark: the tasks are all alike, and `ask_source` is an option of robot_agent's engine, not of the pantry domain. `delegate` is left at its default, `None`, which makes it a campaign suite.

Called offline, the hooks behave as the front end expects:

```text
pantry/fetch True t00 4 True ('It is on shelf a.', 'source', 'a') 1.0
```

The columns are the suite key, whether the protocol file exists, the first task id, the number of tasks, whether the default arms are among the arms, the answer, and the distance of a one-call log. These are the same checks as `test_suites_registered_with_their_protocols` makes for the three factory suites ([`tests/test_bench.py` L45](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/tests/test_bench.py#L45)): a protocol file that exists, tasks, answer, distance, analyze, and default arms inside the arms. That test was not run under `pytest`.

## Step 3: add the module to `registry.MODULES`

`bench/suites/registry.py` holds a dictionary keyed by `(domain, name)`. A suite module calls `register(Suite(...))` when it is imported, and `MODULES` lists the modules to import:

```python
MODULES = ("bench.suites.factory", "bench.suites.home.register")


def register(s: Suite) -> Suite:
    _SUITES[(s.domain, s.name)] = s
    return s


def load_all() -> None:
    for m in MODULES:
        importlib.import_module(m)
```

Source: [`bench/suites/registry.py` L9-L19](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/registry.py#L9-L19). For a suite in this repository you add your module's dotted name to that tuple. For the runs on this page the repository was not edited: a three-line launcher added `pantry_suite` to `registry.MODULES` and then called the front end:

```python
import sys
from bench.suites import registry
from bench.cli import main

registry.MODULES = (*registry.MODULES, "pantry_suite")
sys.exit(main(sys.argv[1:]))
```

## Step 4: `list`, then `--dry-run`

```text
$ python run_suite.py list | grep pantry
  pantry/fetch: fetch the cup: arms A and B, 4 tasks x 2 repeats (16 episodes)
```

`run_suite.py list` printed the three factory suites, the four household entries and the new one, sorted: eight lines after the header. `--dry-run` prints the plan line and returns before it hashes the protocol, starts a server or creates a folder:

```text
$ python run_suite.py run --domain pantry --suite fetch --out out/p --dry-run
suite pantry/fetch: world small, profile real, tasks 4, repeats 2, arms A,B -> out/p
```

The exit status was 0 and `out/` did not exist afterwards. The numbers come from your `defaults`.

## Step 5: check the protocol hash

`bench/protocol.py` has `register(out, protocol)`, which writes the hash on the first run and checks it on a later one, and `verify(out, protocol)`. Run offline on a scratch folder, with the front end's `verify` command:

```text
$ python run_suite.py verify --domain pantry --suite fetch out/pr
protocol hash matches: out/pr
```

The folder `out/pr` held `PROTOCOL_SHA256` from `protocol.register`. After one line was added to `pantry_suite.md` the same command printed `protocol hash DOES NOT match (or is missing): out/pr` and exited 1; with the file restored it matched again and exited 0. A real run into a folder whose protocol changed stops with `the protocol changed after its hash was recorded ... restore <file> or start a new results folder`; `--allow-protocol-change` overrides it. That message and the stop are in the code ([`bench/protocol.py` L15-L28](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/protocol.py#L15-L28)); the stop was not triggered by a campaign run.

**The task works when** `python -m bench list` shows `pantry/fetch`. In this repository that needs the edit of step 3; here it was shown through the launcher.

## What a real run would do (not run)

`python -m bench run --domain pantry --suite fetch --out ...` would register the protocol hash, start `python -m symbolic_robot run --robot pantry --port <p> --run-dir ...` as a child process, play every (task, repeat, arm) against it, stop the server and call `analyze` ([Campaign runner](../modules/campaign-runner.md)). Two things make this fail for a domain you registered only in a script:

- the child process is a fresh interpreter, so it must find the domain by an entry point or by `registry.BUILTIN` (see [Add a domain](add-a-domain.md));
- the server needs robot_agent importable, and the planner under test needs a language model.

Neither was available, so no campaign was run and no `episodes.jsonl`, `detail/` or `summary.json` was written. The numbers a campaign produces are computed by [Campaign statistics](../modules/campaign-statistics.md).

## Common problems

| symptom | cause | what to do |
|---|---|---|
| `KeyError: 'no suite pantry/nope; known: ...'` | the suite is not registered, or its module is not in `MODULES` | add the module; the error lists the known suites |
| `unknown arguments for pantry/fetch: --bogus`, exit 2 | an option the generic parser does not know (run) | use the options of `python -m bench run` |
| `--dry-run` prints a plan for an unknown arm (`--arms Z`), exit 0 | arms are checked only when the campaign runs | check arm names yourself; a real run stops with `unknown arm(s) ... known: A, B` |
| `the protocol changed after its hash was recorded` | the protocol text was edited after the first run into this folder | restore it, or use a new folder |
| `analysis not computed (...); episodes.jsonl is complete` | a reduced run lacks an arm the analysis compares | run the missing arm, then `python -m bench analyze` |
| `ModuleNotFoundError: No module named 'websockets'` | even `list` imports it | install the extra `bench` |

## What was not run

| not run | why |
|---|---|
| any campaign: `run` without `--dry-run`, the server start, `analyze`, `report` | needs robot_agent, a server and a language model |
| `make bench ROBOT=pantry SUITE=fetch` | the same; and the domain is not built in |
| the test `test_suites_registered_with_their_protocols` under `pytest` | `pytest` is not installed; its checks were repeated by hand for the pantry suite |
| a suite with a `report` hook, `server_args` or `server_env` | the example has none; the factory suites show them |

Back to [Run a benchmark](run-a-benchmark.md).
