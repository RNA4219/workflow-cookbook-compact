# Downsized Workflow Cookbook: Requirements & Specification
_JP: ダウンサイザード Workflow Cookbook: 要件と仕様_

## 1. Objectives
_JP: 目的_

- **Lightweight execution:** ローカル CPU（1〜3B）や小規模 GPU（≈7B）／安価な API でも、要約→要件→設計のワークフローを少ないトークンで実行できること。
- **Governance retention:** Blueprint / Runbook / Evaluation / Guardrails / Design / Spec の必須テンプレートを維持し、課題・制約・受入基準を実装前に確定できること。
- **ROI-first planning:** `ROI_BUDGET` を基準に、価値・労力・リスク・確信度を持つストーリーのみを優先実装すること。

## 2. Scope
_JP: スコープ_

### In scope / 対象範囲
- Markdown テンプレート群と BirdEye ライト運用資料、軽量バックログ (`docs/`)。
- 要約／要件分解／スコープ策定／設計変換／依存可視化の YAML レシピ (`recipes/`)。
- レシピ実行・ROI 計算・LOC 集計・依存解析を行う軽量スクリプト (`tools/`)。
- モデルプロファイル／トークン予算などの設定 (`config/`)、サンプル入出力 (`examples/`)。

### Out of scope / 非対象
- 大規模 BirdEye グラフやフルガバナンス（ADR 管理、セキュリティ審査など）。
- 7B で ≈1k トークン超、CPU で ≈500 トークン超の長大コンテキストを前提とするパイプライン。
- 予算超過の自動ブロック（警告のみ実施）。

## 3. Assumptions & Constraints
_JP: 前提と制約_

- **Context budgets:** 入力は CPU ≈500 トークン／7B ≈1,000 トークン、出力は ≈200–300 トークンをガイドラインとする。必要に応じて要約や分割を行う。
- **Hardware:** GPU なしや量子化モデルを想定し、対話ターン数は最小限とする。
- **JSON outputs:** すべての LLM 応答は検証可能な JSON を返す。
- **ROI budget:** `ROI_BUDGET` で労力上限を制御し、超過ストーリーは保留とする。
- **Design capacity:** ≈50k 行規模を超える場合はタスク分割や手動介入を検討する。

## 4. Key Components
_JP: 主な構成要素_

1. **Directory structure:** `docs/` にテンプレート、`recipes/` に YAML、`tools/` にスクリプト、`examples/` にサンプル、`config/` に設定、ルートに `HUB.codex.md` を配置する。
2. **Templates:** Blueprint（課題・スコープ・I/O）、Runbook（環境・手順・検証）、Evaluation（受入・KPI・チェック）、Guardrails（行動指針・最小コンテキスト）、Spec & Design（I/O・状態・エラー・ディレクトリ設計）。
3. **Pipelines:** レシピランナーが単発実行を基本とし、入力ファイルを読んで LLM を呼び出し、JSON 出力を生成・検証する。`budget.max_input/max_output` を遵守する。
4. **ROI prioritisation:** 要件→SRS レシピで `value` `effort` `risk` `confidence` `roi_score` を付与し、スコープ計画レシピで `ROI_BUDGET` 内のストーリーを選定する。
5. **BirdEye-Lite:** 依存関係を抽出して ≤30 ノード／≤60 エッジの Mermaid グラフを生成し、最小限のコンテキスト取り込みを維持する。
6. **Guardrails & evaluation:** `GUARDRAILS.md` に安全な LLM 活用ルールを記述し、`EVALUATION.md` のチェックリストでスキーマ検証・ROI 準拠・受入基準を確認できるようにする。

## 5. Non-Functional Requirements
_JP: 非機能要件_

- **Portability:** Node.js または Python で動作し、重い依存や GPU を要求しない。
- **Extensibility:** 新規レシピ・テンプレート・予算設定を容易に追加できる汎用構造とする。
- **Maintainability:** Markdown／YAML を採用し、`CHANGELOG.md` で履歴管理を行う。
- **Usability:** README に導入手順、`examples/` にサンプル、`config/` にデフォルト値を用意し、セットアップを迅速化する。

## 6. Implementation Notes
_JP: 実装メモ_

- トークン予算は推奨値であり、超過時は警告を出すが強制停止しない。
- BirdEye-Lite・ROI プランナー・LOC チェッカーは任意利用だが、ガードレール遵守と ROI フローの実行を補助するために提供する。
- 生成物は `CHANGELOG.md` と各テンプレートで一貫して追跡する。
