from pathlib import Path

from scripts.check_no_feed_data import FORBIDDEN_MARKERS, MAX_JSON_BYTES, find_violations


def test_large_json_outside_allowed_dirs_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    big = tmp_path / "data" / "game.json"
    big.write_text("x" * (MAX_JSON_BYTES + 1))
    assert find_violations(tmp_path, [Path("data/game.json")])


def test_large_json_in_golden_dir_is_allowed(tmp_path: Path) -> None:
    target = tmp_path / "evals" / "golden" / "g"
    target.mkdir(parents=True)
    (target / "game.json").write_text("x" * (MAX_JSON_BYTES + 1))
    assert not find_violations(tmp_path, [Path("evals/golden/g/game.json")])


def test_feed_urls_are_rejected(tmp_path: Path) -> None:
    (tmp_path / "notes.md").write_text(f"see https://{FORBIDDEN_MARKERS[-1]}.example/logo.jpg")
    assert find_violations(tmp_path, [Path("notes.md")])
