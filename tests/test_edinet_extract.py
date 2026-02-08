"""
EDINET CSV 抽出機能のユニットテスト
"""

import csv
import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

os.environ["EDINET_API_KEY"] = "test_api_key_12345"

from corporate_reports.edinet import (
    EdinetAPIError,
    extract_financial_data,
    _parse_edinet_csv,
    _parse_value,
)


# --- サンプルCSVデータ ---

SAMPLE_HEADER = [
    "\ufeff要素ID",
    "項目名",
    "コンテキストID",
    "相対年度",
    "連結・個別",
    "期間・時点",
    "ユニットID",
    "単位",
    "値",
]

SAMPLE_ROWS = [
    # 売上高 5期分
    [
        "jpcrp_cor:NetSalesSummaryOfBusinessResults",
        "売上高、経営指標等",
        "Prior4YearDuration",
        "四期前",
        "その他",
        "期間",
        "JPY",
        "円",
        "9697800000",
    ],
    [
        "jpcrp_cor:NetSalesSummaryOfBusinessResults",
        "売上高、経営指標等",
        "Prior3YearDuration",
        "三期前",
        "その他",
        "期間",
        "JPY",
        "円",
        "10034069000",
    ],
    [
        "jpcrp_cor:NetSalesSummaryOfBusinessResults",
        "売上高、経営指標等",
        "Prior2YearDuration",
        "前々期",
        "その他",
        "期間",
        "JPY",
        "円",
        "11167637000",
    ],
    [
        "jpcrp_cor:NetSalesSummaryOfBusinessResults",
        "売上高、経営指標等",
        "Prior1YearDuration",
        "前期",
        "その他",
        "期間",
        "JPY",
        "円",
        "12872437000",
    ],
    [
        "jpcrp_cor:NetSalesSummaryOfBusinessResults",
        "売上高、経営指標等",
        "CurrentYearDuration",
        "当期",
        "その他",
        "期間",
        "JPY",
        "円",
        "12383109000",
    ],
    # 経常利益
    [
        "jpcrp_cor:OrdinaryIncomeLossSummaryOfBusinessResults",
        "経常利益又は経常損失（△）、経営指標等",
        "CurrentYearDuration",
        "当期",
        "その他",
        "期間",
        "JPY",
        "円",
        "1447778000",
    ],
    # 純資産
    [
        "jpcrp_cor:NetAssetsSummaryOfBusinessResults",
        "純資産額、経営指標等",
        "CurrentYearInstant",
        "当期末",
        "その他",
        "時点",
        "JPY",
        "円",
        "17965513000",
    ],
    # 総資産
    [
        "jpcrp_cor:TotalAssetsSummaryOfBusinessResults",
        "総資産額、経営指標等",
        "CurrentYearInstant",
        "当期末",
        "その他",
        "時点",
        "JPY",
        "円",
        "19626496000",
    ],
    # BPS
    [
        "jpcrp_cor:NetAssetsPerShareSummaryOfBusinessResults",
        "１株当たり純資産額、経営指標等",
        "CurrentYearInstant",
        "当期末",
        "その他",
        "時点",
        "JPYPerShares",
        "",
        "2635.79",
    ],
    # EPS
    [
        "jpcrp_cor:BasicEarningsLossPerShareSummaryOfBusinessResults",
        "１株当たり当期純利益、経営指標等",
        "CurrentYearDuration",
        "当期",
        "その他",
        "期間",
        "JPYPerShares",
        "",
        "152.64",
    ],
    # ROE
    [
        "jpcrp_cor:RateOfReturnOnEquitySummaryOfBusinessResults",
        "自己資本利益率、経営指標等",
        "CurrentYearDuration",
        "当期",
        "その他",
        "期間",
        "pure",
        "",
        "0.0594",
    ],
    # 自己資本比率
    [
        "jpcrp_cor:EquityToAssetRatioSummaryOfBusinessResults",
        "自己資本比率、経営指標等",
        "CurrentYearInstant",
        "当期末",
        "その他",
        "時点",
        "pure",
        "",
        "0.915",
    ],
    # PER
    [
        "jpcrp_cor:PriceEarningsRatioSummaryOfBusinessResults",
        "株価収益率、経営指標等",
        "CurrentYearDuration",
        "当期",
        "その他",
        "期間",
        "pure",
        "",
        "16.56",
    ],
    # 営業CF
    [
        "jpcrp_cor:NetCashProvidedByUsedInOperatingActivitiesSummaryOfBusinessResults",
        "営業活動によるキャッシュ・フロー、経営指標等",
        "CurrentYearDuration",
        "当期",
        "その他",
        "期間",
        "JPY",
        "円",
        "1633839000",
    ],
    # 投資CF
    [
        "jpcrp_cor:NetCashProvidedByUsedInInvestingActivitiesSummaryOfBusinessResults",
        "投資活動によるキャッシュ・フロー、経営指標等",
        "CurrentYearDuration",
        "当期",
        "その他",
        "期間",
        "JPY",
        "円",
        "-420143000",
    ],
    # 財務CF
    [
        "jpcrp_cor:NetCashProvidedByUsedInFinancingActivitiesSummaryOfBusinessResults",
        "財務活動によるキャッシュ・フロー、経営指標等",
        "CurrentYearDuration",
        "当期",
        "その他",
        "期間",
        "JPY",
        "円",
        "-421779000",
    ],
    # 現金同等物
    [
        "jpcrp_cor:CashAndCashEquivalentsSummaryOfBusinessResults",
        "現金及び現金同等物の残高、経営指標等",
        "CurrentYearInstant",
        "当期末",
        "その他",
        "時点",
        "JPY",
        "円",
        "9791709000",
    ],
    # 従業員数
    [
        "jpcrp_cor:NumberOfEmployees",
        "従業員数",
        "CurrentYearInstant",
        "当期末",
        "その他",
        "時点",
        "pure",
        "人",
        "295",
    ],
    # 個別：1株配当
    [
        "jpcrp_cor:DividendPaidPerShareSummaryOfBusinessResults",
        "１株当たり配当額、経営指標等",
        "CurrentYearDuration_NonConsolidatedMember",
        "当期",
        "個別",
        "期間",
        "JPYPerShares",
        "",
        "55.00",
    ],
    # 個別：配当性向
    [
        "jpcrp_cor:PayoutRatioSummaryOfBusinessResults",
        "配当性向、経営指標等",
        "CurrentYearDuration_NonConsolidatedMember",
        "当期",
        "個別",
        "期間",
        "pure",
        "",
        "0.3603",
    ],
    # 値なし（－）
    [
        "jpcrp_cor:DilutedEarningsPerShareSummaryOfBusinessResults",
        "潜在株式調整後１株当たり当期純利益、経営指標等",
        "CurrentYearDuration",
        "当期",
        "その他",
        "期間",
        "JPYPerShares",
        "",
        "－",
    ],
]


