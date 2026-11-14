"""D3 task sets: ``d3dev`` (looked at case by case) and ``d3fresh`` (nobody looks at a case until the one final measure).

Made by the benchmark's own generator, like ``gen/pool.py``, with the shape of the shipped dev split instead of a training mix:

* the same families and checks as the shipped data (``sample.PLAN``, the oracle solves every task in the ideal profile);
* worlds: ``seed_state = SEED_BASE[name] + randrange(10000)`` (30000.. and 40000..), above every shipped task (< 10000) and above
  both pools (10000.., 20000..); houses: the six train houses; test-only templates are never used;
* the shares of (structure, kind) follow the shipped dev split (``SHARE_FROM``, read from its labels only: a count per stratum);
  the families of a compound structure come from the generator's plan, weighted so that each stratum has about ``OVER`` times
  its quota of candidates;
* identities (house, goals, order: independent of the world seed): a task repeats no identity of train, dev, ``pool_train``,
  ``pool_eval`` (when their files are given), nor of the other D3 set, and no identity twice inside a set. Texts: the generator's
  own near / exact duplicate check against train and dev (and the other D3 set). The test split is never read: a D3 task may
  still equal a test task by identity (same generator, same houses); worlds never coincide (test worlds are < 10000);
* the ``split`` field of a record is ``dev`` (the runner's default split filter keeps the tasks of a ``--tasks`` file with
  that value, so ``run --tasks FILE`` works without ``--split``; the runner is frozen); the id ``hl-d3dev-NNNNNN`` /
  ``hl-d3fresh-NNNNNN`` and ``meta.pool`` tell the set;
* wording: the generator's templates (no LLM paraphrase, no text written by a model; ``source`` is ``template``).

``python -m bench.suites.home.gen.d3 --out DIR [--fresh-out DIR2] [--pools DIR]`` writes ``DIR/d3dev.jsonl`` and ``d3fresh.jsonl`` (in
``DIR2`` when given: the fresh set is kept where nobody reads it) and prints a manifest (counts per stratum and the sha256 of both files). Deterministic for a given ``--gen-seed``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from . import resplit
from .pool import _preload, finish, load_reference, write
from .sample import PLAN, SPLIT_HOUSES, Gen, quotas
from .split import assign_ids, is_test_template

NAMES = ("d3dev", "d3fresh")
SEED_BASE = {"d3dev": 30000, "d3fresh": 40000}          # worlds: base .. base + 9999
SIZE = 150
OVER = 8                      # candidates per quota of a stratum (the identity rules drop many)
FILE_SPLIT = "dev"            # the ``split`` field written to the files; the id (``hl-<name>-N``) and ``meta.pool`` name the set
SHARE_FROM = "dev"            # the shipped split whose (structure, kind) counts give the shares
SPLIT_HOUSES.update({n: SPLIT_HOUSES["train"] for n in NAMES})


def strata_targets(size: int = SIZE) -> dict:
    """{(structure, kind): n} summing to ``size``: the shares of the shipped dev split (labels only)."""
    from ..tasks import read_records
    cnt = Counter((r["structure"], r["kind"]) for r in read_records(SHARE_FROM))
    keys = sorted(cnt)
    return dict(zip(keys, quotas(size, [cnt[k] for k in keys])))


def family_structures() -> dict:
    """plan key -> structure, from the structure the shipped dev split gives each family (single families are 'single')."""
    from ..tasks import read_records
    out = {k: "single" for k, typ, *_ in PLAN if typ == "single"}
    for r in read_records(SHARE_FROM):
        if r["structure"] != "single":
            out[r["meta"]["plan_key"]] = r["structure"]
    return out


def candidate_plan(targets: dict) -> list:
    """[(plan entry, n)]: each family gets candidates in proportion to its plan weight within its structure's quota."""
    fam = family_structures()
    need = Counter()
    for (st, _kind), n in targets.items():
        need[st] += n
    tot = Counter()
    for key, typ, gen, filt, w in PLAN:
        tot[fam.get(key, "single")] += w
    out = []
    for e in PLAN:
        st = fam.get(e[0])
        if st is None or tot[st] == 0:
            continue
        n = round(need[st] * OVER * e[4] / tot[st])
        if n > 0:
            out.append((e, n))
    return out


def _ident_sets(pools_dir) -> set:
    """Identities of every ``pool_*.jsonl`` under ``pools_dir`` (several hash seeds may sit in sub-directories)."""
    ids = set()
    for p in sorted(Path(pools_dir).rglob("pool_*.jsonl")) if pools_dir else []:
        ids |= {resplit.identity(json.loads(x)) for x in open(p, encoding="utf-8")}
    return ids


def _key(r: dict) -> str:
    return hashlib.sha256((resplit.identity(r) + json.dumps(r["text"], sort_keys=True, ensure_ascii=False)).encode()).hexdigest()


