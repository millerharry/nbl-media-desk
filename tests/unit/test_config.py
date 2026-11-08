import pytest

from nbl_media_desk.config import Settings


def test_defaults_use_current_claude_models(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    settings = Settings(_env_file=None)
    assert settings.writer_model == "claude-opus-5-5"
    assert settings.extractor_model == "claude-haiku-5-5"
    assert settings.anthropic_api_key is None


def test_api_key_is_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-test-not-real")
    settings = Settings(_env_file=None)
    assert settings.anthropic_api_key is not None
    assert "sk-test-not-real" not in repr(settings)


def test_env_prefix_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("NBL_DESK_MAX_REPAIR_ROUNDS", "1")
    assert Settings(_env_file=None).max_repair_rounds == 1
