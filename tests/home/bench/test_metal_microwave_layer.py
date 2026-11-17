"""The D1 layer ``metal_microwave`` (data of robot_agent's option hazard, robot_agent docs/metal_microwave.md): selectable by name only, its overlay
data labelled and from the cited pages, the arm hashes unchanged, its words decided by robot_agent's own rule matcher on made-up objects ("zorb ...")."""
import hashlib
import json
from types import SimpleNamespace as NS

import pytest

from bench.suites.home.planners import d1_options as D

D3_HASH = "f751d73417c679250af675869633f8f1278ab7fcfe9127c3c249f53e294beab3"
D2_HASH = "64b278b5beef2493d675eac77ebd6d10b799e2ce2e307014e56b3f207e356942"
ALL_HASH = "78f601bfeee57accd86d4d628ce0b9385dca7327c3546944ed18d126fbe6669a"
MODEL = "hl-understand-p3-s700"
OVEN = "microwave@kitchen"


def env(v):
    return {D.LAYERS_ENV: v}


def digest(e):
    ov = D.d1_overlay({}, MODEL, e)
    ov.pop("note", None)
    blob = json.dumps({"on": D.selected_layers(e), "opts": D.layer_options(e), "overlay": ov}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()


def test_metal_microwave_is_selectable_only_and_leaves_the_arm_hashes():
    assert "metal_microwave" in D.SELECTABLE and "metal_microwave" not in D.ALL_LAYERS
    assert digest(env("d3")) == D3_HASH and digest(env("all")) == ALL_HASH and digest(env("d2")) == D2_HASH


def test_metal_microwave_on_top_of_all_adds_the_manifest_list_only():
    on = env(",".join(D.ALL_LAYERS + ("metal_microwave",)))
    assert D.selected_layers(on) == D.ALL_LAYERS + ("metal_microwave",) and D.layer_options(on) == D.layer_options(env("all"))
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, env("all"))
    assert ov.pop("safety") == {"hazards": D.METAL_MICROWAVE} and "safety" not in base
    ov.pop("note"), base.pop("note")
    assert ov == base


def test_metal_microwave_every_entry_is_labelled_cites_the_three_pages_and_says_the_same_reason():
    for e in D.METAL_MICROWAVE:
        assert all(u in e["source"] for u in ("news2use.ors.nih.gov", "ehs.berkeley.edu", "service.hoover.co.uk")) and e["say"] == D.METAL_SAY
    assert "assumed" not in D.METAL_MICROWAVE[0] and D.METAL_MICROWAVE[1]["assumed"] is True       # page words sourced, the rest assumed
    assert "sourced: " + D.METAL_SOURCE in D._labels(D.LAYERS["metal_microwave"][1])


def test_metal_microwave_lists_no_utensil_or_container_noun_and_no_safe_material_empty():
    text = " ".join(p for e in D.METAL_MICROWAVE for p in e["objects"])
    assert not any(w in text for w in ("fork", "knife", "spoon", "can", "glass", "ceramic", "plastic", "safe"))


def test_metal_microwave_overlay_joins_the_frozen_profile_path_in_the_manifest_safety_section():
    from bench.suites.home.planners.robot_agent_adapter import apply_overlay
    loop = NS(robot=NS(manifest=NS(safety={"profile": "safety/made_up.yaml"}, planner={})))
    apply_overlay(loop, D.LAYERS["metal_microwave"][1])
    assert loop.robot.manifest.safety == {"profile": "safety/made_up.yaml", "hazards": D.METAL_MICROWAVE}


# the words through robot_agent's own matcher (made-up objects; the place is the mock robot's ENV key head)
@pytest.mark.parametrize("obj, said, to, refused", [
    ("foil wrapped zorb", "", OVEN, True), ("zorb_tray_metal_trim", "", OVEN, True), ("zorb", "the zorb in its aluminium foil", OVEN, True),
    ("ceramic zorb mug with a metal handle", "", OVEN, True), ("stainless steel zorb", "", OVEN, True), ("zorb", "은박 접시의 조브", OVEN, True),
    ("metal-free glass zorb bowl", "", OVEN, False), ("non-metal zorb", "", OVEN, False), ("plastic zorb fork", "", OVEN, False),
    ("zorb fork", "", OVEN, False), ("foil wrapped zorb", "", "counter@kitchen", False), ("zorb", "비금속 조브 그릇", OVEN, False),
])
def test_metal_microwave_word_table_through_the_engines_matcher(obj, said, to, refused):
    safety = pytest.importorskip("robot_agent.core.safety")
    g = {"type": "in", "object": obj, "said": said, "from": "", "to": to}
    assert (safety.find_rule(g, NS(env={}), safety.EMPTY, D.METAL_MICROWAVE) is not None) is refused
