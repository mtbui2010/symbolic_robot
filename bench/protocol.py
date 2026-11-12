"""Pre-registration: the protocol file of a suite is hashed BEFORE the first episode; the hash goes in the results folder
(PROTOCOL_SHA256) and a later run into that folder refuses a changed protocol."""
from __future__ import annotations

import hashlib
from pathlib import Path

FILE = "PROTOCOL_SHA256"


def sha256_of(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def register(out: Path, protocol: Path | None, allow_change: bool = False) -> str:
    """Write the hash on the first run; on a later run check it. -> the hash ('' when the suite has no protocol file). Raises on a change."""
    if protocol is None:
        return ""
    h, f = sha256_of(protocol), Path(out) / FILE
    if f.exists():
        old = f.read_text().split()[0]
        if old != h and not allow_change:
            raise SystemExit(f"the protocol changed after its hash was recorded ({f}): {old[:12]} -> {h[:12]}; "
                             f"restore {protocol} or start a new results folder")
        return old
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(f"{h}  {Path(protocol).name}\n")
    return h


def verify(out: Path, protocol: Path) -> bool:
    f = Path(out) / FILE
    return f.exists() and f.read_text().split()[0] == sha256_of(protocol)
