---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-14
next_review_due: 2025-11-14
---

# Agent Tool Policy — Dual Stack

## Runtimes

- ネイティブ関数呼び出しツール（OpenAI/Gemini/Vertex など）が存在する場合はそちらを優先する。
- ツールが存在しない場合は外部オーケストレータが JSON ブロックを解釈する。

## Rules

1. ネイティブツールがあれば指定の論理名で呼び出す。
2. すべての呼び出しは JSON エンベロープを併記し、非ネイティブ実行環境でも解析可能にする。
3. ツール結果は改変しない。利用不能時は `plan` と JSON エンベロープのみ出力する。
4. プラットフォーム固有マクロは展開せず原文を維持する。
5. 既定言語は日本語（コード識別子などで必要な場合のみ英語）。

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
`BLUEPRINT.md` など既存ファイルに加えて、必要に応じて `orchestration/*.md` などオーケストレーション向け資料も取り込む。

## 目的

- リポジトリ内の計画資料を走査し、優先度付きタスク候補へ変換する。
- Orchestration 系資料から依存関係を展開し、必要な子タスクを揃える。
- 生成結果を `TASK.*-MM-DD-YYYY` 形式の Task Seed に投影する。

## 2. 入力ファイル分類

- **Blueprint** (`docs/BLUEPRINT.md`): 要件と背景。最優先。
- **Runbook** (`docs/RUNBOOK.md`): 実行手順とコマンド。次点。
- **Guardrails** (`docs/GUARDRAILS.md`): 行動基準と制約。最優先。
- **Evaluation** (`docs/EVALUATION.md`): 受入条件。優先度: 中。
- **Design / Spec** (`docs/DESIGN.md`, `docs/SPEC.md`): 詳細設計と仕様。優先度: 中。
- **Task Seeds** (`docs/TASKS.md`, `TASK.*-MM-DD-YYYY`): 既存タスク案。優先度: 高。
- **Birdseye** (`docs/birdseye/*.json`, `docs/BIRDSEYE.md`): 依存トポロジ。優先度: 高。
- **Downsized requirements** (`docs/downsized_cookbook_requirements_spec.md`): 軽量運用方針。優先度: 中。

補完資料: `README.md`, `CHANGELOG.md`, `LICENSE`, `NOTICE`、および `config/` `recipes/` `examples/` `tools/` 内の README。

更新日: 2025-10-24

## 3. 自動タスク分割フロー

1. ルートおよび `docs/` を走査し、front matter 付き Markdown を優先取得する。
2. Birdseye JSON で関連ノード（±2 hop）と役割を補完する。
3. `##` 見出しをノード化し、`priority` や `dependencies` を抽出する。
4. Orchestration 節の依存パスを解決して親子ノードをリンクする。
5. 箇条書きタスクを 0.5 日以下に分割し、元資料の該当行を引用する。
6. ノードを `TASK.*-MM-DD-YYYY` 形式の Task Seed に整形し、JSON/YAML 出力を整備する。

## 4. ノード抽出ルール

- front matter の `priority` `owner` `deadline` を最優先で採用する。
- `[Blocker]` を含む節タイトルは最上位優先度とする。
- `- [ ]` チェックリストはタスク候補、コードブロックは `commands` へ集約する。
- ステータス遷移は `planned` → `active` → `in_progress` → `reviewing` → `done`。`blocked` は一時停止を示す。

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

- Orchestration 文書の段階見出し（例: `## Phase`）を揃えて依存解析を容易にする。
- タスク自動生成ツールは JSON ドライランを確認してから Issue / PR へ展開する。
- 反映済みタスクは `CHANGELOG.md` に移し、Birdseye の `generated_at` が古ければ再収集する。
- Birdseye を再生成した場合のみ `codemap.update` を実行し、Dual Stack では関数呼び出しと `tool_request` の内容を同期させる。
