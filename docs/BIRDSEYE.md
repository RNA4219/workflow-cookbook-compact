---
intent_id: DOC-LEGACY
owner: docs-core
status: active
last_reviewed_at: 2025-10-28
next_review_due: 2025-11-28
---

# Birdseye リファレンス

Birdseye は、Workflow Cookbook の知識マップを `docs/birdseye/index.json` と `docs/birdseye/hot.json` の 2 ファイルで提供します。
本書は Guardrails などが JSON を開けない場合のフォールバックとして、主要ノードの関係と更新フローを要約します。

## 主要エッジ

`docs/birdseye/index.json` を基に、最小構成で追跡しているノードのみを抜粋しています。

- `README.md` ↔ `GUARDRAILS.md`／`HUB.codex.md`／`RUNBOOK.md`／`EVALUATION.md`／`docs/birdseye/index.json`
- `GUARDRAILS.md` ↔ `README.md`／`HUB.codex.md`／`RUNBOOK.md`／`EVALUATION.md`
- `HUB.codex.md` ↔ `README.md`／`GUARDRAILS.md`／`RUNBOOK.md`／`EVALUATION.md`／`docs/TASKS.md`
- `RUNBOOK.md` ↔ `README.md`／`GUARDRAILS.md`／`EVALUATION.md`
- `EVALUATION.md` ↔ `README.md`／`GUARDRAILS.md`／`RUNBOOK.md`／`docs/TASKS.md`
- `docs/birdseye/index.json` ↔ `README.md`／`GUARDRAILS.md`／`HUB.codex.md`／`docs/birdseye/README.md`

> 上記にないノードは現行リポジトリでは運用対象外です。追加する場合は JSON 側にエントリがあることを確認してから記載してください。

## ホットリスト概要

`docs/birdseye/hot.json` の必須エントリのみを列挙します。

- `README.md`: 導入と参照順序の起点。
- `GUARDRAILS.md`: 行動指針と鮮度管理の要点。
- `HUB.codex.md`: 依存・タスク参照のハブ。
- `RUNBOOK.md`: 運用と再生成ステップ。
- `EVALUATION.md`: 受入基準と品質チェックの一覧。
- `docs/TASKS.md`: タスク起点とログの管理。
- `docs/BIRDSEYE.md`: 本フォールバックガイド。
- `docs/birdseye/index.json`: hop 抽出の基盤データ。
- `docs/birdseye/README.md`: JSON 更新時の運用ガイド。

`generated_at` は `index.json` と `hot.json` を同一タイミングで更新し、ゼロ埋め連番を継承してください。ホットリストの `last_verified_at` を使う場合は手動更新日と揃えます。

## Birdseye 更新手順

1. 更新対象ノードを整理し、外部の Birdseye 生成ツール（例: codemap 互換ツール）または手動編集で `docs/birdseye/index.json` と `docs/birdseye/hot.json` を同時に更新します。
2. 両ファイルの `generated_at` が揃っているか確認し、差分がガバナンス文書と矛盾しないかレビューします。
3. JSON 変更後は本ドキュメントと `docs/birdseye/README.md` の記載が最新構成と一致しているかを確認します。
4. `GUARDRAILS.md` の [鮮度管理](../GUARDRAILS.md#鮮度管理staleness-handling) に従い、必要に応じて関係者へ通知します。

## フォールバック運用

- 自動ツールが利用できない場合は、`README.md` → `docs/birdseye/index.json` → `docs/birdseye/hot.json` の順に確認してノードを特定します。
- JSON が取得できない場合は、本書と `docs/birdseye/README.md` の手順を参考に暫定判断を行い、可能な環境で早急に JSON を復旧させます。
- インシデントを検知した場合は `RUNBOOK.md` に従って復旧し、必要なら `docs/TASKS.md` で記録します。

> 最新状態は必ず `docs/birdseye/index.json` および `docs/birdseye/hot.json` を基準に確認してください。
