# Roadmap & Specs ハブ

## 上位ドキュメント索引
| レイヤ | ドキュメント | 主要内容 | 関連ワークフロー |
| :-- | :-- | :-- | :-- |
| 骨子 | [BLUEPRINT.md](../BLUEPRINT.md) | 課題・スコープ・I/O 契約を1ページに集約。 | 設計着手前にインテントを固め、`HUB.codex.md` の[入力ファイル分類](../HUB.codex.md#2-入力ファイル分類)へ渡す。 |
| 実行 | [RUNBOOK.md](../RUNBOOK.md) | 環境差分と準備→実行→確認の手順を列挙。 | インシデント時に [IN-20250115-001.md](IN-20250115-001.md) を参照し、`CHECKLISTS.md` の [Release](../CHECKLISTS.md#release) を更新。 |
| 検収 | [EVALUATION.md](../EVALUATION.md) | 受入基準・KPI・検証チェックリストを定義。 | ガバナンス CI で `governance/policy.yaml` の[禁止パス](../governance/policy.yaml)を監視。 |
| 行動指針 | [GUARDRAILS.md](../GUARDRAILS.md) | 行動原則と Birdseye 読込手順を規定。 | 「[Birdseye / Minimal Context Intake Guardrails](../GUARDRAILS.md#birdseye--minimal-context-intake-guardrails鳥観図最小読込)」を参照し、タスク分割前に対象ノードを確定。 |
| タスク統制 | [HUB.codex.md](../HUB.codex.md) | 仕様・運用ドキュメントを束ね、タスク化を自動分配。 | `TASK.*` シード生成時に [入力ファイル分類](../HUB.codex.md#2-入力ファイル分類)を参照。 |
| リリース判定 | [CHECKLISTS.md](../CHECKLISTS.md) | 日次・リリース・衛生のチェック項目。 | リリース前に `EVALUATION.md` の[Verification Checklist](../EVALUATION.md#verification-checklist)と突き合わせ。 |
| 依存グラフ | [docs/birdseye/index.json](birdseye/index.json) / [caps/*](birdseye/caps/) | ノード一覧とカプセルで Birdseye トポロジを提供。 | `codemap.update` で再生成し、`GUARDRAILS.md` の[鮮度管理](../GUARDRAILS.md#鮮度管理staleness-handling)に従って鮮度を監視。 |
| ガバナンス | [governance/policy.yaml](../governance/policy.yaml) / [prioritization.yaml](../governance/prioritization.yaml) / [metrics.yaml](../governance/metrics.yaml) | セルフモディフィケーション制御、優先度算出基準、定常メトリクス。 | `HUB.codex.md` の優先度判定および `CHECKLISTS.md` の衛生チェックで参照。 |

## 実装ディレクトリ↔仕様対応
| ディレクトリ | 紐付く仕様ドキュメント | 備考 |
| :-- | :-- | :-- |
| `docs/birdseye/` | [GUARDRAILS.md](../GUARDRAILS.md#birdseye--minimal-context-intake-guardrails鳥観図最小読込)<br>[tools/codemap/README.md](../tools/codemap/README.md#実行手順) | Birdseye トポロジーを生成し鮮度を保つ[^birdseye] |
| `docs/security/` | [SECURITY.md](../SECURITY.md)<br>[security/Security_Review_Checklist.md](security/Security_Review_Checklist.md) | セキュリティレビューと SAC を同期[^security] |
| `examples/` | [design.md](design.md)<br>[spec.md](spec.md) | レシピの参照実装と設計・仕様を突き合わせる |
| `styles/` | [design.md](design.md)<br>[requirements.md](requirements.md) | QA ルールに基づく表記統一・禁止用語チェック[^styles] |
| `tools/` | [design.md](design.md)<br>[../RUNBOOK.md](../RUNBOOK.md#execute) | ドキュメント同期用スクリプトと運用手順を連結 |
| `tools/codemap/` | [tools/codemap/README.md](../tools/codemap/README.md)<br>[../CHECKLISTS.md](../CHECKLISTS.md#hygiene) | Birdseye 再生成 CLI と衛生チェックを担保[^codemap] |
| `governance/` | [../EVALUATION.md](../EVALUATION.md#acceptance-criteria)<br>[../governance/policy.yaml](../governance/policy.yaml) | 受入基準と禁止パス・優先度設定を同期[^governance] |
| `tests/` | [../EVALUATION.md](../EVALUATION.md#test-outline)<br>[birdseye/caps/](birdseye/caps/) | テストアウトラインと Birdseye カプセルを連携更新[^tests] |

[^birdseye]: `python tools/codemap/update.py` で `docs/birdseye/index.json` と `caps/*` を再生成し、`GUARDRAILS.md` の鮮度管理基準を維持する。
[^security]: レビュー結果と是正策は `docs/security/SAC.md` に記録し、チェックリストでトレースする。
[^styles]: `styles/qa/QA.yml` の用語統一・禁止用語ルールをレビュー時に適用する。
[^codemap]: CLI 実行後は `CHECKLISTS.md` の Hygiene セクションで差分確認を行う。
[^governance]: 方針改定時は `EVALUATION.md` の Acceptance Criteria と照合し、必要に応じて優先度・禁止パスを更新する。
[^tests]: テスト追加時は `EVALUATION.md` の Test Outline と Birdseye カプセルの `tests` フィールドを更新する。

## ロードマップ
- **Guardrails 更新の定期レビュー**
  - [GUARDRAILS.md](../GUARDRAILS.md) の `next_review_due` を起点に方針を棚卸し。
  - 更新内容は `CHECKLISTS.md` の[Release](../CHECKLISTS.md#release) でレビューし、`HUB.codex.md` の[Rules](../HUB.codex.md#rules)へ波及。
- **Birdseye 鮮度管理の自動化**
  - `docs/birdseye/index.json` の `generated_at` 監視と、`tools/codemap/update.py` の `--targets` / `--emit` フローを `RUNBOOK.md` の[Execute](../RUNBOOK.md#execute)へ追記予定。
  - ステータスは `GUARDRAILS.md` の[鮮度管理](../GUARDRAILS.md#鮮度管理staleness-handling)と[codemap 未実装時の暫定手順](../GUARDRAILS.md#codemap-未実装時の暫定手順)で追跡。
- **CI テンプレ整備**
  - `ci-config.md` の設定例を `README.md` の[再利用CIの呼び出し例](../README.md#再利用ciの呼び出し例下流リポ側)と整合させる。
  - `governance/policy.yaml` の `ci.required_jobs` を基準に、`CHECKLISTS.md` の[Daily](../CHECKLISTS.md#daily)で稼働状況をモニタ。

## 更新フロー
1. **Guardrails ドキュメント改訂**
   - 方針変更は `BLUEPRINT.md` の[Constraints / Assumptions](../BLUEPRINT.md#3-constraints--assumptions)で前提を更新後、`GUARDRAILS.md` の[実装原則](../GUARDRAILS.md#実装原則)と[生成物に関する要求](../GUARDRAILS.md#生成物に関する要求出力契約)へ反映。
   - 改訂後、`EVALUATION.md` の[Acceptance Criteria](../EVALUATION.md#acceptance-criteria)および `CHECKLISTS.md` の[Release](../CHECKLISTS.md#release)で相互リンクを確認。
2. **Birdseye 再生成**
   - `GUARDRAILS.md` の[鮮度管理](../GUARDRAILS.md#鮮度管理staleness-handling)に沿って再生成条件を判定。
   - `tools/codemap/README.md` の[実行手順](../tools/codemap/README.md#実行手順)通り `python tools/codemap/update.py` を実行し、`docs/birdseye/index.json` と `caps/*` を更新。
   - ツール未整備時は `GUARDRAILS.md` の[codemap 未実装時の暫定手順](../GUARDRAILS.md#codemap-未実装時の暫定手順)に従って手動更新を依頼し、結果を `HUB.codex.md` の[Output Contract](../HUB.codex.md#output-contract)へ反映。
