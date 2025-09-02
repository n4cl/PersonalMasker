# System Architecture (Draft)

## 目的

本ドキュメントは個人情報を検出・マスクするWebアプリの全体構成を定義

## 構成図
```mermaid
flowchart LR
  user["User"]
  fe["Frontend"]
  be["Backend"]
  user --> fe --> be
```

## シーケンス（主要機能）
```mermaid
sequenceDiagram
  participant U as "User"
  participant B as "Browser"
  participant N as "Nginx"
  participant A as "FastAPI"
  participant G as "NLP"

  U->>B: 入力
  B->>N: 機能 テキストマスク
  N->>A: フォワード
  A->>G: マスク処理
  G-->>A: 検出結果
  A-->>B: マスク結果
  B-->>U: 表示
```

## コンポーネント概要
- Frontend: UI と静的配信
- Backend: API と処理

## デプロイ

## 可観測性
- 構造化ログ（リクエストID、処理時間、検出件数）

## セキュリティ/プライバシー

## 非機能

