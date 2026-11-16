"""The selectable D1 layer ``single_goals`` (robot_agent option ``single_goals``: one action with no destination is read and done as that action):
named on top of d3 it turns on the option and nothing else; it is not in ``all``, so the all / d3 / d2 hashes stay. Pure data: no run, no model."""
import pytest

from bench.suites.home.planners import d1_options as D
from tests.home.bench.test_d4_layers import ALL_HASH, D2_HASH, D3, D3_HASH, MODEL, digest, env


def test_single_goals_is_selectable_and_not_in_all_d3_or_d2():
    assert "single_goals" in D.SELECTABLE and "single_goals" in D.LAYERS
    for alias in ("all", "d3", "d2", "none"):
        assert "single_goals" not in D.selected_layers(env(alias)) and "single_goals" not in D.layer_options(env(alias))
    assert digest(env("all")) == ALL_HASH and digest(env("d3")) == D3_HASH and digest(env("d2")) == D2_HASH


def test_single_goals_alone_on_top_of_d3_turns_on_its_option_with_no_overlay_data():
    on = env(",".join(D3 + ("single_goals",)))
    assert D.selected_layers(on) == D3 + ("single_goals",)
    assert D.layer_options(on) == {**D.layer_options(env("d3")), "single_goals": "1"}
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, env("d3"))
    assert "single_goals (no overlay data)" in ov["note"]
    ov.pop("note"), base.pop("note")
    assert ov == base                                    # the rule lines and the phrase are robot_agent's language-pack data


def test_single_goals_on_top_of_all_adds_only_its_option():
    on = env(",".join(D.ALL_LAYERS + ("single_goals",)))
    assert D.selected_layers(on) == D.ALL_LAYERS + ("single_goals",)
    assert D.layer_options(on) == {**D.layer_options(env("all")), "single_goals": "1"}


def test_single_goals_layer_data_is_labelled_or_empty():
    data = D.LAYERS["single_goals"][1]
    assert not data or D._labels(data)
    with pytest.raises(ValueError):
        D.selected_layers(env("single_goal"))           # a misspelt name is refused, not ignored
