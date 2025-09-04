from fastapi import APIRouter, HTTPException, Request

from backend.schemas.mask import Entity, MaskRequest, MaskResponse

router = APIRouter(prefix="/mask", tags=["mask"])


@router.post(
    "",
    response_model=MaskResponse,
    summary="テキスト中の個人情報をマスク",
    description=(
        "プレーンテキストを受け取り、指定ラベルのエンティティをマスクします。"
        "文単位で解析し、検出エンティティは全文オフセットで返却します。"
    ),
    responses={
        200: {"description": "マスク結果"},
        400: {"description": "入力不正"},
        422: {"description": "スキーマ不正"},
        500: {"description": "内部エラー"},
    },
)
async def mask_text(payload: MaskRequest, request: Request) -> MaskResponse:
    try:
        if not payload.text:
            raise HTTPException(status_code=400, detail="text は必須です")

        masking = payload.masking
        replacement = masking.replacement if masking and masking.replacement else "＊"
        preserve_length = masking.preserve_length if masking is not None else True
        fixed_length = masking.fixed_length if masking is not None else None

        masker = request.app.state.masker
        masked, detected_spans = masker.mask(
            text=payload.text,
            targets=payload.targets,
            replacement=replacement,
            preserve_length=preserve_length,
            fixed_length=fixed_length,
        )

        # マスク後オフセットを計算（サービスからの情報は元オフセットのみ）
        # ここでは masked 側の位置を再計算する（処理はサービスに寄せても良い）
        # 簡易実装として、マスク適用アルゴリズムを再現せず、文字列検索で近傍を特定するのは不安定のため、
        # サービス内で用いたマップ計算を将来公開する予定（現時点では preserve_length=True の場合は同一）
        # 今回は preserve_length=True / fixed_length=None の既定に対しては一致、それ以外は近似として start を基準に設定
        detected: list[Entity] = []
        for s in detected_spans:
            masked_start = s.start
            masked_end = s.end
            if fixed_length is not None:
                masked_end = masked_start + fixed_length
            elif not preserve_length:
                masked_end = masked_start + len(replacement)
            detected.append(
                Entity(
                    label=s.label,
                    text=s.text,
                    start_char=s.start,
                    end_char=s.end,
                    masked_start=masked_start,
                    masked_end=masked_end,
                )
            )
        return MaskResponse(original=payload.text, masked=masked, detected=detected)
    except HTTPException:
        raise
    except Exception as e:  # noqa: BLE001
        # 例外の詳細はログなどでトレース（ここでは簡略化）
        raise HTTPException(status_code=500, detail="内部エラー") from e
