---
sources: [symbolic_robot/domains/factory/configs/, symbolic_robot/domains/factory/__init__.py, symbolic_robot/domain.py, symbolic_robot/result.py, tests/test_layering.py]
verified_at: a5cc7a4943aa
---

# Packs, manifests and the hub

!!! abstract "In this page"
    - A [pack](../reference/glossary.md#pack) is the set of files that lets robot_agent (the hub) plan for and drive a robot it has never heard of: a [manifest](../reference/glossary.md#manifest), an [adapter](../reference/glossary.md#adapter), skill functions and a map. Each domain of this repo has one under `configs/`.
    - The hub sees the simulator only through the pack. In this repo, only the packs and two server files may import the hub; a test checks it.
    - A real pack is shown: the map of the factory floor, the skill function that wraps a simulated skill, and the way the live backend is handed to the pack.

## The question: how does a planner that knows no robot drive this one?

robot_agent is the planner and executor. It is not written for the factory floor or for a household. It asks a robot package three things: what skills exist, how to turn a plan step into a call, and what the world looks like. A package of this kind is called a pack. This page explains what is in one and why the simulator keeps it in a separate place. The hub side (how the hub loads a package, what a manifest field means) is described on the framework site: [Robot package](https://mtbui2010.github.io/robot_agent/contracts/robot-package/) and [Add a new robot](https://mtbui2010.github.io/robot_agent/guides/add-a-robot/). The overview of this repo from the hub's side is [symbolic_robot on the framework site](https://mtbui2010.github.io/robot_agent/repos/symbolic-robot/).

## The files of a pack

A pack lives in `symbolic_robot/domains/<name>/configs/`. The factory pack, with what the hub reads from each file:

| file | what robot_agent reads from it | factory example |
|---|---|---|
| `manifest.yaml` | the skills, each with `action`, `pre`, `effects`, `verify` and the failure codes it may return; geometry; a `planner` block; the safety file | 12 skills; `move` has the effect `arrived(?inputs)` |
| `adapter.py` | an `Adapter`: `bind` turns a plan step into a skill call; `observe` and `reconcile` read and write the hub's world model | `make_adapter()` |
| `skills_config.py` | a table: skill name to the function that runs it | `'move': ('symbolic_robot.domains.factory.configs.ra_skills', 'move')` |
| `ra_skills.py` | the skill functions, each `f(node=None, inputs="", **params)` | `move(inputs="main bench")` |
| `tasks.py` | [`ENV`](../reference/glossary.md#env): one entry for every place | 9 entries for the 10 places of `small_workshop` |
| `backend.py` | the robot the functions drive | `set_backend(robot)` |
| `safety/*.yaml` | the safety rules the hub checks before it acts | `safety/factory.yaml` |

The household pack has the same files, and one more (`ra_dialog.py`) for its spoken answers. Its detail is on [Household pack](../modules/home-pack.md); the factory pack is on [Factory pack](../modules/factory-pack.md).

The manifest is data: a skill is declared, not coded. Whether it matches the skill table is something the hub's own tool checks: `skills_config.py` says in a comment that `python -m robot_agent.contract.check_manifest symbolic_robot.domains.factory --strict` checks the manifest against the table. I did not run it, because robot_agent is not installed here. I also do not reproduce the head of the factory manifest: it carries the robot's name, which this site does not print.

## Skill functions return a [legacy dict](../reference/glossary.md#legacy-dict)

The hub does not know `Result`. Its skill functions return a plain dict, `{isdone, msg, code?, **data}`. The simulator keeps its own result and converts it at the edge:

```python
    def to_legacy(self) -> dict:
        """The dict robot_agent skill functions return: {isdone, msg, code?, **data}."""
        out = {"isdone": self.ok, "msg": self.msg}
        if self.code:
            out["code"] = self.code
        out.update(self.data)
        return out
```

[symbolic_robot/result.py:16-22](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/result.py#L16-L22)

Note what the dict leaves out: `truth` and `duration_s`. The hub gets the report, not the hidden truth (see [Symbolic worlds](symbolic-worlds.md)). A skill function is a thin wrapper:

```python
def _run(skill: str, **args) -> dict:
    return get_backend().call(skill, **args).to_legacy()


def move(node=None, inputs: str = "", **params) -> dict:
    return _run("move", target=str(inputs))


def find(node=None, inputs: str = "", **params) -> dict:
    out = _run("find", obj=str(inputs))
    if out.get("isdone") and out.get("found"):
        out["ins"] = {out["found"]: {"pose_3d": [0.6, 0.0, 0.8]}}
    return out
```

[symbolic_robot/domains/factory/configs/ra_skills.py:7-19](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/factory/configs/ra_skills.py#L7-L19)

The hub's `inputs` is a text, and the simulator's argument is named (`target`, `obj`). The wrapper renames it. `find` also adds `pose_3d`, because the hub expects a pose; the value `[0.6, 0.0, 0.8]` is a fixed made-up one. Run offline on `small_workshop`, profile `ideal`, with the robot set as backend:

```text
move(inputs="main bench")   -> {'isdone': True, 'msg': 'arrived at main bench', 'at': 'main_bench@bench_area'}
find(inputs="large wrench") -> {'isdone': True, 'msg': 'found large wrench', 'found': 'large wrench', 'ins': {'large wrench': {'pose_3d': [0.6, 0.0, 0.8]}}}
```

## ENV: the map the hub plans on

The hub needs a map of places, so that it can resolve "the main bench" and search for objects. The pack builds it with `env_for(world)`: one entry per place, with `loc` (x, y), `aliases`, `openable` and `surface`. Two places are special. The forklift lane is left out altogether, because it is a keep-out region and the hub searches every place in `ENV`. The charging dock stays, with `search: false`, so the hub does not look for objects on the charger.

Run offline on `small_workshop` (10 places):

```text
places: 10   ENV entries: 9   left out: ['forklift_lane@aisle']
dock aliases: ['charging dock', 'charging dock in the entry', 'charge', 'charging', 'charging station']
dock: search False, openable False, surface False
toolbox: openable True, no search key
```

The code that builds an entry is [`tasks.py:11-32`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/factory/configs/tasks.py#L11-L32). `ENV` itself is built when the module is imported, for the floor named by `SYMBOLIC_FACTORY_FLOOR` (default `assembly_hall`).

## Why the hub is imported only here

The simulator and its benchmark must run without the hub. A researcher who only wants the engine should not need to install the hub. So the repo has a rule, and a test that enforces it:

```python
def test_robot_agent_only_in_server_glue_and_domain_packs():
    bad = []
    for p in CORE.rglob("*.py"):
        rel = p.relative_to(CORE)
        in_pack = "configs" in rel.parts and rel.parts[0] == "domains"      # a domain's robot_agent pack is robot_agent's own plug-in format
        if not in_pack and p.name not in GLUE and any(m.split(".")[0] == "robot_agent" for m in imports(p)):
            bad.append(str(rel))
    assert not bad, bad
```

[tests/test_layering.py:49-56](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/tests/test_layering.py#L49-L56)

Only a pack (a `configs` folder of a domain) and the two server files may import robot_agent. The bench package may do so in two planner files, and only inside functions, so that listing planners needs no hub. I read the test; I did not run it with `pytest`. [Layering tests](../modules/layering-tests.md) explains all the rules.

## Handing the live backend to the pack

When the server starts, it builds a [live backend](../reference/glossary.md#livebackend), and then asks the domain to install the pack:

```python
    def install_pack(self, live) -> None:
        from .configs.backend import set_backend
        set_backend(live)
```

[symbolic_robot/domains/factory/__init__.py:52-54](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/factory/__init__.py#L52-L54)

The base class has an empty `install_pack` ([`domain.py:70-71`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domain.py#L70-L71)); the server calls it at [`server.py:137`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/server.py#L137). From then on, every skill function that the hub calls goes to the live robot, so the hub and the benchmark's reset and `sim_command` calls act on the same world. Without a backend, `get_backend()` builds a default episode of the default floor, which is useful in a test and surprising in a server. See [Live backend and sim commands](../modules/live-backend-and-sim-commands.md) and [Server and CLI](../modules/server-and-cli.md).

!!! warning "The ROS-off switch is not on the hub's main branch"
    The Makefile exports `ROBOT_AGENT_ROS=off` and the server sets it as a default. It is meant to tell the hub not to start ROS. The framework site checked the hub at `main` and found no such switch: the hub imports `rclpy` at start-up. The simulators of this workspace run against a synced copy of the hub that has it. So the server may not start against a plain hub without ROS 2. This was reasoned from the code on the framework site and is not run here. The reason and the way around it are in [symbolic_robot on the framework site](https://mtbui2010.github.io/robot_agent/repos/symbolic-robot/). The offline parts of the benchmark do not need the hub.

!!! code "Where in the code"
    - The factory pack: [`domains/factory/configs/`](https://github.com/mtbui2010/symbolic_robot/tree/a5cc7a4943aa/symbolic_robot/domains/factory/configs); the household pack: [`domains/home/configs/`](https://github.com/mtbui2010/symbolic_robot/tree/a5cc7a4943aa/symbolic_robot/domains/home/configs)
    - Legacy dict: [`result.py:16-22`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/result.py#L16-L22); install: [`domain.py:70-71`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domain.py#L70-L71), [`factory/__init__.py:52-54`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/factory/__init__.py#L52-L54)
    - The layering rule: [`tests/test_layering.py:49-63`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/tests/test_layering.py#L49-L63)
    - Module pages: [Factory pack](../modules/factory-pack.md), [Household pack](../modules/home-pack.md), [Domain protocol](../modules/domain-protocol.md)

## What this means when you use it

- To add a domain you write a pack: a manifest, an adapter, a skill table, the skill functions and a map. Start from the factory pack, which is the smaller one. The steps are in [Add a domain](../guides/add-a-domain.md).
- Do not import robot_agent outside `configs/` and the server glue. The layering test will fail, and the benchmark would need the hub.
- Put a place that is not a destination (a keep-out lane) in the world but out of `ENV`, or give it `search: false`.
- The hub sees `{isdone, msg, code?, **data}` only. Anything a judge needs to know goes into `truth`, which never crosses the pack.
- A pack runs offline only in part. The skill functions and `env_for` do; the adapter needs robot_agent's contract classes, and `check_manifest` and the hub import are not run here.

**Next:** [The benchmark protocol](benchmark-protocol.md)
