---
sources: [symbolic_robot/simcommand.py, symbolic_robot/backend.py, symbolic_robot/server.py, symbolic_robot/server_skills.py, symbolic_robot/domain.py, symbolic_robot/domains/factory/__init__.py, symbolic_robot/domains/home/domain.py, bench/runner.py, tests/test_server.py]
verified_at: a5cc7a4943aa
---

# sim_command ops and endpoints

!!! abstract "In this page"
    - The six `sim_command` ops with their fields, answers and error messages, and how the factory and the household domain differ.
    - The HTTP and WebSocket endpoints that the server and the benchmark runner use, with the shape of what they return.
    - Real answers of the ops on both domains, run offline without a server.

The ops are explained with their code in [Live backend and sim commands](../modules/live-backend-and-sim-commands.md). The server that exposes them is in [Server glue](../modules/server-and-cli.md). Words: [sim_command](glossary.md#sim-command), [truth](glossary.md#truth), [stub node](glossary.md#stub-node).

## Endpoints

The routes belong to robot_agent's app. This repo adds three agents to it (through the [stub node](glossary.md#stub-node)) and two launcher skills. The table lists the routes the repo's own code and tests call. Nothing in this section was run: it needs the server, which needs robot_agent, fastapi and uvicorn.

| route | method | what it gives | used by |
|---|---|---|---|
| `/agent/mobile_pose/get` | GET | `{"value": <robot snapshot>}` | `make run` and `make status` (readiness), `tests/test_server.py` |
| `/agent/sim_world/get` | GET | `{"value": <world view>}`: the truth | the bench runner (before and after each episode), the bench front end (readiness), tests |
| `/agent/sim_command/send` | POST | the answer of the op, for a JSON body `{"cmd": "<op>", ...}` | scripts and tests |
| `/agent/sim_command/get` | GET | the answer of the op `state` (`CommandAgent.get`) | the agent interface |
| `/skill/reset_world` | POST | `{"isdone", "msg", "erased"}` | the bench runner before every episode, with `profile` and `seed` |
| `/skill/spawn_object` | POST | `{"isdone", ...}` | tests |
| `/ws/agent` | WebSocket | the run events (`speak`, `listen`, `done`, `error`, ...) | the bench runner |
| `/agent/listen/<id>` | POST | accepts the person's answer text `{"text": ...}` | the scripted person ([headless ask](glossary.md#headless-ask)) |
| `/agent/cancel` | POST | cancels the current run | the bench runner on timeout |

All three agents have `get`, `send` and `cancel` (robot_agent's device-agent interface). `mobile_pose` and `sim_world` are read-only: their `send` answers `{"isdone": true, "msg": "read-only agent"}` and their `cancel` returns `False`.

### What `mobile_pose` and `sim_world` return

`mobile_pose` is the robot snapshot: the domain's `view(...)["robot"]` plus `x`, `y`, `yaw`, `busy` and `t_sim`. `sim_world` is the domain's `view` plus `robot` (the same snapshot), `log`, `profile`, `seed` and `world`. Run on both domains:

| domain | keys of the `sim_world` value | keys of the robot snapshot |
|---|---|---|
| factory | `floor`, `log`, `objects`, `profile`, `robot`, `seed`, `world` | `at`, `holding`, `x`, `y`, `yaw`, `busy`, `t_sim` |
| household | `log`, `objects`, `people`, `profile`, `robot`, `seed`, `world` | `holding`, `x`, `y`, `yaw`, `busy`, `t_sim` |

The runner reads `objects[<id>]["at"]` to judge a factory episode, `log` for the distance and the faults, and `robot["t_sim"]`. A log entry has `t_wall`, `skill`, `args`, `ok`, `code`, `msg`, `t_sim`, `dur` and `truth`; the factory returns the robot's own log, whose entries have no `t_wall`.

## The ops

A command is `{"cmd": "<op>", ...}`. The answer is always a dict with `ok`, usually `msg`, and `isdone` equal to `ok`. Every op runs under the backend's lock. A Python exception inside an op becomes `{"ok": false, "msg": "<ExceptionType>: <text>"}`, and an unknown op answers `unknown cmd '<name>'`.

| op | request fields | success answer | `ok: false` answers |
|---|---|---|---|
| `state` | none | `ok`, `symbolic` (true), `domain`, `world`, `worlds`, `scenes`, `objects`, `catalog`, `profile`, `seed` | only on an exception |
| `truth` | `last` (default 50) | `ok`, the world view without `log`, `busy`, `log` (the last `last` entries) | `ValueError: ...` if `last` is not an integer |
| `reset` | `what` (`objects`, `robot`, `all`; default `all`), `profile`, `seed`, `forget` | `reset (a new episode)`, plus `; memory erased: <files>` | `reset what='x': use objects, robot or all`; `unknown profile 'x' (have: ideal, real, stress)` |
| `load` | `name`, `forget` | `world <name>` (plus `, memory erased`) | `no world or scene '<name>' (worlds: ...)` |
| `move_object` | `body` or `name`, `place` | `<id> is now at <place>` | `move_object needs body (or name) and place`; the domain's message; `move_object is not supported by domain '<name>'` |
| `spawn` | `cls` or `name`, `place` or `surface`, extra keys | `<id> is now at <place>`, `id`, `at` | `spawn needs cls and place, e.g. {cls: 'mug', place: '<place id>'}`; the domain's message; `spawn is not supported by domain '<name>'` |

`forget` (default true) erases robot_agent's memory files of the old world through the callback the server installs; `0`, `false`, `no` or `off` keeps them. In `load`, a name that is a world builds a new episode of that world; otherwise the domain's `op_load` is asked, and neither built-in domain has one, so in practice `load` takes a world name. `state` has a `scenes` list for domains with scene files; for both built-in domains it equals the world names.

Run offline (factory, `small_workshop`, `ideal`, seed 0, backend and handler built in Python):

```text
reset profile=nope  -> {'ok': False, 'msg': "unknown profile 'nope' (have: ideal, real, stress)", 'isdone': False}
reset what=robot, seed=3, profile=stress -> {'ok': True, 'msg': 'reset (a new episode)', 'isdone': True}
   state afterwards: profile 'stress', seed 3
load assembly_hall  -> {'ok': True, 'msg': 'world assembly_hall', 'isdone': True}
move_object (no fields) -> {'ok': False, 'msg': 'move_object needs body (or name) and place', 'isdone': False}
move_object nope@x  -> {'ok': False, 'msg': "no object 'nope' or no single place 'x'", 'isdone': False}
spawn (no fields)   -> {'ok': False, 'msg': "spawn needs cls and place, e.g. {cls: 'mug', place: '<place id>'}", 'isdone': False}
```

Household, `senior_flat`, `ideal`: `state` returns the same eleven keys with 23 objects, each with `at`, `body`, `cls`, `color`, `name`; `truth` has the keys `busy`, `isdone`, `log`, `objects`, `ok`, `people`, `profile`, `robot`, `seed`, `world`; `load studio_flat` answers `world studio_flat`; `move_object` of a missing object answers `no object 'nope' or no place 'x'`; `reset` answers `reset (a new episode)`.

!!! warning "Current behaviour (F5): `reset` ignores `what`"
    `what` is checked against `objects`, `robot` and `all`, and then never used: every `reset` builds a whole new episode through `LiveBackend.reset` ([simcommand.py:52-61](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/simcommand.py#L52-L61)). Send `reset` only when a full new episode is what you want.

!!! warning "Current behaviour (F6): the factory `color` is its variant"
    The factory's world snapshot fills the object key `color` from the object's variant, which is a size such as `large` ([factory/world.py:143](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/factory/world.py#L143)). The household's `color` is a real color. This key is in `state`, `truth` and `sim_world`.

!!! note "`truth` with `last: 0`"
    The log is cut with `log[-last:]`, and `-0` is the start of the list, so `last: 0` returns the whole log, not an empty one. Run: with 4 calls logged, `last` of 0, 1, 2 and 10 returned 4, 1, 2 and 4 entries.

## How the two domains differ

The three data ops are hooks of the domain ([domain.py](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domain.py#L73-L84)). A hook that returns `None` means "not supported".

| | factory | household |
|---|---|---|
| `move_object` place | a place id or a place name, resolved to one place | an exact place id only |
| `move_object` capacity | not checked | not checked |
| `spawn` extra keys | `variant` (needed when the label already exists) | `color`, `obj_id` |
| `spawn` refuses | an unknown class or place; a label that exists (give a `variant`); a full place | an unknown place; a full place; an existing `obj_id` |
| new object id | `<cls>_<n>` | `<cls>_<n>`, or `obj_id` |
| `load` of a scene | not supported | not supported |
| world label | floor | house |

Example (factory): `{"cmd": "spawn", "cls": "caliper", "place": "entry_table@entry"}` answers `an object named 'caliper' exists: give a variant`; with `"variant": "small"` it answers `caliper_1 is now at entry_table@entry` (run, see the module page).

## The launcher skills

Besides the ops, the server adds two skills to the pack's own ([Server glue](../modules/server-and-cli.md)). They are called as `POST /skill/<name>`.

| skill | body fields | does |
|---|---|---|
| `reset_world` | `profile`, `seed`, `world`, any domain option, `forget` (default true) | a new episode, and the memory files erased unless `forget` is false. This is what the bench runner calls before each episode, with `profile` and the episode's seed |
| `spawn_object` | `cls`, `place`, any extra | the same as the op `spawn`; `isdone` false with `spawn_object needs cls and place and a domain that supports it` when either is missing or the op is unsupported |

With `--dialogue human` the server also routes `ask` and `say` to the headless versions: `say` is only logged; `ask` emits a `listen` event and waits for `POST /agent/listen/<id>`.

## Not run

The endpoints, the WebSocket and the two skill routes were not called. The ops were run by constructing `LiveBackend` and `SimCommands` directly on a copy of the pinned commit. `tests/test_server.py` does call the endpoints; it skips itself without robot_agent and fastapi, and pytest is not installed here, so no test result is claimed.

Next: [Command lines](cli.md), [Known pitfalls](known-pitfalls.md).
