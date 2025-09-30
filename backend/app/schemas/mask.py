from typing import Optional  # noqa: F401 - 互換注釈のための残置（型の説明で使用）

from pydantic import BaseModel, ConfigDict, Field


class Entity(BaseModel):
    label: str
    text: str
    start_char: int
    end_char: int
    masked_start: int
    masked_end: int


class MaskRequest(BaseModel):
    text: str
    # マスク対象とするラベルの一覧（省略時は既定集合）
    targets: list[str] | None = Field(
        default=None,
        description=(
            "マスク対象とするエンティティラベル。省略時は"
            "[PERSON, LOCATION, ORGANIZATION, EMAIL, PHONE, URL] を使用"
        ),
    )
    # マスク方法の指定（置換文字・長さ保持など）
    class MaskingOptions(BaseModel):
        replacement: str = Field(
            default="＊",
            description="マスク置換に用いる文字列（1文字以上）",
            min_length=1,
        )
        preserve_length: bool = Field(
            default=True, description="マスク後も元テキスト長を維持するか"
        )
        fixed_length: int | None = Field(
            default=None,
            ge=0,
            description=(
                "指定時はスパン長に関わらず、この固定長でマスク（preserve_length より優先）"
            ),
        )

    masking: MaskingOptions | None = Field(
        default=None, description="マスク方法のオプション"
    )

    # Pydantic v2 設定
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "東京都の太郎はメール taro@example.com に連絡した。",
                "targets": [
                    "PERSON",
                    "LOCATION",
                    "ORGANIZATION",
                    "EMAIL",
                    "PHONE",
                    "URL",
                ],
                "masking": {"replacement": "＊", "preserve_length": True},
            }
        }
    )


class MaskResponse(BaseModel):
    original: str
    masked: str
    detected: list[Entity]

    # Pydantic v2 設定
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "original": "東京都の太郎はメール taro@example.com に連絡した。",
                "masked": "＊＊＊の＊＊はメール *************** に連絡した。",
                "detected": [
                    {
                        "label": "PERSON",
                        "text": "太郎",
                        "start_char": 4,
                        "end_char": 6,
                        "masked_start": 4,
                        "masked_end": 6
                    },
                    {
                        "label": "EMAIL",
                        "text": "taro@example.com",
                        "start_char": 11,
                        "end_char": 27,
                        "masked_start": 11,
                        "masked_end": 27
                    },
                ],
            }
        }
    )
