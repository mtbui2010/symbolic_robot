---
sources: [symbolic_robot/result.py, symbolic_robot/domains/factory/robot.py, symbolic_robot/domains/factory/world.py, symbolic_robot/domains/home/types.py, symbolic_robot/domains/home/skills.py]
verified_at: a5cc7a4943aa
---

# Symbolic worlds, skills and the hidden truth

!!! abstract "In this page"
    - A [symbolic world](../reference/glossary.md#world) is a short list of places, objects and a robot state. A skill checks its conditions on that list, changes it, and returns a result and a time.
    - Every result has two faces: what the planner may see, and [`truth`](../reference/glossary.md#truth), what really happened. The judge reads `truth`; the planner never does.
    - The household robot keeps its own belief of the world. A silent failure makes that belief differ from the truth. A real run shows it.

## The question: how can a robot "fail" when nothing moves?

You send `move(target="main bench")` to this simulator and the robot does not roll anywhere. The call is answered from a small table in memory. So what is a failure here?

A symbolic world holds only what a planner needs to decide:

| part | what it is | example (factory, `small_workshop`, run offline) |
|---|---|---|
| place | a spot the robot can go to; id is `name@zone` (factory) or `name@room` (household) | `main_bench@bench_area`, `bed@main` |
| object | a thing with an `at` field that names a place, `robot` while held, or the floor | `wrench_l` ("large wrench") is at `main_bench@bench_area` |
| robot state | where it is (`at`), what it holds (`holding`), which containers are open | at `charging_dock@entry`, holding nothing, nothing open |

The factory floor has 10 places. Nothing else is simulated: no physics, no geometry beyond the distance between two place positions. See [Factory world](../modules/factory-world.md) and [Household world](../modules/home-world.md) for the two implementations.

## A skill is a precondition, an outcome, an effect and a time

A [skill](../reference/glossary.md#skill) is one function of the robot. Its parts:

1. **Precondition.** What must be true before: the target exists, the gripper is empty, the container is open. If it is not, the call fails at once with a code.
2. **Outcome.** A fault drawn from the profile may still make the call fail (see [Declared outcomes](declared-outcomes.md)).
3. **Effect.** On success the world changes: `at` becomes the new place, `holding` becomes the object.
4. **Duration.** Simulated seconds, added to the clock. Nothing waits in real time.

The factory `move` shows all four in about ten lines (verbatim):

```python
    def _sk_move(self, target=""):
        w = self.world
        pid, why = self._place(target)
        if pid is None:
            return Result(False, why, "unreachable")
        if w.places[pid].kind == "lane":
            return Result(False, f"{w.places[pid].name} is a forklift lane: not allowed", "blocked", truth={"hazard": "entered_forklift_lane", "place": pid})
        d = w.dist(w.at, pid)
        dur = d / float(self.prof.get("speed_mps")) + (float(self.prof.get("durations_s")["move_overhead"]) if d > 1e-6 else 0.0)
        truth = {"leg": {"from": w.at, "to": pid, "dist": round(d, 3)}}
        w.at = pid
        return Result(True, f"arrived at {w.places[pid].name}", data={"at": pid}, duration_s=dur, truth=truth)
```

[symbolic_robot/domains/factory/robot.py:87-98](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/factory/robot.py#L87-L98)

Three calls on `small_workshop`, profile `real`, seed 0 (run offline on a copy of the pinned commit):

| call | `ok` | `code` | duration | `truth` |
|---|---|---|---|---|
| `move(target="main bench")` | true | none | 14.078 s | `{"leg": {"from": "charging_dock@entry", "to": "main_bench@bench_area", "dist": 8.062}}` |
| `move(target="forklift lane")` | false | `blocked` | 1.0 s | `{"hazard": "entered_forklift_lane", "place": "forklift_lane@aisle"}` |
| `fly()` | false | `software` | 1.0 s | `{}` (message "unknown skill fly") |

The first duration is distance over speed plus a fixed overhead: 8.062 m at the profile's 0.8 m/s, plus 4.0 s. The second call fails by precondition, not by luck: the lane is a keep-out region, and the `truth` records the hazard so a judge can count it as a safety violation. The third call shows that an unknown skill is a failure, not a crash.

## The result has two faces

Both domains return an outcome of the same shape. The core type (factory) is:

```python
@dataclass
class Result:
    ok: bool
    msg: str = ""
    code: str | None = None                 # a robot_agent FailureCode value when ok is False
    data: dict = field(default_factory=dict)
    duration_s: float = 0.0
    truth: dict = field(default_factory=dict)
```

[symbolic_robot/result.py:7-14](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/result.py#L7-L14)

| field | who sees it | meaning |
|---|---|---|
| `ok`, `msg`, `code`, `data`, `duration_s` | the planner | the report |
| `truth` | the judge and the tests | what happened: the real cause, the event, whether the effect took place |

The household type, `SkillResult`, has the same fields plus `injected` (the outcome came from the failure model, not from a precondition). It has two views: `public()` for the planner, and `to_json()`, which adds `injected` and `truth`. Details are in [Results, simulated time and seeded draws](../modules/results-time-draws.md) and [Household skills](../modules/home-skills.md).

### The 11 failure codes

A failure carries one of 11 [codes](../reference/glossary.md#failure-code). The household domain lists them in `FailureCode`, and says their values are the same as robot_agent's `FailureCode` ([types.py:13-26](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/home/types.py#L13-L26)). A test compares the two when robot_agent is importable; I did not run it here (robot_agent is not installed).

| code | typical cause here |
|---|---|
| `absent` | the object is not at this place, or the detector missed it |
| `perception_unavailable` | the camera is out |
| `unreachable` | no such place, or no path |
| `blocked` | a keep-out lane, a closed container, a full place |
| `grasp_failed` | the grip slipped, or the object is too heavy |
| `dropped` | the object fell while carried or placed |
| `hw_fault` | a transient or persistent hardware fault |
| `estop` | the emergency stop is pressed |
| `timeout` | the call ran out of time, or nobody answered |
| `cancelled` | the call was interrupted |
| `software` | a bad call: unknown skill, bad arguments |

## Truth versus what the robot reports

A real robot does not know the world exactly. It knows what its own reports say. The household robot models that gap with a `believed` state, built only from the results it returned. It is updated after each call by `_update_belief`:

```python
    def _update_belief(self, skill: str, out: SkillResult) -> None:
        d = out.data
        if out.ok:
            if skill == "pick":
                self.believed_holding = d.get("holding")
            elif skill in ("place", "put_in", "handover"):
                self.believed_holding = None
            elif skill == "open" and d.get("opened"):
                self.believed_opened.add(d["opened"])
            elif skill == "close" and d.get("closed"):
                self.believed_opened.discard(d["closed"])
        elif out.code == F.DROPPED:
            self.believed_holding = None
```

[symbolic_robot/domains/home/skills.py:310-322](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/home/skills.py#L310-L322)

If a call reports `ok`, the belief follows it. A **[silent failure](../reference/glossary.md#silent-failure)** is a call that reports `ok` while the effect did not happen. On `studio_flat`, profile `real`, seed 45 (run offline), the `pick` of the book reports success and the truth says "slip":

| view | what it holds |
|---|---|
| the report (`public()`) | `ok: true`, `data: {"holding": "book_1"}`, `msg: "ok"`, `duration_s: 9.081555` |
| the extra fields of `to_json()` | `injected: false`, `truth: {"effect": false, "event": "slip"}` |
| `robot.believed` | `{'at': 'bed@main', 'holding': 'book_1', 'opened': []}` |
| the true world | the robot holds nothing; `book_1` is still at `bed@main` |

The planner believes it holds the book. Only a check (`grasp_check`, `vlm_check`) or a later failure can show otherwise.

An **[injected](../reference/glossary.md#injected)** failure is a miss drawn from the profile. Seed 7, `move` to `bed@main`, then `find(obj="book")`:

| the planner sees (`public()`) | the judge sees (`to_json()`) |
|---|---|
| `{"ok": false, "code": "absent", "msg": "book_1 not found", "data": {"place": "bed@main"}, "duration_s": 3.52234}` | the same, plus `"injected": true` and `"truth": {"effect": false, "event": "miss"}` |

The book was there. The planner cannot tell a miss from an object that is really elsewhere. The next `pick(obj="book_1")` succeeds in this run, because the grasp camera looks again (`skills.py:724-728`): a miss is not permanent.

!!! code "Where in the code"
    - Factory skills and the `Result` they return: [`factory/robot.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/factory/robot.py), [`result.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/result.py)
    - Household result and codes: [`home/types.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/home/types.py) (`FailureCode`, `SkillResult`)
    - The belief: [`home/skills.py:310-328`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/home/skills.py#L310-L328)
    - Module pages: [Factory world](../modules/factory-world.md), [Factory skills](../modules/factory-skills.md), [Household world](../modules/home-world.md), [Household skills](../modules/home-skills.md)

## What this means when you use it

- A failure code is the report, not the cause. When a planner is blamed for a failure, read `truth` before you decide whose fault it was.
- A planner that never verifies can finish with a wrong belief and still be told `ok`. Whether a verifying planner gains from its extra calls is a result you can measure, not a guess.
- Durations are simulated. A benchmark run costs CPU, not robot time, and a time budget is a budget in simulated seconds.
- The factory robot has no separate belief: `believed` there is computed from the world itself, so silent failure is a household feature. Do not expect it from the factory domain.

**Next:** [Declared outcomes and profiles](declared-outcomes.md)
