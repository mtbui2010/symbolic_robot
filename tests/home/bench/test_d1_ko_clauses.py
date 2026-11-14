"""The ASSUMED Korean clause words of the D1 ``lang_words`` layer: they take out real conditions and negations, and leave requests and nouns alone.
Made-up words are used where the point is a noun that merely ends like a conditional (the class), plus plain request sentences."""
import re

from bench.suites.home.planners.d1_options import KO_CONDITION, KO_NEGATION

COND, NEG = re.compile(KO_CONDITION, re.I), re.compile(KO_NEGATION, re.I)


def active(text):
    return " ".join(NEG.sub(" ", COND.sub(" ", text)).split())


def test_a_request_of_the_form_myeon_dwae_or_johgesseo_is_not_a_condition():
    for t in ("머그컵을 식탁에 놓으면 돼", "컵을 서랍에 넣어 주면 좋겠어", "이것만 치우면 돼", "문을 닫으면 괜찮아"):
        assert active(t) == t, t


def test_a_noun_that_ends_in_myeon_or_ji_is_left_in_the_request():
    for t in ("수건을 화면 옆에 둬", "TV 화면 앞에 리모컨을 놓아 줘", "라면 가져다 줘", "바지 말려줘", "바지를 세탁기에 넣어 줘"):
        assert active(t) == t, t


def test_a_real_condition_and_a_real_negation_are_taken_out():
    assert "냉장고" not in active("냉장고 문이 열려 있으면 우유를 꺼내 줘") and "우유를 꺼내 줘" in active("냉장고 문이 열려 있으면 우유를 꺼내 줘")
    assert "만약" not in active("만약 불이 켜져 있으면, 컵을 놓아 줘") and "컵을 놓아 줘" in active("만약 불이 켜져 있으면, 컵을 놓아 줘")
    assert "램프" not in active("컵을 식탁에 놓아 줘. 램프는 만지지 마")
    assert "소파" not in active("컵을 식탁에 놓고 소파는 건드리지 말고")


def test_the_condition_words_and_negation_words_have_no_label_dependency_empty():
    for t in ("", "컵을 놓아 줘", "put the cup on the table"):
        assert active(t) == t
