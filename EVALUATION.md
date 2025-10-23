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

- checklist_compliance_rate
  - 目的: ドキュメント出荷時に必須チェックリストへ準拠できた割合を可視化し、ヒューマンエラーの早期検知につなげる。
  - 収集方法:
    - 以下のコマンドを実行して `.ga/qa-metrics.json` を生成する。

      ```bash
      python -m tools.perf.collect_metrics --suite qa --metrics-url <Prometheus URL> --log-path <Chainlit ログ>
      ```

    - `checklist_compliance_rate` を JSON から取得し、必要に応じて構成管理ログ（`docs/logs/docops.log` など）で完了数と対象総数を突合する。
  - 目標値: 0.95 以上を週次で維持。
- task_seed_cycle_time_minutes
  - 目的: Task Seed の受付から初回処理完了までの所要時間を把握し、着手遅延を抑制する。
  - 収集方法:
    - 構造化ログ内の `task_seed_cycle_time_*` 系イベントを `tools.perf.collect_metrics` が正規化する値として `.ga/qa-metrics.json` から取得する。
  - 目標値: 1440 分（24 時間）以下を維持。
- birdseye_refresh_delay_minutes
  - 目的: Birdseye ダッシュボードの更新遅延を監視し、情報可視化の鮮度を保証する。
  - 収集方法:
    - Prometheus の `birdseye_refresh_delay_*` 系メトリクスまたはジョブ監視ログを `tools.perf.collect_metrics` で平均化した値を採用する。
  - 目標値: 60 分以下を維持。
- review_latency
  - 目的: レビュー待機時間を定量化し、レビューのボトルネックを可視化する。
  - 収集方法:
    - Prometheus の `workflow_review_latency_*` および `legacy_review_latency_*` を `tools.perf.collect_metrics` が正規化する。
    - 正規化後の値を `.ga/qa-metrics.json` から取得する。
  - 目標値: 12 時間以下を維持。
- compress_ratio
  - 目的: トリミング後コンテキストの圧縮率を測定し、コンテキスト削減による情報損失を防ぐ。
  - 収集方法:
    - `tools.perf.metrics_registry.MetricsRegistry.observe_trim` から `compress_ratio` をエクスポートする。
    - エクスポート済みの値を `tools.perf.collect_metrics` で収集する。
  - 目標値: 0.60 以下に抑え、過剰圧縮を避ける。
- semantic_retention
  - 目的: コンテキストトリミング後に保持された意味情報の割合を監視し、質の劣化を検知する。
  - 収集方法:
    - Chainlit の埋め込みログまたは `StructuredLogger` が出力する `semantic_retention` を取り込む。
    - 取り込んだ値を `tools.perf.collect_metrics` で統合し、`.ga/qa-metrics.json` から取得する。
  - 目標値: 0.85 以上を維持。
- reopen_rate
  - 目的: 再オープン率を追跡し、運用完了後の手戻りを抑制する。
  - 収集方法:
    - Prometheus の `workflow_reopen_rate_*` から `docops_reopen_rate` を経て正規化された値を `tools.perf.collect_metrics` で取得する。
  - 目標値: 5% 以下を維持。
- spec_completeness
  - 目的: スペック充足率を定量化し、要求事項の欠落を防ぐ。
  - 収集方法:
    - Prometheus の `workflow_spec_completeness_*` を参照し、`tools.perf.collect_metrics` が正規化した値を取得する。
    - Chainlit ログの `spec_completeness_*` を取り込み、`.ga/qa-metrics.json` で欠損や乖離がないか確認する。
  - 目標値: 90% 以上を維持。

> KPI の収集手順は [`RUNBOOK.md#Observability`](RUNBOOK.md#observability) と同期し、CLI やログ出力の設定に差異がないことを確認する。

## Test Outline

- 単体: 入力→出力の例テーブル（[ケース I-03](docs/addenda/I_Test_Cases.md#i-03-task-seed-tdd-例)）
- 結合: 代表シナリオ（[ケース I-02](docs/addenda/I_Test_Cases.md#i-02-birdseye-再生成確認)）
- 回帰: 重要パス再確認（[ケース I-01](docs/addenda/I_Test_Cases.md#i-01-チェックリスト突合)）

> 検証手順の詳細は [`docs/addenda/I_Test_Cases.md`](docs/addenda/I_Test_Cases.md) を参照する。

## Verification Checklist

- [ ] 主要フローが動作する（手動確認）
- [ ] エラー時挙動が明示されている
- [ ] 依存関係が再現できる環境である
