---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-14
next_review_due: 2025-11-14
---

# Downsized Workflow Cookbook / Codex Task Kit

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

ローカル CPU／小規模 GPU／安価な API を想定した軽量ワークフロー集です。オリジナル Cookbook の統治とガードレールを維持しながら、**要約 → 要件整理 → 設計化** を単発または少ターンで完遂するための最小セットを収録しています。詳細は `docs/downsized_cookbook_requirements_spec.md`、概要は `docs/downsized_cookbook_summary.md` を参照してください。

## クイックリファレンス

| カテゴリ | 要点 | 主な参照 |
| --- | --- | --- |
| 目的 | 少ターンで要約→要件→設計を完了しガードレールを維持 | `docs/downsized_cookbook_requirements_spec.md` §1 |
| スコープ | Markdown テンプレート、YAML レシピ、軽量スクリプト、設定、サンプル | 同 §2 |
| 前提 | 入出力トークン上限、JSON スキーマ準拠、ROI 予算、設計キャパ ≈50k 行 | 同 §3 |
| ワークフロー | テンプレート整備→ROI 選定→レシピ実行→BirdEye 可視化→評価・記録 | 本 README「標準ワークフロー」 |
| ガバナンス | Guardrails／Evaluation／BirdEye／CHANGELOG による監査性 | `docs/EVALUATION.md`, `docs/GUARDRAILS.md`, `docs/TASKS.md` |

### 最初に読むドキュメント

- `docs/downsized_cookbook_summary.md` – チェックリスト形式の概要。
- `docs/downsized_cookbook_requirements_spec.md` – 目的・スコープ・制約の詳細仕様。
- `docs/TASKS.md` – タスクシード運用と簡易オーケストレーションの手引き。

## 構成概要

- `docs/` – Blueprint / Runbook / Evaluation / Guardrails / Spec / Design テンプレートと BirdEye ライト関連資料。
- `recipes/` – 要約、要件分解、ROI 選定、設計変換、依存可視化の YAML レシピ。
- 補助ツール – 外部スクリプトの概要は `docs/downsized_cookbook_requirements_spec.md` §4 を参照。
- `config/` – モデルプロファイルとトークン予算、ROI 設定。
- `examples/` – サンプル入出力と ROI 付与例。

## 標準ワークフロー

1. `docs/` のテンプレートで課題・制約・検証基準を定義。
2. `.env` と `config/` を基に `ROI_BUDGET`／モデルプロファイルを調整し、`recipes/req_to_srs_roi.yaml` と `recipes/srs_scope_plan.yaml` で優先ストーリーを決定。
3. `recipes/*.yaml` を任意の LLM ランナーで実行し、`budget.max_input/max_output` と JSON スキーマを検証。
4. `docs/BIRDSEYE.md` の手順で ≤30 ノード／≤60 エッジの Mermaid グラフを作成。
5. `docs/EVALUATION.md` で成果を確認し、`CHANGELOG.md` に記録。

## 主なレシピとツール

| ファイル | 目的 | 主な出力 |
| --- | --- | --- |
| `recipes/summarize.yaml` | 入力要約 | 箇条書き JSON |
| `recipes/req_to_srs_roi.yaml` | 要件の SRS 分解と ROI 評価 | `value` / `effort` / `risk` / `confidence` / `roi_score` |
| `recipes/srs_scope_plan.yaml` | ROI に基づく採択 | 予算内・保留ストーリー |
| `recipes/srs_to_design_roi.yaml` | SRS→設計マッピング | ストーリー別モジュール一覧 |
| `recipes/birdseye_summary.yaml` | 依存可視化 | Mermaid グラフ |

補助ツールの役割と前提条件は `docs/downsized_cookbook_requirements_spec.md` §4「Supplementary tools」に集約しています。

## ガバナンスと記録

- `docs/GUARDRAILS.md` で行動原則と長文要約手順を管理。
- `docs/EVALUATION.md` でスキーマ適合・ROI 準拠・受入基準を確認。
- 変更履歴は `CHANGELOG.md` に記録します。
- タスク分解と記録は `docs/TASKS.md` を基準に管理します。

このテンプレート群を活用することで、限られたリソースでもガバナンスを維持しながら迅速なワークフロー運用が可能になります。
