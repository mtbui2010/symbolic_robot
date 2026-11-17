"""The D1 layer ``closed_can_microwave`` (data of robot_agent's option hazard, robot_agent docs/metal_microwave.md "Closed can"): selectable by
name only, the arm hashes unchanged, its list joined with the metal lists (not replaced), its words decided by robot_agent's own rule matcher
on made-up objects ("zorb ...", "조브 ...")."""
from types import SimpleNamespace as NS

import pytest

from bench.suites.home.planners import d1_options as D
from test_metal_microwave_layer import ALL_HASH, D2_HASH, D3_HASH, MODEL, OVEN, digest, env


def hazards(*extra):
    return D.d1_overlay({}, MODEL, env(",".join(D.ALL_LAYERS + extra))).get("safety", {}).get("hazards")


def test_closed_can_microwave_off_is_selectable_only_and_leaves_the_arm_hashes():
    assert "closed_can_microwave" in D.SELECTABLE and "closed_can_microwave" not in D.ALL_LAYERS
    assert digest(env("d3")) == D3_HASH and digest(env("all")) == ALL_HASH and digest(env("d2")) == D2_HASH
    assert hazards() is None


def test_closed_can_microwave_empty_no_list_gives_no_safety_key():
    assert D._hazards([{}, {"safety": {}}, {"planner": {}}]) == [] and "safety" not in D.d1_overlay({}, MODEL, env("none"))


def test_closed_can_microwave_adds_its_list_and_no_loop_option():
    on = env(",".join(D.ALL_LAYERS + ("closed_can_microwave",)))
    assert D.layer_options(on) == D.layer_options(env("all")) and hazards("closed_can_microwave") == D.CLOSED_CAN


@pytest.mark.parametrize("extra, want", [
    (("metal_microwave",), "M"), (("metal_microwave_ask",), "MA"), (("metal_microwave", "metal_microwave_ask"), "MA"),
    (("metal_microwave", "closed_can_microwave"), "MC"), (("metal_microwave_ask", "closed_can_microwave"), "MAC"),
])
def test_closed_can_microwave_lists_are_joined_and_the_metal_lists_stay_as_before(extra, want):
    parts = {"M": D.METAL_MICROWAVE, "A": D.METAL_ASK, "C": D.CLOSED_CAN}
    assert hazards(*extra) == [e for k in want for e in parts[k]]


def test_closed_can_microwave_entries_are_labelled_assumed_and_cite_the_three_manuals():
    for e in D.CLOSED_CAN:
        assert e["assumed"] is True and e["say"] == D.CAN_SAY and e["places"] == D.METAL_OVEN
        assert all(w in e["source"] for w in ("NDSU", "FN1622", "HL-MX465S", "closed cans or bottles", "JE1240L", "closed jars", "URLs are unknown"))
    assert "sourced: " + D.CLOSED_CAN[0]["source"] in D._labels(D.LAYERS["closed_can_microwave"][1])


# the words through robot_agent's own matcher (made-up objects; the place is the mock robot's ENV key head)
@pytest.mark.parametrize("obj, said, to, refused", [
    ("sealed zorb can", "put the sealed zorb can in the microwave", OVEN, True), ("zorb", "the closed zorb jar", OVEN, True),
    ("unopened zorb tin", "", OVEN, True), ("sealed plastic zorb bottle", "", OVEN, True), ("zorb can", "the zorb can is still sealed", OVEN, True),
    ("zorb", "밀봉된 조브 캔을 전자레인지에", OVEN, True), ("조브 통조림", "따지 않은 조브 통조림", OVEN, True), ("zorb", "뚜껑이 닫힌 조브 병을", OVEN, True),
    ("open zorb can", "put the open zorb can in the microwave", OVEN, False), ("zorb soup", "heat the zorb soup in a bowl", OVEN, False),
    ("plastic zorb box", "", OVEN, False), ("ceramic zorb mug", "", OVEN, False), ("zorb can", "", OVEN, False),
    ("unsealed zorb can", "", OVEN, False), ("zorb can", "the zorb can is not sealed", OVEN, False), ("sealed zorb jar that is open", "", OVEN, False),
    ("sealed zorb can with no lid", "", OVEN, False), ("sealed empty zorb jar", "", OVEN, False),
    ("zorb", "open the sealed zorb can and heat the zorb in a bowl", OVEN, False), ("zorb", "the closed zorb fridge can you heat it", OVEN, False),
    ("zorb", "밀봉된 조브 캔을 따서 그릇에", OVEN, False), ("zorb", "밀봉 안 된 조브 캔", OVEN, False), ("zorb", "개봉한 조브 캔", OVEN, False),
    ("zorb", "빈 조브 병", OVEN, False), ("zorb", "닫힌 냉장고 안의 조브 병", OVEN, False), ("zorb", "플라스틱 조브 그릇", OVEN, False),
    ("sealed zorb can", "", "counter@kitchen", False),
])
def test_closed_can_microwave_word_table_through_the_engines_matcher(obj, said, to, refused):
    safety = pytest.importorskip("robot_agent.core.safety")
    g = {"type": "in", "object": obj, "said": said, "from": "", "to": to}
    assert (safety.find_rule(g, NS(env={}), safety.EMPTY, D.CLOSED_CAN) is not None) is refused


def test_closed_can_microwave_regression_a_sealed_can_into_the_oven_is_refused_with_the_can_reason_not_asked():
    """The class: a reading in(<sealed can> -> microwave) with the metal layers on was neither refused (no material word) nor asked (no utensil
    word); with this layer on, robot_agent's matcher refuses it, and with the can's reason (the metal entries do not fire first)."""
    safety = pytest.importorskip("robot_agent.core.safety")
    g = {"type": "in", "object": "zorb soup can", "said": "put the sealed zorb soup can in the microwave", "from": "", "to": OVEN}
    refusing = [e for e in hazards("metal_microwave_ask") if not e.get("ask")]
    assert safety.find_rule(g, NS(env={}), safety.EMPTY, refusing) is None
    refusing = [e for e in hazards("metal_microwave_ask", "closed_can_microwave") if not e.get("ask")]
    assert safety.find_rule(g, NS(env={}), safety.EMPTY, refusing).say == D.CAN_SAY
