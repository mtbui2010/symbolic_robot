---
sources:
  - symbolic_robot/domain.py
  - symbolic_robot/registry.py
  - symbolic_robot/profile.py
  - symbolic_robot/cli.py
  - tests/toy.py
  - tests/test_core.py
  - docs/domains.md
  - pyproject.toml
verified_at: a5cc7a4943aa
---

# Add a domain

!!! abstract "In this page"
    You copy the toy domain of the tests, rename it, register it, and serve it through the live backend and the `sim_command` handler by calling the functions of `tests/test_core.py` directly. Then you see where a plug-in package declares its entry point (read, not run) and how fault rates go into a data file with a source label.
    The guide ends with `python -m symbolic_robot list` showing your domain. That output was produced with the domain registered in the same process; the entry-point route to the same list was **not run**, because it needs an installed package.
    All runs: offline, on a copy of commit `a5cc7a4943aa`, 2026-11-19, with `pyyaml` only. The server step (a domain served to robot_agent) was not run.

A **domain** is one simulated world with its robot: the factory, the household, or yours. The core knows nothing about floors or grippers. It asks the domain through a fixed list of hooks, and every hook has a default that does nothing ([Domain protocol](../modules/domain-protocol.md), [glossary](../reference/glossary.md#domain)).

## Step 1: copy the toy domain

`tests/toy.py` is a whole domain written only against the protocol: a robot with a place (`a` or `b`), one item (`cup`), a failure drawn from the seed, and a clock. Copy it to a folder outside the repository and rename it. Here the domain becomes `pantry`:

```text
$ diff tests/toy.py plug/pantry.py
10c10
< class ToyRobot:
---
> class PantryRobot:
21c21
<             res = Result(False, "failed", "hw_fault", duration_s=1.0, truth={"fault": "toy"})
---
>             res = Result(False, "failed", "hw_fault", duration_s=1.0, truth={"fault": "pantry"})
30c30
< class ToyEpisode:
---
> class PantryEpisode:
33c33
<         self.robot = ToyRobot(0.0 if profile == "ideal" else 0.5, seed)
---
>         self.robot = PantryRobot(0.0 if profile == "ideal" else 0.5, seed)
36,38c36,38
< class Toy(BaseDomain):
<     name = "toy"
<     description = "two places and a cup"
---
> class Pantry(BaseDomain):
>     name = "pantry"
>     description = "two shelves and a cup"
48c48
<         return ToyEpisode(world, profile, seed)
---
>         return PantryEpisode(world, profile, seed)
```

The class `Pantry` overrides the catalogue (`worlds`, `profiles`), the episode (`make_episode`, `pose`, `view`) and one op (`op_move_object`). Everything else uses the default. The minimum for a server is `make_episode`, `robot`, `pose` and `view`; the table of every hook and what happens without it is on the [Domain protocol](../modules/domain-protocol.md) page.

Four things your robot must do, shown by the toy:

| rule | in the toy |
|---|---|
| `robot.call(skill, **args)` returns a `Result` with `ok`, `msg`, `code`, `data`, `duration_s` and `truth` | `Result(True, "ok", duration_s=2.0)` |
| every random choice comes from a seeded `Rng`, keyed by what is drawn | `self.rng.chance(self.p_fail, "fail", skill)` ([Results, time and draws](../modules/results-time-draws.md)) |
| time moves only by the durations the calls report | `self.clock.advance(res.duration_s)` |
| the hidden facts go in `truth`, never in `msg` | `truth={"fault": "pantry"}` |

## Step 2: register it and serve it, through `tests/test_core.py`

Registering is one call, `registry.register("pantry", Pantry)`. Then the **live backend** (`LiveBackend`, the single running episode) and the **`sim_command` handler** (`SimCommands`, the ops `state`, `move_object`, `spawn` and others) work on it without a change in the core ([Live backend and sim commands](../modules/live-backend-and-sim-commands.md)):

```python
from symbolic_robot import registry
from symbolic_robot.backend import LiveBackend
from symbolic_robot.simcommand import SimCommands
from pantry import Pantry

print(registry.names(), registry.world_labels())
registry.register("pantry", Pantry)
print(registry.names(), registry.world_labels())
live = LiveBackend(Pantry(), "small", "ideal", 0)
print(live.call("go", to="b").ok, live.snapshot())
c = SimCommands(live)
print(c.handle({"cmd": "move_object", "body": "cup", "place": "b"}))
print(c.handle({"cmd": "spawn", "cls": "x", "place": "a"}))
try:
    registry.get("nope")
except KeyError as e:
    print("KeyError:", e)
```

```text
['factory', 'home'] ['floor', 'house']
['factory', 'home', 'pantry'] ['floor', 'house', 'room']
True {'at': 'b', 'x': 3.0, 'y': 0.0, 'yaw': 0.0, 'busy': '', 't_sim': 2.0}
{'ok': True, 'msg': 'cup is now at b', 'isdone': True}
{'ok': False, 'msg': "spawn is not supported by domain 'pantry'", 'isdone': False}
KeyError: "unknown domain 'nope'; known: factory, home, pantry"
```

Read it so: the list of domain names and of world labels (`room`) grew by one. A call went through the backend and the snapshot shows `x = 3.0` from `pose`, `at` from `view` and `t_sim = 2.0` from the robot's clock. `move_object` worked because the domain overrides it. `spawn` answers `ok: false` with a message, because `op_spawn` is not overridden: that is what a missing hook looks like.

The repository's own checks are the three functions of `tests/test_core.py` that serve the toy. To run them on your domain, copy the test file and rename `Toy` to `Pantry` and `"toy"` to `"pantry"`. `pytest` is not installed here, so the three functions were **called directly**, with a stand-in for the one helper they use, `pytest.raises`:

```text
passed test_registry_lists_builtins_and_takes_a_plugin
passed test_live_backend_and_sim_commands_work_for_a_new_domain
passed test_live_backend_reset_and_world_change_callback
```

The first checks that `factory` and `home` are listed, that `get("nope")` raises `KeyError`, and that after `register` the worlds are `["small", "big"]` and `room` is a world label. The second checks a call, the log, the snapshot, `state`, `move_object` with and without a place, `spawn` (not supported) and an unknown command. The third checks `reset` with a new seed and with a new world, and the world-change callback. This is not a `pytest` run: it is the same assertions called by hand.

## Step 3: put your facts in data, with a source for every number

The rule of the repository is that facts are data: floors, object classes and fault rates go in YAML next to the domain, a `source` label on every number, and Python holds only the engine ([Profiles](../modules/profiles.md), [Declared outcomes](../learn/declared-outcomes.md)). A profile directory with `real.yaml` gets `ideal` for free, and `stress` if `real.yaml` says `derive: {stress: {scale: ...}}`.

A one-parameter file for the pantry, `profiles/real.yaml`:

```yaml
profile: real
derive:
  stress: {scale: 2.0}
params:
  p_fail:
    {kind: prob, value: 0.1, source: "invented, round number", note: "any call: a transient fault"}
```

Loading it with `symbolic_robot.profile`:

```text
['ideal', 'real', 'stress']
real 0.1
ideal 0.0
stress 0.2
```

A parameter without a source is refused. A copy of the file with `{kind: prob, value: 0.1}` and nothing else gave:

```text
ValueError: real.yaml: parameter p_fail needs a value and a source label
```

The toy does not read this file (its failure rate is in the code); a real domain loads it and passes `profile.get("p_fail")` to its robot. The household domain keeps its own profile code ([Home profiles](../modules/home-profiles.md)).

## Step 4: the entry point in a package (read, not run)

Registering with `register` works in a test or a script. A domain shipped in a package declares an entry point, and `registry.names()` then lists it with no call. In the package's `pyproject.toml` (from `docs/domains.md`):

```toml
[project.entry-points."symbolic_robot.domains"]
toy = "my_package.toy:Toy"
```

The key is the domain name; the value is `"module:attr"`, where `attr` is a `BaseDomain` subclass or an instance. The registry merges three sources in this order, and a later one wins on the same name: the built-in table (`factory`, `home`), the entry points, and `register()`. **Not run:** an entry point needs an installed package, and nothing was installed. For the built-in route (a domain of this repository), the name and `"module:Class"` go in `registry.BUILTIN`.

## Step 5: the list shows it

`python -m symbolic_robot list` does not call `register`, so a domain registered in your script shows up only when the script calls the command's `main`. This script did that:

```python
from symbolic_robot import registry
from symbolic_robot.cli import main
from pantry import Pantry

registry.register("pantry", Pantry)
main(["list"])
```

```text
domains:
  factory    simulated factory floor: zones, benches, bins, a lockable cabinet, a forklift lane; floors/*.yaml
             floors: assembly_hall, small_workshop   (default assembly_hall)
             profiles: ideal, real, stress
  home       simulated household (the frozen household simulator): houses, rooms, furniture, a person; profiles ideal | real | stress
             houses: care_home_suite, couple_flat, family_house, korean_apt_59, korean_apt_84, senior_flat, shared_flat, studio_flat   (default senior_flat)
             profiles: ideal, real, stress
  pantry     two shelves and a cup
             rooms: small, big   (default small)
             profiles: ideal, real
```

**The task works when** your domain is in that list with its worlds and profiles. With an entry point the plain `python -m symbolic_robot list` shows it; that run was not done.

## Common problems

| symptom | cause | what to do |
|---|---|---|
| `KeyError: "unknown domain 'x'; known: ..."` | the name is not registered in this process; the command line turns it into `cannot start: ...` with exit 2 (run with `--robot nope`) | register it, or install the package with its entry point |
| `NotImplementedError: domain '' cannot build episodes` | `make_episode` is not overridden (a domain with a name shows it) | override `make_episode` |
| `{'ok': False, 'msg': "spawn is not supported by domain 'x'"}` | an op whose hook is not overridden | override the hook (`op_spawn`, `op_move_object`, `op_load`) or accept it |
| `not available: <reason>` in the list | `available()` returns a reason, for example a missing optional package | install it; nothing else breaks |
| a plug-in that cannot be imported | `get` raises its `ModuleNotFoundError`; `names()` still lists it and `world_labels()` skips it | fix the import |
| `ValueError: ...: parameter p needs a value and a source label` | a YAML parameter without a value or a source | add both |
| `python -m symbolic_robot run --robot pantry` ends with `ModuleNotFoundError: No module named 'robot_agent'` | serving a domain needs robot_agent; the `run` command also does not know a domain you registered only in a script | use an entry point or `BUILTIN`, and install robot_agent. See [Server and CLI](../modules/server-and-cli.md) |

## What was not run

| not run | why |
|---|---|
| the entry point route, `pip install` of a plug-in package | nothing was installed |
| `python -m symbolic_robot run --robot pantry`, `make run`, any call to a server endpoint | needs robot_agent and a server |
| a robot_agent pack for the domain (`pack`, `install_pack`, `manifest.yaml`) | it needs robot_agent; see [Factory pack](../modules/factory-pack.md) for a finished example |
| `pytest` on the tests | `pytest` is not installed; the three functions were called by hand |
| a domain with its own skills, worlds and profile files | the toy shows the protocol; the factory ([Factory world](../modules/factory-world.md)) is the worked example |

Rules from the repository's `docs/domains.md` for a domain of your own: do not put a fact of one robot, language or benchmark in the core; do not import `bench` or a sibling domain; do not import robot_agent outside the pack's `configs/`. A test enforces the layering ([Layering tests](../modules/layering-tests.md)).

Next: [Add a suite](add-a-suite.md).
