"""What the D1 planners (``sage_s8n_d1``, ``sage_s8n_ft_d1``) turn on in robot_agent, and the pack data those options read.

Kept apart from ``robot_agent_adapter.py`` (at its size limit). Every option here is OFF by default in robot_agent (a registered option,
``python -m robot_agent.core.options list``) and is switched on only for D1 through ``loop_options``; the data an option needs is declared as a
manifest overlay (the frozen mock-robot pack declares none), recorded in the run config as ``manifest_overlay`` with ``assumed: true``.

Failure classes (found on the D1 dev pilot, fixed as classes, never as tasks):

* ``search_per_object``: the search budget (``search_total``) was one count for the whole run, so the places a first object used up were
  charged to the second one.
* ``place_find``: a Find of a place the robot moves to (``MoveTo m, Find m, Open m``) is always absent and counted as a miss.
* ``reopen_on_miss``: a Find that misses right after an Open (a door opened only part way) closes and opens the container once, then looks
  again. The remedy ``[Close, Open]`` OVERLAPS the simulator (its partial-open state is cleared by a Close): read it as an ablation.
* ``end_state``: a ``go`` goal for the dock is made true (go there, Dock) before done, wherever the reader put it in the goal list. Like the
  remedy above it matches the simulator's ``docked()`` condition: read it as an ablation.
* ``object_words``: the goal's 'phone' and the plan's 'Pick cell phone' are one object for the goal checks.

Round D2 (one layer per failure class, each a robot_agent option, default off): ``LAYERS`` below. The environment variable ``SYMBOLIC_D1_LAYERS`` (formerly
``HOMELOOP_D1_LAYERS``, still accepted: ``layers_value``) picks which layers D1 turns on: ``all`` (default; the ``d3`` layers + the four D4 layers), ``d3`` (the 18 layers of the D3 arm), ``d2`` (the ten D2 layers only), ``none`` (D1 exactly as in experiment D: the baseline arm) or a comma list of layer names (the ``SELECTABLE`` layers only so). It is read when
this module is imported (the planner classes are built then); the layers on are recorded in the run config (``loop_options``) and in the overlay note.
"""

from __future__ import annotations

import copy
import functools
import os
import sys

# search legs, at most 6 places per search, no search second look (robot_agent: planner.search_legs / search_total / detector_miss_rate)
D1_SEARCH = {"search_legs": 1, "search_total": 6, "detector_miss_rate": 0}
# false-success class: the goal check believed one sighting that followed a miss (the camera sees what is not there). With robot_agent's
# option ``confirm_look`` (default off) a third look decides: believed only when the object is seen again (two sightings in a row).
D1_CONFIRM = {"confirm_look": "1"}
# the failure-class options of the 2026-11-13 round (all default off in robot_agent)
D1_CLASSES_D = {"search_per_object": "1", "place_find": "1", "reopen_on_miss": "1", "end_state": "1", "object_words": "1"}

LAYERS_ENV = "SYMBOLIC_D1_LAYERS"
# D2 layers: name -> (loop options, pack data), in the order they were added. The data is the mock robot pack's own, with its source.
# Korean clause words, ASSUMED (general grammar, not measured). A condition is a predicate (stem: be / not be / do / become / open or closed / on or off)
# ending in a conditional (-(eu)myeon, -damyeon), up to three words of its own clause before it (none that ends a clause with a comma: the words before
# a comma are the previous clause's request), not followed by a request form ("... myeon dwae /
# johgesseo": that is the request, not a condition). A noun that only ends in "myeon" is no ending (stems are listed; bare "-ramyeon" is not).
# A negation is "-ji ma / -ji mal-go / -ji anh-" ("do not ...") or "malgo / ppaego / jeoehago" ("not that, except"); "ji mal-" is read only before
# go / a / ra, so a noun ending in "ji" before a word that starts with "mal" (a verb "to dry") stays.
KO_CONDITION = (r"(?:(?:만약|혹시)\s+)?(?:[^\s,;.!?]+\s+){0,3}\S*(?:(?:있|없|하|되|열려|닫혀|켜져|꺼져)(?:으)?면|[가-힣]다면)"
                r"(?![가-힣])(?!\s*(?:돼|되|좋겠|괜찮|충분))(?=\s|[,;.!?]|$)")
KO_NEGATION = (r"(?:[^\s,;.!?]+\s+)?\S*(?:지\s*(?:마(?:세요|시오|라|요)?|말(?:고|아\S*|라)|않\S*)|말고|빼고|제외하고)(?=\s|[,;.!?]|$)")
# The Korean conditional ending the D2 clause above does not read, read only by the D3 layer cond_extract (its own declared clauses, never the lang_words ones:
# the D2 data is unchanged). ASSUMED, general Korean grammar (not measured, no word list of any task text): a word that ends a clause in the conditional
# ending -(eu)myeon after a verb stem: a consonant stem or a past marker + "eu-myeon"; a stem made with a voice / causative suffix (-i, -hi, -ri, -gi), the
# honorific -si, "become" -ji, or a b- / reu-irregular stem (-u, -reu) + "myeon". Not read: the request forms ("... myeon dwae / johgesseo / gomapgesseo /
# gamsahagesseumnida": that is the request, not a condition), a plain vowel stem + "myeon" (its bare form is also a noun: a mask, a screen, noodles), and
# "a-ni-myeon / a-ni-ra-myeon", the ordinary "or / otherwise" of a choice question.
KO_COND_MORE = (r"(?:(?:만약|혹시)\s+)?(?:[^\s,;.!?]+\s+){0,3}\S*[가-힣](?:으|[이히리기시지우르])면"
                r"(?![가-힣])(?!\s*(?:돼|되|좋겠|괜찮|충분|고맙|감사))(?=\s|[,;.!?]|$)")
# the extraction call of cond_extract (prompt language, ASSUMED text): the request, the reader's numbered goals, one JSON of the option's fixed schema
COND_PROMPT = ("A household robot request may hold a condition: something is to be done only if an object is (or is not) at a place, and perhaps something else otherwise.\n"
               "Request: {request}\nThe goals already read from it, numbered:\n{goals}\n"
               "Answer in JSON. conditional: true only when the request really makes a goal depend on whether an object is at a place, else false with empty lists. "
               "object and at: the object and the place the condition looks at, in the words of the request. present: true when the condition holds if the object IS at that "
               "place, false when it holds if the object is NOT there. if_goals: the numbers of the goals to do when the condition holds. else_goals: the numbers of the goals to "
               "do when it does not hold (the 'otherwise' part). drop: the numbers of goals that only restate the condition and are no request. A number is in at most one list; "
               "leave a goal out of all lists when it is to be done in every case. unsure: true when you cannot tell.")

