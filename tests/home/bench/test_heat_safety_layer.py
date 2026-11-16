"""The D1 layer ``heat_safety`` (robot_agent option, default off): selectable by name only, its overlay data labelled, the arm hashes unchanged.
Pure data: no run, no model."""
import hashlib
import json

from bench.suites.home.planners import d1_options as D

D3_HASH = "f751d73417c679250af675869633f8f1278ab7fcfe9127c3c249f53e294beab3"
D2_HASH = "64b278b5beef2493d675eac77ebd6d10b799e2ce2e307014e56b3f207e356942"
ALL_HASH = "78f601bfeee57accd86d4d628ce0b9385dca7327c3546944ed18d126fbe6669a"
MODEL = "hl-understand-p3-s700"


def env(v):
    return {D.LAYERS_ENV: v}


def digest(e):
    ov = D.d1_overlay({}, MODEL, e)
    ov.pop("note", None)
    blob = json.dumps({"on": D.selected_layers(e), "opts": D.layer_options(e), "overlay": ov}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()


def test_heat_safety_is_selectable_only_and_leaves_the_arm_hashes():
    assert "heat_safety" in D.SELECTABLE and "heat_safety" not in D.ALL_LAYERS
    assert digest(env("d3")) == D3_HASH and digest(env("all")) == ALL_HASH and digest(env("d2")) == D2_HASH


def test_heat_safety_on_top_of_all_adds_its_option_and_its_data_only():
    on = env(",".join(D.ALL_LAYERS + ("heat_safety",)))
    assert D.selected_layers(on) == D.ALL_LAYERS + ("heat_safety",)
    assert D.layer_options(on) == {**D.layer_options(env("all")), "heat_safety": "1"}
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, env("all"))
    assert ov["planner"]["options"].pop("heat_safety") == D.HEAT_SAFETY
    ov.pop("note"), base.pop("note")
    assert ov == base


def test_heat_safety_every_entry_is_labelled_and_cites_the_fema_page():
    data = D.HEAT_SAFETY
    entries = list(data["places"].values()) + [data["burnable"]]
    assert all(e.get("assumed") is True and "usfa.fema.gov" in e["source"] for e in entries)
    assert all(e["clearance_m"] == 0.91 for e in data["places"].values())          # 3 feet, the cited distance
    assert "sourced: " + D.HEAT_SOURCE in D._labels(D.LAYERS["heat_safety"][1])


def test_heat_safety_word_list_is_generic_no_cookware_empty():
    words = set(D.HEAT_SAFETY["burnable"]["words"])
    assert not words & {"pot", "pan", "kettle", "frying pan", "wok"}          # the stove's own things pass (fail open)
