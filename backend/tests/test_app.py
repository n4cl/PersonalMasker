"""
アプリ起動テスト

- startup で Masker が設定されることを確認（Masker をモックして軽量化）
"""
from __future__ import annotations

from backend.app import app
from fastapi.testclient import TestClient


class _DummyMasker:
    def __init__(self, model_name: str = "ja_ginza") -> None:  # noqa: D401
        self.model_name = model_name


def test_startup_sets_masker(monkeypatch) -> None:
    monkeypatch.setattr("backend.app.Masker", _DummyMasker)
    with TestClient(app) as client:
        assert hasattr(client.app.state, "masker")
        assert isinstance(client.app.state.masker, _DummyMasker)
