"""The D1 layer ``cond_answer`` (robot_agent option cond_goal keys answer / open_closed / confirm_none, default off): selectable by name only, its
overlay data labelled assumed, the arm hashes unchanged, and the ASSUMED answer-negation words read made-up answers. Pure data: no run, no model."""
import hashlib
import json
import re

from bench.suites.home.planners import d1_options as D

D3_HASH = "f751d73417c679250af675869633f8f1278ab7fcfe9127c3c249f53e294beab3"
D2_HASH = "64b278b5beef2493d675eac77ebd6d10b799e2ce2e307014e56b3f207e356942"
ALL_HASH = "78f601bfeee57accd86d4d628ce0b9385dca7327c3546944ed18d126fbe6669a"
MODEL = "hl-understand-p3-s700"
KEYS = {"cond_goal.answer": "1", "cond_goal.open_closed": "1", "cond_goal.confirm_none": "1"}


def env(v):
    return {D.LAYERS_ENV: v}


def digest(e):
    ov = D.d1_overlay({}, MODEL, e)
    ov.pop("note", None)
    blob = json.dumps({"on": D.selected_layers(e), "opts": D.layer_options(e), "overlay": ov}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode()).hexdigest()


def test_cond_answer_is_selectable_only_and_leaves_the_arm_hashes():
    assert "cond_answer" in D.SELECTABLE and "cond_answer" not in D.ALL_LAYERS
    assert digest(env("d3")) == D3_HASH and digest(env("all")) == ALL_HASH and digest(env("d2")) == D2_HASH


def test_cond_answer_on_top_of_all_adds_its_keys_and_its_data_only():
    on = env(",".join(D.ALL_LAYERS + ("cond_answer",)))
    assert D.selected_layers(on) == D.ALL_LAYERS + ("cond_answer",)
    assert D.layer_options(on) == {**D.layer_options(env("all")), **KEYS}
    ov, base = D.d1_overlay({}, MODEL, on), D.d1_overlay({}, MODEL, env("all"))
    assert ov["planner"]["options"]["cond_goal"].pop("clauses") == D.ANSWER_NEGATION
    assert ov["planner"]["action_roles"]["open"] == base["planner"]["action_roles"]["open"] == "Open"
    ov.pop("note"), base.pop("note")
    assert ov == base


def test_cond_answer_off_none_selected_has_none_of_its_keys():
    for arm in ("all", "d3", "d2", "none"):
        assert not set(KEYS) & set(D.layer_options(env(arm)))


def test_cond_answer_data_is_labelled_assumed():
    assert D._labels(D.LAYERS["cond_answer"][1]) == ["assumed"]
    assert all(v.get("assumed") is True for v in D.ANSWER_NEGATION.values())


def test_answer_negation_words_read_made_up_answers():
    en, ko = (re.compile(D.ANSWER_NEGATION[lg]["negation"], re.I) for lg in ("en", "ko"))
    for t in ("It isn't in the crate.", "I don't think so", "No, it wasn't there", "you won't find it"):
        assert en.search(t), t
    for t in ("It is in the crate.", "The tin is on the bench.", "Yes, it's there"):
        assert not en.search(t), t
    for t in ("상자에 없어요.", "거기 안 있어요", "아니요, 못 봤어요"):
        assert ko.search(t), t
    for t in ("상자 안에 있어요.", "네, 의자 위에 있어요", ""):
        assert not ko.search(t), t
