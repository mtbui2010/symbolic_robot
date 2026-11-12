# symbolic_robot

One engine for SYMBOLIC simulated robots: skills do not run for real, each returns an outcome drawn from declared probabilities over a small symbolic world.
Domains (factory, home, ...) plug in; benchmark suites live in a separate package `bench/` that depends on the engine, never the other way.
Docs: [architecture](docs/architecture.md), [domains](docs/domains.md) (how to add one), [bench](docs/bench.md), [CHANGELOG](docs/CHANGELOG.md).

## Rules
1. **Generality.** No fact about a robot, domain, language or benchmark in the core. Facts are declared data (YAML, with a `source` label) with a safe default that does nothing: a missing hook or file means the feature is absent, not guessed.
2. **Modularity.** A domain or option is a module that registers into the core (`registry`, `BaseDomain`, `Suite`). Layers: core (`symbolic_robot/*.py`) -> domains (`symbolic_robot/domains/<name>/`) -> server glue (`server*.py`, `cli.py`); `bench/` depends on all of them, none of them on `bench/`. Functions <= 80 lines, files <= 600 lines; the limits do not grow (`tests/size_baseline.json` lists justified exceptions, now none). A refactor must show identical behaviour (the replay parity, `tests/parity/`).
3. **robot_agent** is imported only in `server.py`, `server_skills.py` and in a domain's robot_agent pack (`domains/<name>/configs/`, robot_agent's own plug-in format); `bench/` talks to servers over HTTP only. Never edit robot_agent; engine problems are reported, not worked around.
4. **Frozen things stay untouched:** the household simulator package that the `home` domain wraps (import it, never copy or edit it) and its own benchmark (only delegated to, by subprocess; never read its test split). Recorded results of other repositories are read-only data and are not copied here.
5. **No private names** (projects, customers, companies, robots) anywhere; `tests/test_layering.py` scans the repo. The one named exception is the later-step plan file `docs/migration_<sibling simulator>.md`, to be deleted before publishing.
6. **Deterministic by seed:** a draw depends on (seed, key, n-th use) or on (seed, skill, arguments, n-th call), SHA-256 based; no wall clock, no `hash()`.
7. Judge / scoring code (success from the truth, distance, paired tests) lives only in `bench/`. The evaluated system never imports `bench`.
8. Keep this file short. Commit locally with messages that say what changed and why; no push.

## Test
`make test` (pytest, about 25 s; the server tests need robot_agent, the home tests the household package: each skips when absent).
Parity with the earlier simulators: `python tests/parity/factory_replay.py <recorded results dir>` (docs/architecture.md).
