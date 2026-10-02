from pathlib import Path

import leetcode_fsrs


def test_pytest_imports_package_from_current_checkout() -> None:
    checkout_package = Path(__file__).resolve().parents[1] / "leetcode_fsrs"
    imported_package = Path(leetcode_fsrs.__file__).resolve().parent

    assert imported_package == checkout_package, (
        "pytest imported leetcode_fsrs outside the current checkout: "
        f"{imported_package}"
    )
