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

`governance/metrics.yaml` に定義された可観測性メトリクスを、リリース運用基準
（[`docs/addenda/M_Versioning_Release.md`](docs/addenda/M_Versioning_Release.md)）
と整合させて管理する。許容レンジと集計頻度は以下を標準とする。

| key | 指標の意味 | 許容レンジ | 集計頻度 | 取得手段 |
| :-- | :-- | :-- | :-- | :-- |
| review_latency | 平均レビュー完了時間(h) | 24h 未満 | 週次 | `python -m tools.perf.collect_metrics --suite qa --metrics-url <Prometheus URL>` |
| reopen_rate | 再修正率(%) | 15% 以下 | スプリント単位 | 上記コマンド + `.ga/qa-metrics.json` 確認 |
| spec_completeness | 要件/仕様/設計が揃った PR 比率(%) | 90% 以上 | スプリント単位 | Chainlit ログを `--log-path` で渡す |
| compress_ratio | 圧縮後サイズ/元サイズの比率(%) | 85%〜115% | 週次 | `collect_metrics` の圧縮統計出力 |
| semantic_retention | 圧縮後レビューコメントの意味保持率(%) | 95% 以上 | スプリント単位 | `collect_metrics` のレビューログ解析出力 |

集計結果は `.ga/qa-metrics.json` に保存し、リリース判定前に
[`docs/Release_Checklist.md`](docs/Release_Checklist.md) と突き合わせて許容レンジ内であることを確認する。

## Test Outline

- 単体: 入力→出力の例テーブル（[ケース I-03](docs/addenda/I_Test_Cases.md#i-03-task-seed-tdd-例)）
- 結合: 代表シナリオ（[ケース I-02](docs/addenda/I_Test_Cases.md#i-02-birdseye-再生成確認)）
- 回帰: 重要パス再確認（[ケース I-01](docs/addenda/I_Test_Cases.md#i-01-チェックリスト突合)）

> 検証手順の詳細は [`docs/addenda/I_Test_Cases.md`](docs/addenda/I_Test_Cases.md) を参照する。

## Verification Checklist

- [ ] 主要フローが動作する（手動確認）
- [ ] エラー時挙動が明示されている
- [ ] 依存関係が再現できる環境である
