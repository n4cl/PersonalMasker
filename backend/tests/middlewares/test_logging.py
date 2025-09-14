"""
アクセスログミドルウェアのユニットテスト（TDD）

- 目的: FastAPI リクエスト/レスポンスの基本項目がログされること
- PII保護: 既定では原文本文(text)はログに含めない
- デバッグ時: 環境変数で有効化した場合のみ原文本文をログに含める
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from typing import Any

import pytest
from backend.app import app
from backend.middlewares.logging import setup_access_log_middleware
from backend.services.masker import Span
from fastapi.testclient import TestClient


class _FakeMasker:
    """ルーターの動作を軽量化するための簡易スタブ。"""

    def mask(  # noqa: ARG002 - テスト用の未使用引数を許容
        self,
        text: str,
        targets: list[str] | None,
        replacement: str,
        preserve_length: bool,
        fixed_length: int | None,
    ) -> tuple[str, list[Span]]:
        # 未使用引数を明示的に参照して Lint を抑制
        _ = (targets, fixed_length)
        # 固定スパン1件（[7, 11)）を返す
        detected = [Span(start=7, end=11, label="EMAIL", text=text[7:11])]
        masked = text[:7] + (replacement * (4 if preserve_length else 1)) + text[11:]
        return masked, detected


@pytest.fixture(autouse=True)
def _reset_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """テスト間でログ関連の環境変数をリセット。"""
    for k in ["LOG_JSON", "LOG_LEVEL", "LOG_DEBUG_BODY", "LOG_BODY_MAX", "LOG_SAMPLE"]:
        if k in os.environ:
            monkeypatch.delenv(k, raising=False)


def _digest(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def test_access_log_basic_without_body(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    """
    既定（LOG_DEBUG_BODY=false）では原文本文はログに含まず、ダイジェストのみ。
    """
    monkeypatch.setenv("LOG_JSON", "true")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("LOG_DEBUG_BODY", "false")
    monkeypatch.setenv("LOG_BODY_MAX", "64")

    setup_access_log_middleware(app)
    # 起動時の Masker 生成を軽量スタブへ差し替え（TestClient 起動前に適用）
    monkeypatch.setattr("backend.app.Masker", lambda *_args, **_kwargs: _FakeMasker())

    with TestClient(app) as client:
        client.app.state.masker = _FakeMasker()
        body = {"text": "太郎のメールは taro@example.com です。"}
        expect_digest = _digest(body["text"])

        caplog.set_level(logging.INFO, logger="app.access")
        res = client.post("/mask", json=body)
        assert res.status_code == 200

        # JSONメッセージを直接パース（caplog.records から message を取得）
        found_out = False
        found_in = False
        for rec in caplog.records:
            if rec.name != "app.access":
                continue
            try:
                obj: dict[str, Any] = json.loads(rec.getMessage())
            except Exception:  # noqa: BLE001
                continue
            # 完了ログ（OUT）のみを対象に検証
            if obj.get("path") == "/mask" and obj.get("event") == "OUT":
                assert obj.get("method") == "POST"
                assert obj.get("status") == 200
                # OUT では本文要約は出さない（digest/len ともに不要）
                assert "req_body_digest" not in obj
                assert "req_body" not in obj
                found_out = True
            # 開始ログ（IN）で長さ/ダイジェストを検証
            if obj.get("path") == "/mask" and obj.get("event") == "IN":
                assert obj.get("method") == "POST"
                assert obj.get("req_body_digest") == expect_digest
                assert obj.get("req_body_len") == len(body["text"]) + 0
                assert "req_body" not in obj
                found_in = True
        assert found_out, "OUT ログが見つかりませんでした"
        assert found_in, "IN ログが見つかりませんでした"
        # ログ全体にも本文は含まれない
        assert "太郎のメールは" not in caplog.text


def test_access_log_with_debug_body(monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture) -> None:
    """
    デバッグ時（LOG_DEBUG_BODY=true）は原文本文をログに含める。
    """
    monkeypatch.setenv("LOG_JSON", "true")
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    monkeypatch.setenv("LOG_DEBUG_BODY", "true")
    monkeypatch.setenv("LOG_BODY_MAX", "256")

    setup_access_log_middleware(app)
    monkeypatch.setattr("backend.app.Masker", lambda *_args, **_kwargs: _FakeMasker())

    with TestClient(app) as client:
        client.app.state.masker = _FakeMasker()
        body = {"text": "太郎のメールは taro@example.com です。"}

        caplog.set_level(logging.INFO, logger="app.access")
        res = client.post("/mask", json=body)
        assert res.status_code == 200

        # 本文がどこかのログ行に含まれること（JSONの req_body に入る）
        included = False
        in_has_len = False
        for rec in caplog.records:
            if rec.name != "app.access":
                continue
            try:
                obj: dict[str, Any] = json.loads(rec.getMessage())
            except Exception:  # noqa: BLE001
                continue
            if obj.get("path") == "/mask" and isinstance(obj.get("req_body"), str):
                if "太郎のメールは" in obj["req_body"]:
                    included = True
            if obj.get("path") == "/mask" and obj.get("event") == "IN":
                if obj.get("req_body_len") == len(body["text"]) + 0:
                    in_has_len = True
        assert included, "デバッグ時の本文ログが見つかりませんでした"
        assert in_has_len, "デバッグ時の IN ログに req_body_len がありません"
