# Migration: the household simulator and benchmark moved into this repository (2026-11-13)

From now on use ONLY `symbolic_robot`. The two standalone repositories are not changed (they stay as a read-only record) and nothing new should be done in them.

## What moved

| from (standalone) | to | notes |
|---|---|---|
| `homeloop_robot/homeloop_robot/` (the simulator package) | `symbolic_robot/domains/home/` | content unchanged except imports and paths; its `__init__.py` is the package's own; the old thin wrapper class is `domains/home/domain.py` |
| `homeloop_robot/tests/` (incl. `golden/`) | `tests/home/sim/` | |
| `homeloop_robot/docs/`, `README.md`, `CLAUDE.md` | `docs/home/sim/` | a note at the top of README / CLAUDE maps old paths |
| `homeloop_robot/LICENSE` | `symbolic_robot/domains/home/LICENSE` | verbatim (Apache-2.0) |
| `homeloop_bench/homeloop_bench/` (package) | `bench/suites/home/` | package data (`data/tasks`, `data/llm_cache`, `planners/*.json|yaml`) moves with it |
| `homeloop_bench/data/quality/` | `bench/suites/home/data/quality/` | |
| `homeloop_bench/tools/` | `bench/suites/home/tools/` | |
| `homeloop_bench/results/` (tracked: `live_smoke`, `r4a`) | `results/` (same relative paths) | `.gitignore` keeps these two folders; the other result folders are not committed |
| `homeloop_bench/tests/` | `tests/home/bench/` | |
| `homeloop_bench/docs/` (incl. `experiments.md`), `README.md`, `CLAUDE.md` | `docs/home/bench/` | |
| `homeloop_bench/LICENSE`, `LICENSE-DATA`, `NOTICE`, `CITATION.cff` | `bench/suites/home/` | verbatim; the README of this repository says which licence covers what |
| `pyproject.toml`, `.gitignore` of both | not carried | their facts (package data, ignore rules, dependencies) are in this repository's own files |
| `homeloop_bench/homeloop_bench/__init__.py` `__version__` | `bench/suites/home/__init__.py` | `0.1.0` |
| the old subprocess delegation (`bench/suites/home/delegate_legacy.py` of the first home wrapper) | removed | `bench/suites/home/register.py` calls the household CLI in process |

## Import and command mapping

| old | new |
|---|---|
| `import homeloop_robot` / `from homeloop_robot import make_episode` | `from symbolic_robot.domains.home import make_episode` |
| `homeloop_robot.<module>` (`world`, `skills`, `profiles`, `oracle`, `configs.backend`, `configs.ra_skills`, ...) | `symbolic_robot.domains.home.<module>` |
| `python -m homeloop_robot.selftest` / `.profiles validate` / `.realism` / `.report` | `python -m symbolic_robot.domains.home.selftest` / ... |
| robot_agent pack name `homeloop_robot` (`RobotView.load("homeloop_robot")`, `load_adapter`) | `symbolic_robot.domains.home` (dotted, like the factory pack) |
| `import homeloop_bench` / `from homeloop_bench.env import EpisodeEnv` | `from bench.suites.home.env import EpisodeEnv` |
| `homeloop_bench.planners.robot_agent_adapter:SageS8nPlanner` | `bench.suites.home.planners.robot_agent_adapter:SageS8nPlanner` |
| `homeloop-bench <sub> ...` or `python -m homeloop_bench.cli <sub> ...` | `python -m bench.suites.home.cli <sub> ...` or `python -m bench run --domain home --suite <sub> ...` (planners, run, compare, report) or `make bench ROBOT=home SUITE=<sub> ARGS=...` |
| `python -m homeloop_bench.data ...` | `python -m bench.suites.home.data ...` |
| `tools/llm_gpu0.sh`, `tools/lora/...` | `bench/suites/home/tools/...` |
| run-config keys `homeloop_bench`, `homeloop_robot`, `homeloop_bench_git`, `homeloop_robot_git`; planner names (`oracle`, `robot_agent:sage_s8n_d1`, ...); `host_id: homeloop` | unchanged (old results stay comparable). The two `_git` values now describe this repository; `seed_pool` is relative to the repository root (`symbolic_robot/domains/home/planner/seed_memory.jsonl`, was `homeloop_robot/planner/seed_memory.jsonl`) |

## The two source repositories at the time of the move

| repository | branch (HEAD) | commits | other refs |
|---|---|---|---|
| `homeloop_robot` | `r19` = `ce47651a228999a6632875788390fd82bff9f9d4` | 93 | `main` = `6432c357826f` (= tag `sim-freeze-r13`, an ancestor of `r19`); tag `sim-freeze-r19` (annotated, `f14a862`, points at `ce47651`) |
| `homeloop_bench` | `r21-p4b` = `133be46a737fa089bea22447e142ba7e6690669d` | 176 | `main` `314c7f0`, `r12` `feef26d`, `r14` `75fc84b`, `r15` `5912789`, `r16` `3443635`, `r16a` `ad53ce2`, `r16b` `b83f976`, `r17` `05a64fa`, `r18` `e2888ee`, `r19` `1a6415d`, `r20` `09baf70` (all ancestors of `r21-p4b` except `r18`) |

Both working trees were clean. The two repositories were not modified (read only; the history was rewritten in scratch clones).

