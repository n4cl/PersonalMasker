PersonalMasker
===

## 概要
PersonalMasker は、ドキュメント内の個人情報を自動検出し、マスク処理を行うアプリケーションを予定しています。

個人情報を匿名化し、安全なドキュメント共有を実現します。

本アプリケーションは以下の特徴を持つ予定です：  
- Web インターフェースと REST API の両方をサポート  
- カスタマイズ可能なマスキング設定

## 予定している機能

### マスキング機能
- テキスト内の個人情報を自動検出しマスク処理を実施
- 以下の個人情報に対応予定
  - 氏名
  - 住所 
  - 電話番号
  - メールアドレス

### 対応フォーマット
- プレーンテキスト (.txt)
- Microsoft Office ファイル
  - Word (.docx)
  - Excel (.xlsx) 
  - PowerPoint (.pptx)

### インターフェース
#### Web インターフェース
- ドラッグ&ドロップによるファイルアップロード
- マスク処理のプレビュー機能
- 処理済みファイルのダウンロード
- 処理履歴の管理

#### REST API
- ファイルアップロード
- マスク処理実行
- ファイルダウンロード

## プロジェクトの状態
現在、PersonalMasker は設計段階にあり、最初のプロトタイプ開発に着手しています。  
次のマイルストーンでは以下を目指します：  
- マスキングアルゴリズムの実装