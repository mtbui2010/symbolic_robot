"""D1 planners translate with their own reader (the pack's 30B translator is not available on this machine); other planners keep the pack's."""
from bench.suites.home.planners import robot_agent_adapter as A
import importlib

from bench.suites.home.planners import REGISTRY


def _cls(name):
    mod, cls = REGISTRY[name][:2]
    return getattr(importlib.import_module(f"bench.suites.home.planners.{mod}"), cls)


def _tm(name):
    return _cls(name).run_config()["translate_model"]


def test_d1_planners_share_reader_and_translator():
    assert _tm("robot_agent:sage_s8n_d1") == "qwen3-vl:8b-instruct"
    ft = _cls("robot_agent:sage_s8n_ft_d1")
    assert _tm("robot_agent:sage_s8n_ft_d1") == ft.loop_options["understand_model"]


def test_other_planners_keep_the_pack_translator():
    base = A.manifest_planner().get("translate_model")
    assert _tm("robot_agent:sage_s8n") == base
    assert _tm("robot_agent:sage_s8n_ft") == base
