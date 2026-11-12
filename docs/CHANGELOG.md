# CHANGELOG

## 2026-11-12
* New repository. One core engine (`Result`, `Rng` and per-call `CallDraws`, profiles with sources, `SimClock`, domain protocol and registry, live backend, generic `sim_command`, map drawing) and server glue for robot_agent.
* `factory` domain moved from the earlier factory simulator; replay of 774 recorded episodes (15,690 calls) matches call for call.
* `home` domain: wrapper over the frozen household package; 510 scripted calls identical to direct use.
* `bench/` package with suites `factory/protocol`, `factory/messy`, `factory/messy_fix` and delegating `home/*`; analysis of recorded episodes reproduces the recorded summaries exactly.
* `make run|terminate|status|logs|test|bench|list`, default port 8091, `PORT=` override.
