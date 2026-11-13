# Reader comparison: LoRA reader against the base Qwen3-VL-8B (understand step only)

Measured 2026-11-13 with `understand-eval` (one LLM call per task, no question, plan or motion), on dev 700..999 (300 tasks, not used for tuning or per-task analysis before this run), EN and KO, text clean and asr (profile real, seed 0): 1200 paired records. Design was written to `results/understand_eval_700_999/NOTE.md` before the run.

* A: `robot_agent:sage_s8n_d1`, `--model qwen3-vl:8b-instruct` (base reader and translator).
* B: `robot_agent:sage_s8n_ft_d1`, `--model hl-understand-p3-s700` (LoRA reader and translator, as in experiment D).
* Metric: exact match of the understood goal set with the gold goals (after grounding). Paired by record; McNemar.

| subset | n | A exact | B exact | only A right | only B right | p |
|---|---|---|---|---|---|---|
| all | 1200 | 0.463 | 0.666 | 16 | 259 | 1e-57 |
| EN | 600 | 0.533 | 0.682 | 13 | 102 | 3e-18 |
| KO | 600 | 0.393 | 0.650 | 3 | 157 | 9e-43 |
| EN clean / asr | 300 / 300 | 0.580 / 0.487 | 0.723 / 0.640 | 5 / 8 | 48 / 54 | <1e-8 |
| KO clean / asr | 300 / 300 | 0.457 / 0.330 | 0.733 / 0.567 | 1 / 2 | 84 / 73 | <1e-18 |
| feasible tasks | 908 | 0.572 | 0.785 | 8 | 202 | 1e-49 |
| clarify tasks | 164 | 0.098 | 0.183 | 3 | 17 | 0.003 |
| conditional requests | 80 | 0.212 | 0.188 | 5 | 3 | 0.73 |

Confident-wrong readings (the reader is sure and wrong): A 289, B 173 of 1200.

## Reading
* The LoRA reader understands requests clearly better than the base model, in both languages and with or without speech-recognition noise. Almost every record the base gets right, the LoRA reader gets right too (16 against 259 the other way).
* It is not good enough: about a third of the requests are still not read exactly (B 0.666), and 14% of the readings are confident and wrong. Clarify tasks (a request that needs a question) are read exactly in only 18%. Conditional requests are not helped (no goal type for them).
* This measures the understand step only; it says nothing about planning, which the LoRA model was not trained for.
* The trained model could overlap the dev text slightly (about 1% of the dev texts appear in the train split); not checked for dev 700..999.
