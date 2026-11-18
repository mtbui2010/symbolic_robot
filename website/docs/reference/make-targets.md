---
sources: [Makefile, bench/orchestrate.py, bench/cli.py, symbolic_robot/cli.py]
verified_at: a5cc7a4943aa
---

# Make targets

!!! abstract "In this page"
    - Every target of the `Makefile`, every variable with its default, and the files the targets write.
    - Which targets need robot_agent and which run offline.
    - Real output of `make help`, `make list`, `make bench` (dry run) and `make bench ... SUITE=planners`, and two behaviours of the Makefile that differ from what the command line suggests (F12, F13).

The Makefile has eight targets: `help`, `list`, `run`, `terminate`, `status`, `logs`, `test` and `bench`. It sets `SHELL := /bin/bash`, `.ONESHELL` and `.SILENT`, so each recipe is one shell and the commands are not echoed ([Makefile:43-45](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/Makefile#L43-L45)). It includes an optional, uncommitted file of machine-specific values (for example `PY` and `ROBOT_AGENT_DIR`); the repo's `.gitignore` lists it.

## Variables

| variable | default | used by | meaning |
|---|---|---|---|
| `PY` | `python3` | all | the interpreter |
| `ROBOT` | `factory` | `run`, `test`, `bench` | the domain (`factory` or `home`) |
| `PORT` | `8091` | `run`, `terminate`, `status`, `logs` | the port of the background server |
| `HOST` | `0.0.0.0` | `run` | the address uvicorn listens on (the command line itself defaults to `127.0.0.1`) |
| `PROFILE` | `real` | `run` | `real`, `ideal` or `stress` |
| `SEED` | `0` | `run` | the episode seed |
| `ASK_MODE` | `headless` | `run` | passed as `--ask-mode`; `headless` is the only value that works |
| `DIALOGUE` | `human` | `run` | passed as `--dialogue`: `human` or `sim` |
| `OPTS` | empty | `run` | extra flags, for example `OPTS="--floor assembly_hall"` |
| `RUN_ROOT` | `run` | `run`, `terminate`, `status`, `logs` | the folder for the pid file, the log and the site folder |
| `BENCH_PORTS` | `8120-8129` | `bench` | the range of test ports a campaign may use |
| `SUITE` | empty | `bench` | the suite name |
| `ARGS` | empty | `bench` | extra arguments of `python -m bench run` |
| `ROBOT_AGENT_DIR` | empty | all | a folder added to `PYTHONPATH` so robot_agent can be imported |

Two variables are exported to every recipe: `PYTHONPATH` (the repo, then `ROBOT_AGENT_DIR` if set, then the old value) and `ROBOT_AGENT_ROS=off`, which switches ROS off in robot_agent ([Makefile:32-33](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/Makefile#L32-L33)).

Derived paths: the pid file `run/.server-<PORT>.pid`, the log `run/server-<PORT>.log` and the site folder `run/site-<PORT>` (robot_agent's config folder for that server).

## The targets

| target | needs robot_agent | what it does |
|---|---|---|
| `help` | no | prints the first 15 lines of the Makefile without the leading `#` |
| `list` | no (needs `websockets` for the second command) | `python -m symbolic_robot list` then `python -m bench list` |
| `run` | yes | starts the benchmark backend in the background and waits until it answers |
| `terminate` | no | stops the instance that `run` started on `PORT` |
| `status` | no | says whether that instance runs, and prints its robot snapshot |
| `logs` | no | `tail -n 40 -f` on the log |
| `test` | no | `pytest -q -p no:warnings tests` (see F12) |
| `bench` | depends on the suite | `python -m bench run --domain $(ROBOT) --suite $(SUITE) ...` |

### `run`

In order ([Makefile:54-72](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/Makefile#L54-L72)):

1. Stop with a message if `$(PY)` is not found.
2. Create `RUN_ROOT`. If the pid file names a live process, print "already running" and exit 0.
3. If `ss` shows something listening on `PORT`, refuse: the port belongs to another process.
4. Start `python -m symbolic_robot run --robot ... --host ... --port ... --run-dir run/site-<PORT> --profile ... --seed ... --ask-mode ... --dialogue ... $(OPTS)` with `setsid nohup`, output to the log, pid to the pid file.
5. Poll `http://127.0.0.1:<PORT>/agent/mobile_pose/get` once a second for up to 90 s. If the process dies, print the last 15 log lines and exit 1. If nothing answers in 90 s, exit 1.
6. On success print `up: http://127.0.0.1:<PORT>`; with `HOST=0.0.0.0` it also prints a line with the machine's network address, and it ends with how to stop the instance.

A second instance needs another `PORT`: `make run PORT=8121 ROBOT=home`.

### `terminate`, `status`, `logs`

`terminate` works by pid file only, never by process name. It sends SIGTERM, waits up to 10 s (20 checks of 0.5 s), then SIGKILL, then removes the pid file. With no pid file it says so and, if something listens on the port, names it without touching it. `status` prints `running: pid ..., port ..., site folder ...` and the answer of `/agent/mobile_pose/get`, or `not running`.

### `bench`

With no `SUITE`, `make bench` prints a usage line and exits 1. Otherwise it runs ([Makefile:97-100](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/Makefile#L97-L100)):

```text
$(PY) -m bench run --domain $(ROBOT) --suite $(SUITE) --python $(PY) --ports $(BENCH_PORTS) --out results/$(ROBOT)_$(SUITE) $(ARGS)
```

For a factory suite the front end starts its own server on a free port of `BENCH_PORTS`, plays the campaign, stops the server and analyses ([Campaign runner](../modules/campaign-runner.md)). For a household suite it runs in the same process, with no server, and `--python` and `--ports` are dropped ([The bench front end](../modules/bench-front-end.md)). Results go to `results/<ROBOT>_<SUITE>/`, which git ignores except for the two recorded folders.

## Real output (offline)

All of this was run on a copy of the pinned commit with an interpreter that has pyyaml and websockets; nothing was started.

`make help` (one line, about where machine-specific values go, is left out here):

```text
symbolic_robot: simulated robots (domains) served as the HEADLESS BACKEND OF BENCHMARK RUNS, and the benchmark suites (bench/) that run on them.

  make list                                   domains, floors / houses, profiles, suites
  make run ROBOT=<home|factory> [PORT=8091]   start the benchmark backend in the background and wait until it answers
  make terminate [PORT=8091]                  stop the instance `make run` started on $(PORT) (by its pid file only: never by name)
  make status | logs | test [ROBOT=..] | help
  make bench ROBOT=<domain> SUITE=<name> [ARGS=...]   run a benchmark suite (bench/); starts and stops its own server on a free
                                              test port (BENCH_PORTS, default 8120-8129); results in results/<domain>_<suite>/
  make bench ROBOT=home SUITE=<planners|run|compare|report> [ARGS=...]   the household benchmark, in process (no server): ARGS go to its CLI
  make test [ROBOT=home]                      all tests; ROBOT=home only the household ones

Variables: ROBOT=factory  PORT=8091  HOST=0.0.0.0  PROFILE=real|ideal|stress  SEED=0
  ASK_MODE=headless  DIALOGUE=human|sim  OPTS="--floor assembly_hall"  PY=python3  RUN_ROOT=run
A second instance: make run PORT=8121 ROBOT=home
```

`make bench` with no suite, and two dry runs (`--dry-run` makes the front end print what it would do):

```text
$ make bench
usage: make bench ROBOT=<domain> SUITE=<name> [ARGS=...]   (suites: make list)
$ make bench ROBOT=factory SUITE=protocol ARGS="--tasks 3 --seeds 1 --arms A,B --dry-run"
suite factory/protocol: world assembly_hall, profile real, tasks 3, repeats 1, arms A,B -> results/factory_protocol
$ make bench ROBOT=home SUITE=run ARGS="--planner oracle --split dev --limit 20 --dry-run"
household benchmark: python -m bench.suites.home.cli run --planner oracle --split dev --limit 20 --out results/home_run
```

`make bench ROBOT=home SUITE=planners` lists the planners; the first six lines (the rest are the `robot_agent:*` entries, marked unavailable when robot_agent cannot be imported):

```text
household benchmark: python -m bench.suites.home.cli planners
oracle  privileged reference: re-solves from the true world after every call; retries, waits, asks for help
naive  privileged ablation: the oracle's start-state plan, open loop, no recovery or asking
saycan_like  after SayCan (Ahn et al. 2022): LLM picks one affordance-filtered call per step by index
inner_monologue_like  after Inner Monologue (Huang et al. 2022): step-wise LLM with result and scene feedback
progprompt_like  after ProgPrompt (Singh et al. 2022): one LLM-written program with assert/recover lines
```

`make list` prints the same text as `python -m symbolic_robot list` followed by `python -m bench list` (see [Command lines](cli.md)).

Not run: `make run`, `terminate`, `status`, `logs` (they start or probe a server, which needs robot_agent, fastapi and uvicorn), `make test` (pytest is not installed in the documentation environment), and a real `make bench` campaign. The `test` and `bench` recipes were read, and printed with `make -n`:

```text
$ make -n test ROBOT=home PY=python3
"python3" -m pytest -q -p no:warnings tests -k home
$ make -n test PY=python3
"python3" -m pytest -q -p no:warnings tests 
```

## Two things to know

!!! warning "F12: `make test ROBOT=home` selects by keyword"
    The `test` recipe adds `-k home` when `ROBOT` is not `factory` ([Makefile:94-95](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/Makefile#L94-L95)). `-k` is pytest's keyword expression, not a folder: it keeps the tests whose names, modules or folders contain that word. The comment calls the result "only the household ones". With `ROBOT=factory`, the default, it runs everything, not only factory tests. Any other value is passed to `-k` in the same way.

!!! warning "F13: two different readiness checks"
    `make run` waits for `/agent/mobile_pose/get` ([Makefile:67](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/Makefile#L67)). The bench front end waits for `/agent/sim_world/get` and then sleeps a further 10 s so robot_agent can load its connections ([orchestrate.py:37-48](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/orchestrate.py#L37-L48)). An instance that `make run` reports as up may therefore be a little earlier than the front end would call it ready.

## Failure modes

| symptom | cause | what to do |
|---|---|---|
| `python not found: ...` | `PY` names no interpreter | set `PY=...` on the command line, or in the uncommitted file of machine values |
| `port ... is already in use by another process` | something not started by this Makefile listens there | choose another `PORT` |
| `the server exited; last log lines:` | the process died: often robot_agent is not importable (F4 in [Known pitfalls](known-pitfalls.md)) | read the log; set `ROBOT_AGENT_DIR` |
| `no answer after 90 s` | the server is slow or stuck | `make logs` |
| `make bench` prints the usage line | `SUITE` is empty | pass `SUITE=<name>`; `make list` shows the names |
| `ModuleNotFoundError: websockets` on `make list` | `bench/cli.py` imports the runner, which imports `websockets` | install the `bench` extra |

Next: [Command lines](cli.md), [Server glue](../modules/server-and-cli.md), [Run a benchmark](../guides/run-a-benchmark.md).
