"""RobotAdapter of the simulated shop-floor robot (robot_agent finds it with load_adapter('symbolic_robot.domains.factory'))."""
from __future__ import annotations

from pathlib import Path

from robot_agent.contract import Geometry, Manifest, Messages, Observation, Unbindable

from .backend import get_backend

MANIFEST_PATH = Path(__file__).with_name("manifest.yaml")
TEXT_ACTIONS = {"Say", "Ask"}
OBJECT_ACTIONS = {"Find", "Pick"}
DOCK_NAMES = {"dock", "charger", "home", "charging dock", "charging station", "base"}
PHRASES: dict = {
    "cannot_do": {"en": "I can't do that. I can move, find, pick up, put down, open and close things, talk and ask."},
    "done": {"en": "Done."},
}


class Adapter:
    quiet_skills = {"say", "ask"}

    def __init__(self, manifest: Manifest | None = None):
        self.manifest = manifest or Manifest.from_yaml(MANIFEST_PATH)
        self.geometry = Geometry.from_dict(self.manifest.geometry)
        self.i18n = Messages(language=self.manifest.language, phrases=PHRASES)

    def _world(self):
        return getattr(get_backend(), "world", None)

    def _resolve(self, name: str, kind: str) -> str:
        """A planner name -> the world's own name when it names exactly one thing, else the name as written."""
        w, n = self._world(), str(name or "").strip()
        if w is None or not n:
            return n
        if kind == "place":
            if n.lower() in DOCK_NAMES:
                return w.dock
            r = w.resolve_place(n)
            return r if isinstance(r, str) else n
        ids = w.resolve_objects(n)
        return w.objects[ids[0]].label if len(ids) == 1 else n

    def bind(self, step: dict, world=None):
        action = (step.get("action") or "").strip()
        obj = str(step.get("object") or step.get("target") or step.get("inputs") or "").strip()
        spec = self.manifest.skill_for(action)
        if spec is None or spec.action in ("Observe", "Verify"):
            raise Unbindable(f"no skill for {action!r} on {self.manifest.robot} (it can {', '.join(sorted(self.plannable_actions))})")
        if spec.action in TEXT_ACTIONS:
            if not obj:
                raise Unbindable(f"{action} needs a sentence")
            params = {"inputs": obj}
            if step.get("lang"):
                params["lang"] = step["lang"]
            return spec.name, params
        if spec.action == "Look":
            return spec.name, {}
        if not obj:
            raise Unbindable(f"{action} needs an argument")
        return spec.name, {"inputs": self._resolve(obj, "object" if spec.action in OBJECT_ACTIONS else "place")}

    @property
    def plannable_actions(self) -> set:
        return {s.action for s in self.manifest.skills if s.action not in ("Observe", "Verify")}

    def _observe(self) -> dict:
        try:
            return get_backend().observe()
        except Exception:                               # noqa: BLE001 - observe never raises
            return {}

    def observe(self, node=None) -> Observation:
        b, o = get_backend(), self._observe()
        bel = getattr(b, "believed", {}) or {}
        held, at = bel.get("holding"), o.get("at")
        return Observation(text=f"at {at or 'between places'}; holding {held or 'nothing'}", visible=[],
                           pose=list(o.get("pose_est") or []) or None, arrived=at, hands={"right": held},
                           opened=set(bel.get("opened") or []), sensor_health=self.health(node))

    def reconcile(self, world, node=None):
        o, bel = self._observe(), getattr(get_backend(), "believed", {}) or {}
        for attr, val in (("arrived", o.get("at")), ("holding", bel.get("holding"))):
            try:
                setattr(world, attr, val)
            except AttributeError:
                pass
        opened = getattr(world, "opened", None)
        if isinstance(opened, set):
            opened.clear()
            opened.update(bel.get("opened") or [])
        return world

    def pose(self, node=None) -> dict:
        p = self._observe().get("pose_est")
        return {"x": float(p[0]), "y": float(p[1]), "yaw": float(p[2]), "age_s": 0.0} if p else {}

    def container_states(self, node=None) -> dict:
        w = self._world()
        if w is None:
            return {}
        return {pid: ((pid in w.opened) if pid == w.at else None) for pid, p in sorted(w.places.items()) if p.openable}

    def health(self, node=None) -> dict:
        try:
            return get_backend().health()
        except Exception:                               # noqa: BLE001
            return {"ok": None}


def make_adapter() -> Adapter:
    return Adapter()
