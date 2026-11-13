"""D1 retry, inside the skill: the planner issues ONE call and sees ONE result; the repeats cost simulated time but no call budget.

(Before 2026-11-13 the proxy repeated by calling env.call again: each repeat used a call of the budget, was a call of the log and the
count of reported calls, and `absent` was never repeated. A second look, going back to a place after a detour, is the planner's business
and is not changed.)"""
import pytest

from fixtures import feasible_tasks
from bench.suites.home import retry
from bench.suites.home.env import Budgets, EpisodeEnv
from bench.suites.home.planners.robot_agent_adapter import RobotProxy, SageS8nD1Planner, SageS8nFtD1Planner, SageS8nFtPlanner, SageS8nPlanner
from symbolic_robot.domains.home.types import FailureCode, SkillResult

F = FailureCode
RETRYABLE_CODES = [c for c in F if c.value not in retry.NEVER_RETRY_CODES]


class StubRobot:
    """Scripted outcomes (code or None, seconds) for the episode's robot; moves the episode's simulated clock like the real one."""

    def __init__(self, env, script):
        self.clock, self.script, self.trace, self.seen = env.ep.clock, list(script), [], []

    def call(self, skill, /, **args):
        code, dur = self.script.pop(0)
        t0 = self.clock.t
        self.clock.advance(dur)
        self.seen.append(skill)
        self.trace.append({"k": len(self.seen) - 1, "skill": skill, "args": dict(args), "t": t0, "dur": dur, "code": code.value if code else None})
        return SkillResult(ok=code is None, code=code, msg="", data={}, duration_s=dur, injected=code is not None, truth={"event": None})

    def pop_events(self):
        return []

    def observe(self):
        return {}


def _env(script, attempts=2, **budgets):
    env = EpisodeEnv(feasible_tasks(1)[0], "ideal", 0, "en", budgets=Budgets(**budgets))
    stub = StubRobot(env, script)
    env.robot = retry.RetryingRobot(stub, attempts, env.budgets.max_sim_time_s)
    return env, stub


def test_default_is_one_call_and_the_robot_is_not_wrapped():
    env = EpisodeEnv(feasible_tasks(1)[0], "ideal", 0, "en")
    robot = env.robot
    retry.install(env, 1)
    assert env.robot is robot
    assert not hasattr(RobotProxy, "RETRY_SKILLS") and not hasattr(RobotProxy(env), "retries")        # the proxy is one call, one result
    assert env.robot is robot                                    # a proxy with the default attempts wraps nothing
    RobotProxy(env, attempts=2)                                  # what the D1 planners do
    assert isinstance(env.robot, retry.RetryingRobot) and env.robot.attempts == 2


def test_find_absent_is_retried_and_the_planner_sees_one_call_with_the_final_result():
    env, stub = _env([(F.ABSENT, 4.0), (None, 5.0)])
    r = env.call("find", obj="mug_1")
    assert r["ok"] is True and stub.seen == ["find", "find"]
    assert len(env.calls) == 1 and env.n_calls == 1 and len(env._hist) == 1 and env.last["ok"] is True
    assert env.calls[0]["ok"] is True and env.calls[0]["code"] is None


def test_a_retry_does_not_use_the_call_budget():
    env, stub = _env([(F.ABSENT, 1.0), (None, 1.0), (None, 1.0)], max_calls=2)
    assert env.call("find", obj="mug_1")["ok"]                 # two attempts, one call
    assert env.observe().calls_left == 1
    assert env.call("look")["ok"] and env.observe().calls_left == 0
    assert stub.seen == ["find", "find", "look"] and len(env.calls) == 2
    r = env.call("look")
    assert r["code"] == "timeout" and r["msg"] == "episode budget exhausted" and env.over


def test_every_attempt_costs_simulated_time_and_the_call_reports_the_sum():
    env, stub = _env([(F.HW_FAULT, 3.0), (F.TIMEOUT, 7.0)], attempts=2)
    t0 = env.ep.clock.t
    r = env.call("move", target="kitchen")
    assert not r["ok"] and r["code"] == "timeout"                      # the last attempt's result
    assert env.ep.clock.t == pytest.approx(t0 + 10.0) and r["duration_s"] == pytest.approx(10.0)
    c = env.calls[0]
    assert c["dur"] == pytest.approx(10.0) and c["t"] == pytest.approx(t0) and c["code"] == "timeout"


def test_attempts_are_recorded_in_the_truth_and_the_call_log():
    env, _ = _env([(F.ABSENT, 1.0), (F.BLOCKED, 1.0), (None, 1.0)], attempts=3)
    env.call("find", obj="mug_1")
    assert env.last_result.truth["attempts"] == 3 and env.last_result.truth["attempt_codes"] == ["absent", "blocked", "ok"]
    assert env.calls[0]["attempts"] == 3 and env.calls[0]["attempt_codes"] == ["absent", "blocked", "ok"]
    env.robot._robot.script.append((None, 1.0))
    env.call("look")
    assert env.calls[1]["attempts"] == 1 and "attempt_codes" not in env.calls[1]
    pub = env.last                                                      # what the planner sees has no truth
    assert "truth" not in pub and "attempts" not in pub


