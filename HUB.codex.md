---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-14
next_review_due: 2025-11-14
---

# Agent Tool Policy — Dual Stack

## Runtimes

- Native function-calling tools are registered (OpenAI/Gemini/Vertex).
- No native tools; an external orchestrator parses JSON blocks in text.

## Rules

1. If native tools exist, CALL them (function calling) using the tool names below.
2. Always MIRROR each call as a JSON envelope so non-native runtimes can parse:

   ```tool_request
   {"name":"web.search","arguments":{"q":"...", "recency":30}}
   ```

3. Never fabricate tool results. If tools are unavailable, emit `plan` and JSON envelopes only.
4. Platform-specific macros remain VERBATIM (do not expand).
5. Default language: Japanese unless code identifiers dictate otherwise.

## Logical Tool Names

- web.search{q, recency?, domains?}
- web.open{url}
- drive.search{query, owner?, modified_after?}
- gmail.search{query, max_results?}
- calendar.search{time_min?, time_max?, query?}

## Output Contract

`plan`/`patch`/`tests`/`commands`/`notes`

## HUB.codex.md

リポジトリ内の仕様・運用MDを集約し、エージェントがタスクを自動分割できるようにするハブ定義。
`BLUEPRINT.md` など既存ファイルに加えて、オーケストレーション専用のMD（例: `orchestration/*.md`）も取り込む。

## 目的

- リポジトリ内の計画資料を走査し、優先度付きタスク候補へ変換する。
- Orchestration 系資料から依存関係を展開し、必要な子タスクを揃える。
- 生成結果を `TASK.*-MM-DD-YYYY` 形式の Task Seed に投影する。

## 2. 入力ファイル分類

- **Blueprint** (`docs/BLUEPRINT.md`): 要件と背景。最優先で参照。
- **Runbook** (`docs/RUNBOOK.md`): 実行手順とコマンド。次点優先。
- **Guardrails** (`docs/GUARDRAILS.md`): 行動基準と制約。最優先。
- **Evaluation** (`docs/EVALUATION.md`): 受入条件の一覧。優先度: 中。
- **Design / Spec** (`docs/DESIGN.md`, `docs/SPEC.md`): 詳細設計と仕様。優先度: 中。
- **Task Seeds** (`docs/TASKS.md`, `TASK.*-MM-DD-YYYY`): 既存タスク案。優先度: 高。
- **Birdseye** (`docs/birdseye/*.json`, `docs/BIRDSEYE.md`): 依存トポロジ。優先度: 高。
- **Downsized requirements** (`docs/downsized_cookbook_requirements_spec.md`): 軽量運用方針。優先度: 中。

補完資料:

- `README.md`, `CHANGELOG.md`, `LICENSE`, `NOTICE`
- `config/`, `recipes/`, `examples/`, `tools/` に付属する README 類

更新日: 2025-10-24

## 3. 自動タスク分割フロー

1. ルートと `docs/` を再帰探索し、front matter を持つ Markdown を優先取得する。
2. Birdseye JSON を併用して関連ノード（±2 hop）と役割を補完する。
3. 各ファイルの `##` レベル節をノード化し、`priority` `dependencies` などのキーワードを抽出する。
4. Orchestration 節に記載された依存パスを解決し、参照先の節を子ノードとしてリンクする。
5. 箇条書きタスクを 0.5 日以下の単位に分解し、不足情報は元資料の該当行を引用する。
6. ノードを `TASK.*-MM-DD-YYYY` 形式の Task Seed に整形し、JSON/YAML の両方で出力できるよう整備する。

## 4. ノード抽出ルール

- front matter の `priority` `owner` `deadline` を最優先で採用する。
- 節タイトルに `[Blocker]` を含む場合は優先度を最上位へ引き上げる。
- `- [ ]` 形式のチェックリストをタスク候補として扱い、コードブロックは `commands` セクションへ集約する。
- ステータスは `planned` → `active` → `in_progress` → `reviewing` → `done` を基本遷移とし、`blocked` は一時停止を意味する。

## 5. 出力テンプレート

```yaml
- task_id: 20240401-01
  source: docs/RUNBOOK.md#execute
  objective: 実行手順のフェーズ切替を段階実行
  scope:
    in: [recipes/srs_scope_plan.yaml]
    out: [examples/]
  requirements:
    - RUNBOOK Execute フェーズは無停止で切り替える
  commands:
    - rg "Phase" docs/RUNBOOK.md
  dependencies:
    - docs/BLUEPRINT.md#5-minimal-flow
```

## 6. 運用メモ

- Orchestration 文書の段階見出し (`## Phase` など) を揃えて依存解析を容易にする。
- タスク自動生成ツールは JSON ドライランを確認してから Issue / PR へ展開する。
- 反映済みタスクは `CHANGELOG.md` に移し、 Birdseye の `generated_at` が古ければ再収集する。
- `codemap.update` は Birdseye を再生成した場合のみ実行し、Dual Stack では関数呼び出しと `tool_request` のミラー内容を一致させる。
