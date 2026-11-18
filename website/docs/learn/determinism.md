---
sources: [symbolic_robot/rng.py, symbolic_robot/clock.py, symbolic_robot/domains/home/rng.py, symbolic_robot/domains/home/clock.py, symbolic_robot/domains/home/outcomes.py, symbolic_robot/domains/home/skills.py, bench/runner.py, bench/suites/home/env.py, bench/suites/home/llm.py, tests/test_core.py]
verified_at: a5cc7a4943aa
---

# Determinism by seed

!!! abstract "In this page"
    - The same seed gives the same run, call by call. A draw is a SHA-256 hash of the seed, a key and a counter, so it depends on names, not on the order of other calls. You can verify one draw by hand.
    - Two planners that make different calls still meet the same bad luck on the same call. These are [common random numbers](../reference/glossary.md#common-random-numbers), and they are what makes a paired test possible.
    - Time is simulated and has no wall clock. The one thing that breaks all this is an LLM, and the benchmark has a way to replay it from a cache.

## The question: can I trust that a rerun gives the same numbers?

A simulator with random faults is only a benchmark if a rerun gives the same faults. There are two traps. The first is a random number generator that other code also uses: one extra call by planner B shifts every later draw, and A and B no longer face the same luck. The second is anything that depends on the machine: the wall clock, Python's salted `hash()`, the order of a dictionary. This engine avoids both with one idea: a draw is a function of names.

## One draw, by hand

The core generator [`Rng`](../reference/glossary.md#rng) is 15 lines:

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
```

[symbolic_robot/rng.py:15-24](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/rng.py#L15-L24)

A draw is made in three steps. Join the seed, the key and a counter `n` with `|`. Hash the text with SHA-256 and keep the first 8 bytes (64 bits). Divide that integer by 2 to the power 64, which gives a number in [0, 1). The counter `n` counts how many times this key was asked, starting at 1.

Run offline, with seed 5 and key `"x"`:

```text
Rng(5).uniform("x")            -> 0.10508243923211916    (first use)
same Rng, uniform("x") again   -> 0.3446454403780886     (second use: n = 2)
a fresh Rng(5).uniform("x")    -> 0.10508243923211916    (first use again)
```

Now the same first draw by hand. The text is `5|x|1`: seed 5, key `x`, counter 1. Its SHA-256 is:

```text
sha256("5|x|1") = 1ae6aec7e2c7a9df6c866c8a0a44bce9f50233c56bf2dc9547f25589c03b910a
first 8 bytes   = 1ae6aec7e2c7a9df  = 1938428863156038111
1938428863156038111 / 2**64 = 0.10508243923211916
```

The two ways agree to the last digit. The `Rng` is nothing more than this. `chance(p, *key)` is `uniform(*key) < p`, and `pick(seq, *key)` indexes a list with a draw.

A seed can itself be derived from names. `derive_seed(*parts)` hashes the parts joined with `|` and keeps 64 bits. `derive_seed(1, "a")` is 15374730731433132414, which is the first 8 bytes of the SHA-256 of the text `1|a` (`d55e0424345a817e` in hex).

### Why a counter per key

The counter is per key, not global. Another key does not shift this one. The test says so in a line ([tests/test_core.py:16-23](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/tests/test_core.py#L16-L23)): after `a` draws `x` and `y`, a second generator `b` that draws only `y` gets the same value as a fresh generator would. I ran the mirror case by hand: after two draws of `y`, the first draw of `x` is 0.10508243923211916 again.

Because `n` changes with each use, a retry is a new draw. A retry of the same skill with the same arguments is not a replay of the failure.

## Three schemes, and who uses which

| scheme | draw is keyed by | used by |
|---|---|---|
| core `Rng` | seed, a key such as `("miss", object)`, the n-th use of that key | the factory domain, `tests/toy.py` |
| core [`CallDraws`](../reference/glossary.md#calldraws) | seed, skill, arguments, n-th call with these arguments; a vector of 16 uniforms | no domain at this commit; only `tests/test_core.py:32-42` |
| household [`Streams`](../reference/glossary.md#streams)`.rng_for("outcome", skill, args, nth)` | seed, episode key, skill, arguments, `nth` (from 0); a vector of 14 uniforms | the household domain |

This is current behaviour, not a plan: `CallDraws` is a core helper that no domain uses. A new domain may use it, or copy the household design. See [Results, simulated time and seeded draws](../modules/results-time-draws.md). The household vector is the subject of [Household outcomes](../modules/home-outcomes.md).

### Slots: each rule reads its own number

In the household design a call does not draw one number at a time. Before a call runs, it draws a vector of 14 uniforms keyed by names, and each rule of the failure model reads its own [slot](../reference/glossary.md#slot): `HW` is slot 0, `FAIL` is 2, `SILENT` is 4, `DUR` is 8, and so on (class `U` in `outcomes.py`). The key is the skill name and the canonical text of its arguments, plus the count of earlier calls with them:

```python
        u = uniforms(self.streams.rng_for("outcome", skill, key[1], nth))
```

[symbolic_robot/domains/home/skills.py:345](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/home/skills.py#L345)

Slots mean that a new rule, or a changed rate, does not steal numbers from other rules. Raise `find.p_miss` and the `FAIL` slot of a `pick` stays the same.

## Common random numbers

Two planners meet the same luck when they make the same call. "The same call" means the same skill, the same arguments and the same count. So when planner A and planner B both `find` the mug for the first time in the same episode seed, they both draw the same numbers for it. A and B may differ in what else they do first.

A real check on the household domain, `studio_flat`, profile `real`, seed 9, key `crn`. One run does a `move` to the desk and a `find` of the mug. The other first calls `wait` (5 s) and `say`, then does the same two calls. Run offline:

| | plain | with `wait` and `say` first |
|---|---|---|
| `move(desk@main)` | ok, 7.315 s | ok, 7.315 s |
| `find(mug)` | `absent`, 3.221 s, truth `miss` | `absent`, 3.221 s, truth `miss` |
| clock at the end | 10.536 s | 15.936 s |

The outcomes and the durations of the two calls are identical, including the bad luck of the `find`. Only the clock differs, by the time of the two extra calls: the luck is shared, the time is not. This is the property that [paired tests](paired-tests.md) rely on: the same task and seed give every planner the same faults.

On the factory side the same seed gives the same moves. Profile `stress`, floor `assembly_hall`, three moves in a row:

```text
3 ['ok', 'ok', 'ok'] simulated seconds: 16.13
3 ['ok', 'ok', 'ok'] simulated seconds: 16.13
4 ['ok', 'hw_fault', 'ok'] simulated seconds: 11.0
```

Seed 3 twice gives the same row and the same 16.13 s. Seed 4 gives a hardware fault on the second move. That fault is the simulator's draw, not a bug in the planner or the robot.

## Which seed an episode gets

The benchmark turns a task and a repeat number into an episode seed:

| where | rule |
|---|---|
| campaign runner (`bench/runner.py:79-82`) | `task_number * 100 + repeat`: the same for every arm, different for every task |
| household suite (`bench/suites/home/env.py:212-213`) | the seed is `derive_seed(task_id, seed)` and the episode key is the text `task_id|seed` |

The first rule keeps arms paired and stops one repeat number from giving every task the same fault. The second does the same with a hash: the household vector is keyed by the seed and the key together.

## Time has no clock

[`SimClock`](../reference/glossary.md#simclock) holds a number `t` that moves only when a skill reports a duration. The core clock is 11 lines ([`clock.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/clock.py)). The household clock refuses a negative step with a `ValueError` ([`home/clock.py:11-16`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/home/clock.py#L11-L16)). Nothing waits in real time and nothing reads the wall clock, so a run is as fast as the CPU and is the same on any machine.

## What breaks determinism: an LLM

The simulator is deterministic. A planner that calls an LLM is not: sampling, batching and a server's version can change an answer. The household suite wraps an LLM in a JSONL cache keyed by a SHA-256 of the model, the prompt, the format, the temperature and a seed ([`llm.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/llm.py), top comment). With `run --llm cache-only` a rerun replays the cache, and a prompt that is not in the cache marks the episode `replay_miss`. A shared cache makes parallel runs share the same answers, and `--cache-lock` is the option for that. I did not run any of this: it needs an LLM server and robot_agent. Treat a run with an LLM as a measurement with its own noise, and report its cache or seed.

!!! code "Where in the code"
    - Core `Rng`, `derive_seed`, `canon_args`, `CallDraws`: [`symbolic_robot/rng.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/rng.py)
    - Household seeds and streams: [`home/rng.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/home/rng.py); the slots: [`home/outcomes.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/symbolic_robot/domains/home/outcomes.py)
    - Campaign seed: [`bench/runner.py:79-82`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/runner.py#L79-L82)
    - Tests: [`tests/test_core.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/tests/test_core.py)
    - Module pages: [Results, simulated time and seeded draws](../modules/results-time-draws.md), [Household outcomes](../modules/home-outcomes.md)

## What this means when you use it

- To reproduce a run, you need four things: the seed, the profile (and its hash), the task, and the same call history of the planner. An LLM planner also needs its cache.
- If two runs of one planner differ, check the seed, the key and the profile first. The simulator is not the likely cause.
- A planner that makes more calls does not make the others unlucky. A faulty call is faulty for everyone who makes it.
- A retry is a new draw. Do not expect a retry to repeat a failure, or to be the same as the first attempt.
- Common random numbers cut the noise of a comparison, but they do not remove it: two planners that make different calls still diverge once their calls differ. Use the paired tests of the next chapters.

**Next:** [Packs, manifests and the hub](packs-and-manifests.md)
