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
        assert p["action_roles"] == {**b["action_roles"], "find": "Find"}
        assert {k: v for k, v in p["recovery"].items() if k != "reopen_on_miss"} == b["recovery"]      # wait, blocked_putin, return_tries stay
        assert "end_state" not in b and d1.manifest_overlay["assumed"] is True
        assert "reopen_on_miss" not in b["recovery"] and "find" not in b["action_roles"]               # the base overlay object is not mutated


def test_every_option_exists_in_robot_agent_and_is_off_by_default_there():
    from robot_agent.core.options import REGISTRY
    specs = {s.name: s for s in REGISTRY.specs()}
    for name in D.D1_CLASSES:
        assert name in specs and specs[name].key(specs[name].enabled).default is False
