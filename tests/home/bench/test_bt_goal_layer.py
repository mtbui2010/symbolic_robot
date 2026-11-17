"""The D1 layer ``bt_goal`` (robot_agent option, default off, prototype): selectable by name only, its tree labelled and built from the mock
robot's own declared skills, the arm hashes unchanged. Pure data: no run, no model."""
import hashlib
import json

import pytest
import yaml

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


def leaves(node):
    if node[0] in ("sequence", "fallback"):
        for c in node[1:]:
            yield from leaves(c)
    elif node[0] == "retry":
        yield from leaves(node[2])
    else:
        yield node


def test_bt_goal_is_selectable_only_and_leaves_the_arm_hashes():
    assert {"bt_goal", "bt_goal_sage"} <= set(D.SELECTABLE) and not {"bt_goal", "bt_goal_sage"} & set(D.ALL_LAYERS)
    assert digest(env("d3")) == D3_HASH and digest(env("all")) == ALL_HASH and digest(env("d2")) == D2_HASH


@pytest.mark.parametrize("layer,opts", [("bt_goal", {"bt_goal": "1"}), ("bt_goal_sage", {"bt_goal": "1", "bt_goal.exhausted": "sage_once"})])
def test_bt_goal_on_top_of_all_adds_its_option_and_its_trees_only(layer, opts):
    on = env(",".join(D.ALL_LAYERS + (layer,)))
    assert D.selected_layers(on) == D.ALL_LAYERS + (layer,)
    assert D.layer_options(on) == {**D.layer_options(env("all")), **opts}
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, env("all"))
    data = ov["planner"]["options"].pop("bt_goal")
    assert set(data["trees"]) == {"on", "open", "close", "go"} and all(t["assumed"] is True and t["source"] for t in data["trees"].values())
    assert data["menu"] == D.BT_MENU and data["menu"]["assumed"] is True
    ov.pop("note"), base.pop("note")
    assert ov == base


def test_bt_goal_trees_name_only_actions_the_mock_robot_declares():
    import symbolic_robot.domains.home.configs as cfg
    from pathlib import Path
    man = yaml.safe_load((Path(cfg.__file__).parent / "manifest.yaml").read_text(encoding="utf-8"))
    declared = {s["action"] for s in man["skills"]}
    acts = {leaf[1] for t in D.BT_TREES.values() for leaf in leaves(t["tree"]) if leaf[0] == "act"}
    assert acts == {"MoveTo", "Find", "Pick", "Place", "Open", "Close"} and acts <= declared and "Ask" in declared
    assert set(D.BT_MENU["phrases"]) <= declared
    first = {k: t["tree"][1] for k, t in D.BT_TREES.items()}               # the goal's condition comes first: an achieved goal does nothing
    assert {k: f[0] for k, f in first.items()} == {k: "cond" for k in first}
