---
intent_id: INT-999
owner: sample-author
status: active
last_reviewed_at: 2025-01-15
next_review_due: 2025-02-15
---

# SLO Reporting Workflow (Sample Requirement)

## Context / メタデータ

```yaml
task_id: 20250115-01
repo: https://github.com/example/workflow-cookbook-sample
base_branch: main
work_branch: feat/add-slo-reports
priority: P2
langs: [python, typescript]
```

## Problem Statement / 課題

SLO レポート生成を自動化し、週次で主要サービスのしきい値逸脱を検知したい。現状は手動集計で遅延が発生している。

## Scope / スコープ

- **In:** `docs/slo/**`, `tools/reporting/**`, `.github/workflows/slo-report.yml`
- **Out:** `backend/api/**`, `frontend/**`, `infra/terraform/**`

## Constraints / 制約

- 既存 API や CLI の互換性を維持すること。
- 追加依存は標準ライブラリと既存ロックファイル内に限定。
- `ruff` / `mypy --strict` / `pytest -q` / `pnpm lint` / `pnpm test` を全てグリーンに保つ。

## Inputs & Outputs / I/O 契約

| 種別 | パス | 内容 |
| --- | --- | --- |
| Input | `config/slo.yaml` | 対象サービス名と SLO しきい値を含む YAML |
| Output | `artifacts/slo-report-<date>.md` | 週次 SLO レポート (Markdown) |

## ROI Story Table / ROI ストーリーテーブル

| id | value | effort | risk | confidence | roi_score | notes |
| -- | ----- | ------ | ---- | ---------- | --------- | ----- |
| SLO-1 | 5 | 3 | 2 | 0.7 | 1.17 | レポート生成 CLI の追加 |
| SLO-2 | 4 | 2 | 1 | 0.6 | 1.20 | GitHub Actions 連携 |
| SLO-3 | 2 | 1 | 2 | 0.8 | 0.80 | 閾値逸脱の通知テンプレート |

`ROI_BUDGET=4` の場合、SLO-1 と SLO-2 を優先採択し、SLO-3 はバックログに保留する。

## Acceptance Criteria / 受入基準

1. `python tools/reporting/generate.py` が JSON で成功レスポンスを返し、`artifacts/` に最新レポートを出力する。
2. GitHub Actions ワークフローが ROI 採択ストーリーのみを実行し、成果物をアーティファクトとして保存する。
3. BirdEye-Lite で `tools/reporting/**` の依存が 30 ノード / 60 エッジ以内に収まること。

## Verification / 検証コマンド

```bash
ruff check docs/slo tools/reporting \
  && mypy --strict tools/reporting \
  && pytest tests/reporting -q \
  && pnpm lint --filter slo-dashboard \
  && pnpm test --filter slo-dashboard
```

## Notes / 備考

- ROI 未採択の SLO-3 については次フェーズで検討する。
- レポートテンプレートは `docs/slo/TEMPLATE.md` に保守する。
- 生成ステップは `docs/RUNBOOK.md` の BirdEye-Lite 手順を再利用する。
