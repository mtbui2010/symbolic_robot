import math

import pytest

from symbolic_robot.domains.factory import make_episode
from symbolic_robot.domains.factory.configs.tasks import env_for
from symbolic_robot.domains.factory.tasks_gen import generate_tasks
from symbolic_robot.domains.factory.user import DONT_KNOW, SimUser
from symbolic_robot.domains.factory.world import list_floors, load_floor
from symbolic_robot.domains.factory.world import load_floor as lf
from symbolic_robot.rng import Rng


def run(robot, plan):
    return [robot.call(s, **a) for s, a in plan]


PLAN = [("move", {"target": "tool_wall@tool_crib"}), ("find", {"obj": "large wrench"}), ("pick", {"obj": "large wrench"}),
        ("move", {"target": "assembly_bench_1@assembly_a"}), ("place", {"target": "assembly_bench_1@assembly_a"})]


def test_floors_load_and_are_consistent():
    assert {"assembly_hall", "small_workshop"} <= set(list_floors())
    for name in ("assembly_hall", "small_workshop"):
        w = load_floor(name)
        assert w.dock in w.places and len(w.objects) >= 10
        for p in w.places.values():
            assert p.zone in w.zones
        assert len({o.label for o in w.objects.values()}) == len(w.objects)
    h = load_floor("assembly_hall")
    assert len(h.zones) >= 9 and len(h.places) >= 25 and len(h.objects) >= 20
    assert sum(1 for z in load_floor("small_workshop").zones) == 5


def test_ideal_run_is_exact_and_deterministic():
    a, b = make_episode(profile="ideal", seed=3).robot, make_episode(profile="ideal", seed=3).robot
    ra, rb = run(a, PLAN), run(b, PLAN)
    assert all(r.ok for r in ra)
    assert a.world.objects["wrench_l"].at == "assembly_bench_1@assembly_a"
    assert a.log == b.log
    d = math.dist(a.world.pos_of("charging_dock@receiving"), a.world.pos_of("tool_wall@tool_crib")) + math.dist(
        a.world.pos_of("tool_wall@tool_crib"), a.world.pos_of("assembly_bench_1@assembly_a"))
    assert a.total_distance() == pytest.approx(d, abs=0.01)


def test_real_profile_is_deterministic_by_seed_and_differs_across_seeds():
    def outcome(seed):
        r = make_episode(profile="real", seed=seed).robot
        run(r, PLAN)
        return [(e["skill"], e["ok"], e["code"]) for e in r.log]
    assert outcome(11) == outcome(11)
    assert len({tuple(outcome(s)) for s in range(60)}) > 1


def test_detector_miss_rate_is_near_the_profile():
    misses = n = 0
    for seed in range(400):
        r = make_episode(profile="real", seed=seed).robot
        r.call("move", target="tool_wall@tool_crib")
        res = r.call("find", obj="large wrench")
        if res.truth.get("find") in ("seen", "detector_miss"):
            n += 1
            misses += res.truth["find"] == "detector_miss"
    assert 0.05 < misses / n < 0.16


def test_all_fault_kinds_occur_and_ideal_has_none():
    seen = set()
    for seed in range(600):
        r = make_episode(profile="real", seed=seed).robot
        run(r, PLAN)
        seen |= {e["truth"].get("fault") or e["truth"].get("find") for e in r.log} - {None, "seen"}
        for _ in range(3):
            r.call("pick", obj="x")
    assert {"detector_miss", "slip", "hw_fault", "persistent_hw_fault", "dropped"} <= seen
    for seed in range(100):
        r = make_episode(profile="ideal", seed=seed).robot
        assert all(x.ok for x in run(r, PLAN))


def test_preconditions():
    r = make_episode(profile="ideal").robot
    assert r.call("pick", obj="large wrench").code == "absent"          # not at the tool wall yet
    assert r.call("place", target="tool_wall@tool_crib").code in ("blocked", "unreachable")   # nothing held
    r.call("move", target="tool_wall@tool_crib")
    assert r.call("find", obj="gasket").code == "absent"
    r.world.objects["wrench_s"].at = "tool_wall@tool_crib"          # both wrenches in view: the bare class name is ambiguous
    res = r.call("find", obj="wrench")
    assert res.code == "absent" and "which one" in res.msg
    r.call("pick", obj="large wrench")
    assert r.call("pick", obj="sd_phil").code in ("blocked", "absent")      # hand full
    r.call("move", target="tool_cabinet@tool_crib")
    assert r.call("put_in", container="tool_cabinet@tool_crib").code == "blocked"   # closed
    assert r.call("place", target="tool_cabinet@tool_crib").code == "blocked"        # a container takes put_in
    assert r.call("open", container="tool_cabinet@tool_crib").ok
    assert r.call("put_in", container="tool_cabinet@tool_crib").ok


def test_closed_container_hides_objects_and_locked_cabinet_stays_shut():
    r = make_episode(profile="ideal").robot
    r.call("move", target="toolbox@tool_crib")
    assert not r.call("find", obj="small wrench").ok
    assert r.call("open", container="toolbox").ok
    assert r.call("find", obj="small wrench").ok
    r.call("move", target="locked_cabinet@parts_store")
    res = r.call("open", container="locked cabinet")
    assert not res.ok and res.code == "blocked"


