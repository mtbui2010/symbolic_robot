"""The D1 layer ``cond_schema``, round 1: its extraction prompt says the base prompt's ``present`` sentence word for word for a presence condition
(``COND_PRESENT`` is cut from ``COND_PROMPT``), and a question kind (state / unobservable) gets its own polarity sentence, so no "the answer is yes"
clause reaches a presence condition. The base ``COND_PROMPT`` and the arm hashes are unchanged. Pure data: no run, no model."""
import hashlib

from bench.suites.home.planners import d1_options as D
from tests.home.bench.test_cond_answer_layer import ALL_HASH, D2_HASH, D3_HASH, MODEL, digest, env

COND_PROMPT_SHA = "43dd99f8bb99b266788c93c29c37c57a81e58c080fafd1f542009e4c28e766eb"     # COND_PROMPT before round 1 (f251adc)


def test_cond_schema_polarity_off_the_base_prompt_and_the_arm_hashes_are_unchanged():
    assert hashlib.sha256(D.COND_PROMPT.encode()).hexdigest() == COND_PROMPT_SHA
    assert digest(env("d3")) == D3_HASH and digest(env("all")) == ALL_HASH and digest(env("d2")) == D2_HASH
    ce = D.d1_overlay({}, MODEL, env(",".join(D.ALL_LAYERS + ("cond_answer",))))["planner"]["options"]["cond_extract"]
    assert ce["prompt"] == D.COND_PROMPT


def test_cond_schema_polarity_empty_the_present_sentence_is_cut_from_the_base_prompt():
    assert D.COND_PRESENT.startswith("present:") and D.COND_PRESENT.strip() and D.COND_PRESENT in D.COND_PROMPT


def test_the_kinds_prompt_says_the_base_present_sentence_unchanged():
    assert D.COND_PRESENT in D.COND_PROMPT_KINDS
    assert "yes" not in D.COND_PRESENT and "answer" not in D.COND_PRESENT                   # no question wording in the presence sentence


def test_a_question_kind_has_its_own_polarity_sentence():
    rest = D.COND_PROMPT_KINDS.replace(D.COND_PRESENT, "")
    assert "present" in rest and "yes means the condition holds" in rest
    assert "or the answer is yes" not in D.COND_PROMPT_KINDS                                 # the shared clause of before


def test_regression_the_presence_sentence_is_not_mixed_with_the_question_polarity():
    i = D.COND_PROMPT_KINDS.index(D.COND_PRESENT)
    assert D.COND_PROMPT_KINDS[i:i + len(D.COND_PRESENT)] == D.COND_PRESENT and D.COND_PROMPT_KINDS.count("present: true") == 1
    assert D.COND_PROMPT_KINDS.format(request="r", goals="g")                                # the two slots still format
