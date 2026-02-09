"""build_report モジュールのテスト"""

import json
from pathlib import Path

import pytest

from corporate_reports.build_report import (
    build_echarts_script,
    build_report,
    extract_meta,
    inject_charts,
    render_markdown_to_html,
)


# ---------------------------------------------------------------------------
# render_markdown_to_html
# ---------------------------------------------------------------------------


class TestRenderMarkdown:
    def test_basic_heading(self):
        html = render_markdown_to_html("# テスト見出し")
        assert "<h1" in html
        assert "テスト見出し" in html

    def test_table_rendering(self):
        md = "| 項目 | 値 |\n|---|---|\n| 売上 | 100 |\n"
        html = render_markdown_to_html(md)
        assert "<table>" in html
        assert "<th>" in html
        assert "売上" in html

    def test_nav_link_stripped(self):
        md = "[← トップ](./) ｜ [一覧](../../)\n\n# レポート"
        html = render_markdown_to_html(md)
        assert "← トップ" not in html
        assert "レポート" in html

    def test_multiple_headings(self):
        md = "# H1\n## H2\n### H3"
        html = render_markdown_to_html(md)
        assert "<h1" in html
        assert "<h2" in html
        assert "<h3" in html


# ---------------------------------------------------------------------------
# extract_meta
# ---------------------------------------------------------------------------


class TestExtractMeta:
    def test_normal(self):
        name, code = extract_meta("# ジェコス（9991）企業分析レポート")
        assert name == "ジェコス"
        assert code == "9991"

    def test_fallback(self):
        name, code = extract_meta("# タイトルのみ")
        assert name == "企業"
        assert code == "0000"

    def test_with_prefix(self):
        md = "[← top](./)\n\n# カナレ電気（5819）企業分析レポート"
        name, code = extract_meta(md)
        assert name == "カナレ電気"
        assert code == "5819"


# ---------------------------------------------------------------------------
# inject_charts
# ---------------------------------------------------------------------------


class TestInjectCharts:
    def _make_html(self):
        return (
            "<h2>セグメント構成</h2>\n"
            "<table><tr><th>項目</th></tr><tr><td>データ</td></tr></table>\n"
            "<h2>財務ハイライト</h2>\n"
            "<p>テキスト</p>"
        )

    def test_after_table(self):
        html = self._make_html()
        charts = [
            {
                "id": "chart-1",
                "section_heading": "セグメント構成",
                "position": "after_table",
                "title": "テストチャート",
                "note": "",
                "height": 300,
            }
        ]
        result = inject_charts(html, charts)
        assert 'id="chart-1"' in result
        # chart-container はテーブルの後にある
        table_pos = result.find("</table>")
        chart_pos = result.find("chart-1")
        assert chart_pos > table_pos

    def test_before_section(self):
        html = self._make_html()
        charts = [
            {
                "id": "chart-2",
                "section_heading": "財務ハイライト",
                "position": "before_section",
                "title": "",
                "note": "",
                "height": 400,
            }
        ]
        result = inject_charts(html, charts)
        assert 'id="chart-2"' in result
        # chart-2 は 財務ハイライト見出しの前にある
        chart_pos = result.find("chart-2")
        heading_pos = result.find("財務ハイライト")
        assert chart_pos < heading_pos

    def test_after_section(self):
        html = self._make_html()
        charts = [
            {
                "id": "chart-3",
                "section_heading": "セグメント構成",
                "position": "after_section",
                "title": "",
                "note": "",
                "height": 400,
            }
        ]
        result = inject_charts(html, charts)
        assert 'id="chart-3"' in result
        # chart-3 は 次の見出し（財務ハイライト）の前にある
        chart_pos = result.find("chart-3")
        next_heading_pos = result.find("財務ハイライト")
        assert chart_pos < next_heading_pos

    def test_partial_match(self):
        html = "<h2>連結経営指標の推移</h2>\n<table><tr><td>x</td></tr></table>"
        charts = [
            {
                "id": "chart-partial",
                "section_heading": "経営指標の推移",
                "position": "after_table",
                "title": "",
                "note": "",
                "height": 300,
            }
        ]
        result = inject_charts(html, charts)
        assert 'id="chart-partial"' in result

    def test_no_match_skipped(self, capsys):
        html = "<h2>存在する見出し</h2>"
        charts = [
            {
                "id": "chart-miss",
                "section_heading": "存在しない見出し",
                "position": "after_table",
                "title": "",
                "note": "",
                "height": 300,
            }
        ]
        result = inject_charts(html, charts)
        assert "chart-miss" not in result
        captured = capsys.readouterr()
        assert "WARNING" in captured.err

    def test_empty_charts(self):
        html = "<h2>見出し</h2>"
        result = inject_charts(html, [])
        assert result == html


