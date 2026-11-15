# Flexibility tests: a structure that helps known tasks must not hurt new ones

Why: TAMP-lite, declared task methods (HTN) and execution templates (BT) add structure. Structure can raise the score on known cases and lower it on new ones, and the
score on a dev set would not show it. A structure is kept only if it passes these tests (written 2026-11-16, before TAMP-lite is measured).

| Test | How | Accept when |
|---|---|---|
| 1 Empty data | Switch the structure on with all its data removed (no reach, no methods, no templates). Cache-only replay of d3dev. | Byte-identical to the arm without it (the `_empty` tests already cover each option; this is the same at episode level). |
| 2 Second robot | A made-up robot pack: other reach, other skill names, no shift skill, no sensor. Loop-level tests on CPU, no GPU. | The option adapts through data alone or stays inert; no edit of the engine to add the robot. |
| 3 Novel structures | The per-structure table of the paired report (single, sequence, conjunction, correction, conditional, ordered, shared_object, with_context) for every cell. For methods: tasks that no method covers, and tasks that look like a method but differ in one part. | No structure and cell is worse than the arm without the structure beyond noise (paired counts, a loss is named and explained). |
| 4 Other language | KO cells and a made-up language in unit tests. | Same as test 3 for KO; the made-up language is not broken. |
| 5 LLM stays the default | Where the structure does not match, the run takes the old path. Check by an event: 'structure matched / not matched' per step. | Unmatched steps run exactly as before (no extra call, same plan). |
| 6 Physical variety (MuJoCo, TAMP-lite) | Objects at depths 0.45 to 1.10 m on three surfaces, with and without reach_check; a robot variant that declares a shorter reach. | Success not lower with the option; the shorter reach changes behaviour through data only. |

Rules: a loss in test 3 or 4 is reported even when the total rises; a structure that fails any test is not kept (it is deleted, as in the D4 stay gate); the tests
are run before the structure is added to `all`.
