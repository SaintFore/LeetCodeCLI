"""Local, device-specific configuration and XDG paths."""

from __future__ import annotations

import json
import os
import shlex
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path

APP_NAME = "leetcode-fsrs"


def config_home() -> Path:
    return Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config")) / APP_NAME


def data_home() -> Path:
    return (
        Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share")) / APP_NAME
    )


@dataclass(slots=True)
class LocalConfig:
    shared_dir: str = ""
    device_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    solver_argv: list[str] = field(default_factory=lambda: ["nvim", "+Leet"])

    @classmethod
    def load(cls, path: Path | None = None) -> LocalConfig:
        path = path or config_home() / "config.json"
        if not path.exists():
            return cls()
        data = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            shared_dir=str(data.get("shared_dir", "")),
            device_id=str(data.get("device_id") or uuid.uuid4()),
            solver_argv=list(data.get("solver_argv") or ["nvim", "+Leet"]),
        )

    def save(self, path: Path | None = None) -> None:
        path = path or config_home() / "config.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(".tmp")
        temporary.write_text(
            json.dumps(asdict(self), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        temporary.replace(path)

    @property
    def shared_path(self) -> Path | None:
        return Path(self.shared_dir).expanduser() if self.shared_dir else None

    def set_solver_command(self, command: str) -> None:
        self.solver_argv = shlex.split(command)
