---
sources: [symbolic_robot/result.py, symbolic_robot/clock.py, symbolic_robot/rng.py, symbolic_robot/__init__.py, tests/test_core.py]
verified_at: a5cc7a4943aa
---

# Results, simulated time and seeded draws

!!! abstract "In this page"
    - The three small primitives of the engine core: `Result` (what a skill call returns), `SimClock` (simulated time) and `Rng` / `CallDraws` (draws that depend only on the seed).
    - Why the same seed gives the same fault at the same event, even when two planners ask for different things first. A real run is shown.
    - What each one returns, with values taken from real runs, and where they can surprise you.
    - Current behaviour: no domain uses `CallDraws` at this commit. The household domain uses none of the three (it has its own).

!!! code "Where in the code"
    - [`result.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/result.py): `Result`
    - [`clock.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/clock.py): `SimClock`
    - [`rng.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/rng.py): `Rng`, `derive_seed`, `canon_args`, `CallDraws`, `Draw`
    - [`__init__.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/__init__.py): re-exports `SimClock`, `Result`, `CallDraws`, `Rng`
    - Tests: [`tests/test_core.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/tests/test_core.py)

## Why these three exist

A skill in this engine does not move a real robot. It returns an outcome that the engine draws from declared probabilities over a small symbolic world (see [../learn/symbolic-worlds.md](../learn/symbolic-worlds.md)). Three things are needed for that to be a fair benchmark:

| need | primitive |
|---|---|
| A skill reports success or failure, and also what really happened, without telling the planner | `Result` |
| Time passes, but nothing ever waits in real time | `SimClock` |
| A random fault is the same fault on every run of the same seed | `Rng`, `CallDraws` |

The factory domain uses `Result`, `SimClock` and `Rng` (`domains/factory/robot.py`, `user.py`). The household domain does not import any of them: it has its own clock, its own random streams and its own result type, and takes only `BaseDomain` from the core. Words used here are in the [glossary](../reference/glossary.md).

## Result: what a skill returns

`Result` is a dataclass. `ok` says whether the skill worked. `truth` holds what really happened in the simulation: the robot (and so the planner) never sees it, but the live backend logs it ([live-backend-and-sim-commands.md](live-backend-and-sim-commands.md)) and the judge can read it.

| field | type | unit | meaning | example (run) |
|---|---|---|---|---|
| `ok` | bool | | did the skill report success | `False` |
| `msg` | str | | text the planner may see | `"no"` |
| `code` | str or None | | a failure code when `ok` is false (a robot_agent `FailureCode` value, by the source comment) | `"absent"` |
| `data` | dict | | extra values returned with the result | `{"x": 1}` |
| `duration_s` | float | s of simulated time | how long the call took | `0.0` |
| `truth` | dict | | the real cause: a fault, a hazard, the object | `{}` |

`to_legacy()` gives the dict that robot_agent skill functions return: `isdone`, `msg`, `code` only when it is set, then every key of `data`.

```python
from symbolic_robot import Result
print(Result(False, "no", "absent", data={"x": 1}).to_legacy())
print(Result(True, "ok").to_legacy())
```

Output (run):

```text
{'isdone': False, 'msg': 'no', 'code': 'absent', 'x': 1}
{'isdone': True, 'msg': 'ok'}
```

`truth` is not in the legacy dict. That is the point: the planner gets `isdone`, `msg` and `code`; the benchmark keeps `truth` to find silent failures.

## SimClock: time that only moves when told

`SimClock` has one number, `t`, and one method. A skill reports its duration; the robot calls `advance(dt)`; `t` grows by `dt` and the new `t` is returned. There is no `sleep` and no wall clock anywhere in it.

```python
from symbolic_robot import SimClock
c = SimClock()
print(c.advance(5.0), c.advance(2.5), c.t)
```

Output (run):

```text
5.0 7.5 7.5
```

The core clock does not check the sign of `dt`. A negative duration would move time backwards. The household domain's own clock does raise on a negative step; the core one does not.

## Rng: a draw depends on a key, not on order

This is the part to understand. A normal random generator gives one stream: the third call returns the third number, so a plan that makes one extra call earlier shifts every later fault. Then two planners on the "same seed" would meet different faults and a comparison would be unfair.

`Rng` has no stream. Each draw is the SHA-256 hash of three things: the seed, a **key** you pass, and `n`, the number of times that key has been asked so far. The first eight bytes of the hash, read as an integer and divided by 2^64, are the float. Another key never moves `n` of this key, so the order of unrelated calls does not matter. No wall clock and no Python `hash()` is involved (the latter changes between runs).

```python
class Rng:
    def __init__(self, seed: int):
        self.seed = int(seed)
        self._n: dict = {}

    def uniform(self, *key) -> float:
        k = "|".join(str(x) for x in key)
        n = self._n[k] = self._n.get(k, 0) + 1
        h = hashlib.sha256(f"{self.seed}|{k}|{n}".encode()).digest()
        return int.from_bytes(h[:8], "big") / 2 ** 64

    def chance(self, p: float, *key) -> bool:
        return p > 0 and self.uniform(*key) < p

    def pick(self, seq, *key):
        seq = list(seq)
        return seq[min(len(seq) - 1, int(self.uniform(*key) * len(seq)))] if seq else None
```

Source: [`symbolic_robot/rng.py` L15-L31](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/rng.py#L15-L31).

| call | input | output |
|---|---|---|
| `Rng(seed)` | episode seed, int | a generator with an empty counter |
| `uniform(*key)` | any parts; each goes through `str()` and the parts are joined with a vertical bar | float in [0, 1) |
| `chance(p, *key)` | probability `p` in [0, 1] | `True` with probability `p` |
| `pick(seq, *key)` | a sequence | one element, or `None` for an empty sequence |

### Same seed, same draw (run)

```python
import hashlib
from symbolic_robot import Rng

r = Rng(5)
print(r.uniform("x"), r.uniform("x"), r.uniform("y"))
print(Rng(5).uniform("x"), Rng(5).uniform("x"))      # new generators, same seed
print(Rng(6).uniform("x"))                           # another seed
a = Rng(5); a.uniform("x"); a.uniform("y")
print(Rng(5).uniform("y"))                           # "y" asked first, on its own
h = hashlib.sha256(b"5|x|1").digest()                # by hand: seed|key|n
print(int.from_bytes(h[:8], "big") / 2**64)
```

Output (run):

```text
0.10508243923211916 0.3446454403780886 0.5203153170348381
0.10508243923211916 0.10508243923211916
0.7912094272785382
0.5203153170348381
0.10508243923211916
```

Read it line by line:

- The second use of `"x"` gives a new number (0.3446...): `n` went from 1 to 2.
- Two separate `Rng(5)` objects give the same first `"x"` draw, 0.10508243923211916. That is determinism by seed.
- Seed 6 gives a different number.
- `"y"` is 0.5203153170348381 whether or not `"x"` was drawn before it. That is order independence.
- The last line recomputes the first draw by hand from the string `5|x|1`: the same number.

Other examples from the same run: `Rng(4).chance(0.5, "hw", "move")` is `True` (the draw is 0.2000...) and `Rng(5)` for the same key draws 0.8786, so it is `False`. `pick([], "k")` returns `None`, and `Rng(3).pick(["a", "b", "c"], "k")` returns `"a"`.

### The same seed in a real domain (run)

The factory robot asks `Rng` for each fault with a key made of the event: for example `chance(detector_miss, "miss", <object id>)` in `find` (`domains/factory/robot.py`). So the n-th look for an object gets the same answer in every run with the same seed. This run uses the `stress` profile (detector miss 0.30) on `small_workshop`, looks for the caliper 16 times, and writes `S` for seen and `m` for missed. The third line makes four extra `move` calls in the middle of the run; the plan is different but the finds are the same.

```text
seed 1 extra_moves=False: SSmmSmSSSSmmSSmm
seed 1 extra_moves=False: SSmmSmSSSSmmSSmm
seed 1 extra_moves=True: SSmmSmSSSSmmSSmm
seed 4 extra_moves=False: mmSSSSSSSmmSSSSS
seed 5 extra_moves=False: SmmSSmSSmSSmSSSS
```

The script is: make `LiveBackend(factory, "small_workshop", "stress", seed)`, call `move` to `vise_bench@bench_area`, then call `find` with `obj="caliper"` 16 times, adding a `move` away and back before every third find when `extra` is on. Seeds 1, 4 and 5 differ from one another; repeating seed 1 does not.

!!! note "Where the guarantee stops"
    The guarantee is per key. It holds as long as two runs ask for the same key in the same count. If a planner looks for the caliper once more than another planner, the n-th draw for that key is shifted for it. Ordering of other keys does not matter.

## CallDraws: one vector per skill call

`CallDraws` is the second scheme. Instead of one key per event it gives one fixed vector of `n_slots` floats (default 16) for each skill call, keyed by the seed, the skill name, the arguments and how many times this skill has been called with these arguments. Each rule inside a skill is meant to read its own slot of the vector.

```python
    def begin(self, skill: str, args: dict) -> "Draw":
        key = (skill, canon_args(args))
        n = self._nth[key] = self._nth.get(key, 0) + 1
        return Draw(self, skill, key[1], n)

    def reset(self) -> None:
        self._nth.clear()


class Draw:
    def __init__(self, owner: CallDraws, skill: str, args: str, n: int):
        self.owner, self.skill, self.args, self.n = owner, skill, args, n
        self.u = self._vec(0)

    def _vec(self, attempt: int) -> list:
        rng = random.Random(derive_seed(self.owner.seed, self.skill, self.args, self.n, attempt))
        return [rng.random() for _ in range(self.owner.n_slots)]

    def attempt(self, k: int) -> list:
        return self.u if k == 0 else self._vec(k)
```

Source: [`symbolic_robot/rng.py` L51-L70](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/rng.py#L51-L70).

`derive_seed(*parts)` is SHA-256 over the parts joined with `|`, first eight bytes as an int. It seeds a standard `random.Random`, which then gives the 16 floats. `attempt(k)` is the vector of the k-th internal retry of one call (`attempt(0)` is `u` itself).

| name | type | meaning | example (run) |
|---|---|---|---|
| `CallDraws(seed, n_slots=16)` | int, int | a generator for one episode | `CallDraws(7)` |
| `begin(skill, args)` | str, dict | start one call; returns a `Draw` | `("pick", {"o": 1})` |
| `Draw.n` | int | 1 for the first call with these arguments | `1` |
| `Draw.u` | list of 16 floats | the vector | first four: `[0.8654, 0.678, 0.317, 0.6405]` |
| `Draw.attempt(k)` | int | the vector of attempt k | `attempt(1)` differs from `u` |

Run:

```python
from symbolic_robot.rng import CallDraws, canon_args
d = CallDraws(7); b = d.begin("pick", {"o": 1})
print(b.n, [round(x, 4) for x in b.u[:4]], len(b.u))
d2 = CallDraws(7); d2.begin("move", {"to": "x"}); b2 = d2.begin("pick", {"o": 1})
print(b2.n, b2.u == b.u)                      # a call before it does not matter
c = d.begin("pick", {"o": 1}); print(c.n, c.u[:2])   # second call, same arguments
print(canon_args({"o": 1, "node": object(), "wait": 1, "log_fn": 2}), canon_args({"o": "1"}))
```

Output (run):

```text
1 [0.8654, 0.678, 0.317, 0.6405] 16
1 True
2 [0.221377658675871, 0.1177913233078518]
{"o": 1} {"o": "1"}
```

Two generators with seed 7 give the same vector for the first `pick`, even though the second one made a `move` call first. The second `pick` with the same arguments gets a different vector.

!!! warning "Current behaviour: no domain uses CallDraws"
    At this commit `CallDraws` is a core helper that no domain uses. The factory uses `Rng`; the household domain uses its own streams with a 14-slot vector. The only caller in the repo is `tests/test_core.py` (lines 32-41). It is available to a new domain. Do not expect it in the factory's code path.

## Failure modes and surprises

| symptom | cause | what to do |
|---|---|---|
| `canon_args` drops `node`, `wait` and `log_fn`: changing a callback does not change the draw | line 40 of `rng.py` filters those three names | none; this is intended |
| `{"o": 1}` and `{"o": "1"}` are different calls for `CallDraws` | `canon_args` is JSON, which keeps the type | pass the same types in every run |
| `Rng` treats `("a", "b")` and `("a|b",)` as the same key, and `1` and `"1"` as the same key | the key is the parts after `str()`, joined with a vertical bar (checked: both pairs give equal draws) | keep the key parts free of the bar and use a fixed shape |
| `chance(0, ...)` does not use up a draw | `p > 0 and ...` short-circuits, so `n` does not grow | harmless: the counter is per key |
| `pick([])` returns `None`, no error | explicit empty check | the caller handles `None` |
| `SimClock.advance(-1)` moves time back | no check in the core clock | report non-negative durations |
| An unrelated change in a skill's key names changes the faults of old seeds | the key text is part of the hash | treat key text as part of the result format |

No function here raises on normal input.

## How it is verified

`tests/test_core.py` (pytest is not installed here, so the functions were called by hand through a small stand-in for `pytest.raises`; all of the functions below passed that way, which is not a pytest run):

- `test_rng_is_deterministic_and_keyed_not_ordered`: same seed gives the same draw, another seed another, the n-th use of a key is new, another key does not shift this one.
- `test_rng_uniform_is_uniform`: 4,000 draws have a mean within 4 standard errors of 0.5.
- `test_call_draws_vector_is_stable_per_call`: 16 floats in [0, 1), `n` is 1, a call before it does not matter, the second call differs, `attempt(1)` is stable.
- `test_clock_moves_only_by_reported_durations`: 5.0 then 2.5 gives 7.5.
- `test_result_legacy_shape`: the two legacy dicts shown above.

Next: [profiles.md](profiles.md) (the parameters these draws are compared with), [domain-protocol.md](domain-protocol.md), and the learn page [../learn/determinism.md](../learn/determinism.md).
