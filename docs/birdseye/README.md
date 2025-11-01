# Birdseye データセット運用ガイド

Birdseye は、Workflow Cookbook の知識マップを `index.json`（全体のエッジ情報）と `hot.json`（重要ノードのサマリー）の 2 層で提供します。
ダウンサイザード版では `caps/` 階層やリポジトリ内スクリプトは保持していません。JSON の編集は外部ツールまたは手動で行い、最終成果物だけを本リポジトリに格納します。

## ディレクトリ構成

- `index.json`
  - 役割: Birdseye ノード一覧と隣接関係の基盤データ。
  - Guardrails 連携: ±hop 抽出の一次ソース。`generated_at` はゼロ埋め連番を継続します。
- `hot.json`
  - 役割: 主要ノードのホットリスト。
  - Guardrails 連携: 初動で確認すべきノードの一覧を提供し、`last_verified_at` で鮮度を記録します（必要に応じて利用）。
- `README.md`
  - 役割: 本手順書。JSON の更新フローと整合チェックを維持します。
- `../BIRDSEYE.md`
  - 役割: JSON を参照できない状況でのフォールバック。ホットリストとエッジの要約を提供します。

## 更新フロー

1. 変更したいノードやエッジを整理し、外部の Birdseye 生成ツール（codemap 互換など）または手動で `index.json` と `hot.json` を同時に更新します。
2. `generated_at` の値が両ファイルで揃っていることを確認し、ゼロ埋め連番が途切れていないかチェックします。
3. `hot.json` を使用している場合は `last_verified_at` や `refresh_command` が現行の運用手順と一致しているか見直します。
4. 変更内容をレビューし、`../BIRDSEYE.md` と `docs/TASKS.md` に記載された導線・ログ運用と矛盾がないかを確認します。
5. 必要に応じて `GUARDRAILS.md` の [鮮度管理](../GUARDRAILS.md#鮮度管理staleness-handling) 手順に従い、再生成や周知を行います。

## 保守上の留意点

- JSON が破損した場合は `RUNBOOK.md` の復旧手順に従い、状況を `docs/TASKS.md` や `CHANGELOG.md` に記録します。
- 新しいノードを追加する際は、実在するファイルまたはレシピに限定し、不要になった参照は削除してください。
- Birdseye を再生成したら、`README.md` と `../BIRDSEYE.md` の記述が最新構成と一致するかを確認します。
