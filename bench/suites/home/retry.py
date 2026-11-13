"""Retry INSIDE a skill (bench side; the simulator and the judge are not touched).

A person who arrives somewhere and looks again twice is still doing one thing. The planner variants with ``skill_attempts`` > 1
(``robot_agent:sage_s8n_d1``, ``robot_agent:sage_s8n_ft_d1``) get the same: the planner issues ONE call and sees ONE result, the last
attempt's. It is different from a second look, which is a planner decision (going back to a place after a detour) and is not touched here.

* Which skills: the ones that only read, look or move (``SAFE_SKILLS``). Never pick, place, put_in, handover, say, announce, ask, wait
  (pick / place / put_in have their own ``num_trials``; the others change the world or the person, or cost nothing to repeat for nothing).
* Which codes: every failure except ``NEVER_RETRY_CODES`` (estop, cancelled), ``absent`` included (a look that finds nothing is looked at again).
* Not counted: the planner's call budget (``max_calls``), ``len(env.calls)``, the number of calls reported and the call log all see one call.
  Counted: the simulated time of every attempt (the clock moves in the simulator, the call's ``duration_s`` is the sum), and no attempt
  starts when the simulated-time budget is already used up.
* Recorded: ``truth["attempts"]`` and, when there was a repeat, ``truth["attempt_codes"]`` of the call (copied into the call log of the
  episode), and the variant's run config (``skill_retry``).

Implemented as a wrapper of the episode's robot, installed by the planner adapter (``install``): the episode environment and the robot
see it as the robot, so nothing in them changes, and a variant with one attempt (the default) is not wrapped at all.
"""
from __future__ import annotations

import dataclasses

from symbolic_robot.domains.home.rng import r6

SAFE_SKILLS = ("move", "find", "look", "open", "close", "vlm_check", "dock", "grasp_check", "pose")
NEVER_RETRY_CODES = ("estop", "cancelled")


def code_of(res) -> str:
    c = getattr(res, "code", None)
    return "ok" if getattr(res, "ok", False) else str(getattr(c, "value", c))


def describe(attempts: int) -> dict:
    """The variant's retry rule as recorded in its run config."""
    return {"where": "inside the skill: the planner issues one call and sees the last attempt",
            "attempts_total": int(attempts), "skills": list(SAFE_SKILLS),
            "codes": "every failure code except " + ", ".join(NEVER_RETRY_CODES),
            "counted_in_call_budget": False, "sim_time_counted": True, "stops_when_sim_time_budget_used": True}


class RetryingRobot:
    """The episode's robot, repeating a safe skill that failed (``attempts`` in total, the first one included)."""

    def __init__(self, robot, attempts: int, max_sim_time_s: float):
        self._robot = robot
        self.attempts = max(1, int(attempts))
        self.max_sim_time_s = float(max_sim_time_s)
        self.trace: list = []                     # one record per call the planner made (the inner robot's own trace has one per attempt)

    def __getattr__(self, name):                  # everything else (observe, health, believed, clock, pop_events, ...) is the robot's
        return getattr(self._robot, name)

    def _again(self, skill: str, res, n_done: int) -> bool:
        return (n_done < self.attempts and skill in SAFE_SKILLS and not getattr(res, "ok", True)
                and code_of(res) not in NEVER_RETRY_CODES and float(self._robot.clock.t) < self.max_sim_time_s)

    def call(self, skill: str, /, **args):
        res = self._robot.call(skill, **args)
        first = self._robot.trace[-1]
        results, recs = [res], [first]
        while self._again(skill, results[-1], len(results)):
            results.append(self._robot.call(skill, **args))
            recs.append(self._robot.trace[-1])
        n = len(results)
        res = results[-1]
        truth = {**(res.truth or {}), "attempts": n}
        if n > 1:
            truth["attempt_codes"] = [code_of(r) for r in results]
        rec = {**recs[-1], "t": first["t"], "dur": r6(sum(float(x["dur"]) for x in recs)), "attempts": n}
        self.trace.append(rec)
        total = sum(float(r.duration_s) for r in results)
        return dataclasses.replace(res, duration_s=total if n > 1 else res.duration_s, truth=truth)


def install(env, attempts: int) -> None:
    """Wrap the episode's robot when the variant repeats safe skills (``attempts`` > 1); otherwise leave everything as it is."""
    if int(attempts) > 1:
        env.robot = RetryingRobot(env.robot, attempts, env.budgets.max_sim_time_s)
