---
sources:
  - bench/suites/factory/
  - symbolic_robot/domains/factory/tasks.py
  - symbolic_robot/domains/factory/person.py
verified_at: a5cc7a4943aa
---

# Factory suites: three registered campaigns

!!! abstract "In this page"
    You get the three benchmark suites of the factory domain (`factory/protocol`, `factory/messy`,
    `factory/messy_fix`): what each one asks, its arms, how many episodes, the simulated person who
    answers questions, and the analysis that follows. This is the worked example of a campaign suite
    for people who add their own ([Add a suite](../guides/add-a-suite.md)). No suite was run for
    this page: a run needs the server, robot_agent and a language model. Everything shown is
    from reading the code or from offline calls that build tasks and previews.

| | |
|---|---|
| **Input** | the suite name, and the options of `python -m bench run` ([bench front end](bench-front-end.md)) |
| **Output** | a results folder: `episodes.jsonl`, `detail/`, `tasks.json`, `PROTOCOL_SHA256`, `summary.json`, `report.md` |
| **Used by** | the front end through the registry |
| **Uses** | [Campaign runner](campaign-runner.md), [Campaign statistics](campaign-statistics.md), the factory task generators and the scripted person |
| **Source** | [bench/suites/factory/](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/factory/__init__.py) |
| **Tests** | `tests/test_bench.py::test_suites_registered_with_their_protocols` |

## Background

All three suites ask one kind of question about a robot_agent engine: do some run options of the
planner help when the task does not say where the object is, so the robot must ask a person? The
person is a script, the world is the simulated assembly hall of the factory domain
([Factory world](factory-world.md)), and each option set is an **arm**. Each suite has a protocol text
that is written and hashed before the first episode (see
[Campaign statistics](campaign-statistics.md)).

## The three suites

| suite | arms | tasks | repeats | episodes | its question |
|---|---|---|---|---|---|
| `protocol` | A, B, C, A2 | 36 | 2 | 288 | do asking where the object is, re-asking after a miss, and looking at nearer places first help? |
| `messy` | A, C, D, A2 | 42 (6 for each of 7 answer policies) | 2 | 336 | do the options that act on the person's answer help when the answer is not one clear place? |
| `messy_fix` | A, E, D | 25 fixed tasks of the messy set | 2 | 150 | do three newer `ask_source` keys repair the tasks that failed before? |

The episode counts are tasks x arms x repeats: 36 x 4 x 2, 42 x 4 x 2 and 25 x 3 x 2. `A2` is a second
run of the setting of A. The difference between A2 and A is the noise of the whole pipeline.

`messy_fix` chooses its tasks because they failed in `messy`. Its protocol says so: it is a repair
check, not a new unbiased test, and its numbers are descriptive.

## The arms

An arm is a dictionary of run options, sent with each run; it overrides the server's environment.

```python
"""The arms of the factory suites: run options of the planning engine, sent with each run (they override the server's environment)."""
from __future__ import annotations

_NEW_OFF = {"ask_source_room": 0, "ask_source_clarify": 0, "ask_source_near": 0}      # sent explicitly: a server may set them on in its environment (a domain's planner_env may)

ARMS = {  # run options sent with each run (they override the environment): the three engine options under test
    "A":  {"ask_source": 1, "ask_source_reask": 0, "search_route_weight": 0, **_NEW_OFF},
    "B":  {"ask_source": 1, "ask_source_reask": 0, "search_route_weight": 0.3, **_NEW_OFF},
    "C":  {"ask_source": 1, "ask_source_reask": 1, "search_route_weight": 0.3, **_NEW_OFF},
    "A2": {"ask_source": 1, "ask_source_reask": 0, "search_route_weight": 0, **_NEW_OFF},   # A/A repeat: same setting, measures noise
    # messy-person protocol (messy.md): D = C plus the two later options
    "D":  {"ask_source": 1, "ask_source_reask": 1, "search_route_weight": 0.3, "relook": 1, "confirm_look": 1, **_NEW_OFF},
    # messy-fix re-run (messy_fix.md): E = D plus the three new keys of ask_source (a room answer is used, an unusable
    # answer is asked about once, a nearly-named place is confirmed)
    "E":  {"ask_source": 1, "ask_source_reask": 1, "search_route_weight": 0.3, "relook": 1, "confirm_look": 1,
           "ask_source_room": 1, "ask_source_clarify": 1, "ask_source_near": 1},
}
```

| arm | `ask_source` | `ask_source_reask` | `search_route_weight` | later options |
|---|---|---|---|---|
| A, A2 | 1 | 0 | 0 | none |
| B | 1 | 0 | 0.3 | none |
| C | 1 | 1 | 0.3 | none |
| D | 1 | 1 | 0.3 | `relook` 1, `confirm_look` 1 |
| E | 1 | 1 | 0.3 | as D, plus `ask_source_room`, `ask_source_clarify`, `ask_source_near` all 1 |

