# CHANGELOG

## 2026-11-12 (benchmark-only cleanup)
* Removed the live and dashboard parts: the map picture and MAP config (`mapview.py`), the `layout()`, `path()` and `speech_lang()` domain hooks, display-pose replay and `speedup` pacing (`--speedup`, `SPEEDUP`), `move_to`, `warmup_servers`, the voice and text dialogue (`ask_human`, `say_human`, Whisper `stt` connection, `--whisper-url`) and the `voice`/`text` values of `--ask-mode` (`headless` is the only one). `sim_command state` no longer lists map places; `move_object` takes a place, not a point. Pillow and requests left the `server` extra.
* Kept: `make run|terminate|status|logs|list|test|bench` (default port 8091), `reset_world`, `spawn_object`, the headless `ask`/`say`, `sim_command` ops, the LLM connection. Factory replay: 0 mismatches; home parity and `make bench` smoke unchanged.

## 2026-11-12
* New repository. One core engine (`Result`, `Rng` and per-call `CallDraws`, profiles with sources, `SimClock`, domain protocol and registry, live backend, generic `sim_command`, map drawing) and server glue for robot_agent.
* `factory` domain moved from the earlier factory simulator; replay of 774 recorded episodes (15,690 calls) matches call for call.
* `home` domain: wrapper over the frozen household package; 510 scripted calls identical to direct use.
* `bench/` package with suites `factory/protocol`, `factory/messy`, `factory/messy_fix` and delegating `home/*`; analysis of recorded episodes reproduces the recorded summaries exactly.
* `make run|terminate|status|logs|test|bench|list`, default port 8091, `PORT=` override.
