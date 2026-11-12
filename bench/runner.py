"""Domain-neutral experiment runner. It drives a running robot_agent server over HTTP + WebSocket exactly as any robot_agent client does
(/skill/reset_world, /ws/agent, /agent/listen/<id>, /agent/sim_world/get) and measures from the simulator's own truth, never from the
robot's claim. A suite (bench.suite.Suite) supplies the arms (run options), the simulated person and the distance measure."""
from __future__ import annotations

import asyncio
import json
import time
import urllib.request

import websockets


def http(base: str, method: str, path: str, body=None, timeout: float = 60):
    req = urllib.request.Request(f"http://{base}{path}", data=None if body is None else json.dumps(body).encode(),
                                 headers={"content-type": "application/json"}, method=method)
    return json.loads(urllib.request.urlopen(req, timeout=timeout).read().decode() or "{}")


async def _episode(suite, base: str, task: dict, options: dict, timeout_s: float) -> dict:
    events, dialog = [], []
    last_speak, n_where = "", 0
    t0 = time.time()
    loop = asyncio.get_running_loop()
    async with websockets.connect(f"ws://{base}/ws/agent", max_size=None) as ws:
        await ws.send(json.dumps({"prompt": task["prompt"], "lang": "en", "planner": "sage", "options": options}))
        try:
            while True:
                left = timeout_s - (time.time() - t0)
                if left <= 0:
                    await loop.run_in_executor(None, lambda: http(base, "POST", "/agent/cancel", {}))
                    events.append({"event": "timeout", "_t": round(time.time() - t0, 2)})
                    break
                ev = json.loads(await asyncio.wait_for(ws.recv(), timeout=left))
                ev["_t"] = round(time.time() - t0, 3)
                events.append(ev)
                if ev.get("speak"):
                    last_speak = str(ev["speak"])
                    if ev.get("speak_id"):                      # the line was "said": acknowledge it as the browser would
                        await loop.run_in_executor(None, lambda i=ev["speak_id"]: _ack(base, i))
                lis = ev.get("listen")
                if isinstance(lis, dict) and lis.get("id"):
                    q = str(lis.get("prompt") or last_speak)
                    ans, kind, grounded = suite.answer(task, q, n_where)
                    if kind == "source":
                        n_where += 1
                    await asyncio.sleep(0.2)
                    await loop.run_in_executor(None, lambda: _ack(base, lis["id"], ans))
                    dialog.append({"q": q, "a": ans, "kind": kind, "grounded": grounded, "t": ev["_t"]})
                if ev.get("event") in ("done", "error"):
                    break
        except (websockets.exceptions.ConnectionClosed, asyncio.TimeoutError):
            pass
    return {"events": events, "dialog": dialog, "wall_s": round(time.time() - t0, 2)}


def _ack(base, req_id, text=""):
    try:
        http(base, "POST", f"/agent/listen/{req_id}", {"text": text}, timeout=10)
    except Exception:                                   # noqa: BLE001 - the request may have timed out
        pass


def sim_faults(log: list) -> list:
    """The simulator's injected faults in the call log (a drop, a grip slip, a detector miss, a hardware fault...): names of truth events/faults,
    both simulators' formats. An object that is simply not at a place (not_here, none_here) is not a fault."""
    out = []
    for e in log:
        t = e.get("truth") or {}
        if t.get("fault"):
            out.append(str(t["fault"]))
        elif t.get("event") and t["event"] != "not_here":
            out.append(str(t["event"]))
        elif t.get("really_here"):
            out.append("miss")
    return out


def episode_seed(task: dict, seed: int) -> int:
    """The simulator seed of (task, repeat): the same for every arm, different for every task, so faults are paired across arms
    and one seed number does not give every task the same fault."""
    return int("".join(c for c in task["id"] if c.isdigit()) or 0) * 100 + int(seed)


def run_episode(suite, base: str, task: dict, arm: str, seed: int, profile: str = "real", timeout_s: float = 420.0) -> dict:
    """One episode: fresh world and memory (reset_world), one run, then the truth read back. Never raises for a failed run."""
    ep_seed = episode_seed(task, seed)
    http(base, "POST", "/skill/reset_world", {"profile": profile, "seed": ep_seed})
    w0 = http(base, "GET", "/agent/sim_world/get")["value"]
    rec = asyncio.run(_episode(suite, base, task, suite.arms[arm], timeout_s))
    w1 = http(base, "GET", "/agent/sim_world/get")["value"]
    done = next((e for e in reversed(rec["events"]) if e.get("event") == "done"), {})
    truth_ok = w1["objects"].get(task["obj_id"], {}).get("at") == task["dest"]
    status = done.get("status")
    n_q = len(rec["dialog"])
    src = [d for d in rec["dialog"] if d["kind"] == "source"]
    bad = [i for i, d in enumerate(src) if d["grounded"] in ("room", "none")]       # answers that name no place (messy policies only)
    out = {"domain": suite.domain, "task": task["id"], "arm": arm, "seed": seed, "sim_seed": ep_seed, "policy": task.get("policy"), "kind": task["kind"],
           "status": status or "none", "success": bool(truth_ok), "claimed_done": status == "success",
           "wrong_done": status == "success" and not truth_ok, "distance_m": round(suite.distance(w1["log"]), 2),
           "questions": n_q, "q_source": len(src),
           "unusable_answers": len(bad), "clarified": sum(1 for i in bad if i + 1 < len(src)),      # an unusable answer followed by another where-question
           "t_sim": w1["robot"].get("t_sim"), "wall_s": rec["wall_s"], "n_events": len(rec["events"]),
           "faults": sim_faults(w1["log"]), "timeout": any(e.get("event") == "timeout" for e in rec["events"]), "engine_msg": str(done.get("msg", ""))[:200]}
    out["_detail"] = {"dialog": rec["dialog"], "log": w1["log"], "events": [e for e in rec["events"] if e.get("event") not in ("step_log",)],
                      "world_start": w0["objects"], "world_end": w1["objects"], "task": task}
    return out
