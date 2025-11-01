---
intent_id: DOC-LEGACY
owner: docs-core
status: active
last_reviewed_at: 2025-10-28
next_review_due: 2025-11-28
---

# Task Seeds 運用ガイド

## 1. 目的

- `HUB.codex.md` や `BLUEPRINT.md` などで抽出された課題を、着手可能な Task Seed として整理する。
- `docs/EVALUATION.md` と `docs/downsized_cookbook_requirements_spec.md` に記載された基準と突合し、受け入れ条件を明確にする。
- 実施内容は `CHANGELOG.md` や関連 PR から追跡できるように記録する。

## 2. 記入テンプレート

Task Seed は本ドキュメントで示すテンプレートに準拠し、以下の要点を押さえる。

```markdown
---
intent_id: INT-xxx
owner: contributor-handle
status: planned|active|...
last_reviewed_at: YYYY-MM-DD
next_review_due: YYYY-MM-DD
---

# Task Seed Title

## Objective
- 目的を一文で記す。

## Scope
- In: 影響範囲（ディレクトリや機能名）
- Out: 明示的に触れない領域

## Requirements
- Behavior / I/O / Constraints / Acceptance Criteria を本テンプレートと同じ粒度で箇条書き。
- Lint/Type/Test のゼロエラーを必須条件として明記する。

## Affected Paths
- グロブ表記で変更予定ファイル群を列挙。

## Local Commands
- 利用スタックに応じたゲートコマンドをテンプレート内の例から抜粋。

## Deliverables
- PR 要約・Intent 明記・必要なドキュメント差分を記載。
```

> **用語補足**: `Objective`・`Scope`・`Requirements` の定義は `docs/downsized_cookbook_requirements_spec.md` の該当セクションと整合させる。

## 3. 検証ログ（TDD 前提）

1. **テスト設計を先行**: 着手前に必要なユニット/統合テストを列挙し、期待する失敗/成功条件を `Tests` セクションへ記す。
2. **実行コマンドの記録**: `Tests` もしくは `Commands` セクションに、実際に走らせたコマンドと結果（例: `pytest -q` → fail/pass）を時系列で追記する。
3. **インシデントとの連携**: 重大な不具合に遭遇した場合は `docs/RUNBOOK.md#observability` の初動手順に沿って共有し、検証ログから参照できるようリンクを残す。
4. **評価基準の照合**: ゲート通過後は `docs/EVALUATION.md` を確認し、未完了項目があれば Follow-up へ移す。

## 4. フォローアップ手順

- **未解決事項**: 実装後も残るリスクや TODO は `Follow-ups` セクションに列挙し、必要なら新規 Task Seed を起票する。
- **情報同期**: 追記した Task Seed は `HUB.codex.md` の分類に基づき、関連ドキュメント（Blueprint /
  Guardrails / Incident）とのリンクを整備する。
- **レビュー結果の反映**: レビュアーからの追加要求は `Notes` に記録し、着手が別タスクになる場合は Task Seed ID を採番して紐付ける。
- **完了判定**: `docs/EVALUATION.md` の条件を満たし、検証ログがすべてグリーンであることを確認して `status: done` へ更新する。
- **Changelog 通番**: 変更履歴を編集する場合は `CHANGELOG.md` の最新通番を確認し、既存の最大値に 1 を加えて 4 桁ゼロ埋めで記録する。
- **成果の転記**: 完了した Task Seed の成果差分は `[Unreleased](../CHANGELOG.md#unreleased)` に通番付きで記録し、
  当該 Task Seed からリンクを張って追跡できるようにする。

---

更新日: 2025-10-14