# COND_PROMPT's own `present` sentence, cut from it (not retyped): the kinds prompt below says it for a presence condition word for word, so the field
# means what the base prompt means. (Round 1, d5dev: one clause "... or the answer is yes" shared with the question kinds flipped `present` to false on
# Korean "X-ga iss-eumyeon ..., eops-eumyeon ..." requests, which dropped the if branch.)
COND_PRESENT = COND_PROMPT[COND_PROMPT.index("present: true"):COND_PROMPT.index("if_goals:")]
# the extraction prompt of layer cond_schema (robot_agent cond_extract key kinds, schema SCHEMA_KINDS): COND_PROMPT's keys plus kind, always and question.
# ASSUMED text, general (no task text): the robot's look settles only whether an object is at a place; any other condition is asked as one yes / no question.
# A question kind gets its own polarity sentence (its question is phrased so that yes means the condition holds), apart from COND_PRESENT.
COND_PROMPT_KINDS = ("A household robot request may hold a condition: something is to be done only if the condition holds, and perhaps something else otherwise.\n"
                     "Request: {request}\nThe goals already read from it, numbered:\n{goals}\n"
                     "Answer in JSON. conditional: true only when the request really makes a goal depend on a condition, else false with empty lists. "
                     "kind: presence when the condition is whether an object is (or is not) at a place, which the robot can go and look at; state when it is "
                     "whether something is open, closed, on or off; unobservable when nothing the robot can see settles it. object and at: for presence, the object "
                     "and the place the condition looks at, in the words of the request; else empty. " + COND_PRESENT +
                     "question: for state and unobservable, one short yes / no question to the person, in the language of the request, phrased so that the "
                     "answer yes means the condition holds; else empty. For state and unobservable, present is true: the answer yes is the condition holding. "
                     "if_goals: the numbers of the goals to do when the condition holds. else_goals: the numbers of the goals to do when it does not hold (the "
                     "'otherwise' part). always: the numbers of the goals to do in every case, whatever the condition. drop: the numbers of goals that only restate "
                     "the condition and are no request. A number is in at most one list. unsure: true when you cannot tell.")
# A Korean conditional ending neither clause above reads (cond20 dev analysis: a clause "...들어오면" never started the extraction): the verb stem 오- "come"
# (and its compounds 들어오-, 돌아오-, 나오-) + "myeon". ASSUMED, general grammar; "오면" ends no common noun. The request forms are excluded as above.
KO_COND_COME = r"(?:(?:만약|혹시)\s+)?(?:[^\s,;.!?]+\s+){0,3}\S*오면(?![가-힣])(?!\s*(?:돼|되|좋겠|괜찮|충분|고맙|감사))(?=\s|[,;.!?]|$)"


# precond_repair's label; the replan_block layer extends it with the ``near`` need of the two releases (a second source of the same manifest)
PRECOND_SOURCE = ("mock robot manifest, skills[].pre (hand_empty(), not hand_empty()); achieves: assumed (the manifest "
                  "effects name no goal; a put-down ends an on goal, a hand-over a hand goal)")


# heat_safety: the mock robot's heat place, its clearance and the words of things that can burn (robot_agent docs/heat_safety.md). The rule and its distance
# are the cited page's; the stove is ASSUMED covered (the page lists heat sources "including" fireplaces, wood stoves, radiators, space heaters or candles;
# a cooking stove top is not named); the word list is ASSUMED (general household materials and items, written with the hazard probe's items in view;
# 'duster' was added after the reader wrote 'duster' for a Korean dish cloth in that probe).
HEAT_SOURCE = ("US Fire Administration (FEMA), Heating Fire Safety, https://www.usfa.fema.gov/prevention/home-fires/prevent-fires/heating (page reviewed "
               "2023-05): 'Keep anything that can burn at least 3 feet from all heat sources including fireplaces, wood stoves, radiators, space heaters or candles.'")
HEAT_SAFETY = {"places": {"stove@kitchen": {"clearance_m": 0.91, "source": HEAT_SOURCE, "assumed": True}},
               "burnable": {"words": ["paper", "newspaper", "magazine", "book", "cardboard", "tissue", "napkin", "towel", "cloth", "dishcloth", "rag",
                                      "duster", "fabric", "plastic", "wood", "wooden", "lighter", "match", "matchbox"],
                            "source": HEAT_SOURCE + " (the class 'anything that can burn'; the words are assumed)", "assumed": True}}


# metal_microwave (robot_agent docs/metal_microwave.md): no metal into a microwave oven, as data of option hazard (the manifest list safety.hazards: the frozen
# pack's profile file cannot take a rule). The rule and its English words are the three pages' (opened by the task's author, 2026-11-17); the place is the
# mock robot's ENV key head 'microwave' (ASSUMED); the other materials and the Korean words are ASSUMED. A word counts whole and when not denied (non-, no,
# without, -free); no material exemption (the pages name metal trim, no safe material). Written from the pages only, before any d5dev replay.
METAL_SOURCE = ("NIH ORS, Fire Safety Tips for Using Microwave Ovens (News2Use, 2016-03-01), https://news2use.ors.nih.gov/Pages/Fire-Safety-Tips-for-Using-"
                "Microwave-Ovens.aspx: 'Never use metallic articles and aluminum foil in a microwave oven.'; UC Berkeley EH&S, Microwave Oven Safety Guidelines, "
                "https://ehs.berkeley.edu/node/1128: 'Do not use aluminum foil or any metal containers, metal utensils, metal objects, or objects with metal or "
                "foil trim in the oven.' 'Such items can cause arcing, damaging the oven and creating a fire or burn hazard.'; Hoover UK advice centre, "
                "https://service.hoover.co.uk/advice-centre/sparks-and-blue-flashes-inside-the-microwave-oven/143-ensure-that-no-metal-cooking-trays-or-foil-is-"
                "used-to-contain-the-food: 'When placing food in the microwave ensure the cooking tray is not metallic or has metal trims.'")
METAL_NOT_DENIED = r"(?<!non[-_ ])(?<!\bno[ _])(?<!without[ _])(?<![a-z0-9])"
METAL_END = r"(?![a-z0-9])(?![-_ ]?free(?![a-z0-9]))"
METAL_OVEN = [r"^microwave(?:@|$)"]
METAL_SAY = "metal in a microwave oven can cause sparks and a fire"      # the Berkeley page's reason in short words (wording assumed)
METAL_MICROWAVE = [
    {"objects": [METAL_NOT_DENIED + r"(?:metal(?:s|lic)?|foils?|alumin(?:um|ium))" + METAL_END], "places": METAL_OVEN, "say": METAL_SAY,
     "source": METAL_SOURCE},
    {"objects": [METAL_NOT_DENIED + r"(?:steel|stainless|irons?|tins?|tinfoils?)" + METAL_END, r"(?<!비)금속|알루미늄|호일|포일|은박|스테인리스|양철|무쇠"],
     "places": METAL_OVEN, "say": METAL_SAY, "source": METAL_SOURCE + " (the class; these words are assumed)", "assumed": True},
]


# metal_microwave_ask (robot_agent docs/metal_microwave.md, "Ask"): a BARE utensil word (no material word) put into the microwave makes the robot ASK
# "is it metal?" (robot_agent option hazard, key ask; question: the language-pack phrase q_metal_microwave). The UC Berkeley page names "metal utensils"
# a risk; it does not say that a spoon is metal, so the utensil words, the safe material words and the Korean words are ASSUMED. A material word decides
# without a question: the metal words above run first (steel spoon: refused), METAL_SAFE (plastic spoon) skips it. No can, no container (not in the pages).
METAL_UTENSIL = (r"(?<![a-z0-9])(?:(?:tea|table)?spoons?|forks?|knife|knives|cutlery|utensils?|ladles?|whisks?|tongs|chopsticks?)(?![a-z0-9])",
                 r"(?<![가-힣])(?:숟가락|티스푼|포크|칼|나이프|수저|젓가락|국자|거품기|집게)(?:[은는이가을를도]|(?![가-힣]))")     # a noun alone or + one particle
