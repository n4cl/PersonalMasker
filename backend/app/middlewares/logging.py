"""
アクセスログ用ミドルウェア。

- FastAPI の入出力（メソッド/パス/ステータス/遅延など）を記録
- 既定では PII を含む原文本文は記録しない（ダイジェストと長さのみ）
- デバッグ時（`LOG_DEBUG_BODY=true`）のみ原文本文をログに含める

環境変数:
- LOG_JSON: true/false（JSON 形式で出力）
- LOG_LEVEL: INFO/DEBUG など（logging レベル）
- LOG_DEBUG_BODY: true/false（原文本文のログ許可。既定 false）
- LOG_BODY_MAX: 本文の最大記録長（既定 256）
- LOG_SAMPLE: サンプリング率 0.0〜1.0（既定 1.0）
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from datetime import datetime
from typing import Any

from fastapi import FastAPI, Request, Response


def _sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def setup_access_log_middleware(app: FastAPI) -> None:
    """
    アクセスログミドルウェアをアプリへ登録する（多重登録は回避）。
    """

    if getattr(app.state, "_access_log_installed", False):
        return

    logger = logging.getLogger("app.access")

    @app.middleware("http")
    async def access_log(request: Request, call_next) -> Response:  # type: ignore[override]
        start = time.perf_counter()

        # 設定（毎回読む: テストでの切替や動的変更に備える）
        log_json = os.getenv("LOG_JSON", "true").lower() == "true"
        debug_body = os.getenv("LOG_DEBUG_BODY", "false").lower() == "true"
        try:
            body_max = int(os.getenv("LOG_BODY_MAX", "256"))
        except Exception:  # noqa: BLE001
            body_max = 256
        try:
            sample = float(os.getenv("LOG_SAMPLE", "1.0"))
        except Exception:  # noqa: BLE001
            sample = 1.0

        # 低コストなサンプリング（簡易）: 現状は全件想定
        _ = sample  # 未使用（将来拡張）

        method = request.method
        path = request.url.path

        # リクエストID（ヘッダ優先、無ければ採番）
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        # 後段で参照できるように state にも保存
        request.state.request_id = request_id

        # タイムスタンプ（UTC, RFC3339）
        def _now_ts() -> str:
            # ローカルタイム（コンテナのTZに依存）でISO8601を出力
            return datetime.now().astimezone().isoformat(timespec="milliseconds")
        start_ts = _now_ts()

        # リクエスト本文の取得（JSON前提で text を抽出。失敗時は空扱い）
        req_text: str = ""
        try:
            raw = await request.body()
            # 本文を読み取った場合はダウンストリームでも参照できるように復元する
            # 1) キャッシュへ格納
            try:
                request._body = raw  # type: ignore[attr-defined]
            except Exception:  # noqa: BLE001
                pass
            # 2) 受信チャネルを差し替え（受信側が body() 以外で読む場合に備える）
            async def _receive() -> dict[str, Any]:
                return {"type": "http.request", "body": raw, "more_body": False}

            try:
                request._receive = _receive  # type: ignore[attr-defined]
            except Exception:  # noqa: BLE001
                pass
            if raw:
                # JSON を想定（/mask）
                try:
                    obj = json.loads(raw.decode("utf-8"))
                    if isinstance(obj, dict) and "text" in obj and isinstance(obj["text"], str):
                        req_text = obj["text"]
                except Exception:  # noqa: BLE001
                    # JSON でなければスキップ
                    req_text = ""
        except Exception:  # noqa: BLE001
            req_text = ""

        # 実行前ログ（IN）
        start_log: dict[str, Any] = {
            "logger": "app.access",
            "level": "INFO",
            "event": "IN",
            "request_id": request_id,
            "ts": start_ts,
            "method": method,
            "path": path,
        }
        if req_text:
            # 長さは常に記録（プレビュー有無に関わらず）
            start_log["req_body_len"] = len(req_text)
            if debug_body:
                start_log["req_body"] = req_text[:body_max]
                # 必要に応じてダイジェストも保持（整合性確認用）
                start_log["req_body_digest"] = _sha256_hex(req_text)
            else:
                start_log["req_body_digest"] = _sha256_hex(req_text)
        _emit(logger, start_log, log_json)

        # ルーティング実行
        response: Response
        try:
            response = await call_next(request)
            status = response.status_code
        except Exception as ex:  # noqa: BLE001
            status = 500
            # エラーもログして再送出
            end = time.perf_counter()
            latency_ms = int((end - start) * 1000)
            log_obj: dict[str, Any] = {
                "logger": "app.access",
                "level": "ERROR",
                "event": "OUT",
                "request_id": request_id,
                "ts": _now_ts(),
                "method": method,
                "path": path,
                "status": status,
                "latency_ms": latency_ms,
                "error": ex.__class__.__name__,
            }
            if debug_body and req_text:
                log_obj["req_body"] = req_text[:body_max]
            else:
                if req_text:
                    log_obj["req_body_digest"] = _sha256_hex(req_text)
                    log_obj["req_body_len"] = len(req_text)
            _emit(logger, log_obj, log_json)
            raise

        end = time.perf_counter()
        latency_ms = int((end - start) * 1000)

        # レスポンス本文を捕捉（後で新しい Response に包み直す）
        # まず既存レスポンスのヘッダ/属性を保持
        headers = dict(response.headers)
        headers.setdefault("X-Request-ID", request_id)

        body_bytes = b""
        if getattr(response, "body_iterator", None) is not None:
            async for chunk in response.body_iterator:  # type: ignore[attr-defined]
                body_bytes += chunk
        else:
            try:
                body_bytes = response.body  # type: ignore[attr-defined]
            except Exception:  # noqa: BLE001
                body_bytes = b""

        # リクエストログ（完了: OUT）
        log_obj = {
            "logger": "app.access",
            "level": "INFO",
            "event": "OUT",
            "request_id": request_id,
            "ts": _now_ts(),
            "method": method,
            "path": path,
            "status": status,
            "latency_ms": latency_ms,
        }
        # OUT ログは本文/ダイジェストともに出力しない（IN のみ記録）。

        _emit(logger, log_obj, log_json)

        # レスポンス付加情報（/mask のみ、masked 情報を安全に要約）
        if path == "/mask" and body_bytes:
            try:
                body_obj = json.loads(body_bytes.decode("utf-8"))
                if isinstance(body_obj, dict):
                    masked = body_obj.get("masked")
                    detected = body_obj.get("detected")
                    if isinstance(masked, str):
                        log_obj["masked_len"] = len(masked)
                        if debug_body:
                            log_obj["masked_preview"] = masked[:body_max]
                    if isinstance(detected, list):
                        log_obj["detected_count"] = len(detected)
            except Exception:  # noqa: BLE001
                pass

        # 包み直したレスポンスを返却
        return Response(
            content=body_bytes,
            status_code=status,
            headers=headers,
            media_type=response.media_type,
            background=getattr(response, "background", None),
        )

    app.state._access_log_installed = True


def _emit(logger: logging.Logger, payload: dict[str, Any], as_json: bool) -> None:
    """ロガーへ出力（JSON文字列 or テキスト）。"""
    if as_json:
        logger.info(json.dumps(payload, ensure_ascii=False))
    else:
        # テキスト整形（簡易）。キー:値 の並び。
        parts = [f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in payload.items()]
        logger.info(" ".join(parts))
