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

- 可観測性指標は [`governance/metrics.yaml`](governance/metrics.yaml) を基準とし、[ADR-021](docs/ADR/ADR-021-metrics-observability.md) で定義した統合フローに従う。
- QA メトリクス収集
  - `python -m tools.perf.collect_metrics --suite qa --metrics-url <Prometheus URL> --log-path <ログパス>` を実行し、`.ga/qa-metrics.json` を生成する。
  - `--metrics-url` は `review_latency` / `reopen_rate` / `compress_ratio` を取得し、`--log-path` は `semantic_retention` / `spec_completeness` を取り込む。片方のみ利用可能な場合は指定可能な引数だけ渡す。
  - Chainlit などの UI でログ出力する場合は `tools.perf.structured_logger.StructuredLogger` を利用して JSON 行を生成し、`collect_metrics --log-path <ファイル>` で取り込む。
  - Web サービスへ組み込む場合は `tools.perf.metrics_registry.MetricsRegistry` を初期化し、`observe_trim` を呼び出して `compress_ratio` / `semantic_retention` を記録する。
- 許容レンジ確認
  - `python - <<'PY'` で `.ga/qa-metrics.json` を読み、`EVALUATION.md#KPIs` の閾値と突き合わせる。
  - リリース前には [`docs/Release_Checklist.md`](docs/Release_Checklist.md) の該当項目を更新し、逸脱があればフォローアップを `docs/TASKS.md` に登録する。
- 失敗兆候と一次対応
  - `.ga/qa-metrics.json` 未生成: `collect_metrics --help` でオプションを再確認し、再実行前にキャッシュを削除。
  - 閾値逸脱: ログファイルで入力・応答の異常を確認し、再実行条件と共に記録。
  - コマンドエラー: 依存パッケージ不足を確認し、仮想環境へ必要モジュールを追加後に再実行。
- インシデント発生時は `docs/IN-YYYYMMDD-XXX.md` を作成し、最新サンプル（例: [`docs/IN-20250115-001.md`](docs/IN-20250115-001.md)）の書式でログ・メトリクス抜粋を添付する。

## Confirm

- Execute 結果を主要メトリクス・アウトプットと突き合わせ、`CHECKLISTS.md` の [Hygiene](CHECKLISTS.md#hygiene) で整合性と未完了項目を再確認
- インシデント記録を [docs/INCIDENT_TEMPLATE.md](docs/INCIDENT_TEMPLATE.md) に沿って初動報告→確定記録まで更新し、関連 PR / チケットへリンクを共有
- `Observability` で検知したアラート・兆候の解消を運用チャネルへ報告し、残るフォローアップを RUNBOOK / docs/IN-YYYYMMDD-XXX.md に追記

## Rollback / Retry

- どこまで戻すか、再実行条件
- インシデントサマリを更新後、該当PRの説明欄と本RUNBOOKの該当セクションにリンクを追加する
