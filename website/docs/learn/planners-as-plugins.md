---
sources:
  - bench/suites/home/planners/__init__.py
  - bench/suites/home/planners/base.py
  - bench/suites/home/env.py
  - bench/suites/home/runner.py
verified_at: a5cc7a4943aa
---

# 7. Planners as plug-ins

!!! abstract "In this chapter"
    - A planner is a class with a `name`, a `privileged` flag and one method, `run(env)`. The helper `StepPlanner` reduces that to one method of your own, `act(obs)`.
    - Only `oracle` and `naive` may read the true world. One more name, `robot_agent:sage_gold`, is marked privileged too, as a diagnostic.
    - You can plug in any class as `package.module:ClassName`. Below, a short floor planner is run offline and judged. The 52 `robot_agent:*` names cannot run here.

## The question

You have a planner. What must it look like for the benchmark to run it, and what stops it from peeking at the answer?

## The idea

### One method

The benchmark owns the world, the skills, the person, the budgets and the judge. A planner only decides what to call next. The contract is a protocol with two attributes and one method ([`base.py:31-36`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/planners/base.py#L31-L36)): `name`, `privileged`, and `run(env)`, which must end the episode with `env.finish(status, say)`.

Most planners do not write `run`. `StepPlanner` loops for you (`base.py:56-66`):

```python
    def run(self, env) -> None:
        self.reset(env)
        while env.status is None:
            if env.over:
                env.finish("give_up", give_up_text(env.lang), reason="budget exhausted")
                return
            a = self.act(env.observe())
            if isinstance(a, Finish):
                finish_with(env, a)
                return
            env.call(a.skill, **dict(a.args))
```

You write `act(obs)`. It returns either a `ToolCall` (a skill name and its arguments) or a `Finish` (a status, what the robot says, and a private reason). `PlanPlanner` is the other shape: you write `plan(obs)`, a whole list of calls, and `run` executes it and stops at the first failure unless your `on_failure` returns more calls. The table is the full interface (`base.py:31-80`, `env.py`):

| attribute or method | type | required | used by |
|---|---|---|---|
| `name` | `str` | yes | the record (`make_planner` overwrites it with the name you asked for) |
| `privileged` | `bool` | yes; `False` for a normal planner | `run_episode` passes it to `EpisodeEnv` |
| `run(env)` | method | yes | `run_episode`; must end the episode |
| `needs_llm` | `bool` | optional (default `False`) | `check_llm`: the run refuses to start without `--llm` if true |
| `description` | `str` | optional | the listing of `python -m bench run --domain home --suite planners` |
| `interrupt_via` | `"robot"` or `"inject"` | optional | read from the class before the episode starts: how a scripted correction reaches the planner |
| `raise_errors` | `bool` | optional | if true, a crash in `run` is re-raised instead of recorded as status `error` |
| `act(obs)` (`StepPlanner`) | method | for that helper | `StepPlanner.run` |
| `plan(obs)`, `on_failure(call, result, obs)` (`PlanPlanner`) | methods | for that helper | `PlanPlanner.run` |

### What the planner sees and does

`env.observe()` returns a frozen `Observation` (`env.py:100-118`). It is built from the robot's belief side only: the task text as the robot heard it, the house's places and people, a memory of every object's usual place, the robot's sensed state, the public part of the last skill result, user events, the planner's own call history, the step count, the simulated time, what is left of the budgets, and what the robot sees of each person now (`people_now`). The full field list and the judge are on [the episode page](../modules/episode-env-and-judge.md). The planner acts with `env.call(skill, **args)`, may decline part of a request with `env.note_refusal`, and ends with `env.finish("done" | "refuse" | "give_up", say)`.

### The registry and plug-in names

A planner name is either a registry key or `package.module:ClassName`. The registry maps a key to a module, a class, a one-line description and `needs_llm` (`planners/__init__.py:10-88`). `planner_class` imports the module by name when the planner is first needed, so listing the planners never imports the hub. A name with a colon that is not a registry key is a **spec**: `is_spec` checks that module and class are valid identifiers, and `planner_class` imports the module and gets the class (`planners/__init__.py:104-131`). Your module only has to be importable, for example through `PYTHONPATH`. Details: [planner interface](../modules/planner-interface.md).

### Who may read the truth

`privileged` is enforced by the environment, not left to honour. `EpisodeEnv` reads the flag from the planner's class:

```python
    @property
    def truth(self):
        return self._world if self.privileged else None

    @property
    def llm_calls(self) -> int:
        return self._llm.calls if self._llm is not None else 0

    def llm(self):
        return self._llm

    @property
    def goal(self) -> dict:
        """The current judge goal (conjunction of the subtask goals). Privileged planners only."""
        if not self.privileged:
            raise PermissionError("the goal is hidden from non-privileged planners")
        return self.current_goal()
```

[`env.py:275-291`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/env.py#L275-L291). Run offline, a non-privileged planner that reads `env.goal` ends its episode with status `error`, because the runner records any ordinary exception as a failed episode (see below). The private attribute `_world` is private by name only: a planner that reads it anyway is not comparable with the others, and nothing in the code stops it. That is why the rule is part of the protocol and the records must be reviewed.

Only two registry planners are the **references** that may read the truth ([privileged planners](../reference/glossary.md#privileged-planner)): `oracle` ([glossary](../reference/glossary.md#oracle)) re-solves from the true world after every call, and `naive` ([glossary](../reference/glossary.md#naive)) runs the oracle's start-state plan open loop ([reference planners](../modules/reference-planners.md)). They are upper and lower reference points for a comparison, not planners to compare claims with. A third name is privileged as well:

!!! warning "The one exception: `robot_agent:sage_gold`"
    The comment in `base.py` says "oracle, naive only". That holds for the reference planners. The registry also holds a diagnostic variant, `robot_agent:sage_gold`, whose class sets `privileged = True`: it starts from the task's gold goals and skips the understanding step, so it is the ceiling for execution alone. Run offline, the classes of all 58 registry names give exactly three privileged ones: `oracle`, `naive` and `robot_agent:sage_gold`. Mark it in every table, and never use it as a headline planner.

### The three groups of the registry

58 names are registered at this commit. Counted offline with `REGISTRY`:

| group | names | count | needs an LLM | runs here |
|---|---|---|---|---|
| references, privileged | `oracle`, `naive` | 2 | no | yes |
| baselines in the style of published planners | `saycan_like`, `inner_monologue_like`, `progprompt_like`, `knowno_like` | 4 | yes | listed as available; not run (no LLM) |
| robot_agent planners | `robot_agent:sage`, `robot_agent:grace`, `robot_agent:llm_direct` and 49 variants of `sage` | 52 | yes | no |

`planner_available` reports six of the 58 names as available on the machine that wrote this page: the first six rows above. The 52 `robot_agent:*` names are **unavailable here**: they run the hub (robot_agent), which is another repository and is not importable in this environment, so the registry lists them as `[unavailable: robot_agent not importable]`. They were not run. They are the planners that the benchmark exists to test; what they are, and how the adapter drives the hub, is in [robot_agent planners](../modules/robot-agent-planners.md) and on the framework site's [Benchmark a planner](https://mtbui2010.github.io/robot_agent/guides/benchmark-a-planner/) guide. The four baselines are described on [LLM baselines](../modules/llm-baselines.md).

### A floor planner, run

The smallest useful planner ends every episode at once with `give_up`. It is the floor for any comparison: a planner that does worse than this has a problem. This is the example of the framework guide, run again on a copy of the pinned commit, saved outside the repository as `giveup_planner.py`:

```python
from bench.suites.home.env import Finish
from bench.suites.home.planners.base import StepPlanner


class GiveUp(StepPlanner):
    """A floor baseline: ends every episode at once with 'give_up'."""
    name = "giveup"
    description = "gives up at once"

    def act(self, obs):
        return Finish("give_up", reason="floor baseline")
```

With the folder on `PYTHONPATH` it runs by spec, in the same command as any registry planner:

```text
$ python -m bench run --domain home --suite run --out out/giveup --planner giveup_planner:GiveUp --split dev --limit 20 --profile real --seeds 2
{"false_success": 0.0, "goal_condition_success": 0.070175, "help_rate": 0.0, "n_episodes": 40, "n_error": 0, "rejection_rate": 0.0, "smoke": true, "success": 0.0, "success_ci95": [0.0, 0.087622]}
```

All 40 episodes have status `give_up`, 0 skill calls and the finish reason `floor baseline`. A give-up is never a success, and it is never a false success, because it claims nothing. It does not refuse, so even the refuse tasks fail (`rejection_rate` 0.0). Compared with the oracle on the same 40 pairs, `compare` printed b = 33, c = 0, so the oracle's 0.825 is 33 episodes above this floor. For this spec, `planner_available` gave `(True, '')` and `needs_llm` gave false.

The same offline check on the first dev task (its text is never printed) shows how the three kinds of planner end, through `run_episode`:

```text
giveup_planner:GiveUp privileged: False | status: give_up | success: False | n_calls: 0 | error: None
peek_planner:Peek privileged: False | status: error | success: False | n_calls: 0 | error: PermissionError
oracle privileged: True | status: done | success: True | n_calls: 2 | error: None
```

`Peek` is a short `StepPlanner` whose `act` reads `self.env.goal` and returns `Finish("done")`. The hidden goal raised `PermissionError`, the runner recorded the episode as `error`, and the run goes on. The planner's own exception does not stop the run; an LLM failure or an import error does, as `InfraError` (see [chapter 5](benchmark-protocol.md)).

!!! code "Where in the code"
    - Protocol and helpers: [`planners/base.py#L31-L80`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/planners/base.py#L31-L80)
    - Registry, `is_spec`, `planner_class`: [`planners/__init__.py#L104-L131`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/planners/__init__.py#L104-L131)
    - Observation: [`env.py#L100-L118`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/env.py#L100-L118); truth and goal: [`env.py#L275-L291`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/env.py#L275-L291)

    The links resolve after the owner pushes this commit.

## What this means when you use it

- To add a planner, write a class with `name`, `privileged = False` and `act` (or `plan`), put it on `PYTHONPATH`, and pass `--planner package.module:Class`. No registration is needed. The step-by-step version is [Add a planner](../guides/add-a-planner.md).
- Never set `privileged = True` for a planner you want to compare. A privileged planner is a reference: its numbers are not comparable with the others.
- Run the floor planner next to yours. A number means little without the point it must beat.
- A planner whose class cannot be imported, or an LLM that fails, stops the whole run. A planner that raises on its own only fails its own episode, so look at `n_error` and `errors_by_type` in the summary.
- Do not count on the registry for the hub planners. They need the hub on `PYTHONPATH` and an LLM; check `python -m bench run --domain home --suite planners` first.

**Next:** [Add a planner (guide) →](../guides/add-a-planner.md)
