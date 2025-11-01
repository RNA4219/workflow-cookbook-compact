# 付録A: 用語集（Workflow Cookbook）

| 用語 | 定義 | 関連資料 |
| :--- | :--- | :--- |
| Task Seed | `TASK.codex.md` テンプレートに基づき作成する作業ドラフト。Objective・Scope・Requirements を揃えてタスク化の起点とする。 | [`docs/TASKS.md`](../TASKS.md), [`TASK.codex.md`](../../TASK.codex.md) |
| Birdseye | `docs/birdseye/` 配下のインデックス/カプセルから成る依存グラフ。ノードIDと `deps_out` を基に、作業範囲±2 hop の影響を可視化する。 | [`docs/BIRDSEYE.md`](../BIRDSEYE.md), [`tools/codemap/README.md`](../../tools/codemap/README.md) |
| チェックリスト | リリースやレビュー時に必須項目の抜け漏れを防ぐための項目集。`CHECKLISTS.md` や各種テンプレートで段階別に定義する。 | [`CHECKLISTS.md`](../../CHECKLISTS.md), [`docs/Release_Checklist.md`](../Release_Checklist.md) |
| Codemap | Birdseye カプセルの生成・更新を自動化するスクリプト群。`tools/codemap/update.py` を用いて差分に応じた index/caps を再構築する。 | [`tools/codemap/update.py`](../../tools/codemap/update.py), [`tools/codemap/README.md`](../../tools/codemap/README.md) |
| Dual Stack | ネイティブ関数呼び出しと JSON ミラー出力を両立するエージェント運用方式。どちらのランタイムでも同一リクエストを再現できるようにする。 | [`HUB.codex.md`](../../HUB.codex.md) |
| インシデントログ | 重大事象の発生・影響・再発防止を記録する文書。Task Seed や Birdseye ノードと相互リンクし、再発テストの設計根拠を提供する。 | [`docs/IN-20250115-001.md`](../IN-20250115-001.md), [`docs/INCIDENT_TEMPLATE.md`](../INCIDENT_TEMPLATE.md) |
| Evaluation | 受入基準と品質指標を列挙した基準書。Intent/Task Seed の完了判定やリリース前検証の最低条件を定義する。 | [`EVALUATION.md`](../../EVALUATION.md) |

> **補足**: ダウンサイザード版では Intent/Priority Score ベースの統制は提供対象外です。必要に応じてオリジナル版のガバナンス文書を参照してください。
