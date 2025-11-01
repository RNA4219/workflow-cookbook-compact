# Downsized Workflow Cookbook: クイックサマリー

本サマリーは `README.md` と `docs/downsized_cookbook_requirements_spec.md` の主要情報を圧縮した確認シートです。軽量環境でワークフローを運用する際の前提と導線だけを抽出しています。

## 概要
- **目的:** 要約→要件→設計の一連フローを少ターンで完遂し、Blueprint／Runbook／Evaluation／Guardrails／Spec／Design を維持する（`docs/downsized_cookbook_requirements_spec.md` §1）。
- **対象:** JSON を入出力とする Markdown／YAML 主体のテンプレート群と ROI 指向のレシピセット（同 §2）。
- **想定環境:** CPU ≈500 トークン〜小規模 GPU・量子化 7B モデル ≈1,000 トークン（同 §3）。

## ディレクトリと主資産
| パス | 役割 | 主なアセット |
| --- | --- | --- |
| `docs/` | ガバナンスおよびテンプレート | Blueprint, Runbook, Evaluation, Guardrails, Spec, Design, `BIRDSEYE.md`, `TASKS.md` |
| `recipes/` | LLM レシピ | `summarize.yaml`, `req_to_srs_roi.yaml`, `srs_scope_plan.yaml`, `srs_to_design_roi.yaml`, `birdseye_summary.yaml` |
| `tools/` | 補助スクリプトのガイド | `tools/README.md`（BirdEye-Lite・ROI/LOC チェックの概要） |
| `config/` | モデル・ROI 設定 | モデルプロファイル、`ROI_BUDGET` |
| `examples/` | サンプル成果物 | ROI 付与例、入出力例 |

## 推奨フロー
1. `docs/` テンプレートに課題・制約・検証基準を記入し初期状態を固める。
2. `.env` と `config/` を基に `ROI_BUDGET` を調整し、`recipes/req_to_srs_roi.yaml` と `recipes/srs_scope_plan.yaml` で採択ストーリーを決定。
3. LLM ランナーで各レシピを実行し、`budget.max_input/max_output` と JSON 検証を順守する。
4. `docs/BIRDSEYE.md` に沿って BirdEye-Lite 相当ツールで ≤30 ノード／≤60 エッジの依存グラフを生成し、`docs/EVALUATION.md`・`CHANGELOG.md` で検証と記録を行う。

## 要件ハイライト
- **実行要件:** トークン上限内での実行・必要に応じた要約／分割・検証可能な JSON 出力（`docs/downsized_cookbook_requirements_spec.md` §3）。
- **統治理想:** ガードレール資料とテンプレートを成果物として保持し、ROI 指向で優先度を決定（同 §4）。
- **範囲:** Markdown／YAML／軽量スクリプト／設定／サンプルが対象で、大規模 BirdEye や自動 ROI ブロッカーは非対象（同 §2）。
- **非機能:** 可搬性・拡張性・保守性・使いやすさを重視し、履歴は `CHANGELOG.md` で追跡（同 §5）。

## ガバナンスと補助資料
- `docs/GUARDRAILS.md`: 行動指針と鮮度管理。
- `docs/EVALUATION.md`: スキーマ検証・ROI 監査・受入基準。
- `docs/TASKS.md`: タスクシードの起点とログ運用。
- `docs/BIRDSEYE.md` / `docs/birdseye/*.json`: 依存関係の可視化と更新手順。
- `CHANGELOG.md`: 変更履歴の記録先。

## 参照
- 詳細要件: `docs/downsized_cookbook_requirements_spec.md`
- 導入・背景: `README.md`