METAL_SAFE = (r"(?<![a-z0-9])(?:plastics?|wood(?:en)?|silicone|glass|ceramic)(?![a-z0-9])", r"플라스틱|나무|원목|실리콘|유리|도자기|세라믹")
METAL_ASK = [{"ask": "q_metal_microwave", "objects": list(METAL_UTENSIL), "places": METAL_OVEN, "unless": list(METAL_SAFE), "say": METAL_SAY,
              "source": METAL_SOURCE + " (the class 'metal utensils'; the utensil and material words are assumed)", "assumed": True}]


# closed_can_microwave (robot_agent docs/metal_microwave.md, "Closed can"): a CLOSED / SEALED can, jar or bottle put into the microwave is refused
# (option hazard, no question). The class and the words closed / sealed, can / bottle / jar are the three manuals' (quotes below, verified by the task's
# author; the page URLs were not recorded); the phrase shape (up to two words between, the other form "... is still sealed"), the guards and all other
# words (unopened, tin, Korean) are ASSUMED, written from the sources only, no benchmark text read. Not denied: un-, not, non-, no longer, never; not
# an object of "open the"; no open / empty word in between; not followed by "is open / empty", "with no lid"; a modal "can you" is no can.
CAN_SOURCE = ("NDSU Extension, FN1622: names 'metal cans' among the things not to use in a microwave oven; Panasonic HL-MX465S operating manual: "
              "'Do not heat any closed cans or bottles because they might explode.'; GE JE1240L owner's manual: 'sealed containers—for example, "
              "closed jars—will explode'; the exact page URLs are unknown")
CAN_SAY = "a closed can, jar or bottle can explode in a microwave oven"       # the Panasonic / GE reason in short words (wording assumed)
_C_NOT = (r"(?<![a-z0-9])(?<!not[-_ ])(?<!non[-_ ])(?<!longer[-_ ])(?<!never[-_ ])(?<!open[-_ ]the[-_ ])(?<!open[-_ ]a[-_ ])"
          r"(?<!open[-_ ]an[-_ ])(?<!opening[-_ ]the[-_ ])")
_C_GAP = r"[-_ ](?:(?!(?:open(?:ed)?|empt(?:y|ied)|and|or|in|into|from|on|onto|to|with)(?![a-z0-9]))[a-z0-9]+[-_ ]){0,2}?"
_C_END = (r"(?![a-z0-9])(?![-_ ](?:(?:that|which)[-_ ])?(?:(?:is|was|are)[-_ ])?(?:(?:already|now)[-_ ])?(?:open(?:ed)?|empt(?:y|ied))(?![a-z0-9]))"
          r"(?![-_ ](?:with[-_ ]no|without(?:[-_ ](?:a|its|the))?)[-_ ](?:lid|cap)s?(?![a-z0-9]))")
_C_NOUN = r"(?:cans?(?![-_ ](?:you|i|we|they|please)(?![a-z0-9]))|jars?|bottles?)"
_C_KO_SHUT = r"(?<![가-힣])(?:밀봉된|밀봉한|밀봉돼 ?있는|밀봉되어 ?있는|밀폐된|밀폐한|닫힌|닫혀 ?있는|따지 ?않은|안 ?딴|뜯지 ?않은|개봉하지 ?않은|개봉 ?안 ?한|미개봉(?:된|한)?)"
_C_KO_OPEN = r"(?:따서|따고|따 ?줘|열어|열고|개봉해|개봉하고|뜯어|뜯고)"
_C_KO_GAP = (r"(?: (?!(?:빈|열린|딴|개봉한|개봉된|뜯은|뜯긴|안|속|위|옆|뒤|앞)(?: |$))(?!" + _C_KO_OPEN + r")(?!\S*(?:의|에|에서|있는)(?: |$))\S+){0,2}?")
_C_KO = (_C_KO_SHUT + _C_KO_GAP + r" ?[가-힣]*(?:캔|통조림|병|깡통)(?:[은는이가을를도에의와과만](?![가-힣])|(?![가-힣]))(?! ?" + _C_KO_OPEN + ")")
CLOSED_CAN = [
    {"objects": [_C_NOT + r"(?:closed|sealed)" + _C_GAP + _C_NOUN + _C_END], "places": METAL_OVEN, "say": CAN_SAY,
     "source": CAN_SOURCE + " (the class and the words closed / sealed, can / bottle / jar; the phrase shape and its guards are assumed)", "assumed": True},
    {"objects": [_C_NOT + r"(?:closed|sealed|unopened)" + _C_GAP + r"(?:" + _C_NOUN + r"|tins?)" + _C_END,
                 r"(?<![a-z0-9])(?:cans?|jars?|bottles?|tins?)[-_ ](?:(?:that|which)[-_ ])?(?:is|was|are)[-_ ](?:still[-_ ])?(?:closed|sealed|unopened)(?![a-z0-9])",
                 _C_KO],
     "places": METAL_OVEN, "say": CAN_SAY, "source": CAN_SOURCE + " (the class; these words are assumed)", "assumed": True},
]


# closed_can_ask (robot_agent docs/metal_microwave.md, "Ask: a bare can"): a BARE can / tin / canned food (no closed, open or bowl word) put into the
# microwave makes the robot ASK "is it still sealed?" (option hazard key ask, phrase q_closed_can_microwave): yes refuses with CAN_SAY, only a clear no
# or an open word goes on (robot_agent's fail-safe answer rule). All words ASSUMED (from the manuals' class only, no benchmark text read). An open /
# empty / poured / no-lid / in-a-bowl word skips the question unless a negation is anywhere in the text (then it asks; an answer with one refuses).
CAN_WORD = (r"(?<![a-z0-9])(?<!trash[-_ ])(?<!garbage[-_ ])(?<!waste[-_ ])(?<!watering[-_ ])(?:cans?(?![-_ ](?:you|please)(?![a-z0-9]))"
            r"|tins?(?![-_ ]?foils?(?![a-z0-9]))|canned)(?![a-z0-9])(?![-_ ]?openers?(?![a-z0-9]))",
            r"(?<![가-힣])(?:[가-힣]*(?<!스)캔|[가-힣]*(?:통조림|깡통))(?:[은는이가을를도에의와과만](?![가-힣])|(?![가-힣]))")   # a noun alone or + one particle
_A_NEG = (r"(?s)^(?!.*(?:(?<![a-z0-9])(?:not|never|nor|neither|cannot|no[-_ ]longer)(?![a-z0-9])|n't(?![a-z0-9])"
          r"|않|못|(?<![가-힣])안 ?(?=[땄따딴열뜯개비부덜])|미개봉|아니(?=에|야|라|고|다|었)|아닌|아닙|그대로)).*")     # no negation anywhere
