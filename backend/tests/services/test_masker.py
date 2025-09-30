"""
Masker サービスのユニットテスト（TDD）

- spaCy のロードや NER はモック/スタブ化し、サービスのロジックのみ検証
"""
from typing import Any

import pytest
from backend.app.services.masker import Masker, Span


class _FakeDoc:
    def __init__(self, ents: list[Any]):
        self.ents = ents


class _FakeEnt:
    """spaCy の Entity 互換スタブ"""

    def __init__(self, start_char: int, end_char: int, label: str) -> None:
        self.start_char = start_char
        self.end_char = end_char
        self.label_ = label


class _FakeNLP:
    """GiNZA の代替スタブ（テスト用）"""

    def __init__(self) -> None:
        self._ents: list[_FakeEnt] = []

    def set_ents(self, ents: list[_FakeEnt]) -> None:
        self._ents = ents

    def __call__(self, _text: str) -> _FakeDoc:  # noqa: D401, ARG002
        # 現在設定されているエンティティをそのまま返す
        return _FakeDoc(ents=self._ents)


@pytest.fixture
def masker(monkeypatch: pytest.MonkeyPatch) -> Masker:
    # spaCy のロードをスタブ化して、Masker 生成時の重い依存を回避
    fake_nlp = _FakeNLP()
    monkeypatch.setattr("spacy.load", lambda _name: fake_nlp)
    masker = Masker(model_name="ja_ginza")
    # テストから擬似 NER を書き換えられるように保持
    masker.nlp = fake_nlp
    return masker


def _find_span(detected: list[Span], label: str) -> Span:
    return next(s for s in detected if s.label == label)


def test_email_default_mask(masker: Masker) -> None:
    """EMAIL を既定設定でマスクし、長さ維持を確認する"""
    text = "東京都の太郎はメール taro@example.com に連絡した。"
    masked, detected = masker.mask(text=text, targets=["EMAIL"])  # NERは空→正規表現で検出
    s = _find_span(detected, "EMAIL")
    assert text[s.start:s.end] == "taro@example.com"
    # 既定: replacement="＊", preserve_length=True
    assert set(masked[s.start:s.end]) == {"＊"}
    assert len(masked[s.start:s.end]) == len("taro@example.com")


def test_fixed_length_option(masker: Masker) -> None:
    """EMAIL に fixed_length を指定したマスク長を検証する"""
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
    """preserve_length=False のときに置換文字が 1 回のみになる"""
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


def test_phone_mask_via_regex(masker: Masker) -> None:
    """PHONE を正規表現検出でマスクし、置換文字が繰り返される"""
    text = "連絡は 090-1234-5678 までお願いします。"
    masked, detected = masker.mask(text=text, targets=["PHONE"], replacement="X")
    phone_span = _find_span(detected, "PHONE")
    assert text[phone_span.start:phone_span.end] == "090-1234-5678"
    assert set(masked[phone_span.start:phone_span.end]) == {"X"}


def test_url_mask_via_regex(masker: Masker) -> None:
    """URL を正規表現検出でマスクし、? で埋められる"""
    text = "公式サイトは https://example.com/docs を参照してください。"
    masked, detected = masker.mask(text=text, targets=["URL"], replacement="?")
    url_span = _find_span(detected, "URL")
    assert text[url_span.start:url_span.end] == "https://example.com/docs"
    assert set(masked[url_span.start:url_span.end]) == {"?"}


def test_person_entity_mask_with_label_mapping(masker: Masker) -> None:
    """GiNZA の PER ラベルが PERSON にマップされてマスクされる"""
    masker.nlp.set_ents([_FakeEnt(start_char=0, end_char=2, label="PER")])
    text = "太郎は会議に参加した"
    masked, detected = masker.mask(text=text, targets=["PERSON"])
    person_span = _find_span(detected, "PERSON")
    assert text[person_span.start:person_span.end] == "太郎"
    assert set(masked[person_span.start:person_span.end]) == {"＊"}


def test_overlapping_entities_are_merged(masker: Masker) -> None:
    """重複する PERSON スパンがマージされ、1 度のマスクになる"""
    masker.nlp.set_ents(
        [
            _FakeEnt(start_char=0, end_char=2, label="PERSON"),
            _FakeEnt(start_char=1, end_char=3, label="PERSON"),
        ]
    )
    text = "山田太郎は出張中"
    masked, detected = masker.mask(text=text, targets=["PERSON"], replacement="◎")
    assert len(detected) == 2  # 元スパンは保持
    # マージ後は 0-3 を1度だけマスクし、元文字数分だけ繰り返される
    assert masked[:3] == "◎◎◎"
