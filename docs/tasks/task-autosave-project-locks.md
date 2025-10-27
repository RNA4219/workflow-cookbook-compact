---
intent_id: INT-001
owner: docs-core
status: planned
last_reviewed_at: 2025-01-14
next_review_due: 2025-02-14
---

# Task Seed: AutoSave Project Locks

## 背景

- AutoSave のロック整合性と Merge 精度モードの切替を同期させる必要がある。
- [docs/IMPLEMENTATION-PLAN.md](../IMPLEMENTATION-PLAN.md) で定義した段階導入フローにより、ユーザー影響を最小化する。
- 詳細設計は [docs/AUTOSAVE-DESIGN-IMPL.md](../AUTOSAVE-DESIGN-IMPL.md) と [docs/MERGE-DESIGN-IMPL.md](../MERGE-DESIGN-IMPL.md) に委譲する。

## ゴール

- `autosave.project_lock` と `merge.precision_mode` のフラグを段階導入し、主要ユースケースのデータ損失ゼロを保証する。
- AutoSave と Merge のログを統合し、テレメトリで回帰が検出された場合に即時ロールバック可能とする。

## TDD

1. AutoSave の不変条件を検証するシナリオテストを追加し、[docs/AUTOSAVE-DESIGN-IMPL.md](../AUTOSAVE-DESIGN-IMPL.md) の I/O 契約を満たすことを確認する。
2. Merge 精度モードごとの比較テストを作成し、[docs/MERGE-DESIGN-IMPL.md](../MERGE-DESIGN-IMPL.md) のロック協調要件を満たすことを検証する。
3. フラグ状態遷移とロールバックを `baseline` → `strict` → `baseline` で往復させ、実装計画に沿った可逆性を確認する。

## ロールバック手順

1. テレメトリ指標が閾値を超えた場合、`merge.precision_mode` を `baseline` に戻し、AutoSave の書き込みをトグル式で一時停止する。
2. [docs/AUTOSAVE-DESIGN-IMPL.md](../AUTOSAVE-DESIGN-IMPL.md) の例外設計に従い、リトライ可能例外をキューに退避し、リトライ不可例外は即座に人間レビューへ引き渡す。
3. [docs/IMPLEMENTATION-PLAN.md](../IMPLEMENTATION-PLAN.md) の段階導入チェックリストに照らして影響分析を行い、再度フラグを有効化するかを判断する。

---

- 逆リンク: [docs/AUTOSAVE-DESIGN-IMPL.md](../AUTOSAVE-DESIGN-IMPL.md) / [docs/MERGE-DESIGN-IMPL.md](../MERGE-DESIGN-IMPL.md) / [README.md](../../README.md) / [HUB.codex.md](../../HUB.codex.md)
