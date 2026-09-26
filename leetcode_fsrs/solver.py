"""Launch an external solver without coupling study data to an editor plugin."""

from __future__ import annotations

import os
import subprocess

from .domain import Question


def run_solver(argv: list[str], question: Question) -> int:
    if not argv:
        raise ValueError("Solver command is empty")
    values = {
        "key": question.key,
        "slug": question.slug,
        "url": question.url,
        "frontend_id": question.frontend_id,
    }
    command = [part.format_map(values) for part in argv]
    environment = os.environ.copy()
    environment.update(
        {
            "LEETCODE_FSRS_KEY": question.key,
            "LEETCODE_FSRS_SLUG": question.slug,
            "LEETCODE_FSRS_URL": question.url,
        }
    )
    return subprocess.run(command, env=environment, check=False).returncode
