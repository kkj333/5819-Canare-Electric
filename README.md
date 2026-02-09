# 企業分析レポート

[![CI](https://github.com/kkj333/corporate-reports/actions/workflows/ci.yml/badge.svg)](https://github.com/kkj333/corporate-reports/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/kkj333/corporate-reports/branch/main/graph/badge.svg)](https://codecov.io/gh/kkj333/corporate-reports)

上場企業の分析レポート集。有価証券報告書・決算短信に基づく独自分析。

## 企業一覧

| コード | 企業名 | 市場 | レポート (MD) | レポート (HTML) |
|---|---|---|---|---|
| 5819 | カナレ電気 | 東証スタンダード | [Markdown](reports/5819_canare/report.md) | [HTML](reports/5819_canare/report.html) |
| 9991 | ジェコス | 東証プライム | [Markdown](reports/9991_jecos/report.md) | [HTML](reports/9991_jecos/report.html) |

## GitHub Pages

- [カナレ電気](https://kkj333.github.io/corporate-reports/reports/5819_canare/report.html)
- [ジェコス](https://kkj333.github.io/corporate-reports/reports/9991_jecos/report.html)

HTMLレポートは `report.md` から自動生成されるスタンドアロンHTML（EChartsチャート付き）です。

```bash
# チャート付きHTML生成（Claude Codeスキル）
/build-report reports/9991_jecos

# CLIから直接生成
uv run corporate-reports build-report reports/9991_jecos

# チャートなし（テキストのみ）
uv run corporate-reports build-report reports/9991_jecos --no-charts

# サイドバーTOCなし
uv run corporate-reports build-report reports/9991_jecos --no-toc
```

## ドキュメント

- [セットアップ手順](docs/getting-started.md) - 初回セットアップとスキル一覧
- [EDINET API 設定](docs/edinet-api-setup.md) - APIキーの取得と設定方法
- [スキル一覧](docs/skills.md) - 利用可能なすべてのスキルの詳細