_A_PUT, _A_DONE = r"(?:bowls?|plates?|dish(?:es)?|mugs?)", r"[-_ ]?(?:놓|놨|둔|뒀)"
CAN_OPEN = (_A_NEG + r"(?:(?<![a-z0-9])(?:open(?![-_ ](?:the|a|an|it|up|this|that|my|your|its)(?![a-z0-9]))|opened(?![-_ ](?:the|a|an|my|your|this|"
            r"that)(?![a-z0-9]))|unsealed|empty|emptied|poured)(?![a-z0-9])|(?<![a-z0-9])(?:with[-_ ]no|without(?:[-_ ](?:a|its|the))?)[-_ ](?:lid|cap|top)"
            r"s?(?![a-z0-9])|(?<![a-z0-9])(?:lid|cap|top)[-_ ](?:is[-_ ])?(?:off|removed)(?![a-z0-9])|(?<![a-z0-9])(?:in|into|on)[-_ ](?:(?:a|the|my|its|"
            r"his|her|their)[-_ ])?(?:[a-z0-9]+[-_ ]){0,2}" + _A_PUT + r"(?![a-z0-9])|(?<![a-z0-9])" + _A_PUT + r"[-_ ]of(?![a-z0-9]))",
            _A_NEG + r"(?:열린|열려 ?있|열었|열어" + _A_DONE + r"|땄|따" + _A_DONE + r"|(?<!미)개봉(?:한|된|했|돼|되어)|뜯은|뜯었|뜯어" + _A_DONE
            + r"|(?<![가-힣])빈(?![가-힣])|비어 ?있|비었|부은|부었|부어" + _A_DONE + r"|덜어" + _A_DONE + r"|덜었|뚜껑(?:이|을|은)? ?(?:없|열려|열린|뗀|뗐)"
            r"|(?:그릇|접시|머그(?:컵)?|대접|사발)(?:에|에다|에다가)(?![가-힣]))")
CAN_ASK = [{"ask": "q_closed_can_microwave", "objects": list(CAN_WORD), "places": METAL_OVEN, "unless": list(CAN_OPEN), "say": CAN_SAY,
            "source": CAN_SOURCE + " (the class 'closed cans'; the can, open and bowl words and the question are assumed)", "assumed": True}]


# bt_goal (robot_agent docs/bt_goal.md): the trees of the goal kinds on / open / close / go from the mock robot's OWN declared skills (manifest move / find /
# pick / place / open / close = MoveTo / Find / Pick / Place / Open / Close, its Ask skill) in the order its manifest notes and pre-conditions give ("Find an
# object at its place before Pick"; pick pre found + hand_empty; place / open / close pre arrived(?inputs); open / close pre hand_empty). Each tree: the goal's
# condition first (already achieved: nothing to do), the steps, the goal's condition and an empty hand last. The engine's own ladder runs inside each step
# (retries, waits, search, its help question): no Retry or Ask node here. ASSUMED: the tree shapes are a design choice, not tuned on any task.
# Every MoveTo of a tree goes only when the robot is not at the place already (``_go``): a move to where the robot stands is a robot call SAGE's plan
# never makes (the engine's plan tidy drops it), and on the real profile one more chance of an injected fault (bt_goal 3 pilot, class "move to here").
def _go(slot: str) -> list:
    return ["fallback", ["cond", "at", slot], ["act", "MoveTo", slot]]


BT_ON = ["fallback", ["cond", "placed", "{object}", "{to}"],
         ["sequence",
          ["fallback", ["cond", "holding", "{object}"],
           ["sequence", ["cond", "hand_free"], _go("{from}"), ["act", "Find", "{object}"], ["act", "Pick", "{object}"],
            ["cond", "holding", "{object}"]]],
          _go("{to}"), ["act", "Place", "{to}"], ["cond", "placed", "{object}", "{to}"], ["cond", "hand_free"]]]
BT_OPEN = ["fallback", ["cond", "opened", "{object}"],
           ["sequence", ["cond", "hand_free"], _go("{object}"), ["act", "Open", "{object}"], ["cond", "opened", "{object}"]]]
BT_CLOSE = ["fallback", ["cond", "closed", "{object}"],
            ["sequence", ["cond", "hand_free"], _go("{object}"), ["act", "Close", "{object}"], ["cond", "closed", "{object}"]]]
BT_GO = _go("{to}")
BT_SOURCE = ("mock robot manifest (configs/manifest.yaml): skills move / find / pick / place / open / close / ask, planner.notes 'Find an object at its "
             "place before Pick', pick pre found(?inputs) hand_empty(), place pre arrived(?inputs), open / close pre arrived(?inputs) hand_empty(); the tree "
             "shapes are assumed")
# the question when a tree has no way left: robot_agent's ask_next menu phrases and answer words (language-pack data), per action of the mock robot
BT_MENU = {"phrases": {"Find": "q_ask_next_find", "Pick": "q_ask_next_pick", "MoveTo": "q_ask_next_move"},
           "retry": ["ask_next.retry", "ask_next.elsewhere", "dialogue.yes"], "stop": ["ask_next.stop", "dialogue.stop"],
           "source": "robot_agent option ask_next: its menu phrases q_ask_next_* and word lists (lang/*.json); the action map is the mock robot's", "assumed": True}
# in / say (robot_agent bt_goal 3): ``in`` = the container opened first while the hand is empty (open pre hand_empty(); put_in pre opened(?inputs),
# the manifest note "Open a container before PutIn"), then the fetch of ``on``, then PutIn and the goal's condition; the note's "close it after" is a
# later ``close`` goal's (data), not this tree's. ``say`` = the engine's own template (goals.compile_steps: MoveTo the place when not there, Say the
# sentence as the reader wrote it), with a place and without one; no condition after (nothing reads "said"). No ``deliver`` tree: this robot's
# WaitForUnload is only an alias of handover (manifest comment: the deliver goal does not fit an arm robot) and its reader is offered no deliver
# kind. No ``give`` tree: understand_give_kind is off in the D1 planners.
BT_IN = ["fallback", ["cond", "placed", "{object}", "{to}"],
         ["sequence",
          ["fallback", ["cond", "opened", "{to}"],
           ["sequence", ["cond", "hand_free"], _go("{to}"), ["act", "Open", "{to}"], ["cond", "opened", "{to}"]]],
          ["fallback", ["cond", "holding", "{object}"],
           ["sequence", ["cond", "hand_free"], _go("{from}"), ["act", "Find", "{object}"], ["act", "Pick", "{object}"],
            ["cond", "holding", "{object}"]]],
          _go("{to}"), ["act", "PutIn", "{to}"], ["cond", "placed", "{object}", "{to}"], ["cond", "hand_free"]]]
BT_SAY_AT = ["sequence", _go("{to}"), ["act", "Say", "{object}"]]
BT_SAY_HERE = ["act", "Say", "{object}"]
BT_SOURCE_3 = BT_SOURCE + "; put_in pre arrived(?inputs) opened(?inputs), say: robot_agent goals.compile_steps (the say template)"
BT_TREES = {"on": {"tree": BT_ON, "skip_if": ["hand"], "source": BT_SOURCE, "assumed": True},
            "open": {"tree": BT_OPEN, "source": BT_SOURCE, "assumed": True},
            "close": {"tree": BT_CLOSE, "source": BT_SOURCE, "assumed": True},
            "go": {"tree": BT_GO, "source": BT_SOURCE, "assumed": True},
            "in": {"tree": BT_IN, "source": BT_SOURCE_3, "assumed": True},
            "say": [{"tree": BT_SAY_AT, "source": BT_SOURCE_3, "assumed": True},
                    {"tree": BT_SAY_HERE, "skip_if": ["to"], "source": BT_SOURCE_3, "assumed": True}]}