def test_attempts_is_a_total_that_includes_the_first_call():
    env, stub = _env([(F.HW_FAULT, 1.0)] * 5, attempts=2)
    assert not env.call("move", target="a")["ok"] and len(stub.seen) == 2
    env, stub = _env([(F.HW_FAULT, 1.0)] * 5, attempts=3)
    assert not env.call("move", target="a")["ok"] and len(stub.seen) == 3


@pytest.mark.parametrize("skill", retry.SAFE_SKILLS)
@pytest.mark.parametrize("code", RETRYABLE_CODES)
def test_every_safe_skill_is_retried_on_every_code_but_estop_and_cancelled(skill, code):
    env, stub = _env([(code, 1.0), (None, 1.0)])
    assert env.call(skill)["ok"] and stub.seen == [skill, skill]


@pytest.mark.parametrize("skill", ["pick", "place", "put_in", "handover", "say", "announce", "ask", "wait"])
def test_unsafe_skills_are_never_repeated(skill):
    for code in (F.HW_FAULT, F.TIMEOUT, F.ABSENT, F.BLOCKED):
        env, stub = _env([(code, 1.0), (None, 1.0)])
        assert not env.call(skill)["ok"] and stub.seen == [skill]


@pytest.mark.parametrize("skill", retry.SAFE_SKILLS)
@pytest.mark.parametrize("code", [F.ESTOP, F.CANCELLED])
def test_estop_and_cancelled_are_final(skill, code):
    env, stub = _env([(code, 1.0), (None, 1.0)])
    assert not env.call(skill)["ok"] and stub.seen == [skill]


def test_no_repeat_when_the_time_budget_is_used_up():
    env, stub = _env([(F.HW_FAULT, 60.0), (None, 1.0)], max_sim_time_s=50.0)
    r = env.call("move", target="a")
    assert not r["ok"] and stub.seen == ["move"] and env.over                  # the first attempt used up the time
    env, stub = _env([(F.HW_FAULT, 10.0), (None, 1.0)], max_sim_time_s=50.0)
    assert env.call("move", target="a")["ok"] and stub.seen == ["move", "move"]


def test_proxy_hands_robot_agent_the_last_result_of_one_call():
    env, stub = _env([(F.ABSENT, 2.0), (None, 3.0)])
    res = RobotProxy(env).call("find", obj="mug_1")
    assert res.ok and res.duration_s == pytest.approx(5.0) and res.truth["attempts"] == 2
    assert len(env.calls) == 1 and stub.seen == ["find", "find"]


def test_real_robot_absent_find_is_looked_at_again_with_its_time_counted():
    env = EpisodeEnv(feasible_tasks(1)[0], "ideal", 0, "en")
    retry.install(env, 3)
    t0 = env.ep.clock.t
    r = env.call("find", obj="no_such_object_xyz")
    inner = env.robot._robot.trace
    assert r["code"] == "absent" and len(inner) == 3 and len(env.calls) == 1
    assert env.calls[0]["attempts"] == 3 and env.calls[0]["attempt_codes"] == ["absent"] * 3
    assert env.ep.clock.t == pytest.approx(t0 + sum(x["dur"] for x in inner)) and env.ep.clock.t > t0


def test_variant_setup_is_declared_and_base_unchanged():
    assert SageS8nD1Planner.skill_attempts == 2 and SageS8nFtD1Planner.skill_attempts == 2
    o = SageS8nD1Planner.loop_options
    assert (o["search_legs"], o["search_total"], o["detector_miss_rate"]) == (1, 6, 0)
    assert not hasattr(SageS8nPlanner, "skill_attempts") and "search_total" not in SageS8nPlanner.loop_options
    rc = SageS8nD1Planner.run_config()
    assert rc["skill_attempts"] == 2 and rc["skill_retry"]["attempts_total"] == 2 and rc["skill_retry"]["counted_in_call_budget"] is False
    assert set(rc["skill_retry"]["skills"]) == set(retry.SAFE_SKILLS)
    assert "skill_retry" not in SageS8nPlanner.run_config() and "skill_attempts" not in SageS8nPlanner.run_config()


def test_d1_confirms_a_sighting_that_followed_a_miss_base_unchanged():
    for d1, base in ((SageS8nD1Planner, SageS8nPlanner), (SageS8nFtD1Planner, SageS8nFtPlanner)):
        assert d1.loop_options["confirm_look"] == "1" and "confirm_look" not in base.loop_options
        assert d1.run_config()["loop_options"]["confirm_look"] == "1"        # recorded in the run config
