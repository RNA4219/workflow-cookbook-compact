---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-14
next_review_due: 2025-11-14
---

# Downsized Workflow Cookbook / Codex Task Kit

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

ローカル CPU／小規模 GPU／安価な API を想定した軽量ワークフロー集です。オリジナル Cookbook の統治とガードレールを保ちながら、
**要約 → 要件整理 → 設計化** を単発または少ターンで進められるように整理しました。詳細要件は `docs/downsized_cookbook_requirements_spec.md` を参照してください。

> **クイックサマリー:** 主要ポイントのみを確認したい場合は `docs/downsized_cookbook_summary.md` を参照してください。

## サマリー

| 項目 | ハイライト |
| --- | --- |
| 対象 | Blueprint／Runbook／Evaluation／Guardrails／Spec／Design の必須テンプレートと最小限の YAML レシピ群 |
| 入出力 | すべて JSON を前提としたシングルターン中心のワークフロー |
| ハードウェア | GPU なし／量子化モデルでも実行可能、7B モデルは ≈1,000 トークン、CPU モデルは ≈500 トークンを想定 |
| ガバナンス | `HUB.codex.md` に統治ポリシーを集約し、BirdEye-Lite と ROI 設計で最小限の監査性を確保 |

## 主要アセット

- `docs/` – Blueprint / Runbook / Evaluation / Guardrails / Spec / Design ほか、BirdEye ライト運用と軽量バックログ (`BIRDSEYE.md`, `birdseye/`, `TASKS.md`)。
- `recipes/` – 要約、要件→SRS (ROI)、スコープ選定、設計変換、BirdEye 可視化の YAML 定義。
- `tools/` – レシピランナー (`runner.{ts,py}`)、BirdEye-Lite、ROI プランナー、LOC 予算チェッカー。
- `config/` – モデルプロファイルとトークン予算、ROI 設定。
- `examples/` – 入出力サンプルと ROI 付与例。

## 実行フロー

1. `docs/` のテンプレートをプロジェクト用に複製し、課題・スコープ・制約・検証基準を記述。
2. `.env` 等で `ROI_BUDGET` とプロファイルを設定し、`recipes/req_to_srs_roi.yaml` → `recipes/srs_scope_plan.yaml` で ROI 選定。
3. `tools/runner.{ts,py}` でレシピを実行し、`budget.max_input/max_output` 内で JSON 成果物を取得。
4. `tools/birdseye_lite.py` で最大 30 ノード／60 エッジの依存グラフを生成し、成果物に添付。
5. `docs/EVALUATION.md` のチェックリストでスキーマ検証・ROI コンプライアンスを確認し、`CHANGELOG.md` に記録。

## レシピ一覧

| ファイル | 役割 | 主出力 |
| --- | --- | --- |
| `summarize.yaml` | 入力要約 | 箇条書き JSON 要約 |
| `req_to_srs_roi.yaml` | 要件→SRS 分解 | `value` / `effort` / `risk` / `confidence` / `roi_score` |
| `srs_scope_plan.yaml` | ROI ベースの採択 | 予算内ストーリーと保留ストーリー |
| `srs_to_design_roi.yaml` | SRS→設計対応付け | ストーリー別のモジュール／インターフェース表 |
| `birdseye_summary.yaml` | 依存関係要約 | 主要エッジのみの Mermaid グラフ |

## 制約と前提

- 入力は CPU ≈500 トークン／7B ≈1,000 トークン、出力は 200–300 トークンを目安に分割や要約を行う。
- すべての LLM 応答は JSON スキーマで検証可能な形に揃える。
- `ROI_BUDGET` が労力上限を制御し、超過ストーリーは自動保留。
- 設計キャパシティは ≈50k 行規模をガイドラインとし、超過時はタスク分割を検討。

## ツールと自動化

- **Runner** – レシピ読み込み、プロンプト組立、JSON スキーマ検証、成果保存までを一括実行。
- **BirdEye-Lite** – 依存解析を行い、トークン予算内で扱える小型 Mermaid グラフを生成。
- **ROI Planner** – ストーリーごとの ROI 計算と `ROI_BUDGET` 内の採択を支援。
- **LOC Budget Checker** – 目安行数を計測し、設計キャパシティ超過を警告。

## ガバナンス

- `GUARDRAILS.md` で長文事前要約やモデル能力の遵守など行動原則を定義。
- `EVALUATION.md` でスキーマ／受入基準／ROI テストをチェックリスト化。
- `HUB.codex.md` でテンプレートとタスクオーケストレーション方針を統合。
- すべての更新を `CHANGELOG.md` に記録。

## 追加ドキュメント

- 詳細な要件と仕様: `docs/downsized_cookbook_requirements_spec.md`
- BirdEye 運用: `docs/BIRDSEYE.md`, `docs/birdseye/`
- タスク管理: `docs/TASKS.md`

このテンプレート群を活用することで、限られたリソースでもガバナンスを維持しながら迅速なワークフロー運用が可能になります。
