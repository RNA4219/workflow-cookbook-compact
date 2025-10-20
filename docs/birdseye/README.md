# Birdseye データセット運用ガイド

Birdseye は、Workflow Cookbook の知識マップを 3 層（Index / Capsules / Hot）で提供し、Guardrails の「Bootstrap → Index → Caps」の読込順序を支えるデータセットです。本ディレクトリでは各層の成果物と鮮度管理ルールを管理します。

## ディレクトリ構成

| ファイル / ディレクトリ | 役割 | Guardrails 連携 |
| --- | --- | --- |
| `index.json` | Birdseye ノード一覧と隣接関係（Edges）の基盤データ | `plan`/`notes` で ±hop を抽出する際の一次ソース |
| `caps/` | 各ノードのカプセル要約。`<path>.json` を 1 ノード 1 ファイルで保持 | Guardrails が要求する `deps_out` / 公開 API / リスク情報を提供 |
| `hot.json` | 主要ノードのホットリスト | Guardrails の「頻出入口ホットリスト」を充足し、即時参照を補助 |
| `README.md` | データセット運用手順 | Birdseye の生成・検証フローを共有 |
| `../BIRDSEYE.md` | フォールバック用の人間向け導線 | Guardrails の最終手段として Edges/Hot/更新手順を提示 |

## `codemap.update` 実行手順

Birdseye の生成・更新は `tools/codemap/update.py` を介して行います。Guardrails が要求する「自動再生成＋鮮度確認」を満たすため、以下のコマンドを基準としてください。

```bash
python tools/codemap/update.py \
  --targets docs/birdseye/index.json,docs/birdseye/hot.json \
  --emit index+caps
```

1. 対象ノード（`--targets`）に今回更新したファイルや重要エントリをカンマ区切りで列挙します。
2. `--emit` で出力対象を指定します。現在は `index+caps` が標準です。
3. `index.json` を更新すると `hot.json` も同一ターゲットで自動同期されます。
   出力後は `index.json.generated_at` / `hot.json.generated_at` / 各カプセルの `last_verified_at` が最新コミットに追随しているか確認します。
4. 差分をレビューし、`docs/BIRDSEYE.md` のフォールバック情報と矛盾がないことをチェックしてからコミットします。

> 手動編集が必要な場合でも、Birdseye スキーマ（`id` / `role` / `caps` / `edges` など）とパス命名規則（`/` を `.` に置換）を崩さないでください。

## ホットリストと鮮度管理

- `docs/birdseye/hot.json` は `index.json` の再生成時に自動同期され、`refresh_command` と `index_snapshot` で更新履歴を追跡します。
- ノードごとの `last_verified_at` は、対象カプセルの確認日または再生成日を記録します。`GUARDRAILS.md` の [鮮度管理](../GUARDRAILS.md#鮮度管理staleness-handling) に従い、日付が古いノードは優先的に再生成してください。
- ホットリストの構成は `README.md` / `GUARDRAILS.md` / `HUB.codex.md` など主要導線を中心に選定し、Katamari リポジトリのホットリスト形式を参考に `edges` を明示しています。
- `docs/BIRDSEYE.md` ではホットリストの概要と Edges を人間が参照できるように再掲しているため、変更時は両ドキュメントの整合性を確認します。

## Guardrails との整合

- `GUARDRAILS.md` で定義された「Birdseye JSON を第一読者とし、人間向けはフォールバック」という方針を満たすため、JSON ファイルは常に最新の情報源となるよう保守します。
- フォールバック時には `docs/BIRDSEYE.md` の Edges/Hot/更新手順を参照し、必要に応じて本 README の `codemap.update` 手順に合流してください。
- Birdseye を更新した場合は、関連するチェックリストや運用ドキュメント（`CHECKLISTS.md` / `RUNBOOK.md` など）にも鮮度情報を反映し、リポジトリ全体の整合を保ちます。
