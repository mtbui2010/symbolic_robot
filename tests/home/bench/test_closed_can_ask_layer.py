"""The D1 layer ``closed_can_ask`` (robot_agent option hazard key ``ask``, robot_agent docs/metal_microwave.md "Ask: a bare can"): selectable by
name only, the arm hashes unchanged, one switch (the loop key and the whole list), joined with the metal and closed-can lists, its words and the
answers decided by robot_agent's own matcher and answer rule on made-up objects ("zorb ...", "조브 ...")."""
from types import SimpleNamespace as NS

import pytest

from bench.suites.home.planners import d1_options as D
from test_metal_microwave_layer import ALL_HASH, D2_HASH, D3_HASH, MODEL, OVEN, digest, env

PARTS = {"M": D.METAL_MICROWAVE, "A": D.METAL_ASK, "C": D.CLOSED_CAN, "K": D.CAN_ASK}


def hazards(*extra):
    return D.d1_overlay({}, MODEL, env(",".join(D.ALL_LAYERS + extra))).get("safety", {}).get("hazards")


def says(g, entries):
    """What robot_agent's option hazard does with goal ``g`` under ``entries``: refuse (with which say), ask (which phrase) or None."""
    safety = pytest.importorskip("robot_agent.core.safety")
    hazard = pytest.importorskip("robot_agent.options.hazard")
    v = safety.find_rule(g, NS(env={}), safety.EMPTY, [e for e in entries if not e.get("ask")])
    if v is not None:
        return "refuse:" + v.say
    hit = [e for e in entries if e.get("ask") and not hazard.unless_hit(e, g)
           and safety.find_rule(g, NS(env={}), safety.EMPTY, [e], "pack") is not None]
    return "ask:" + hit[0]["ask"] if hit else None


def goal(obj, said="", to=OVEN):
    return {"type": "in", "object": obj, "said": said, "from": "", "to": to}


def test_closed_can_ask_off_is_selectable_only_and_leaves_the_arm_hashes():
    assert "closed_can_ask" in D.SELECTABLE and "closed_can_ask" not in D.ALL_LAYERS
    assert digest(env("d3")) == D3_HASH and digest(env("all")) == ALL_HASH and digest(env("d2")) == D2_HASH
    assert hazards() is None and "hazard_ask" not in D.layer_options(env("all"))


def test_closed_can_ask_empty_an_entry_with_no_words_asks_nothing():
    empty = [{**D.CAN_ASK[0], "objects": []}]
    assert says(goal("zorb can"), empty) is None and D._hazards([{}, {"safety": {"hazards": []}}]) == []


@pytest.mark.parametrize("extra", [("closed_can_ask",), ("closed_can_microwave", "closed_can_ask")])
def test_closed_can_ask_is_one_switch_the_key_and_the_whole_list(extra):
    on = env(",".join(D.ALL_LAYERS + extra))
    assert D.layer_options(on) == {**D.layer_options(env("all")), "hazard_ask": "1"}
    assert D.d1_overlay({}, MODEL, on)["safety"] == {"hazards": D.CLOSED_CAN + D.CAN_ASK}


@pytest.mark.parametrize("extra, want", [
    (("metal_microwave",), "M"), (("metal_microwave_ask",), "MA"), (("metal_microwave_ask", "closed_can_microwave"), "MAC"),
    (("metal_microwave", "closed_can_ask"), "MCK"), (("metal_microwave_ask", "closed_can_ask"), "MACK"),
    (("metal_microwave_ask", "closed_can_microwave", "closed_can_ask"), "MACK"),
])
def test_closed_can_ask_lists_are_joined_and_the_earlier_lists_stay_as_before(extra, want):
    assert hazards(*extra) == [e for k in want for e in PARTS[k]]


def test_closed_can_ask_entry_is_labelled_assumed_and_names_its_phrase_and_the_can_reason():
    (e,) = D.CAN_ASK
    assert e["assumed"] is True and "HL-MX465S" in e["source"] and "assumed" in e["source"] and "URLs are unknown" in e["source"]
    assert e["ask"] == "q_closed_can_microwave" and e["say"] == D.CAN_SAY and e["places"] == D.METAL_OVEN


