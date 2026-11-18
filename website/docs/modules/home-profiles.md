---
sources:
  - symbolic_robot/domains/home/profiles/__init__.py
  - symbolic_robot/domains/home/profiles/validate.py
  - symbolic_robot/domains/home/profiles/__main__.py
  - symbolic_robot/domains/home/profiles/ideal/profile.yaml
  - symbolic_robot/domains/home/profiles/stress/profile.yaml
  - symbolic_robot/domains/home/profiles/real/skills.yaml
  - symbolic_robot/domains/home/profiles/real/user.yaml
  - symbolic_robot/domains/home/profiles/real/safety.yaml
  - symbolic_robot/domains/home/profiles/real/reach.yaml
  - symbolic_robot/domains/home/consistency.py
  - symbolic_robot/domains/home/report.py
  - tests/home/sim/test_profiles.py
  - tests/home/sim/test_consistency.py
verified_at: a5cc7a4943aa
---

# Household profiles and calibration

!!! abstract "In this page"
    You learn what a household profile is, how the three profiles `ideal`, `real` and `stress` are built from one calibrated
    file set, how many of the 113 numbers come from a source and how many are assumed, and how the validator keeps this honest.
    You can run the validator and the profile commands offline.

## What a profile is

A profile is the set of numbers that says how the simulated robot and the simulated people behave: failure rates, durations,
speeds, speech-recognition error rates, safety distances. The household domain has three:

| profile | meaning | how it is made |
|---|---|---|
| `real` | the calibrated one; the benchmark's default | read from four YAML fragments |
| `ideal` | no failures, no noise, people stay still | derived from `real` by zeroing rules |
| `stress` | harder: failure probabilities doubled | derived from `real` by scaling rules |

`ideal` and `stress` store no numbers of their own, only rules applied to `real`. So the three profiles always have the same
113 parameter names. The idea behind declared, sourced outcomes is in [Declared outcomes](../learn/declared-outcomes.md); the core
engine's own profile loader is in [Profiles](profiles.md). The household domain has its own loader (`domains/home/profiles/`),
a design choice described on [Household outcomes](home-outcomes.md).

## The parameter registry

`PARAM_REGISTRY` in `profiles/__init__.py` lists every parameter the code reads. Each entry has a `kind` (probability, range of
seconds, speed, ...) and a `role`. `real` must hold exactly these keys, no more and no fewer; the validator checks it.
I counted them on the pinned copy:

| role | count | meaning |
|---|---|---|
| `failure` | 28 | a probability or rate of something going wrong in the robot |
| `recovery` | 7 | the chance that a retry or a wait clears a fault |
| `nominal` | 61 | durations, speeds, distances, geometry, switches |
| `user_noise` | 15 | speech recognition errors, wrong answers, interruptions |
| `safety_noise` | 2 | detection miss and latency jitter of the safety monitor |
| total | 113 | |

The `real` values live in four fragments, merged by `load_real_fragments` (a duplicated key is an error):

| fragment | parameters |
|---|---|
| `skills.yaml` | 53 |
| `user.yaml` | 32 |
| `safety.yaml` | 21 |
| `reach.yaml` | 7 |

## Sourced and assumed

Every entry carries `kind`, `role`, `value` and a `note` of at least 20 characters. In addition it is one of two things:

- **sourced**: it has a `source` (an arXiv id, a DOI or a URL) and a `where` (a section or figure), and a note that explains how the
  published number was used (the note of `find.p_miss` below is an example);
- **assumed**: it has `assumed: true` and a note that explains the assumption (for example what was searched and not found). An assumed entry
  may carry an `anchor`, a reference that bounds or motivates the value without stating it.

On the pinned copy: **58 entries have a source and 55 are assumed**, and no entry is both (58 + 55 = 113). Of the 58 sourced
entries, 28 have the role `nominal`, 17 `failure`, 8 `user_noise` and 5 `recovery`. Of the 55 assumed ones, 33 are `nominal`,
11 `failure`, 7 `user_noise`, 2 `recovery` and 2 `safety_noise`. So a good part of the failure model, and nearly all of the
safety noise, rests on stated assumptions. That is on purpose: the validator lists them, and a result can be read against it.

Here is one sourced entry in full, the camera miss rate (`profiles/real/skills.yaml`):

