# Birdseye データセット運用ガイド

Birdseye は、エージェントがリポジトリ全体を最小トークンで把握できるよう設計された 3 層構造のデータセットです。本ディレクトリでは以下の成果物を管理します。

## 構成

| ファイル | 役割 | 補足 |
| --- | --- | --- |
| `index.json` | ノード一覧と隣接関係を持つインデックス | LLM が ±hop を即時抽出するための基盤データ |
| `caps/` | 各ノードの要約カプセル | 1 ノード = 1 JSON。公開 API、依存関係、リスクなどを要約 |
| `hot.json` | 主要ノードのホットリスト | README・GUARDRAILS 等の頻出入口を即参照するためのサブセット |

## 更新手順

1. 対象ノードを整理し、`tools/codemap/update.py` で Birdseye を再生成する。例：
   ```bash
   python tools/codemap/update.py --targets README.md GUARDRAILS.md --emit index caps hot
   ```
2. 生成された JSON を確認し、`generated_at` や `last_verified_at` が最新コミットを反映しているかチェックする。
3. 差分をレビューし、Guardrails の要求（型・lint・テスト）に照らして問題が無いことを確認してからコミットする。

> 手動で修正する場合でも、スキーマ（`id` / `role` / `caps` 等）と命名規則（パスをドット連結）を崩さないこと。

## Guardrails 連携

- `GUARDRAILS.md` の Birdseye セクションで定義された読込順序（Bootstrap → Index → Caps）を満たすためのデータソースです。
- `docs/BIRDSEYE.md` は Guardrails からの参照起点であり、本 README はその補助資料として更新手順を提供します。
- `hot.json` は Guardrails の「頻出入口ホットリスト」要件を満たし、即座に読むべきノードを提示します。
