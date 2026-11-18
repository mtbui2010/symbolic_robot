---
sources: [symbolic_robot/profile.py, symbolic_robot/domains/factory/profiles/real.yaml, symbolic_robot/domains/home/profiles/__init__.py, symbolic_robot/domains/home/profiles/real/skills.yaml, symbolic_robot/domains/home/profiles/stress/profile.yaml, symbolic_robot/domains/home/outcomes.py, symbolic_robot/domains/home/report.py]
verified_at: a5cc7a4943aa
---

# Declared outcomes and the three profiles

!!! abstract "In this page"
    - Every failure rate of the simulator is a named number with a source label, in a YAML file. Nothing is hidden in code. An invented number says so.
    - You get three [profiles](../reference/glossary.md#profile) from one file: `real` (the declared values), `ideal` (no failures) and `stress` (failures made more likely). The factory domain scales by 3, the household domain by 2.
    - The household `real` profile has 113 parameters: 58 have a source and 55 are [assumed](../reference/glossary.md#assumed-parameter), and the validator lists the assumed ones. A real run measures the declared miss rate back from 2,000 seeds.

## The question: where does "10 % of finds fail" come from?

A benchmark that says "planner A succeeds on 71 % of tasks" is only as honest as the failure rates behind it. If the simulator misses an object 10 % of the time, somebody chose 0.10. This engine asks that person to write the number down, with where it came from. It refuses to load a parameter that has no value and no source label.

## A parameter is a record

Core profiles (the factory domain) have one record per parameter, in `real.yaml`:

```yaml
  slip:
    {kind: prob, value: 0.05, source: "invented, round number", note: "pick: the grip fails, the object stays"}
```

[symbolic_robot/domains/factory/profiles/real.yaml:11-12](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/factory/profiles/real.yaml#L11-L12)

The file's own header says that every number in it is invented and none is measured. That is the honest label: the factory domain is a simulated plant. The household profile is different. Its records have two more keys, `role` and `where`, and either a `source` (an arXiv id, a DOI or a URL) or `assumed: true`. Here is how the household record of the camera miss rate reads, in short: kind `prob`, role `failure`, value 0.093, source arXiv 2401.12202, where "Sec. III-D", plus a note that says how the published figure is used.

The [kinds](../reference/glossary.md#parameter-kind) say how a number is used and whether `ideal` and `stress` change it:

| kind | meaning | example |
|---|---|---|
| `prob` | a probability | factory `slip` 0.05 |
| `prob_map` | a probability per label | household `move.p_fail` by clutter: low, medium, high |
| [`split`](../reference/glossary.md#split) | shares of failure codes, which add up to 1 | household `move.split`: `blocked` 0.666667, `unreachable` 0.333333 |
| `range` | a `[low, high]` pair, drawn uniformly | household `move.fail_time_frac` |
| `number`, `map`, others | kept as they are | factory `speed_mps` 0.8 |

A `split` is used by inverse CDF over the sorted labels: add the shares in alphabetical order and take the first label whose running total is above the draw `u`.

```python
    def choose(self, key: str, u: float) -> str:
        """A label from a `split` parameter (shares per label): inverse CDF over the sorted labels."""
        split, acc = self.get(key), 0.0
        for k in sorted(split):
            acc += float(split[k])
            if u < acc:
                return k
        return sorted(split)[-1]
```

[symbolic_robot/profile.py:45-52](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/profile.py#L45-L52)

With the household `move.split`, a draw of 0.1 or 0.45 gives `blocked`, and 0.95 gives `unreachable` (run offline). The household code does the same in `outcomes.py:92-101`.

## Three profiles from one file

You write `real`. The other two are computed from it.

```python
def derived(real: "Profile", name: str) -> "Profile":
    """`ideal`: every probability 0. Other names: only when real declares `derive.<name>.scale`."""
    params = copy.deepcopy(real.params)
    if name == "ideal":
        fn = lambda v: 0.0                                           # noqa: E731
        note = "ideal profile: failure switched off"
    else:
        scale = float((real.derive.get(name) or {}).get("scale", 0))
        if scale <= 0:
            raise KeyError(name)
        fn = lambda v: min(1.0, float(v) * scale)                    # noqa: E731
        note = f"{name} profile: probabilities of real x{scale:g}, capped at 1"
    for p in params.values():
        if p.get("kind") in PROB_KINDS and p.get("ideal") != "keep":
            p["value"] = _map(p["value"], fn)
            p["source"] = f"{note} (real: {p.get('source', '')})"
    return Profile(name, params, real.derive)
```

[symbolic_robot/profile.py:71-87](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/profile.py#L71-L87)

- `ideal`: every `prob` and `prob_map` becomes 0. Durations, speeds and ranges stay.
- `stress`: every probability is multiplied by the scale and capped at 1. It exists only when `real` declares `derive.stress.scale`. The factory file declares 3.0.
- A parameter that is the probability of recovering, not of failing, says `ideal: keep` and is left alone by both ([profile.py:9-11](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/profile.py#L9-L11)).
- The derived profile rewrites the `source` label, so you can see where a number came from. Run offline on the factory domain:

| parameter | `real` | `ideal` | `stress` |
|---|---|---|---|
| `slip` | 0.05 | 0.0 | 0.15000000000000002 |
| `detector_miss` | 0.1 | 0.0 | 0.30000000000000004 |
| `speed_mps` | 0.8 | 0.8 | 0.8 |

The `ideal` label of `slip` reads "ideal profile: failure switched off (real: invented, round number)". The stray digits in 0.15000000000000002 are floating-point arithmetic of 0.05 times 3.

The household domain has its own loader, with more roles. There the derivation is a short YAML file per profile ([Household profiles](../modules/home-profiles.md)):

| | `ideal` | `stress` |
|---|---|---|
| failure probabilities | 0 | times 2, capped at 0.95 |
| user noise, safety noise | 0 | not scaled |
| recovery probabilities | not changed | not scaled (scaling them would make `stress` easier) |
| sourced override | none | `open.p_fail` is 0.5 for doors and drawers (a sourced worst case, arXiv 2401.14403) |

Real values, run offline:

| parameter | `real` | `ideal` | `stress` |
|---|---|---|---|
| `move.p_fail` (low, medium, high clutter) | 0.0067, 0.02, 0.025 | 0, 0, 0 | 0.0134, 0.04, 0.05 |
| `open.p_fail` (door, drawer) | 0.21, 0.167 | 0, 0 | 0.5, 0.5 |
| `find.p_miss` | 0.093 | 0.0 | 0.186 |

Each profile has a hash over its sorted values. They are `fe93eed0af9c` (`real`), `cfe3574d0bad` (`ideal`) and `c1f81f714ba9` (`stress`). A result that records the hash says which numbers produced it.

## Assumed is allowed, and listed

The household `real` profile has 113 parameters. Counted offline on the pinned copy: **58 have a source and 55 are assumed**, and no parameter is both. The validator checks seven rules and prints the 55 assumed names:

```text
$ python -m symbolic_robot.domains.home.profiles validate
PASS  rule 1: real loads, 113 params, key set == PARAM_REGISTRY (113)
...
PASS  rule 4: assumed entries have a note; anchors valid and listed (55 assumed)
...
== profiles validate: 0 rule(s) failed, 0 warning(s)
```

(Rules 2, 3, 5, 6 and 7 and the list of names are left out here. The check needs `pyyaml` and runs from a full checkout.) An assumed number is not hidden: it has a note that explains the assumption, and it is in a list that a reader can find. A result can then be read against it: if a conclusion changes when you move an assumed rate, say so. [Household profiles](../modules/home-profiles.md) breaks the count down by role and shows the validator in full.

The factory domain goes further in the other direction. It has no sources at all, and each number says "invented". Use it to test a planner's logic, not to estimate how a planner fares on a robot.

## The hardware-rate table

One of the household assumptions is easy to feel in numbers. `hw.p_per_motion_call` is 0.01875 per motion call, and `hw.p_persistent` (the share of faults that stay for the whole episode) is 0.5. The `hw-rates` report turns the per-call rate into a rate per task. Run offline:

```text
$ python -m symbolic_robot.domains.home.report hw-rates
profile real: hw.p_per_motion_call 0.01875, hw.p_persistent 0.5; OK-Robot 7.5% per 4-primitive trial
p_persistent  calls  any_fault(no retry)  lost(retry transients)
         0.2      4                7.29%                   1.51%
         0.2      8               14.05%                   3.01%
         0.2     12               20.32%                   4.47%
         0.5      4                7.29%                   3.73%
         0.5      8               14.05%                   7.32%
         0.5     12               20.32%                  10.78%
        0.94      4                7.29%                   6.87%
        0.94      8               14.05%                  13.27%
        0.94     12               20.32%                  19.24%
```

Read the row `0.5, 8`. An 8-call task meets some hardware fault 14.05 % of the time. If a planner retries a transient fault, 7.32 % of tasks are lost, because the rest of the faults persist. The first number does not depend on `p_persistent`; the second does, and `p_persistent` is assumed. The table lets you see how much the assumption matters: at 0.2 you lose 3.01 %, at 0.94 you lose 13.27 %.

## Declared, then measured

A declared number is a claim. You can test it by drawing many times. The factory domain: `move` to the main bench, then `find(obj="large wrench")` on `small_workshop`, for 2,000 seeds per profile (0 to 1,999), run offline on 2026-11-19. The count is the share of finds whose `truth` says `detector_miss`.

| profile | declared | measured miss among finds | finds | episodes whose `move` failed |
|---|---|---|---|---|
| `ideal` | 0 | 0.0 | 2,000 | 0 |
| `real` | 0.10 | 0.0942 | 1,954 | 46 (`hw_fault`) |
| `stress` | 0.30 | 0.3094 | 1,884 | 116 (`hw_fault`) |

Declared 0.10 gives 0.0942 (184 of 1,954); declared 0.30 gives 0.3094 (583 of 1,884). The gap is what 2,000 draws allow: for a true 0.10, the standard deviation of a share over 1,954 draws is about 0.007. The episodes that failed the `move` with a hardware fault never reached the `find`, so they are not counted among the finds. This is an experiment on the draws, not a benchmark result.

The household domain has this check built in. `consistency.py` makes 20,000 calls per failure parameter and tests the observed rate with an exact binomial test at the 0.1 % level. I did not run it here: it takes long. [Household profiles](../modules/home-profiles.md) describes it.

!!! code "Where in the code"
    - Core profile loader, `derived`, `choose`: [`symbolic_robot/profile.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/profile.py)
    - Factory profile: [`factory/profiles/real.yaml`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/factory/profiles/real.yaml)
    - Household profiles, registry, validator: [`home/profiles/`](https://github.com/mtbui2010/symbolic_robot/tree/a5cc7a4943aa/symbolic_robot/domains/home/profiles)
    - Household split and outcome rules: [`home/outcomes.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/home/outcomes.py)
    - Module pages: [Profiles](../modules/profiles.md), [Household profiles](../modules/home-profiles.md), [Household outcomes](../modules/home-outcomes.md)

## What this means when you use it

- Quote the profile with every result. The name and the hash say which numbers were used; `real` of the factory domain is invented and `real` of the household domain is partly assumed.
- A planner that ranks first on `ideal` and last on `stress` has a weakness in handling faults. A planner that ranks the same on both is not stressed by them. Run both.
- If you change a rate for a sensitivity study, change it by name and keep the hash. The household domain accepts `real+find.p_miss=0.2` as a profile name.
- Do not read a scale of 3 (factory) and a scale of 2 (household) as comparable. They are the design choices of two domains.
- Assumed numbers are a fact of the data, not a defect hidden by the engine. When a finding depends on one, name it.

**Next:** [Determinism by seed](determinism.md)
