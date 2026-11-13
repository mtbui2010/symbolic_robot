"""Home domain parity: through the domain protocol, a scripted skill-call sequence gives results identical to calling the
package's make_episode directly (same houses, profiles and seeds)."""
import pytest

from symbolic_robot import registry
from symbolic_robot.backend import LiveBackend

import symbolic_robot.domains.home as homeloop
HOUSES = ["senior_flat", "studio_flat", "couple_flat", "family_house", "korean_apt_59"]
PROFILES = ["ideal", "real", "stress"]


def script(world):
    """A sequence made from the world itself: fetch two objects to other places, look, ask, say, open and close things, dock."""
    objs = sorted(world.objects.values(), key=lambda o: o.id)[:3]
    places = [p.id for p in world.places.values() if p.kind not in ("floor", "dock")]
    plan = [("look", {}), ("say", {"text": "hello", "lang": "en"}), ("pose", {})]
    for i, o in enumerate(objs):
        plan += [("move", {"target": o.at}), ("find", {"obj": o.id}), ("open", {"container": o.at}), ("pick", {"obj": o.id}),
                 ("grasp_check", {}), ("move", {"target": places[(i * 2 + 1) % len(places)]}),
                 ("place", {"target": places[(i * 2 + 1) % len(places)]}), ("close", {"container": o.at}), ("look", {})]
    plan += [("ask", {"question": "Where is the mug?", "lang": "en"}), ("wait", {"seconds": 2}), ("dock", {}), ("nosuchskill", {})]
    return plan


def run(robot, plan):
    out = []
    for skill, args in plan:
        r = robot.call(skill, **args)
        out.append((skill, r.to_json()))
    return out


@pytest.mark.parametrize("house", HOUSES)
@pytest.mark.parametrize("profile", PROFILES)
def test_scripted_calls_identical_to_the_package(house, profile):
    seed = 11
    direct = homeloop.make_episode(house, 0, profile, seed, lang="en", key="live")
    dom = registry.get("home")
    via = dom.make_episode(house, profile, seed)
    plan = script(direct.world)
    a, b = run(direct.robot, plan), run(dom.robot(via), plan)
    assert a == b and len(a) == len(plan)
    assert direct.clock.t == dom.clock_t(via) and {k: o.at for k, o in direct.world.objects.items()} == {k: o.at for k, o in via.world.objects.items()}


def test_live_backend_over_the_wrapper_is_the_same_robot_and_a_realistic_message_option():
    dom = registry.get("home")
    direct = homeloop.make_episode("senior_flat", 0, "real", 3, lang="en", key="live")
    lv = LiveBackend(dom, "senior_flat", "real", 3)
    plan = script(direct.world)
    assert [(s, direct.robot.call(s, **a).to_json()) for s, a in plan] == [(s, lv.call(s, **a).to_json()) for s, a in plan]
    assert dom.live_opts == {"realistic_msgs": True}
    raw = dom.make_episode("senior_flat", "ideal", 0)
    quiet = dom.make_episode("senior_flat", "ideal", 0, realistic_msgs=True)
    a, b = dom.robot(raw).call("find", obj="no_such_thing_xyz"), dom.robot(quiet).call("find", obj="no_such_thing_xyz")
    assert a.code == b.code and a.msg.replace(": no such object", "") == b.msg and ": no such object" not in b.msg


def test_wrapper_ops():
    dom = registry.get("home")
    lv = LiveBackend(dom, "senior_flat", "ideal", 0)
    places = [p for p in lv.episode.world.house.places.values() if p.kind == "surface"]
    assert places
    from symbolic_robot.simcommand import SimCommands
    c = SimCommands(lv)
    oid = next(iter(lv.world_view()["objects"]))
    target = next(p.id for p in places if p.id != lv.world_view()["objects"][oid]["at"])
    assert c.handle({"cmd": "move_object", "body": oid, "place": target})["ok"] and lv.world_view()["objects"][oid]["at"] == target
    sp = c.handle({"cmd": "spawn", "cls": "banana", "place": target})
    assert sp["ok"] and sp["id"] in lv.world_view()["objects"]
    assert not c.handle({"cmd": "spawn", "cls": "banana", "place": "nowhere"})["ok"]
    assert dom.env(lv.episode) and dom.pack == "symbolic_robot.domains.home"
