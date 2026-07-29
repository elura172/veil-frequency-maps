from __future__ import annotations

import json
import os
from pathlib import Path

from .memory import TemporalMemory


class SessionStore:
    """Atomic local persistence for derived memory; never accepts audio."""

    def __init__(self, path: str | Path):
        self.path = Path(path).expanduser()

    def load_into(self, memory: TemporalMemory) -> bool:
        if not self.path.exists():
            return False
        data = json.loads(self.path.read_text(encoding="utf-8"))
        memory.restore_session(data)
        return True

    def save(self, memory: TemporalMemory) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.path.with_name(self.path.name + ".tmp")
        payload = json.dumps(memory.export_session(), indent=2, sort_keys=True) + "\n"
        temporary.write_text(payload, encoding="utf-8")
        os.replace(temporary, self.path)
