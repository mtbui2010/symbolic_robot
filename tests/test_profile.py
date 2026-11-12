import pytest
import yaml

from symbolic_robot import profile as P
from symbolic_robot.domains.factory.profiles import PROFILE_DIR, load_profile

OLD_REAL = {"speed_mps": 0.8, "detector_miss": 0.10, "slip": 0.05, "drop": 0.03, "hw_fault": 0.02, "persistent_fault": 0.04}
OLD_IDEAL = {"speed_mps": 0.8, "detector_miss": 0.0, "slip": 0.0, "drop": 0.0, "hw_fault": 0.0, "persistent_fault": 0.0}
DURATIONS = {"find": 3.0, "pick": 6.0, "place": 5.0, "put_in": 6.0, "open": 5.0, "close": 4.0, "say": 2.0, "ask": 4.0, "grasp_check": 0.5,
             "pose": 0.2, "move_overhead": 4.0}


def test_real_values_and_sources():
    real = load_profile("real")
    assert {k: real.get(k) for k in OLD_REAL} == OLD_REAL and real.get("durations_s") == DURATIONS
    assert all(real.source(k) for k in real.keys())


def test_ideal_is_derived_from_real_and_has_no_failures():
    assert not (PROFILE_DIR / "ideal.yaml").exists()
    ideal = load_profile("ideal")
    assert {k: ideal.get(k) for k in OLD_IDEAL} == OLD_IDEAL and ideal.get("durations_s") == DURATIONS     # the same numbers the old ideal file had
    assert "failure switched off" in ideal.source("slip")


def test_stress_is_derived_only_when_real_declares_it():
    s = load_profile("stress")
    assert s.get("slip") == pytest.approx(0.15) and s.get("speed_mps") == 0.8 and s.get("detector_miss") == pytest.approx(0.30)
    assert load_profile("real").with_overrides(slip=1.0).get("slip") == 1.0
    assert P.available(PROFILE_DIR) == ["ideal", "real", "stress"]
    with pytest.raises(ValueError):
        load_profile("nope")


def test_probability_maps_and_missing_source(tmp_path):
    (tmp_path / "real.yaml").write_text(yaml.safe_dump({"profile": "real", "derive": {"stress": {"scale": 10}}, "params": {
        "a": {"kind": "prob_map", "value": {"low": 0.01, "high": 0.2}, "source": "s"},
        "b": {"kind": "split", "value": {"x": 0.5, "y": 0.5}, "source": "s"}}}))
    assert P.load(tmp_path, "ideal").get("a") == {"low": 0.0, "high": 0.0} and P.load(tmp_path, "ideal").get("b") == {"x": 0.5, "y": 0.5}
    assert P.load(tmp_path, "stress").get("a") == {"low": pytest.approx(0.1), "high": 1.0}
    (tmp_path / "bad.yaml").write_text(yaml.safe_dump({"params": {"a": {"kind": "prob", "value": 0.1}}}))
    with pytest.raises(ValueError):
        P.load(tmp_path, "bad")
    assert P.load(tmp_path, "real").get("zzz", 5) == 5
