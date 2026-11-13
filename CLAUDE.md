# symbolic_robot

One engine for SYMBOLIC simulated robots: skills do not run for real, each returns an outcome drawn from declared probabilities over a small symbolic world.
Scope: this repo runs BENCHMARKS (the server is the benchmark's backend, not a live demo launcher; live demos live in other repos).
Domains (factory, home, ...) plug in; benchmark suites live in a separate package `bench/` that depends on the engine, never the other way.
This is the ONE repository for the household simulator (`domains/home/`) and its benchmark (`bench/suites/home/`): the earlier standalone repositories are not used any more ([docs/migration_home.md](docs/migration_home.md)).
Docs: [architecture](docs/architecture.md), [domains](docs/domains.md) (how to add one), [bench](docs/bench.md), [home](docs/home/README.md) (the household simulator and benchmark docs), [CHANGELOG](docs/CHANGELOG.md).

## Rules
1. **Generality.** No fact about a robot, domain, language or benchmark in the core. Facts are declared data (YAML, with a `source` label) with a safe default that does nothing: a missing hook or file means the feature is absent, not guessed.
2. **Modularity.** A domain or option is a module that registers into the core (`registry`, `BaseDomain`, `Suite`). Layers: core (`symbolic_robot/*.py`) -> domains (`symbolic_robot/domains/<name>/`) -> server glue (`server*.py`, `cli.py`); `bench/` depends on all of them, none of them on `bench/`. Functions <= 80 lines, files <= 600 lines; the limits do not grow (`tests/size_baseline.json` lists justified exceptions, now none). A refactor must show identical behaviour (the replay parity, `tests/parity/`).
3. **robot_agent** is imported only in `server.py`, `server_skills.py` and in a domain's robot_agent pack (`domains/<name>/configs/`, robot_agent's own plug-in format); `bench/` talks to servers over HTTP only, with one moved exception: the home planners' two adapter files (`bench/suites/home/planners/robot_agent_*.py`) import it inside functions to drive its loops in process. Never edit robot_agent; engine problems are reported, not worked around.
4. **Frozen things stay untouched:** the household simulator `symbolic_robot/domains/home/` (everything except `domain.py`) is frozen since tag `home-sim-freeze-r19`: no behaviour change (tests/test_home_baseline.py and `tests/home/sim/test_freeze_r19.py` pin it); a deliberate change needs a new freeze tag and a CHANGELOG line. Scoring rules of `bench/suites/home/` change only with a documented round. Never read the household test split (`bench/suites/home/data/tasks/test.jsonl`) outside the benchmark's own protocol. Recorded results of other repositories are read-only data and are not copied here (the household history under `results/live_smoke`, `results/r4a` came with the merge).
5. **No private names** (projects, customers, companies, robots) anywhere; `tests/test_layering.py` scans the repo. The one named exception is the later-step plan file `docs/migration_<sibling simulator>.md`, to be deleted before publishing.
6. **Deterministic by seed:** a draw depends on (seed, key, n-th use) or on (seed, skill, arguments, n-th call), SHA-256 based; no wall clock, no `hash()`.
7. Judge / scoring code (success from the truth, distance, paired tests) lives only in `bench/`. The evaluated system never imports `bench`.
8. Keep this file short. Commit locally with messages that say what changed and why; no push.

## Test
`make test` (pytest, about 4 min with the household tests; `make test ROBOT=home` runs those alone; the server tests need robot_agent and skip when it is absent).
Parity with the earlier simulators: `python tests/parity/factory_replay.py <recorded results dir>` (docs/architecture.md).
