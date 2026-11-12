"""The factory domain through the generic layers: the domain protocol, the live backend, sim_command ops, size of the world."""
from symbolic_robot import registry
from symbolic_robot.backend import LiveBackend
from symbolic_robot.simcommand import SimCommands


def live(**kw):
    return LiveBackend(registry.get("factory"), "assembly_hall", kw.get("profile", "ideal"), kw.get("seed", 0))


def test_domain_catalogue():
    d = registry.get("factory")
    assert d.available() is None and d.worlds() == ["assembly_hall", "small_workshop"] and d.profiles() == ["ideal", "real", "stress"]
    assert d.pack == "symbolic_robot.domains.factory" and d.world_label == "floor"


def test_live_backend_matches_the_robot_and_publishes_truth():
    lv = live()
    assert lv.call("move", target="tool_wall@tool_crib").ok
    v = lv.world_view()
    assert v["robot"]["at"] == "tool_wall@tool_crib" and v["robot"]["t_sim"] > 0 and v["floor"] == "assembly_hall"
    assert v["log"][-1]["truth"]["leg"]["to"] == "tool_wall@tool_crib" and (v["robot"]["x"], v["robot"]["y"]) == (22.0, 3.0) or v["robot"]["x"] > 0
    lv.record_ask("Where?", "There.")
    assert lv.world_view()["log"][-1]["msg"] == "typed answer"


def test_sim_command_ops():
    lv = live()
    c = SimCommands(lv)
    st = c.handle({"cmd": "state"})
    assert st["ok"] and st["isdone"] and len(st["objects"]) == 21 and "wrench" in st["catalog"]["objects"] and st["domain"] == "factory"
    assert c.handle({"cmd": "move_object", "body": "wrench_l", "place": "lathe bench"})["ok"]
    assert lv.world_view()["objects"]["wrench_l"]["at"] == "lathe_bench@machining"
    assert c.handle({"cmd": "move_object", "name": "wrench_l", "x": 4.5, "y": 5.0})["ok"]             # a point near the pallet stand
    assert lv.world_view()["objects"]["wrench_l"]["at"] == "pallet_stand@receiving"
    sp = c.handle({"cmd": "spawn", "cls": "wrench", "place": "lathe_bench@machining", "variant": "tiny"})
    assert sp["ok"] and sp["id"] == "wrench_1" and lv.world_view()["objects"]["wrench_1"]["label"] == "tiny wrench"
    assert not c.handle({"cmd": "spawn", "cls": "no_such_class", "place": "lathe_bench@machining"})["ok"]
    assert not c.handle({"cmd": "spawn", "cls": "wrench"})["ok"]
    lv.call("move", target="tool_wall@tool_crib")
    erased = []
    c2 = SimCommands(lv, on_new_world=lambda: erased.append(1) or ["memory.json"])
    out = c2.handle({"cmd": "reset", "what": "all", "seed": 5, "profile": "real"})
    assert out["ok"] and "memory.json" in out["msg"] and lv.kw["seed"] == 5 and lv.kw["profile"] == "real"
    assert lv.world_view()["objects"]["wrench_l"]["at"] == "tool_wall@tool_crib" and lv.world_view()["robot"]["at"] == "charging_dock@receiving"
    assert not c.handle({"cmd": "reset", "profile": "nope"})["ok"] and not c.handle({"cmd": "reset", "what": "x"})["ok"]
    assert c.handle({"cmd": "reset", "forget": False})["ok"] and erased == [1]
    assert c.handle({"cmd": "load", "name": "small_workshop"})["ok"] and lv.kw["world"] == "small_workshop"
    assert not c.handle({"cmd": "load", "name": "nowhere"})["ok"]
    t = c.handle({"cmd": "truth", "last": 3})
    assert t["ok"] and t["world"] == "small_workshop" and "objects" in t


def test_layout_and_env_for_the_server():
    lv = live()
    lay = lv.domain.layout(lv.episode)
    assert any(p["kind"] == "dock" for p in lay["places"]) and lay["labels"] and len(lay["places"]) == 25
    assert "forklift_lane@main_aisle" not in lv.domain.env(lv.episode)
