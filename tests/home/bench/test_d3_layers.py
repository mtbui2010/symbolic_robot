"""D3: the D1 layer switch with the ``d2`` alias and the D3 layers (``HOMELOOP_D1_LAYERS``). Pure data: no run, no model."""
import hashlib
import json

from bench.suites.home.planners import d1_options as D

D2 = ("precond_repair", "gate_prune", "dedupe_keep_end", "goal_words", "ask_focus", "entity_cover", "hazard", "hw_wait", "search_budget", "lang_words")
D3 = ("cond_extract", "recipient_keep", "plan_complete", "ask_agree", "name_recover", "replan_block", "release_near", "hw_tries")   # ``all`` after the D2 ten, in this order
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


def test_all_is_the_d2_layers_then_every_d3_layer_in_order():
    got = D.selected_layers(env("d3"))                                         # D4: the D3 arm is the alias d3; all = d3 + D4 (test_d4_layers.py)
    assert got == D2 + D3 and set(got) | set(D.D4_LAYERS) == set(D.LAYERS)    # every known layer; until 2026-11-15 plan_complete, ask_agree, hw_tries were left out
    assert D.selected_layers({}) == D.ALL_LAYERS == got + D.D4_LAYERS                 # the default is all (D4: the seven retired layers deleted)
    assert D.layer_options(env("d3")) == {k: v for n in D2 + D3 for k, v in D.LAYERS[n][0].items()}
    for n in ("plan_complete", "ask_agree", "hw_tries"):
        assert n in got and {k: v for k, v in D.layer_options(env("all")).items() if k in D.LAYERS[n][0]} == D.LAYERS[n][0]
    assert "plan_complete" in D.d1_overlay({}, MODEL, env("all"))["planner"]["options"]


def test_none_d2_and_each_single_layer_select_as_before():
    assert D.selected_layers(env("none")) == () and D.layer_options(env("none")) == {} and digest(env("d2")) == D2_HASH
    ov_none = D.d1_overlay({}, MODEL, env("none"))
    assert "options" not in ov_none["planner"] and "D2 layers on" not in ov_none["note"]       # none: D1 of D2 (the D1 data only)
    for n in D.LAYERS:
        assert D.selected_layers(env(n)) == (n,) and D.layer_options(env(n)) == D.LAYERS[n][0], n
        assert D.selected_layers(env(",".join(D2 + (n,)))) == (D2 if n in D2 else D2 + (n,)), n


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
    assert "ask_agree" in D.selected_layers(env("all")) and "ask_agree" in D.LAYERS
    assert digest(env("d2")) == D2_HASH


def test_replan_block_alone_on_top_of_d2_adds_the_option_and_its_assumed_codes_only():
    on = ",".join(D2 + ("replan_block",))
    assert D.selected_layers(env(on)) == D2 + ("replan_block",)
    assert D.layer_options(env(on)) == {**D.layer_options(env("d2")), "replan_guard": "1"} and "replan_guard" not in D.layer_options(env("d2"))
    ov, ov2 = D.d1_overlay({}, MODEL, env(on)), D.d1_overlay({}, MODEL, env("d2"))
    crit = ov["planner"]["options"]["replan_guard"]["critical"]
    assert crit["assumed"] is True and crit["codes"] and "replan_guard" not in ov2["planner"].get("options", {})
    assert "replan_block" in D.selected_layers(env("all")) and "plan_complete" in D.selected_layers(env("all")) and digest(env("d2")) == D2_HASH


def test_release_near_declares_the_near_need_of_the_releases_with_a_source_and_leaves_d2_data_as_it_was():
    on = ",".join(D2 + ("release_near",))
    need, need2 = (D.d1_overlay({}, MODEL, env(e))["planner"]["options"]["precond_repair"]["needs"] for e in (on, "d2"))
    assert need["rules"]["Place"]["near"] is True and need["rules"]["PutIn"]["near"] is True and "arrived" in need["source"]
    assert need["source"].startswith(need2["source"]) and {a: {k: v for k, v in r.items() if k != "near"} for a, r in need["rules"].items()} == need2["rules"]
    assert not any(r.get("near") for r in need2["rules"].values()) and digest(env("d2")) == D2_HASH
    assert D.layer_options(env(on)) == D.layer_options(env("d2"))            # data only: no loop option of its own
    assert "precond_repair" not in D.d1_overlay({}, MODEL, env("none"))["planner"].get("options", {})


