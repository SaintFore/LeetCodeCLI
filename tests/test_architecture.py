from pathlib import Path


def test_production_adapters_only_use_the_public_application_service() -> None:
    root = Path(__file__).parents[1] / "leetcode_fsrs"
    sources = "\n".join(
        (root / name).read_text(encoding="utf-8") for name in ("cli.py", "tui.py")
    )

    for internal_name in (
        ".projection",
        ".config",
        ".store",
        ".config_path",
        ".scan_problems",
        ".semantic_errors",
        ".read_only",
    ):
        assert f"service{internal_name}" not in sources
