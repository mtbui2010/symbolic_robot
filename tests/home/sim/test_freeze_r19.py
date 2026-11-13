"""sim-freeze-r19 pin: round 19 changed no simulator behaviour (the scoring change lives in homeloop_bench, which owns the
judge). The selftest traces of the sim-freeze-r13 code are byte-identical; if this fails, the simulator moved and the
freeze note in docs/user_model.md must say so."""

import hashlib
import subprocess
import sys

import pytest

PINS = {"real": "4a071034b4166c52f10d624eabfa722928cbe2823865f73b5cc2a61820f4153f",
        "stress": "05800b6f79c258d4357a5ed8a82d44bc8f373aee3094970e5a67ea7acbb6a219"}


@pytest.mark.parametrize("profile", sorted(PINS))
def test_selftest_trace_is_the_r13_trace(profile, tmp_path):
    out = tmp_path / "t.jsonl"
    subprocess.run([sys.executable, "-m", "symbolic_robot.domains.home.selftest", "--seed", "7", "--episodes", "30", "--profile", profile,
                    "--out", str(out)], check=True, capture_output=True)
    assert hashlib.sha256(out.read_bytes()).hexdigest() == PINS[profile]
