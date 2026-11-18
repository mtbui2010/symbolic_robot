---
sources:
  - bench/suites/home/metrics.py
  - bench/suites/home/cli.py
  - bench/stats.py
verified_at: a5cc7a4943aa
---

# 6. Paired tests: comparing two planners without fooling yourself

!!! abstract "In this chapter"
    - Two planners on the same tasks and seeds give **pairs**. Only the pairs where they differ carry information. `compare` runs McNemar on them, then two tests at the level of the task.
    - The 40 episodes of a small run come from 20 tasks. Seeds of one task are not independent, so the interval in `report.md` is **task-clustered**, with an **effective sample size** ([glossary](../reference/glossary.md#effective-sample-size)).
    - The factory campaigns use another method: per-task means, an exact sign test and a bootstrap interval.
    - Every number below is from a 40-episode smoke run (a smoke run, not a result).

## The question

The oracle succeeded in 33 of 40 episodes, the naive planner in 25. Is the oracle better, or did it get lucky? And when the report says `0.825 [0.668, 0.917]`, what is the bracket?

Two answers are needed: a test for the difference of two planners, and an interval for one planner.

## The idea

### Why pairing

Both planners play the same (task, seed) pairs. The same pair gives the same random draws, so a call that fails for one planner fails the same way for the other ([determinism](determinism.md)). Task difficulty cancels out. For each pair there are four outcomes. The oracle against the naive planner, 40 pairs:

| | naive succeeded | naive did not succeed |
|---|---|---|
| **oracle succeeded** | 25 | **b = 8** |
| **oracle did not succeed** | **c = 0** | 7 |

The oracle has 33 successes (25 + 8), the naive planner 25 (25 + 0). The two bold cells are the **discordant pairs**. The 25 pairs where both succeed and the 7 where both fail say nothing about which planner is better. The question becomes: of the 8 pairs where they differ, is 8 against 0 more than a fair coin would give?

### McNemar

The **McNemar test** ([glossary](../reference/glossary.md#mcnemar-test)) answers that. With b + c below 25 it is the exact two-sided binomial test of `min(b, c)` against b + c fair coin flips; otherwise a chi-square statistic with continuity correction, `(|b - c| - 1)^2 / (b + c)`, with one degree of freedom.

```python
def mcnemar(a: dict, b: dict) -> dict:
    """Paired McNemar test. ``a``/``b``: {(task_id, seed): success}. Exact binomial when b + c < 25,
    else chi-square with continuity correction (p from the chi2(1) survival function via erfc)."""
    keys = sorted(set(a) & set(b))
    bb = sum(1 for k in keys if a[k] and not b[k])
    cc = sum(1 for k in keys if (not a[k]) and b[k])
    n = len(keys)
    if bb + cc < 25:
        method = "exact_binomial"
        stat = float(min(bb, cc))
        p = binom_two_sided(bb, cc)
    else:
        method = "chi2_continuity"
        stat = (abs(bb - cc) - 1.0) ** 2 / (bb + cc)
        p = math.erfc(math.sqrt(stat / 2.0))
    sa = sum(1 for k in keys if a[k])
    sb = sum(1 for k in keys if b[k])
    return {"n_pairs": n, "b": bb, "c": cc, "statistic": r6(stat), "p_value": r6(p), "method": method,
            "success_a": r6(sa / n) if n else None, "success_b": r6(sb / n) if n else None}
```

[`metrics.py:419-437`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/metrics.py#L419-L437). The exact branch is the sign test: for 8 against 0 it is `2 * (1/2)^8 = 0.0078`.

### The catch: seeds of one task are not independent

The 40 pairs are 20 tasks times 2 seeds. Two seeds of one task share the task, the house and the goal. If a task is hard, it tends to fail twice. Treating 40 pairs as 40 independent trials makes the p value too small. So `compare` adds two tests whose unit is the **task**, when there is more than one seed per task (`metrics.py:401-416`):

- **McNemar on the per-task majority** (`task_majority`, `metrics.py:393-398`). Each task becomes one pair: a success if more than half of its seeds succeeded. A tie counts as a failure, so with 2 seeds a task needs both.
- **Task sign-flip permutation test** ([glossary](../reference/glossary.md#task-sign-flip-test)) (`cluster_permutation`, `metrics.py:369-390`). For each task, `d_t` is the mean success of A minus that of B over its seeds. The statistic is the sum of the `d_t`. Under "no difference", the sign of each non-zero `d_t` is as likely to flip as not, so the test flips them at random 10,000 times with `random.Random(0)` and counts how often the absolute sum reaches the observed one: `p = (1 + hits) / (1 + 10000)`. The fixed seed makes it deterministic.

Run offline on a copy of the pinned commit, with the two smoke runs (the folder names are shortened):

```text
$ python -m bench run --domain home --suite compare out/oracle out/naive
household benchmark: python -m bench.suites.home.cli compare out/oracle out/naive
paired McNemar test on (task, seed): A = out/oracle  B = out/naive
| n_pairs | success A | success B | b (A ok, B fail) | c (A fail, B ok) | statistic | p | method |
|---|---|---|---|---|---|---|---|
| 40 | 0.8250 | 0.6250 | 8 | 0 | 0.0000 | 0.0078 | exact_binomial |

2 seeds per task: seeds of one task are correlated, so use the task-level tests below for claims (docs/metrics.md).
| test | n | statistic | p |
|---|---|---|---|
| McNemar on per-task majority (exact_binomial) | 20 tasks | 0.0000 | 0.0625 |
| task sign-flip permutation (10000 perms) | 20 tasks | 4.0000 | 0.0324 |
```

Three tests, three answers to slightly different questions:

| test | unit | b, c | p |
|---|---|---|---|
| McNemar on (task, seed) pairs | 40 pairs | 8, 0 | 0.0078 |
| McNemar on per-task majority | 20 tasks | 5, 0 | 0.0625 |
| task sign-flip permutation | 20 tasks | sum of `d_t` = 4.0 | 0.0324 |

Five tasks are won by the oracle and none by the naive planner, but five against zero is just short of 0.05 in an exact test. The pair test looks more certain than the data allows. The printed note says to use the task-level tests for claims. The two task-level tests disagree about the 0.05 line, which is what a 20-task run should do. A real comparison needs far more tasks. The same command against the floor planner of [chapter 7](planners-as-plugins.md) gave b = 33, c = 0, a chi-square p printed as `0.0000`, and task-level p of 0.0001 for both tests.

### The interval of one planner: Wilson, then task-clustered

The **Wilson interval** ([glossary](../reference/glossary.md#wilson-interval)) is the score interval for k successes in n trials (`wilson`, `metrics.py:27-35`). For 33 of 40 it is [0.6805, 0.912546]. The framework guide calls the interval in the headline a Wilson interval; that is right, and the code refines it. The headline `success_ci95` is the Wilson interval at an **effective sample size**, and the plain one is kept as `success_ci95_episode`. The steps (`clustered`, `metrics.py:48-74`):

1. Group the 0/1 outcomes by task: k tasks, n episodes, mean p.
2. Estimate the **intraclass correlation** (ICC): how alike two episodes of one task are compared with two episodes of different tasks. One-way ANOVA estimator, floored at 0.
3. The **design effect** ([glossary](../reference/glossary.md#design-effect)) is `deff = 1 + (m0 - 1) * ICC`, where `m0` is the mean cluster size from the ANOVA, never below 1.
4. The effective sample size is `n_eff = n / deff`: how many independent episodes the 40 are worth.
5. The interval is Wilson at `n_eff` in place of n.

With one episode per task, `deff` is 1 and the two intervals are equal. The real values of the two smoke runs, from their `summary.json` (a smoke run, not a result):

| planner | successes | `success_ci95` (headline) | `n_eff` | ICC | design effect | `success_ci95_episode` (plain) |
|---|---|---|---|---|---|---|
| oracle | 33 of 40 | [0.667847, 0.917035] | 34.503817 | 0.159292 | 1.159292 | [0.6805, 0.912546] |
| naive | 25 of 40 | [0.450741, 0.771945] | 31.319149 | 0.277174 | 1.277174 | [0.470324, 0.75777] |

Here the clustered interval is a little wider on both sides, because two seeds of 20 tasks carry little clustering (ICC 0.16 for the oracle). Seeds that agree within a task show the effect more clearly. This script builds two synthetic layouts of 20 tasks times 2 seeds, both with 33 successes of 40; it holds no task data:

```python
def episodes(successes_per_task):          # 2 seeds per task: the list gives 0, 1 or 2 successes for each task
    return [{"task_id": f"t{i}", "success": j < s} for i, s in enumerate(successes_per_task) for j in range(2)]


layouts = {"seeds disagree": [2] * 13 + [1] * 7,            # 33 successes of 40
           "seeds agree":    [2] * 16 + [1] * 1 + [0] * 3}  # 33 successes of 40
for name, per_task in layouts.items():
    e = episodes(per_task)
    k = sum(x["success"] for x in e)
    c = clustered(e)
    print(name, k, "of", len(e), "| plain", wilson(k, len(e)), "| n_eff", c["n_eff"], "icc", c["icc"], "| clustered", c["ci95"])
```

(The script imports `clustered` and `wilson` from `bench.suites.home.metrics`.) Output:

```text
seeds disagree 33 of 40 | plain [0.6805, 0.912546] | n_eff 40.0 icc 0.0 | clustered [0.6805, 0.912546]
seeds agree 33 of 40 | plain [0.6805, 0.912546] | n_eff 21.800948 icc 0.834783 | clustered [0.621396, 0.931229]
```

Same 33 of 40, but when the seeds agree the 40 episodes are worth about 22 independent ones and the interval widens from 0.23 to 0.31 in width. The estimator is floored at 0, so a layout with negative correlation gets no credit for it.

### The factory campaigns: another method

The campaign suites compare arms with the task as the unit, with no McNemar (`bench/stats.py:1-60`, see [campaign statistics](../modules/campaign-statistics.md)):

1. Each measure is **averaged over the repeats** of a task (`per_task`).
2. An arm **wins** a task if its success is higher and **loses** if lower. When success is equal, a distance shorter than the baseline's by more than the tie band `max(0.5 m, 5 % of the baseline's distance)` is a win, longer is a loss, anything else is a tie.
3. An **exact sign test** ([glossary](../reference/glossary.md#sign-test)) on the wins and losses, ties dropped (`sign_test`).
4. A **bootstrap interval** ([glossary](../reference/glossary.md#bootstrap-interval)) of the paired differences: 10,000 resamples, seed 0 (`boot_ci`).

Run offline on synthetic data: six tasks, one repeat, arm B against arm A.

```python
print([sign_test(w, l) for w, l in ((0, 0), (6, 0), (5, 0), (3, 3), (9, 1))])
# six tasks, one repeat: (success of B, success of A, distance of B, distance of A)
cells = [(1, 0, 10, 10), (1, 0, 10, 10), (1, 1, 6, 10), (1, 1, 10.4, 10), (1, 1, 10, 6), (0, 1, 10, 10)]
rows = []
for t, (sb, sa, db, da) in enumerate(cells):
    for arm, s, d in (("B", sb, db), ("A", sa, da)):
        rows.append({"task": t, "arm": arm, "seed": 0, "success": s, "distance_m": d, "wrong_done": 0, "questions": 0, "t_sim": 0})
c = compare(rows, "B", "A")
print(c["n_tasks"], c["combined"])
print(c["success_only"], c["distance_only"])
```

(`sign_test` and `compare` come from `bench.stats`.)

```text
[1.0, 0.03125, 0.0625, 1.0, 0.021484375]
6 {'wins': 3, 'losses': 2, 'ties': 1, 'p': 1.0}
{'wins': 2, 'losses': 1, 'p': 1.0} {'wins': 1, 'losses': 1, 'p': 1.0}
```

Read the second line: three wins (two on success, one on a 4 m shorter distance), two losses (one on success, one on a 4 m longer distance), one tie (a 0.4 m difference is inside the 0.5 m band). Six wins against none is the smallest count with p below 0.05 (0.03125); five against none is not (0.0625). The campaign's own noise check is the **A/A arm** ([glossary](../reference/glossary.md#aa-arm)) `A2`, which repeats the baseline `A`: the difference between `A2` and `A` is how much noise alone can produce.

### One quoted aggregate

The household benchmark has one pre-registered comparison of two arms. The file `docs/home/bench/d5_final_result.md` in the repository reports, measured on 2026-11-18 over 1,200 episodes per arm, a success count of **887 against 897 of 1,200** and a paired p value of **0.253**. That is no detectable difference between the two arms. This site quotes the aggregate only and shows nothing from the underlying records.

!!! note "General knowledge, not verified here"
    The statistical properties of McNemar's test, of permutation tests, of the Wilson interval and of the bootstrap are textbook material that this repository's code does not prove. The code's own docstring cites Kish (1965) and Donner and Klar (2000) for the design effect. For the tests, use a statistics textbook, for example the chapters on paired binary data in Agresti's *Categorical Data Analysis* and on the bootstrap in Efron and Tibshirani's *An Introduction to the Bootstrap*. I did not check these references against the text.

!!! code "Where in the code"
    - McNemar: [`metrics.py#L419-L437`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/metrics.py#L419-L437); `compare` with the task-level tests: [`#L401-L416`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/metrics.py#L401-L416)
    - Per-task majority and the sign-flip test: [`#L369-L398`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/metrics.py#L369-L398)
    - Wilson and the clustered interval: [`#L27-L74`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/metrics.py#L27-L74)
    - Campaign statistics: [`bench/stats.py#L1-L60`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/stats.py#L1-L60)

    The links resolve after the owner pushes this commit. Module pages: [metrics and compare](../modules/home-metrics-and-report.md), [campaign statistics](../modules/campaign-statistics.md).

## What this means when you use it

- Compare planners on the same split, profile, seeds, language and budgets, and say how many tasks you used. Check that `data_sha` and `profile_sha` in `summary.json` `config` agree.
- With more than one seed per task, quote the task-level tests, not the first row. The (task, seed) p value is the smallest and the least safe.
- Read `n_eff` next to the interval. A wide gap between `success_ci95` and `success_ci95_episode` means the seeds of a task agree and you have fewer independent tests than episodes.
- A p value above 0.05 is not proof of no difference. The aggregate above (887 against 897 of 1,200, p = 0.253) says "none detected" with 1,200 episodes per arm.
- `compare --json` stores the first folder under the key `a` and the second under `b_dir`, while `b` is a count. Read the keys before you script against them.

**Next:** [7. Planners as plug-ins →](planners-as-plugins.md)
