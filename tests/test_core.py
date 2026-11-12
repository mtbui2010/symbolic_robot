import math

import pytest

from symbolic_robot import registry
from symbolic_robot.backend import LiveBackend
from symbolic_robot.clock import SimClock
from symbolic_robot.result import Result
from symbolic_robot.rng import CallDraws, Rng, derive_seed
from symbolic_robot.simcommand import SimCommands

from toy import Toy


# ---- rng
def test_rng_is_deterministic_and_keyed_not_ordered():
    a, b = Rng(5), Rng(5)
    a.uniform("x"), a.uniform("y")
    assert b.uniform("y") == Rng(5).uniform("y")           # another key does not shift this one
    assert Rng(5).uniform("k") != Rng(6).uniform("k")
    r = Rng(1)
    assert r.uniform("k") != r.uniform("k")                 # the n-th use of a key is a new draw
    assert Rng(1).uniform("k") == Rng(1).uniform("k")


def test_rng_uniform_is_uniform():
    r = Rng(3)
    xs = [r.uniform("u") for _ in range(4000)]
    assert abs(sum(xs) / len(xs) - 0.5) < 4 * math.sqrt(1 / 12 / len(xs))


def test_call_draws_vector_is_stable_per_call():
    d1, d2 = CallDraws(7), CallDraws(7)
    d1.begin("move", {"to": "x"})
    a = d1.begin("pick", {"o": 1})
    b = d2.begin("pick", {"o": 1})
    assert len(a.u) == 16 and all(0 <= x < 1 for x in a.u)
    assert a.n == 1 and b.n == 1 and a.u == b.u                 # another call before it does not matter
    assert d1.begin("pick", {"o": 1}).u != a.u                  # the 2nd call with the same arguments differs
    assert a.attempt(1) != a.u and a.attempt(1) == b.attempt(1)
    assert derive_seed(1, "a") == derive_seed(1, "a") != derive_seed(1, "b")


# ---- clock
def test_clock_moves_only_by_reported_durations():
    c = SimClock()
    assert c.t == 0.0 and c.advance(5.0) == 5.0 and c.advance(2.5) == 7.5 and c.t == 7.5


# ---- result
def test_result_legacy_shape():
    assert Result(True, "ok", data={"x": 1}).to_legacy() == {"isdone": True, "msg": "ok", "x": 1}
    assert Result(False, "no", "absent").to_legacy() == {"isdone": False, "msg": "no", "code": "absent"}


# ---- registry and a domain written only against the protocol
def test_registry_lists_builtins_and_takes_a_plugin():
    assert {"factory", "home"} <= set(registry.names())
    with pytest.raises(KeyError):
        registry.get("nope")
    registry.register("toy", Toy)
    assert registry.get("toy").worlds() == ["small", "big"]
    assert "room" in registry.world_labels()


def test_live_backend_and_sim_commands_work_for_a_new_domain():
    live = LiveBackend(Toy(), "small", "ideal", 0)
    assert live.call("go", to="b").ok and live.snapshot()["x"] == 3.0
    assert live.log[-1]["skill"] == "go" and live.world_view()["log"][-1]["ok"] is True
    assert live.world_view()["profile"] == "ideal" and live.t == 2.0              # attribute of the inner robot
    cmds = SimCommands(live)
    st = cmds.handle({"cmd": "state"})
    assert st["ok"] and st["objects"][0]["body"] == "cup" and st["catalog"]["objects"] == ["cup"]
    assert cmds.handle({"cmd": "move_object", "body": "cup", "place": "b"})["ok"]
    assert live.world_view()["objects"]["cup"]["at"] == "b"
    assert not cmds.handle({"cmd": "move_object", "body": "cup"})["ok"]                     # no place given
    assert not cmds.handle({"cmd": "spawn", "cls": "x", "place": "a"})["ok"]       # the toy does not support spawn: says so
    assert not cmds.handle({"cmd": "nope"})["ok"]


def test_live_backend_reset_and_world_change_callback():
    live = LiveBackend(Toy(), "small", "real", 3)
    seen = []
    live.on_new_world = lambda lv: seen.append(lv.kw["world"])
    live.call("go", to="b")
    live.reset(seed=4)
    assert live.kw["seed"] == 4 and live.log == [] and live.snapshot()["x"] == 0.0 and seen == []
    live.reset(world="big")
    assert seen == ["big"]
