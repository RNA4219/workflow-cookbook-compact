---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-14
next_review_due: 2025-11-14
---

# Downsized Workflow Cookbook / Codex Task Kit

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](LICENSE)

ローカルCPUや小規模GPUでも回せる、軽量なワークフロー運用テンプレート集です。オリジナル版のガバナンスとガードレールを維持しつつ、最小限のレシピとツールで**要約→要件→設計**までをシングルターン中心で実行できます。

## 目的 / Purpose

- **軽量化:** 1〜3Bクラスのローカルモデルや≈7B GPUモデル、安価なAPIでも実行可能なテンプレートとレシピを提供します。
- **ガバナンス維持:** Blueprint / Runbook / Evaluation / Guardrails / Spec / Design などの必須テンプレートを残し、実装前の要件整理と受入基準定義を徹底します。
- **ROI重視:** 要件を価値・労力・リスク・確信度で評価し、`ROI_BUDGET` 内で高ROIのストーリーを優先実装します。

## スコープ / Scope

### 対象範囲

- 上記テンプレート群（`docs/`配下）と、最小限のガイド付きレシピ（`recipes/`）。
- レシピ実行を支援する軽量スクリプトと BirdEye-Lite、ROI プランナー等のツール（`tools/`）。
- モデル別プロフィールやトークン予算を定義する設定ファイル（`config/`）。
- 入力・出力例、ROI スコア付与例を収めたサンプル群（`examples/`）。

### 対象外

- 大規模BirdEyeグラフやフル装備のガバナンス文書（ADR管理、セキュリティ審査の全工程等）。
- 7Bモデルで約1kトークン、CPUモデルで約500トークンを超える長大な入出力を前提としたパイプライン。
- 予算超過を自動ブロックする機能（通知と警告のみ提供）。

## 制約 / Constraints

- **コンテキスト予算:** CPUモデルは入力≈500トークン、7Bモデルは≈1,000トークンを上限に想定。出力も≈200–300トークンで設計します。
- **ハードウェア:** GPUなしや量子化済みモデルを想定し、会話ターン数を極小化します。
- **JSON必須:** すべてのLLM出力は JSON スキーマで検証可能な形に揃えます。
- **ROI予算:** `ROI_BUDGET` 環境変数で実装可能な総労力を制御し、超過ストーリーは自動で後回しにします。
- **設計キャパシティ:** 日次の厳密上限は設けませんが、5万行規模を超える場合はタスク分割や手動介入を検討してください。

## ディレクトリ構成 / Directory Layout

```
downsized-cookbook/
├── docs/                   # テンプレートとガバナンス文書
│   ├── BLUEPRINT.md        # 課題/スコープ/制約/I-O契約/フロー
│   ├── RUNBOOK.md          # 環境構築・実行手順・検証
│   ├── EVALUATION.md       # 受入基準・KPI・チェック項目
│   ├── GUARDRAILS.md       # 行動指針と最小コンテキストルール
│   ├── SPEC.md             # レシピI/O・状態・エラー設計
│   ├── DESIGN.md           # ディレクトリ構成と高位アーキ
│   └── ...                 # 追加の軽量ドキュメント
├── recipes/                # 共通スキーマのYAMLレシピ
│   ├── summarize.yaml
│   ├── req_to_srs_roi.yaml
│   ├── srs_scope_plan.yaml
│   ├── srs_to_design_roi.yaml
│   └── birdseye_summary.yaml
├── tools/                  # レシピ実行とチェック用スクリプト
│   ├── runner.{ts,py}
│   ├── birdseye_lite.py
│   ├── loc_budget_check.py
│   └── roi_planner.py
├── examples/               # サンプル入力/出力/ROIテーブル
├── config/                 # モデルプロファイルと予算設定
└── README.md               # 本ドキュメント
```

## クイックスタート / Quick Start

1. **必須テンプレートをコピー:** `docs/`直下の Blueprint / Runbook / Evaluation / Guardrails / Spec / Design をプロジェクト用に複製し、課題・制約・受入基準を埋めます。
2. **ROI予算を設定:** `.env` 等で `ROI_BUDGET=<effort_points>` を設定し、`recipes/req_to_srs_roi.yaml` → `recipes/srs_scope_plan.yaml` の順に実行します。
3. **レシピを実行:** `tools/runner.{ts,py}` で YAML を読み込み、入力ファイルを指定してシングルターンで JSON 出力を得ます。`budget.max_input`/`max_output` を守り、必要に応じて要約や分割を挟みます。
4. **BirdEye-Lite:** `tools/birdseye_lite.py` を使い、対象リポジトリの import/use 関係から最大30ノード/60エッジの Mermaid 図を生成し、レシピに添付します。
5. **成果を検証:** `EVALUATION.md` に定義したスキーマ検証・ROIコンプライアンス・受入テストを満たしているか確認し、`CHANGELOG.md` に通番付きで記録します。

## レシピ概要 / Recipes

| レシピ | 目的 | 主な出力 |
| --- | --- | --- |
| `summarize.yaml` | テキスト要約 | JSON形式の箇条書き要約（例: 5項目） |
| `req_to_srs_roi.yaml` | 要件→SRS変換 | ストーリーごとの `value` / `effort` / `risk` / `confidence` / `roi_score` |
| `srs_scope_plan.yaml` | ROI選別とスコープ策定 | `ROI_BUDGET` 内で採択したストーリー一覧と残余ストーリー |
| `srs_to_design_roi.yaml` | 設計アーティファクト生成 | ストーリーIDとモジュール/インターフェース対応表 |
| `birdseye_summary.yaml` | 依存関係可視化 | 上位依存のみの Mermaid グラフ |

## ツール / Tools

- **レシピランナー:** YAMLを読み込みプロンプト組立→LLM呼び出し→JSONスキーマ検証→成果保存を自動化。
- **BirdEye-Lite:** リポジトリを走査し、重要な import/use エッジを抽出・ランキングして軽量 Mermaid グラフを生成。
- **LOC予算チェッカー:** 指定ディレクトリの行数を集計し、推奨設計キャパシティ超過を警告。
- **ROIプランナー:** ストーリーのROIスコア計算と予算内選択を支援。

## ガバナンスと評価 / Governance & Evaluation

- **GUARDRAILS.md:** 長文投入前の要約やモデルの能力範囲遵守など、LLM連携時の行動指針を明記しています。
- **EVALUATION.md:** スキーマ検証・ROIテスト・受入基準をチェックリスト化し、自動検証を容易にします。
- **CHANGELOG.md:** すべての変更を時系列で記録し、テンプレートの適用と成果物を追跡します。

## 非機能要件 / Non-Functional Notes

- **移植性:** Node.js または Python のみで実行でき、重い依存を避けています。
- **拡張性:** 新しいレシピやテンプレート、プロファイルを追加しやすい汎用構造です。
- **ユーザビリティ:** README / `examples/` / `config/` に初期セットアップとデフォルト値を用意し、導入の初速を高めます。

## 次のステップ / Next Steps

- プロジェクト固有の課題・制約を `BLUEPRINT.md` に整理し、ROI 観点で実装対象を絞り込む。
- LLM クライアント（OpenAI互換APIやOllama等）を設定し、`tools/runner` 経由でサンプルレシピを実行する。
- 生成された成果物を `docs/` 配下へ格納し、`EVALUATION.md` のチェックリストで検収する。

この Downsized Workflow Cookbook により、限られたハードウェアでも再現性とガバナンスを担保しつつ、短時間でワークフローを回せるようになります。

