"""D3 L9: an option's pack data in a variant's manifest overlay reaches the option in a loop-level run (robot_agent ``refresh_options``).

The class: robot_agent resolves its option keys when the loop is built and the adapter merges the overlay afterwards, so an option whose data is
only in the overlay was on and silently did nothing (``cond_extract`` with no prompt: no extraction call, no lab flag in any D3 run).
Synthetic fixture tasks (one with a made-up condition sentence), the fake LLM; skipped when robot_agent is not importable."""
import copy
import os

import pytest

pytest.importorskip("robot_agent")

from fixtures import fixture_tasks  # noqa: E402
from bench.suites.home.planners import d1_options as D  # noqa: E402
from bench.suites.home.planners import robot_agent_adapter as A  # noqa: E402
from bench.suites.home.runner import run_episode  # noqa: E402

TASKS = {t["id"]: t for t in fixture_tasks()}
D1 = "robot_agent:sage_s8n_ft_d1"
needs_l9 = pytest.mark.skipif("cond_extract" not in A.SageS8nFtD1Planner.loop_options, reason="layer cond_extract not selected (SYMBOLIC_D1_LAYERS)")


def _capture(monkeypatch):
    got = []
    orig = A._RobotAgentPlanner._make_loop

    def make(self, agent, tmp, fake):
        loop = orig(self, agent, tmp, fake)
        got.append(loop)
        return loop
    monkeypatch.setattr(A._RobotAgentPlanner, "_make_loop", make)
    return got


def _conditional():
    """A fixture task whose English words carry a condition (made-up sentence over the fixture's own objects)."""
    t = copy.deepcopy(TASKS["fx-feas-010"])
    t["text"] = {**t["text"], "en": "If the blue mug is not on the kitchen sink, please put the blue mug on the kitchen sink."}
    return t


def _flags(ep, flag):
    return [x for x in ep.get("lab_events") or [] if x.get("flag") == flag]


@needs_l9
def test_d1_cond_extract_fires_in_a_loop_run_with_the_d1_pack_data_one_call(monkeypatch):
    got = _capture(monkeypatch)
    ep = run_episode(_conditional(), D1, "ideal", 0, "en", "fake")
    cfg = got[0].options.configs
    assert cfg["cond_extract"]["prompt"] == D.COND_PROMPT and cfg["cond_extract"]["q_unclear"]          # the overlay's data, seen through the keys
    assert cfg["cond_goal"]["q_where"] and cfg["cond_goal"]["q_unsure"] and not cfg["cond_goal"]["prompt"]   # cond_goal without the reader prompt key
    assert len(_flags(ep, "cond_extract")) == 1                                                       # the option fired once


@needs_l9
def test_d1_cond_extract_no_condition_word_no_extraction_no_keyword(monkeypatch):
    got = _capture(monkeypatch)
    ep = run_episode(TASKS["fx-feas-010"], D1, "ideal", 0, "en", "fake")
    assert got[0].options.configs["cond_extract"]["prompt"] == D.COND_PROMPT and _flags(ep, "cond_extract") == []


def test_a_variant_whose_overlay_has_no_option_data_resolves_as_before_off(monkeypatch):
    """The refresh changes nothing for a variant that declares no option data: its keys equal the keys of the pack's own manifest."""
    from robot_agent.core.options import REGISTRY
    from robot_agent.core.options.config import resolve
    got = _capture(monkeypatch)
    run_episode(TASKS["fx-feas-000"], "robot_agent:sage_ei_wait", "ideal", 0, "en", "fake")
    assert A.SageEiWaitPlanner.manifest_overlay                                                   # it has an overlay, so the adapter refreshed
    base = {s.name: dict(resolve(s, dict(A.SageEiWaitPlanner.loop_options), os.environ, A.manifest_planner())) for s in REGISTRY.specs()}
    assert {n: dict(c) for n, c in got[0].options.configs.items()} == base


def test_the_d1_overlay_without_option_data_leaves_every_option_key_empty_empty():
    """No option data declared = nothing to see: the D1 overlay of the ``none`` switch names no option."""
    ov = D.d1_overlay({}, "a-made-up-reader", environ={D.LAYERS_ENV: "none"})
    assert "options" not in ov["planner"]
