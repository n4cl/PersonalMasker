"""
ルーター層のユニットテスト

- app.state.masker を Fake に置き換えてルートの入出力のみ検証
"""
from backend.app import app
from backend.services.masker import Span
from fastapi.testclient import TestClient


class _FakeMasker:
    def mask(
        self,
        text: str,
        targets: list[str] | None,  # noqa: ARG002 - テスト用Fakeのため未使用
        replacement: str,
        preserve_length: bool,
        fixed_length: int | None,  # noqa: ARG002 - テスト用Fakeのため未使用
    ) -> tuple[str, list[Span]]:
        # 固定のスパンを返す（EMAILとして [7, 11) をマスク）
        detected = [Span(start=7, end=11, label="EMAIL", text=text[7:11])]
        masked = text[:7] + (replacement * (4 if preserve_length else 1)) + text[11:]
        return masked, detected


def test_router_uses_app_state_masker() -> None:
    with TestClient(app) as client:
        client.app.state.masker = _FakeMasker()
        payload = {"text": "abcdefgWXYZhij"}
        res = client.post("/mask", json=payload)
        assert res.status_code == 200
        body = res.json()
        assert body["original"] == payload["text"]
        assert body["masked"][7:11] == "＊＊＊＊"
        assert any(d["label"] == "EMAIL" for d in body["detected"])
