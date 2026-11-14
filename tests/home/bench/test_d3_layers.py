"""D3: the D1 layer switch with the ``d2`` alias and the D3 layers (``HOMELOOP_D1_LAYERS``). Pure data: no run, no model."""
import hashlib
import json

from bench.suites.home.planners import d1_options as D

D2 = ("precond_repair", "gate_prune", "dedupe_keep_end", "goal_words", "ask_focus", "entity_cover", "hazard", "hw_wait", "search_budget", "lang_words")
D3 = ("cond_extract", "recipient_keep", "name_recover", "replan_block")
D2_HASH = "64b278b5beef2493d675eac77ebd6d10b799e2ce2e307014e56b3f207e356942"      # the ten D2 layers: on, loop options, overlay without its note
MODEL = "hl-understand-p3-s700"


def env(v):
    return {D.LAYERS_ENV: v}


def digest(e):
    ov = D.d1_overlay({}, MODEL, e)
    ov.pop("note", None)
    blob = json.dumps({"on": D.selected_layers(e), "opts": D.layer_options(e), "overlay": ov}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()


def test_d2_alias_is_exactly_the_ten_d2_layers_and_equals_the_d2_overlay():
    assert D.selected_layers(env("d2")) == D2 == D.D2_LAYERS and D.selected_layers(env(" D2 ")) == D2
    assert digest(env("d2")) == D2_HASH                                       # the loop options, the overlay and the on tuple as in D2


def test_all_is_the_d2_layers_then_the_d3_layers_that_exist():
    got = D.selected_layers(env("all"))
    assert got[:10] == D2 and got[10:] and set(got[10:]) <= set(D3)
    assert [n for n in D3 if n in got] == list(got[10:])                       # in the order of the brief
    assert D.selected_layers({}) == got                                        # the default is all


def test_none_selects_nothing():
    assert D.selected_layers(env("none")) == () and D.layer_options(env("none")) == {}


def test_recipient_keep_alone_on_top_of_d2_changes_only_its_own_option():
    both = D.selected_layers(env(",".join(D2 + ("recipient_keep",))))
    assert both == D2 + ("recipient_keep",)
    assert {k: v for k, v in D.layer_options(env("d2")).items()} == {k: v for k, v in D.layer_options(env(",".join(both))).items() if k != "recipient_keep"}
    assert D.layer_options(env(",".join(both)))["recipient_keep"] == "1" and "recipient_keep" not in D.layer_options(env("d2"))
    assert D.layer_options(env("recipient_keep")) == {"recipient_keep": "1"}


def test_an_unknown_layer_is_refused_and_d2_is_not_a_member_name():
    try:
        D.selected_layers(env("d2,no_such_layer"))
    except ValueError as e:
        assert "no_such_layer" in str(e)
    else:
        raise AssertionError("an unknown layer must be refused")
