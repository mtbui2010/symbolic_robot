# Layer cond_schema (selectable, not in `all`): the kind of a condition, an always list, a question for a condition no look settles, heard words

**What.** It turns on robot_agent's option `cond_extract` key `kinds` (robot_agent docs/options.md, `cond_extract`, "Keys of layer cond_schema") and gives
it the data of key `heard_match`. Its extraction then uses the schema `SCHEMA_KINDS`: the old keys plus `kind` (`presence` | `state` | `unobservable`),
`always` (goals to do in every case: no condition on them) and `question`. A `presence` condition is looked at as before. A `state` or `unobservable` one
with a question becomes ONE yes / no question that `cond_goal` asks and reads with its key `answer` (layer `cond_answer`: a yes, a no, a negation; anything
else is UNKNOWN and the run ends failed saying the question). `heard_match` checks the condition's object and place words against the heard words (the
request, its English reading, the person's answers): no object word heard is UNKNOWN (the run ends failed, nothing invented is looked for or done), no
place word heard asks `q_unclear`. Overlay (all `assumed`): `COND_PROMPT_KINDS` (replaces `COND_PROMPT`), `HEARD_MATCH` (the numbers of `heard_check`,
not tuned) and the `cond_extract` Korean clause list plus `KO_COND_COME` (the verb stem 오- "come" and its compounds + "myeon", which `KO_COND_MORE`
leaves out with the plain vowel stems). It needs the `cond_extract` and `cond_answer` layers; without `cond_answer` the question is not asked (the
goals run as read); without `cond_extract` it does nothing. Turn it on with `HOMELOOP_D1_LAYERS=<base list>,cond_answer,cond_schema`. The hashes of
all, d3 and d2 are unchanged (tests/home/bench/test_cond_schema_layer.py).

**Why (classes A and I of the cond20 dev analysis, 2026-11-18).** The extraction put goals that hold in every case into the else branch; it took an
object from a misheard word (the robot then acted on it and said success); it turned a condition no look can settle into an object to look for at an
invented place; and a Korean clause ending in "-오면" never started the extraction. No regex moves goals between lists: the model says the lists.

**Not measured.** No live run was made with the layer (the coordinator runs the live measure). cond20 is a development set of 20 tasks (too small
for a rate). Unknown: whether the reader model fills `kind`, `always` and `question` as the prompt asks; whether the simulated person answers a
free yes / no question the robot writes; how often the heard check fails a run whose object was only said in other words.

**Limits and risks.** A state the robot could see (a door it holds open in its belief) is asked, not looked at. A question the model writes with the
wrong polarity (yes = the condition does not hold) keeps the wrong branch: a false success is possible. An object said in other words than the
model's (no word in common, same script) ends the run failed. An object word in another script than every heard word is not checked (fail open).

**Round 1 (d5dev, 2026-11-18).** Measured on top of `cond_answer`: 3 losses, 0 wins, false successes 18 -> 19. One defect of this layer: `COND_PROMPT_KINDS` said one polarity sentence for every kind ("... if the object IS at that place or the answer is yes ..."), and the question wording bled into presence conditions: on Korean "X가 있으면 ..., 없으면 ..." requests the model wrote `present` false in 7 of 16 paired extractions (0 of 16 in English; the old `COND_PROMPT` said true in all 16), so the if branch was dropped (ko_ideal 000093, 000058; the lucky passes 086 and 117 came from the same flip). Fixed in the data only: the prompt now says `COND_PRESENT`, the base prompt's own `present` sentence cut from `COND_PROMPT` (word for word, same field meaning), and a question kind has its own sentence (its question is phrased so that yes means the condition holds; its `present` is true). `COND_PROMPT` is unchanged (test_cond_schema_polarity.py pins it). robot_agent's `cond_extract` lab entry now carries `present` (and `kind`), so a flip shows in the events. Not re-measured: the coordinator compares `present` of the old and new prompt on the dev conditional requests (both languages) before a live run.
