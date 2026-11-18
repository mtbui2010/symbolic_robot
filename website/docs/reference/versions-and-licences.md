---
sources: [pyproject.toml, LICENSE, README.md, symbolic_robot/__init__.py, bench/__init__.py, symbolic_robot/domains/home/LICENSE, bench/suites/home/LICENSE, bench/suites/home/LICENSE-DATA, bench/suites/home/NOTICE, bench/suites/home/CITATION.cff]
verified_at: a5cc7a4943aa
---

# Versions and licences

!!! abstract "In this page"
    - The version of the engine and what it needs: Python, packages, extras.
    - What these docs were checked against: the commit pin, the freeze tag, the interpreters used.
    - Which licence covers which part of the repo, and what the README and the licence files say about the task data.
    - This page summarises the repo's own statements. It is not legal advice: read the licence files before you copy or redistribute anything.

## Versions

| what | value | where |
|---|---|---|
| package `symbolic_robot` | `0.1.0` | [pyproject.toml](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/pyproject.toml), and `__version__` in `symbolic_robot/__init__.py` |
| package `bench` | `0.1.0` | `__version__` in `bench/__init__.py`; it is installed with the same project |
| Python | 3.10 or later | `requires-python = ">=3.10"` |
| required package | `pyyaml` | `dependencies` (core and the household simulator) |
| extra `server` | `fastapi`, `uvicorn` | for `python -m symbolic_robot run` |
| extra `bench` | `websockets` | for `python -m bench` (even `list`) |
| extra `test` | `pytest` | for `make test` |
| console script | `symbolic-robot` | calls `symbolic_robot.cli:main` |

The pyproject gives no upper bounds and no version for fastapi, uvicorn, websockets, pytest or pyyaml.

### Things this repo needs but does not pin

| dependency | what the repo says |
|---|---|
| robot_agent | needed by the server and by the household `robot_agent:*` planners. It must have the `ROBOT_AGENT_ROS=off` switch, which the Makefile and `build()` set. The repo names no revision; a result from the household `robot_agent:*` planners belongs to a hub revision, so name it next to the result ([robot_agent planners](../modules/robot-agent-planners.md), [robot_agent docs](https://mtbui2010.github.io/robot_agent/)). The household pack declares some planner keys that the hub's published `main` may not define |
| embodiplan | the household `robot_agent:*` planners need it importable too ([embodiplan docs](https://mtbui2010.github.io/embodiplan/)). `oracle`, `naive` and the LLM baselines do not |
| a local LLM server | the server writes an Ollama connection into `connections.json` when a model is set; the runs that call an LLM need that server |

Each household run records the git revisions of what it used in `config.versions` of `summary.json`, with `git describe --always --dirty`; a dirty checkout changes the file ([Result files](result-files.md)).

## What these docs were checked against

| item | value |
|---|---|
| commit of every code link and line number | `a5cc7a4943aa` (full `a5cc7a4943aaf1ac9603f14fab10bf8889d46278`) |
| freeze tag of the household simulator | `home-sim-freeze-r19` ([Parity and frozen behaviour](../modules/parity.md)) |
| interpreter for the engine | CPython 3.12.3 with PyYAML 6.0.1, no `websockets` |
| interpreter for `python -m bench` | CPython 3.11.18 with PyYAML 6.0.3 and `websockets` 17.4 |
| not available when checking | pytest, fastapi, uvicorn, robot_agent, any LLM |

Permalinks to the commit resolve once the commit is on the public remote.

## Licences

The repo merges two projects that were licensed separately. Each part keeps its own text. The table is the README's "Licences" section checked against the files at the pin.

| part | where | licence |
|---|---|---|
| the engine, the factory domain, the generic benchmark front end, the factory suites | `symbolic_robot/*.py`, `symbolic_robot/domains/factory/`, `bench/*.py`, `bench/suites/factory/` | **MIT**, the root `LICENSE` (copyright 2026, the repo owner). The root `LICENSE` covers only these files |
| the household simulator: code, house and profile data | `symbolic_robot/domains/home/` | **Apache-2.0**, `symbolic_robot/domains/home/LICENSE` |
| the household benchmark: code | `bench/suites/home/` | **Apache-2.0**, `bench/suites/home/LICENSE` |
| the household task data | `bench/suites/home/data/` | mixed; part is research-only (below) |
| citation of the household benchmark | `bench/suites/home/CITATION.cff` | names Apache-2.0 for the software |

So "the code is MIT" holds for the engine, the factory domain and the generic benchmark. The household domain and its benchmark are Apache-2.0 inside the same repo.

All three files exist at the pin: the root `LICENSE` is the standard MIT text, and the two others are the Apache License, Version 2.0.

### The task data

The task data of the household benchmark is **not under one licence**. The README and `bench/suites/home/LICENSE-DATA` (with `NOTICE`) say, in summary:

| part of the data | licence |
|---|---|
| the English texts, the Korean templates, the goals, the labels and the other fields | Apache-2.0 |
| the Korean text written by the EXAONE 3.5 model, and the cache rows built from it | **not** Apache-2.0. Research use only; no commercial use; no use of it to develop or improve other models (do not train or fine-tune on it) |
| the author's selection, filtering and labels attached to that part | CC BY-NC 4.0 |

The data files name the exact fields and the number of records in each part. This page does not repeat them. For any use outside those terms, the licence files say to use the Korean template wording of the same task, which is Apache-2.0, instead of the model-written Korean.

`tests/home/bench/test_licence.py` checks that the licence statements still match the data files (not run here: pytest is not installed, and the test split is not in the copy used for these checks).

!!! warning "What this site does with the task data"
    The site quotes no task text in any language, no gold goal and no per-task row. Where a number about the data appears, it is an aggregate with its source file, its count and its date. Read `LICENSE-DATA` and `NOTICE` before you use, copy or redistribute any of the data, and do not train a model on the research-only part.

### Reading the repo's own notices

`LICENSE-DATA`, `NOTICE` and `CITATION.cff` are the standalone benchmark's files word for word. Their text uses the earlier standalone package's name and its old paths, so read the old data path as `bench/suites/home/data/` (the README says so too). Do not take a sentence of those files out of that context.

Next: [Task data](../modules/task-data.md), [Layering and size limits](../modules/layering-tests.md), [Known pitfalls](known-pitfalls.md).
