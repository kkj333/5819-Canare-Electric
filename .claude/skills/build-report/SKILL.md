---
name: build-report
description: report.md からチャート付き report.html を生成する。使い方 /build-report [レポートディレクトリ]
---

# レポート HTML ビルド

`$0` ディレクトリの `report.md` を読み、ECharts チャート付きのスタンドアロン `report.html` を生成する。

---

## Phase 1: チャート候補テーブル選定

`$0/report.md` を読み、テーブルをスキャンしてチャート化すべきものを選定する。

### チャート化する基準
- **時系列データ（3期以上の年度比較）** → チャート化
- **比較データ（2カテゴリ以上の並列比較）** → チャート化
- **セグメント構成** → チャート化

### スキップする基準
- 概要テーブル（会社概要、沿革など key-value 形式）
- 計算過程テーブル（清算価値の計算詳細など）
- 小さいテーブル（2行以下）
- テキスト中心のテーブル（リスク分析、評価根拠など）

### チャート種別マッピング

| データ種別 | ECharts type | 構成 |
|---|---|---|
| 売上・利益推移 | bar + line | 棒: 売上高、線: 営業利益率 |
| セグメント構成 | bar (grouped) | セグメント間比較 |
| CF推移 | bar + line | 棒: 営業CF、線: FCF |
| 配当推移 | bar + line | 棒: 配当額、線: 配当性向 |
| ROE推移 | line + markLine | 折れ線 + 目標8%ライン |
| 競合比較 | radar | 多軸レーダー |
| DCFシナリオ | bar (horizontal) | 3シナリオ横棒 |
| BPS vs 株価 | bar + markLine | BPS棒 + 株価水平線 |

## Phase 2: chart_config.json 生成

Phase 1 の選定結果をもとに `$0/chart_config.json` を生成する。

### スキーマ

```json
{
  "version": "1.0",
  "company_name": "企業名",
  "company_code": "証券コード",
  "generated_at": "ISO8601タイムスタンプ",
  "charts": [
    {
      "id": "chart-unique-id",
      "section_heading": "report.md 内の見出しテキスト（完全一致で指定）",
      "position": "after_table | after_section | before_section",
      "title": "チャートのタイトル",
      "note": "チャートの補足説明（1行）",
      "height": 400,
      "echarts_option": {
        "tooltip": {},
        "legend": {},
        "xAxis": {},
        "yAxis": [],
        "series": []
      }
    }
  ]
}
```

### 重要ルール
- `section_heading` は report.md の見出しテキストと**完全一致**で指定する（Markdownの `#` やスペースは除く）
- `position` は通常 `after_table`（テーブル直後にチャートを配置）
- `echarts_option` は ECharts 5 の完全な option オブジェクトを指定する
- 数値は report.md のテーブルからそのまま抽出する。計算しない
- 色は統一感のあるパレットを使用する（例: `#5470c6`, `#91cc75`, `#fac858`, `#ee6666`, `#73c0de`）
- 日本語ラベル対応（tooltip formatter で「百万円」「%」等の単位を表示）
- Y軸が2つある場合（金額 + 比率）は yAxisIndex で分離する

## Phase 3: HTML ビルド実行

以下のコマンドを実行する:

```bash
uv run corporate-reports build-report $0
```

これにより `$0/report.html` が生成される。

## Phase 4: 生成 HTML 検証

生成された `$0/report.html` を読み、以下を確認する:

1. **テーブルが正しく変換されているか**: HTML内に `<table>` タグが存在する
2. **チャート div が正しい位置に挿入されているか**: 各 `chart-container` が対応するセクション付近にある
3. **ECharts スクリプトが含まれているか**: `echarts.init` の呼び出しがチャート数と一致する
4. **メタ情報が正しいか**: `<title>` タグに企業名・証券コードが含まれる
5. **サイドバーTOCが生成されているか**: `toc-sidebar` 内に h2/h3 見出しへのリンクが存在する

問題があれば chart_config.json を修正して Phase 3 を再実行する。

## CSS カスタマイズ

HTMLのスタイルは `assets/report.css` で一元管理されている。全レポートの HTML が相対パスでこのファイルを参照するため、CSS を変更するだけで全レポートに即反映される（再ビルド不要）。

## オプション

- `--no-charts`: チャートなしでビルド（chart_config.json を無視）
- `--no-toc`: サイドバーTOCなしでビルド