`ask_source` makes the robot ask "where is the object?" when the request names no place;
`ask_source_reask` asks once more if the first look misses; `search_route_weight` 0.3 looks at nearer
likely places first. All of these belong to robot_agent's engine; see
[robot_agent](https://mtbui2010.github.io/robot_agent/) for the engine. The `_NEW_OFF` keys are
sent explicitly as 0 in every arm except E, because a server's environment may switch them on.

## The server environment

The front end starts the server with `--ask-mode headless --dialogue human` (`SERVER_ARGS`) and the
environment of arm A (`SERVER_ENV`, `bench/suites/factory/__init__.py:19`), so that a run without
options behaves as arm A. The world is `assembly_hall` and the default profile is `real`.

## Tasks and the scripted person

Tasks come from seeded generators; nothing is hand-picked. `factory_tasks(floor, n, seed)` builds the
standard set from the floor's own objects and places; `factory_messy_tasks` also uses the places'
names, aliases and zone names to make the person's wording. The task seed is 7. For `protocol`, 36
tasks were built offline: 10 with the policy `knows`, 10 `unknown`, 10 `wrong` and 6 where the request
already names the source (policy none). A generated task is a dict with `id`, `prompt`, `kind`,
`obj_id`, `object`, `dest`, `true_place`, `wrong_place` and the spoken names. One of them:

```text
{'id': 't07', 'prompt': 'Put the bolt box on the weld table.', 'policy': 'knows', 'kind': 'ask'}
```

`answer_for(task, question, n_where)` in `symbolic_robot/domains/factory/person.py` is the simulated
person. It reads the question: a where-question that mentions putting is a destination question; "where
is" is a source question; a confirmation question gets "Yes."; a "which" question names the object. The
policy decides the source answer.

| policy | first source answer | later source answers |
|---|---|---|
| `knows` | the true place | the true place |
| `unknown` | "I do not know." | "I do not know." |
| `wrong` | a real place where the object is not | the true place |
| messy policies (`room_only`, `vague`, `mind_change`, `partial_name`, `silent`) | the first line of the task's `script` | the next line of the script; the last line repeats |

Run offline on task `t07`, the person answered a source question with `It is on the bolt bin.`, a
destination question with `On the weld table.` and `Is that right?` with `Yes.`. The `messy` set
splits as 6 tasks for each of its seven policies (the five above and `knows` and `wrong`), checked offline.

## Analyses and reports

| suite | analysis module | the rule |
|---|---|---|
| `protocol` | `analyze_protocol.py` | pre-registered: B or C beats A on more tasks than it loses, and wrong-done does not rise |
| `messy` | `analyze_messy.py` | the same for C or D against A, and a win counts as above noise only if it exceeds the A2-against-A gap; per-policy claims need p below 0.05 |
| `messy_fix` | `analyze_fix.py` | none: descriptive counts per group; needs `detail/` |

Each factory suite wraps its analysis so that it also writes `summary.json`. `protocol` and `messy`
have a report module that prints markdown tables from `summary.json`; `messy_fix` has none, so no
`report.md` is written for it. The statistics are in [Campaign statistics](campaign-statistics.md).
The distance measure for all three is the sum of the legs of successful `move` calls in the call log
(offline check: legs 2.5 m and 9 m, the second of a failed call, gave 2.5).

Two post-hoc tools sit beside them and are not part of the pre-registered measures: `grounding.py`
describes where the robot went first (needs `detail/`), and `probe.py` compares what two readers
understood on the same tasks. I did not run them.

## Previewing a suite

```text
$ python -m bench run --domain factory --suite messy_fix --out out/y --dry-run
suite factory/messy_fix: world assembly_hall, profile real, tasks 6, repeats 2, arms A,E,D, only t02,t09,t16,t23,t30,t37,t03,t10,t17,t24,t31,t38,t13,t27,t41,t06,t20,t34,t40,t00,t07,t14,t01,t08,t15 -> out/y
```

The real run is `make bench ROBOT=factory SUITE=<name>` ([Make targets](../reference/make-targets.md)).
It starts its own server, so it needs robot_agent and a model. Not run here.

## Edge cases and failure modes

| symptom | cause | fix |
|---|---|---|
| `unknown arm(s) [...] for factory/<suite>; known: ...` | an arm not in the suite's table | use the arms in the table above |
| `the protocol changed after its hash was recorded` | the protocol text was edited after the first run into this folder | restore it or use a new folder |
| `analysis not computed (...)` | a reduced run lacks an arm the analysis compares | run the missing arm, then `python -m bench analyze` |
| `messy_fix` analysis fails | `detail/` is missing | it needs the dialogue files |
| `tasks 6` in the plan of `messy` and `messy_fix` | for the messy suites `--tasks` means tasks per policy | `messy_fix` keeps `only` to 25 ids |

## How it is verified

`test_suites_registered_with_their_protocols` checks that each of the three suites has an existing
protocol file, task, answer, distance and analysis hooks, that its default arms are among its arms, that
arm B sends `search_route_weight` 0.3, and that `protocol` builds 36 tasks. I ran the same checks by
hand (not under pytest, which is not installed). The factory person and tasks have tests of their own in
`tests/test_factory_messy.py` (the messy scripts and the person) that I did not run for this page.

!!! code "Where in the code"
    - Suite definitions: https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/factory/__init__.py#L37-L53
    - Arms: https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/factory/arms.py#L1-L17
    - Scripted person: https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/factory/person.py#L12-L45
    - Task generators: https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/factory/tasks.py#L9-L25

Next: [Add a suite](../guides/add-a-suite.md), [Campaign statistics](campaign-statistics.md).