# bt_open_source: the fetch of ``on`` / ``in`` opens the SOURCE first when the ENV declares it openable (robot_agent bt_goal entry key needs_openable;
# a surface, a place with no openable field: the tree above). Open only when not open in the belief, at the source (open pre arrived, hand_empty), before
# the Find. ASSUMED: the shape (the manifest's Find has no opened pre; SAGE's plans open first, bt_goal_layer.md measure 1), not tuned on any task.
BT_OPEN_FROM = ["fallback", ["cond", "opened", "{from}"], ["sequence", ["act", "Open", "{from}"], ["cond", "opened", "{from}"]]]


def _open_source(entry: dict) -> list:
    """[the entry with BT_OPEN_FROM right before its Find (used for an openable source only), the entry as it is]."""
    def put(node):
        if not isinstance(node, list) or node[0] not in ("sequence", "fallback"):
            return node
        kids = [put(c) for c in node[1:]]
        at = next((i for i, c in enumerate(kids) if c[:2] == ["act", "Find"] and node[0] == "sequence"), None)
        return [node[0], *(kids if at is None else kids[:at] + [BT_OPEN_FROM] + kids[at:])]
    src = entry["source"] + "; the Open of an openable source before Find is assumed (layer bt_open_source)"
    return [{**entry, "tree": put(entry["tree"]), "needs_openable": ["from"], "source": src}, entry]


BT_TREES_OPEN = {**BT_TREES, "on": _open_source(BT_TREES["on"]), "in": _open_source(BT_TREES["in"])}
# heard_check: robot_agent's starting values (docs/heard_check.md), ASSUMED, not measured or tuned on this benchmark
HEARD_MATCH = {"min_prefix": 2, "min_ratio": 0.5, "assumed": True}
# cond_answer: the words that negate an ANSWER ("it isn't there", "없어요"), added by robot_agent cond_goal key ``clauses`` to the language packs' negation
# patterns (English: not / don't / never ...). ASSUMED, general grammar, not measured or taken from any task text: English be / do / have / modal + n't; Korean
# 없- (not there), 않- (not), 아니 (no, not), 안 / 못 as a separate word (not / cannot; "안에", inside, is a noun + particle and does not match).
ANSWER_NEGATION = {"en": {"negation": r"\b(?:is|are|was|were|do|does|did|has|have|had|ca|could|wo|would|should)n'?t\b", "assumed": True},
                   "ko": {"negation": r"없|않|아니|(?<![가-힣])(?:안|못)(?=\s)", "assumed": True}}