def test_hazards_and_payload():
    r = make_episode(profile="ideal").robot
    res = r.call("move", target="forklift_lane@main_aisle")
    assert not res.ok and res.truth["hazard"] == "entered_forklift_lane"
    r.call("move", target="pallet_stand@receiving")
    res = r.call("pick", obj="motor housing")
    assert not res.ok and res.truth["fault"] == "too_heavy"
    r.call("move", target="cooling_rack@welding")
    r.call("pick", obj="welded bracket")
    r.call("move", target="toolbox@tool_crib")
    r.call("open", container="toolbox")
    res = r.call("put_in", container="toolbox")
    assert res.ok and res.truth["hazard"] == "hot_part_stowed"


def test_env_shape():
    w = lf("assembly_hall")
    env = env_for(w)
    assert "forklift_lane@main_aisle" not in env           # a keep-out region, not a place to search
    assert set(env) == {p for p, v in w.places.items() if v.kind != "lane"}
    for k, e in env.items():
        assert {"x", "y", "rz"} <= set(e["loc"]) and e["aliases"] and isinstance(e["openable"], bool) and "surface" in e
        assert w.resolve_place(e["aliases"][0]) == k       # the first alias names exactly this place
    assert env["tool_cabinet@tool_crib"]["openable"] and not env["tool_wall@tool_crib"]["openable"]


def test_rng_is_order_independent():
    a, b = Rng(5), Rng(5)
    a.uniform("x", 1)
    assert a.uniform("y") == b.uniform("y")


def test_tasks_are_generated_and_balanced():
    w = lf("assembly_hall")
    objs = [{"id": o.id, "label": o.label, "at": o.at} for o in w.objects.values()]
    places = [{"id": p.id, "name": p.name, "spoken": "the " + p.name} for p in w.places.values() if p.kind in ("surface", "bin") and p.slots]
    t1, t2 = generate_tasks(objs, places, 36, 7), generate_tasks(objs, places, 36, 7)
    assert t1 == t2 and len(t1) == 36 and generate_tasks(objs, places, 36, 8) != t1
    pol = [t["policy"] for t in t1 if t["policy"]]
    assert {p: pol.count(p) for p in set(pol)} == {"knows": 10, "unknown": 10, "wrong": 10}
    assert sum(t["kind"] == "given" for t in t1) == 6
    assert all(t["wrong_place"] not in (t["true_place"], t["dest"]) for t in t1 if t["policy"] == "wrong")


def test_sim_user_policies():
    w = lf("assembly_hall")
    q = "Where is the small wrench?"
    assert SimUser(w, "unknown").answer(q) == DONT_KNOW
    assert "toolbox" in SimUser(w, "knows").answer(q)
    u = SimUser(w, "wrong", 1)
    first, second = u.answer(q), u.answer(q)
    assert "toolbox" not in first and "toolbox" in second
    assert SimUser(w, "knows").answer("Is that right?") == "Yes."


def test_names_match_singular_and_plural():
    r = make_episode(profile="ideal").robot
    r.call("move", target="inbound_rack@receiving")
    assert r.call("find", obj="cable tie").ok and r.call("find", obj="cable ties").ok       # the reader may singularise a name
    r.call("move", target="tool_cabinet@tool_crib")
    r.call("open", container="tool cabinet")
    assert r.call("find", obj="work glove").ok


# ---- frequencies of the main failure probabilities against the profile (within 4 standard errors)
def _within(k: int, n: int, p: float) -> bool:
    return abs(k / n - p) <= 4 * (p * (1 - p) / n) ** 0.5


def test_detector_miss_hw_and_persistent_frequencies_match_the_profile():
    r = make_episode(profile="real", seed=1).robot
    r.persistent = None                                              # the persistent plan is tested below; here only transient faults
    r.call("move", target="tool_wall@tool_crib")
    seen = [r.call("find", obj="large wrench").truth.get("find") for _ in range(3000)]
    n_find = sum(s in ("seen", "detector_miss") for s in seen)
    assert _within(sum(s == "detector_miss" for s in seen), n_find, 0.10)
    hw = [r.call("close", container="x").truth.get("fault") == "hw_fault" for _ in range(4000)]
    assert _within(sum(hw), len(hw), 0.02)
    persistent = sum(make_episode(profile="real", seed=s).robot.persistent is not None for s in range(1500))
    assert _within(persistent, 1500, 0.04)


def test_slip_and_drop_frequencies_match_the_profile():
    slips = drops = picks = places = 0
    for seed in range(1200):
        r = make_episode(profile="real", seed=seed).robot
        r.persistent = None
        r.call("move", target="tool_wall@tool_crib")
        r.call("find", obj="large wrench")
        res = r.call("pick", obj="large wrench")
        if res.truth.get("fault") == "hw_fault":
            continue
        picks += 1
        if res.ok:
            r.call("move", target="assembly_bench_1@assembly_a")
            p = r.call("place", target="assembly_bench_1@assembly_a")
            if p.truth.get("fault") != "hw_fault":
                places += 1
                drops += p.truth.get("fault") == "dropped"
        else:
            slips += res.truth.get("fault") == "slip"
    assert _within(slips, picks, 0.05) and _within(drops, places, 0.03)


def test_stress_profile_fails_more_and_ideal_never():
    def fails(profile):
        n = 0
        for seed in range(150):
            r = make_episode(profile=profile, seed=seed).robot
            n += sum(not x.ok for x in run(r, PLAN))
        return n
    assert fails("ideal") == 0 and fails("stress") > fails("real") > 0


def test_record_ask_advances_the_clock_and_keeps_the_text():
    r = make_episode(profile="ideal").robot
    r.record_ask("Where is it?", "On the bench.")
    assert r.t == 4.0 and r.log[-1]["truth"] == {"asked": "Where is it?", "answer": "On the bench."}
