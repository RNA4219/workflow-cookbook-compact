---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-14
next_review_due: 2025-11-14
---

# Changelog

## [Unreleased]

- 次の改善項目をここへ追記してください。

## 1.0.0 - 2025-10-16

### Added

- `README.md` をローカル LLM 向けの Downsized Workflow Cookbook 概要へ再構成し、軽量運用の目的・前提・標準フロー・主要レシピを集約。【F:README.md†L1-L66】
- `docs/downsized_cookbook_requirements_spec.md` と `docs/downsized_cookbook_summary.md` を追加し、制約・要件・導線をリファレンス／チェックリスト形式で即参照できるようにした。【F:docs/downsized_cookbook_requirements_spec.md†L1-L87】【F:docs/downsized_cookbook_summary.md†L1-L39】
- ROI とトークン予算の初期値を `config/budget.yaml` と `config/profiles.yaml` に定義し、軽量モデル選定とコスト配分の開始点を提供。【F:config/budget.yaml†L1-L8】【F:config/profiles.yaml†L1-L16】
- 要約→要件分解→ROI 採択→設計化→可視化を支える最小限の YAML レシピを `recipes/` に整備し、JSON スキーマとトークン予算を明示。【F:recipes/summarize.yaml†L1-L37】【F:recipes/req_to_srs_roi.yaml†L1-L66】【F:recipes/srs_scope_plan.yaml†L1-L48】【F:recipes/srs_to_design_roi.yaml†L1-L66】【F:recipes/birdseye_summary.yaml†L1-L47】
- `docs/` 配下に Blueprint／Design／Evaluation／Guardrails／Runbook／Spec／BirdEye テンプレートとガイドラインを再収録し、軽量フォークでのガバナンス資料をひとまとめにした。【F:docs/BLUEPRINT.md†L1-L41】【F:docs/DESIGN.md†L1-L22】【F:docs/EVALUATION.md†L1-L38】【F:docs/GUARDRAILS.md†L1-L160】【F:docs/RUNBOOK.md†L1-L149】【F:docs/SPEC.md†L1-L23】【F:docs/BIRDSEYE.md†L1-L56】
- サンプル入出力と要件定義例を `examples/` に配置し、軽量ワークフローの初回実行イメージを共有。【F:examples/input.txt†L1-L9】【F:examples/requirements.md†L1-L74】

### Changed

- 既存テンプレート群をローカル LLM／低リソース前提へ最適化し、`docs/TASKS.md` や `docs/EVALUATION.md` で ROI 指向の意思決定・検証手順を更新。【F:docs/TASKS.md†L1-L75】【F:docs/EVALUATION.md†L1-L38】
- `docs/RUNBOOK.md` と `docs/BIRDSEYE.md` を ≤30 ノード／≤60 エッジの BirdEye Lite 運用と JSON 検証ワークフローへ差し替え、軽量 CI なしでも再現できるよう整理。【F:docs/RUNBOOK.md†L1-L149】【F:docs/BIRDSEYE.md†L1-L56】
- `docs/GUARDRAILS.md` を再編集し、タスク分解・要約・設計化でのガードレールと失敗モード対策を簡潔に統合。【F:docs/GUARDRAILS.md†L1-L160】

### Removed

- 旧ブランド固有の記述や重複していたセキュリティワークフロー参照を全削除し、軽量フォークに不要な CI・SLO 記述を排除。【F:README.md†L1-L66】【F:docs/GUARDRAILS.md†L1-L160】

## 0.1.0 - 2025-10-13

- オリジナル Workflow Cookbook から意図・運用ポリシー・テンプレートを抽出し、軽量フォーク立ち上げの土台を作成。
