---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-14
next_review_due: 2025-11-14
---

# Changelog

## [Unreleased]

### Changed

- 0007: `CHECKLISTS.md` に Development / Pull Request / Ops チェックリストを追加し、Release セクションが新設項目と重複しないよう参照構造へ更新
- 0008: 過去のブランド表現をワークフロー向けの共通名称・リンクへ差し替え、関連チェックリストとメトリクス定義の整合性を再確認
- 0009: `<旧ブランド名>` 参照を中立表現へ整理
- 0010: ブランド非依存の表現へ整理し、`CHANGELOG.md` と `CHECKLISTS.md` の記述を同期

## 0.1.0 - 2025-10-13

- 0001: 初版（MD一式 / Codex対応テンプレ含む）

## 1.0.0 - 2025-10-16

### Added

- 0002: Stable Template API（主要MDの凍結）
- 0003: PR運用の明確化（Intent / EVALUATION リンク / semverラベル）
- 0004: CIワークフロー（links/prose/release）

### Known limitations

- 0005: SLOバッジ自動生成は未実装（README と policy.yaml を手動同期）
- 0006: Canary 連携は任意
