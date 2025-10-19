---
intent_id: INT-001
owner: your-handle
status: active   # draft|active|deprecated
last_reviewed_at: 2025-10-14
next_review_due: 2025-11-14
---

# Workflow Cookbook / Codex Task Kit

This repo defines QA/Governance-first workflows (not application code).
AI agents implement changes under these policies with acceptance tests and
canary rules.

<!-- LLM-BOOTSTRAP v1 -->
読む順番:

1. docs/birdseye/index.json  …… ノード一覧・隣接関係（軽量）
2. docs/birdseye/caps/`<path>`.json …… 必要ノードだけ point read（個別カプセル）

フォーカス手順:

- 直近変更ファイル±2hopのノードIDを index.json から取得
- 対応する caps/*.json のみ読み込み

<!-- /LLM-BOOTSTRAP -->

任意のリポジトリに貼るだけで、**仕様→実装→検収**まで一貫して回せるMD群。

- 人間にもエージェント（Codex等）にも読ませやすい最小フォーマット
- 言語・技術スタック非依存（存在するコマンドだけ使う）

## 使い方（最短）

1. これらのMDをリポジトリ直下に配置
   - この5ファイルを別リポにコピー
     - `BLUEPRINT.md`
     - `RUNBOOK.md`
     - `EVALUATION.md`
     - `CHECKLISTS.md`
     - `CHANGELOG.md`
2. `BLUEPRINT.md` で要件と制約を1ページに集約
3. 実行手順は `RUNBOOK.md`、評価基準は `EVALUATION.md` に記述し、
   以下で Birdseye の最小読込とタスク分割の前提を共有

    - [`GUARDRAILS.md`](GUARDRAILS.md) …… 行動指針と Birdseye の `deps_out`
      と整合する最小読込ガードレールを確認
    - [`tools/codemap/README.md`](tools/codemap/README.md) …… Birdseye カプセル
      再生成前提と `codemap.update` の流れを把握
    - [`tools/codemap/update.py`](tools/codemap/update.py) ……
      `python tools/codemap/update.py` で `codemap.update` を実行し
      Birdseye カプセルを再生成する。標準では直近変更ファイルから±2 hop の
      カプセルのみ更新し、今後導入予定の `--full` オプション指定時に
      全カプセルを再生成する（`GUARDRAILS.md` の
      [鮮度管理](GUARDRAILS.md#鮮度管理staleness-handling)
      参照）。

      ```sh
      # 例: カプセル出力先と解析ルートを指定して再生成
      python tools/codemap/update.py --caps docs/birdseye/caps --root .
      ```

    - [`HUB.codex.md`](HUB.codex.md) …… 仕様集約とタスク分割ハブを整備し、Birdseye カプセルの依存関係を維持
    - [`docs/IN-20250115-001.md`](docs/IN-20250115-001.md) …… インシデントログを参照し
      Birdseye カプセル要約で指示される `deps_out` を照合
4. タスクごとに `TASK.codex.md` を複製して内容を埋め、エージェントに渡す
   - 雛形との差分を確認したい場合は `examples/TASK.sample.md` を参照し、実在の値が埋め込まれたダミーサンプルと比較する
5. リリースは `CHECKLISTS.md` をなぞり、差分は `CHANGELOG.md` に追記

### 最小導入セット

- [`BLUEPRINT.md`](BLUEPRINT.md) …… Intent と仕様全体の骨子を提示
- [`RUNBOOK.md`](RUNBOOK.md) …… 実装および運用手順を逐次記載
- [`EVALUATION.md`](EVALUATION.md) …… 受入基準と検証観点を定義
- [`GUARDRAILS.md`](GUARDRAILS.md) …… 行動指針と Birdseye 連携の制約を明示
- [`HUB.codex.md`](HUB.codex.md) …… タスク分割と依存グラフの中核ハブを維持
- [`CHECKLISTS.md`](CHECKLISTS.md) …… リリースとレビューフローのチェックリストを提供
- [`governance-gate.yml`](.github/workflows/governance-gate.yml)
  …… Intent 検証 CI を常時有効化
- [`docs/security/SAC.md`](docs/security/SAC.md) …… セキュリティ非機能要件を契約として明文化
- [`docs/security/Security_Review_Checklist.md`](docs/security/Security_Review_Checklist.md) …… 準備→実装→レビューで実施するセキュリティ審査手順を提供
- [`reusable/python-ci.yml`](.github/workflows/reusable/python-ci.yml) /
  [`reusable/security-ci.yml`](.github/workflows/reusable/security-ci.yml)
  …… 他リポから `workflow_call` で利用できる最小CIセット
- Intent ゲートは
  [`tools/ci/check_governance_gate.py`](tools/ci/check_governance_gate.py) により
  自動適用されるため、CI の設定だけで運用に組み込めます
- SRC の主要言語に応じて、以下の CI テストセットを組み合わせると、導入直後から
  最低限の品質・安全・可搬性が確保できます

### 再利用CIの呼び出し例（下流リポ側）

```yaml
name: example CI
on: [push, pull_request]
jobs:
  python:
    uses: RNA4219/workflow-cookbook/.github/workflows/reusable/python-ci.yml@v0.1
    with:
      python-version: '3.11'
  security:
    uses: RNA4219/workflow-cookbook/.github/workflows/reusable/security-ci.yml@v0.1
    with:
      python-version: '3.11'
    secrets: inherit
  governance:
    uses: RNA4219/workflow-cookbook/.github/workflows/governance-gate.yml@v0.1
```

#### 言語別 CI テストセット（鉄板構成）

<!-- markdownlint-disable MD013 -->

| 言語 | カテゴリ | コマンド | 目的 |
| :--- | :--- | :--- | :--- |
| Rust | Format | `cargo fmt --all -- --check` | コード整形確認 |
| Rust | Lint | `cargo clippy --all-targets --all-features -D warnings` | 警告・アンチパターン検出 |
| Rust | Test | `cargo test --all-features` | 単体・統合テスト |
| Rust | Build | `cargo build --release` | リリースビルド確認 |
| Rust | Security | `cargo audit` / `cargo deny check` | 依存脆弱性・ライセンス確認 |
| Rust | Docs | `cargo doc -D warnings` | ドキュメント構文確認 |
| Rust (任意) | Coverage | `cargo llvm-cov` | カバレッジ測定 |
| Python | Format | `black --check .` | コード整形確認 |
| Python | Lint | `ruff check .` / `flake8 .` / `pylint src/` | コード品質 |
| Python | Typing | `mypy src/` | 型整合性 |
| Python | Test | `pytest --maxfail=1 --disable-warnings -q` | 単体・統合テスト |
| Python | Security | `bandit -r src/` / `pip-audit` | 静的セキュリティ解析 |
| Python | Coverage | `pytest --cov=src` | カバレッジ |
| Python | Docs | `pydocstyle src/` | docstring 構文確認 |
| Node.js/TS | Lint | `eslint .` / `tsc --noEmit` | コード・型検査 |
| Node.js/TS | Format | `prettier --check .` | 整形検証 |
| Node.js/TS | Test | `npm test` / `vitest run` / `jest --ci` | ユニットテスト |
| Node.js/TS | Build | `npm run build` | 本番ビルド |
| Node.js/TS | Security | `npm audit --audit-level=moderate` | 依存脆弱性 |

> CI 設定全体と最新実行のみを保持する自動キャンセル構成は、[`docs/ci-config.md`](docs/ci-config.md) を参照してください。
| Node.js/TS (任意) | Coverage | `npm run coverage` | カバレッジ |
| Node.js/TS | Docs | `typedoc` / `markdownlint` | API/MD構文確認 |
| Go | Format | `gofmt -l .` | 整形確認 |
| Go | Lint | `golangci-lint run` | 静的解析 |
| Go | Vet | `go vet ./...` | 構文・型安全検査 |
| Go | Test | `go test -v ./...` | 単体テスト |
| Go | Build | `go build ./...` | ビルド保証 |
| Go | Security | `gosec ./...` | 脆弱性スキャン |
| Go (任意) | Coverage | `go test -cover ./...` | カバレッジ測定 |
| Java | Format | `mvn formatter:validate` / `spotless:check` | 整形確認 |
| Java | Lint | `mvn checkstyle:check` / `spotbugs:check` | 静的解析 |
| Java | Test | `mvn test` / `gradle test` | 単体テスト |
| Java | Coverage | `mvn jacoco:report` | カバレッジ |
| Java | Security | `mvn dependency-check:check` | 依存脆弱性 |
| Java | Build | `mvn package` / `gradle build` | 本番ビルド |
| C/C++ | Format | `clang-format --dry-run -Werror` | 整形確認 |
| C/C++ | Lint | `cppcheck --enable=all` | 静的解析 |
| C/C++ | Build | `cmake . && make` / `meson compile` | ビルド確認 |
| C/C++ | Test | `ctest --output-on-failure` / `gtest` | 単体テスト |
| C/C++ | Security | `clang --analyze` / `cppcheck --addon=cert` | セキュリティ |
| C/C++ | Coverage | `lcov` / `gcov` | カバレッジ測定 |

#### 共通モジュール4種（全リポ共通）

| モジュール | 目的 | 設定例 |
| :--- | :--- | :--- |
| CodeQL | 静的解析・脆弱性検出 | `uses: github/codeql-action/init@v3` + `languages: python,javascript,go,rust` → `analyze` |
| Dependabot | 依存更新の自動PR | `.github/dependabot.yml` → `package-ecosystem: github-actions/npm/pip` + `schedule: weekly` |
| Pre-commit Hooks | Lint/Format 再現 | `.pre-commit-config.yaml` → `pre-commit-hooks`（YAML/EOF/WS） + `psf/black` などを追加 |
| Artifact Upload | テスト・レポート共有 | ジョブ末尾で `actions/upload-artifact@v4` → `if: always()` + `path: logs/*` |

![lint](https://github.com/RNA4219/workflow-cookbook/actions/workflows/markdown.yml/badge.svg)
![links](https://github.com/RNA4219/workflow-cookbook/actions/workflows/links.yml/badge.svg)
![lead_time_p95_hours](https://img.shields.io/badge/lead__time__p95__hours-24h-blue)
![mttr_p95_minutes](https://img.shields.io/badge/mttr__p95__minutes-30m-blue)
![change_failure_rate_max](https://img.shields.io/badge/change__failure__rate__max-0.20-blue)
<!-- markdownlint-enable MD013 -->

> バッジ値は `governance/policy.yaml` の `slo` と同期。更新時は同ファイルの値を修正し、上記3つのバッジ表示を揃える。

### Commit message guide

- feat: 〜 を追加
- fix: 〜 を修正
- chore/docs: 〜 を整備
- semver:major/minor/patch ラベルでリリース自動分類

### Pull Request checklist (CI 必須項目)

- PR 本文に `Intent: INT-xxx`（例: `Intent: INT-123`）を含めること。
- `EVALUATION` 見出し（例:
  `[Acceptance Criteria](EVALUATION.md#acceptance-criteria)`）へのリンクを本文に
  明示すること。
- 可能であれば `Priority Score: number` を追記し、`prioritization.yaml` の
  値を参照する。
- ローカルでゲートを確認する場合は `PR_BODY` に PR 本文を渡してから
  `python tools/ci/check_governance_gate.py` を実行する。

  ```sh
  PR_BODY=$(cat <<'EOF'
  Intent: INT-123
  ## EVALUATION
  - [Acceptance Criteria](EVALUATION.md#acceptance-criteria)
  Priority Score: 1
  EOF
  ) python tools/ci/check_governance_gate.py
  ```
