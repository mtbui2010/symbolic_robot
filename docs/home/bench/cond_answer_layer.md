# Layer cond_answer (selectable, not in `all`): the condition's answer read by itself, a closed place opened before the look

**What.** It turns on three keys of robot_agent's option `cond_goal` (robot_agent docs/options.md, `cond_goal`, "Keys of layer cond_answer"):
`answer` (the answer to "Is the X at the P?" is read by itself: a yes, a no, a negation, or the place it names; "I don't know", silence or nothing
usable is UNKNOWN and the run ends failed saying the question, never a default), `open_closed` (a place the ENV declares openable that the belief
holds closed is opened with the mock robot's `Open` before the look) and `confirm_none` (every goal dropped on a look that could not see inside: the
question once more). Overlay: `ANSWER_NEGATION` of `d1_options.py` (English `n't` forms, Korean 없 / 않 / 아니 / 안 / 못; assumed, general grammar) and
the `open` role. It needs the `cond_extract` layer (that turns `cond_goal` on); alone it is on and inert. Turn it on with
`HOMELOOP_D1_LAYERS=<all list>,cond_answer`. The hashes of all, d3 and d2 are unchanged (tests/home/bench/test_cond_answer_layer.py).

**Why (class B of the cond20 dev analysis, 2026-11-18).** The robot went to the condition's place, looked into a CLOSED container (a fridge: the look
cannot see inside), missed twice, asked "Is the milk carton at the kitchen fridge?", got an answer with no yes / no word (per the analysis, the simulated person answers it with a location; the answer text was not logged), and
robot_agent's `yes_no` read it as no (`interact/dialog.py`: anything without a yes / no word is False). In 009 (en_real, en_ideal, ko_ideal) every
goal was dropped and the run said "Task completed"; in 010 (en_ideal) the blind miss kept the wrong branch. All four are false successes. The fix
reads the answer in `cond_goal` itself (dialog.py is unchanged) and opens the container first.

**Not measured.** No live run was made with the layer (the coordinator runs the live measure). cond20 is a development set of 20 tasks (too small for
a rate). Unknown: how the simulated person answers a second "Is the X at P?" and whether it says a place for every condition question.

**Limits and risks.** A container the layer opens stays open (no Close; the retired `close_opened` lost three tasks). A partial open (the look misses
after an Open that reported success) counts as an observed miss. An answer that names the condition's place with a negation the data does not list
("it's never been in there" is listed, "it left the fridge" is not) is read as present. "No, it's in the fridge" (no and the place disagree) is UNKNOWN.

**Round 1 (d5dev, 2026-11-18; robot_agent cf72893).** Measured with `cond_schema` on top (base list + `cond_answer,cond_schema`): 3 losses, 0 wins, false successes 18 -> 19. One defect of this layer: the place `open_closed` opened went through robot_agent's `run_step` (the end-of-run check's path), which applies the belief change but does not mark the place opened just now as the engine's own Open does; the run's stale-open doubt then cleared the fresh open on a later miss of another object there, and the search (a `bt_goal` tree) had no way left and asked the menu (ko_real 000093). Fixed in robot_agent (engine service `opened_now`, used by `open_closed`); a belief open before the run is still doubted. Not re-measured live.
