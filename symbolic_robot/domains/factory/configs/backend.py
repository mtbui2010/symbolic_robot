"""The robot the skill functions drive: get_backend() / set_backend(robot). Without one, a default episode of the default floor is built."""
from __future__ import annotations

_backend = None


def set_backend(robot) -> None:
    global _backend
    _backend = robot


def get_backend():
    global _backend
    if _backend is None:
        from ..episode import make_episode
        _backend = make_episode().robot
    return _backend


def reset_backend() -> None:
    global _backend
    _backend = None
