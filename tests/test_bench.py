import json
import socket
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

from bench import campaign, orchestrate, protocol, stats
from bench.suites import registry
from bench.suites.home import command


def test_sign_test_exact_values():
    assert stats.sign_test(0, 0) == 1.0
    assert stats.sign_test(6, 0) == pytest.approx(0.03125)
    assert stats.sign_test(5, 0) == pytest.approx(0.0625)
    assert stats.sign_test(3, 3) == 1.0
    assert stats.sign_test(9, 1) == pytest.approx(0.021484375)


def test_bootstrap_is_deterministic_and_brackets_the_mean():
    m, lo, hi = stats.boot_ci([1.0, 2.0, 3.0, 4.0, 5.0])
    assert (m, lo, hi) == stats.boot_ci([1.0, 2.0, 3.0, 4.0, 5.0]) and lo <= m <= hi and m == 3.0
    assert stats.boot_ci([]) == (0.0, 0.0, 0.0)


def rows(a_succ, b_succ):
    out = []
    for i, (a, b) in enumerate(zip(a_succ, b_succ)):
        for arm, s in (("A", a), ("B", b)):
            out.append({"task": f"t{i}", "arm": arm, "seed": 0, "success": s, "wrong_done": 0, "distance_m": 10.0, "questions": 1, "t_sim": 1.0})
    return out


def test_compare_combined_criterion_counts_wins_losses_ties():
    r = rows([0, 0, 1, 1, 0, 1], [1, 1, 1, 0, 0, 1])
    c = stats.compare(r, "B", "A")
    assert c["combined"] == {"wins": 2, "losses": 1, "ties": 3, "p": 1.0} and c["n_tasks"] == 6
    assert c["d_success"]["mean"] == pytest.approx(1 / 6, abs=1e-3)


def test_suites_registered_with_their_protocols():
    keys = {d + "/" + n for d, n, _ in registry.listing()}
    assert {"factory/protocol", "factory/messy", "factory/messy_fix", "home/planners", "home/run"} <= keys
    for n in ("protocol", "messy", "messy_fix"):
        s = registry.get("factory", n)
        assert s.protocol.exists() and s.tasks and s.answer and s.distance and s.analyze and set(s.default_arms) <= set(s.arms)
    assert registry.get("factory", "protocol").arms["B"]["search_route_weight"] == 0.3
    assert len(registry.get("factory", "protocol").tasks("assembly_hall", 36, 7)) == 36
    with pytest.raises(KeyError):
        registry.get("factory", "nope")


def test_protocol_hash_is_pre_registered(tmp_path):
    doc = tmp_path / "p.md"
    doc.write_text("v1")
    out = tmp_path / "res"
    h = protocol.register(out, doc)
    assert (out / protocol.FILE).read_text().split()[0] == h == protocol.sha256_of(doc) and protocol.verify(out, doc)
    assert protocol.register(out, doc) == h
    doc.write_text("v2")
    assert not protocol.verify(out, doc)
    with pytest.raises(SystemExit):
        protocol.register(out, doc)
    assert protocol.register(out, doc, allow_change=True) == h
    assert protocol.register(out, None) == ""


def test_campaign_resumes_limits_and_rejects_unknown_arms(tmp_path, monkeypatch):
    calls = []

    def fake(suite, base, t, arm, seed, profile):
        calls.append((t["id"], arm, seed))
        return {"task": t["id"], "arm": arm, "seed": seed, "status": "success", "success": True, "wrong_done": False, "distance_m": 1.0, "questions": 0,
                "wall_s": 0.1, "_detail": {"x": 1}}
    monkeypatch.setattr(campaign, "run_episode", fake)
    s = registry.get("factory", "protocol")
    out = tmp_path / "r"
    assert campaign.run_campaign(s, "x:1", out, "assembly_hall", 3, 2, ["A", "B"], limit=5) == 5
    assert campaign.run_campaign(s, "x:1", out, "assembly_hall", 3, 2, ["A", "B"]) == 7           # 12 in all, 5 done before
    assert campaign.run_campaign(s, "x:1", out, "assembly_hall", 3, 2, ["A", "B"]) == 0
    assert len(set(calls)) == 12 == len(calls)
    assert len((out / "episodes.jsonl").read_text().splitlines()) == 12 and (out / "PROTOCOL_SHA256").exists()
    assert json.loads((out / "tasks.json").read_text())[0]["id"] == "t00" and (out / "detail" / "t00_A_0.json").exists()
    order = [(c[0], c[1]) for c in calls if c[2] == 0][:4]
    assert order == [("t00", "A"), ("t00", "B"), ("t01", "B"), ("t01", "A")]                        # the arm order rotates with the task
    with pytest.raises(SystemExit):
        campaign.run_campaign(s, "x:1", out, "assembly_hall", 3, 1, ["Z"])
    only = campaign.run_campaign(s, "x:1", tmp_path / "o", "assembly_hall", 3, 1, ["A"], only=["t01"])
    assert only == 1


def test_home_suite_delegates_by_command_line_and_refuses_the_test_split():
    cmd = command("py", "run", ["--planner", "oracle", "--split", "dev", "--limit", "3"], "results/home_run")
    assert cmd == ["py", "-m", "homeloop_bench.cli", "run", "--planner", "oracle", "--split", "dev", "--limit", "3", "--out", "results/home_run"]
    assert command("py", "run", ["--out", "mine"], "results/x").count("--out") == 1
    assert command("py", "planners", [], "results/x") == ["py", "-m", "homeloop_bench.cli", "planners"]
    with pytest.raises(SystemExit):
        command("py", "run", ["--split", "test"], None)
    with pytest.raises(SystemExit):
        command("py", "run", ["--split=test"], None)


def test_port_helpers_and_stop_only_the_started_process():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        s.listen()
        busy = s.getsockname()[1]
        assert not orchestrate.is_free(busy)
        assert orchestrate.free_port(range(busy, busy + 1 + 40)) != busy
    assert orchestrate.port_range("8120-8122") == range(8120, 8123) and orchestrate.port_range("9000") == range(9000, 9001)
    p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])
    t0 = time.time()
    orchestrate.stop(p)
    assert p.poll() is not None and time.time() - t0 < 5
    orchestrate.stop(p)                                                                             # idempotent


def test_dry_run_prints_the_plan_and_starts_nothing(capsys):
    from bench.cli import main
    assert main(["run", "--domain", "factory", "--suite", "messy_fix", "--out", "x", "--dry-run"]) == 0
    out = capsys.readouterr().out
    assert "tasks 6" in out and "arms A,E,D" in out and "only t02" in out
    assert main(["run", "--domain", "home", "--suite", "planners", "--out", "x", "--dry-run", "--python", "py"]) == 0
    assert "homeloop_bench.cli planners" in capsys.readouterr().out
