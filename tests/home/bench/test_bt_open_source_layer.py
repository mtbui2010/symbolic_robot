"""The D1 layer ``bt_open_source`` (robot_agent bt_goal entry key needs_openable): selectable only, the on / in fetch opens an openable source before
the Find, a surface or a place with no openable field keeps the bt_goal tree, the arm hashes unchanged. Pure data, made-up places; no run, no model."""
import pytest

from bench.suites.home.planners import d1_options as D
from robot_agent.core.planning import behavior_tree as bt
from robot_agent.options import bt_goal as B
from tests.home.bench.test_bt_goal_layer import ALL_HASH, D2_HASH, D3_HASH, MODEL, digest, entries, env, guarded

BOX, DESK, NOOK, SINK = "box@study", "desk@study", "nook@study", "tub@study"
ENV = {BOX: {"openable": True}, DESK: {"openable": False}, NOOK: {}, SINK: {"openable": True}}
ACTS = {"MoveTo", "Find", "Pick", "Place", "PutIn", "Open", "Close", "Say"}


def openable(key):
    return B.declared_openable(ENV, key, lambda k: bool(ENV[k].get("openable")))


def tree(kind, trees, src, opener=openable):
    g = {"type": kind, "object": "trinket", "from": src, "to": SINK if kind == "in" else DESK}
    return B.tree_for(g, trees, ACTS, True, lambda k: True, openable=opener)


def acts(t):
    return [leaf[1] for leaf in bt.leaves(t) if leaf[0] == "act"]


def test_bt_open_source_is_selectable_only_and_leaves_the_arm_hashes():
    assert "bt_open_source" in D.SELECTABLE and "bt_open_source" not in D.ALL_LAYERS
    assert digest(env("d3")) == D3_HASH and digest(env("all")) == ALL_HASH and digest(env("d2")) == D2_HASH


@pytest.mark.parametrize("before", [(), ("bt_goal",), ("bt_goal_sage",)])
def test_the_layer_adds_bt_goal_and_changes_only_the_on_and_in_trees(before):
    on = env(",".join(D.ALL_LAYERS + before + ("bt_open_source",)))
    ref = env(",".join(D.ALL_LAYERS + (before or ("bt_goal",))))
    assert D.layer_options(on) == D.layer_options(ref)
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, ref)
    got, was = ov["planner"]["options"]["bt_goal"].pop("trees"), base["planner"]["options"]["bt_goal"].pop("trees")
    assert {k: v for k, v in got.items() if k not in ("on", "in")} == {k: v for k, v in was.items() if k not in ("on", "in")}
    assert all(got[k] == [got[k][0], was[k]] and got[k][0]["needs_openable"] == ["from"] for k in ("on", "in"))
    ov.pop("note"), base.pop("note")
    assert ov == base


def test_bt_goal_trees_are_unchanged_off():
    assert D.LAYERS["bt_goal"][1]["planner"]["options"]["bt_goal"]["trees"] is D.BT_TREES
    assert not any("needs_openable" in e for e in entries(D.BT_TREES))


def test_the_opening_entries_are_labelled_guarded_and_name_only_declared_actions():
    for e in entries(D.BT_TREES_OPEN):
        assert e["assumed"] is True and e["source"] and guarded(e["tree"])[0] == guarded(e["tree"])[1]
        assert set(acts(e["tree"])) <= ACTS


@pytest.mark.parametrize("kind,want", [("on", ["MoveTo", "Open", "Find", "Pick", "MoveTo", "Place"]),
                                       ("in", ["MoveTo", "Open", "MoveTo", "Open", "Find", "Pick", "MoveTo", "PutIn"])])
def test_regression_an_openable_source_is_opened_before_the_find(kind, want):
    """The class (d5dev bt_goal): the fetch looked into a closed source container (absent, one attempt used) and opened it only after."""
    t = tree(kind, D.BT_TREES_OPEN, BOX)
    assert acts(t) == want and acts(t).index("Find") == acts(t).index("Open", 2 if kind == "in" else 0) + 1
    assert ["act", "Open", BOX] in list(bt.leaves(t))


@pytest.mark.parametrize("kind", ["on", "in"])
@pytest.mark.parametrize("src", [DESK, NOOK, "attic@study"])
def test_a_surface_or_unknown_source_keeps_the_bt_goal_tree(kind, src):
    assert tree(kind, D.BT_TREES_OPEN, src) == tree(kind, D.BT_TREES, src)


def test_no_place_data_keeps_the_bt_goal_tree_empty():
    for kind in ("on", "in"):
        assert tree(kind, D.BT_TREES_OPEN, BOX, opener=None) == tree(kind, D.BT_TREES, BOX)
        assert tree(kind, D.BT_TREES_OPEN, BOX, opener=lambda k: B.declared_openable({}, k, bool)) == tree(kind, D.BT_TREES, BOX)
