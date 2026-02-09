"""
report.md + chart_config.json → report.html ビルドスクリプト

AI判断は含まない。決定的な変換処理のみ。
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import markdown
from bs4 import BeautifulSoup, NavigableString


# ---------------------------------------------------------------------------
# HTML テンプレート（CSS は assets/report.css を外部参照）
# ---------------------------------------------------------------------------

HTML_TEMPLATE = """\
<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{company_name}（{company_code}）企業分析レポート</title>
<link rel="stylesheet" href="{css_path}">
</head>
<body>
{body}
{chart_script}
</body>
</html>
"""


# ---------------------------------------------------------------------------
# Markdown → HTML 変換
# ---------------------------------------------------------------------------


def render_markdown_to_html(md_text: str) -> str:
    """Markdown テキストを HTML に変換する。"""
    # report.md 先頭のナビリンク行を除去（[← ...] で始まる行）
    lines = md_text.split("\n")
    if lines and lines[0].startswith("["):
        lines = lines[1:]
    md_text = "\n".join(lines)

    html = markdown.markdown(
        md_text,
        extensions=["tables", "toc"],
        extension_configs={
            "toc": {"slugify": _slugify},
        },
    )
    return html


def _slugify(value: str, separator: str = "-") -> str:
    """日本語見出しをスラグ化する。"""
    # 英数字・日本語はそのまま、記号はセパレータに
    value = re.sub(r"[^\w\s\u3000-\u9fff\uff00-\uffef]", "", value)
    value = value.strip().lower()
    value = re.sub(r"[\s\u3000]+", separator, value)
    return value


# ---------------------------------------------------------------------------
# チャート挿入
# ---------------------------------------------------------------------------


def inject_charts(html_body: str, charts: list[dict]) -> str:
    """BeautifulSoup で HTML にチャート div をセクション直後に挿入する。"""
    if not charts:
        return html_body

    soup = BeautifulSoup(html_body, "html.parser")
    headings = soup.find_all(re.compile(r"^h[1-6]$"))

    for chart in charts:
        section = chart.get("section_heading", "")
        position = chart.get("position", "after_table")
        chart_id = chart.get("id", "chart")
        title = chart.get("title", "")
        note = chart.get("note", "")
        height = chart.get("height", 400)

        target = _find_heading(headings, section)
        if target is None:
            print(
                f"WARNING: section_heading '{section}' not found, skipping chart '{chart_id}'",
                file=sys.stderr,
            )
            continue

        chart_html = _build_chart_div(chart_id, title, note, height)
        chart_tag = BeautifulSoup(chart_html, "html.parser")

        if position == "before_section":
            target.insert_before(chart_tag)
        elif position == "after_section":
            # 次の見出しの直前に挿入
            next_heading = _find_next_heading(target)
            if next_heading:
                next_heading.insert_before(chart_tag)
            else:
                # 末尾に追加
                soup.append(chart_tag)
        else:
            # after_table: セクション見出し後の最初のテーブル直後に挿入
            table = _find_next_table(target)
            if table:
                table.insert_after(chart_tag)
            else:
                # テーブルがなければ見出し直後
                _insert_after_element(target, chart_tag)

    return str(soup)


def _find_heading(headings: list, text: str):
    """見出し要素から完全一致→部分一致で探索。"""
    # 完全一致
    for h in headings:
        if h.get_text(strip=True) == text:
            return h
    # 部分一致
    for h in headings:
        if text in h.get_text(strip=True):
            return h
    return None


def _find_next_heading(element):
    """指定要素の後にある次の見出し要素を探す。"""
    sibling = element.next_sibling
    while sibling:
        if (
            hasattr(sibling, "name")
            and sibling.name
            and re.match(r"^h[1-6]$", sibling.name)
        ):
            return sibling
        sibling = sibling.next_sibling
    return None


def _find_next_table(heading):
    """見出し要素の後にある最初の table を探す。次の見出しが先に来たら None。"""
    sibling = heading.next_sibling
    while sibling:
        if hasattr(sibling, "name") and sibling.name:
            if re.match(r"^h[1-6]$", sibling.name):
                return None
            if sibling.name == "table":
                return sibling
        sibling = sibling.next_sibling
    return None


def _insert_after_element(element, new_tag):
    """要素の直後に新しいタグを挿入する。"""
    if element.next_sibling:
        element.next_sibling.insert_before(new_tag)
    elif element.parent:
        element.parent.append(new_tag)


def _build_chart_div(chart_id: str, title: str, note: str, height: int) -> str:
    """チャート用 HTML div を生成する。"""
    parts = [f'<div class="chart-container">']
    if title:
        parts.append(f'  <div class="chart-title">{title}</div>')
    if note:
        parts.append(f'  <div class="chart-note">{note}</div>')
    parts.append(
        f'  <div id="{chart_id}" class="chart-box" style="height:{height}px;"></div>'
    )
    parts.append("</div>")
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# ECharts スクリプト生成
# ---------------------------------------------------------------------------


def build_echarts_script(charts: list[dict]) -> str:
    """全チャートの ECharts 初期化スクリプトを生成する。"""
    if not charts:
        return ""

    lines = [
        '<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>',
        "<script>",
        "document.addEventListener('DOMContentLoaded', function() {",
    ]

    for chart in charts:
        chart_id = chart.get("id", "chart")
        option = chart.get("echarts_option", {})
        if not option:
            continue
        option_json = json.dumps(option, ensure_ascii=False, indent=2)
        lines.append(f"  (function() {{")
        lines.append(f"    var el = document.getElementById('{chart_id}');")
        lines.append(f"    if (!el) return;")
        lines.append(f"    var chart = echarts.init(el);")
        lines.append(f"    var option = {option_json};")
        lines.append(f"    chart.setOption(option);")
        lines.append(
            f"    window.addEventListener('resize', function() {{ chart.resize(); }});"
        )
        lines.append(f"  }})();")

    lines.append("});")
    lines.append("</script>")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# テンプレート適用
# ---------------------------------------------------------------------------


def render_full_html(
    body: str,
    chart_script: str,
    company_name: str,
    company_code: str,
    css_path: str = "../../assets/report.css",
) -> str:
    """最終 HTML を組み立てる。CSS は外部参照。"""
    return HTML_TEMPLATE.format(
        css_path=css_path,
        body=body,
        chart_script=chart_script,
        company_name=company_name,
        company_code=company_code,
    )


# ---------------------------------------------------------------------------
# report.md からメタ情報を抽出
# ---------------------------------------------------------------------------


def extract_meta(md_text: str) -> tuple[str, str]:
    """report.md の h1 から企業名と証券コードを抽出する。"""
    m = re.search(r"^#\s+(.+?)（(\d{4})）", md_text, re.MULTILINE)
    if m:
        return m.group(1), m.group(2)
    # フォールバック
    return "企業", "0000"


# ---------------------------------------------------------------------------
# メインビルド関数
# ---------------------------------------------------------------------------


def build_report(report_dir: Path, no_charts: bool = False) -> Path:
    """report.md (+ chart_config.json) から report.html を生成する。"""
    report_dir = Path(report_dir)
    md_path = report_dir / "report.md"
    chart_config_path = report_dir / "chart_config.json"
    output_path = report_dir / "report.html"

    if not md_path.exists():
        raise FileNotFoundError(f"report.md not found: {md_path}")

    md_text = md_path.read_text(encoding="utf-8")
    company_name, company_code = extract_meta(md_text)

    # Markdown → HTML
    html_body = render_markdown_to_html(md_text)

    # チャート処理
    charts: list[dict] = []
    if not no_charts and chart_config_path.exists():
        config = json.loads(chart_config_path.read_text(encoding="utf-8"))
        charts = config.get("charts", [])
        # config から企業情報を取得（あれば上書き）
        if config.get("company_name"):
            company_name = config["company_name"]
        if config.get("company_code"):
            company_code = config["company_code"]

    # チャート div 挿入
    if charts:
        html_body = inject_charts(html_body, charts)

    # ECharts スクリプト生成
    chart_script = build_echarts_script(charts)

    # 最終 HTML 組み立て
    full_html = render_full_html(html_body, chart_script, company_name, company_code)

    output_path.write_text(full_html, encoding="utf-8")
    return output_path
