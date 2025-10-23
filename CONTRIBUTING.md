---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-14
next_review_due: 2025-11-14
---

# CONTRIBUTING

このリポジトリへのコントリビュート手順を、Katamari 版ガイドラインを踏まえつつ本リポの運用資料（`CHECKLISTS.md` / `docs/TASKS.md` / `SECURITY.md`）へ揃えて要約します。

## ブランチ運用

- 作業前に `TASK.codex.md` でタスクを定義し、`CHECKLISTS.md` の Development セクションに沿ってスコープとフォローアップを同期してください。
- すべての作業は main から分岐した短命のフィーチャーブランチで行い、早期にリベースして差分を最小化します。
- ブランチ名には Intent ID や Task Seed ID を含め、PR 作成時に `[Unreleased](CHANGELOG.md#unreleased)` へ通番付きで成果を転記します。
- インシデント／セキュリティ対応の場合は `RUNBOOK.md` と `docs/security/Security_Review_Checklist.md` を併読し、該当チェックリストの完了を証跡化してください。

## テスト駆動開発（TDD）

- `docs/TASKS.md` の「検証ログ（TDD 前提）」に従い、着手前に必要なテストを列挙し、失敗ケースを再現するテストから実装を開始します。
- テストの実行履歴は Task Seed の `Tests` / `Commands` セクションへ記録し、`CHECKLISTS.md` Development の要件に従ってゲート通過状況を同期します。
- 受け入れ条件は `EVALUATION.md` と `docs/ROADMAP_AND_SPECS.md` を参照し、`SECURITY.md` に定義された連絡ポリシー・SLA を満たす形でレビューを進めてください。

## 必須チェックコマンド

以下は最小限のゲートコマンドです。プロジェクトの言語・スタックに応じて `README.md` の CI テストセットを追加してください。

```sh
ruff check .
mypy --strict .
pytest -q
pnpm lint
pnpm test
```

- 必要に応じて `python tools/codemap/update.py --since --emit index+caps` など運用スクリプトを実行し、Birdseye とチェックリストの鮮度を保ちます。
- 変更によりセキュリティへ影響が生じる場合は `docs/security/Security_Review_Checklist.md` のフェーズ別タスクを完了させ、PR に結果を添付してください。

## AI 併用時の記録

- AI サポートを利用した場合は、`TASK.*` の `Notes` に使用モデル・プロンプト概要・判断根拠を記載し、`docs/TASKS.md` のフローに従ってフォローアップを切り出してください。
- 自動生成された差分は `CHECKLISTS.md` Pull Request / Review セクションの要求どおり、テスト緑化とセキュリティチェックの完了証跡を添付してレビューへ提出します。
- セキュリティ報告に AI を使用した場合でも、`SECURITY.md` の連絡先と公開方針を厳守してください。

## リリースまでの流れ

1. Development / Pull Request / Review / Release の各チェックリストをすべて通過。
2. `CHANGELOG.md` の `[Unreleased](CHANGELOG.md#unreleased)` に通番付きで結果を追記。
3. `RUNBOOK.md` と関連ドキュメントへ必要な差分を反映し、Task Seed の `Follow-ups` を解消。
4. `SECURITY.md` に記載された報告フローが不要か再確認し、必要な場合は連絡と証跡を完了。

更新日: 2025-10-14
