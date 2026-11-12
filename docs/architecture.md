# Architecture

## Layers and the rules that enforce them

```
bench/                          benchmark suites: runner, campaign, paired statistics, protocol hash, suites registry
  |  imports (one way)           talks to servers over HTTP / WebSocket; to an external benchmark by subprocess only
  v
symbolic_robot/
  cli.py  server.py  server_skills.py        glue: the only core modules that import robot_agent
  domains/<name>/                            a domain: world, skills, profiles, data, and its robot_agent pack (configs/)
  result rng profile clock domain registry   the core: no robot, domain or language fact
  backend simcommand
```

| rule | enforced by |
|---|---|
| core and domains never import `bench` | `tests/test_layering.py::test_core_and_domains_never_import_bench` |
| `bench` never imports the household benchmark or robot_agent | `test_bench_does_not_import_the_frozen_household_benchmark`, `test_robot_agent_only_in_server_glue_and_domain_packs` |
| robot_agent only in `server.py`, `server_skills.py` and `domains/*/configs/` (a pack is robot_agent's own plug-in format, it must import its contract) | `test_robot_agent_only_in_server_glue_and_domain_packs` |
| domains do not import each other or the server | `test_domains_do_not_import_each_other_or_the_server` |
| no private names; the frozen household package is named only where it is wrapped | `test_no_private_names_anywhere`, `test_frozen_household_package_is_named_only_where_it_is_wrapped` |
| function <= 80 lines, file <= 600 lines, baseline does not grow | `test_size_limits_do_not_grow`, `tests/size_baseline.json` |
| frozen packages untouched | the `home` domain only imports; nothing is copied (see `domains/home/__init__.py`) |

## The core

* `Result(ok, msg, code, data, duration_s, truth)`: what a skill returns. `truth` is what really happened; the robot never sees it.
* `rng`: `Rng` (a draw depends on seed, a key and the n-th use of that key) and `CallDraws` (one vector of 16 uniforms per call, from SHA-256 of seed, skill, arguments and the n-th call with them; each rule reads its own slot). Same seed, same call: same numbers, whatever else happened between.
* `profile`: one YAML file per profile, each parameter `{kind, value, source, note}`. `ideal` is derived from `real` (every probability 0, durations kept); `stress` only when `real` declares `derive.stress.scale`.
* `SimClock`: simulated time moves only by reported durations; nothing ever waits in real time.
* `BaseDomain` (`domain.py`): the protocol a domain implements, with safe defaults (a hook not overridden does nothing). `registry`: built-in domains (loaded lazily), the entry point group `symbolic_robot.domains`, and `register()` for tests and local plug-ins.
* `LiveBackend`: wraps a domain's episode so the world can be replaced between runs and logs every call with its truth; `GET /agent/mobile_pose/get` reports the domain's pose. It is installed as the pack's robot (`__getattr__` passes everything else to the inner robot).
* `SimCommands`: the generic `sim_command` handler (`state, truth, reset, load, move_object by place, spawn`); `load` switches the world. An op a domain does not support answers `ok: false`.
* Server glue: `server.build()` seeds the connection to the LLM, creates the robot_agent app for the domain's pack, installs a stub node with the agents `mobile_pose`, `sim_world`, `sim_command`, adds the skills `reset_world`, `spawn_object` and the headless dialogue skills (`ask`: waits for the answer the benchmark's scripted person posts to `/agent/listen/<id>`; `say`: logged only), and publishes ENV for the current world. No map, no voice, no display pacing. `ROBOT_AGENT_ROS=off`.

## How the three earlier engines were unified

| engine | reused | dropped or left for later |
|---|---|---|
| the small factory simulator | all of it: world, skills, outcomes, user policies, messy scripts, task generator, floors, profile values, pack, experiment code (now `bench/`). Its keyed `Rng` is the core `Rng` bit for bit. | its flat profile format (now params with source labels); the server and live backend (now generic) |
| the sibling symbolic simulator (uncommitted work, a public repo) | the design: per-call 16-slot draws (`CallDraws`), per-parameter `kind/value/source/note`, ideal derived from real, `sim_command` ops, stub node with three agents, ENV/connections written by the launcher, check of dependencies (its MAP and speedup pacing were not kept: this repo is for benchmark runs) | its house layout, objects and skills (they are one robot's facts; they stay for its own domain), scene save/load/delete, furniture edits, device fault states with retry clearing, clutter-indexed failure maps: see the later-step plan, the `docs/migration_*` file |
| the household live server | the backend, the `reset_world` / `spawn_object` skills, the headless dialogue skills, connections seeding (its route-following display pose, `move_to`, warm-up and voice skills, and the PNG plan were removed: live-only) | its measured-apartment layout and picture (private layout: not brought), its video recorders and run scripts |

## Parity checks

* Factory replay: `tests/parity/factory_replay.py` replays the call sequences recorded in an earlier campaign (read only) and compares ok, code, msg, duration, simulated time and the whole truth of every call. Result at the time of writing: 774 episodes, 15,690 calls, 0 mismatches (`factory_v2`, `messy_factory`, `messy_fix_factory`; the older `factory_v1_plural_bug` differs on purpose: a bug fixed before v2).
* Analysis replay: `bench` analysis of the recorded `episodes.jsonl` gives exactly the recorded `summary.json` (protocol and messy suites); task generators give exactly the recorded `tasks.json`.
* Home wrapper: `tests/test_home_parity.py` compares 510 scripted calls over 5 houses and 3 profiles with direct calls of the household package (identical `to_json()` of every result, same clock and object places).
