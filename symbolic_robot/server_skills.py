"""Skill functions the launcher adds to the domain pack's own (robot_agent calls `f(node=None, **params) -> dict`).

Server glue: this module and server.py are the only ones of the core that import robot_agent (always inside functions).
They reach the running backend through `set_live`.
"""
from __future__ import annotations

import glob
import os

_LIVE = None
MEMORY_FILES = ("object_memory.*.json", "grace_memory.*.jsonl", "world_state.*.json")


def set_live(live) -> None:
    global _LIVE
    _LIVE = live


def live():
    if _LIVE is None:
        raise RuntimeError("no live backend installed (server.build calls set_live)")
    return _LIVE


def forget_memory(*_args) -> list:
    """Erase the robot's memory of the old world (where it saw objects, past runs, the belief): robot_agent's files in the common folder."""
    from robot_agent.state import current
    erased = []
    for pattern in MEMORY_FILES:
        for path in glob.glob(os.path.join(str(current().common_dir), pattern)):
            try:
                os.remove(path)
                erased.append(os.path.basename(path))
            except OSError:
                pass
    return erased


def reset_world(node=None, profile=None, seed=None, forget=True, **params) -> dict:
    """A new simulated episode (objects back in place, robot on its dock). Optional: profile, seed, world, and any option of the domain
    (for example a different arrangement of the objects). forget (default true) also erases the robot's memory files."""
    opts = {k: v for k, v in params.items() if k not in ("inputs", "lang")}
    live().reset(profile=profile, seed=None if seed is None else int(seed), **opts)
    erased = [] if str(forget).lower() in ("0", "false", "no", "off") else forget_memory()
    return {"isdone": True, "msg": "world reset" + (f" (memory erased: {', '.join(erased)})" if erased else ""), "erased": erased}


def spawn_object(node=None, cls: str = "", place: str = "", **params) -> dict:
    """Put an object of the domain's catalog at a place, now. Lasts until reset_world. Example: spawn_object::cls='mug', place='<place id>'."""
    b = live()
    out = b.domain.op_spawn(b.episode, str(cls or "").strip(), str(place or "").strip(), **params) if cls and place else None
    if out is None:
        return {"isdone": False, "msg": "spawn_object needs cls and place and a domain that supports it"}
    return {"isdone": bool(out.get("ok")), **out}


# ---- headless dialogue: the benchmark's scripted person answers ---------------------------------------------------------------

def say_quiet(node=None, inputs: str = "", lang: str = "en", **params) -> dict:
    """Say, headless: recorded in the call log only (nobody is listening)."""
    return live().call("say", text=str(inputs), lang=lang).to_legacy()


def ask_typed(node=None, inputs: str = "", lang: str = "en", retries: int = 0, timeout: float = 120.0, **params) -> dict:
    """Ask, headless: emits a `listen` event (text mode, the question in `prompt`) and waits for the answer posted to /agent/listen/<id>
    (an experiment script plays the person)."""
    from robot_agent.utils import listen_dashboard
    q = str(inputs or "").strip()
    try:
        text = listen_dashboard(prompt=q, lang="en", max_sec=10.0, timeout=float(timeout), mode="text", capture="browser")
    except RuntimeError as e:
        return {"isdone": False, "text": "", "answer": "", "msg": str(e)}
    live().record_ask(q, text or "")
    return {"isdone": bool(text), "text": text or "", "answer": text or "", "msg": "ok" if text else "no answer heard"}
