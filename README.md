# symbolic_robot

> **Scope: benchmark runs only. This repo is not for live demos.** The server below is a headless backend so the benchmark runner can
> drive a simulated robot through `robot_agent`. It has no map picture, no voice dialogue and no display pacing; live use belongs to
> the live launchers kept elsewhere. Do not add live features here.

A shared engine for **symbolic simulated robots**. A skill does not move anything: it checks the preconditions on a small symbolic world,
draws its outcome (success, or a failure with a code) from declared probabilities, applies the effect, advances a simulated clock and returns
the result together with a hidden `truth` record. The same engine serves different **domains** and is served to a planner
(robot_agent) through one headless server.

```
python -m symbolic_robot list                        # domains, floors / houses, profiles
make run ROBOT=factory                               # background benchmark backend on port 8091 (headless)
make run ROBOT=home PORT=8121                        # a second one (the household simulator is part of this repo)
make terminate PORT=8121                            # stops only the instance started on that port (pid file)
make bench ROBOT=factory SUITE=protocol ARGS="--tasks 3 --seeds 1 --arms A,B"
make bench ROBOT=home SUITE=planners                  # the household benchmark: planners | run | compare | report
make bench ROBOT=home SUITE=run ARGS="--planner oracle --split dev --limit 20 --llm fake"
make test
```

| domain | what | worlds | profiles |
|---|---|---|---|
| `factory` | a data-driven factory floor: zones, benches, bins, a lockable cabinet, a forklift lane, one arm and gripper (all in this repo) | `assembly_hall`, `small_workshop` | `real`, `ideal`, `stress` |
| `home` | the household simulator (houses, rooms, furniture, a person, a safety monitor; frozen since `home-sim-freeze-r19`), merged here with its history; docs in [docs/home](docs/home/README.md) | 8 houses, e.g. `senior_flat`, `studio_flat`, `family_house` (`python -m symbolic_robot list`) | `ideal`, `real`, `stress` |

Layout: `symbolic_robot/` the core and the domains (`domains/factory/`, `domains/home/`), `bench/` the benchmark package (one-way dependency on the core; `suites/factory/`, `suites/home/` with the household task data, planners and tools), `docs/` (`docs/home/` for the household parts), `results/` (recorded household runs `live_smoke`, `r4a`; new runs are not committed), `tests/`.
Start with [docs/architecture.md](docs/architecture.md); to add a domain read [docs/domains.md](docs/domains.md); for suites [docs/bench.md](docs/bench.md).

## Install

Python >= 3.10. `pip install -e .` (core and the household simulator: pyyaml only). Extras: `[server]` (fastapi, uvicorn), `[bench]` (websockets), `[test]`.
The household benchmark's robot_agent planners need robot_agent (and embodiplan) importable; `python -m bench run --domain home --suite planners` and the `oracle` / `naive` planners do not.
The server needs robot_agent with its `ROBOT_AGENT_ROS=off` switch (the Makefile sets it) on `PYTHONPATH` or via `ROBOT_AGENT_DIR`.
Machine-specific values (`PY`, `ROBOT_AGENT_DIR`) go in `env.local.mk` (not committed). Everything here is simulation: no ROS, no sensors, no real robot.

## Using it

* **Benchmark backend:** `make run ...` starts it by hand (`make status`, `make logs`, `make terminate`); `make bench` starts and stops its own.
  The scripted person answers the robot's questions through `POST /agent/listen/<id>` (`--ask-mode headless`, the only mode).
* **Planner:** the server exposes robot_agent's API (`/ws/agent`, `/skill/<name>`, `/agent/sim_world/get` for the truth, `/agent/sim_command/send` for `state, truth, reset, load, move_object, spawn`).
* **Experiments:** `python -m bench run --domain factory --suite protocol ...` starts its own server on a free test port, runs the arms on the same tasks and seeds, and writes episodes, a summary and a report.

## Licences

This repository merges two projects that were licensed separately. Each part keeps its own text, unchanged:

| part | where | licence |
|---|---|---|
| the engine, the factory domain, the generic benchmark front end | `symbolic_robot/*.py`, `symbolic_robot/domains/factory/`, `bench/*.py`, `bench/suites/factory/` | MIT, `LICENSE` (root; it covers only these files: the parts below keep their own licence) |
| the household simulator (code, house and profile data) | `symbolic_robot/domains/home/` | Apache-2.0, `symbolic_robot/domains/home/LICENSE` |
| the household benchmark (code) | `bench/suites/home/` | Apache-2.0, `bench/suites/home/LICENSE` |
| the household task data (`bench/suites/home/data/tasks/*.jsonl`, `data/llm_cache/*.jsonl`) | `bench/suites/home/data/` | Apache-2.0 for the English texts, Korean templates, goals and labels; the Korean text written by the EXAONE 3.5 model is NOT Apache-2.0 (research use only, no training of other models on it): read `bench/suites/home/LICENSE-DATA` and `NOTICE` before using or redistributing the data |
| citation of the household benchmark | `bench/suites/home/CITATION.cff` | |

`LICENSE-DATA`, `NOTICE` and `CITATION.cff` are the standalone benchmark's files word for word, so they name the old paths: read
`homeloop_bench/data/...` as `bench/suites/home/data/...` ([docs/migration_home.md](docs/migration_home.md) has the full mapping).
`tests/home/bench/test_licence.py` still checks that the licence statements match the data.