How the history came in: in a scratch clone of each, `git filter-branch --index-filter` rewrote every path of every commit to its new place (table above), then the rewritten branch was merged here with `--allow-unrelated-histories`
(merge commits `2b18cd5` simulator, `471d6eb` benchmark). Commit hashes therefore differ from the originals, authors, dates and messages are the same, and `git log --follow` / `git blame` work on the new paths.
Tags: `sim-freeze-r13` -> `home-sim-freeze-r13`, `sim-freeze-r19` -> `home-sim-freeze-r19` (annotated; the message still starts with the old name), and every benchmark branch tip as `home-bench-main`, `home-bench-r12` ... `home-bench-r20`
(`home-bench-r18` is the only way to reach that branch). Old hash -> new hash for the tags:

| tag | old | new |
|---|---|---|
| `home-sim-freeze-r13` | `6432c357826f` | `ff1d83e5fcb6` |
| `home-sim-freeze-r19` | `ce47651a228999` (commit) | `2440d992de59` |
| `home-bench-main` | `314c7f0821ba` | `7314adfac770` |
| `home-bench-r12` / `r14` / `r15` / `r16` | `feef26d2504b` / `75fc84b4f798` / `591278945ef3` / `34436355b8ff` | `c062648dc6d0` / `c48d448a8809` / `de7b0dc173d8` / `f7ef6c3ecf6a` |
| `home-bench-r16a` / `r16b` / `r17` / `r18` | `ad53ce2922ba` / `b83f97616ac8` / `05a64fa151dc` / `e2888eeb5409` | `bd93936e73fb` / `a26d82bd5221` / `8574dc9e8497` / `e90ed73ecd9b` |
| `home-bench-r19` / `r20` | `1a6415d5f46c` / `09baf709b4ae` | `d1cfd7438809` / `1a57e463021f` |

(The head of `r21-p4b` is the second parent of merge `471d6eb`.) Files carried over byte for byte can be checked against the old checkouts, e.g. `cmp symbolic_robot/domains/home/world.py <old>/homeloop_robot/world.py`.

## What changed on purpose (besides paths)

* `domains/home/domain.py`: no longer wraps an external package; `pack` is `symbolic_robot.domains.home`; `available()` only needs pyyaml.
* `bench/suites/home/register.py` replaces the delegation; `bench/cli.py` hands every argument of a home run to the household CLI (see CHANGELOG: the old front end dropped `--limit`, `--profile`, `--seeds`, `--tasks`).
* Tests: only paths changed, plus `tests/home/sim/test_configs_adapter.py::test_check_manifest_strict` runs `strict=False` (robot_agent's checker warns "module is outside <pkg>, not inspected" for a dotted pack name; the same known limitation as the factory pack; its errors are still asserted to be none).
  `tests/test_layering.py` rules were reworded for the merge (CHANGELOG). Nothing was removed.
* Rules in `CLAUDE.md` (3 and 4) and the size baseline (31 moved files and functions over the limits, with their source).

## Checks

* Scripted calls: 62 episodes (5 houses x 3 profiles x 2 seeds x 2 languages), `to_json()` of every result, clock and object places: byte-identical to the standalone package (`tests/test_home_baseline.py`, baseline in `tests/home/parity/`).
* `--planner oracle --split dev --limit 20 --llm fake`: `episodes.jsonl` byte-identical and `summary.json` equal except the two `_git` version strings; the same for oracle (real, 2 seeds) and naive (stress).
* Tests (venv-bench Python, robot_agent and embodiplan importable): before, standalone `homeloop_robot` 979 + `homeloop_bench` 546 + `symbolic_robot` 78 = 1603; after the move 1604 + the 4 new baseline tests (the extra one: the in-process home front end). Final count of this series: see the CHANGELOG.

## Places outside this repository that still name the old packages (not changed here)

See the list in the report of this change; the short form:

* `venv-bench` (`/media/keti/workdir/data/homeloop_lora/venv-bench`): editable installs `homeloop-robot`, `homeloop-bench` (console script `homeloop-bench`) point at the old checkouts. Replace with one editable install of this repo: `venv-bench/bin/pip uninstall -y homeloop-robot homeloop-bench && venv-bench/bin/pip install -e /media/keti/workdir/remote_dir/symbolic_robot`.
* `homeloop_live` (`/media/keti/workdir/remote_dir/homeloop_live`): imports `homeloop_robot.*` and `homeloop_bench.*` in `server.py`, `skills.py`, `episodes.py`, `video.py`, `video_live.py`, `render.py`, `lab_apartment.py`, `serve.py`, `tests/test_live.py`; `pyproject.toml` depends on `homeloop-robot`; README and Makefile mention them. Apply the import mapping above.
* `robot_agent`: `tests/test_architecture.py` and `tools/arch_rules.json` forbid `homeloop_bench` / `homeloop_robot` imports (add `bench`, `symbolic_robot`); docs (`docs/env.md`, `docs/safety.md`, `docs/architecture.md`, `CHANGELOG.md`) name the old repositories and paths.
* `framework_guide/` (11 chapters), `data/homeloop_lora/p4/*.sh` (use `venv-bench/bin/homeloop-bench` and `cd ~/trung_workdir/homeloop_bench`), `~/.claude/skills/{dev-test-loop,lora-finetune}/SKILL.md`, and the copies `/media/keti/workdir/remote_dir/homeloop_robot`, `.../homeloop_bench` (old clones at `main`).
