"""The D1 layer ``shared_instances`` (robot_agent option, default off; class C1 "an exact name hides a shared memory record"): selectable by
name only, its loop option alone, no overlay data, the arm hashes unchanged. Pure data: no run, no model."""
from bench.suites.home.planners import d1_options as D
from test_bt_goal_layer import ALL_HASH, D2_HASH, D3_HASH, MODEL, digest, env


def test_shared_instances_is_selectable_only_and_leaves_the_arm_hashes():
    assert "shared_instances" in D.SELECTABLE and "shared_instances" not in D.ALL_LAYERS
    assert digest(env("d3")) == D3_HASH and digest(env("all")) == ALL_HASH and digest(env("d2")) == D2_HASH


def test_shared_instances_on_top_of_all_adds_its_option_only():
    on = env(",".join(D.ALL_LAYERS + ("shared_instances",)))
    assert D.selected_layers(on) == D.ALL_LAYERS + ("shared_instances",)
    assert D.layer_options(on) == {**D.layer_options(env("all")), "shared_instances": "1"}
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, env("all"))
    assert "shared_instances (no overlay data)" in ov.pop("note")
    base.pop("note")
    assert ov == base
