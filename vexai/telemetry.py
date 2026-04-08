import json
from collections import deque
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional


@dataclass
class MemoryReplayBuffer:
    max_records: int = 500
    records: Deque[Dict[str, Any]] = field(default_factory=deque)

    def append(self, record: Dict[str, Any]) -> None:
        self.records.append(record)
        while len(self.records) > self.max_records:
            self.records.popleft()


class JsonlReplayLogger:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a", encoding="utf-8")

    def write(self, record: Dict[str, Any]) -> None:
        self._handle.write(json.dumps(record, sort_keys=True) + "\n")
        self._handle.flush()

    def close(self) -> None:
        self._handle.close()


class ConsoleMirrorLogger:
    def __init__(self, enabled: bool = True):
        self.enabled = enabled

    def write(self, record: Dict[str, Any]) -> None:
        if self.enabled:
            print(json.dumps(record, sort_keys=True))


@dataclass(frozen=True)
class ReplayLoadResult:
    valid: List[Dict[str, Any]]
    invalid: List[Dict[str, Any]]


def load_replay_records(path: Path) -> ReplayLoadResult:
    path = Path(path)
    valid = []
    invalid = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw_line.strip():
            continue
        try:
            parsed = json.loads(raw_line)
        except json.JSONDecodeError as exc:
            invalid.append({"line": line_number, "error": str(exc)})
            continue
        if "t_ms" not in parsed or "robot_local" not in parsed or "field" not in parsed:
            invalid.append({"line": line_number, "error": "missing required fields"})
            continue
        valid.append(parsed)
    return ReplayLoadResult(valid=valid, invalid=invalid)
