from pathlib import Path

import pytest

from leetcode_fsrs.config import LocalConfig
from leetcode_fsrs.services import ApplicationService


@pytest.fixture
def service(tmp_path: Path) -> ApplicationService:
    application = ApplicationService(
        LocalConfig(),
        config_path=tmp_path / "config.json",
        database_path=tmp_path / "projection.sqlite3",
    )
    application.initialize_library(tmp_path / "shared", "Asia/Shanghai", "alice")
    return application
