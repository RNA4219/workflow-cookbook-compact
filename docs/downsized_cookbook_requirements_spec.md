# Downsized Workflow Cookbook: Requirements & Specification
_JP: ダウンサイザード Workflow Cookbook: 要件と仕様_

> 概要のみを確認したい場合は `docs/downsized_cookbook_summary.md` を参照してください。

## Snapshot Summary

| 項目 | 要約 | 詳細節 |
| --- | --- | --- |
| 目的 | 軽量環境で要約→要件→設計を少ターンで完遂しつつ統治理想を維持 | §1 |
| スコープ | Markdown テンプレート、YAML レシピ、軽量スクリプト、設定、サンプル | §2 |
| 制約 | トークン／ROI 予算、JSON 準拠、設計キャパ ≈50k 行、低リソース HW | §3 |
| コア要素 | ディレクトリ構成、テンプレート、レシピランナー、ROI 優先付け、BirdEye-Lite、ガードレール | §4 |
| 非機能 | 可搬性・拡張性・保守性・使いやすさを重視 | §5 |

## 1. Objectives
_JP: 目的_

- **Lightweight execution:** CPU（1〜3B）や小規模 GPU（≈7B）でも要約→要件→設計のワークフローを少トークンで回せること。
- **Governance retention:** Blueprint／Runbook／Evaluation／Guardrails／Design／Spec の必須テンプレートを通じて、課題・制約・受入基準を実装前に固められること。
- **ROI-first planning:** `ROI_BUDGET` を軸に、価値・労力・リスク・確信度の評価済みストーリーから優先実装を決定できること。

## 2. Scope
_JP: スコープ_

### In scope / 対象範囲
- `docs/`: テンプレート群、BirdEye ライト運用資料、軽量バックログ。
- `recipes/`: 要約・要件分解・スコープ策定・設計変換・依存可視化の YAML 定義。
- `tools/`: レシピ実行、ROI 計算、LOC 集計、依存解析を支援するスクリプト。
- `config/`: モデルプロファイル、トークン予算、ROI 設定。
- `examples/`: 入出力サンプルと ROI 付与例。

### Out of scope / 非対象
- 大規模 BirdEye グラフや ADR／セキュリティ審査などのフルガバナンス。
- 7B で ≈1k トークン超、CPU で ≈500 トークン超の長大コンテキストを前提とした処理。
- ROI 予算超過を自動的に遮断する強制制御（警告のみ提供）。

## 3. Assumptions & Constraints
_JP: 前提と制約_

- **Context budgets:** CPU ≈500 トークン、7B ≈1,000 トークン、出力 ≈200–300 トークンを目安とし、必要に応じて要約／分割する。
- **Hardware:** GPU なしや量子化モデルを想定し、対話ターン数は最小限に抑える。
- **JSON outputs:** すべての LLM 応答は検証可能な JSON を返す。
- **ROI budget:** `ROI_BUDGET` で労力上限を管理し、超過ストーリーは保留扱いとする。
- **Design capacity:** ≈50k 行を超える見込みの場合はタスク分割や手動介入を検討する。

## 4. Key Components
_JP: 主な構成要素_

1. **Directory structure:** `docs/` にテンプレート、`recipes/` に YAML、`tools/` に補助スクリプト、`examples/` にサンプル、`config/` に設定を配置し、ツールの詳細は `tools/README.md` で補足する。
2. **Templates:** Blueprint、Runbook、Evaluation、Guardrails、Spec、Design で課題・スコープ・I/O・検証・統制を固定化する。
3. **Pipelines:** レシピランナーが入力を読み込み、LLM を呼び出し、`budget.max_input/max_output` を守りながら JSON を生成・検証する。
4. **ROI prioritisation:** 要件→SRS レシピで `value` `effort` `risk` `confidence` `roi_score` を付与し、スコープ計画レシピで `ROI_BUDGET` 内のストーリーを採択する。
5. **BirdEye-Lite:** 依存関係を抽出し、≤30 ノード／≤60 エッジの Mermaid グラフを生成してコンテキストを最小化する。
6. **Guardrails & evaluation:** `GUARDRAILS.md` と `EVALUATION.md` により行動基準と受入チェックを一元管理する。

## 5. Non-Functional Requirements
_JP: 非機能要件_

- **Portability:** Node.js または Python で動作し、重い依存や GPU を要求しない。
- **Extensibility:** レシピ・テンプレート・設定の追加を容易に行える汎用構造を保つ。
- **Maintainability:** Markdown／YAML と `CHANGELOG.md` による履歴管理でシンプルに保守できる。
- **Usability:** README と `examples/` で導入手順とサンプルを提示し、セットアップを迅速化する。

## 6. Implementation Notes
_JP: 実装メモ_

- トークン予算は推奨値であり、超過時は警告のみ行う。
- BirdEye-Lite、ROI プランナー、LOC チェッカーは任意利用だが、ガードレール遵守と ROI フロー実行を補助する目的で提供する。
- 生成物は `CHANGELOG.md` と各テンプレートで一貫して追跡する。