LAYERS = {
    "precond_repair": ({"precond_repair": "1"},
                       {"planner": {"action_roles": {"pick": "Pick"},
                                    "options": {"precond_repair": {"needs": {
                                        "rules": {"Pick": {"hand_free": True}, "Place": {"holding": True, "achieves": "on"},
                                                  "PutIn": {"holding": True}, "Handover": {"holding": True, "achieves": "hand"}},
                                        "source": PRECOND_SOURCE}}}}}),
    # gate_prune: an Open / Close of a place the ENV declares not openable (explicit openable false) is dropped. Data: the roles of the mock robot's own
    # open / close actions, ASSUMED (names of its skills); without them the option does nothing.
    "gate_prune": ({"gate_prune": "1"}, {"planner": {"action_roles": {"open": "Open", "close": "Close"}}}),
    # dedupe_keep_end: the gate's removal of a repeated fetch keeps the way home after it. No pack data.
    "dedupe_keep_end": ({"dedupe_keep_end": "1"}, {}),
    # no pack data: it reads the robot's own object memory and limits (whole words, catalogue first)
    "goal_words": ({"goal_words": "1"}, {}),
    # no pack data: the world is the robot's object memory and limits; the phrases of "I don't know" are the language packs' own
    "ask_focus": ({"ask_focus": "1"}, {}),
    # no pack data: the names are the robot's object catalogue (object memory, limits.objects), read against the request's words
    "entity_cover": ({"entity_cover": "1"}, {}),
    # the receiver rules (hazard.receivers) are the mock robot's own safety profile (manifest safety.profile, household.yaml): no overlay data
    "hazard": ({"hazard_receiver": "1"}, {}),
    # hw_wait: the wait schedule and tries per failure kind. ASSUMED numbers (the mock robot's spec sheet declares none): a camera that is down and a
    # device fault get the same doubling backoff as the base wait, with tries; a kind not named here keeps the policy table. Not a simulator rule.
    "hw_wait": ({"hw_wait": "1"},
                {"planner": {"options": {"hw_wait": {"kinds": {
                    "perception_unavailable": {"schedule_s": [2, 4, 8], "tries": 3, "action": "wait_health"},
                    "hw_fault": {"schedule_s": [2, 4, 8], "tries": 2, "action": "wait_health"},
                    "assumed": True}}}}}),
    # search_budget: looks per object and the stop probability, ASSUMED numbers (about 8 looks, stop under about 10%; the brief's, not tuned), ask once. The
    # layer also turns reopen_on_miss OFF: its remedy [Close, Open] mirrors the simulator's partial-open state and cost 56-74 commands with no gain on the
    # ideal profile; the option is already once per container and pack-declared, so there is nothing left to narrow. (Not a simulator rule.)
    "search_budget": ({"search_budget": "1", "reopen_on_miss": "0"},
                      {"planner": {"options": {"search_budget": {"budget": {
                          "looks_per_object": 8, "stop_probability": 0.1, "ask": "once", "assumed": True}}}}}),
    # lang_words: condition and negation words per language. English is the pack's own (robot_agent lang/en.json); Korean has no clause data in the pack, so
    # the layer declares it here, ASSUMED (general grammar: a conditional ending on the last words of a clause, a "not / except" ending), not measured.
    "lang_words": ({"lang_words": "1"},
                   {"planner": {"options": {"lang_words": {"clauses": {"ko": {
                       "condition": KO_CONDITION,
                       "negation": KO_NEGATION,
                       "assumed": True}}}}}}),
    # --- D3 layers (on top of the ten D2 layers above, in the order cond_extract, recipient_keep, name_recover, replan_block; the ones that exist) ---
    # cond_extract (L9): a request with a condition word gets ONE extra model call that splits it into condition / goals-if / goals-else; cond_goal (without its
    # ``prompt`` key: the reader's schema and prompt stay) goes to the place, looks and keeps the branch that matches. ASSUMED data (each section labelled
    # ``assumed: true``: robot_agent uses an unlabelled text of these options as none): the extraction prompt, the Korean words above (the English ones are the
    # language pack's), the two questions (where to look, is it there), the move role of the mock robot's own skill. No sentence is said.
    "cond_extract": ({"cond_extract": "1", "cond_goal": "1"},
                     {"planner": {"action_roles": {"move": "MoveTo"},
                                  "options": {"cond_extract": {"prompt": COND_PROMPT, "q_unclear": "Where should I look for the {object}?",
                                                               "clauses": {"ko": {"condition": [KO_CONDITION, KO_COND_MORE], "assumed": True}},
                                                               "assumed": True},
                                              "cond_goal": {"q_where": "Where should I look for the {object}?", "q_unsure": "Is the {object} at the {place}?",
                                                            "assumed": True}}}}),
    # recipient_keep: a delivery's recipient moves to the speaker only on first-person evidence of the language packs. No pack data of its own.
    "recipient_keep": ({"recipient_keep": "1"}, {}),
    # plan_complete: a plan that stops short of the step its goal needs. ASSUMED data (names of the mock robot's own skills and what they end / need, not
    # simulator rules): a put-in ends an ``in`` goal, a hand-over ends a hand goal and needs the person near, a speech needs its listener near; the roles of
    # its open / close / speech / pick actions. The way home is the ``end_state`` data above.
    "plan_complete": ({"plan_complete": "1"},
                      {"planner": {"action_roles": {"open": "Open", "close": "Close", "say": "Say", "pick": "Pick"},
                                   "options": {"plan_complete": {"needs": {
                                       "rules": {"PutIn": {"achieves": "in"}, "Handover": {"achieves": "hand", "near": True}, "Say": {"near": True}},
                                       "assumed": True}}}}}),
    # ask_agree: the read-back dialogue (one more yes / no after a bare no and the same request; an "I don't know" keeps only a clean reading; an either-or when a
    # value changed). No pack data of its own: the words are the language packs' (fillers, first-person words, unsure phrases and their declared endings).
    "ask_agree": ({"ask_agree": "1"}, {}),
    # name_recover (L11): an object name the speech recogniser garbled takes the one near name of the object catalogue (two near names: asked), and asr_guard asks to repeat
    # an empty request or one with a hole (an article directly followed by a function word) without calling the reader. No pack data here: the limits are option keys with
    # their assumed defaults, the hole and distance-unit data are in the language packs (robot_agent lang/*.json, key ``asr``, labelled assumed).
    "name_recover": ({"name_recover": "1", "asr_guard": "1"}, {}),
    # replan_block: a replan repairs the right block (embodiplan SAGE key replan_block_fix, passed through the option), a goal change replans for sub-goals rebuilt
    # from the new goals, a replan suffix with a critical rule finding goes through the one refine; a finding the run-time check refuses itself only steers that
    # refine (the suffix then runs, the guard replans at the step), an empty-hand repeat of the last release is dropped. ASSUMED data: the action-model codes counted
    # critical in a suffix (a release with an empty hand, a release away from its place); not a simulator rule.
    "replan_block": ({"replan_guard": "1"},
                     {"planner": {"options": {"replan_guard": {"critical": {
                         "codes": ["place_without_holding", "place_wrong_location"], "assumed": True}}}}}),
    # release_near: SOURCED data only: the two releases need the robot at their place (the mock robot manifest's skills[].pre arrived(?inputs) of place / put_in),
    # so precond_repair (a D2 layer, it runs on a replan's suffix too) puts the missing MoveTo before them. It applies with precond_repair on, to EVERY plan (first
    # plans too), so it is its own layer (part of replan_block until 2026-11-15): an arm can tell its effect from replan_block's.
    "release_near": ({}, {"planner": {"options": {"precond_repair": {"needs": {
        "rules": {"Place": {"near": True}, "PutIn": {"near": True}},
        "source": PRECOND_SOURCE + "; near of Place / PutIn: skills[].pre arrived(?inputs) (layer release_near)"}}}}}),
    # hw_tries: with hw_wait on, an unhealthy robot after a wait does not stop the run while the tries declared by the hw_wait layer are left (hw_wait key more_tries).
    # The hw_wait layer alone behaves as in D2.
    "hw_tries": ({"hw_more_tries": "1"}, {}),
    # --- D4 layers (on top of the 18 D3 layers, in the build order of docs/home/bench/d4_layers.md) ---
    # plan_release (L15): the held object's own release goes before the Close of its ``in`` goal place even when the plan releases another object later, and the
    # release that splice empties gets its fetch. ASSUMED data, as plan_complete's (names of the mock robot's own skills and the goal kind each ends; the manifest
    # effects name no goal): a put-in ends an ``in`` goal, a put-down an ``on`` goal, a hand-over a hand goal; the roles are the mock robot's own action names.
    "plan_release": ({"plan_release": "1"},
                     {"planner": {"action_roles": {"move": "MoveTo", "find": "Find", "pick": "Pick", "close": "Close"},
                                  "options": {"plan_release": {"needs": {
                                      "rules": {"PutIn": {"achieves": "in"}, "Place": {"achieves": "on"}, "Handover": {"achieves": "hand"}},
                                      "assumed": True}}}}}),
    # repair_sync (L17): the gate's symbolic repair edits the plan the gate scores (the planner's blocks lined up with the steps the on_plan options added or
    # dropped), the suffix operator finish passes over a goal done before the replan, a suffix whose last release of a goal's object is elsewhere gets the
    # finding release_off_goal. No pack data (plan structure and the action model's replay only).
    "repair_sync": ({"repair_sync": "1"}, {}),
    # goal_ledger (L18): a go goal the engine's goal filter (F4.4) would drop is kept at the drop site when a heard word starts with a name of its place (restore,
    # silent). No pack data: the names are the ENV's heads and aliases; min_share is the option's own assumed default. OFF here: named (kept with no evidence, named
    # in the read-back), which the offline replay of d3dev fired on as many passing as failing episodes (the kill ratio of the red team), and retract, until its
    # firing on passing episodes is measured.
    "goal_ledger": ({"goal_ledger": "1"}, {}),
    # answer_align (L19): an answer or a correction is matched to a reading by the words that tell the readings apart: a yes or no to an either-or is asked
    # once more naming the options (reask), a correction that names one object leaves the other goals' destinations as they were (correction). No pack data:
    # the language packs' words (particles, endings, speaker forms, the q_pick_one phrase, labelled assumed in robot_agent lang/*.json). OFF here: ask_agree's
    # key distinct (the read-back's either-or by those words), which the offline replay of d3dev fired on one passing and one failing episode of the same
    # request (the kill ratio of the red team), until a pilot measures it.
    "answer_align": ({"answer_align": "1"}, {}),
    # --- SELECTABLE layers (named in a comma list only; not in ALL_LAYERS, so all / d3 / d2 and their hashes stay) ---
    # reach_check (TAMP-lite, robot_agent docs/reach_check.md): a Pick of an object a Find saw beyond the declared side reach gets the pack's declared
    # base shift first. No overlay data: the reach is the mock pack's own manifest geometry.reach_m, and the mock pack declares NO shift skill (none
    # is invented here), so the option is on and INERT in the bench (no reach_check lab event expected).
    "reach_check": ({"reach_check": "1"}, {}),
    # ask_next (robot_agent docs/ask_next.md): after a failed find / pick / move used its retries the robot asks "again here, somewhere else, or stop?"
    # and does what the answer says. No overlay data: the menu and its words are robot_agent's language-pack data (assumed). OFF in every arm: the
    # simulated person may not understand a menu question (its answers were not designed for it); to be measured in MuJoCo with a scripted person.
    "ask_next": ({"ask_next": "1"}, {}),
    # drop_search (robot_agent docs/options.md): a failed hand-over whose hand sensor reads empty looks for the carried object on the floor places of
    # the person's room, of the rooms passed since the Pick and of the Pick's place (the engine's REFIND rung), then hands it over again. Data: the
    # head of the map's floor places (the robot's ENV lists a floor@<room> place per room, brief section 5). ASSUMED: that head name.
    "drop_search": ({"drop_search": "1"}, {"planner": {"options": {"drop_search": {"floors": {"head": "floor", "assumed": True}}}}}),
    # heat_safety (robot_agent docs/heat_safety.md): a goal that puts a thing that can burn on or in a heat-source place is refused (or dropped and
    # named). Data: HEAT_SAFETY above (the mock robot's stove as the heat place, the FEMA clearance, a small list of words of things that burn).
    "heat_safety": ({"heat_safety": "1"}, {"planner": {"options": {"heat_safety": HEAT_SAFETY}}}),
    # bt_goal (robot_agent docs/bt_goal.md): when EVERY goal of a request is of a kind with a tree above (an ``on`` goal not a hand delivery, in, open, close, go, say),
    # the trees run the goals with the engine's own recovery, no plan call; any other goal in the request: SAGE plans the whole run. A tree with no way left:
    # policy A (robot_agent default ``exhausted`` = ask_or_stop: the menu question once when a person can help, else stop). bt_goal_sage: the same with
    # policy B (``sage_once``: the remaining goals to the SAGE replan once).
    "bt_goal": ({"bt_goal": "1"}, {"planner": {"options": {"bt_goal": {"trees": BT_TREES, "menu": BT_MENU}}}}),
    "bt_goal_sage": ({"bt_goal": "1", "bt_goal.exhausted": "sage_once"}, {"planner": {"options": {"bt_goal": {"trees": BT_TREES, "menu": BT_MENU}}}}),
    # bt_open_source: bt_goal (policy A unless bt_goal_sage is on too) with the on / in trees that open an openable closed source before the Find
    # (BT_TREES_OPEN above). On its own or after bt_goal / bt_goal_sage the overlay is the same (its trees replace theirs key by key).
    "bt_open_source": ({"bt_goal": "1"}, {"planner": {"options": {"bt_goal": {"trees": BT_TREES_OPEN, "menu": BT_MENU}}}}),
    # metal_microwave (robot_agent docs/metal_microwave.md): a goal that puts a thing with a metal word into the microwave is refused by option hazard
    # (on in every arm; its rules key core reads the manifest list). No loop option; data: METAL_MICROWAVE above.
    "metal_microwave": ({}, {"safety": {"hazards": METAL_MICROWAVE}}),
    # metal_microwave_ask: metal_microwave plus a question for a bare utensil word (key hazard.ask; the whole list, so on its own or after metal_microwave
    # the overlay is the same: a later layer's list replaces an earlier one).
    "metal_microwave_ask": ({"hazard_ask": "1"}, {"safety": {"hazards": METAL_MICROWAVE + METAL_ASK}}),
    # closed_can_microwave: a closed / sealed can, jar or bottle put into the microwave is refused (option hazard, no loop option; data CLOSED_CAN above).
    # With metal_microwave(_ask) on too, the lists are joined (``_hazards``), not replaced.
    "closed_can_microwave": ({}, {"safety": {"hazards": CLOSED_CAN}}),
    # closed_can_ask: closed_can_microwave plus a question for a bare can word (key hazard.ask; the whole list, so on its own or after closed_can_microwave
    # the overlay is the same; joined with metal_microwave(_ask) by ``_hazards``).
    "closed_can_ask": ({"hazard_ask": "1"}, {"safety": {"hazards": CLOSED_CAN + CAN_ASK}}),
    # heard_check (robot_agent docs/heard_check.md): a goal whose own quote of the person (``said``, a say goal's message) no heard word matches gets an
    # ``object`` issue on the read-back (the engine's re-sample, repeat question, read-back follow). ASSUMED data, not tuned: two characters in common at the
    # start of a word (one syllable pair, one letter pair), half the characters of the word cut to the quote's length.
    "heard_check": ({"heard_check": "1"}, {"planner": {"options": {"heard_check": {"match": HEARD_MATCH}}}}),
    # shared_instances (robot_agent docs/options.md, class C1): a goal object named exactly like a memory record with no instance id, while the records
    # with an id that hold the name are two or more instances, is asked about (inventory_ask's which-question; a read-back choice issue). No overlay data:
    # the records are the robot's own object memory (the seed writes no id for a name two objects share).
    "shared_instances": ({"shared_instances": "1"}, {}),
    # cond_answer (robot_agent cond_goal keys answer / open_closed / confirm_none; class B of the cond20 dev analysis): the answer to "is the X at P?" is read
    # by itself (a yes, a no, a negation, or the place it names; "I don't know" or nothing usable: UNKNOWN, the run ends failed with the question), a closed
    # place the ENV declares openable is opened before the look, and a "nothing to do" decided on a look that could not see inside is asked once more. Needs
    # the cond_extract layer (it turns cond_goal on). Data: ANSWER_NEGATION above and the open role of the mock robot's own Open skill (assumed).
    "cond_answer": ({"cond_goal.answer": "1", "cond_goal.open_closed": "1", "cond_goal.confirm_none": "1"},
                    {"planner": {"action_roles": {"open": "Open"}, "options": {"cond_goal": {"clauses": ANSWER_NEGATION, "assumed": True}}}}),
    # cond_schema (robot_agent cond_extract keys kinds / heard_match; classes A and I of the cond20 dev analysis): the extraction also says the kind of the
    # condition, the goals to do in every case (always) and, for a condition no look settles, one yes / no question that cond_goal asks and reads (needs the
    # cond_answer layer: without it nothing is asked); a condition object no heard word matches is UNKNOWN (the run ends failed), an unheard place is asked.
    # Data (assumed): COND_PROMPT_KINDS, HEARD_MATCH (heard_check's numbers, not tuned) and the clause list of cond_extract plus KO_COND_COME.
    "cond_schema": ({"cond_extract.kinds": "1"},
                    {"planner": {"options": {"cond_extract": {
                        "prompt": COND_PROMPT_KINDS, "heard_match": HEARD_MATCH, "assumed": True,
                        "clauses": {"ko": {"condition": [KO_CONDITION, KO_COND_MORE, KO_COND_COME], "assumed": True}}}}}}),
}
SELECTABLE = ("reach_check",)
SELECTABLE += ("ask_next",)
SELECTABLE += ("drop_search",)
SELECTABLE += ("heat_safety",)
SELECTABLE += ("bt_goal",)
SELECTABLE += ("bt_goal_sage",)
SELECTABLE += ("bt_open_source",)
SELECTABLE += ("metal_microwave",)
SELECTABLE += ("metal_microwave_ask",)
SELECTABLE += ("heard_check",)
SELECTABLE += ("shared_instances",)
SELECTABLE += ("closed_can_microwave",)
SELECTABLE += ("closed_can_ask",)
SELECTABLE += ("cond_answer",)
SELECTABLE += ("cond_schema",)
D2_LAYERS = ("precond_repair", "gate_prune", "dedupe_keep_end", "goal_words", "ask_focus", "entity_cover", "hazard", "hw_wait", "search_budget", "lang_words")
# ``d3``: the D2 layers, then every D3 layer in this order (the D3 arm; its loop options, overlay and on tuple hash to f751d734..., the D3 snapshot). Until
# 2026-11-15 the D3 part held only cond_extract, recipient_keep, name_recover, replan_block (an interface criterion written before L13 / L14 existed), so a D3
# arm measured before that date never ran plan_complete, ask_agree or hw_tries. release_near (the near data that came with replan_block until that date)
# follows replan_block.
D3_LAYERS = D2_LAYERS + ("cond_extract", "recipient_keep", "plan_complete", "ask_agree", "name_recover", "replan_block", "release_near", "hw_tries")
# ``all`` (and unset): the D3 layers, then the D4 layers in their build order. A base_d3 arm must say ``d3``.
D4_LAYERS = ("plan_release", "repair_sync", "goal_ledger", "answer_align")
# Deleted on 2026-11-15 after the D4 stay gate (d4_layers.md ## Removed; robot_agent commit that added each option): effect_check (91bbced),
# question_cap (2ab4c9c), partial_end (ac322b9), safety_profile (e329a71), fault_ladder (0e4a112), close_opened (9fa2ecc), else_ask (47eeb14); their
# D1 entries (and the overlay data FIRE_CLEARANCE, FAULT_DEVICES) are in this file's git history before the deletion (symbolic_robot efdd8d8).
# Deleted on 2026-11-17 (d4_layers.md ## Removed): the selectable drop_search_goal (robot_agent drop_search key goal_check, 559ce54); D5 dev, 3 arms x 4
# cells x 150 tasks: 9 fires, 0 outcomes changed, +0 successes, +2 false successes; its D1 entry is in this file's git history before the deletion.
ALL_LAYERS = D3_LAYERS + D4_LAYERS


