"""
OpenAPI エクスポートスクリプト
- backend.app の FastAPI アプリから OpenAPI を生成し、指定パスに出力します。
使い方（リポジトリルートで実行）:
    python backend/scripts/export_openapi.py --out docs/api/openapi.v1.json
引数を省略した場合は docs/api/openapi.v1.json に出力します。
"""
import argparse
import json
from pathlib import Path

from backend.app import app


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="OpenAPI をファイルに出力します")
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("docs/api/openapi.v1.json"),
        help="出力先ファイルパス (default: docs/api/openapi.v1.json)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    out: Path = args.out
    out.parent.mkdir(parents=True, exist_ok=True)
    data = app.openapi()
    out.write_text(json.dumps(data, ensure_ascii=False, indent=2))
    print(f"wrote: {out}")


if __name__ == "__main__":
    main()
