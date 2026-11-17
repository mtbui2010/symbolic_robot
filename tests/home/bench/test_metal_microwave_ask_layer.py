"""The D1 layer ``metal_microwave_ask`` (robot_agent option hazard key ``ask``, robot_agent docs/metal_microwave.md "Ask"): selectable by name
only, the arm hashes unchanged, one switch (the loop key and the whole list), its words decided by robot_agent's own matcher on made-up
objects ("zorb ...")."""
from types import SimpleNamespace as NS

import pytest

from bench.suites.home.planners import d1_options as D
from test_metal_microwave_layer import ALL_HASH, D2_HASH, D3_HASH, MODEL, OVEN, digest, env


def test_metal_microwave_ask_is_selectable_only_and_leaves_the_arm_hashes():
    assert "metal_microwave_ask" in D.SELECTABLE and "metal_microwave_ask" not in D.ALL_LAYERS
    assert digest(env("d3")) == D3_HASH and digest(env("all")) == ALL_HASH and digest(env("d2")) == D2_HASH


@pytest.mark.parametrize("extra", [("metal_microwave_ask",), ("metal_microwave", "metal_microwave_ask")])
def test_metal_microwave_ask_is_one_switch_the_key_and_the_whole_list(extra):
    on, base = env(",".join(D.ALL_LAYERS + extra)), env("all")
    assert D.layer_options(on) == {**D.layer_options(base), "hazard_ask": "1"}
    ov = D.d1_overlay({}, MODEL, on)
    assert ov["safety"] == {"hazards": D.METAL_MICROWAVE + D.METAL_ASK}


def test_metal_microwave_ask_entry_is_labelled_assumed_and_names_its_phrase_and_reason():
    (e,) = D.METAL_ASK
    assert e["assumed"] is True and "ehs.berkeley.edu" in e["source"] and "assumed" in e["source"]
    assert e["ask"] == "q_metal_microwave" and e["say"] == D.METAL_SAY and e["places"] == D.METAL_OVEN
    assert "can" not in " ".join(e["objects"]).replace("cutlery", "")        # no can: not in the cited pages


# robot_agent's own matcher: which made-up goal is asked, refused or left alone (the order: the metal entries refuse first)
@pytest.mark.parametrize("obj, said, to, says", [
    ("zorb spoon", "", OVEN, "ask"), ("zorb", "the zorb teaspoon", OVEN, "ask"), ("zorb knives", "", OVEN, "ask"),
    ("zorb", "숟가락을 전자레인지에", OVEN, "ask"), ("plastic zorb spoon", "", OVEN, None), ("wooden zorb fork", "", OVEN, None),
    ("zorb", "실리콘 숟가락", OVEN, None), ("steel zorb spoon", "", OVEN, "refuse"), ("metal zorb fork", "", OVEN, "refuse"),
    ("zorb spoon", "", "drawer@kitchen", None), ("zorb spoonful", "", OVEN, None), ("zorb", "칼국수", OVEN, None),
])
def test_metal_microwave_ask_word_table_through_robot_agents_matcher(obj, said, to, says):
    safety = pytest.importorskip("robot_agent.core.safety")
    hazard = pytest.importorskip("robot_agent.options.hazard")
    g = {"type": "in", "object": obj, "said": said, "from": "", "to": to}
    if safety.find_rule(g, NS(env={}), safety.EMPTY, D.METAL_MICROWAVE) is not None:
        got = "refuse"
    else:
        e = D.METAL_ASK[0]
        fires = safety.find_rule(g, NS(env={}), safety.EMPTY, [e], "pack") is not None and not hazard.unless_hit(e, g)
        got = "ask" if fires else None
    assert got == says
