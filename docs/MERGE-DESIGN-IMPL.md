---
intent_id: INT-001
owner: docs-core
status: draft
last_reviewed_at: 2025-10-28
next_review_due: 2025-11-28
---

# Merge 実装設計

参照: [README.md](../README.md) / [HUB.codex.md](../HUB.codex.md) /
[docs/IMPLEMENTATION-PLAN.md](IMPLEMENTATION-PLAN.md) /
[docs/tasks/task-autosave-project-locks.md](tasks/task-autosave-project-locks.md) /
[docs/AUTOSAVE-DESIGN-IMPL.md](AUTOSAVE-DESIGN-IMPL.md)

## 精度モード

- `baseline`: 既存マージアルゴリズムを維持し、AutoSave のロックをオプション扱いにする。失敗時はリトライ後に警告ログを残す。
- `strict`: AutoSave のロック取得を必須とし、CRDT 差分の矛盾を検知した場合に即時ロールバックする。`merge.precision_mode` フラグで切替。
- 精度モードは [docs/IMPLEMENTATION-PLAN.md#フラグ方針](IMPLEMENTATION-PLAN.md#%E3%83%95%E3%83%A9%E3%82%B0%E6%96%B9%E9%87%9D) と同期し、テレメトリ完了までは `baseline` がデフォルト。

## I/O 契約

- 入力: `project_id`, `merged_snapshot`, `lock_token?`, `precision_mode`, `last_applied_snapshot_id`。
- 出力: `status` (`merged` | `conflicted` | `rolled_back`), `resolved_snapshot_id?`, `lock_release?`。
- `lock_release` は AutoSave へ返却され、
  [docs/AUTOSAVE-DESIGN-IMPL.md#ui-ロック協調](AUTOSAVE-DESIGN-IMPL.md#ui-%E3%83%AD%E3%83%83%E3%82%AF%E5%8D%94%E8%AA%BF) の UI 更新をトリガーする。

## ロック協調

- AutoSave からの `lock_token` を検証し、未発行または期限切れの場合はリトライ可能例外を返す。
- Merge はロック競合時に `backoff_ms` を倍増させつつ最大 5 回再試行し、それでも解決しない場合はロールバック手順を発動する。
- ロック解放時には AutoSave へ `lock_release` イベントを送信し、スナップショットの単調性を共有する。

## テレメトリ要件

- `merge.precision_mode` ごとに `merge.success.rate` と `merge.conflict.rate` を計測し、閾値超過時にカナリア結果を
  [docs/tasks/task-autosave-project-locks.md#tdd](tasks/task-autosave-project-locks.md#tdd) へ記録する。
- AutoSave 連携遅延を `merge.autosave.lag_ms` として追跡し、目標値 200ms を超過した場合にフラグを `baseline` へ戻す。
- すべてのテレメトリは [docs/IMPLEMENTATION-PLAN.md#依存関係](IMPLEMENTATION-PLAN.md#%E4%BE%9D%E5%AD%98%E9%96%A2%E4%BF%82) で定義したストレージに集約する。

---

- 逆リンク: [docs/tasks/task-autosave-project-locks.md](tasks/task-autosave-project-locks.md) /
  [docs/AUTOSAVE-DESIGN-IMPL.md](AUTOSAVE-DESIGN-IMPL.md) /
  [docs/IMPLEMENTATION-PLAN.md](IMPLEMENTATION-PLAN.md) /
  [README.md](../README.md) /
  [HUB.codex.md](../HUB.codex.md)
