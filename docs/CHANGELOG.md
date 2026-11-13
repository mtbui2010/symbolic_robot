# CHANGELOG

## 2026-11-13 (the household simulator and benchmark move in)
* `homeloop_robot` (the household simulator, frozen at tag `sim-freeze-r19`) is now `symbolic_robot/domains/home/` and `homeloop_bench` (HomeLoop-Bench: data, runner, planners, metrics, tools, recorded history) is now `bench/suites/home/`, both with their git history (tags `home-sim-freeze-r13`, `home-sim-freeze-r19`, `home-bench-<branch>`). Use only this repository from now on; the standalone repositories are not used any more. What moved where, the import mapping and the commits of the two sources: [migration_home.md](migration_home.md); their docs are in `docs/home/`.
* No behaviour change: the scripted calls of 62 episodes (5 houses x 3 profiles x 2 seeds x 2 languages) and the oracle / naive episodes of three benchmark runs are byte-identical to the standalone packages (`tests/test_home_baseline.py`); all 979 simulator tests and 546 benchmark tests pass here (home tests changed only in paths, one in strictness: `test_check_manifest_strict`, see the migration note).
* `python -m bench run --domain home --suite <planners|run|compare|report>` runs the household CLI in process (the subprocess delegation is gone) and passes it every argument; before, `--limit`, `--profile`, `--seeds`, `--tasks` of a home run were consumed by the generic parser and never reached the household CLI. `--split test` is still refused at the front end.
* Rules changed with the merge (CLAUDE.md, `tests/test_layering.py`): the household simulator is no longer "frozen outside this repo" but frozen in place (tag `home-sim-freeze-r19`); robot_agent may be imported inside functions of the home planner adapter files; the moved code over the size limits is listed in `tests/size_baseline.json` with its source (31 entries, not reduced by the move).

## 2026-11-12 (benchmark-only cleanup)
* Removed the live and dashboard parts: the map picture and MAP config (`mapview.py`), the `layout()`, `path()` and `speech_lang()` domain hooks, display-pose replay and `speedup` pacing (`--speedup`, `SPEEDUP`), `move_to`, `warmup_servers`, the voice and text dialogue (`ask_human`, `say_human`, Whisper `stt` connection, `--whisper-url`) and the `voice`/`text` values of `--ask-mode` (`headless` is the only one). `sim_command state` no longer lists map places; `move_object` takes a place, not a point. Pillow and requests left the `server` extra.
* Kept: `make run|terminate|status|logs|list|test|bench` (default port 8091), `reset_world`, `spawn_object`, the headless `ask`/`say`, `sim_command` ops, the LLM connection. Factory replay: 0 mismatches; home parity and `make bench` smoke unchanged.

## 2026-11-12
* New repository. One core engine (`Result`, `Rng` and per-call `CallDraws`, profiles with sources, `SimClock`, domain protocol and registry, live backend, generic `sim_command`, map drawing) and server glue for robot_agent.
* `factory` domain moved from the earlier factory simulator; replay of 774 recorded episodes (15,690 calls) matches call for call.
* `home` domain: wrapper over the frozen household package; 510 scripted calls identical to direct use.
* `bench/` package with suites `factory/protocol`, `factory/messy`, `factory/messy_fix` and delegating `home/*`; analysis of recorded episodes reproduces the recorded summaries exactly.
* `make run|terminate|status|logs|test|bench|list`, default port 8091, `PORT=` override.
