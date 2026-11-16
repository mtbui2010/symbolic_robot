"""The D1 layer ``bt_goal`` (robot_agent option, default off, prototype): selectable by name only, its tree labelled and built from the mock
robot's own declared skills, the arm hashes unchanged. Pure data: no run, no model."""
import hashlib
import json

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
    assert "bt_goal" in D.SELECTABLE and "bt_goal" not in D.ALL_LAYERS
    assert digest(env("d3")) == D3_HASH and digest(env("all")) == ALL_HASH and digest(env("d2")) == D2_HASH


def test_bt_goal_on_top_of_all_adds_its_option_and_its_tree_only():
    on = env(",".join(D.ALL_LAYERS + ("bt_goal",)))
    assert D.selected_layers(on) == D.ALL_LAYERS + ("bt_goal",)
    assert D.layer_options(on) == {**D.layer_options(env("all")), "bt_goal": "1"}
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, env("all"))
    trees = ov["planner"]["options"].pop("bt_goal")["trees"]
    assert set(trees) == {"on"} and trees["on"]["tree"] == D.BT_ON and trees["on"]["assumed"] is True and trees["on"]["source"]
    ov.pop("note"), base.pop("note")
    assert ov == base


def test_bt_goal_tree_names_only_actions_the_mock_robot_declares():
    import symbolic_robot.domains.home.configs as cfg
    from pathlib import Path
    man = yaml.safe_load((Path(cfg.__file__).parent / "manifest.yaml").read_text(encoding="utf-8"))
    declared = {s["action"] for s in man["skills"]}
    acts = {leaf[1] for leaf in leaves(D.BT_ON) if leaf[0] == "act"}
    assert acts == {"MoveTo", "Find", "Pick", "Place"} and acts <= declared and "Ask" in declared
