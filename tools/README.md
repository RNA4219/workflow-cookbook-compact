# Tools Overview

- `runner.py` / `runner.ts`: Execute recipes with JSON validation and budget checks.
- `birdseye_lite.py`: Produce compact dependency graphs (≤30 nodes, ≤60 edges).
- `loc_budget_check.py`: Warn when line-of-code limits exceed recommendations.
- `roi_planner.py`: Calculate ROI scores and suggest priority scopes.

各ツールは ROI とトークン予算のガードレールを尊重し、JSON 出力を標準とします。
