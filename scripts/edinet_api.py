#!/usr/bin/env python3
"""
EDINET API v2 クライアント

APIキーを .env から安全に読み込み、書類検索・ダウンロードを行う。
使用例:
    python scripts/edinet_api.py search --date 2025-03-27 --sec-code 5819
    python scripts/edinet_api.py download --doc-id S100XXXX --type 2 --output report.zip
"""

import os
import sys
import time
import json
import argparse
from pathlib import Path
from typing import Optional, Dict, List

import requests
from dotenv import load_dotenv

# プロジェクトルートの .env を読み込み
project_root = Path(__file__).parent.parent
load_dotenv(project_root / ".env")

API_KEY = os.getenv("EDINET_API_KEY")
BASE_URL = "https://api.edinet-fsa.go.jp/api/v2"
RATE_LIMIT_DELAY = 0.35  # 秒間3リクエスト = 約0.33秒間隔


class EdinetAPIError(Exception):
    """EDINET API エラー"""
    pass


def check_api_key():
    """APIキーの存在確認"""
    if not API_KEY:
        print("ERROR: EDINET_API_KEY が設定されていません", file=sys.stderr)
        print("", file=sys.stderr)
        print("設定方法:", file=sys.stderr)
        print("1. プロジェクトルートに .env ファイルを作成", file=sys.stderr)
        print("2. 以下の内容を追加:", file=sys.stderr)
        print("   EDINET_API_KEY=あなたのAPIキー", file=sys.stderr)
        print("", file=sys.stderr)
        print("APIキーの取得:", file=sys.stderr)
        print("https://api.edinet-fsa.go.jp/api/auth/index.aspx?mode=1", file=sys.stderr)
        sys.exit(1)


def search_documents(
    date: str,
    sec_code: Optional[str] = None,
    ordinance_code: Optional[str] = None,
    form_code: Optional[str] = None,
) -> List[Dict]:
    """
    書類一覧APIで検索

    Args:
        date: 検索対象日 (YYYY-MM-DD)
        sec_code: 証券コード（4桁または5桁）
        ordinance_code: 府令コード (例: "010" = 金商法)
        form_code: 様式コード (例: "030000" = 有価証券報告書)

    Returns:
        書類情報のリスト
    """
    check_api_key()

    url = f"{BASE_URL}/documents.json"
    params = {
        "date": date,
        "type": "2",  # メタデータ + 書類一覧
        "Subscription-Key": API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        if data.get("metadata", {}).get("status") != "200":
            raise EdinetAPIError(f"API returned status: {data.get('metadata')}")

        results = data.get("results", [])

        # フィルタリング
        if sec_code:
            # 4桁コードの場合は前方一致（EDINETは5桁で末尾0付き）
            sec_prefix = sec_code[:4]
            results = [
                r
                for r in results
                if r.get("secCode") and r.get("secCode")[:4] == sec_prefix
            ]

        if ordinance_code:
            results = [r for r in results if r.get("ordinanceCode") == ordinance_code]

        if form_code:
            results = [r for r in results if r.get("formCode") == form_code]

        time.sleep(RATE_LIMIT_DELAY)
        return results

    except requests.exceptions.RequestException as e:
        raise EdinetAPIError(f"API request failed: {e}")


def download_document(doc_id: str, doc_type: str, output_path: str) -> str:
    """
    書類をダウンロード

    Args:
        doc_id: 書類管理番号 (例: S100XXXX)
        doc_type: 取得形式
            1 = ZIP (XBRL + PDF + 監査報告書)
            2 = PDF (提出書類)
            3 = PDF (代替書類・英文)
            5 = CSV (構造化財務データ)
        output_path: 保存先パス

    Returns:
        保存先のパス
    """
    check_api_key()

    url = f"{BASE_URL}/documents/{doc_id}"
    params = {
        "type": doc_type,
        "Subscription-Key": API_KEY,
    }

    try:
        response = requests.get(url, params=params, timeout=60, stream=True)
        response.raise_for_status()

        # ファイルに保存
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        time.sleep(RATE_LIMIT_DELAY)
        return str(output_file)

    except requests.exceptions.RequestException as e:
        raise EdinetAPIError(f"Download failed: {e}")


def main():
    parser = argparse.ArgumentParser(description="EDINET API v2 クライアント")
    subparsers = parser.add_subparsers(dest="command", help="コマンド")

    # search コマンド
    search_parser = subparsers.add_parser("search", help="書類を検索")
    search_parser.add_argument("--date", required=True, help="検索対象日 (YYYY-MM-DD)")
    search_parser.add_argument("--sec-code", help="証券コード (4桁または5桁)")
    search_parser.add_argument("--ordinance-code", help="府令コード (例: 010)")
    search_parser.add_argument("--form-code", help="様式コード (例: 030000)")

    # download コマンド
    download_parser = subparsers.add_parser("download", help="書類をダウンロード")
    download_parser.add_argument("--doc-id", required=True, help="書類管理番号")
    download_parser.add_argument("--type", required=True, choices=["1", "2", "3", "5"],
                                 help="取得形式 (1:XBRL, 2:PDF, 3:代替PDF, 5:CSV)")
    download_parser.add_argument("--output", required=True, help="保存先パス")

    args = parser.parse_args()

    try:
        if args.command == "search":
            results = search_documents(
                date=args.date,
                sec_code=args.sec_code,
                ordinance_code=args.ordinance_code,
                form_code=args.form_code,
            )
            print(json.dumps(results, ensure_ascii=False, indent=2))

        elif args.command == "download":
            output_path = download_document(
                doc_id=args.doc_id,
                doc_type=args.type,
                output_path=args.output,
            )
            print(json.dumps({"status": "success", "file": output_path}, ensure_ascii=False))

        else:
            parser.print_help()
            sys.exit(1)

    except EdinetAPIError as e:
        print(json.dumps({"status": "error", "message": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
