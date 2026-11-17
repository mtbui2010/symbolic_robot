# Layer metal_microwave (selectable, not in `all`): a metal thing put into the microwave is refused

**What.** No loop option: it adds the manifest list `safety.hazards` = `METAL_MICROWAVE` of `d1_options.py` to the overlay. robot_agent's option
`hazard` (on in every arm, rules key `core`) reads that list after the frozen pack's own profile (robot_agent docs/metal_microwave.md). Two
entries, the same place (`^microwave(@|$)`, the mock robot's ENV key head, assumed) and the same `say`:
1. sourced: metal, metallic, foil, aluminum / aluminium (NIH ORS, UC Berkeley EH&S, Hoover UK; quotes in `METAL_SOURCE`);
2. assumed: steel, stainless, iron, tin, tinfoil and Korean words (금속, 알루미늄, 호일, 포일, 은박, 스테인리스, 양철, 무쇠).
A word counts whole and when not denied (non-, no, without, -free). No material exemption; no utensil or container noun. The data was written
from the pages only, before any replay, and is not changed after it. Turn it on with `HOMELOOP_D1_LAYERS=<all list>,metal_microwave`. The
hashes of all, d3 and d2 are unchanged (tests/home/bench/test_metal_microwave_layer.py).

**Why.** An earlier analysis of d5dev found five requests whose reading puts a metal thing into the microwave, carried out by the robot.
The words of those requests were not read for this data: the rule and its words come from the cited pages (the generator's hazard tags were
not used either). A bare fork, spoon or can carries no material word, so this rule may not refuse it (a known gap, robot_agent docs/metal_microwave.md).

**Acceptance (pre-registered 2026-11-17, before the replay).** Cache-only CPU replay of d5dev, arm all + metal_microwave against arm all, 4 cells,
one snapshot. Every changed episode listed with its reason; the five microwave tasks (000001, 015, 029, 042, 055) per cell; the seven refuse tasks
refused before / after; successes and false successes per cell. Hard: no success lost; false successes do not rise; every episode whose goal
puts a thing into the microwave with a declared metal word in its object phrase is refused (the ones that are not, with the reader's goal).

**Results.** Not measured yet.
