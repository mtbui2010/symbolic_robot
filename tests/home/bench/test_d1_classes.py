"""D1 turns on the failure-class options of robot_agent (all default off there) through ``loop_options`` and declares the pack data they read as a manifest
overlay (``planners/d1_options.py``); the base planners are unchanged, the existing D1 overlay parts (translator, recovery, action roles) survive the merge,
and the options exist in the installed robot_agent."""
from bench.suites.home.planners import d1_options as D
from bench.suites.home.planners.robot_agent_adapter import (SageS8nD1Planner, SageS8nFtD1Planner, SageS8nFtPlanner, SageS8nPlanner)

PAIRS = ((SageS8nD1Planner, SageS8nPlanner), (SageS8nFtD1Planner, SageS8nFtPlanner))


def test_d1_enables_the_class_options_the_bases_do_not():
    for d1, base in PAIRS:
        for k, v in D.D1_CLASSES.items():
            assert d1.loop_options[k] == v and k not in base.loop_options
        assert d1.run_config()["loop_options"]["end_state"] == "1"          # recorded in the run config


def test_the_overlay_merges_the_data_without_losing_the_base_parts():
    for d1, base in PAIRS:
        p, b = d1.manifest_overlay["planner"], base.manifest_overlay["planner"]
        assert p["end_state"] == {"places": ["dock"], "action": "Dock"} and p["recovery"]["reopen_on_miss"] == ["Close", "Open"]
        assert {k: v for k, v in p["action_roles"].items() if k != "pick"} == {**b["action_roles"], "find": "Find"}      # pick: the layer precond_repair
        assert {k: v for k, v in p["recovery"].items() if k != "reopen_on_miss"} == b["recovery"]      # wait, blocked_putin, return_tries stay
        assert "end_state" not in b and d1.manifest_overlay["assumed"] is True
        assert "reopen_on_miss" not in b["recovery"] and "find" not in b["action_roles"]               # the base overlay object is not mutated


def test_every_option_exists_in_robot_agent_and_is_off_by_default_there():
    from robot_agent.core.options import REGISTRY
    specs = {s.name: s for s in REGISTRY.specs()}
    for name in {**D.D1_CLASSES, **D.layer_options({})}:
        assert name in specs and specs[name].key(specs[name].enabled).default is False


# ---- round D2: the layer switch (HOMELOOP_D1_LAYERS) ----
D_LOOP_OPTIONS = {"search_per_object": "1", "place_find": "1", "reopen_on_miss": "1", "end_state": "1", "object_words": "1"}
BASE_OV = {"planner": {"action_roles": {"move": "MoveTo", "put_down": "Place"}, "recovery": {"wait": 3}}, "assumed": True, "note": "base"}


def env(v=None):
    return {} if v is None else {D.LAYERS_ENV: v}


def test_layer_switch_default_all_none_and_a_list():
    assert D.selected_layers(env()) == tuple(D.LAYERS) == D.selected_layers(env("all")) == D.selected_layers(env(" ALL "))
    assert D.selected_layers(env("none")) == ()
    assert D.selected_layers(env("precond_repair")) == ("precond_repair",)
    assert D.selected_layers(env("")) == tuple(D.LAYERS)                      # empty = the default
    try:
        D.selected_layers(env("precond_repair,no_such_layer"))
    except ValueError as e:
        assert "no_such_layer" in str(e)
    else:
        raise AssertionError("an unknown layer name must be refused")


def test_layers_none_is_the_d1_of_experiment_d_options_and_overlay():
    assert D.layer_options(env("none")) == {}
    out = D.d1_overlay(BASE_OV, "m", env("none"))
    assert out["planner"] == {**BASE_OV["planner"], "action_roles": {"move": "MoveTo", "put_down": "Place", "find": "Find"},
                              "recovery": {"wait": 3, "reopen_on_miss": ["Close", "Open"]}, "end_state": {"places": ["dock"], "action": "Dock"},
                              "translate_model": "m"}
    assert out["note"] == "base; " + D.D1_DATA["note"] and "D2" not in out["note"]
    assert D.D1_CLASSES_D == D_LOOP_OPTIONS


def test_precond_repair_layer_adds_its_option_and_its_pack_data_only_when_on():
    assert D.layer_options(env("precond_repair")) == {"precond_repair": "1"}
    on = D.d1_overlay(BASE_OV, "m", env("precond_repair"))
    off = D.d1_overlay(BASE_OV, "m", env("none"))
    needs = on["planner"]["options"]["precond_repair"]["needs"]
    assert needs["source"] and needs["rules"]["Handover"] == {"holding": True} and on["planner"]["action_roles"]["pick"] == "Pick"
    assert "options" not in off["planner"] and "pick" not in off["planner"]["action_roles"]
    assert "precond_repair" in on["note"] and BASE_OV["planner"] == {"action_roles": {"move": "MoveTo", "put_down": "Place"}, "recovery": {"wait": 3}}


def test_the_planner_classes_carry_the_layers_that_were_on_at_import_and_record_them():
    for d1, _base in PAIRS:
        for k, v in D.layer_options().items():
            assert d1.loop_options[k] == v and d1.run_config()["loop_options"][k] == v


def test_the_layer_pack_data_passes_the_manifest_contract():
    from robot_agent.contract.manifest import _planner
    errs = []
    _planner(D.d1_overlay(PAIRS[0][1].manifest_overlay, "m", env("all"))["planner"], errs)
    assert errs == []


def test_goal_words_layer_adds_its_option_and_no_pack_data():
    assert D.layer_options(env("goal_words")) == {"goal_words": "1"}
    assert D.d1_overlay(BASE_OV, "m", env("goal_words"))["planner"] == D.d1_overlay(BASE_OV, "m", env("none"))["planner"]      # no data
    both = D.layer_options(env("precond_repair,goal_words"))
    assert both == {"precond_repair": "1", "goal_words": "1"} and D.layer_options(env("none")) == {}
    assert "goal_words" in D.d1_overlay(BASE_OV, "m", env("goal_words"))["note"]


def test_ask_focus_layer_adds_its_option_and_no_pack_data():
    assert D.layer_options(env("ask_focus")) == {"ask_focus": "1"}
    assert D.d1_overlay(BASE_OV, "m", env("ask_focus"))["planner"] == D.d1_overlay(BASE_OV, "m", env("none"))["planner"]      # no data
    assert D.layer_options(env("none")) == {} and "ask_focus" in D.layer_options(env("all"))
    assert "ask_focus" in D.d1_overlay(BASE_OV, "m", env("ask_focus"))["note"]
