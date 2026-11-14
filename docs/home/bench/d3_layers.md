# D3: the task sets, and the layers L9..L12 on top of D2

D3 improves the engine (`robot_agent`, `embodiplan`) and the bench around the same model, `hl-understand-p3-s700`. There is no fine-tuning. Dev 0..999 is used up
(0..599 tuning, 600..699 exposed, 700..849 D2 development, 850..999 D2 held-out, measured once), so D3 has two new task sets made by the benchmark's own generator.
The layers of the round are described in the second part; the loop writes their notes and the pilot results here.

## The two sets

| set | tasks | worlds (`seed_state`) | looked at |
|---|---|---|---|
| `d3dev` | 150 | 30000..39999 | case by case: pilots, traces, class analysis |
| `d3fresh` | 150 | 40000..49999 | never per case; one aggregate measure at the very end (`measure_d3.sh ... --fresh-final`) |

Made by `bench/suites/home/gen/d3.py` (module doc has the rules), with the same families, checks and oracle test as the shipped data (`sample.PLAN`, the
oracle solves every task in the ideal profile) and the texts the generator's templates write (no LLM, no text written by a model; `source` is `template`).
The shipped dev texts are LLM paraphrases of templates, so the D3 wording is the templates' own (see Limits).

* Shares: the (structure, kind) shares of the shipped dev split, largest-remainder over 150. Structure: single 67 (44.7 %), sequence 16, with_context 15,
  conjunction 14, correction 12, ordered 10, conditional 8 (5.3 %), shared_object 8. Kind: d3dev feasible 123, clarify 20, refuse 7; d3fresh feasible 123,
  clarify 22, refuse 5 (the refuse identities are few; d3fresh is 2 refuse tasks short and the places went to single clarify). The dev split itself is single
  44.8 %, conditional 5.6 %, feasible 81.7 %, clarify 13.8 %, refuse 4.5 %.
* Worlds and houses: worlds above every shipped task (< 10000) and above both pools (10000.., 20000..); the six train houses (never the two test houses);
  no test-only template.
* Identities (house, goals, order; independent of the world seed): a D3 task repeats no identity of train, dev, `pool_train`, `pool_eval` (each generated
  under `PYTHONHASHSEED` 0, 1 and 2), nor of the other D3 set, nor one of its own set. Texts: the generator's exact and near-duplicate check against train and
  dev (and the template texts) and the other D3 set; `audit_sets.py` of the loop repeats it.
* The test split is never read. Whether a D3 task equals a test task by identity cannot be checked (the same generator and houses can make the same
  identity); the worlds never coincide (test worlds are < 10000), as in the data design A.1.
* The `split` field of a record is `dev` so that `run --tasks FILE` (default `--split dev`) keeps its tasks; the id (`hl-d3dev-NNNNNN`, `hl-d3fresh-NNNNNN`)
  and `meta.pool` name the set.

### Files and how to make them again

`d3dev.jsonl` is committed at `bench/suites/home/data/pools/d3dev.jsonl` (297 KB). `d3fresh.jsonl` is NOT in the repos: it sits in
`/media/keti/workdir/data/homeloop_d3_fresh/` (mode 600) so no agent reads a case by accident; the same command makes it again. The generator is deterministic only for a
fixed `PYTHONHASHSEED` (the shipped families iterate over sets); use 0.

```
PYTHONHASHSEED=h python -m bench.suites.home.gen.pool --name pool_train --out POOLS/hH           # h = 0, 1, 2
PYTHONHASHSEED=h python -m bench.suites.home.gen.pool --name pool_eval  --out POOLS/hH --other POOLS/hH/pool_train.jsonl
PYTHONHASHSEED=0 python -m bench.suites.home.gen.d3 --out bench/suites/home/data/pools --fresh-out SEALED --pools POOLS
```

| file | sha256 |
|---|---|
| d3dev.jsonl | b5163df9edce0a05b12802f97e13e86660cab745b23a749db7c4a8df15452284 |
| d3fresh.jsonl | 966c692083e0cf845ca90ff86735ab10cbd3aab351a9ce5ff1183810b41bff0d |
| pool_train.jsonl h0 / h1 / h2 | 3edfcf70bee1a1bc427763707aee4b3ecd651e257d54ba82e46b37a6fe987ee9 / bd8ae5228351e3f858080a15a59f44c38864874b0aac24453f19fc5932ed9d96 / d5ccf17632da3fb0c0ef0e6ac0f7f86c1bb9e1b98e97b568be580b71c6950353 |
| pool_eval.jsonl h0 / h1 / h2 | eeb115c5f50b800326997edd686b078c3721096df07f6c7af2d5f1c19b273a11 / 8b12a6cce386129e87c6871d96b258f070975ec58299df851bc61eb81c6dbf51 / 09f22a576f94a77c6f1daa8fd948c8250313d69cc1bdb20011c88bb3bea7875f |

