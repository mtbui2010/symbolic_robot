"""D4: the D1 layer switch with the ``d3`` alias and the D4 layers (``HOMELOOP_D1_LAYERS``). Pure data: no run, no model."""
import hashlib
import json

from bench.suites.home.planners import d1_options as D

D3 = ("precond_repair", "gate_prune", "dedupe_keep_end", "goal_words", "ask_focus", "entity_cover", "hazard", "hw_wait", "search_budget", "lang_words",
      "cond_extract", "recipient_keep", "plan_complete", "ask_agree", "name_recover", "replan_block", "release_near", "hw_tries")
D3_HASH = "f751d73417c679250af675869633f8f1278ab7fcfe9127c3c249f53e294beab3"     # the 18 D3 layers: on, loop options, overlay without its note
D2_HASH = "64b278b5beef2493d675eac77ebd6d10b799e2ce2e307014e56b3f207e356942"
BUILD = ("plan_release", "effect_check", "repair_sync", "goal_ledger", "answer_align", "question_cap", "partial_end", "safety_profile", "fault_ladder",
         "close_opened", "else_ask")                                              # the D4 build order (layers not built yet are not in LAYERS)
MODEL = "hl-understand-p3-s700"


def env(v):
    return {D.LAYERS_ENV: v}


def digest(e):
    ov = D.d1_overlay({}, MODEL, e)
    ov.pop("note", None)
    blob = json.dumps({"on": D.selected_layers(e), "opts": D.layer_options(e), "overlay": ov}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()


def test_d3_alias_is_the_18_d3_layers_and_equals_the_d3_hash_d2_keeps_its_hash():
    assert D.selected_layers(env("d3")) == D3 == D.D3_LAYERS and D.selected_layers(env(" D3 ")) == D3
    assert digest(env("d3")) == D3_HASH and digest(env("d2")) == D2_HASH


def test_all_is_d3_then_the_d4_layers_in_build_order_and_the_default():
    allv = D.selected_layers(env("all"))
    assert allv[:18] == D3 and allv[18:] == D.D4_LAYERS and D.D4_LAYERS == tuple(n for n in BUILD if n in D.D4_LAYERS)   # build order; layers are built in parallel worktrees
    assert set(D.D4_LAYERS) <= set(BUILD)
    assert D.selected_layers({}) == allv == D.ALL_LAYERS and set(allv) == set(D.LAYERS)
    assert "plan_release" in D.D4_LAYERS and D.layer_options(env("all"))["plan_release"] == "1"
    assert "plan_release" not in D.layer_options(env("d3")) and "plan_release" not in D.d1_overlay({}, MODEL, env("d3"))["planner"]["options"]


def test_none_selects_nothing():
    assert D.selected_layers(env("none")) == () and D.layer_options(env("none")) == {}


def test_plan_release_alone_on_top_of_d3_adds_its_option_and_its_labelled_data_only():
    on = env(",".join(D3 + ("plan_release",)))
    assert D.selected_layers(on) == D3 + ("plan_release",)
    assert D.layer_options(on) == {**D.layer_options(env("d3")), "plan_release": "1"}
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, env("d3"))
    need = ov["planner"]["options"].pop("plan_release")["needs"]
    assert need["assumed"] is True and need["rules"]["PutIn"] == {"achieves": "in"}
    assert ov["planner"]["action_roles"] == base["planner"]["action_roles"]          # its roles are those the d3 layers already declare
    ov.pop("note"), base.pop("note")
    assert ov == base and digest(env("d3")) == D3_HASH


def test_every_d4_layer_overlay_data_has_a_label():
    for n in D.D4_LAYERS:
        data = D.LAYERS[n][1]
        assert not data or D._labels(data), n
        assert n in D.layer_note(n)