@functools.lru_cache(maxsize=None)
def _warn_both(new: str, old_name: str, old: str) -> None:
    print(f"warning: {LAYERS_ENV}={new!r} and {old_name}={old!r} differ; {LAYERS_ENV} is used", file=sys.stderr)


def layers_value(environ=None):
    """The raw layer list: ``LAYERS_ENV``, else (unset or empty) the former name ``HOMELOOP_D1_LAYERS`` (renamed 2026-11-18, still accepted);
    None when neither is set. Both set and different: the new name wins, with one stderr line per pair of values."""
    env = environ if environ is not None else os.environ
    old_name = "HOMELOOP_D1_LAYERS"
    new, old = env.get(LAYERS_ENV), env.get(old_name)
    if new and old and new.strip().lower() != old.strip().lower():
        _warn_both(new, old_name, old)
    return new or old


def selected_layers(environ=None) -> tuple:
    """The layers that are on: ``all`` (unset too: ``ALL_LAYERS``, d3 + the D4 layers), ``d3`` (exactly the 18 D3 layers), ``d2`` (exactly the ten D2
    layers), ``none``, or a comma list of names of ``LAYERS``; an unknown name is an error."""
    raw = (layers_value(environ) or "all").strip().lower()
    aliases = {"all": ALL_LAYERS, "d3": D3_LAYERS, "d2": D2_LAYERS}
    if raw in aliases:
        return aliases[raw]
    names = [n.strip() for n in raw.split(",") if n.strip()] if raw != "none" else []
    bad = [n for n in names if n not in LAYERS]
    if bad:
        raise ValueError(f"{LAYERS_ENV}: unknown layer {bad} (known: {sorted(LAYERS)}, all, d3, d2, none)")
    return tuple(n for n in LAYERS if n in names)


