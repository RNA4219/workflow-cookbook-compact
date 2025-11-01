# Downsized Workflow Cookbook: Requirements & Specification
_JP: ダウンサイザード Workflow Cookbook: 要件と仕様_

> 概要のみを確認したい場合は `docs/downsized_cookbook_summary.md` を参照してください。

## Snapshot Summary

| 項目 | 要約 | 詳細節 |
| --- | --- | --- |
| 目的 | 軽量環境で要約→要件→設計を最小ターンで遂行し統治理想を維持 | §1 |
| スコープ | Markdown テンプレート、YAML レシピ、軽量スクリプト、設定、サンプル | §2 |
| 制約 | トークン／ROI 予算、JSON 準拠、設計キャパ ≈50k 行、低リソース HW | §3 |
| コア要素 | ディレクトリ構成、テンプレート、レシピランナー、ROI 優先付け、BirdEye-Lite、ガードレール | §4 |
| 非機能 | 可搬性・拡張性・保守性・使いやすさを重視 | §5 |

## 1. Objectives
_JP: 目的_

- **Lightweight execution:** 1〜7B クラスのモデルで要約→要件→設計を少トークンで完了させる。
- **Governance retention:** Blueprint／Runbook／Evaluation／Guardrails／Design／Spec テンプレートで前提と制約を維持する。
- **ROI-first planning:** `ROI_BUDGET` を軸に価値・労力・リスク・確信度を評価し、優先タスクを選定する。

## 2. Scope
_JP: スコープ_

### In scope / 対象範囲
- `docs/`: テンプレート群、BirdEye ライト資料、軽量バックログ。
- `recipes/`: 要約・要件分解・スコープ策定・設計変換・依存可視化の YAML。
- 補助ツール: レシピ実行や ROI/LOC/依存チェックを行う外部スクリプト群（§4 参照）。
- `config/`: モデルプロファイル、トークン予算、ROI 設定。
- `examples/`: 入出力サンプルと ROI 付与例。

### Out of scope / 非対象
- 大規模 BirdEye グラフや ADR／セキュリティ審査などのフルガバナンス。
- 7B で ≈1k トークン超、CPU で ≈500 トークン超の長大コンテキストを前提とした処理。
- ROI 予算超過を自動的に遮断する強制制御（警告のみ提供）。

## 3. Assumptions & Constraints
_JP: 前提と制約_

- **Context budgets:** CPU ≈500 トークン、7B ≈1,000 トークン、出力 ≈200–300 トークン。超過時は要約や分割で調整。
- **Hardware:** GPU なしや量子化モデルを想定し、対話ターンは最小化する。
- **JSON outputs:** すべての LLM 応答は検証可能な JSON を返す。
- **ROI budget:** `ROI_BUDGET` で労力上限を管理し、超過ストーリーは保留する。
- **Design capacity:** 設計見積が ≈50k 行を超える場合はタスク分割や手動介入を検討する。

## 4. Key Components
_JP: 主な構成要素_

1. **Directory structure:**
   `docs/` にテンプレート、`recipes/` に YAML、補助ツールは外部スクリプトとして管理し、`examples/` にサンプル、`config/` に設定を配置する。
2. **Templates:**  
   Blueprint／Runbook／Evaluation／Guardrails／Spec／Design で課題・スコープ・I/O・検証・統制を固定化する。
3. **Pipelines:**  
   レシピランナーが `budget.max_input/max_output` を順守しながら LLM を呼び出し、JSON を生成・検証する。
4. **ROI prioritisation:**  
   要件→SRS レシピで `value` `effort` `risk` `confidence` `roi_score` を算出し、スコープ計画レシピで `ROI_BUDGET` 内のストーリーを選定する。
5. **BirdEye-Lite:**
   依存関係を抽出し、≤30 ノード／≤60 エッジの Mermaid グラフでコンテキストを最小化する。
6. **Guardrails & evaluation:**
   `docs/GUARDRAILS.md` と `docs/EVALUATION.md` で行動基準と受入チェックを管理する。

### Supplementary tools / 補助ツール概要

このリポジトリには実装済みスクリプトは含まれていませんが、以下の補助ツールを外部実装として運用することを想定しています。

- **レシピランナー**: YAML レシピを実行し、JSON 検証やトークン予算 (`budget.max_input/max_output`) の監視を担う外部実装。
- **BirdEye-Lite**: 依存関係を抽出し、≤30 ノード／≤60 エッジの Mermaid グラフを生成する可視化ツール。手順は `docs/BIRDSEYE.md` を参照。
- **ROI Planner**: `value` / `effort` / `risk` / `confidence` から `roi_score` を算出し、`ROI_BUDGET` 内のストーリー選定を補助。
- **LOC Budget Checker**: 設計キャパシティや推奨行数を超過しないかを確認し、超過時に警告するためのユーティリティ。

各ツールは ROI とトークン予算のガードレールを尊重し、検証可能な JSON を出力することを前提としています。

## 5. Non-Functional Requirements
_JP: 非機能要件_

- **Portability:** Node.js または Python で動作し、重い依存や GPU を要求しない。
- **Extensibility:** レシピ・テンプレート・設定の追加を容易に行える汎用構造を保つ。
- **Maintainability:** Markdown／YAML と `CHANGELOG.md` で履歴を追跡する。
- **Usability:** README と `examples/` で導入手順とサンプルを提供し、セットアップを簡易化する。

## 6. Implementation Notes
_JP: 実装メモ_

- トークン予算は推奨値であり、超過時は警告のみ行う。
- BirdEye-Lite、ROI プランナー、LOC チェッカーは任意利用だが、ガードレール遵守と ROI フローの補助として提供する。
- 生成物は `CHANGELOG.md` と各テンプレートで一貫して追跡する。
