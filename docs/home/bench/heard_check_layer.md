# Layer heard_check (selectable, not in `all`): a goal whose own quote is not in the heard words is asked about

**What.** It turns on robot_agent's option `heard_check` (robot_agent docs/heard_check.md) with the overlay `HEARD_MATCH` of `d1_options.py`
(`min_prefix 2`, `min_ratio 0.5`, assumed: robot_agent's starting values, not tuned here). A goal whose `said` (or a say goal's message) no heard
word matches gets an `object` issue on the read-back; the engine re-samples, asks its repeat question and reads back. Turn it on with
`HOMELOOP_D1_LAYERS=<all list>,heard_check`. The hashes of all, d3 and d2 are unchanged (tests/home/bench/test_heard_check_layer.py).

**Why (class B of the D5 false-success analysis).** The reader filled an ASR gap with content the person never said: `책` for a garbled `호일`
(039) or `안경` (133), a garbled "go and charge" read as a new say goal that replaced the dock goal (080, 130), a correction read as a new task with `책`
(108, ko_ideal), `저녁` for a garbled `점심` (129). All six are Korean; English readings carry no `said`.

**Acceptance (pre-registered by the caller before the run, 2026-11-17).** Cache-only CPU replay of d5dev, arm all vs all + heard_check, 4 cells,
one snapshot (robot_agent 3d50514, symbolic_robot 0e5c94c, embodiplan 4bfa87a), on a COPY of results/home_D5/shared_cache_D5. Arm all replayed
600/600 identical to DEV_all (cache counters aside). With the layer, the EN cells and ko_ideal: 0 fires, 450/450 identical. ko_real: 9 fires. Two
changed only their lab events (058, 128: a re-sample reading had an unheard quote; same calls, same give_up). Seven needed calls the cache did not
hold; they were run live on local Ollama (2 workers, 42 live calls; a 7-task subset of arm all replays identical to the full run, so the subset is valid).

| task (ko_real) | before | after | how |
|---|---|---|---|
| 039 `책` | done, false success | success | repeat asked, the person said it again (`호일`); one "no" to a read-back, said again, confirmed |
| 080 say `이제 준비됐어요.` | done, false success | success | repeat asked; the restatement gave the dock goal back |
| 130 say `주방으로 와 주세요.` | done, false success | success | same |
| 133 `책` | done, false success | success | repeat asked; `안경` read |
| 031 `우유` (clarify task) | success | success | the request names no drink (the reader guessed); asked, then the clarify dialogue |
| 032 `파란 책` | success | success | one read-back fewer |
| 141 `칼` | budget | budget | one question merged with the repeat |

Totals over 600: success 423 -> 427 (ko_real 78 -> 82), false success 38 -> 34 (ko_real 14 -> 10). Successes lost: 0. Not flagged: 129 (the
reader's `저녁` shares half its letters with the heard `저심`: accepted as an ASR correction) and 108 (a request said during the run has no
read-back stage in the engine). d5dev was used for development (optimistic); the seven live episodes are one sample of the model each.

**Limits.** A 2-character quote token is found when one character matches in place (lenient). A quote in another script is not checked.
