"""The selectable D1 layer ``reach_check`` (TAMP-lite, robot_agent option ``reach_check``): named on top of d3 it turns on the option and nothing
else; it is not in ``all``, so the all / d3 / d2 hashes stay. Pure data: no run, no model."""
import pytest

from bench.suites.home.planners import d1_options as D
from tests.home.bench.test_d4_layers import ALL_HASH, D2_HASH, D3, D3_HASH, MODEL, digest, env


def test_reach_check_is_selectable_and_not_in_all_d3_or_d2():
    assert "reach_check" in D.SELECTABLE and "reach_check" in D.LAYERS     # the exact SELECTABLE tuple: test_ask_next_layer.py (2026-11-16)
    for alias in ("all", "d3", "d2", "none"):
        assert "reach_check" not in D.selected_layers(env(alias)) and "reach_check" not in D.layer_options(env(alias))
    assert digest(env("all")) == ALL_HASH and digest(env("d3")) == D3_HASH and digest(env("d2")) == D2_HASH


def test_reach_check_alone_on_top_of_d3_turns_on_its_option_with_no_overlay_data():
    on = env(",".join(D3 + ("reach_check",)))
    assert D.selected_layers(on) == D3 + ("reach_check",)
    assert D.layer_options(on) == {**D.layer_options(env("d3")), "reach_check": "1"}
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, env("d3"))
    assert "reach_check (no overlay data)" in ov["note"]
    ov.pop("note"), base.pop("note")
    assert ov == base                                    # no shift skill is invented: the mock pack declares none, so the option is inert here


def test_reach_check_on_top_of_all_adds_only_its_option():
    on = env(",".join(D.ALL_LAYERS + ("reach_check",)))
    assert D.selected_layers(on) == D.ALL_LAYERS + ("reach_check",)
    assert D.layer_options(on) == {**D.layer_options(env("all")), "reach_check": "1"}


def test_reach_check_layer_data_is_labelled_or_empty():
    data = D.LAYERS["reach_check"][1]
    assert not data or D._labels(data)
    with pytest.raises(ValueError):
        D.selected_layers(env("reach_chek"))            # a misspelt name is refused, not ignored
