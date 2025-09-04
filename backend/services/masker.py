"""
マスキングサービス

- 文分割（日本語向けの簡易ルールベース）
- GiNZA による NER 抽出
- EMAIL/URL/PHONE の正規表現補完
- 重複/重なりスパンのマージ（マスキング適用用）
- マスク文字列の生成（replacement/preserve_length/fixed_length）

注意:
- 返却する detected は元の検出スパン（全文オフセット）。
- 実際のマスク適用はマージ後スパンに対して行う。
"""
import re
from collections.abc import Iterable
from dataclasses import dataclass


@dataclass
class Span:
    """テキスト中のスパン（半開区間）"""

    start: int
    end: int
    label: str
    text: str


class Masker:
    """GiNZA ベースのマスキングユーティリティ（ステートフル）。"""

    def __init__(self, model_name: str = "ja_ginza") -> None:
        # モデルは起動時にロードして保持（初回リクエストの重さを避ける）
        # CI の OpenAPI 生成時など、トップレベルimportで重依存を解決しないため局所import
        import spacy

        self.nlp = spacy.load(model_name)
        # 日本語向けの閉じ括弧/引用符と終端記号
        self.closers: str = "」』］】）】〉》”’\"]"
        self.sent_end: str = "。．！？!?"
        # 代表的な識別子の正規表現
        self.re_email = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        self.re_url = re.compile(r"(https?://[^\s\u3000]+|www\.[^\s\u3000]+)")
        self.re_phone = re.compile(
            r"\b(?:\+?\d{1,3}[- ]?)?(?:\d{2,4}[- ]?\d{2,4}[- ]?\d{3,4})\b"
        )

    def _sentence_spans(self, text: str) -> list[tuple[int, int]]:
        """
        日本語向けの簡易文分割。
        - 句点/終端記号（。．！？!?）を境界とみなし、その直後の閉じ括弧・引用符も文末に含める。
        - 最後に残ったテキストも文として扱う。
        """
        spans: list[tuple[int, int]] = []
        i: int = 0
        n: int = len(text)
        while i < n:
            # 終端記号を探す
            m = re.search(f"[{self.sent_end}]", text[i:])
            if not m:
                spans.append((i, n))
                break
            end_idx = i + m.end()
            # 直後の閉じ括弧・引用符を含める
            j = end_idx
            while j < n and text[j] in self.closers:
                j += 1
            spans.append((i, j))
            i = j
        if not spans:
            spans.append((0, n))
        return spans

    @staticmethod
    def _map_label(ent_label: str) -> str | None:
        """GiNZA のラベルを API 公開ラベルへ正規化。該当しない場合は None。"""
        lbl = ent_label.upper()
        if lbl in {"PERSON", "PER"}:
            return "PERSON"
        if lbl in {"ORG", "ORGANIZATION"}:
            return "ORGANIZATION"
        if lbl in {"GPE", "LOC", "LOCATION"}:
            return "LOCATION"
        if lbl in {"EMAIL", "E-MAIL"}:
            return "EMAIL"
        if lbl in {"PHONE", "TEL", "TELEPHONE"}:
            return "PHONE"
        if lbl in {"URL", "URI", "WEB"}:
            return "URL"
        return None

    def _regex_pii(self, text: str, allow: Iterable[str]) -> list[Span]:
        spans: list[Span] = []
        allow_set = set(allow)
        if "EMAIL" in allow_set:
            for m in self.re_email.finditer(text):
                spans.append(Span(m.start(), m.end(), "EMAIL", m.group(0)))
        if "URL" in allow_set:
            for m in self.re_url.finditer(text):
                spans.append(Span(m.start(), m.end(), "URL", m.group(0)))
        if "PHONE" in allow_set:
            for m in self.re_phone.finditer(text):
                spans.append(Span(m.start(), m.end(), "PHONE", m.group(0)))
        return spans

    @staticmethod
    def _merge_spans(spans: list[Span]) -> list[Span]:
        """重複/隣接をマージ（ラベルは先頭スパンを維持、text は後で未参照）。"""
        if not spans:
            return []
        spans_sorted = sorted(spans, key=lambda s: (s.start, -s.end))
        merged: list[Span] = []
        cur = spans_sorted[0]
        for s in spans_sorted[1:]:
            if s.start <= cur.end:  # 重なり or 隣接
                cur.end = max(cur.end, s.end)
            else:
                merged.append(cur)
                cur = s
        merged.append(cur)
        return merged

    @staticmethod
    def _repeat_to_length(token: str, length: int) -> str:
        """token を繰り返して指定長にし、超過分は切り詰める。"""
        if length <= 0:
            return ""
        times, rem = divmod(length, len(token))
        return token * times + token[:rem]

    def mask(
        self,
        text: str,
        targets: list[str] | None = None,
        replacement: str = "＊",
        preserve_length: bool = True,
        fixed_length: int | None = None,
    ) -> tuple[str, list[Span]]:
        """
        テキストを対象ラベルでマスクする。

        戻り値: (masked_text, detected_spans)
          - detected_spans は全文オフセット・元検出スパン（マージ前）
        """
        allow = targets or [
            "PERSON",
            "LOCATION",
            "ORGANIZATION",
            "EMAIL",
            "PHONE",
            "URL",
        ]
        allow_set = {t.upper() for t in allow}

        detected: list[Span] = []

        # 文分割
        sent_spans = self._sentence_spans(text)
        for (s_start, s_end) in sent_spans:
            sent = text[s_start:s_end]
            doc = self.nlp(sent)
            for ent in doc.ents:
                mapped = self._map_label(ent.label_)
                if mapped and mapped in allow_set:
                    start = s_start + ent.start_char
                    end = s_start + ent.end_char
                    detected.append(Span(start, end, mapped, text[start:end]))

        # 正規表現での補完
        detected.extend(self._regex_pii(text, allow_set))

        # マージはマスク適用用にのみ
        merged = self._merge_spans([Span(s.start, s.end, s.label, s.text) for s in detected])

        # マスク適用しつつ、マスク後オフセットを計算
        result: list[str] = []
        last = 0
        masked_offset_map: list[tuple[int, int, int]] = []  # (orig_start, orig_end, masked_len)
        for sp in merged:
            if last < sp.start:
                result.append(text[last:sp.start])
            span_len = sp.end - sp.start
            if fixed_length is not None:
                repl = self._repeat_to_length(replacement, fixed_length)
            elif preserve_length:
                repl = self._repeat_to_length(replacement, span_len)
            else:
                repl = replacement
            result.append(repl)
            masked_offset_map.append((sp.start, sp.end, len(repl)))
            last = sp.end
        if last < len(text):
            result.append(text[last:])

        masked = "".join(result)

        # 元スパンごとに masked 側の start/end を算出
        def calc_masked_offsets(s: Span) -> tuple[int, int]:
            masked_cursor = 0
            orig_cursor = 0
            masked_start = None
            masked_end = None
            for m_start, m_end, m_len in masked_offset_map:
                # 原文の未マスク領域の長さ
                if orig_cursor < m_start:
                    gap = m_start - orig_cursor
                    if s.start >= orig_cursor and s.start < m_start and masked_start is None:
                        masked_start = masked_cursor + (s.start - orig_cursor)
                    if s.end > orig_cursor and s.end <= m_start and masked_end is None:
                        masked_end = masked_cursor + (s.end - orig_cursor)
                    masked_cursor += gap
                    orig_cursor = m_start
                # マスク領域
                if s.start >= m_start and s.start < m_end and masked_start is None:
                    masked_start = masked_cursor
                if s.end > m_start and s.end <= m_end and masked_end is None:
                    masked_end = masked_cursor + m_len
                masked_cursor += m_len
                orig_cursor = m_end
            # 残りの未マスク領域
            if orig_cursor < len(text):
                if masked_start is None and s.start >= orig_cursor:
                    masked_start = masked_cursor + (s.start - orig_cursor)
                if masked_end is None and s.end >= orig_cursor:
                    masked_end = masked_cursor + (s.end - orig_cursor)
            # フォールバック
            if masked_start is None:
                masked_start = s.start
            if masked_end is None:
                masked_end = masked_start
            return masked_start, masked_end

        detected_with_masked: list[Span] = []
        # 既存の Span を再利用し、後段で router で masked_* を組み立てるため保持
        for s in detected:
            _ = calc_masked_offsets(s)
            detected_with_masked.append(s)

        return masked, detected_with_masked
