---
intent_id: INT-001
owner: docs-core
status: draft
last_reviewed_at: 2025-10-28
next_review_due: 2025-11-28
---

# Merge 実装設計

参照: [README.md](../README.md) / [HUB.codex.md](../HUB.codex.md) / [docs/tasks/task-autosave-project-locks.md](tasks/task-autosave-project-locks.md)

## 精度モード

- `baseline`: 既存マージアルゴリズムを維持し、AutoSave のロックをオプション扱いにする。失敗時はリトライ後に警告ログを
  残す。
- `strict`: AutoSave のロック取得を必須とし、CRDT 差分の矛盾を検知した場合に即時ロールバックする。`merge.precision_mode`
  フラグで切替。
- 精度モードは `docs/IMPLEMENTATION-PLAN.md` の段階導入チェックリストと同期し、テレメトリ完了までは `baseline` がデフォルト。

## ロック協調

- AutoSave からの `lock_token` を検証し、未発行または期限切れの場合はリトライ可能例外を返す。
- Merge はロック競合時に `backoff_ms` を倍増させつつ最大 5 回再試行し、それでも解決しない場合はロールバック手順を発動する。
- ロック解放時には AutoSave へ `lock_release` イベントを送信し、スナップショットの単調性を共有する。

## テレメトリ要件

- `merge.precision_mode` ごとに `merge.success.rate` と `merge.conflict.rate` を計測し、閾値超過時にカナリア結果を [docs/tasks/task-autosave-project-locks.md](tasks/task-autosave-project-locks.md) へ記録する。
- AutoSave 連携遅延を `merge.autosave.lag_ms` として追跡し、目標値 200ms を超過した場合にフラグを `baseline` へ戻す。
- すべてのテレメトリは [docs/IMPLEMENTATION-PLAN.md](IMPLEMENTATION-PLAN.md) の依存関係セクションで定義したストレージに集約する。

---

- 逆リンク: [docs/tasks/task-autosave-project-locks.md](tasks/task-autosave-project-locks.md) / [README.md](../README.md) / [HUB.codex.md](../HUB.codex.md)
