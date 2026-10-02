#!/usr/bin/env python3
"""Render versioned AUR binary metadata from the release template."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("version")
    parser.add_argument("sha256")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", args.version):
        parser.error("version must have the form X.Y.Z")
    if not re.fullmatch(r"[0-9a-f]{64}", args.sha256):
        parser.error("sha256 must be 64 lowercase hexadecimal characters")

    root = Path(__file__).resolve().parent.parent
    template = root / "packaging/aur-bin/PKGBUILD.template"
    rendered = (
        template.read_text(encoding="utf-8")
        .replace("@VERSION@", args.version)
        .replace("@SHA256@", args.sha256)
    )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(rendered, encoding="utf-8")


if __name__ == "__main__":
    main()
