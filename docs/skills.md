# スキル一覧

Claude Code で利用可能なスキルの詳細ガイド。

---

## `/corporate-report`

企業の分析レポートとチャートを生成する。

### 使い方

```
/corporate-report [証券コード] [企業名]
```

### 例

```
/corporate-report 5819 カナレ電気
```

### 処理内容

1. 企業ディレクトリ `[証券コード]_[企業名小文字]` を作成
2. EDINET API から有価証券報告書・四半期報告書をダウンロード
3. 財務データを抽出・構造化
4. レポート（Markdown）を生成
5. 財務チャート（HTML）を生成

### 出力ファイル

- `report.md` - 分析レポート
- `data/` - 元データ（PDF, CSV, XBRL）

生成後、`/build-report` でチャート付き HTML を生成可能。

---

## `/build-report`

report.md からチャート付き report.html を生成する。

### 使い方

```
/build-report [レポートディレクトリ]
```

### 例

```
/build-report reports/9991_jecos
```

### 処理内容

1. report.md を読み、チャート候補テーブルを選定
2. chart_config.json を生成（ECharts option 付き）
3. `uv run corporate-reports build-report` を実行して HTML 生成
4. 生成された HTML を検証

### 出力ファイル

- `chart_config.json` - チャート定義（AI 生成）
- `report.html` - チャート付き HTML レポート

### CLI から直接実行

```bash
# チャート付き
uv run corporate-reports build-report reports/9991_jecos

# テキストのみ（chart_config.json を無視）
uv run corporate-reports build-report reports/9991_jecos --no-charts

# サイドバーTOCなし
uv run corporate-reports build-report reports/9991_jecos --no-toc
```

### CSS カスタマイズ

HTML のスタイルは `assets/report.css` で一元管理。全レポートがこのファイルを参照するため、CSS 変更が即反映される。

---

## `/download-edinet`

EDINET API から有価証券報告書・四半期報告書をダウンロードする。

### 使い方

```
/download-edinet [証券コード] [企業名]
```

### 例

```
/download-edinet 5819 カナレ電気
```

### 処理内容

1. 企業の開示書類を EDINET API で検索
2. 有価証券報告書・四半期報告書（PDF・CSV）をダウンロード
3. 企業ディレクトリの `data/` 以下に保存

**注意**: 決算短信はTDnet管轄のためEDINET APIでは取得不可。企業IRページ等から手動でPDFを取得する。

### 取得形式

| 形式 | 内容 | 用途 |
|---|---|---|
| CSV | 構造化財務データ | **推奨**: 正確で効率的 |
| PDF | 提出書類 | 定性情報の確認 |
| XBRL | タクソノミ付き完全データ | 必要時のみ |

### 注意点

- APIキーが `.env` に設定されている必要がある
- レート制限: 秒間3リクエストまで（自動制御）
- 2024年4月以降の書類で CSV 取得可能

---

## `/extract-data`

PDF から財務データを抽出して構造化する。

### 使い方

```
/extract-data [PDFファイルパス]
```

### 例

```
/extract-data reports/5819_canare/data/pdf/yuho_2024.pdf
```

### 処理内容

1. PDF から貸借対照表・損益計算書を抽出
2. JSON 形式で構造化
3. 企業ディレクトリの `data/financial_data.json` に保存

### 対応書類

- 有価証券報告書
- 決算短信

### 注意点

- CSV 取得済みの場合は不要（CSV のほうが正確）
- PDF の構造によっては抽出精度が低下する場合がある

---

## `/update-report`

既存の企業分析レポートに新しい決算データを反映する。

### 使い方

```
/update-report [企業ディレクトリ]
```

### 例

```
/update-report reports/5819_canare
```

### 処理内容

1. 最新の有価証券報告書をダウンロード
2. 財務データを抽出
3. 既存レポートに新決算データを追加
4. チャートを更新

### 使用タイミング

- 新決算発表後
- 四半期報告書発表後

---

## `/update-price`

株価を入力してバリュエーション指標を再計算する。

### 使い方

```
/update-price [企業ディレクトリ] [株価]
```

### 例

```
/update-price reports/5819_canare 1250
```

### 処理内容

1. 指定された株価で PER・PBR・配当利回りを再計算
2. レポートのバリュエーション指標セクションを更新
3. チャートの株価推移を更新

### 再計算される指標

- PER（株価収益率）
- PBR（株価純資産倍率）
- 配当利回り
- 時価総額

---

## `/compare`

複数企業の横比較表を生成する。

### 使い方

```
/compare [企業ディレクトリ1] [企業ディレクトリ2] ...
```

### 例

```
/compare reports/5819_canare 6857_advantest
```

### 処理内容

1. 各企業の財務データを読み込み
2. 横比較表（Markdown）を生成
3. `comparison_report.md` として保存

### 比較項目

- 基本情報（市場、業種、決算月）
- 財務指標（売上高、営業利益、純資産等）
- 収益性指標（営業利益率、ROE、ROA）
- 安全性指標（自己資本比率、流動比率）
- バリュエーション（PER、PBR、配当利回り）

---

## スキルの組み合わせ例

### 1. 新規企業を分析する

```
/corporate-report 5819 カナレ電気
/build-report reports/5819_canare
```

レポート生成後、チャート付き HTML を作成。

### 2. 既存企業の決算を更新する

```
/update-report reports/5819_canare
/update-price reports/5819_canare 1250
/build-report reports/5819_canare
```

最新決算を反映後、株価を更新し、HTML を再ビルド。

### 3. 複数企業を比較する

```
/corporate-report 5819 カナレ電気
/corporate-report 6857 アドバンテスト
/compare reports/5819_canare 6857_advantest
```

各企業のレポートを作成後、横比較。

---

## トラブルシューティング

### スキルが見つからない

```
ERROR: Skill not found
```

→ `.claude/skills/` 以下にスキル定義ファイルがあることを確認。

### EDINET API エラー

```
ERROR: EDINET_API_KEY が設定されていません
```

→ [edinet-api-setup.md](edinet-api-setup.md) を参照して APIキーを設定。

### データ抽出の精度が低い

CSV 形式でダウンロードすると抽出精度が向上します:

```
/download-edinet 5819 カナレ電気
```

（2024年4月以降の書類で CSV 対応）
