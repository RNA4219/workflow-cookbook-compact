# Downsized Workflow Cookbook: クイックサマリー

本サマリーは `README.md` と `docs/downsized_cookbook_requirements_spec.md` の主要情報を圧縮した確認シートです。軽量環境でワークフローを運用する際の要点のみを抽出しています。

## 概要
- **目的:** 要約→要件→設計を少ターンで完遂し、Blueprint／Runbook／Evaluation／Guardrails／Spec／Design を維持する（`docs/downsized_cookbook_requirements_spec.md` §1）。
- **対象:** JSON 出力を前提とした Markdown／YAML テンプレート、ROI 指向レシピ、補助スクリプト（同 §2）。
- **制約:** CPU ≈500 トークン／7B ≈1,000 トークン、出力 ≈200–300 トークン、`ROI_BUDGET` による労力管理（同 §3）。

## ディレクトリと主資産
| パス | 役割 | 主なアセット |
| --- | --- | --- |
| `docs/` | ガバナンスおよびテンプレート | Blueprint, Runbook, Evaluation, Guardrails, Spec, Design, `BIRDSEYE.md`, `TASKS.md` |
| `recipes/` | LLM レシピ | `summarize.yaml`, `req_to_srs_roi.yaml`, `srs_scope_plan.yaml`, `srs_to_design_roi.yaml`, `birdseye_summary.yaml` |
| 補助ツール | 外部スクリプトのガイド | `docs/downsized_cookbook_requirements_spec.md` §4（BirdEye-Lite・ROI/LOC チェックの概要） |
| `config/` | モデル・ROI 設定 | モデルプロファイル、`ROI_BUDGET` |
| `examples/` | サンプル成果物 | ROI 付与例、入出力例 |

## 推奨フロー
1. `docs/` テンプレートで課題・制約・検証基準を定義する。
2. `config/` のモデルプロファイルと `ROI_BUDGET` を確認し、`recipes/req_to_srs_roi.yaml`／`recipes/srs_scope_plan.yaml` で優先ストーリーを選定する。
3. `recipes/*.yaml` を実行しつつ `budget.max_input/max_output` と JSON 検証を順守し、`docs/BIRDSEYE.md`・`docs/EVALUATION.md`・`CHANGELOG.md` に沿って可視化と記録を行う。

## 要件ハイライト
- **実行:** トークン上限内での運用、必要時の要約・分割、検証可能な JSON 出力（`docs/downsized_cookbook_requirements_spec.md` §3）。
- **統治:** ガードレール資料とテンプレートを成果物として保持し、ROI 指向で優先度を決定（同 §4）。
- **範囲:** Markdown／YAML／軽量スクリプト／設定／サンプルを対象とし、大規模 BirdEye や自動 ROI ブロッカーは非対象（同 §2）。
- **非機能:** 可搬性・拡張性・保守性・使いやすさを重視し、履歴は `CHANGELOG.md` で追跡（同 §5）。

## ガバナンスと補助資料
- `docs/GUARDRAILS.md` – 行動指針。
- `docs/EVALUATION.md` – スキーマ検証と受入基準。
- `docs/TASKS.md` – タスクシード運用。
- `docs/BIRDSEYE.md`／`docs/birdseye/*.json` – 依存関係の可視化。
- `CHANGELOG.md` – 変更履歴の記録。

## 参照
- 詳細要件: `docs/downsized_cookbook_requirements_spec.md`
- 導入・背景: `README.md`
