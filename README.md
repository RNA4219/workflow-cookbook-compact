# Workflow Cookbook / Codex Task Kit

任意のリポジトリに貼るだけで、**仕様→実装→検収**まで一貫して回せるMD群。
- 人間にもエージェント（Codex等）にも読ませやすい最小フォーマット
- 言語・技術スタック非依存（存在するコマンドだけ使う）

## 使い方（最短）
1. これらのMDをリポジトリ直下に配置
2. `BLUEPRINT.md` で要件と制約を1ページに集約
3. 実行手順は `RUNBOOK.md`、評価基準は `EVALUATION.md` に記述
4. タスクごとに `TASK.codex.md` を複製して内容を埋め、エージェントに渡す
5. リリースは `CHECKLISTS.md` をなぞり、差分は `CHANGELOG.md` に追記

![lint](https://github.com/RNA4219/workflow-cookbook/actions/workflows/markdown.yml/badge.svg) ![links](https://github.com/RNA4219/workflow-cookbook/actions/workflows/links.yml/badge.svg)

