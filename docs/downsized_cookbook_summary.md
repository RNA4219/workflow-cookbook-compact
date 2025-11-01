# Downsized Workflow Cookbook: クイックサマリー

本サマリーは `README.md` と `docs/downsized_cookbook_requirements_spec.md` の主要情報を一望できるよう再整理したものです。軽量な実行環境でワークフローを構築する際の確認シートとして活用してください。

## 概要
- **目的:** 要約→要件→設計を少ターンで実施しつつ、Blueprint／Runbook／Evaluation／Guardrails／Spec／Design の統治テンプレートを維持。
- **対象:** JSON ベースのシングルターン中心ワークフロー、ROI 指向のレシピとテンプレート群。
- **想定環境:** GPU なしの CPU（≈500 トークン）〜小規模 GPU・量子化 7B モデル（≈1,000 トークン）。

## ディレクトリと主資産
| パス | 役割 | キーアセット |
| --- | --- | --- |
| `docs/` | テンプレートとガバナンス資料 | Blueprint, Runbook, Evaluation, Guardrails, Spec, Design, `BIRDSEYE.md`, `TASKS.md` |
| `recipes/` | YAML レシピ | `summarize.yaml`, `req_to_srs_roi.yaml`, `srs_scope_plan.yaml`, `srs_to_design_roi.yaml`, `birdseye_summary.yaml` |
| `tools/` | 補助ツール | コンセプト概要のみ（レシピランナーや BirdEye-Lite などの実装は別途用意） |
| `config/` | プロファイル・予算設定 | モデル設定、ROI 設定 |
| `examples/` | サンプル入出力 | ROI 付与例、成果物サンプル |

## 推奨フロー
1. テンプレート複製：課題・制約・検証基準を `docs/` テンプレートに記述。
2. ROI 設定：`.env` などで `ROI_BUDGET` とプロファイルを調整し、`req_to_srs_roi.yaml` → `srs_scope_plan.yaml` で採択。
3. レシピ実行：任意のレシピランナー（JSON 検証・トークン予算対応済みのもの）で `budget.max_input/max_output` を順守。
4. 可視化：`docs/BIRDSEYE.md` の手順に沿って BirdEye-Lite 相当のツール（外部実装）で ≤30 ノード／≤60 エッジの依存グラフを生成。
5. 監査：`docs/EVALUATION.md` チェックリストでスキーマ・ROI・受入基準を確認し、`CHANGELOG.md` に記録。

## 要件サマリー
- **Lightweight execution:** トークン予算を守り、必要に応じて要約・分割を行う。
- **Governance retention:** ガードレール資料とテンプレートを必須成果物として維持。
- **ROI-first planning:** `value` `effort` `risk` `confidence` `roi_score` を指標に `ROI_BUDGET` 内で採択。

### スコープ
- **対象:** Markdown テンプレート、YAML レシピ、軽量スクリプト、設定ファイル、サンプル。
- **非対象:** 大規模 BirdEye グラフ、長大トークン前提のパイプライン、予算超過の自動ブロック。

### 前提・制約
- 入力は CPU ≈500 トークン／7B ≈1,000 トークン、出力は ≈200–300 トークンを目安。
- GPU なしでも動作し、対話ターン数は最小限。
- すべての LLM 応答は検証可能な JSON。
- `ROI_BUDGET` が労力上限を制御し、超過ストーリーは保留。
- 設計キャパシティ ≈50k 行を超える場合はタスク分割を検討。

### 非機能要件
- **Portability:** Node.js / Python で動作し、重い依存を避ける。
- **Extensibility:** レシピ・テンプレート・予算設定の追加が容易。
- **Maintainability:** Markdown／YAML を採用し、`CHANGELOG.md` で履歴管理。
- **Usability:** README と `examples/` に導入手順とサンプルを提供。

## ガバナンスと補助ツール
- `GUARDRAILS.md` で安全な LLM 活用ルールを定義。
- `EVALUATION.md` でスキーマ検証・ROI 準拠・受入基準をチェック。
- `HUB.codex.md` でテンプレート方針とタスクオーケストレーションを統合。
- BirdEye-Lite・ROI Planner・LOC Budget Checker は任意利用だが監査性向上に寄与。

## 参照
- 詳細要件: `docs/downsized_cookbook_requirements_spec.md`
- 包括的説明: `README.md`
