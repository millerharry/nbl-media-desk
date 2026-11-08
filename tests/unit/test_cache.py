from pathlib import Path

import pytest

from nbl_media_desk.cache import GameCache


def test_round_trip(tmp_path: Path) -> None:
    cache = GameCache(tmp_path)
    path = cache.put("livestats", "123", {"a": 1})
    assert path == tmp_path / "livestats" / "123.json"
    assert cache.get("livestats", "123") == {"a": 1}
    assert not list(path.parent.glob("*.tmp"))


def test_missing_returns_none(tmp_path: Path) -> None:
    assert GameCache(tmp_path).get("livestats", "404") is None


@pytest.mark.parametrize("key", ["../etc", "a/b", "..", "", "x y"])
def test_unsafe_keys_rejected(tmp_path: Path, key: str) -> None:
    with pytest.raises(ValueError, match="unsafe cache key"):
        GameCache(tmp_path).get("livestats", key)


def test_non_object_payload_rejected(tmp_path: Path) -> None:
    (tmp_path / "livestats").mkdir()
    (tmp_path / "livestats" / "1.json").write_text("[1, 2]")
    with pytest.raises(ValueError, match="not a JSON object"):
        GameCache(tmp_path).get("livestats", "1")
