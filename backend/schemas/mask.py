from typing import List

from pydantic import BaseModel


class Entity(BaseModel):
    label: str
    text: str
    start_char: int
    end_char: int


class MaskRequest(BaseModel):
    text: str

    class Config:
        json_schema_extra = {
            "example": {
                "text": "東京都の太郎はメール taro@example.com に連絡した。"
            }
        }


class MaskResponse(BaseModel):
    original: str
    masked: str
    detected: List[Entity]

    class Config:
        json_schema_extra = {
            "example": {
                "original": "東京都の太郎はメール taro@example.com に連絡した。",
                "masked": "＊＊＊の＊＊はメール *************** に連絡した。",
                "detected": [
                    {"label": "PERSON", "text": "太郎", "start_char": 4, "end_char": 6},
                    {"label": "EMAIL", "text": "taro@example.com", "start_char": 11, "end_char": 27},
                ],
            }
        }
