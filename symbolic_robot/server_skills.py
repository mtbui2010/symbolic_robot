"""Skill functions the launcher adds to the domain pack's own (robot_agent calls `f(node=None, **params) -> dict`).

Server glue: this module and server.py are the only ones of the core that import robot_agent (always inside functions).
They reach the running backend through `set_live`.
"""
from __future__ import annotations

import glob
import math
import os

_LIVE = None
NEAR_M = 1.2
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


def move_to(node=None, x=None, y=None, rz=None, max_dist_m: float = NEAR_M, **params) -> dict:
    """Click-to-move from the map: go to the nearest place within max_dist_m of the point (x, y) [m]. The simulated robot moves between
    places, not to free points."""
    if x is None or y is None:
        return {"isdone": False, "msg": "move_to needs x and y"}
    b = live()
    x, y = float(x), float(y)
    places = [p for p in b.domain.layout(b.episode).get("places", []) if p.get("kind") != "floor"]
    best = min(places, key=lambda p: math.dist(p["pos"], (x, y)), default=None)
    if best is None or math.dist(best["pos"], (x, y)) > max_dist_m:
        return {"isdone": False, "msg": f"no place within {max_dist_m} m of ({x:.1f}, {y:.1f})"}
    res = b.call("move", target=best["id"])
    return {"isdone": bool(res.ok), "msg": f"{best['id']}: {res.msg}", "at": best["id"]}


def spawn_object(node=None, cls: str = "", place: str = "", **params) -> dict:
    """Put an object of the domain's catalog at a place, now. Lasts until reset_world. Example: spawn_object::cls='mug', place='<place id>'."""
    b = live()
    out = b.domain.op_spawn(b.episode, str(cls or "").strip(), str(place or "").strip(), **params) if cls and place else None
    if out is None:
        return {"isdone": False, "msg": "spawn_object needs cls and place and a domain that supports it"}
    return {"isdone": bool(out.get("ok")), **out}


# ---- dialogue with a person through the dashboard ------------------------------------------------------------------------------

def say_human(node=None, inputs: str = "", lang: str | None = None, **params) -> dict:
    """The robot says a line: voiced by the browser (a speak event of the running agent)."""
    from robot_agent.utils import say_to_user
    text = str(inputs or "").strip()
    if text:
        say_to_user(text, lang=live().domain.speech_lang(text, lang), source="dashboard", wait=True)
    return {"isdone": True, "msg": "ok"}


def ask_human(node=None, inputs: str = "", lang: str = "en", retries: int = 0, max_sec: float = 10.0, **params) -> dict:
    """The robot asks and takes the person's answer: the browser voices the question and opens the mic (Whisper on the 'stt' connection),
    or shows a text box when SYMBOLIC_ROBOT_ASK_MODE=text. The reply keeps the shape of the simulated ask: out['text']."""
    from robot_agent.utils import listen_dashboard, say_to_user
    q = str(inputs or "").strip()
    lg = live().domain.speech_lang(q, lang)
    say_to_user(q, lang=lg, source="dashboard", wait=True)
    mode = os.environ.get("SYMBOLIC_ROBOT_ASK_MODE", "voice")
    text = None
    for _ in range(max(0, int(retries or 0)) + 1):
        try:
            text = listen_dashboard(prompt=None, lang=lg, max_sec=float(max_sec), timeout=120.0 if mode == "text" else 60.0, mode=mode,
                                    capture="whisper", stt="whisper", silence_sec=1.5, earcon=0.3 if mode == "voice" else 0.0)
        except RuntimeError as e:             # the person cancelled the run, the microphone is blocked, no dashboard run is attached
            return {"isdone": False, "text": "", "answer": "", "msg": str(e)}
        if text:
            break
    return {"isdone": bool(text), "text": text or "", "answer": text or "", "msg": "ok" if text else "no answer heard"}


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


def _silence_wav(seconds: float = 1.0) -> bytes:
    import io
    import struct
    import wave
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(struct.pack("<h", 0) * int(16000 * seconds))
    return buf.getvalue()


def _warm_jobs(entries) -> list:
    import requests
    jobs = []                                  # (kind, connection, label, callable)
    for e in entries:
        cfg = e.get("config") or {}
        url = str(cfg.get("url") or "").rstrip("/")
        if not url:
            continue
        if e["type"] == "llm":
            for m in dict.fromkeys([m for m in (cfg.get("model"), os.environ.get("ROBOT_AGENT_UNDERSTAND_MODEL")) if m]):
                def warm(url=url, m=m, cfg=cfg):
                    requests.post(f"{url}/api/chat", json={"model": m, "stream": False, "keep_alive": "30m", "messages": [{"role": "user", "content": "hi"}],
                                                           "options": {"num_predict": 1, "num_ctx": int(cfg.get("num_ctx") or 8192)}},
                                  timeout=240).raise_for_status()
                jobs.append(("vlms", e["name"], f"{m} @ {url}", warm))
        elif e["type"] == "stt":
            def warm(url=url, cfg=cfg):
                requests.post(f"{url}/v1/audio/transcriptions", files={"file": ("w.wav", _silence_wav(), "audio/wav")},
                              data={"model": cfg.get("model", ""), "language": "en", "vad_filter": "true"}, timeout=240).raise_for_status()
            jobs.append(("voices", e["name"], f"{cfg.get('model', '')} @ {url}", warm))
    return jobs


def warmup_servers(node=None, **kwargs) -> dict:
    """Load the models of the servers this robot talks to (LLM, speech-to-text) before a session. Moves nothing, says nothing.
    Result shape = what the dashboard's 'Warm up' button reads: {isdone, level, kinds: {vlms|voices: {level, servers}}, msg}."""
    import time
    from robot_agent.state import current
    jobs = _warm_jobs(current().dm.get_all())
    if not jobs:
        return {"isdone": False, "level": "error", "kinds": {}, "msg": "no server to warm up (no llm or stt connection)"}
    kinds: dict = {}
    for kind, conn, label, fn in jobs:
        t0 = time.time()
        try:
            fn()
            ok, err = True, ""
        except Exception as ex:                # noqa: BLE001
            ok, err = False, str(ex)[:120]
        k = kinds.setdefault(kind, {"servers": []})
        k["servers"].append({"connection": conn, "idx": len(k["servers"]), "label": label, "primary": True, "ok": ok,
                             "sec": round(time.time() - t0, 1), "error": err})
    for k in kinds.values():
        good = sum(1 for s in k["servers"] if s["ok"])
        k["level"] = "ok" if good == len(k["servers"]) else ("warn" if good else "error")
    level = "error" if any(k["level"] == "error" for k in kinds.values()) else ("warn" if any(k["level"] == "warn" for k in kinds.values()) else "ok")
    names = {"vlms": "VLMs", "voices": "Voices"}
    msg = " | ".join(f"{names[n]} {'ok' if k['level'] == 'ok' else 'FAILED'} ({sum(1 for s in k['servers'] if s['ok'])}/{len(k['servers'])})"
                     for n, k in kinds.items())
    return {"isdone": level != "error", "level": level, "kinds": kinds, "msg": msg}
