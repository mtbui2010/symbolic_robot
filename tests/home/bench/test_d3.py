"""D3 task sets (gen/d3.py): the shares follow dev, the worlds and houses stay apart, the committed d3dev file obeys the rules."""

import hashlib
import json
import re
from pathlib import Path

from bench.suites.home.gen import d3, resplit
from bench.suites.home.gen.pool import load_reference

ROOT = Path(__file__).resolve().parents[3]
DEV_FILE = ROOT / "bench/suites/home/data/pools/d3dev.jsonl"
DOC = ROOT / "docs/home/bench/d3_layers.md"


def _rec(st, kind, i):
    return {"structure": st, "kind": kind, "house": "h", "text": {"en": f"t{i}", "ko": f"k{i}"}, "goal": {"all": [i]}, "id": f"x{i}"}


def test_targets_follow_dev_and_sum_to_the_size():
    t = d3.strata_targets()
    assert sum(t.values()) == d3.SIZE == 150
    assert sum(n for (st, _k), n in t.items() if st == "single") in range(60, 75)       # dev: 45 % single, not the plan's 59 %
    assert {k for (_s, k) in t} == {"feasible", "clarify", "refuse"}
    assert sum(d3.strata_targets(40).values()) == 40


def test_select_fills_a_shortage_from_the_same_structure_then_anything():
    cands = [_rec("single", "feasible", i) for i in range(5)] + [_rec("sequence", "feasible", 9)]
    got, short = d3.select(cands, {("single", "feasible"): 2, ("single", "refuse"): 2, ("sequence", "feasible"): 1})
    assert short == {("single", "refuse"): 2} and len(got) == 5 and len({r["id"] for r in got}) == 5


def test_a_small_set_obeys_the_rules_and_is_deterministic():
    ref = load_reference()
    a, short_a = d3.generate("d3dev", 2026, ref, set(), None, size=10)
    b, _ = d3.generate("d3dev", 2026, ref, set(), None, size=10)
    assert len(a) == 10 and not d3.problems(a, "d3dev")
    assert [r["text"] for r in a] == [r["text"] for r in b]
    assert all(r["split"] == d3.FILE_SPLIT and r["id"].startswith("hl-d3dev-") and r["meta"]["pool"] == "d3dev" for r in a)
    assert not {resplit.identity(r) for r in a} & (ref["dev"] | ref["train"])


def test_the_two_sets_have_other_worlds():
    assert d3.SEED_BASE["d3dev"] + 10000 <= d3.SEED_BASE["d3fresh"] and d3.SEED_BASE["d3dev"] >= 30000


def test_problems_flags_a_low_world_a_test_house_and_a_repeat():
    ref = load_reference()
    r = d3.generate("d3dev", 2026, ref, set(), None, size=4)[0][0]
    bad = dict(r, seed_state=5, house="korean_apt_84")
    why = {w for _i, w in d3.problems([bad, r, r], "d3dev")}
    assert {"seed_state", "house", "identity"} <= why


def test_committed_d3dev_file_is_what_the_doc_says():
    recs = [json.loads(x) for x in open(DEV_FILE, encoding="utf-8")]
    assert len(recs) == 150 and not d3.problems(recs, "d3dev")
    assert hashlib.sha256(DEV_FILE.read_bytes()).hexdigest() in DOC.read_text(encoding="utf-8")
    assert re.search(r"d3fresh.*[0-9a-f]{64}", DOC.read_text(encoding="utf-8"))
