# Agent Tool Policy — Dual Stack

## Runtimes

- Native function-calling tools are registered (OpenAI/Gemini/Vertex).
- No native tools; an external orchestrator parses JSON blocks in text.

## Rules

1. If native tools exist, CALL them (function calling) using the tool names
   below.
2. Always MIRROR each call as a JSON envelope so non-native runtimes can parse:

```tool_request
{"name":"web.search","arguments":{"q":"...", "recency":30}}
```

3. Never fabricate tool results. If tools are unavailable, emit `plan` and JSON
   envelopes only.
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

# HUB.codex.md

リポジトリ内の仕様・運用MDを集約し、エージェントがタスクを自動分割できるようにするハブ定義。
`BLUEPRINT.md` など既存ファイルに加えて、オーケストレーション専用のMD（例: `orchestration/*.md`）も取り込む。

## 1. 目的

* リポジトリ配下の計画資料から作業ユニットを抽出し、優先度順に配列
* オーケストレーションMD（ワークフロー全体の段取り記載）を検出し、必要な子タスクへ展開
* 生成されたタスクリストを `TASK.*-MM-DD-YYYY` 形式の Task Seed へマッピング

## 2. 入力ファイル分類

| 種別 | 例 | 主な内容 | 優先順 | 備考 |
| --- | --- | --- | --- | --- |
| Blueprint | `BLUEPRINT.md` | 要件・制約・背景 | 高 | 最上位方針 |
| Runbook | `RUNBOOK.md` | 実行手順・コマンド | 中 | 具体的操作 |
| Guardrails | `GUARDRAILS.md` | ガードレール/行動指針 | 高 | 全メンバー必読 |
| Evaluation | `EVALUATION.md` | 受け入れ基準・品質指標 | 中 | 検収条件 |
| Checklist | `CHECKLISTS.md` | リリース/レビュー確認項目 | 低 | 後工程 |
| Orchestration | `orchestration/*.md` | ワークフロー構成・依存関係 | 可変 | 最優先のブロッカーを提示 |
| Task Seeds | `TASK.*-MM-DD-YYYY` | 既存タスクドラフト | 可変 | 未着手タスクの候補 |

補完資料:

* `README.md`: リポジトリ概要と参照リンク
* `CHANGELOG.md`: 完了タスクと履歴の記録
* `.github/PULL_REQUEST_TEMPLATE.md`: PR 作成時のチェック項目（Intent/リスク/Canary連携）
* `.github/ISSUE_TEMPLATE/bug.yml`: Intent ID と自動ゲート確認を必須化した不具合報告フォーム
* `governance/policy.yaml`: QA が管理する自己改変境界・カナリア中止条件・SLO
* `governance/prioritization.yaml`: 設計更新の優先度スコア計算ルール
* `docs/INCIDENT_TEMPLATE.md`: 検知/影響/5Whys/再発防止/タイムラインのインシデント雛形
* `SECURITY.md`: 脆弱性報告窓口と連絡手順
* `CODEOWNERS`: `/governance/**` とインシデント雛形を QA 管轄とする宣言
* `LICENSE`: OSS としての配布条件（MIT）
* `.github/release-drafter.yml`: リリースノート自動整形のテンプレート
* `.github/workflows/release-drafter.yml`: Release Drafter の CI 設定

更新日: 2025-10-13

## 3. 自動タスク分割フロー

1. **スキャン**: ルートと `orchestration/` 配下を再帰探索し、Markdown front matter
   (`---`) を含むファイルを優先取得。
2. **ノード生成**: 各ファイルから `##` レベルの節をノード化し、`Priority`
   `Dependencies` などのキーワードを抽出。
3. **依存解決**: Orchestrationノードに含まれる依存パスを解析し、該当セクションを子ノードとして連結。
4. **粒度調整**: ノード内の ToDo / 箇条書きを単位作業へ分割し、`<= 0.5d`
   を目安にまとめ直し。
5. **テンプレート投影**: 各作業ユニットを `TASK.*-MM-DD-YYYY` 形式の Task Seed
   (`Objective` `Requirements` `Commands`) へ変換し、欠損フィールドは元資料の該当行を引用。
6. **出力整形**: 優先度、依存、担当の有無でソートし、GitHub Issue もしくは
   PR下書きとしてJSON/YAMLに整形。

## 4. ノード抽出ルール

* Front matter内の `priority`, `owner`, `deadline` を最優先で採用
* 節タイトルに `[Blocker]` を含む場合は依存解決フェーズで最上位へ昇格
* 箇条書きのうち `[]` or `[ ]` 形式はチェックリスト扱い、`- [ ]` はタスク分解対象
* コードブロックはコマンドサンプルとして `Commands` セクションに集約

## 5. 出力例（擬似）

```yaml
- task_id: 20240401-01
  source: orchestration/api-rollout.md#Phase1
  objective: API Gateway ルーティング切替の段階実行
  scope:
    in: [infra/aws/apigw]
    out: [legacy/cli]
  requirements:
    behavior:
      - Blue/Green 切替時にダウンタイム0
    constraints:
      - 既存API破壊禁止
  commands:
    - terraform plan -target=module.api_gateway
  dependencies:
    - 20240331-ops-01
```

## 6. 運用メモ

* Orchestration MD には `## Phase` `## Stage` 等の段階名を揃える
* タスク自動生成ツールはドライランでJSON出力を確認後にIssue化
* 生成後は `CHANGELOG.md` へ反映済みタスクを移すことで履歴が追える

