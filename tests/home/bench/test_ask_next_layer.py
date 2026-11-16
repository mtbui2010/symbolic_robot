"""The selectable D1 layer ``ask_next`` (robot_agent option ``ask_next``: after a failed step used its retries, ask "again here, somewhere else, or
stop?"): named on top of d3 it turns on the option and nothing else; it is not in ``all``, so the all / d3 / d2 hashes stay. Kept off in every arm:
the simulated person may not understand a menu question. Pure data: no run, no model."""
import pytest

from bench.suites.home.planners import d1_options as D
from tests.home.bench.test_d4_layers import ALL_HASH, D2_HASH, D3, D3_HASH, MODEL, digest, env


def test_ask_next_is_selectable_and_not_in_all_d3_or_d2():
    assert D.SELECTABLE == ("reach_check", "ask_next") and "ask_next" in D.LAYERS
    for alias in ("all", "d3", "d2", "none"):
        assert "ask_next" not in D.selected_layers(env(alias)) and "ask_next" not in D.layer_options(env(alias))
    assert digest(env("all")) == ALL_HASH and digest(env("d3")) == D3_HASH and digest(env("d2")) == D2_HASH


def test_ask_next_alone_on_top_of_d3_turns_on_its_option_with_no_overlay_data():
    on = env(",".join(D3 + ("ask_next",)))
    assert D.selected_layers(on) == D3 + ("ask_next",)
    assert D.layer_options(on) == {**D.layer_options(env("d3")), "ask_next": "1"}
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, env("d3"))
    assert "ask_next (no overlay data)" in ov["note"]
    ov.pop("note"), base.pop("note")
    assert ov == base                                    # the menu and its words are robot_agent's language-pack data, nothing is added here


def test_ask_next_with_reach_check_on_top_of_all_adds_only_their_options():
    on = env(",".join(D.ALL_LAYERS + ("reach_check", "ask_next")))
    assert D.selected_layers(on) == D.ALL_LAYERS + ("reach_check", "ask_next")
    assert D.layer_options(on) == {**D.layer_options(env("all")), "reach_check": "1", "ask_next": "1"}


def test_ask_next_layer_data_is_labelled_or_empty():
    data = D.LAYERS["ask_next"][1]
    assert not data or D._labels(data)
    with pytest.raises(ValueError):
        D.selected_layers(env("ask_nxt"))               # a misspelt name is refused, not ignored
