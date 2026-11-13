# Adding a domain

A domain is a class that implements as much of `symbolic_robot.domain.BaseDomain` as it has data for. Everything it does not override does nothing.

## Minimum

```python
from symbolic_robot.domain import BaseDomain
from symbolic_robot.result import Result
from symbolic_robot.rng import Rng

class Toy(BaseDomain):
    name = "toy"; world_label = "room"
    def worlds(self): return ["small"]
    def profiles(self): return ["ideal", "real"]
    def make_episode(self, world, profile, seed, **opts): ...   # anything with .robot; robot.call(skill, **args) -> Result
    def pose(self, ep): return (x, y, yaw_rad)
    def view(self, ep): return {"objects": {id: {"cls": ..., "at": ...}}, "robot": {...}}
```

`tests/toy.py` is a complete example written only against this protocol; `tests/test_core.py` serves it through the backend and `sim_command`.

## What each hook buys

| hook | without it |
|---|---|
| `make_episode`, `robot`, `pose`, `view` | no server |
| `env(ep)` | the pack's own ENV |
| `op_move_object`, `op_spawn`, `op_load`, `scenes` | the matching `sim_command` ops answer `ok: false` |
| `planner_env()`, `default_model`, `sim_user_opts()`, `live_opts` | the core defaults (no planner options, no LLM connection) |
| `available()` | return a reason string when an optional dependency is missing: the domain is listed as "not available" and nothing else breaks |

## Facts are data

Put floors, object classes, fault rates and safety rules in YAML next to the domain with a `source` label for every number; Python holds the engine. A profile directory with `real.yaml` gets `ideal` for free (and `stress` if `real` has `derive: {stress: {scale: 3}}`). See `symbolic_robot/domains/factory/`: `floors/*.yaml`, `profiles/real.yaml`, `configs/` (the robot_agent pack: `manifest.yaml`, `safety/`, `tasks.py` ENV, `adapter.py`, `skills_config.py`, `ra_skills.py`).

## Registering

Built-in: add the name and `"module:Class"` to `registry.BUILTIN`. Plug-in from another package: an entry point

```toml
[project.entry-points."symbolic_robot.domains"]
toy = "my_package.toy:Toy"
```

or `registry.register("toy", Toy)` in a test. `python -m symbolic_robot list` shows it.

## The robot_agent pack

`pack` is the importable name of a robot_agent pack (`<pack>.configs.adapter`, `.skills_config`, `.tasks`, `manifest.yaml`). It may be dotted (the factory's is `symbolic_robot.domains.factory`, the home domain's `symbolic_robot.domains.home`) or an external package. `install_pack(live)` hands the live backend to the pack's skill functions (the pack's own `set_backend`). robot_agent's `check_manifest --strict` assumes a top-level pack name and so reports "module is outside <pkg>, not inspected" warnings for a dotted one; without `--strict` it reports 0 errors (`tests/test_server.py`).

## Do not

* put a fact of one robot, language or benchmark in the core;
* import `bench` or a sibling domain;
* import robot_agent outside the pack's `configs/` (keep it out of the domain's engine modules).
