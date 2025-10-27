---
intent_id: INT-001
owner: docs-core
status: draft
last_reviewed_at: 2025-01-14
next_review_due: 2025-02-14
---

# 実装計画（Implementation Plan）

本計画は [README.md](../README.md) および [HUB.codex.md](../HUB.codex.md) の導入指針に従い、AutoSave と Merge の段階導入を支える最小単位の意思決定と依存関係を整理する。

## フラグ方針

- `autosave.project_lock` フラグで AutoSave のプロジェクトロック機構を段階的に有効化する。
- `merge.precision_mode` フラグで Merge の精度モード（`baseline` / `strict`）を切り替え、後方互換を維持する。
- 両フラグともに [docs/tasks/task-autosave-project-locks.md](tasks/task-autosave-project-locks.md) のチェックリスト完了を有効化条件とし、未完了状態では強制的にオフ。

## 依存関係

- AutoSave の不変条件・例外設計・I/O 契約は [docs/AUTOSAVE-DESIGN-IMPL.md](AUTOSAVE-DESIGN-IMPL.md) を参照する。
- Merge 精度モード・ロック協調・テレメトリ要件は [docs/MERGE-DESIGN-IMPL.md](MERGE-DESIGN-IMPL.md) に従う。
- タスク実行フローとテスト駆動の証跡は [docs/tasks/task-autosave-project-locks.md](tasks/task-autosave-project-locks.md) に準拠する。

## 段階導入チェックリスト

1. `autosave.project_lock` を `baseline` プロジェクトに対してカナリア実行し、[docs/AUTOSAVE-DESIGN-IMPL.md](AUTOSAVE-DESIGN-IMPL.md) で定義した不変条件の監視アラートを有効化する。
2. `merge.precision_mode` を `baseline` → `strict` へ段階昇格し、[docs/MERGE-DESIGN-IMPL.md](MERGE-DESIGN-IMPL.md) のテレメトリ指標で回帰を確認する。
3. 1・2 の結果を [docs/tasks/task-autosave-project-locks.md](tasks/task-autosave-project-locks.md) のロールバック手順に沿ってレビューし、完了後にフラグを恒常化する。

---

- 逆リンク: [README.md](../README.md) / [HUB.codex.md](../HUB.codex.md)
