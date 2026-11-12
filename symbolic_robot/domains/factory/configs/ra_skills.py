"""robot_agent skill functions (legacy dict results) over the simulated robot: f(node=None, inputs="", **params) -> {isdone, msg, code?, ...}."""
from __future__ import annotations

from .backend import get_backend


def _run(skill: str, **args) -> dict:
    return get_backend().call(skill, **args).to_legacy()


def move(node=None, inputs: str = "", **params) -> dict:
    return _run("move", target=str(inputs))


def find(node=None, inputs: str = "", **params) -> dict:
    out = _run("find", obj=str(inputs))
    if out.get("isdone") and out.get("found"):
        out["ins"] = {out["found"]: {"pose_3d": [0.6, 0.0, 0.8]}}
    return out


def pick(node=None, inputs: str = "", **params) -> dict:
    return _run("pick", obj=str(inputs))


def place(node=None, inputs: str = "", **params) -> dict:
    return _run("place", target=str(inputs))


def put_in(node=None, inputs: str = "", **params) -> dict:
    return _run("put_in", container=str(inputs))


def open(node=None, inputs: str = "", **params) -> dict:  # noqa: A001 - the skill's name
    return _run("open", container=str(inputs))


def close(node=None, inputs: str = "", **params) -> dict:
    return _run("close", container=str(inputs))


def say(node=None, inputs: str = "", lang: str = "en", **params) -> dict:
    return _run("say", text=str(inputs), lang=lang)


def ask(node=None, inputs: str = "", lang: str = "en", retries: int = 0, **params) -> dict:
    out = {}
    for _ in range(max(0, int(retries or 0)) + 1):
        out = _run("ask", question=str(inputs), lang=str(lang or "en"))
        if out.get("isdone"):
            break
    out["text"] = out.get("answer", "")
    return out


def look(node=None, **params) -> dict:
    return _run("look")


def grasp_check(node=None, **params) -> dict:
    out = _run("grasp_check")
    out["isdone"] = bool(out.get("holding"))
    return out


def pose(node=None, **params) -> dict:
    out = _run("pose")
    p = out.get("pose")
    if p:
        out["pose"] = (float(p[0]), float(p[1]), float(p[2]))
    return out
