"""The factory's fault profiles (profiles/<name>.yaml); `ideal` is derived from `real` (no failures), `stress` from its `derive` entry."""
from __future__ import annotations

from pathlib import Path

from ... import profile as P

PROFILE_DIR = Path(__file__).with_name("profiles")


def load_profile(name: str):
    return P.load(PROFILE_DIR, name)


def list_profiles() -> list:
    return P.available(PROFILE_DIR)