def test_replan_block_alone_brings_no_near_data_and_all_has_it_through_release_near():
    rb = D.d1_overlay({}, MODEL, env(",".join(D2 + ("replan_block",))))["planner"]["options"]
    assert rb["precond_repair"] == D.d1_overlay({}, MODEL, env("d2"))["planner"]["options"]["precond_repair"]     # the confound of first plans is gone
    allv = D.selected_layers(env("all"))
    assert allv.index("release_near") == allv.index("replan_block") + 1
    need = D.d1_overlay({}, MODEL, env("all"))["planner"]["options"]["precond_repair"]["needs"]
    assert need["rules"]["Place"]["near"] is True and "release_near" in need["source"]


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
    assert set(ov["cond_extract"]) == {"prompt", "q_unclear", "clauses", "assumed"} and "prompt" not in ov["cond_goal"]
    assert ov["cond_extract"]["assumed"] is True and ov["cond_goal"]["assumed"] is True       # robot_agent uses an unlabelled text of these options as none
    assert ov["cond_extract"]["clauses"]["ko"]["assumed"] is True and "{request}" in ov["cond_extract"]["prompt"] and "{goals}" in ov["cond_extract"]["prompt"]
    assert D.d1_overlay({}, MODEL, env("d2"))["planner"]["options"].keys() >= {"lang_words"} and "cond_extract" not in D.d1_overlay({}, MODEL, env("d2"))["planner"]["options"]


def test_the_overlay_note_names_each_layer_with_the_label_of_its_data_and_none_is_d1_of_d2():
    note = D.d1_overlay({}, MODEL, env(",".join(D2 + ("cond_extract", "recipient_keep"))))["note"]
    assert "D2 layers on" not in note and "data from the mock robot manifest" not in note       # no blanket claim for all layers
    assert "precond_repair (sourced: mock robot manifest" in note and "hw_wait (assumed)" in note and "goal_words (no overlay data)" in note
    assert "cond_extract (assumed)" in note and "recipient_keep (no overlay data)" in note
    none = D.d1_overlay({}, MODEL, env("none"))
    assert none["note"] == "; " + D.D1_DATA["note"] and "options" not in none["planner"] and digest(env("d2")) == D2_HASH


# made-up Korean sentences (no task text): conditionals the D2 clause misses, request forms, plain "or" and nouns that end like a conditional
KO_IF = ("상자 안에 공이 보이면 꺼내 줘", "문이 열리면 알려 줘", "불이 켜지면 꺼 줘", "빗이 서랍에 남았으면 버려", "손님이 오시면 차를 드려",
         "연필을 찾으면 책상에 둬", "그게 빗이면 서랍에 넣어", "손이 더러우면 씻어", "화분 흙이 마르면 물 줘")
KO_REQUEST = ("공을 상자에 넣어 주시면 돼요", "책을 선반에 올려 주시면 좋겠어", "창문을 닫아 주시면 감사하겠습니다", "공을 꺼내 주시면 고맙겠어")
KO_PLAIN = ("빨간 공 가져올까요, 아니면 파란 공?", "책 아니면 공 줘", "공이 아니라면 뭐야?", "화면 켜 줘", "상자 정면에 둬", "가면 벗어 둬", "공을 상자에 넣어 줘")


def test_cond_extract_korean_words_are_the_general_conditional_ending_not_or_nor_a_request():
    import re
    more, d2 = re.compile(D.KO_COND_MORE), re.compile(D.KO_CONDITION)
    for text in KO_IF:
        assert more.search(text), text
    assert not any(d2.search(t) for t in KO_IF[:3])                                   # what the D2 clause did not read
    for text in KO_REQUEST + KO_PLAIN:
        assert not more.search(text) and not d2.search(text), text


def test_cond_extract_with_the_d1_korean_data_calls_the_model_only_for_a_real_conditional_one_call():
    import pytest
    pytest.importorskip("robot_agent")
    from types import SimpleNamespace as NS
    from robot_agent.core.options.config import resolve
    from robot_agent.options.cond_extract import SPEC, CondExtract
    planner = D.d1_overlay({}, MODEL, env(",".join(D2 + ("cond_extract",))))["planner"]
    for text in KO_IF + KO_REQUEST + KO_PLAIN:
        calls = []
        svc = NS(ask_model=lambda run, t, schema: calls.append(t) or {"conditional": False}, ask=lambda run, q: "", cancelled=lambda run: None,
                 lab=lambda *a, **k: None, ground_place=lambda run, t: None, goal_phrase=lambda g, p: g["object"], request_english=lambda run: "")
        run = NS(task=text, lang="ko", goals=[{"type": "on", "object": "zork", "from": "", "to": "crate"}], places=NS(), filtered=[])
        gen = CondExtract(resolve(SPEC, {"cond_extract": "1"}, {}, planner), svc).on_goals(run)
        list(gen) if gen is not None else None
        assert len(calls) == (1 if text in KO_IF else 0), text


def test_hw_tries_alone_on_top_of_d2_adds_only_the_more_tries_key_and_is_last_in_all():
    on = ",".join(D2 + ("hw_tries",))
    assert D.selected_layers(env(on)) == D2 + ("hw_tries",) and D.selected_layers(env("d3"))[-1] == "hw_tries"
    assert D.layer_options(env(on)) == {**D.layer_options(env("d2")), "hw_more_tries": "1"} and "hw_more_tries" not in D.layer_options(env("d2"))
    ov, ov2 = D.d1_overlay({}, MODEL, env(on)), D.d1_overlay({}, MODEL, env("d2"))
    ov.pop("note", None), ov2.pop("note", None)
    assert ov == ov2 and digest(env("d2")) == D2_HASH
