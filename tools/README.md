# Tools Overview

このディレクトリには実装済みスクリプトは含まれていません。`docs/downsized_cookbook_requirements_spec.md` に沿って外部ツールを配置する際の責務を整理するメモとして利用してください。

## 補助ツール一覧

- **レシピランナー**: YAML レシピを実行し、JSON 検証やトークン予算 (`budget.max_input/max_output`) の監視を担う外部実装。
- **BirdEye-Lite**: 依存関係を抽出し、≤30 ノード／≤60 エッジの Mermaid グラフを生成する可視化ツール。手順は `docs/BIRDSEYE.md` を参照。
- **ROI Planner**: `value` / `effort` / `risk` / `confidence` から `roi_score` を算出し、`ROI_BUDGET` 内のストーリー選定を補助。
- **LOC Budget Checker**: 設計キャパシティや推奨行数を超過しないかを確認し、超過時に警告するためのユーティリティ。

各ツールは ROI とトークン予算のガードレールを尊重し、検証可能な JSON を出力することを前提としています。
