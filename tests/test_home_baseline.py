"""The household simulator and benchmark behave exactly as the standalone packages did before they were merged here.

Baselines (tests/home/parity/*.gz) were recorded from the standalone packages (homeloop_robot sim-freeze-r19 and homeloop_bench r21-p4b,
docs/migration_home.md): the scripted calls of tests/home/parity/calls.py, and three runs of the benchmark with the oracle and naive planners
on the dev split with the fake LLM (the first is exactly `--planner oracle --split dev --limit 20 --llm fake`). A difference means behaviour changed: do not update a baseline to make this pass (a deliberate change
needs its own note in docs/CHANGELOG.md and a new baseline file)."""
import gzip
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent / "home" / "parity"
sys.path.insert(0, str(HERE))
import calls  # noqa: E402


def _gz(name: str) -> bytes:
    return gzip.decompress((HERE / (name + ".gz")).read_bytes())


def test_scripted_calls_match_the_standalone_package():
    want = json.loads(_gz("home_calls.json"))
    got = json.loads(json.dumps(calls.record(), sort_keys=True, default=str))
    assert got.keys() == want.keys() and len(got) == 62
    bad = [k for k in want if got[k] != want[k]]
    assert not bad, bad


@pytest.mark.parametrize("name,args", [
    ("oracle_real_dev20", ["--planner", "oracle", "--limit", "20"]),
    ("oracle_real_dev20_seeds2", ["--planner", "oracle", "--profile", "real", "--limit", "20", "--seeds", "2"]),
    ("naive_stress_dev20", ["--planner", "naive", "--profile", "stress", "--limit", "20"]),
])
def test_oracle_and_naive_episodes_are_byte_identical(name, args, tmp_path):
    from bench.suites.home.cli import main
    assert main(["run", "--split", "dev", "--llm", "fake", *args, "--out", str(tmp_path)]) == 0
    assert (tmp_path / "episodes.jsonl").read_bytes() == _gz(name + ".episodes.jsonl")
    if name == "oracle_real_dev20":
        got, want = json.loads((tmp_path / "summary.json").read_text()), json.loads(_gz(name + ".summary.json"))
        for d in (got, want):
            d["config"]["versions"].pop("homeloop_bench_git"), d["config"]["versions"].pop("homeloop_robot_git")     # the checkout, not behaviour
        assert got == want
