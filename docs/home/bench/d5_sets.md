# D5 sets: d5dev and d5fresh

Two task sets made by `bench/suites/home/gen/d3.py` used as a library (a new world base and size per set, the generator is not edited). Generator commit: 9ad880a. Both use train houses only, no test-only template, texts from the template generator (no LLM).

| set | tasks | worlds (seed_state) | gen seed | sha256 |
|---|---|---|---|---|
| d5dev | 150 | 70000..79999 | 2031 | 826f166fbe8b38910dfa203d32e7b04e7d8602ff8847f3e756b44ad6df6a37fe |
| d5fresh | 300 | 60000..69999 | 2032 | 6e13fcfc78992c941b7b1dd533289cd73441c999771c4da8dce9b54420e50303 |

- d5dev (`data/pools/d5dev.jsonl`): structure conditional 8, conjunction 14, correction 12, ordered 10, sequence 16, shared_object 8, single 67, with_context 15; kind feasible 123, clarify 20, refuse 7.
- d5fresh: a sealed set outside the repositories (directory mode 700, file mode 600). Structure conditional 37, conjunction 62, correction 24, ordered 20, sequence 31, shared_object 16, single 80, with_context 30; kind feasible 257, clarify 43, refuse 0 (generator shortage: single|feasible 43, single|refuse 13).
- Identities avoided: train, dev, pool_train, pool_eval, d3dev and the other D5 set; no exact or near-duplicate text against train, dev, d3dev and the other D5 set. d3fresh and d4fresh were not read: their world bands (40000..49999, 50000..59999) are disjoint from these.
- Use: d5dev may be read freely, task by task. d5fresh is measured once, at the end of a future round, and is never opened; only aggregates are printed.
- CPU reference (--llm fake, EN; KO equal within 0.01): oracle ideal 1.00 / 1.00 (dev / fresh), oracle real 0.85 / 0.87, naive ideal 0.95 / 0.98, naive real 0.40 / 0.45; false success 0 except naive real 0.033.
