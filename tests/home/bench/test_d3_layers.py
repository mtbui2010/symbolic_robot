"""D3: the D1 layer switch with the ``d2`` alias and the D3 layers (``HOMELOOP_D1_LAYERS``). Pure data: no run, no model."""
import hashlib
import json

from bench.suites.home.planners import d1_options as D

D2 = ("precond_repair", "gate_prune", "dedupe_keep_end", "goal_words", "ask_focus", "entity_cover", "hazard", "hw_wait", "search_budget", "lang_words")
D3 = ("cond_extract", "recipient_keep", "plan_complete", "ask_agree", "name_recover", "replan_block")
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


def test_plan_complete_alone_on_top_of_d2_adds_its_option_and_its_declared_data_only():
    on = ",".join(D2 + ("plan_complete",))
    assert D.selected_layers(env(on)) == D2 + ("plan_complete",)
    assert D.layer_options(env(on)) == {**D.layer_options(env("d2")), "plan_complete": "1"} and "plan_complete" not in D.layer_options(env("d2"))
    ov, ov2 = D.d1_overlay({}, MODEL, env(on)), D.d1_overlay({}, MODEL, env("d2"))
    need = ov["planner"]["options"]["plan_complete"]["needs"]
    assert need["assumed"] is True and need["rules"]["PutIn"] == {"achieves": "in"} and need["rules"]["Say"]["near"] is True
    assert "plan_complete" not in ov2["planner"].get("options", {}) and ov["planner"]["options"]["precond_repair"] == ov2["planner"]["options"]["precond_repair"]


def test_ask_agree_alone_on_top_of_d2_adds_its_option_and_no_pack_data():
    on = ",".join(D2 + ("ask_agree",))
    assert D.selected_layers(env(on)) == D2 + ("ask_agree",)
    assert D.layer_options(env(on)) == {**D.layer_options(env("d2")), "ask_agree": "1"} and "ask_agree" not in D.layer_options(env("d2"))
    ov, ov2 = D.d1_overlay({}, MODEL, env(on)), D.d1_overlay({}, MODEL, env("d2"))
    ov.pop("note", None), ov2.pop("note", None)
    assert ov == ov2                                                          # no overlay data: the D2 data only
    assert D.selected_layers(env("all")).index("ask_agree") > D.selected_layers(env("all")).index("plan_complete")
    assert digest(env("d2")) == D2_HASH


def test_replan_block_alone_on_top_of_d2_adds_the_option_and_its_assumed_codes_only():
    on = ",".join(D2 + ("replan_block",))
    assert D.selected_layers(env(on)) == D2 + ("replan_block",)
    assert D.layer_options(env(on)) == {**D.layer_options(env("d2")), "replan_guard": "1"} and "replan_guard" not in D.layer_options(env("d2"))
    ov, ov2 = D.d1_overlay({}, MODEL, env(on)), D.d1_overlay({}, MODEL, env("d2"))
    crit = ov["planner"]["options"]["replan_guard"]["critical"]
    assert crit["assumed"] is True and crit["codes"] and "replan_guard" not in ov2["planner"].get("options", {})
    assert D.selected_layers(env("all"))[-1] == "replan_block" and digest(env("d2")) == D2_HASH


def test_name_recover_alone_on_top_of_d2_turns_on_the_two_asr_options_and_no_pack_data():
    on = ",".join(D2 + ("name_recover",))
    assert D.selected_layers(env(on)) == D2 + ("name_recover",)
    assert D.layer_options(env(on)) == {**D.layer_options(env("d2")), "name_recover": "1", "asr_guard": "1"}
    assert "name_recover" not in D.layer_options(env("d2")) and digest(env("d2")) == D2_HASH
    assert D.d1_overlay({}, MODEL, env(on)).get("planner") == D.d1_overlay({}, MODEL, env("d2")).get("planner")      # no data of its own in the overlay


def test_cond_extract_alone_on_top_of_d2_turns_on_it_and_cond_goal_without_the_reader_prompt_key():
    on = ",".join(D2 + ("cond_extract",))
    assert D.selected_layers(env(on)) == D2 + ("cond_extract",)
    assert D.layer_options(env(on)) == {**D.layer_options(env("d2")), "cond_extract": "1", "cond_goal": "1"}      # no cond_goal.prompt: the reader's schema and prompt stay
    assert "cond_extract" not in D.layer_options(env("d2")) and "cond_goal" not in D.layer_options(env("d2"))
    ov = D.d1_overlay({}, MODEL, env(on))["planner"]["options"]
    assert set(ov["cond_extract"]) == {"prompt", "q_unclear", "clauses"} and "prompt" not in ov["cond_goal"]
    assert ov["cond_extract"]["clauses"]["ko"]["assumed"] is True and "{request}" in ov["cond_extract"]["prompt"] and "{goals}" in ov["cond_extract"]["prompt"]
    assert D.d1_overlay({}, MODEL, env("d2"))["planner"]["options"].keys() >= {"lang_words"} and "cond_extract" not in D.d1_overlay({}, MODEL, env("d2"))["planner"]["options"]


def test_cond_extract_korean_words_add_the_sighting_and_the_negation_that_the_d2_clause_misses():
    import re
    more, d2 = re.compile(D.KO_COND_MORE), re.compile(D.KO_CONDITION)
    for text in ("서랍에 컵이 보이면 치워줘", "컵이 식탁에 아니면 가져와", "컵이 거기 아니라면 두지 마"):
        assert more.search(text), text
    assert not d2.search("서랍에 컵이 보이면 치워줘") and not d2.search("컵이 식탁에 아니면 가져와")
    assert not more.search("컵을 식탁에 놓아줘") and not more.search("서랍을 열어줘")
