PersonalMasker
===

## 概要
PersonalMasker は、テキスト中の個人情報（PII）を自動検出し、マスク処理を行うバックエンド API を提供します。

## クイックスタート
### 前提
- Docker / Docker Compose

### 起動
```bash
docker compose up
```
- ヘルスチェック: `GET http://localhost:8000/health` → `{ "status": "healthy" }`
- OpenAPI: `docs/api/openapi.v1.json`
- FastAPI ドキュメント: `http://localhost:8000/docs`

### フロントエンド（Playground）から試す
バックエンドに直接リクエストせず、フロントエンドのPlaygroundから `/mask` を呼び出せます（Vite の dev proxy を利用）。

#### 起動
```bash
# バックエンドとフロントの両方を起動
docker compose up
```

#### アクセス
- Playground: `http://localhost:5173`
- 入力欄にテキストを貼り付け、「マスクを実行」を押すと結果（マスク済みテキスト/検出一覧/差分）が表示されます。

補足:
- フロントの開発サーバは `/mask` を `http://personal:8000` にプロキシします（`frontend/vite.config.ts`）。
- そのため、基本はブラウザ操作のみで確認可能です。


## 環境変数（ログ関連）
| 変数名 | 既定値 | 説明 | 備考 |
|---|---|---|---|
| `LOG_LEVEL` | `INFO` | ログレベル | `DEBUG`/`INFO`/`WARN` など |
| `LOG_JSON` | `true` | ログをJSON形式で出力 | `false` でテキスト出力 |
| `LOG_DEBUG_BODY` | `false` | デバッグ時のみ本文をログに出力 | PII注意・本番では無効推奨 |
| `LOG_BODY_MAX` | `256` | 本文/プレビューの最大長 | 文字数上限 |
| `LOG_SAMPLE` | `1.0` | サンプリング率 | 将来拡張用 |

## 開発
開発時のテスト/Lint 実行はルートの Makefile から行えます（コンテナ起動が前提）。

詳細は `backend/README.md` を参照してください。

### OpenAPI の再生成
```bash
docker exec -w /usr/local/app personal \
  python backend/scripts/export_openapi.py --out docs/api/openapi.v1.json
```

## プロジェクトの状態（v0.3.0）
- 実装済み
  - `/mask` API（文分割 → GiNZA NER → 正規表現補完 → スパンマージ → マスク）
  - OpenAPI 固定化（`docs/api/openapi.v1.json`）
  - テスト（`backend/tests/...`）
  - Makefile によるテスト実行フロー（コンテナ内/外の自動判定）
- 今後
  - 文分割の精度チューニング
  - 追加エンティティ/ルール、ユーザ辞書の検討
