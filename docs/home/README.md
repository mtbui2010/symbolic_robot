# Household simulator and benchmark (merged from two repositories)

Both parts came into this repository with their history on 2026-11-13 ([../migration_home.md](../migration_home.md)). Their documents keep the old
wording and paths; each file that starts a set carries a note that maps them.

| part | code | docs | tests |
|---|---|---|---|
| the household simulator (frozen, tag `home-sim-freeze-r19`): world, skills, failure model, profiles, simulated user, safety monitor, robot_agent pack | `symbolic_robot/domains/home/` | [sim/README.md](sim/README.md), rules in [sim/CLAUDE.md](sim/CLAUDE.md) (architecture, world, skills, failure model, calibration, ...) | `tests/home/sim/` |
| HomeLoop-Bench: task data, runner, planners, metrics, robot_agent adapters, data tools, LoRA tools, experiments log | `bench/suites/home/` (data in `bench/suites/home/data/`, tools in `bench/suites/home/tools/`) | [bench/README.md](bench/README.md), rules in [bench/CLAUDE.md](bench/CLAUDE.md), [experiments log](bench/experiments.md), [CLI](bench/cli.md), [runner](bench/runner.md), [datasheet](bench/datasheet.md) | `tests/home/bench/` |
| recorded household runs (history) | `results/live_smoke/`, `results/r4a/` | [bench/live_smoke.md](bench/live_smoke.md) | |
| behaviour baselines of the merge | `tests/home/parity/` | | `tests/test_home_baseline.py` |

Commands: `make bench ROBOT=home SUITE=planners | run | compare | report ARGS="..."`, or `python -m bench.suites.home.cli <subcommand>` for all of them.
Licences differ per part: see the README of the repository root.