def test_effect_check_alone_on_top_of_d3_adds_its_option_and_its_sourced_data_only():
    on = env(",".join(D3 + ("effect_check",)))
    assert D.selected_layers(on) == D3 + ("effect_check",)
    assert D.layer_options(on) == {**D.layer_options(env("d3")), "effect_check": "1"}
    assert "effect_check" not in D.layer_options(env("d3")) and D.layer_options(env("all"))["effect_check"] == "1"
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, env("d3"))
    data = ov["planner"]["options"].pop("effect_check")["effects"]
    assert data["source"].strip() and data["sensor"]["skill"] and data["releases"] and data["floor"]
    assert "effect_check" not in base["planner"]["options"]
    ov.pop("note"), base.pop("note")
    assert ov == base and digest(env("d3")) == D3_HASH


def test_repair_sync_alone_on_top_of_d3_adds_its_option_and_no_data():
    on = env(",".join(D3 + ("repair_sync",)))
    assert D.selected_layers(on) == D3 + ("repair_sync",)
    assert D.layer_options(on) == {**D.layer_options(env("d3")), "repair_sync": "1"}
    assert "repair_sync" not in D.layer_options(env("d3")) and D.layer_options(env("all"))["repair_sync"] == "1"
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, env("d3"))
    assert "repair_sync (no overlay data)" in ov["note"]
    ov.pop("note"), base.pop("note")
    assert ov == base and digest(env("d3")) == D3_HASH


def test_goal_ledger_alone_on_top_of_d3_adds_its_restore_no_data_named_and_retract_off():
    on = env(",".join(D3 + ("goal_ledger",)))
    assert D.selected_layers(on) == D3 + ("goal_ledger",)
    assert D.layer_options(on) == {**D.layer_options(env("d3")), "goal_ledger": "1"}
    assert "goal_ledger" not in D.layer_options(env("d3")) and D.layer_options(env("all"))["goal_ledger"] == "1"
    assert not any(k.startswith("goal_ledger_") or k.startswith("goal_ledger.") for k in D.layer_options(env("all")))   # named and retract stay off
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, env("d3"))
    assert "goal_ledger (no overlay data)" in ov["note"]
    ov.pop("note"), base.pop("note")
    assert ov == base and digest(env("d3")) == D3_HASH


def test_answer_align_alone_on_top_of_d3_turns_on_its_option_no_data_ask_agree_distinct_off():
    on = env(",".join(D3 + ("answer_align",)))
    assert D.selected_layers(on) == D3 + ("answer_align",)
    assert D.layer_options(on) == {**D.layer_options(env("d3")), "answer_align": "1"}
    assert "answer_align" not in D.layer_options(env("d3")) and D.layer_options(env("all"))["answer_align"] == "1"
    assert not any("distinct" in k or k.startswith("answer_align.") for k in D.layer_options(env("all")))   # reask and correction on with the option
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, env("d3"))
    assert "answer_align (no overlay data)" in ov["note"]
    ov.pop("note"), base.pop("note")
    assert ov == base and digest(env("d3")) == D3_HASH


def test_question_cap_alone_on_top_of_d3_adds_its_option_no_repeat_and_its_assumed_cap_only():
    on = env(",".join(D3 + ("question_cap",)))
    assert D.selected_layers(on) == D3 + ("question_cap",)
    assert D.layer_options(on) == {**D.layer_options(env("d3")), "question_cap": "1", "question_cap_no_repeat": "1"}
    assert "question_cap" not in D.layer_options(env("d3")) and D.layer_options(env("all"))["question_cap"] == "1"
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, env("d3"))
    assert ov["planner"]["options"].pop("question_cap") == {"max_questions": 3, "assumed": True}
    assert "question_cap" not in base["planner"]["options"] and "question_cap (assumed)" in ov["note"]
    ov.pop("note"), base.pop("note")
    assert ov == base and digest(env("d3")) == D3_HASH


def test_partial_end_alone_on_top_of_d3_adds_its_option_and_no_data():
    on = env(",".join(D3 + ("partial_end",)))
    assert D.selected_layers(on) == D3 + ("partial_end",)
    assert D.layer_options(on) == {**D.layer_options(env("d3")), "partial_end": "1"}
    assert "partial_end" not in D.layer_options(env("d3")) and D.layer_options(env("all"))["partial_end"] == "1"
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, env("d3"))
    assert "partial_end (no overlay data)" in ov["note"]
    ov.pop("note"), base.pop("note")
    assert ov == base and digest(env("d3")) == D3_HASH