def _write_sample_csv(
    dirpath: Path,
    filename: str = "jpcrp030000-asr-001_E01350-000_2024-12-31_01_2025-03-21.csv",
):
    """サンプルCSVをUTF-16LE TSVとして書き出す（EDINET実ファイルと同じ形式）"""
    csv_path = dirpath / filename
    with open(csv_path, "w", encoding="utf-16le", newline="") as f:
        writer = csv.writer(f, delimiter="\t", quoting=csv.QUOTE_ALL)
        writer.writerow(SAMPLE_HEADER)
        for row in SAMPLE_ROWS:
            writer.writerow(row)
    return csv_path


class TestParseValue:
    """_parse_value のテスト"""

    def test_integer(self):
        assert _parse_value("12383109000") == 12383109000

    def test_float(self):
        assert _parse_value("2635.79") == 2635.79

    def test_negative(self):
        assert _parse_value("-420143000") == -420143000

    def test_dash(self):
        assert _parse_value("－") is None

    def test_empty(self):
        assert _parse_value("") is None


class TestParseEdinetCSV:
    """_parse_edinet_csv のテスト"""

    def test_parse_rows(self, tmp_path):
        csv_path = _write_sample_csv(tmp_path)
        rows = _parse_edinet_csv(csv_path)
        assert len(rows) == len(SAMPLE_ROWS)
        assert rows[0]["要素ID"] == "jpcrp_cor:NetSalesSummaryOfBusinessResults"
        assert rows[0]["値"] == "9697800000"


