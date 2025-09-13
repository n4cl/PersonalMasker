# Backend 開発ガイド

## 前提
- Docker / Docker Compose が使用可能
- `docker compose up` で `personal` コンテナ（バックエンド）が起動済み

## 起動
```bash
docker compose up personal
```

## テスト
```bash
make backend-test
```

## Lint（Ruff）
```bash
make backend-lint
```

## 一括（pytest → Ruff）
```bash
make backend-all
```

> 注: Make ターゲットは実行環境を自動判定します（コンテナ内: 直接実行 / ホスト: docker compose 経由）。
> ホスト側ではコンテナ起動が前提です。未起動の場合はエラーとなります。

## ログ（開発用）
- `LOG_LEVEL`（既定: INFO）
- `LOG_JSON`（既定: true）
- `LOG_DEBUG_BODY`（既定: false）
- `LOG_BODY_MAX`（既定: 256）
