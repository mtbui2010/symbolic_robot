"""Server glue: serves any registered domain through robot_agent's API (the dashboard, the planner, /ws/agent).

The ONLY module of the core (with server_skills.py) that imports robot_agent, and only inside functions. Needs the `server` extra and a
robot_agent with the ROBOT_AGENT_ROS=off switch. Simulation only: no ROS, no sensors, no real robot.
"""
from __future__ import annotations

import importlib
import json
import os
from pathlib import Path

from . import registry
from .backend import LiveBackend
from .simcommand import SimCommands

OLLAMA_URL = "http://127.0.0.1:11434"
WHISPER_URL = "http://127.0.0.1:8000"
WHISPER_MODEL = "deepdml/faster-whisper-large-v3-turbo-ct2"
AGENT_PREFIX = "ROBOT_AGENT_"


class PoseAgent:
    """robot_agent's device-agent interface: get() -> dict (GET /agent/<name>/get), send(params) -> dict, cancel()."""

    def __init__(self, live):
        self.live = live

    def get(self):
        return self.live.snapshot()

    def send(self, params=None):
        return {"isdone": True, "msg": "read-only agent"}

    def cancel(self):
        return False


class WorldAgent(PoseAgent):
    def get(self):
        return self.live.world_view()


class CommandAgent(PoseAgent):
    def __init__(self, live, cmds):
        super().__init__(live)
        self.cmds = cmds

    def get(self):
        return self.cmds.handle({"cmd": "state"})

    def send(self, params=None):
        return self.cmds.handle(dict(params or {}))


class StubNode:
    """What robot_agent's API needs from a node when there is no ROS: agents plus the cancel / stop hooks."""
    is_init = False

    def __init__(self, agents: dict):
        self.agents = agents

    def cancel_all(self):
        return {}

    def clear_cancel(self):
        return None

    def stop(self):
        return None


def planner_env(domain, model: str) -> None:
    """Environment defaults of the engine (a variable already set wins; an option sent with a run overrides them anyway)."""
    d = os.environ.setdefault
    d("ROBOT_AGENT_ROS", "off")
    d("OLLAMA_NUM_CTX", "8192")
    if model:
        d(AGENT_PREFIX + "UNDERSTAND_MODEL", model)
        d(AGENT_PREFIX + "TRANSLATE_MODEL", model)
    for k, v in domain.planner_env().items():
        d(AGENT_PREFIX + k, str(v))


def seed_connections(site: Path, ollama_url: str, whisper_url: str, model: str) -> None:
    """connections.json BEFORE the app boots (robot_agent loads it in the background): the LLM (Ollama) and the speech-to-text server.
    Existing entries are kept, ours updated."""
    ours = [{"type": "stt", "name": "whisper", "config": {"url": whisper_url, "model": WHISPER_MODEL, "timeout": 30}}]
    if model:
        ours.insert(0, {"type": "llm", "name": "ollama_local", "config": {"name": "llama", "url": ollama_url, "model": model, "num_ctx": 8192}})
    path = Path(site) / "connections.json"
    try:
        have = json.loads(path.read_text()) if path.exists() else []
    except ValueError:
        have = []
    names = {c["name"] for c in ours}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps([c for c in have if isinstance(c, dict) and c.get("name") not in names] + ours, indent=2))


def publish_world(live, site: Path, state) -> None:
    """The planner's ENV and the Map tab's picture for the CURRENT world of the backend."""
    from . import mapview
    d, ep = live.domain, live.episode
    env = d.env(ep)
    if env is not None:                       # robot_agent's config manager falls back to this module attribute
        importlib.import_module(f"{d.pack}.configs.tasks").ENV = env
    png, frame = mapview.render_png(d.layout(ep))
    if png is not None:
        (Path(site) / "map").mkdir(parents=True, exist_ok=True)
        (Path(site) / "map" / "map.png").write_bytes(png)
        err = state.cm.update("MAP", mapview.map_config(frame))
        if err:
            raise RuntimeError(f"MAP rejected: {err}")


def skill_table(domain, dialogue: str, ask_mode: str) -> dict:
    mod = "symbolic_robot.server_skills"
    table = {n: (mod, n) for n in ("reset_world", "move_to", "spawn_object", "warmup_servers")}
    if dialogue == "human":
        pack_skills = importlib.import_module(f"{domain.pack}.configs.skills_config").SKILL_CONFIGS
        ask, say = ("ask_typed", "say_quiet") if ask_mode == "headless" else ("ask_human", "say_human")
        table.update({"ask": (mod, ask), "say": (mod, say)})
        if "announce" in pack_skills:
            table["announce"] = (mod, say)
    return table


def build(robot: str = "factory", world: str | None = None, profile: str = "real", seed: int = 0, run_dir: str = "run_dir",
          speedup: float | None = None, ask_mode: str = "voice", dialogue: str = "human", model: str | None = None,
          ollama_url: str = OLLAMA_URL, whisper_url: str = WHISPER_URL, opts: dict | None = None):
    """-> (app, live). Importable for tests; does not start a server."""
    dom = registry.get(robot)
    why = dom.available()
    if why:
        raise RuntimeError(f"domain {robot!r} is not available: {why}")
    world = world or dom.default_world()
    model = dom.default_model if model is None else model
    os.environ["SYMBOLIC_ROBOT_ASK_MODE"] = "text" if ask_mode == "headless" else ask_mode
    planner_env(dom, os.environ.get("SYMBOLIC_ROBOT_MODEL", model))
    opts = {**dom.live_opts, **(opts or {})}
    if dialogue == "sim":
        opts = {**dom.sim_user_opts(), **opts}
    live = LiveBackend(dom, world, profile, seed, dom.default_speedup if speedup is None else speedup, **opts)
    dom.install_pack(live)
    from . import server_skills as S
    S.set_live(live)

    cfg_dir = Path(run_dir) / "configs"
    site = cfg_dir / "locations" / "default"
    seed_connections(site, ollama_url, whisper_url, os.environ.get("SYMBOLIC_ROBOT_MODEL", model))
    from robot_agent.app_factory import create_app
    from robot_agent.state import current
    app = create_app(dom.pack, config_dir=cfg_dir)
    state = current()
    cmds = SimCommands(live, on_new_world=S.forget_memory)
    state.dm._ros_node = StubNode({"mobile_pose": PoseAgent(live), "sim_world": WorldAgent(live), "sim_command": CommandAgent(live, cmds)})
    state.sr.load_from_skill_configs(skill_table(dom, dialogue, ask_mode))
    publish_world(live, site, state)
    live.on_new_world = lambda lv: publish_world(lv, site, state)
    return app, live