# ---------------------------------------------------------------------------
# build_echarts_script
# ---------------------------------------------------------------------------


class TestBuildEchartsScript:
    def test_generates_script(self):
        charts = [
            {
                "id": "chart-test",
                "echarts_option": {
                    "xAxis": {"type": "category", "data": ["A", "B"]},
                    "yAxis": {"type": "value"},
                    "series": [{"type": "bar", "data": [1, 2]}],
                },
            }
        ]
        script = build_echarts_script(charts)
        assert "echarts.min.js" in script
        assert "echarts.init" in script
        assert "chart-test" in script

    def test_empty_charts(self):
        assert build_echarts_script([]) == ""

    def test_no_option_skipped(self):
        charts = [{"id": "chart-empty", "echarts_option": {}}]
        script = build_echarts_script(charts)
        assert "chart-empty" not in script


# ---------------------------------------------------------------------------
# build_report (統合テスト)
# ---------------------------------------------------------------------------


class TestBuildReport:
    def test_no_charts(self, tmp_path):
        md_content = "# テスト企業（1234）分析レポート\n\n## 概要\n\nテスト内容です。\n"
        (tmp_path / "report.md").write_text(md_content, encoding="utf-8")

        output = build_report(tmp_path, no_charts=True)
        assert output.exists()
        html = output.read_text(encoding="utf-8")
        assert "テスト企業" in html
        assert "1234" in html
        assert "report.css" in html
        assert "echarts.min.js" not in html
        assert "<h1" in html

    def test_with_chart_config(self, tmp_path):
        md_content = (
            "# サンプル（5678）レポート\n\n"
            "## 業績推移\n\n"
            "| 年度 | 売上 |\n|---|---|\n| 2023 | 100 |\n| 2024 | 120 |\n"
        )
        (tmp_path / "report.md").write_text(md_content, encoding="utf-8")

        config = {
            "version": "1.0",
            "company_name": "サンプル",
            "company_code": "5678",
            "charts": [
                {
                    "id": "chart-sales",
                    "section_heading": "業績推移",
                    "position": "after_table",
                    "title": "売上推移",
                    "note": "テスト",
                    "height": 350,
                    "echarts_option": {
                        "xAxis": {"type": "category", "data": ["2023", "2024"]},
                        "yAxis": {"type": "value"},
                        "series": [{"type": "bar", "data": [100, 120]}],
                    },
                }
            ],
        }
        (tmp_path / "chart_config.json").write_text(
            json.dumps(config, ensure_ascii=False), encoding="utf-8"
        )

        output = build_report(tmp_path)
        html = output.read_text(encoding="utf-8")
        assert "chart-sales" in html
        assert "echarts.min.js" in html
        assert "売上推移" in html

    def test_missing_report_md(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            build_report(tmp_path)

    def test_no_chart_config_fallback(self, tmp_path):
        md_content = "# 企業（9999）レポート\n\nテスト\n"
        (tmp_path / "report.md").write_text(md_content, encoding="utf-8")
        # chart_config.json が存在しなくてもエラーにならない
        output = build_report(tmp_path)
        assert output.exists()
        html = output.read_text(encoding="utf-8")
        assert "echarts.min.js" not in html
