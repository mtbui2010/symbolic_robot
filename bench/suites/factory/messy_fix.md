# Messy-fix suite (factory): a repair check of three new `ask_source` keys on the tasks that failed before

A **repair check on tasks selected because they failed in the messy suite**, not a new unbiased test (descriptive statistics only: a few tasks per group). Everything is simulation. Adapted to the factory domain from the report of the original re-run.

## Question
Do three default-off keys of the engine's `ask_source` option help on answers the messy suite showed it could not use?
* `use_room` (run option `ask_source_room`): an answer that names only a room is used; the search looks at that room's places first.
* `clarify_unusable` (`ask_source_clarify`): an answer that names no place or room, and is not an "I don't know", gets one question: "Which room, or which piece of furniture, is it in?".
* `confirm_near` (`ask_source_near`): an answer that nearly names one place is confirmed: "Did you mean the X?".

## Arms (run options sent with every run; same tasks and simulator seeds across arms)
A = the messy suite's arm A; D = the messy suite's arm D (ask_source + reask + route weight 0.3 + relook + confirm_look); E = D plus the three new keys. E vs A mixes D's options with the new keys, so E vs D (the effect of the new keys alone) is reported next to it. The three keys are sent as 0 in arms A to D (a server may set them on in its environment).

## Tasks
The 25 tasks of the messy suite (task seed 7, 6 per policy) that failed first or serve as controls, by id: room_only t02 t09 t16 t23 t30 t37; vague t03 t10 t17 t24 t31 t38; "..." t13 t27 t41; empty string t06 t20 t34; partial name t40; regression controls `knows` t00 t07 t14 and `wrong` t01 t08 t15. `failed_18` = the 18 first-answer-unusable tasks. 2 repeats, 150 episodes. The scripted person answers the clarifying question with its next scripted answer.

## Analysis
`bench/suites/factory/analyze_fix.py`: per group, per arm: success, wrong-done, distance, questions, unusable and clarified answers, clarifying questions asked, room lines said, first move in the true place's zone; paired counts per task (combined criterion of the protocol suite, E vs A, D vs A, E vs D). No pre-registered win rule; numbers are descriptive. Run it with the 25 task ids: `--only` (the default of this suite).
