"""
Masker サービスのユニットテスト（TDD）

- spaCy のロードや NER はモック/スタブ化し、サービスのロジックのみ検証
"""
from typing import Any

import pytest
from backend.services.masker import Masker, Span


class _FakeDoc:
    def __init__(self, ents: list[Any]):
        self.ents = ents


class _FakeNLP:
    """GiNZA の代替スタブ（テスト用）"""

    def __call__(self, _text: str) -> _FakeDoc:  # noqa: D401, ARG002
        # 既定では NER を空にして、正規表現ルートを検証
        return _FakeDoc(ents=[])


@pytest.fixture
def masker(monkeypatch: pytest.MonkeyPatch) -> Masker:
    # spaCy のロードをスタブ化して、Masker 生成時の重い依存を回避
    monkeypatch.setattr("spacy.load", lambda _name: _FakeNLP())
    return Masker(model_name="ja_ginza")


def _find_span(detected: list[Span], label: str) -> Span:
    return next(s for s in detected if s.label == label)


def test_email_default_mask(masker: Masker) -> None:
    text = "東京都の太郎はメール taro@example.com に連絡した。"
    masked, detected = masker.mask(text=text, targets=["EMAIL"])  # NERは空→正規表現で検出
    s = _find_span(detected, "EMAIL")
    assert text[s.start:s.end] == "taro@example.com"
    # 既定: replacement="＊", preserve_length=True
    assert set(masked[s.start:s.end]) == {"＊"}
    assert len(masked[s.start:s.end]) == len("taro@example.com")


def test_fixed_length_option(masker: Masker) -> None:
    text = "連絡先は taro@example.com です。"
    masked, detected = masker.mask(
        text=text,
        targets=["EMAIL"],
        replacement="*",
        fixed_length=4,
    )
    s = _find_span(detected, "EMAIL")
    # 元オフセットは維持。マスク後の長さは fixed_length に従う
    assert masked[s.start : s.start + 4] == "****"


def test_preserve_length_false(masker: Masker) -> None:
    text = "メールは taro@example.com に。"
    masked, detected = masker.mask(
        text=text,
        targets=["EMAIL"],
        replacement="#",
        preserve_length=False,
    )
    s = _find_span(detected, "EMAIL")
    # preserve_length=False の時は replacement を1回だけ
    assert masked[s.start : s.start + 1] == "#"