### Reference runs (no LLM: `--llm fake`, CPU, one seed)

`python -m bench.suites.home.cli run --tasks bench/suites/home/data/pools/d3dev.jsonl --planner {oracle,naive} --llm fake --profile {ideal,real} --lang {en,ko} --out ...`

| set | planner | ideal | real | false success (ideal / real) |
|---|---|---|---|---|
| d3dev | oracle | 1.000 | 0.860 | 0 / 0 |
| d3dev | naive | 0.960 | 0.467 | 0 / 0.013 |
| d3fresh | oracle | 1.000 | 0.853 | 0 / 0 |
| d3fresh | naive | 0.973 | 0.440 | 0 / 0.020 |

(EN and KO are the same: the fake LLM and these planners read the gold goals.) For comparison, on dev 600..699 (experiment D) the oracle was 100 / 88 and naive 95 / 55.

### Limits

* The wording is the generator's templates. The reader was trained on train texts that are templates and paraphrases; about 88-91 % of the English word 4-grams
  of D3 texts occur in train / dev texts (template phrases), so the reader is probably less challenged than on paraphrased dev texts. Compare arms within D3, not with the D2 numbers.
* 150 tasks per set: a difference of fewer than about 12 tasks (8 points) in a cell is inside the noise of one run (paired McNemar says it exactly).
* The generator's own `validate` passes on the sets except its dataset-level share check (refuse 4.0 %, navigate 4.0 % are under 5 % in a 150-task set).

## Layers (D3)

Written by the loop, one section per layer (what, why, data, tests, limits), then the pilot results.

## L10 recipient_keep: the recipient of a hand-over is lost after grounding

**What.** The engine rule `goal_fix.shared_listener` (robot_agent `core/planning/goal_fix.py`, called from `assist_loop.py` after grounding) moved the recipient of a delivery
to the speaker whenever that person is also the listener of a message and the words name them once. The reader had the recipient right ("bring him the phone", "bring the mug over to X and tell him",
"bring my husband the keys, and let him know": the pronoun is not a mention), the rule handed the object to the speaker, the hand-over "succeeded" and the check said done (a false success). In the D2
analysis the rule fired in 5 of 150 Korean ideal episodes and all 5 failed; 6 independent tasks in 4 cells carry the class (EN and KO real).

**Fix.** Option `recipient_keep` (default off, `robot_agent/options/recipient_keep.py`): the engine asks the service `shared_listener` first. The recipient moves to the speaker only when the words hold a
speaker-recipient word of the language packs (`lexicon.RECIPIENT`, the robot's `recipient_words`) that is itself a first-person word (`lexicon.FIRST_PERSON`), and the person is named once. A delivery verb or
"here" alone is not evidence (the shipped English list holds "bring", "give", "here"; they say nothing about who gets the object). A second mention keeps the named person; no evidence keeps the reader's
recipient. Evidence with two mentions is the one case where the two readings disagree: one question with the existing "I can read that two ways" phrase, only when no answer was given yet
(key `ask_when_unsure`). Without first-person data in the packs the recipient always stays.

**D1.** `HOMELOOP_D1_LAYERS`: `d2` (the ten D2 layers; hash `64b278b5...` as in D2), `all` (default) = d2 + `recipient_keep`; the layer has no pack data of its own. Test: `tests/home/bench/test_d3_layers.py`.
**Tests.** robot_agent `tests/test_option_recipient_keep.py` (made-up people, made-up language `zq`, `*_off`, `*_empty`, a `give` run through the loop).
**Limits.** The Korean cases whose recipient the speech recognizer garbled ("husband" heard as another word) are not recovered here: the reader drops the recipient itself (class `asr_loss`, layer L11);
a case where the reader gives no recipient at all is not repaired (no guess). A word like "my" before the person's name is not read as evidence.

**Same round, two D2-layer bugs.** (1) `hw_wait` ignored its declared `tries`: after one wait round an unhealthy robot stopped the run (`assist_loop._apply_policy`). New service `hw_wait.more_tries`: while the declared tries
are left the step runs again; the schedule values are untouched. Test in `tests/test_option_hw_wait.py`. (2) The accounting of `retry.py` (the `injected` flag of the last attempt only) is NOT fixed here:
`bench/suites/home/retry.py` is in the checker's protected list and outside the brief's edit list; the coordinator decides (see the round report).