```yaml
  find.p_miss:
    kind: prob
    role: failure
    value: 0.093
    source: https://arxiv.org/abs/2401.12202
    where: "Sec. III-D"
    note: "OK-Robot: semantic-memory retrieval failure (object not found or ambiguous) in 9.3 % of trials, the first-ranked failure cause (Fig. 4: 35 'localized wrong or no object' of 375 trials). Used per find call when the object is visible; move.p_fail excludes this share so it is not counted twice."
```

[symbolic_robot/domains/home/profiles/real/skills.yaml:142-148](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/home/profiles/real/skills.yaml#L142-L148)

## Deriving `ideal` and `stress`

The two derived profiles are short files:

```yaml
# `ideal`: derived from `real`. No failures, no noise, static people; durations and safety formulas
# unchanged (docs/profiles.md). Rules apply in order; a rule for a parameter that `real` does not
# hold is skipped and noted.
profile: ideal
derive_from: real
rules:
  - {match: {role: [failure, user_noise, safety_noise]}, set: zero}   # every probability / rate -> 0
  - {param: pose.sigma_m, set: 0.0}                                    # exact pose readings
  - {param: user.motion.rate_per_h, set: 0.0}                          # people do not move
note: "No failures, no noise, static people; durations and safety formulas unchanged."
```

[symbolic_robot/domains/home/profiles/ideal/profile.yaml:1-10](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/home/profiles/ideal/profile.yaml#L1-L10)

```yaml
# `stress`: derived from `real` (docs/profiles.md). Every role:failure probability p -> min(cap, p x factor),
# every role:failure rate r -> r x factor; recovery probabilities are NOT scaled (that would make stress
# easier). Sourced worst cases in `overrides` replace the scaled value.
profile: stress
derive_from: real
scaling:
  failure_prob_factor: 2.0
  cap: 0.95
  assumed: true
  note: "The research-notes methodology (R3) sweeps failure rates x0.5 / x1 / x2; stress is the x2 end. A design choice, not a measured value."
overrides:
  open.p_fail:
    value: {door: 0.5, drawer: 0.5}
    source: https://arxiv.org/abs/2401.14403
    where: "Abstract, Fig. 6"
    note: "Articulated-object mobile manipulation: an unadapted behaviour-cloning policy succeeds about 50 % on novel doors / drawers (about 95 % after adaptation). Worst case for both door and drawer."
  # BEGIN user-safety overrides (robot-human-safety edits only inside this block)
  # END user-safety overrides
```

[symbolic_robot/domains/home/profiles/stress/profile.yaml:1-18](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/home/profiles/stress/profile.yaml#L1-L18)

`derive` in `profiles/__init__.py` applies them:

- `ideal`: every `prob` and `prob_map` of the roles `failure`, `user_noise` and `safety_noise` becomes 0, every `rate_per_h`
  becomes 0; then `pose.sigma_m` is 0 (exact pose readings) and `user.motion.rate_per_h` is 0 (people do not move). Durations and
  the safety formulas stay the same as in `real`.
- `stress`: every `failure` probability `p` becomes `min(0.95, 2 p)` and every `failure` rate doubles. Recovery probabilities are not
  scaled (that would make `stress` easier). The override replaces `open.p_fail` by 0.5 for doors and drawers, a sourced worst case.
  The `user_noise` and `safety_noise` roles are not scaled.

Real values of three entries in the three profiles (run offline):

| parameter | `ideal` | `real` | `stress` |
|---|---|---|---|
| `find.p_miss` | 0.0 | 0.093 | 0.186 |
| `pick.p_fail` (low / medium / high clutter) | 0.0 | 0.0534 / 0.0658 / 0.1027 | 0.1068 / 0.1316 / 0.2054 |
| `open.p_fail` (door / drawer) | 0.0 / 0.0 | 0.21 / 0.167 | 0.5 / 0.5 |

## The profile hash and overrides

A `Profile` object has `get(name)`, `entry(name)` for the full entry, `values()`, and `sha`: a SHA-256 over the sorted values as
compact JSON. The household benchmark writes this hash into every run as `profile_sha` (`bench/suites/home/runner.py:298`), and
the selftest does the same, so a result says which numbers produced it. Changing any value changes the hash.

A name may carry overrides for sensitivity runs: `real+find.p_miss=0.2`. Only existing scalar numeric parameters can be set, and
a probability must stay in [0, 1]. Run offline:

```python
from symbolic_robot.domains.home.profiles import load_profile, ProfileError

a = load_profile("real")
b = load_profile("real+find.p_miss=0.2")
print(a, b)
print(a.get("find.p_miss"), b.get("find.p_miss"), b.entry("find.p_miss").get("override"), b.sha == a.sha)
for bad in ("bogus", "real+nope.x=1", "real+find.p_miss=2"):
    try:
        load_profile(bad)
    except ProfileError as e:
        print("ProfileError:", e)
```

```text
Profile('real', 113 params, sha=fe93eed0af) Profile('real+find.p_miss=0.2', 113 params, sha=110a9ea22b)
0.093 0.2 True False
ProfileError: unknown profile 'bogus' (have ideal, real, stress)
ProfileError: real+nope.x=1: unknown parameter 'nope.x'
ProfileError: real+find.p_miss=2: find.p_miss=2.0 is not a probability
```

## The validator

`python -m symbolic_robot.domains.home.profiles validate` checks seven rules and prints the assumed parameters. Run from the
repository root (offline, needs `pyyaml`):

```text
$ python -m symbolic_robot.domains.home.profiles validate
PASS  rule 1: real loads, 113 params, key set == PARAM_REGISTRY (113)
PASS  rule 2: every entry has kind, role, value, note (>= 20 chars); values type-check
PASS  rule 3: sourced entries: source URL, where, listed in docs/calibration.md
PASS  rule 4: assumed entries have a note; anchors valid and listed (55 assumed)
PASS  rule 5: ideal: every failure / noise probability is 0, people static, keys == real
PASS  rule 6: stress: derived from real by the documented scaling + sourced overrides
PASS  rule 7: docs/calibration.md exists and lists every source (61 distinct)
assumed: 55 params
  - ask.timeout_s
  - asr.far_threshold_m
  ...
== profiles validate: 0 rule(s) failed, 0 warning(s)
```

The `...` stands for the other 53 names; the real output lists all 55. The calibration document named in rules 3 and 7 lists every source. The messages call it `docs/calibration.md`; the validator
reads it from a fixed path in the household part of the repository's `docs/` folder, so run the command in a full checkout. `--strict` also fails on warnings. The other commands:

| command | does |
|---|---|
| `profiles list` | prints `ideal`, `real`, `stress` |
| `profiles show NAME` | prints the resolved profile as sorted JSON with its `sha` |
| `profiles consistency [--n N] [--seed S] [--strict]` | simulates calls and compares the rates with the profile (not run for this page) |

## The consistency check

`consistency` (in `consistency.py`) is the second guard. For every failure parameter of `real` it makes 20,000 seeded calls
(`--n`) in the parameter's reference context and tests the empirical rate against the profile with an exact two-sided binomial test
at the 0.1 % level. It also runs random traces through every house and the three profiles and looks for impossible outcomes: a
`dropped` without holding anything, a `grasp_failed` outside `pick` and `handover`, a success effect after a failure, a duration outside its cited
range. It makes 20,000 calls per parameter, so it was not run for this page.

`python -m symbolic_robot.domains.home.report hw-rates` is a small report on one parameter pair; its output is on
[Household outcomes](home-outcomes.md).

!!! note "Privacy of notes"
    Some notes in `real/skills.yaml` name the retired standalone package that the household domain came from. This site does not
    reproduce them. Read them in the file if you need the full reasoning behind a value.

!!! code "Where in the code"
    - `PARAM_REGISTRY`, `Profile`, `derive`, `load_profile` in `symbolic_robot/domains/home/profiles/__init__.py`.
    - The rules in `profiles/validate.py`; the command line in `profiles/__main__.py`.
    - Fragments in `profiles/real/`; derivation specs in `profiles/ideal/profile.yaml` and `profiles/stress/profile.yaml`.

## Edge cases and failure modes

| symptom | cause | fix |
|---|---|---|
| `ProfileError: unknown profile` | a name other than the three, or a bad override | use `ideal`, `real`, `stress` or `real+param=value` |
| validator rule 1 fails | a parameter is in the code registry but not in `real` (or the reverse) | add the entry to a fragment, with kind, role, value, note |
| validator rule 3 or 4 fails | a source or anchor is missing from the calibration document | list it there |
| two fragments define one key | `load_real_fragments` reports it | keep each key in one fragment |
| a result cannot be compared with an older one | the `profile_sha` differs | the numbers changed; compare only equal hashes |

## How it is verified

`tests/home/sim/test_profiles.py` checks that the three profiles have the same keys, that `ideal` has zero failures and `stress` is
the scaled `real`, that the validator passes in strict mode, the source normaliser, and the override syntax.
`tests/home/sim/test_consistency.py` covers the consistency check. These tests were not run with pytest for this page; the
validator and the commands above were run directly.
