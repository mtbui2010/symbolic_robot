---
sources: [bench/suites/home/planners/saycan_like.py, bench/suites/home/planners/inner_monologue_like.py, bench/suites/home/planners/progprompt_like.py, bench/suites/home/planners/knowno_like.py, bench/suites/home/planners/keyword.py, bench/suites/home/planners/prompts.py, bench/suites/home/llm.py, bench/suites/home/shared_cache.py]
verified_at: a5cc7a4943aa
---

# LLM baselines and clients

!!! abstract "In this page"
    An overview of the four LLM baselines of the household benchmark and of the clients that talk to a
    model. You get what each baseline is modelled on, the three forms of `--llm`, what the cache does and why
    it exists, and the rule that the fake LLM never produces a reported number. This is an overview page.
    A later part of this site goes deeper into the planners themselves (their prompts, loops and parsers).
    No LLM call was made for this page.

## At a glance

| | |
|---|---|
| **Input** | an `EpisodeEnv` and an LLM client (`env.llm()`) |
| **Output** | skill calls and a final status, like every planner |
| **Used by** | `run_episode`, through the [planner registry](planner-interface.md) |
| **Uses** | `llm.py` (clients), `prompts.py` (shared prompt text), `keyword.py` (the fake brain) |
| **Source** | [`planners/`](https://github.com/mtbui2010/symbolic_robot/tree/a5cc7a4943aa/bench/suites/home/planners), [`llm.py`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/llm.py) |
| **Tests** | `tests/home/bench/test_planners_llm_fake.py` (not run for this page) |

## The four baselines

These are planners in the style of four published robot-planning methods. They are not re-implementations
of the papers: each file says where it deviates (a chat API gives no token probabilities, so two of them use
samples or an index choice instead). They are not privileged: they see the observation, not the truth.

| Name | Modelled on | One-line idea | Where the LLM is used |
|---|---|---|---|
| `saycan_like` | SayCan (Ahn et al. 2022) | the planner lists the calls that are possible in its own belief; the LLM picks one by index | every step |
| `inner_monologue_like` | Inner Monologue (Huang et al. 2022) | a step loop; the LLM sees the history with the result text of every call and the scene descriptions, and picks the next call, a question, or the end | every step |
| `progprompt_like` | ProgPrompt (Singh et al. 2022) | one LLM call writes a short program with `assert ... else` recovery lines; a small interpreter (no `exec`) runs it | once, plus repairs |
| `knowno_like` | KnowNo (Ren et al. 2023) | the LLM lists up to 4 interpretations of the request; a conformal set over 5 samples decides: one interpretation, act; more, ask the user | before acting, then as inner monologue |

All four need an LLM (`needs_llm` is true). They share one prompt layer, `prompts.py`: the same list of
15 tools and the same rendering of the observation, so they differ in loop and answer format, not in what
they are told about the house. Every prompt starts with a `MODE:` line.

Each LLM answer that must be JSON goes through `ask_json` in `base.py`: parse, check, and on a bad answer up to
two repair prompts. Every attempt counts as one LLM call against the episode budget of 30 calls (a
`CountingLLM` raises `BudgetExceeded` before the call that would exceed it).

## The clients

`llm.py` holds a small stack of clients that all answer `chat(prompt, format, temperature, seed)`.

| Class | What it is |
|---|---|
| `OllamaHTTP` | one POST to an Ollama server's `/api/chat` through `urllib` (no third-party HTTP library). Transient failures are retried with back-off |
| `FakeLLM` | deterministic and rule-based, a stand-in for tests and CI (see below) |
| `NoServer` | the inner client of `cache-only`: it answers nothing, so a miss raises `CacheMiss` at once |
| `CachedLLM` | wraps any client with a JSONL cache keyed by `sha256(model, prompt, format, temperature, seed)` |
| `CountingLLM` | counts calls and enforces the per-episode budget |

Wall-clock latencies go to stderr only, never into results.

### The three forms of `--llm`

!!! code "Where in the code"
    [`llm.py#L356-L369`](https://github.com/mtbui2010/symbolic_robot/blob/a5cc7a4943aa/bench/suites/home/llm.py#L356-L369).
    The permalink resolves after the owner pushes the commit.

```python
def make_llm(spec: Optional[str], model: Optional[str] = None, cache_dir: Optional[str] = None):
    """``"fake"`` -> FakeLLM; ``"http://..."`` -> OllamaHTTP (cached under ``cache_dir`` when given);
    None -> None."""
    if spec is None or spec == "":
        return None
    if spec == "fake":
        return FakeLLM()
    if spec == CACHE_ONLY or spec.startswith(("http://", "https://")):
        llm = NoServer(model or DEFAULT_MODEL) if spec == CACHE_ONLY else OllamaHTTP(spec, model or DEFAULT_MODEL)
        if cache_dir:
            safe = (model or DEFAULT_MODEL).replace("/", "_").replace(":", "_")
            llm = CachedLLM(llm, Path(cache_dir) / f"{safe}.jsonl", shared=shared_cache_path(model or DEFAULT_MODEL))
        return llm
    raise ValueError(f"--llm must be a URL (http://host:port) or 'fake' or 'cache-only', got {spec!r}")
```

| `--llm` value | Client | When to use it |
|---|---|---|
| `http://host:port` | `OllamaHTTP`, wrapped in a `CachedLLM` that writes `OUT/llm_cache/<model>.jsonl` | a live run |
| `cache-only` | `NoServer` inside a `CachedLLM`: replays from the cache; a prompt with no cached answer marks the episode `replay_miss` | repeat a live run without a server |
| `fake` | `FakeLLM`, no cache | tests, CI and smoke checks of the loops |

I ran `make_llm` offline for each form. Output:

```text
FakeLLM NoServer None
OllamaHTTP
ValueError: --llm must be a URL (http://host:port) or 'fake' or 'cache-only', got 'somewhere'
fake url None
64 True False
```

The first line is `make_llm("fake")`, `make_llm("cache-only")` and `make_llm(None)` (the bare `NoServer` is what
you get when no cache directory is given; the run adds the cache). The second is a URL, which only builds the
client and makes no request. The last two lines are `llm_kind` (what `summary.json` records instead of the
URL) and `cache_key`: a 64-character hash that is the same for the same arguments and changes when the seed changes.

!!! warning "The fake LLM is not a planner"
    `FakeLLM` reads only the prompt text and the catalog's common sense and answers in the format of the
    planner's mode (a tool call, an index, a program, a list of interpretations). It exists so the loops, the
    parsers and the runner can be tested without a model. Its numbers are never reported as a planner's
    result. The tests that use it check plumbing, not quality.

## The cache and paired runs

A live LLM is not deterministic across runs, so the benchmark caches answers by prompt hash. Two uses:

- **Replay.** With `cache-only`, a finished live run can be repeated without a server and gives the same
  episodes, because every prompt that the run asked is in its own cache.
- **Paired runs (common random numbers).** `--shared-cache DIR` makes a second cache that several
  configurations of one replicate read and write. A prompt that one configuration already asked gets the same
  answer in the others, so a difference between two configurations comes from a prompt the variant itself changed.
  Configurations that run at the same time on a cold shared cache could both miss the same prompt and keep
  different answers. The safe default is to run them one after another (the baseline first); the runner
  refuses to start next to another live run on the same directory. `--cache-lock` turns on a per-key
  file lock instead (the first answer wins).

The episode record also carries how many prompts came from the run's own cache, the shared file and the server;
an episode that asked something new is marked `touched`. How a paired comparison uses this is part of
[Paired tests](../learn/paired-tests.md) and [Determinism](../learn/determinism.md).

## Edge cases and failure modes

| Symptom | Cause | Result |
|---|---|---|
| run refused: planner needs `--llm URL` or `--llm fake` | an LLM planner with no `--llm` | `PlannerConfigError` before any episode |
| the LLM server fails or times out | `LLMError` | the run aborts with `InfraError` and writes no summary |
| a prompt not in the cache, with `cache-only` | `CacheMiss` | the episode is marked `replay_miss` |
| the answer is not valid JSON or fails the check | model output | up to 2 repair prompts, then the planner gives up |
| LLM budget (30 calls) used up | `CountingLLM` | `BudgetExceeded`; the episode ends with status `budget` |

## What this page leaves out

Part 2 of this site reads each baseline in detail: its prompt, its loop, how it parses and repairs answers, and
the conformal calibration behind `knowno_like`. Not run for this page: any real LLM call, `cache-only` replay,
and the LLM-planner tests.
