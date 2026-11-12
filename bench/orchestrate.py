"""Start a symbolic_robot server on a free test port, wait until it answers, run something, stop it (SIGTERM, then SIGKILL).
Only the process started here is ever signalled; a busy port is never taken."""
from __future__ import annotations

import contextlib
import os
import signal
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path


def port_range(text: str) -> range:
    a, _, b = text.partition("-")
    return range(int(a), int(b or a) + 1)


def is_free(port: int) -> bool:
    for host in ("127.0.0.1", "0.0.0.0"):
        with socket.socket() as s:
            s.settimeout(0.5)
            if s.connect_ex((host, port)) == 0:
                return False
    return True


def free_port(ports: range) -> int:
    for p in ports:
        if is_free(p):
            return p
    raise SystemExit(f"no free port in {ports.start}-{ports.stop - 1}")


def wait_up(port: int, proc, timeout: float = 120.0, settle: float = 10.0) -> None:
    """Poll the server until it answers; then wait `settle` s (robot_agent finishes loading its connections in the background)."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        if proc.poll() is not None:
            raise RuntimeError(f"the server exited with status {proc.returncode}")
        with contextlib.suppress(Exception):
            urllib.request.urlopen(f"http://127.0.0.1:{port}/agent/sim_world/get", timeout=2).read()
            time.sleep(settle)
            return
        time.sleep(1.0)
    raise RuntimeError(f"no answer from port {port} after {timeout:.0f} s")


def stop(proc, grace_s: float = 10.0) -> None:
    if proc.poll() is not None:
        return
    proc.send_signal(signal.SIGTERM)
    try:
        proc.wait(grace_s)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait()


@contextlib.contextmanager
def server(python: str, robot: str, ports: range, run_dir: Path, args=(), env=None, log: Path | None = None):
    """Context manager: yields 127.0.0.1:<port> of a running server for `robot`."""
    port = free_port(ports)
    run_dir = Path(run_dir)
    run_dir.mkdir(parents=True, exist_ok=True)
    cmd = [python, "-m", "symbolic_robot", "run", "--robot", robot, "--port", str(port), "--run-dir", str(run_dir / f"site-{port}"), *args]
    logf = open(log or run_dir / f"server-{port}.log", "w")
    proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT, env={**os.environ, **(env or {})}, start_new_session=True)
    try:
        wait_up(port, proc)
        yield f"127.0.0.1:{port}"
    finally:
        stop(proc)
        logf.close()
