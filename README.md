PersonalMasker
===

## 概要
PersonalMasker は、テキスト中の個人情報（PII）を自動検出し、マスク処理を行うバックエンド API を提供します。v0.1.0 では REST API `/mask` を提供し、検出スパンの位置（元テキスト/マスク後テキストの両方）とマスク済みテキストを返します。

## クイックスタート
### 前提
- Docker / Docker Compose

### 起動
```bash
docker-compose up
```
- ヘルスチェック: `GET http://localhost:8000/health` → `{ "status": "healthy" }`
- OpenAPI: `docs/api/openapi.v1.json`
- FastAPI ドキュメント: `http://localhost:8000/docs`

### 例: マスキング API
- エンドポイント: `POST /mask`
- リクエスト例
```bash
curl -sS -X POST http://localhost:8000/mask \
  -H 'Content-Type: application/json' \
  -d '{
    "text": "東京都の太郎はメール taro@example.com に連絡した。",
    "targets": ["PERSON","LOCATION","ORGANIZATION","EMAIL","PHONE","URL"],
    "masking": {"replacement": "＊", "preserve_length": true}
  }'
```
- レスポンス（概要）
```json
{
  "original": "...",
  "masked": "...",
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
      "masked_end": 33
    }
  ]
}
```

### マスキングオプション
- `targets?: string[]`（既定: `[PERSON, LOCATION, ORGANIZATION, EMAIL, PHONE, URL]`）
- `masking?: { replacement?: string; preserve_length?: boolean; fixed_length?: number|null }`
  - `preserve_length=true`（既定）: 元の長さを維持
  - `fixed_length` 指定時: 常にその長さ
  - `preserve_length=false` かつ `fixed_length` 未指定: `replacement` を1回だけ
- `detected[].start_char/end_char`: 元テキスト基準
- `detected[].masked_start/masked_end`: マスク後テキスト基準

## 開発
### テスト/Lint（Docker コンテナ内実行）
- テスト: `make test`
- Lint: `make lint`
- フォーマット: `make fmt`

### OpenAPI の再生成
```bash
docker exec -w /usr/local/app personal \
  python backend/scripts/export_openapi.py --out docs/api/openapi.v1.json
```

## プロジェクトの状態（v0.1.0）
- 実装済み
  - `/mask` API（文分割 → GiNZA NER → 正規表現補完 → スパンマージ → マスク）
  - OpenAPI 固定化（`docs/api/openapi.v1.json`）
  - テスト（`backend/tests/...`）
  - Ruff（`backend/ruff.toml`）、CI（`.github/workflows/ruff.yml`）
- 今後
  - 文分割の精度チューニング
  - 追加エンティティ/ルール、ユーザ辞書の検討
  - フロントエンド/運用ドキュメントの拡充
