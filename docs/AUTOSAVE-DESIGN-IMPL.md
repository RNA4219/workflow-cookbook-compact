---
intent_id: INT-001
owner: docs-core
status: draft
last_reviewed_at: 2025-01-14
next_review_due: 2025-02-14
---

# AutoSave 実装設計

参照: [README.md](../README.md) / [HUB.codex.md](../HUB.codex.md) / [docs/tasks/task-autosave-project-locks.md](tasks/task-autosave-project-locks.md)

## 不変条件

- プロジェクトロック取得中は同一プロジェクトに対する並列 AutoSave 書き込みを禁止し、最後に確定したスナップショットのタイムスタンプが単調増加すること。
- キャッシュ同期時はローカル差分とサーバースナップショットの CRDT マージ結果が同一であることを検証する。
- フラグ無効化時はロールバック前の最新スナップショットを読み取り専用で保持し、再有効化時に差分適用を保証する。

## 例外設計

- リトライ可能例外: ネットワークタイムアウト、軽微なロック競合。指数バックオフ付きで最大 3 回リトライする。
- リトライ不可例外: スキーマ不一致、整合性チェック失敗。即座に [docs/tasks/task-autosave-project-locks.md](tasks/task-autosave-project-locks.md) のロールバック手順へ移行する。
- すべての例外は `autosave.project_lock` フラグ状態と関連スナップショット ID を含む監査ログに記録する。

## I/O 契約

- 入力: `project_id`, `snapshot_delta`, `lock_token`, `timestamp`。`lock_token` は Merge コンポーネントから提供され、空値を許容しない。
- 出力: `status` (`ok` | `skipped` | `rolled_back`), `applied_snapshot_id`, `next_retry_at?`。
- サイドチャネル: テレメトリイベント `autosave.snapshot.commit` と `autosave.rollback.triggered` を発行する。

---

- 逆リンク: [docs/tasks/task-autosave-project-locks.md](tasks/task-autosave-project-locks.md) / [README.md](../README.md) / [HUB.codex.md](../HUB.codex.md)
