---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-14
next_review_due: 2025-11-14
---

# Evaluation

## Acceptance Criteria

- 必須要件（フォーマット・件数・整合性など）
- PR本文に Priority Score（値と根拠）が記録されていること。
- governance/policy.yaml の forbidden_paths を変更しないこと。
- インシデント発生時は docs/IN-YYYYMMDD-XXX.md を作成し、該当PRおよびRUNBOOKから相互リンクする

## KPIs

- checklist_compliance_rate: ドキュメント出荷時に必須チェックリストへ準拠できた割合(%)。`tools/perf/collect_metrics.py` の出力
  （`checklist_compliance_rate`）を週次で確認し、95%以上を維持する。構成管理ログ（`docs/logs/docops.log` など）から checklist
  完了数/対象総数を抽出して集計する。
- task_seed_cycle_time_minutes: Task Seed の受付から初回処理完了までの平均所要時間(分)。構造化ログ内の `task_seed_cycle_time`
  系イベントを `tools/perf/collect_metrics.py` で集計し、24時間以内（1440分以下）を目標値とする。
- birdseye_refresh_delay_minutes: Birdseye ダッシュボードの更新遅延(分)。Prometheus やジョブ監視ログから更新完了時刻を収集し、
  `tools/perf/collect_metrics.py` で平均遅延を 60 分以内に抑える。

## Test Outline

- 単体: 入力→出力の例テーブル（[ケース I-03](docs/addenda/I_Test_Cases.md#i-03-task-seed-tdd-例)）
- 結合: 代表シナリオ（[ケース I-02](docs/addenda/I_Test_Cases.md#i-02-birdseye-再生成確認)）
- 回帰: 重要パス再確認（[ケース I-01](docs/addenda/I_Test_Cases.md#i-01-チェックリスト突合)）

> 検証手順の詳細は [`docs/addenda/I_Test_Cases.md`](docs/addenda/I_Test_Cases.md) を参照する。

## Verification Checklist

- [ ] 主要フローが動作する（手動確認）
- [ ] エラー時挙動が明示されている
- [ ] 依存関係が再現できる環境である
