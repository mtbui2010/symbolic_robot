"""The scripted person that answers the robot's questions from OUTSIDE the server (through the API), by an answer policy:
knows | unknown | wrong, and the messy scripts of messy.py (a task carries `script`). Written for this repo; no rule, phrase list or
probability of any benchmark is used. (user.py is the same idea inside the simulator, for `--dialogue sim`.)"""
from __future__ import annotations

import re

_CONFIRM = re.compile(r"is that right|right\?|correct\?|did you mean|\b(?:ok|okay)\?|should i (?:do|go ahead)|say yes|please confirm", re.I)
_DEST_WORDS = re.compile(r"\b(?:put|bring|take|deliver|place|go to|leave)\b", re.I)


def answer_for(task: dict, question: str, n_where: int) -> tuple:
    """(answer text, kind, grounded). `grounded` is "" for the old policies; a task with a `script` (messy.py) gives its n-th answer."""
    text, kind = _answer(task, question, n_where)
    if kind == "source" and task.get("script"):
        a = task["script"][min(n_where, len(task["script"]) - 1)]
        return a["text"], kind, a["grounded"]
    return text, kind, ""


_CLARIFY = re.compile(r"which room, or which piece of furniture", re.I)       # the engine's clarifying question (ask_source: clarify_unusable)


def _answer(task: dict, question: str, n_where: int) -> tuple:
    """(answer text, kind) of the scripted person. kind: source | dest | confirm | which | other.
    A where-question is read first ('Where should I put it?' is a destination question, 'Where is the X?' a source question)."""
    s = question.lower()
    if _CLARIFY.search(s):                                 # asks again where the object is: the person's next scripted answer
        return f"It is on {task['true_text']}.", "source"
    if "where" in s:
        if _DEST_WORDS.search(s) and "where is" not in s:
            return f"On {task['dest_text']}.", "dest"
        pol = task.get("policy") or "knows"
        if pol == "unknown":
            return "I do not know.", "source"
        if pol == "wrong" and n_where == 0:
            return f"I think it is on {task['wrong_text']}.", "source"
        return f"It is on {task['true_text']}.", "source"
    if _CONFIRM.search(s):
        return "Yes.", "confirm"
    if "which" in s:
        return f"The {task['object']}.", "which"
    return "Yes.", "other"


