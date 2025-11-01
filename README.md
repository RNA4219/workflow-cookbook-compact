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

## クイックリファレンス

| カテゴリ | チェック項目 | 詳細リソース |
| --- | --- | --- |
| 目的 | 要約→要件→設計を少ターンで完遂し、テンプレートとガードレールを維持 | `docs/downsized_cookbook_requirements_spec.md` §1 |
| スコープ | Markdown テンプレート／YAML レシピ／軽量ツールと設定一式 | 同 §2 |
| 前提 | 入力 ≈500–1,000 トークン、JSON 準拠、ROI 上限、設計キャパ ≈50k 行 | 同 §3 |
| ワークフロー | テンプレート整備→ROI 選定→レシピ実行→BirdEye 可視化→評価チェック | 「実行フロー」節 |
| ガバナンス | Guardrails・Evaluation・BirdEye ライト・CHANGELOG で監査性確保 | 「ガバナンス」節 |

### 最初に読むべきドキュメント

- `docs/downsized_cookbook_summary.md` – README と要件仕様を要約したチェックリスト。
- `docs/downsized_cookbook_requirements_spec.md` – 目的／スコープ／制約の正式な要件定義。
- `HUB.codex.md` – テンプレート運用とタスクオーケストレーションの基準。

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

1. **テンプレート整備:** `docs/` から必要テンプレートを複製し、課題・制約・検証基準を記述。
2. **ROI 設定:** `.env` などで `ROI_BUDGET`／モデルプロファイルを調整し、`recipes/req_to_srs_roi.yaml` と `recipes/srs_scope_plan.yaml` で採択候補を決定。
3. **レシピ実行:** `tools/runner.{ts,py}` で LLM 呼び出し・JSON スキーマ検証を実施し、`budget.max_input/max_output` を厳守。
4. **依存可視化:** `tools/birdseye_lite.py` で ≤30 ノード／≤60 エッジの Mermaid グラフを生成し成果物に添付。
5. **検証と記録:** `docs/EVALUATION.md` チェックリストでスキーマ／ROI／受入基準を確認し、`CHANGELOG.md` に追記。

## レシピ一覧

| ファイル | 役割 | 主出力 |
| --- | --- | --- |
| `summarize.yaml` | 入力要約 | 箇条書き JSON 要約 |
| `req_to_srs_roi.yaml` | 要件→SRS 分解 | `value` / `effort` / `risk` / `confidence` / `roi_score` |
| `srs_scope_plan.yaml` | ROI ベースの採択 | 予算内ストーリーと保留ストーリー |
| `srs_to_design_roi.yaml` | SRS→設計対応付け | ストーリー別のモジュール／インターフェース表 |
| `birdseye_summary.yaml` | 依存関係要約 | 主要エッジのみの Mermaid グラフ |

## 制約と前提

- **トークン予算:** CPU モデルは入力 ≈500 トークン、7B モデルは ≈1,000 トークン、出力は ≈200–300 トークンを目安に要約や分割を実施。
- **フォーマット:** すべての LLM 応答は検証可能な JSON スキーマに準拠。
- **ROI 制御:** `ROI_BUDGET` で労力上限を管理し、超過ストーリーは自動保留。
- **設計キャパシティ:** 約 50k 行を超える見込みの場合はタスク分割や手動介入を検討。
- **ハードウェア:** GPU なしでも動作可能な軽量モデルを前提とし、対話ターン数を最小化。

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
