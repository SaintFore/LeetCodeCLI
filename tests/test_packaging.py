import hashlib
import subprocess
from pathlib import Path

ROOT = Path(__file__).parents[1]


def test_desktop_entry_launches_tui_in_a_terminal() -> None:
    entry = (ROOT / "packaging/desktop/leetcode-fsrs.desktop").read_text(
        encoding="utf-8"
    )

    assert "Type=Application" in entry
    assert "Exec=leetcode-fsrs" in entry
    assert "Icon=leetcode-fsrs" in entry
    assert "Terminal=true" in entry


def test_both_aur_packages_install_desktop_resources(tmp_path: Path) -> None:
    checksum = hashlib.sha256(b"release archive").hexdigest()
    rendered = tmp_path / "PKGBUILD"
    subprocess.run(
        [
            "python",
            str(ROOT / "scripts/render_aur_bin.py"),
            "2.0.0",
            checksum,
            "--output",
            str(rendered),
        ],
        check=True,
    )
    binary_package = rendered.read_text(encoding="utf-8")
    development_package = (ROOT / "packaging/aur-git/PKGBUILD").read_text(
        encoding="utf-8"
    )

    assert checksum in binary_package
    assert "SKIP" not in binary_package
    assert "arch=('x86_64')" in binary_package
    assert "/usr/bin/leetcode-fsrs" in binary_package
    for package in (binary_package, development_package):
        assert "/usr/share/applications/leetcode-fsrs.desktop" in package
        assert "/usr/share/icons/hicolor/1024x1024/apps/leetcode-fsrs.png" in package
