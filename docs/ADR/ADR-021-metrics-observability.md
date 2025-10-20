# ADR-021: メトリクスと可観測性の統合
- 日付: 2025-01-15
- 背景: デプロイ後の振り返りで SLO を示す統一的なメトリクス参照点が不足しており、リリース可否判断やインシデント初動で資料が分散していた。
- 決定: RUNBOOK / EVALUATION / governance/metrics.yaml を統一メトリクスセットで結び、`CHECKLISTS.md` の Release でメトリクス最新化と証跡共有を必須化する。Birdseye マップと Katamari 由来の監視テンプレを同期して、可観測性の指標と操作フローを一元管理する。
- 影響範囲: 運用チーム、レビューフロー、docs/birdseye 配下の依存チャート、tools/perf/* モジュールのダッシュボード生成処理。
- フォローアップ: tools/perf/ 配下モジュールのメトリクス収集テンプレ更新、Birdseye ターゲットの定期同期、Release レビューでのメトリクス差分チェックの運用定着。

## 関連ドキュメント
- [CHECKLISTS.md の Release 手順](../../CHECKLISTS.md#release)
- [RUNBOOK.md の Observability セクション](../../RUNBOOK.md#observability)
- [EVALUATION.md の KPIs セクション](../../EVALUATION.md#kpis)
- [governance/metrics.yaml](../../governance/metrics.yaml)
- [docs/birdseye/index.json](../birdseye/index.json)
