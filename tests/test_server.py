"""Server glue with robot_agent (skipped when it is not importable). Each domain boots in its own process: robot_agent binds one pack per process."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("robot_agent")
pytest.importorskip("fastapi")
ROOT = Path(__file__).resolve().parents[1]
BOOT = r"""
import json, sys
from fastapi.testclient import TestClient
from symbolic_robot import server
robot, world, run_dir = sys.argv[1:4]
app, live = server.build(robot, world, "ideal", 0, run_dir, "headless", "human")
from robot_agent.state import current
c = TestClient(app)
names = sorted(s["name"] for s in current().sr.all())
v = c.get("/agent/sim_world/get").json()["value"]
st = c.post("/agent/sim_command/send", json={"cmd": "state"}).json()
pose = c.get("/agent/mobile_pose/get").json()["value"]
rw = c.post("/skill/reset_world", json={"seed": 2}).json()
sp = c.post("/skill/spawn_object", json={"cls": "nonexistent_class", "place": "x"}).json()
print(json.dumps({"names": names, "objects": len(v["objects"]), "state_ok": st.get("ok"), "pose": pose, "reset": rw.get("isdone"),
                  "seed_after": live.kw["seed"], "spawn_isdone": sp.get("isdone")}))
"""


def boot(robot, world, tmp_path):
    env = {**os.environ, "PYTHONPATH": f"{ROOT}:{os.environ.get('PYTHONPATH', '')}", "ROBOT_AGENT_ROS": "off"}
    out = subprocess.run([sys.executable, "-c", BOOT, robot, world, str(tmp_path)], capture_output=True, text=True, env=env, cwd=ROOT, timeout=180)
    assert out.returncode == 0, out.stderr[-2000:]
    return json.loads(out.stdout.strip().splitlines()[-1]), tmp_path


def test_factory_boots_with_pack_and_launcher_skills(tmp_path):
    r, run_dir = boot("factory", "assembly_hall", tmp_path)
    assert {"move", "find", "pick", "place", "put_in", "open", "close", "say", "ask", "look", "grasp_check", "pose"} <= set(r["names"])
    assert {"reset_world", "spawn_object"} <= set(r["names"]) and not {"move_to", "warmup_servers"} & set(r["names"])
    assert r["objects"] == 21 and r["state_ok"] and r["reset"] is True and r["seed_after"] == 2 and r["spawn_isdone"] is False
    assert not (run_dir / "configs/locations/default/map").exists()
    conns = json.loads((run_dir / "configs/locations/default/connections.json").read_text())
    assert {c["type"] for c in conns} == {"llm"}


def test_home_boots_with_its_own_pack(tmp_path):
    pytest.importorskip("homeloop_robot")
    r, run_dir = boot("home", "senior_flat", tmp_path)
    assert {"move", "find", "pick", "reset_world", "spawn_object"} <= set(r["names"]) and r["state_ok"] and r["objects"] > 5


def test_factory_manifest_check():
    """The checker finds no error. `--strict` would fail only on its 'module is outside <pkg>, not inspected' warnings: it assumes a
    top-level pack name, ours is dotted (symbolic_robot.domains.factory). Reported, not worked around in the engine."""
    env = {**os.environ, "PYTHONPATH": f"{ROOT}:{os.environ.get('PYTHONPATH', '')}"}
    out = subprocess.run([sys.executable, "-m", "robot_agent.contract.check_manifest", "symbolic_robot.domains.factory"],
                         cwd=ROOT, capture_output=True, text=True, env=env, timeout=120)
    assert out.returncode == 0, out.stdout + out.stderr
    assert " 0 error(s)" in out.stdout
    warnings = [x for x in out.stdout.splitlines() if x.strip().startswith("warning")]
    assert warnings and all("not inspected" in w for w in warnings), warnings


def test_factory_adapter_binds_names():
    env = {**os.environ, "PYTHONPATH": f"{ROOT}:{os.environ.get('PYTHONPATH', '')}"}
    code = ("from robot_agent.contract import load_adapter\nad = load_adapter('symbolic_robot.domains.factory')\n"
            "print(ad.bind({'action': 'Pick', 'object': 'Small Wrench'}), ad.bind({'action': 'MoveTo', 'object': 'tool wall'}))")
    out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env, cwd=ROOT, timeout=120)
    assert "('pick', {'inputs': 'small wrench'})" in out.stdout and "('move', {'inputs': 'tool_wall@tool_crib'})" in out.stdout, out.stdout + out.stderr
