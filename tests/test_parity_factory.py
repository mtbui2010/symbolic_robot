"""Factory sim parity against recorded campaigns of the earlier repository (read only). Set SHOPFLOOR_RESULTS to its results folder;
skipped when it is absent. Full replay of every episode: python tests/parity/factory_replay.py <folder>."""
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent / "parity"))
import factory_replay  # noqa: E402

RES = Path(os.environ.get("SHOPFLOOR_RESULTS", "/media/keti/workdir/remote_dir/shopfloor_robot/results"))
pytestmark = [pytest.mark.parity, pytest.mark.skipif(not (RES / "factory_v2" / "episodes.jsonl").exists(), reason="recorded campaigns not available")]


@pytest.mark.parametrize("name", ["factory_v2", "messy_factory", "messy_fix_factory"])
def test_replayed_call_sequences_match_the_recording(name):
    st = factory_replay.run(RES / name, "assembly_hall", "real", stride=5)
    assert st["episodes"] >= 25 and st["calls"] > 400
    assert st["mismatched_calls"] == 0, st["examples"]


def test_tasks_and_analysis_match_the_recorded_summaries(tmp_path):
    from bench.suites import registry
    for name, suite, n in (("factory_v2", "protocol", 36), ("messy_factory", "messy", 6)):
        s = registry.get("factory", suite)
        assert json.loads(json.dumps(s.tasks("assembly_hall", n, 7))) == json.loads((RES / name / "tasks.json").read_text())
        d = tmp_path / name
        d.mkdir()
        for f in ("episodes.jsonl", "tasks.json"):
            (d / f).write_text((RES / name / f).read_text())
        assert json.loads(json.dumps(s.analyze(d))) == json.loads((RES / name / "summary.json").read_text())
