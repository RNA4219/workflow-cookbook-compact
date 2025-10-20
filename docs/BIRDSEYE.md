# Birdseye リファレンス

Birdseye は、Workflow Cookbook の知識マップ（Index / Capsules / Hot list）を統合的に参照するための仕組みです。本書は Guardrails からの参照起点として、確認手順と関連資料を集約します。

## 確認手順

1. `README.md` 冒頭の **LLM-BOOTSTRAP** ブロックで Birdseye 参照先を確認する。
2. `docs/birdseye/index.json` を開き、対象変更ファイルから ±2 hop のノード ID を抽出する。
3. 抽出したノードの `docs/birdseye/caps/*.json` を読み込み、公開 API・依存関係・リスクを把握する。
4. 主要ノードは `docs/birdseye/hot.json` を確認し、更新漏れが無いかをチェックする。
5. `generated_at` が最新コミットより古い場合は、`tools/codemap/update.py` を使って再生成する。

## 関連リンク

- [Birdseye データセット運用ガイド](birdseye/README.md)
- [Birdseye Index](birdseye/index.json)
- [Birdseye Hot List](birdseye/hot.json)
- [Birdseye Capsules](birdseye/caps/)
- [Guardrails（Birdseye セクション）](../GUARDRAILS.md)
- [Codemap 更新スクリプト](../tools/codemap/README.md)

## エスカレーション

- Birdseye データが欠落・破損している場合は、`tools/codemap/update.py` をドライランで実行し、出力を確認してからコミットする。
- 自動再生成が困難な場合は、`docs/IN-20250115-001.md` のインシデント手順に従い、関係者へ共有する。
- Guardrails 更新時には、本書と `docs/birdseye/hot.json` の整合性を確認する。
