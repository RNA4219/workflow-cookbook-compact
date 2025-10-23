---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-21
next_review_due: 2025-11-21
---

# Runbook

## Environments

- Local / CI / Prod の差分（キー名だけ列挙）

## Execute

- 準備 → 実行 → 確認（最短手順）
- 例）
  - 準備: データ投入 / キャッシュ初期化
  - 実行: コマンド/ジョブ名
  - 確認: 出力の存在・件数・整合

## Observability

- ログ/メトリクスの確認点、失敗時の兆候（[ADR-021: メトリクスと可観測性の統合](docs/ADR/ADR-021-metrics-observability.md) を参照）
- インシデント発生時は docs/IN-YYYYMMDD-XXX.md に記録し、最新サンプル（[IN-20250115-001](docs/IN-20250115-001.md)）を参照して検知し、ログ・メトリクスの抜粋を添付
- ドキュメント運用メトリクスの収集と確認
  - `python -m tools.perf.collect_metrics --suite qa --metrics-url <Prometheus URL> --log-path <構造化ログパス>` を実行する。`--suite qa` は `.ga/qa-metrics.json` への書き出しを既定とし、Prometheus（`checklist_compliance_rate` などの Gauge）と構造化ログ（例: `docs/logs/docops.log`）から `checklist_compliance_rate` / `task_seed_cycle_time_minutes` / `birdseye_refresh_delay_minutes` を統合する。出力先を変更したい場合は `--output <JSON パス>` を追加指定する。
  - 構造化ログは `tools.perf.structured_logger.StructuredLogger` で生成する。例: `StructuredLogger(name="docops", path="~/logs/docops.log").record(metrics={"task_seed_cycle_time_minutes": 45.0})`。`collect_metrics --log-path` へ同パスを渡すと `metrics` キー配下の辞書がそのまま集計される。
  - 常駐プロセスから Prometheus へ公開する場合は `tools.perf.metrics_registry.MetricsRegistry` を初期化し、`observe("checklist_compliance_rate", ratio)` や `observe("task_seed_cycle_time_minutes", minutes)` を必要時に呼び出す。`PlainTextResponse(registry.export_prometheus())` を `/metrics` エンドポイントで返すと収集 CLI が利用可能。
  - 実行後に `.ga/qa-metrics.json` が生成されていることを確認する。生成されない場合は `--output` に明示したパスと標準出力を突き合わせて異常を特定。
  - `python - <<'PY'` → `import json; data=json.load(open('.ga/qa-metrics.json', encoding='utf-8')); print({k: data[k] for k in ('checklist_compliance_rate', 'task_seed_cycle_time_minutes', 'birdseye_refresh_delay_minutes')})` で各メトリクスの値を抽出する。閾値逸脱時は直近正常値と実行条件を比較し、フォローアップチケットを起票する。
- 失敗兆候と一次対応
  - `.ga/qa-metrics.json` が生成されない / 壊れている: `python -m tools.perf.collect_metrics --help` でオプションを再確認し、一時ファイルやログ出力設定を洗い直してから再実行。
  - `checklist_compliance_rate` が 95% を下回る: 実行時のチェックリスト完了ログを抽出し、どの項目が未完了かを Birdseye や Git 履歴で確認する。改善作業が必要な場合は Task Seed を追加投入する。
  - `task_seed_cycle_time_minutes` が 1440 分を超過: 受付から着手までの待機要因（担当者アサイン、依頼内容不備など）を振り返り、対応 SLA を再共有する。
  - `birdseye_refresh_delay_minutes` が 60 分を超過: Birdseye 更新ジョブの実行ログとスケジューラ状態を確認し、必要に応じて手動更新を実施。

## Confirm

- Execute 結果を主要メトリクス・アウトプットと突き合わせ、`CHECKLISTS.md` の [Hygiene](CHECKLISTS.md#hygiene) で整合性と未完了項目を再確認
- インシデント記録を [docs/INCIDENT_TEMPLATE.md](docs/INCIDENT_TEMPLATE.md) に沿って初動報告→確定記録まで更新し、関連 PR / チケットへリンクを共有
- `Observability` で検知したアラート・兆候の解消を運用チャネルへ報告し、残るフォローアップを RUNBOOK / docs/IN-YYYYMMDD-XXX.md に追記

## Rollback / Retry

- どこまで戻すか、再実行条件
- インシデントサマリを更新後、該当PRの説明欄と本RUNBOOKの該当セクションにリンクを追加する