class TestExtractFinancialData:
    """extract_financial_data のテスト"""

    def test_extract_from_direct_dir(self, tmp_path):
        """CSVがディレクトリ直下にある場合"""
        _write_sample_csv(tmp_path)
        result = extract_financial_data(tmp_path)

        summary = result["経営指標等"]

        # 売上高 5期分
        assert summary["4期前"]["売上高"] == 9697800000
        assert summary["3期前"]["売上高"] == 10034069000
        assert summary["2期前"]["売上高"] == 11167637000
        assert summary["1期前"]["売上高"] == 12872437000
        assert summary["当期"]["売上高"] == 12383109000

    def test_extract_from_xbrl_to_csv_subdir(self, tmp_path):
        """CSVがXBRL_TO_CSV/サブディレクトリにある場合"""
        subdir = tmp_path / "XBRL_TO_CSV"
        subdir.mkdir()
        _write_sample_csv(subdir)
        result = extract_financial_data(tmp_path)

        assert result["経営指標等"]["当期"]["売上高"] == 12383109000

    def test_current_year_indicators(self, tmp_path):
        """当期の各指標が正しく抽出される"""
        _write_sample_csv(tmp_path)
        result = extract_financial_data(tmp_path)
        current = result["経営指標等"]["当期"]

        assert current["経常利益"] == 1447778000
        assert current["純資産"] == 17965513000
        assert current["総資産"] == 19626496000
        assert current["BPS"] == 2635.79
        assert current["EPS"] == 152.64
        assert current["ROE"] == 0.0594
        assert current["自己資本比率"] == 0.915
        assert current["PER"] == 16.56
        assert current["営業CF"] == 1633839000
        assert current["投資CF"] == -420143000
        assert current["財務CF"] == -421779000
        assert current["現金同等物"] == 9791709000
        assert current["従業員数"] == 295

    def test_non_consolidated_indicators(self, tmp_path):
        """個別指標（配当、配当性向）が正しく抽出される"""
        _write_sample_csv(tmp_path)
        result = extract_financial_data(tmp_path)
        current = result["経営指標等"]["当期"]

        assert current["1株配当"] == 55.00
        assert current["配当性向"] == 0.3603

    def test_csv_not_found(self, tmp_path):
        """CSVが見つからない場合のエラー"""
        with pytest.raises(EdinetAPIError, match="jpcrp030000-asr"):
            extract_financial_data(tmp_path)

    def test_source_path_included(self, tmp_path):
        """出力にソースパスが含まれる"""
        _write_sample_csv(tmp_path)
        result = extract_financial_data(tmp_path)
        assert "source" in result
        assert "jpcrp030000-asr" in result["source"]


class TestExtractCLI:
    """edinet extract CLI コマンドのテスト"""

    @patch("corporate_reports.cli.extract_financial_data")
    @patch(
        "sys.argv",
        [
            "corporate-reports",
            "edinet",
            "extract",
            "--csv-dir",
            "/tmp/test_csv",
        ],
    )
    def test_cli_extract_stdout(self, mock_extract, capsys):
        """extract コマンドで標準出力にJSON"""
        from corporate_reports.cli import main

        mock_extract.return_value = {
            "source": "/tmp/test.csv",
            "経営指標等": {"当期": {"売上高": 12383109000}},
        }

        main()
        mock_extract.assert_called_once_with(csv_dir="/tmp/test_csv")

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["経営指標等"]["当期"]["売上高"] == 12383109000

    @patch("corporate_reports.cli.extract_financial_data")
    def test_cli_extract_to_file(self, mock_extract, tmp_path):
        """extract コマンドで --output にファイル保存"""
        from corporate_reports.cli import main

        output_file = tmp_path / "output.json"

        mock_extract.return_value = {
            "source": "/tmp/test.csv",
            "経営指標等": {"当期": {"売上高": 100}},
        }

        with patch(
            "sys.argv",
            [
                "corporate-reports",
                "edinet",
                "extract",
                "--csv-dir",
                "/tmp/test_csv",
                "--output",
                str(output_file),
            ],
        ):
            main()

        assert output_file.exists()
        data = json.loads(output_file.read_text(encoding="utf-8"))
        assert data["経営指標等"]["当期"]["売上高"] == 100
