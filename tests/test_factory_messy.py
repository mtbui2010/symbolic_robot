"""The messy person's scripts (domains/factory/messy.py): generated from world data, deterministic, every policy present."""
from symbolic_robot.domains.factory.messy import NEW_POLICIES, POLICIES
from symbolic_robot.domains.factory.person import answer_for
from symbolic_robot.domains.factory.tasks import factory_messy_tasks


def test_suite_shape_and_determinism():
    a, b = factory_messy_tasks("assembly_hall", 6, 7), factory_messy_tasks("assembly_hall", 6, 7)
    assert a == b and len(a) == 6 * len(POLICIES)
    for pol in POLICIES:
        assert sum(t["policy"] == pol for t in a) == 6
    for t in a:
        assert t["kind"] == "ask" and ("script" in t) == (t["policy"] in NEW_POLICIES)


def test_scripts_follow_their_policy():
    for t in factory_messy_tasks("assembly_hall", 6, 7):
        s = t.get("script")
        if t["policy"] == "room_only":
            assert t["zone_text"] in s[0]["text"] and s[0]["grounded"] == "room"
            assert t["true_text"] not in s[0]["text"] + s[1]["text"]
        if t["policy"] == "mind_change":
            assert t["wrong_text"] in s[0]["text"] and t["true_text"] in s[1]["text"]
        if t["policy"] == "silent":
            assert s[0]["text"] in ("", "...") and t["true_text"] in s[1]["text"]
        if t["policy"] == "partial_name":
            assert t["variant_text"] in s[0]["text"]


def test_answer_for_uses_script_and_old_policies_unchanged():
    t = [x for x in factory_messy_tasks("assembly_hall", 6, 7) if x["policy"] == "mind_change"][0]
    assert answer_for(t, "Where is the gasket?", 0)[0] == t["script"][0]["text"]
    assert answer_for(t, "Where is the gasket?", 1)[0] == t["script"][1]["text"]
    assert answer_for(t, "Where is the gasket?", 5)[0] == t["script"][1]["text"]          # the last answer repeats
    assert answer_for(t, "Where should I put it?", 0)[1] == "dest"
    old = {"policy": "wrong", "wrong_text": "the A", "true_text": "the B", "dest_text": "the C", "object": "x"}
    assert answer_for(old, "Where is the x?", 0) == ("I think it is on the A.", "source", "")
    assert answer_for(old, "Where is the x?", 1) == ("It is on the B.", "source", "")
