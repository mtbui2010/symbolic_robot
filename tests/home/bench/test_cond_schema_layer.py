"""The D1 layer ``cond_schema`` (robot_agent option cond_extract keys kinds / heard_match, default off): selectable by name only, its overlay data
labelled assumed, the arm hashes unchanged, its prompt asks for every key of the extraction schema, and the ASSUMED Korean "-오면" clause reads made-up
sentences. Pure data: no run, no model."""
import re

from bench.suites.home.planners import d1_options as D
from tests.home.bench.test_cond_answer_layer import ALL_HASH, D2_HASH, D3_HASH, MODEL, digest, env

# the keys of robot_agent's cond_extract.SCHEMA_KINDS (written out: this repository's tests do not import robot_agent)
SCHEMA_KINDS_KEYS = ("conditional", "kind", "object", "at", "present", "if_goals", "else_goals", "always", "drop", "question", "unsure")
BASE = D.ALL_LAYERS


def test_cond_schema_is_selectable_only_and_leaves_the_arm_hashes():
    assert "cond_schema" in D.SELECTABLE and "cond_schema" not in D.ALL_LAYERS
    assert digest(env("d3")) == D3_HASH and digest(env("all")) == ALL_HASH and digest(env("d2")) == D2_HASH


def test_cond_schema_off_none_selected_has_no_kinds_key():
    for arm in ("all", "d3", "d2", "none", ",".join(BASE + ("cond_answer",))):
        assert "cond_extract.kinds" not in D.layer_options(env(arm))


def test_cond_schema_after_cond_answer_adds_its_key_and_its_cond_extract_data_only():
    on, before = env(",".join(BASE + ("cond_answer", "cond_schema"))), env(",".join(BASE + ("cond_answer",)))
    assert D.selected_layers(on)[-2:] == ("cond_answer", "cond_schema")
    assert D.layer_options(on) == {**D.layer_options(before), "cond_extract.kinds": "1"}
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, before)
    ce, ce0 = ov["planner"]["options"]["cond_extract"], base["planner"]["options"]["cond_extract"]
    assert ce.pop("prompt") == D.COND_PROMPT_KINDS and ce0.pop("prompt") == D.COND_PROMPT
    assert ce.pop("heard_match") == D.HEARD_MATCH and "heard_match" not in ce0
    assert ce["clauses"]["ko"]["condition"] == ce0["clauses"]["ko"]["condition"] + [D.KO_COND_COME]
    ce["clauses"] = ce0["clauses"]
    ov.pop("note"), base.pop("note")
    assert ov == base


def test_cond_schema_data_is_labelled_assumed():
    assert D._labels(D.LAYERS["cond_schema"][1]) == ["assumed"]
    assert D.HEARD_MATCH.get("assumed") is True


def test_cond_schema_prompt_names_every_schema_key_and_keeps_the_two_slots():
    for k in SCHEMA_KINDS_KEYS:
        assert re.search(rf"\b{k}\b", D.COND_PROMPT_KINDS), k
    assert "{request}" in D.COND_PROMPT_KINDS and "{goals}" in D.COND_PROMPT_KINDS
    for k in ("presence", "state", "unobservable"):
        assert k in D.COND_PROMPT_KINDS


def test_ko_cond_come_reads_made_up_clauses_and_not_request_forms():
    rx = re.compile(D.KO_COND_COME)
    for t in ("삼촌이 돌아오면 상자를 줘요.", "눈이 오면 장갑을 가져와요", "고양이가 나오면, 문을 닫아 줘"):
        assert rx.search(t), t
    for t in ("장갑을 가져와요.", "상자를 줘요", "돌아오면 돼요", "와 주면 고맙겠어요", ""):
        assert not rx.search(t), t
