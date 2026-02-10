# Corporate Reports

## ワークフロー

企業分析は以下のスキルを組み合わせて行う:

1. `/download-edinet` でデータ取得
2. `/extract-data` でPDFから構造化データ抽出
3. `/corporate-report` でレポート生成（notes.mdがあれば企業固有の論点を反映）
4. `/build-report` でHTML化
5. `/update-report` で新決算データ反映
6. `/update-price` で株価更新
7. `/compare` で企業間比較

## 基本原則

- report.md はピュアMarkdown。HTML/CSS/チャートは `/build-report` の責務
- 数値計算は `valuation.py`（Python）で決定的に実行。LLM推論で計算しない
- 企業固有の論点は `notes.md` に書き、レポート生成時に反映する
- 決算短信はEDINET APIで取得不可（TDnet管轄）。手動DLが必要
