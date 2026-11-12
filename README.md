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
make run ROBOT=home PORT=8121                        # a second one (home needs the household package installed)
make terminate PORT=8121                            # stops only the instance started on that port (pid file)
make bench ROBOT=factory SUITE=protocol ARGS="--tasks 3 --seeds 1 --arms A,B"
make test
```

| domain | what | worlds | profiles |
|---|---|---|---|
| `factory` | a data-driven factory floor: zones, benches, bins, a lockable cabinet, a forklift lane, one arm and gripper (all in this repo) | `assembly_hall`, `small_workshop` | `real`, `ideal`, `stress` |
| `home` | a thin wrapper over the frozen household simulator package (imported, not copied); "not available" when it is not installed | its houses | its profiles |

Layout: `symbolic_robot/` the core and the domains, `bench/` the benchmark package (one-way dependency on the core), `docs/`, `tests/`.
Start with [docs/architecture.md](docs/architecture.md); to add a domain read [docs/domains.md](docs/domains.md); for suites [docs/bench.md](docs/bench.md).

## Install

Python >= 3.10. `pip install -e .` (core: pyyaml only). Extras: `[server]` (fastapi, uvicorn), `[bench]` (websockets), `[test]`.
The server needs robot_agent with its `ROBOT_AGENT_ROS=off` switch (the Makefile sets it) on `PYTHONPATH` or via `ROBOT_AGENT_DIR`.
Machine-specific values (`PY`, `ROBOT_AGENT_DIR`) go in `env.local.mk` (not committed). Everything here is simulation: no ROS, no sensors, no real robot.

## Using it

* **Benchmark backend:** `make run ...` starts it by hand (`make status`, `make logs`, `make terminate`); `make bench` starts and stops its own.
  The scripted person answers the robot's questions through `POST /agent/listen/<id>` (`--ask-mode headless`, the only mode).
* **Planner:** the server exposes robot_agent's API (`/ws/agent`, `/skill/<name>`, `/agent/sim_world/get` for the truth, `/agent/sim_command/send` for `state, truth, reset, load, move_object, spawn`).
* **Experiments:** `python -m bench run --domain factory --suite protocol ...` starts its own server on a free test port, runs the arms on the same tasks and seeds, and writes episodes, a summary and a report.
