from fastapi import APIRouter, HTTPException

from backend.schemas.mask import MaskRequest, MaskResponse

router = APIRouter(prefix="/mask", tags=["mask"])


@router.post(
    "",
    response_model=MaskResponse,
    summary="テキスト中の個人情報をマスク",
    description=(
        "設計段階: プレーンテキストを受け取り、マスク済みテキストと検出エンティティを返す想定です。"
        "現時点では未実装のため 501 を返します。"
    ),
    responses={
        200: {"description": "マスク結果（将来実装）"},
        501: {"description": "未実装"},
    },
)
async def mask_text(payload: MaskRequest):
    # Contract-first stub. To be implemented in subsequent issues.
    raise HTTPException(status_code=501, detail="未実装")