def select(cands: list, targets: dict) -> tuple:
    """Pick the quota of every stratum from the candidates in a fixed (hash) order; a shortage is filled from the same
    structure, then from anything. Returns (records, shortage dict)."""
    by = {}
    for r in sorted(cands, key=_key):
        by.setdefault((r["structure"], r["kind"]), []).append(r)
    taken, left, short = [], {}, {}
    for k, n in sorted(targets.items()):
        got = by.get(k, [])[:n]
        taken += got
        left[k] = by.get(k, [])[n:]
        if len(got) < n:
            short[k] = n - len(got)
    for k, miss in sorted(short.items()):
        pool = left.get(k, []) + [r for kk, v in sorted(left.items()) if kk[0] == k[0] and kk != k for r in v]
        pool += [r for kk, v in sorted(left.items()) if kk[0] != k[0] for r in v]
        for r in pool[:miss]:
            taken.append(r)
            left = {kk: [x for x in v if x is not r] for kk, v in left.items()}
    return taken, short


def generate(name: str, gen_seed: int, ref: dict, avoid: set, other: list | None, log=None, size: int = SIZE) -> tuple:
    """Records of one D3 set (ids ``hl-<name>-NNNNNN``) and the shortage of its strata."""
    targets = strata_targets(size)
    g = Gen(gen_seed, {name: 1}, seed_base={name: SEED_BASE[name]})
    Gen._any_ok = {}
    _preload(g, ref)
    for r in other or []:                           # the other D3 set: no repeated text either
        for lg in ("en", "ko"):
            from .dedup import norm
            g.seen[lg].add(norm(r["text"][lg], lg))
            g.near.add("o:" + r["id"], r["text"][lg], lg, "other")
    forbidden = set(avoid) | ref["dev"] | ref["train"] | {resplit.identity(r) for r in other or []}
    cands, seen = [], set()
    for (key, typ, gen, filt, _w), n in candidate_plan(targets):
        before = len(g.out[name])
        g.fill(name, key, typ, gen, filt, n)
        kept = 0
        for rec in g.out[name][before:]:
            rec = finish(rec)
            if rec is None or is_test_template(rec["template_id"]):
                continue
            i = resplit.identity(rec)
            if i in forbidden or i in seen:
                continue
            seen.add(i)
            rec["meta"]["pool"] = name
            cands.append(rec)
            kept += 1
        if log:
            log(f"[{name}] {key}: {kept}/{n} kept (generated {len(g.out[name]) - before})")
    picked, short = select(cands, targets)
    recs = assign_ids(picked, name, gen_seed)
    for r in recs:
        r["split"] = FILE_SPLIT          # see the module doc: the runner's default split filter then keeps the file's tasks
    return recs, short


def problems(recs: list, name: str) -> list:
    """Rule violations of a D3 set: world floor, houses, test-only templates, repeated identity."""
    out, base, used = [], SEED_BASE[name], Counter()
    for r in recs:
        if not base <= r["seed_state"] < base + 10000:
            out.append((r["id"], "seed_state"))
        if r["house"] not in SPLIT_HOUSES["train"]:
            out.append((r["id"], "house"))
        if is_test_template(r["template_id"]):
            out.append((r["id"], "test_template"))
        used[resplit.identity(r)] += 1
        if used[resplit.identity(r)] > 1:
            out.append((r["id"], "identity"))
    return out


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="python -m bench.suites.home.gen.d3")
    ap.add_argument("--out", required=True)
    ap.add_argument("--gen-seed", type=int, default=2026)
    ap.add_argument("--fresh-out", default=None, help="a directory for d3fresh.jsonl (default: --out); keep it out of the repos")
    ap.add_argument("--pools", default=None, help="a directory with pool_train.jsonl / pool_eval.jsonl whose identities are avoided")
    a = ap.parse_args(argv)
    ref, avoid, out = load_reference(), _ident_sets(a.pools), Path(a.out)
    sets, manifest = {}, {}
    for name in NAMES:
        recs, short = generate(name, a.gen_seed, ref, avoid, sets.get("d3dev"), log=print)
        bad = problems(recs, name)
        if bad:
            raise ValueError(f"{name} breaks its rules: {bad[:5]}")
        path = Path(a.fresh_out or a.out) / f"{name}.jsonl" if name == "d3fresh" else out / f"{name}.jsonl"
        write(recs, path)
        sets[name] = recs
        manifest[name] = {"n": len(recs), "sha256": sha(path), "shortage": {"|".join(k): v for k, v in short.items()},
                          "structure": dict(Counter(r["structure"] for r in recs)), "kind": dict(Counter(r["kind"] for r in recs))}
    print(json.dumps(manifest, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