# robot_agent's own matcher: which made-up goal is asked, refused or left alone with the closed-can list on
@pytest.mark.parametrize("obj, said, to, want", [
    ("zorb can", "", OVEN, "ask"), ("zorb", "the zorb soup can", OVEN, "ask"), ("zorb tin", "", OVEN, "ask"), ("canned zorb", "", OVEN, "ask"),
    ("zorb", "조브 통조림을", OVEN, "ask"), ("zorb", "조브캔", OVEN, "ask"), ("zorb", "깡통에 든 조브", OVEN, "ask"),
    ("zorb", "the zorb can that is not open", OVEN, "ask"), ("zorb", "open the zorb can and heat it", OVEN, "ask"),
    ("zorb", "the zorb can we haven't opened", OVEN, "ask"), ("zorb", "안 딴 조브 캔", OVEN, "refuse"), ("zorb", "뚜껑 안 뗀 조브 캔", OVEN, "ask"),
    ("sealed zorb can", "", OVEN, "refuse"), ("zorb", "밀봉된 조브 캔", OVEN, "refuse"), ("unopened zorb tin", "", OVEN, "refuse"),
    ("open zorb can", "", OVEN, None), ("opened zorb can", "", OVEN, None), ("empty zorb tin", "", OVEN, None),
    ("zorb can", "the zorb can with no lid", OVEN, None), ("zorb", "the canned zorb in a bowl", OVEN, None),
    ("zorb", "zorb from the can poured into a mug", OVEN, None), ("zorb", "a plate of canned zorb", OVEN, None),
    ("zorb", "개봉한 조브 캔", OVEN, None), ("zorb", "그릇에 담은 조브 통조림", OVEN, None), ("zorb", "빈 깡통", OVEN, None),
    ("zorb soup", "", OVEN, None), ("zorb", "can you heat the zorb", OVEN, None), ("zorb", "tin foil zorb", OVEN, None),
    ("zorb", "the zorb can opener", OVEN, None), ("zorb", "trash can zorb", OVEN, None), ("zorb", "pecan zorb", OVEN, None),
    ("zorb", "스캔한 조브", OVEN, None), ("zorb", "캔디", OVEN, None), ("zorb can", "", "counter@kitchen", None),
])
def test_closed_can_ask_word_table_through_robot_agents_matcher(obj, said, to, want):
    got = says(goal(obj, said, to), D.CLOSED_CAN + D.CAN_ASK)
    assert (got.split(":")[0] if got else None) == want
    assert want != "refuse" or got == "refuse:" + D.CAN_SAY


# the answer to "is the zorb can still sealed?" through robot_agent's own reader (yes_no) and fail-safe rule (answer_says)
@pytest.mark.parametrize("answer, want", [
    ("no", "proceed"), ("No, it is open.", "proceed"), ("it's open", "proceed"), ("I opened it", "proceed"), ("it's empty", "proceed"),
    ("no, I poured it into a bowl", "proceed"), ("아니요", "proceed"), ("아니요, 땄어요", "proceed"), ("열려 있어요", "proceed"),
    ("yes", "refuse"), ("네", "refuse"), ("it is closed", "refuse"), ("it's not open", "refuse"), ("I haven't opened it", "refuse"),
    ("never mind", "refuse"), ("I don't know", "refuse"), ("yes it's open", "refuse"), ("안 땄어요", "refuse"), ("열려 있지 않아요", "refuse"),
    ("됐어요", "refuse"), ("", "unanswered"),
])
def test_closed_can_ask_answers_through_robot_agents_fail_safe_rule(answer, want):
    hazard = pytest.importorskip("robot_agent.options.hazard")
    yes_no = pytest.importorskip("robot_agent.core.run_control").yes_no
    assert hazard.answer_says(answer, False, yes_no(answer), hazard.unless_hit(D.CAN_ASK[0], {"object": answer})) == want


@pytest.mark.parametrize("obj, said, want", [
    ("zorb spoon", "", "ask:q_metal_microwave"), ("steel zorb spoon", "", "refuse:" + D.METAL_SAY), ("plastic zorb spoon", "", None),
    ("zorb can", "", "ask:q_closed_can_microwave"), ("sealed zorb can", "", "refuse:" + D.CAN_SAY), ("open zorb can", "", None),
    ("zorb", "the zorb jar", None), ("zorb tin", "", "refuse:" + D.METAL_SAY),       # tin is a metal word: the metal rule refuses first
])
def test_closed_can_ask_three_layers_together_each_rule_fires_only_for_its_own_words(obj, said, want):
    assert says(goal(obj, said), hazards("metal_microwave_ask", "closed_can_microwave", "closed_can_ask")) == want


def test_closed_can_ask_regression_a_bare_can_into_the_oven_is_asked_not_refused_and_not_done_silently():
    """The class: a reading in(<bare soup can> -> microwave) with metal_microwave_ask and closed_can_microwave on was neither refused (no closed
    word) nor asked (no utensil word); with this layer on, robot_agent's matcher asks the can question once, and a yes refuses with the can reason."""
    g = goal("zorb soup can", "put the zorb soup can in the microwave")
    assert says(g, hazards("metal_microwave_ask", "closed_can_microwave")) is None
    assert says(g, hazards("metal_microwave_ask", "closed_can_microwave", "closed_can_ask")) == "ask:q_closed_can_microwave"
