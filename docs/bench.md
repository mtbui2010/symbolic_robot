# bench: benchmark suites

`bench/` is a separate package with a strictly one-way dependency: `bench -> symbolic_robot`. The core, the domains and the evaluated system
never import it (`tests/test_layering.py`). It holds everything that judges or scores: success from the simulator's truth, distance, paired
sign tests, bootstrap intervals, per-policy tables, the pre-registered protocol hash. It drives a running server over HTTP and WebSocket
exactly as the dashboard does, so what it measures is the planner on the symbolic robot, never the robot's own claim.

```
python -m bench list
make bench ROBOT=factory SUITE=protocol                                  # full: 288 episodes
make bench ROBOT=factory SUITE=protocol ARGS="--tasks 3 --seeds 1 --arms A,B"   # a few tasks, end to end
make bench ROBOT=home SUITE=planners                                     # delegation, see below
python -m bench analyze --domain factory --suite protocol results/factory_protocol
python -m bench report  --domain factory --suite messy results/factory_messy
python -m bench verify  --domain factory --suite protocol results/factory_protocol   # protocol hash still matches
```

`make bench` (and `python -m bench run`) starts its own server on the first free port of `BENCH_PORTS` (default 8120-8129; a busy port is never taken),
waits until it answers, runs the arms, stops it (SIGTERM, then SIGKILL; only the process it started), then analyses. Output in `results/<domain>_<suite>/`
(`results/` is not committed): `tasks.json`, `episodes.jsonl` (one line per episode, the run resumes from it), `detail/<task>_<arm>_<repeat>.json` (dialogue, call log with truth, events, world before and after),
`summary.json`, `report.md`, `PROTOCOL_SHA256`, `_server/` (server log and site folder). Options: `--tasks N --seeds K --seed0 K --arms A,B --only t01,t02 --limit N --task-seed 7 --world W --profile real --env KEY=VALUE --dry-run`.

## Factory suites

| suite | what | episodes | protocol text |
|---|---|---|---|
| `protocol` | three engine options of the planner (ask where the object is, ask again on a miss, search nearer places first); arms A, B, C and the A/A repeat A2; a scripted person who knows, does not know, or first names a wrong place | 36 tasks x 4 arms x 2 repeats = 288 | `bench/suites/factory/protocol.md` |
| `messy` | a messy person (room only, vague, changes mind, partial name, silent); arms A, C, D, A2 | 42 x 4 x 2 = 336 | `messy.md` |
| `messy_fix` | a repair check of three more keys on the 25 tasks that failed; arms A, E, D | 25 x 3 x 2 = 150 | `messy_fix.md` |

Same tasks and simulator seeds for every arm (`seed = task number * 100 + repeat`), the arm order rotates with the task, each episode starts with `reset_world`
(objects in place, robot on its dock, the robot's memory files erased), timeout 420 s wall. The arms are run options sent with each run; the server's environment is arm A.
Needs a local LLM server (the domain's `default_model` on Ollama) and the planner in robot_agent.

**Pre-registration.** Before the first episode the hash of the suite's protocol file is written to `PROTOCOL_SHA256`; a later run into that folder refuses a changed protocol
(`--allow-protocol-change` overrides, and the hash stays the old one). The protocol texts here are adapted from the earlier repository's; the hash of the adapted file is what counts for new results.

**Recorded results of the earlier repository** are not copied. The analysis code reproduces its `summary.json` exactly from its `episodes.jsonl`
(`tests/test_parity_factory.py`, needs `SHOPFLOOR_RESULTS`), and the factory replay reproduces its call logs (`docs/architecture.md`).

## Home: delegation

The household simulator has its own benchmark in its own repository (`homeloop_bench`), which is not moved or imported. `home/<subcommand>` runs
`<python> -m homeloop_bench.cli <subcommand> ARGS` as a subprocess, with `--python` / `PY` an interpreter that has it installed:

```
make bench ROBOT=home SUITE=planners                       # lists the planners: needs no data and no LLM (a safe smoke test)
make bench ROBOT=home SUITE=run ARGS="--planner oracle --split dev --limit 20 --profile ideal --seeds 1"   # --out results/home_run is added
```

The wrapper refuses `--split test` and reads no split itself. Subcommands: `planners`, `run`, `compare`, `report`. `--dry-run` prints the command.

## Adding a suite

Create `bench/suites/<domain>/` with a module that builds `bench.suite.Suite(...)` (arms, `tasks(world, n, seed)`, the simulated person `answer(task, question, n_where)`,
`distance(log)`, `analyze`, `report`, a protocol file) and calls `registry.register`; list the module in `bench/suites/registry.py::MODULES`. Domain data (task generators, the
person's scripts) belongs to the domain; judging belongs here.
