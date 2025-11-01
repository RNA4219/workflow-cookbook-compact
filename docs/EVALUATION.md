---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-14
next_review_due: 2025-11-14
---

# Evaluation

## Acceptance Criteria

- 各 Markdown には Intent メタデータ（intent_id / owner / status / review 日付）が残り、変更内容に合わせて更新されている。
- `README.md`・`docs/downsized_cookbook_requirements_spec.md`・`docs/downsized_cookbook_summary.md` の記述が変更差分と矛盾しない。
- `recipes/*.yaml` の `budget.*` 設定や出力スキーマに変更が入る場合は、`config/` と `examples/` の対応する値を併せて確認・更新する。
- 重大な不具合が判明した際は `docs/RUNBOOK.md#observability` に沿って初動記録を残し、関連差分から参照できるようリンクする。

## KPIs

| 指標 | 目的 | 収集方法 | 目標値 |
| --- | --- | --- | --- |
| `doc_alignment` | 主要ドキュメント間の記述差異を早期に把握する。 | `README.md`・`docs/downsized_cookbook_requirements_spec.md`・`docs/downsized_cookbook_summary.md` の対応セクションをレビューし、差異があれば同一 PR 内で整合させる。 | 100% 整合 |
| `roi_traceability` | ROI の算定根拠と設定値を追跡できる状態を保つ。 | `recipes/req_to_srs_roi.yaml`・`recipes/srs_scope_plan.yaml` の `budget.*` と `config/` の ROI 設定、`examples/requirements.md` のフィールドを照合する。 | 更新から 1 営業日以内に同期 |
| `changelog_freshness` | ユーザー影響がある変更を迅速に記録する。 | リリース対象差分では `CHANGELOG.md` の `[Unreleased]` に通番付き項目を追加する。 | 対象変更の 100% |

> KPI の確認結果は `docs/RUNBOOK.md#observability` の共有手順に沿って記録し、乖離があれば双方のドキュメントを更新する。

## Test Outline

- 単体: `examples/requirements.md` を基に `recipes/req_to_srs_roi.yaml` の出力スキーマ（`value` / `effort` / `risk` / `confidence` / `roi_score`）を確認する。
- 結合: `recipes/srs_scope_plan.yaml` と `config/budget.yaml`・`config/profiles.yaml` の整合性を確認し、優先順位が `ROI_BUDGET` 内に収まることを検証する。
- 回帰: `docs/BIRDSEYE.md` の手順で依存グラフを見直し、更新したノードが `docs/birdseye/index.json` に正しく反映されているか点検する。

## Verification Checklist

- [ ] 主要フローが動作する（手動確認）
- [ ] エラー時挙動が明示されている
- [ ] 依存関係が再現できる環境である
