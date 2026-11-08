"""Round 19: the household robot's safety profile is robot pack data (configs/safety/household.yaml, manifest safety.profile).

robot_agent's core holds no hazard rule; this robot declares what is hazardous for it. With robot_agent on the path, the pack's
profile must reproduce the golden decision table made from the r17 core tables (the same table robot_agent's own household
fixture reproduces). Clean room: the simulator never reads the profile, and the robot's ENV carries no scoring tag, so the
profile's classes can only match names and aliases the robot itself has.
"""
import json
from pathlib import Path

import pytest
import yaml

import _safety_golden as SG
from helpers import HAS_RA
from homeloop_robot.configs.tasks import env_for

PKG = Path(__file__).resolve().parents[1] / "homeloop_robot"
PROFILE = PKG / "configs" / "safety" / "household.yaml"
HERE = Path(__file__).parent


def test_the_manifest_declares_the_pack_profile():
    m = yaml.safe_load((PKG / "configs" / "manifest.yaml").read_text(encoding="utf-8"))
    assert m["safety"]["profile"] == "safety/household.yaml"
    p = yaml.safe_load(PROFILE.read_text(encoding="utf-8"))
    assert p["profile"] == "household" and {r["id"] for r in p["rules"]} == {"chem_food", "chem_child"}
    assert all(r.get("provenance") == "assumed" for r in p["rules"])      # no rule claims a source it does not have


def test_the_simulator_never_reads_the_robot_profile():
    """Only configs/ (the robot_agent adapter side) may name the profile; the judge, the world and the user model do not."""
    for f in PKG.rglob("*.py"):
        if "configs" in f.relative_to(PKG).parts:
            continue
        s = f.read_text(encoding="utf-8")
        assert "household.yaml" not in s and "configs/safety" not in s and "safety_profile" not in s, f


def test_the_robot_env_has_no_scoring_tags():
    """The profile's place classes share names with house tags (food_storage, food_prep); the robot must not see the tags."""
    from homeloop_robot.world import from_house
    houses = sorted(p.stem for p in (PKG / "houses").glob("*.yaml"))
    assert len(houses) >= 6
    for h in houses:
        for key, e in env_for(from_house(h, 0)).items():
            assert "tags" not in e and "food_storage" not in json.dumps(e) and "food_prep" not in json.dumps(e), (h, key)


@pytest.mark.skipif(not HAS_RA, reason="robot_agent not importable")
def test_robot_agent_loads_the_pack_profile():
    from robot_agent.contract.manifest import load_manifest
    m = load_manifest(PKG / "configs" / "manifest.yaml")
    prof = m.safety_profile
    assert prof is not None and prof.name == "household" and len(prof.sha256) == 64


@pytest.mark.skipif(not HAS_RA, reason="robot_agent not importable")
def test_the_pack_profile_reproduces_the_r17_decisions():
    from robot_agent.core.safety import check_goal, load_profile
    prof, errs = load_profile(PROFILE)
    assert errs == []
    recv = ("hazard.receivers",)
    gold = json.loads((HERE / "golden" / "safety_household_r17.json").read_text(encoding="utf-8"))
    t = SG.table(lambda g, ps, pack, mode, rec: check_goal(g, ps, prof, pack, mode, recv if rec else ()))
    assert (t["n"], t["sha256"]) == (gold["n"], gold["sha256"])
    assert t["hits"] == gold["hits"]
