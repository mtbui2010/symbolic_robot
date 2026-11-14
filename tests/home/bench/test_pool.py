"""Training pools (gen/pool.py): the shipped generator is unchanged, the pool worlds and houses stay apart, the identity rule."""

import hashlib
import json
from collections import Counter

import pytest

from bench.suites.home.gen import pool as P
from bench.suites.home.gen import resplit
from bench.suites.home.gen.sample import Gen, SPLIT_HOUSES
from bench.suites.home.gen.split import assign_ids

# sha256 over the records of Gen(2026, {train 120, dev 40, test 60}) before seed_base / op_filter existed (checked in a
# worktree of the commit before the change): the default path must stay byte for byte the same
SHIPPED_HASH = "b6ab6b4eb0001d995002120dcd603c4016da0ec981c70c6b2cce89c5a7c5ce47"


def _hash(g):
    out, h = g.run(), hashlib.sha256()
    for s in sorted(out):
        for r in assign_ids(out[s], s, 2026):
            h.update(json.dumps(r, sort_keys=True, ensure_ascii=False).encode())
    return h.hexdigest()


def test_seed_base_zero_is_the_shipped_generator_byte_for_byte():
    assert _hash(Gen(2026, {"train": 120, "dev": 40, "test": 60})) == SHIPPED_HASH
    assert _hash(Gen(2026, {"train": 120, "dev": 40, "test": 60}, seed_base=0)) == SHIPPED_HASH


@pytest.fixture(scope="module")
def train_pool():
    return P.generate_pool("pool_train", sample=3)


def test_pool_worlds_start_at_10000_and_use_train_houses(train_pool):
    assert train_pool and min(r["seed_state"] for r in train_pool) >= 10000
    assert {r["house"] for r in train_pool} <= set(SPLIT_HOUSES["train"])
    assert "korean_apt_84" not in {r["house"] for r in train_pool}
    assert all(r["id"].startswith("hl-pool_train-") for r in train_pool)
    assert not P.problems(train_pool, "pool_train")


def test_pool_has_the_declared_classes_and_both_condition_outcomes(train_pool):
    assert {"cond", "charger", "book_ask", "refuse_soap"} <= {r["meta"]["pool_class"] for r in train_pool}
    holds = {r["subtasks"][0]["condition"]["holds_at_start"] for r in train_pool if r["meta"]["pool_class"] == "cond"
             and r["subtasks"][0].get("condition")}
    assert holds == {True, False}


def test_pool_eval_floor_and_no_identity_of_pool_train(train_pool):
    ev = P.generate_pool("pool_eval", sample=3, other=train_pool)
    assert min(r["seed_state"] for r in ev) >= 20000
    assert not {resplit.identity(r) for r in ev} & {resplit.identity(r) for r in train_pool}
    assert not P.problems(ev, "pool_eval", other=train_pool)


def test_identity_rule(train_pool):
    r = next(x for x in train_pool if x["meta"]["pool_class"] == "cond")
    ident = resplit.identity(r)
    ref = {"dev": {ident}, "train": set()}
    assert not P.identity_ok(r, "pool_train", ref, set(), Counter())          # a dev identity: never
    ref = {"dev": set(), "train": {ident}}
    assert not P.identity_ok(r, "pool_train", ref, set(), Counter())          # cond: no train identity either
    assert not P.identity_ok(r, "pool_eval", ref, set(), Counter())
    assert P.identity_ok(r, "pool_train", {"dev": set(), "train": set()}, set(), Counter())
    assert not P.identity_ok(r, "pool_train", None, set(), Counter({ident: 1}))   # cond: one task per identity
    t = dict(r, meta=dict(r["meta"], pool_class="charger"))
    assert P.identity_ok(t, "pool_train", ref, set(), Counter({ident: P.MAX_SAME - 1}))   # targeted: may repeat a train one
    assert not P.identity_ok(t, "pool_train", ref, set(), Counter({ident: P.MAX_SAME}))
    assert not P.identity_ok(t, "pool_eval", ref, set(), Counter())           # the eval pool never does


def test_problems_flags_a_low_world_a_test_house_and_a_test_template(train_pool):
    bad = dict(train_pool[0], seed_state=5, house="korean_apt_84", template_id="rearrange.feasible.08")
    out = {why for _id, why in P.problems([bad], "pool_train")}
    assert {"seed_state", "house", "test_template"} <= out


def test_load_reference_reads_only_train_and_dev(monkeypatch):
    seen = []

    def fake(split, path=None):
        seen.append(split)
        return []
    import bench.suites.home.tasks as T
    monkeypatch.setattr(T, "read_records", fake)
    ref = P.load_reference()
    assert seen == ["train", "dev"] and ref["dev"] == set() and ref["train"] == set()


def test_no_selector_means_no_filter_and_unknown_pool_is_refused():
    assert P.make_filter(None) is None and P.make_filter({}) is None
    with pytest.raises(ValueError):
        P.generate_pool("pool_test")