def layer_options(environ=None) -> dict:
    """The loop options of the layers that are on."""
    return {k: v for n in selected_layers(environ) for k, v in LAYERS[n][0].items()}


# the pack data those options read. ASSUMED: the mock robot's own action names (find, open, close, dock), not tuned values.
D1_DATA = {"planner": {"action_roles": {"find": "Find"},
                       "recovery": {"reopen_on_miss": ["Close", "Open"]},
                       "end_state": {"places": ["dock"], "action": "Dock"}},
           "note": "assumed: D1 failure-class data (the find role, reopen_on_miss [Close, Open], end_state dock + Dock); the last two match "
                   "the mock robot's partial-open and docked() rules, read them as an ablation"}


D1_CLASSES = {**D1_CLASSES_D, **layer_options()}          # D's options + the layers that are on (LAYERS_ENV)


def _merge(base: dict, add: dict) -> dict:
    out = dict(base or {})
    for k, v in add.items():
        out[k] = _merge(out.get(k) or {}, v) if isinstance(v, dict) else copy.deepcopy(v)
    return out


def _labels(data) -> list:
    """The labels found anywhere in a layer's pack data: ``sourced: <source>`` for a ``source`` string, ``assumed`` for ``assumed: true``."""
    out = []
    if isinstance(data, list):
        return list(dict.fromkeys(x for v in data for x in _labels(v)))
    if isinstance(data, dict):
        out += ["sourced: " + data["source"]] if isinstance(data.get("source"), str) and data["source"].strip() else []
        out += ["assumed"] if data.get("assumed") is True else []
        for v in data.values():
            out += _labels(v)
    return list(dict.fromkeys(out))


def _hazards(overlays) -> list:
    """The manifest lists ``safety.hazards`` of ``overlays`` joined in order, each entry once (a list that holds another, as metal_microwave_ask's
    holds metal_microwave's, gives the same list as before; [] when none has one)."""
    out = []
    for ov in overlays:
        out += [copy.deepcopy(e) for e in (ov.get("safety") or {}).get("hazards") or [] if e not in out]
    return out


def layer_note(name: str) -> str:
    """One layer for the overlay note: its name and the label of its pack data (as declared in ``LAYERS``)."""
    data = LAYERS[name][1]
    if not data:
        return f"{name} (no overlay data)"
    return f"{name} ({'; '.join(_labels(data)) or 'assumed: unlabelled names of the mock robot pack'})"


def d1_overlay(base: dict, translate_model: str, environ=None) -> dict:
    """``base`` (the variant's overlay) with this reader as translator, the D1 data and the data of the layers that are on, merged key by key."""
    on = selected_layers(environ)
    out = _merge(base, {"planner": {**D1_DATA["planner"], "translate_model": translate_model}})
    for n in on:
        out = _merge(out, LAYERS[n][1])
    hazards = _hazards([base] + [LAYERS[n][1] for n in on])
    if hazards:
        out["safety"] = {**out["safety"], "hazards": hazards}
    note = str(base.get("note", "")) + "; " + D1_DATA["note"]
    if on:
        note += "; layers on (" + LAYERS_ENV + "): " + ", ".join(layer_note(n) for n in on)
    return {**out, "assumed": True, "note": note}
