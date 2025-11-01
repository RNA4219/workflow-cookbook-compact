# Downsized Workflow Cookbook: Requirements & Specification
_JP: ダウンサイザード Workflow Cookbook: 要件と仕様_

## Purpose & Goals
_JP: 目的とゴール_

- **Simplify the original Workflow Cookbook for local execution:** The downsized version targets local CPUs (1–3 B models) and modest GPUs (≈7 B) or inexpensive API endpoints.  It provides a lean set of workflows for summarisation, requirements‐to‐SRS conversion and SRS‐to‐design translation, ensuring that tasks can run within limited context windows and hardware budgets.
  - JP: **ローカル実行向けにオリジナルの Workflow Cookbook を簡素化:** ダウンサイザード版はローカル CPU（1〜3B モデル）と小規模 GPU（約7B モデル）または低コストな API エンドポイントを対象とします。要約、要件から SRS への変換、および SRS から設計への変換を行う軽量なワークフローを提供し、限られたコンテキストウィンドウとハードウェア予算内でタスクが実行できるようにします。
- **Preserve core governance and guardrails:**  While the large cookbook supports extensive documents and automated checks, this version retains the essential templates—Blueprint, Runbook, Evaluation, Guardrails and Design—so that users still define problems, scopes, constraints, flows and acceptance criteria before implementation.
  - JP: **主要なガバナンスとガードレールの維持:** 大規模版では広範なドキュメントや自動チェックをサポートしますが、この版では Blueprint、Runbook、Evaluation、Guardrails、Design といった基本的なテンプレートを保持し、実装前に利用者が課題、スコープ、制約、フロー、受け入れ基準を定義できるようにします。
- **Use ROI to focus effort:**  The new pipelines incorporate a return‑on‑investment (ROI) methodology to break down requirements into epics/stories with value, effort, risk and confidence scores; only high‑ROI stories are implemented within the available budget.
  - JP: **ROI による注力対象の明確化:** 新しいパイプラインは投資対効果（ROI）手法を組み込み、要件を価値・労力・リスク・確信度スコア付きのエピック／ストーリーに分解します。利用可能な予算内では高 ROI のストーリーのみを実装します。

## Scope
_JP: スコープ_

- **In scope:**
  - JP: **対象範囲:**
  - A minimal set of markdown templates (Blueprint, Runbook, Evaluation, Guardrails, Spec and Design) to describe tasks, constraints and acceptance criteria.
    - JP: 課題、制約、受け入れ基準を記述する最小限の Markdown テンプレート（Blueprint、Runbook、Evaluation、Guardrails、Spec、Design）。
  - YAML recipes to drive tasks such as summarising input text, converting requirements to SRS (with ROI), creating a scope plan and translating SRS into design artefacts.  Each recipe defines inputs, outputs and budgets.
    - JP: 入出力と予算を定義する YAML レシピ。要約、要件から SRS（ROI 付き）、スコープ計画の作成、SRS から設計成果物への翻訳などのタスクを駆動します。
  - Lightweight scripts to run recipes through pluggable LLM clients (e.g., OpenAI compatible API or Ollama), enforce optional token budgets and output JSON.
    - JP: プラガブルな LLM クライアント（例: OpenAI 互換 API や Ollama）を通じてレシピを実行し、任意のトークン予算を適用し、JSON を出力する軽量スクリプト。
  - A `HUB.codex.md` document that aggregates governance materials and codifies task orchestration rules for agents.
    - JP: ガバナンス資料を集約し、エージェントによるタスクオーケストレーション規則を定義する `HUB.codex.md` ドキュメント。
  - A “BirdEye‑Lite” tool that scans a repository for import/use relations and produces a mermaid graph limited to the top N nodes/edges, avoiding large context ingestion【172882294315981†L18-L32】.
    - JP: リポジトリをスキャンして import／利用関係を抽出し、トップ N ノード／エッジに限定した Mermaid グラフを生成する「BirdEye-Lite」ツール。巨大なコンテキストの取り込みを避けます【172882294315981†L18-L32】。
  - Optional tools to compute line‑of‑code budgets and warn when input sizes exceed the recommended guidelines.
    - JP: 推奨ガイドラインを超過しそうな入力サイズを警告し、行数予算を算出するオプションツール。

- **Out of scope:**
  - JP: **対象外:**
  - Managing large BirdEye graphs or the full suite of governance documents (e.g., ADR management, security review, extensive checklist operations).
    - JP: 大規模な BirdEye グラフや、フルセットのガバナンス文書（ADR 管理、セキュリティレビュー、詳細なチェックリスト運用など）の管理。
  - Tasks requiring more than ~1 k tokens of input on a 7 B model or ~500 tokens on CPU‑only models.
    - JP: 7B モデルで約 1k トークン、CPU のみのモデルで約 500 トークンを超える入力を必要とするタスク。
  - Automatic enforcement of budgets; the kit warns but does not block tasks that exceed the suggested limits.
    - JP: 予算の自動強制。キットは推奨値超過を警告しますがブロックはしません。

## Assumptions & Constraints
_JP: 前提と制約_

- **Limited context budgets:**  The practical input context for local CPU models is about 500 tokens, and for 7 B models about 1 000 tokens; outputs are similarly constrained (≈200–300 tokens).  These limits include the system prompt, task instructions, digests of documents and any code snippets.  Users should summarise or chunk inputs accordingly.
  - JP: **限定されたコンテキスト予算:** ローカル CPU モデルの実用的な入力コンテキストは約 500 トークン、7B モデルは約 1,000 トークン程度です。出力も同様に（約 200〜300 トークン）に制限されます。これらにはシステムプロンプト、タスク指示、ドキュメント要約、コード断片が含まれるため、利用者は入力を要約または分割すべきです。
- **Hardware constraints:**  The kit assumes users may lack GPUs or run small quantised models.  Pipelines and recipes must therefore avoid token‑heavy conversations and rely on single‑turn or few‑turn interactions.
  - JP: **ハードウェア制約:** 利用者が GPU を持たない、または小型の量子化モデルを実行する前提です。そのためパイプラインやレシピはトークンを大量消費する対話を避け、単発もしくは少数ターンのインタラクションに依存します。
- **JSON‑only outputs:**  All LLM outputs must conform to a JSON schema, facilitating downstream processing and validation.
  - JP: **JSON のみの出力:** すべての LLM 出力は JSON スキーマに準拠し、下流での処理と検証を容易にします。
- **ROI budget:**  When breaking requirements into stories, an environment variable (e.g., `ROI_BUDGET`) controls the total effort points to implement.  Stories exceeding this budget are deferred.
  - JP: **ROI 予算:** 要件をストーリーに分解する際、環境変数（例: `ROI_BUDGET`）が実装可能な総労力ポイントを制御します。この予算を超えるストーリーは後回しにします。
- **Design capacity:**  This version does not set a strict daily line limit, but it suggests a design capacity equivalent to ≈50 k lines of code to signal when tasks might need manual intervention.
  - JP: **設計キャパシティ:** 本版では厳密な日次行数制限は設けませんが、タスクに手動介入が必要になる兆候として約 50k 行分の設計キャパシティを推奨します。

## Key Components
_JP: 主な構成要素_

1. **Directory structure:**  Following the original cookbook’s design, the downsized kit places templates and deliverables under `docs/`, sample inputs/outputs under `examples/` and helper scripts under `tools/`【706646524446654†L10-L18】.  Recipes live in a `recipes/` folder, and configuration in `config/`.  This structure ensures CI or scripts can find mandatory files and simplifies navigation.
_JP: 1. **ディレクトリ構成:** オリジナルの Cookbook の設計に従い、テンプレートと成果物は `docs/`、サンプル入出力は `examples/`、ヘルパースクリプトは `tools/` に配置します【706646524446654†L10-L18】。レシピは `recipes/`、設定は `config/` に置きます。この構成により CI やスクリプトが必須ファイルを見つけやすく、ナビゲーションも簡単になります。_
   - Include a root-level `HUB.codex.md` that links these artefacts and defines automation policies for splitting tasks.
     - JP: これらの成果物を連携し、自動タスク分割ポリシーを定義するルート直下の `HUB.codex.md` を含めます。
2. **Templates:**
_JP: 2. **テンプレート:**_
   - **BLUEPRINT.md** – captures the problem statement, scope (in/out), constraints/assumptions, I/O contract, minimal flow and interfaces.  It follows the original blueprint template but encourages brevity.
     - JP: **BLUEPRINT.md** – 課題記述、スコープ（対象／非対象）、制約／前提、I/O 契約、最小フロー、インターフェースをまとめます。オリジナルのブループリントに従いつつ簡潔さを重視します。
   - **RUNBOOK.md** – lists environment setup, execution steps and verification checks; it emphasises differences between local CPU/GPU models and cheap API usage.
     - JP: **RUNBOOK.md** – 環境構築、実行手順、検証手順を列挙します。ローカル CPU／GPU モデルと低コスト API 利用の違いに重点を置きます。
   - **EVALUATION.md** – defines acceptance criteria, KPIs and test/checklist items.  It draws inspiration from the original evaluation document, which ensures that each recipe declares success and failure conditions【134465174200610†L10-L22】.
     - JP: **EVALUATION.md** – 受け入れ基準、KPI、テスト／チェックリスト項目を定義します。各レシピが成功と失敗の条件を宣言するオリジナルの評価ドキュメントに触発されています【134465174200610†L10-L22】。
   - **GUARDRAILS.md** – outlines behaviour principles (e.g., safe model usage, summarising long inputs before ingestion) and minimal context ingestion rules, aligning with the original guardrails and BirdEye guidelines【172882294315981†L18-L32】.
     - JP: **GUARDRAILS.md** – モデルの安全な利用、長文の事前要約といった行動原則と最小限のコンテキスト取り込みルールを示し、オリジナルのガードレールと BirdEye ガイドラインに沿います【172882294315981†L18-L32】。
   - **SPEC.md & DESIGN.md** – summarise the specification (inputs, outputs, states, error handling) and the high‑level directory/architecture design.  They summarise the primary I/O of each recipe, the step states and error handling, as described in the original spec【134465174200610†L10-L22】.
     - JP: **SPEC.md と DESIGN.md** – 仕様（入力、出力、状態、エラーハンドリング）および高レベルなディレクトリ／アーキテクチャ設計をまとめます。各レシピの主要な I/O、ステップ状態、エラーハンドリングを原典どおりに要約します【134465174200610†L10-L22】。
3. **Recipes:**  A set of YAML files define tasks using a common schema (`name`, `inputs`, `steps`, `budget`, `outputs`).  Key recipes include:
_JP: 3. **レシピ:** 共通スキーマ（`name`、`inputs`、`steps`、`budget`、`outputs`）でタスクを定義する YAML ファイル群。主なレシピは以下のとおりです。_
   - **summarize.yaml** – summarises a text into key bullets; ensures output fits within the JSON schema (e.g., five bullets) and budget.
     - JP: **summarize.yaml** – テキストを主要な箇条書きに要約します。JSON スキーマ（例: 5 つの箇条書き）と予算に収まることを保証します。
   - **req_to_srs_roi.yaml** – converts a requirement document into a structured SRS with ROI data, computing `roi_score` for each story and capturing acceptance criteria.
     - JP: **req_to_srs_roi.yaml** – 要件ドキュメントを ROI データ付きの構造化 SRS に変換し、各ストーリーに `roi_score` を算出し、受け入れ基準を収集します。
   - **srs_scope_plan.yaml** – selects high‑ROI stories under a budget (`ROI_BUDGET`) and produces a scope plan.
     - JP: **srs_scope_plan.yaml** – `ROI_BUDGET` 以内で高 ROI のストーリーを選別し、スコープ計画を生成します。
   - **srs_to_design_roi.yaml** – takes the SRS and scope plan and generates a minimal design, mapping stories to modules and interfaces while referencing story IDs.
     - JP: **srs_to_design_roi.yaml** – SRS とスコープ計画を受け取り、ストーリー ID を参照しながらストーリーをモジュールとインターフェースにマッピングする最小限の設計を生成します。
   - **birdseye_summary.yaml** – runs the BirdEye‑Lite tool to produce a mermaid diagram of the repository’s top dependencies.
     - JP: **birdseye_summary.yaml** – BirdEye-Lite ツールを実行し、リポジトリの主要な依存関係を示す Mermaid 図を生成します。
4. **Tools:**  Helper scripts power the recipes and checks:
_JP: 4. **ツール:** レシピとチェックを支えるヘルパースクリプト。_
   - A recipe runner (e.g., in TypeScript or Python) loads YAML, composes prompts, calls an LLM client (OpenAI API or Ollama), validates JSON against a schema and writes results to disk.
     - JP: レシピランナー（TypeScript または Python など）は YAML を読み込み、プロンプトを組み立て、LLM クライアント（OpenAI API や Ollama）を呼び出し、JSON をスキーマに照らして検証し、結果をディスクへ書き込みます。
   - A BirdEye‑Lite extractor scans code for import/use edges, ranks them and outputs a mermaid diagram limited to a fixed number of nodes/edges, reducing context consumption.
     - JP: BirdEye-Lite 抽出器はコードをスキャンして import／利用エッジを特定し、重要度順にランク付けした Mermaid 図を固定数のノード／エッジ内で出力し、コンテキスト消費を抑えます。
   - A LOC budget checker (optional) counts lines in specified directories and warns when the suggested design capacity is exceeded.
     - JP: LOC 予算チェッカー（任意）は指定ディレクトリの行数をカウントし、推奨される設計キャパシティ超過時に警告します。
   - An ROI planner calculates ROI scores and selects stories under a given effort budget.
     - JP: ROI プランナーは ROI スコアを計算し、指定された労力予算内でストーリーを選定します。
5. **Configuration:**  Profiles for different models (e.g., CPU, 7 B, cheap API) and budgets reside in `config/`.  Budgets define `max_input` and `max_output` tokens per recipe; profiles specify base URLs and model names.
_JP: 5. **設定:** 異なるモデル（CPU、7B、低コスト API）と予算向けのプロファイルを `config/` に配置します。予算はレシピごとの `max_input` と `max_output` トークン数を定義し、プロファイルはベース URL とモデル名を指定します。_

## Functional Requirements
_JP: 機能要件_

1. **Simplified template management:**  Users must be able to copy the provided markdown templates, fill them out for their project and commit them.  CI or local scripts should verify the presence of mandatory sections (e.g., problem statement, scope, constraints).
_JP: 1. **簡素化されたテンプレート管理:** 利用者は提供された Markdown テンプレートをコピーし、プロジェクト向けに記入してコミットできる必要があります。CI またはローカルスクリプトは問題記述、スコープ、制約といった必須セクションの存在を検証するべきです。_
2. **Minimal pipeline execution:**  The CLI runner must execute recipes in a single turn wherever possible, reading input files (text or JSON), sending prompts to the chosen LLM and producing JSON output.  It should respect the `budget` section for token limits and apply guardrails for safe input construction.
_JP: 2. **最小限のパイプライン実行:** CLI ランナーは可能な限り単発でレシピを実行し、入力ファイル（テキストまたは JSON）を読み込み、選択した LLM にプロンプトを送信し、JSON 出力を生成します。`budget` セクションで定義されたトークン上限を尊重し、安全な入力構築のためのガードレールを適用します。_
3. **Context budgeting:**  For each recipe the runner should cap the concatenated system prompt, instructions, references and user input according to the configured `max_input`.  The default budgets (~500 tokens for CPU and ~1 000 tokens for 7 B) should be overridable via configuration.
_JP: 3. **コンテキスト予算管理:** 各レシピについて、ランナーはシステムプロンプト、指示、参照、ユーザー入力を連結したものが設定された `max_input` を超えないよう制限します。デフォルト予算（CPU は約 500 トークン、7B は約 1,000 トークン）は設定で上書き可能です。_
4. **ROI prioritisation:**  The requirement‑to‑SRS recipe must attach `value`, `effort`, `risk` and `confidence` to each story and compute an `roi_score`; the subsequent scope planning recipe must select stories whose cumulative effort does not exceed `ROI_BUDGET`.
_JP: 4. **ROI の優先順位付け:** 要件から SRS へのレシピでは、各ストーリーに `value`、`effort`、`risk`、`confidence` を付与し、`roi_score` を算出します。続くスコープ計画レシピは、累積労力が `ROI_BUDGET` を超えないストーリーを選択する必要があります。_
5. **BirdEye‑Lite extraction:**  A tool must read code from the target repository, identify import or usage relationships and produce a mermaid graph summarising the top dependencies.  The graph should be small enough (e.g., ≤30 nodes and ≤60 edges) to be embedded in prompts without breaking token budgets, and must align with the minimal context intake guidelines【172882294315981†L18-L32】.
_JP: 5. **BirdEye-Lite 抽出:** ツールは対象リポジトリのコードを読み込み、import または利用関係を特定し、主要な依存関係をまとめた Mermaid グラフを生成しなければなりません。グラフは小さく（例: ノード ≤30、エッジ ≤60）保ち、トークン予算を超えず、最小限のコンテキスト取り込みガイドラインに従う必要があります【172882294315981†L18-L32】。_
6. **Guardrails and evaluation:**  The GUARDRAILS.md document must list behavioural guidelines for interacting with LLMs (e.g., summarising long documents before ingestion, not exceeding model capabilities).  The evaluation checklist must specify schema validation, acceptance criteria and ROI compliance tests so outputs can be automatically verified.
_JP: 6. **ガードレールと評価:** GUARDRAILS.md ドキュメントには、長文を取り込む前に要約する、モデルの能力を超えないといった LLM との対話ガイドラインを列挙する必要があります。評価チェックリストはスキーマ検証、受け入れ基準、ROI コンプライアンスのテストを指定し、出力が自動検証できるようにします。_

## Non‑Functional Requirements
_JP: 非機能要件_

- **Portability:**  The downsized kit must avoid heavy dependencies and should run on common platforms (Node.js or Python) without requiring GPUs.  Scripts should be platform‑agnostic and support both local LLM back‑ends and remote API calls.
  - JP: **移植性:** ダウンサイザードキットは重い依存関係を避け、GPU を必要とせずに一般的なプラットフォーム（Node.js または Python）で動作する必要があります。スクリプトはプラットフォーム非依存であり、ローカル LLM バックエンドとリモート API 呼び出しの両方をサポートするべきです。
- **Extensibility:**  Although simplified, the design must allow the addition of new recipes, budgets and templates.  The directory structure and configuration files must be generic enough to support custom tasks.
  - JP: **拡張性:** 簡素化されていても、新しいレシピ、予算、テンプレートを追加できる設計とする必要があります。ディレクトリ構成と設定ファイルはカスタムタスクをサポートできるよう汎用的でなければなりません。
- **Maintainability:**  Using markdown and YAML ensures that documentation and recipes can be easily reviewed and version‑controlled.  All changes must be traceable through a changelog.
  - JP: **保守性:** Markdown と YAML を用いることでドキュメントとレシピはレビューしやすく、バージョン管理も容易になります。すべての変更は Changelog を通じて追跡可能でなければなりません。
- **Usability:**  Provide clear instructions in `README.md`, sample inputs/outputs in `examples/` and sensible defaults in `config/` so users can start quickly.
  - JP: **ユーザビリティ:** `README.md` に明快な手順、`examples/` にサンプル入出力、`config/` に妥当なデフォルトを用意し、利用者がすぐに開始できるようにします。

## Proposed File Structure
_JP: 提案するファイル構成_

```
downsized-cookbook/
├── docs/
│   ├── BLUEPRINT.md            # problem, scope, constraints, I/O contract, flow, interfaces
│   ├── RUNBOOK.md              # environment setup, execution steps, verification
│   ├── EVALUATION.md           # acceptance criteria, KPIs, test checklist
│   ├── GUARDRAILS.md           # behavioural principles and minimal context rules
│   ├── SPEC.md                 # summarised specification (I/O, states, error handling)【134465174200610†L10-L22】
│   ├── DESIGN.md               # directory overview and architecture flow【706646524446654†L10-L18】
│   └── ... (additional lightweight docs)
├── recipes/
│   ├── summarize.yaml
│   ├── req_to_srs_roi.yaml
│   ├── srs_scope_plan.yaml
│   ├── srs_to_design_roi.yaml
│   └── birdseye_summary.yaml
├── tools/
│   ├── runner.{ts,py}          # execute recipes with budgets, ROI, schema validation
│   ├── birdseye_lite.py        # extract and rank dependencies, output mermaid
│   ├── loc_budget_check.py     # optional code‑line budget warnings
│   └── roi_planner.py          # compute ROI and select stories
├── examples/
│   ├── requirements.md         # sample requirement
│   ├── input.txt               # sample text for summarisation
│   └── ... (other examples)
├── config/
│   ├── profiles.yaml           # model profiles (local CPU/7 B, cheap API)
│   ├── budget.yaml             # suggested token budgets per profile
│   └── ... (ROI budgets, etc.)
└── README.md                   # quick start and usage instructions
```

```
downsized-cookbook/
├── docs/
│   ├── BLUEPRINT.md            # 課題、スコープ、制約、I/O 契約、フロー、インターフェース
│   ├── RUNBOOK.md              # 環境セットアップ、実行手順、検証
│   ├── EVALUATION.md           # 受け入れ基準、KPI、テストチェックリスト
│   ├── GUARDRAILS.md           # 行動原則と最小限のコンテキストルール
│   ├── SPEC.md                 # 仕様の要約（I/O、状態、エラーハンドリング）【134465174200610†L10-L22】
│   ├── DESIGN.md               # ディレクトリ概要とアーキテクチャフロー【706646524446654†L10-L18】
│   └── ... (追加の軽量ドキュメント)
├── recipes/
│   ├── summarize.yaml
│   ├── req_to_srs_roi.yaml
│   ├── srs_scope_plan.yaml
│   ├── srs_to_design_roi.yaml
│   └── birdseye_summary.yaml
├── tools/
│   ├── runner.{ts,py}          # 予算、ROI、スキーマ検証付きでレシピを実行
│   ├── birdseye_lite.py        # 依存関係を抽出・ランク付けし、Mermaid を出力
│   ├── loc_budget_check.py     # 任意のコード行数予算警告
│   └── roi_planner.py          # ROI を計算しストーリーを選定
├── examples/
│   ├── requirements.md         # 要件サンプル
│   ├── input.txt               # 要約用テキストサンプル
│   └── ... (その他のサンプル)
├── config/
│   ├── profiles.yaml           # モデルプロファイル（ローカル CPU／7B、低コスト API）
│   ├── budget.yaml             # プロファイルごとの推奨トークン予算
│   └── ... (ROI 予算など)
└── README.md                   # クイックスタートと使用方法
```

## Implementation Notes
_JP: 実装メモ_

- **Token budgets are advisory:**  The downsized kit proposes default budgets (e.g., 500 input tokens for CPU models, 1 000 for 7 B) but does not strictly enforce them.  Warnings should alert users when they exceed recommended sizes.
  - JP: **トークン予算は推奨値:** ダウンサイザードキットはデフォルト予算（例: CPU モデル向け入力 500 トークン、7B 向け 1,000 トークン）を提案しますが、厳密な強制は行いません。推奨値を超える場合に警告を表示するべきです。
- **JSON output enforcement:**  Recipes must set `response_format` or similar options to ensure that LLM responses are valid JSON.  Schema validation should run after each call.
  - JP: **JSON 出力の強制:** レシピは `response_format` などのオプションを設定し、LLM 応答が有効な JSON となるようにします。各呼び出し後にスキーマ検証を実施します。
- **Environment configuration:**  Users should be able to switch between local and remote models by editing `config/profiles.yaml` without changing recipes.  Credentials (e.g., API keys) must be stored outside of the repository.
  - JP: **環境設定:** 利用者は `config/profiles.yaml` を編集するだけでローカル／リモートモデルを切り替えられるべきです。認証情報（API キーなど）はリポジトリ外で管理します。
- **ROI budgets via environment variables:**  The ROI planning recipes should read an environment variable (e.g., `DOWNSIZED_ROI_BUDGET`) to cap total effort.  A default value can be provided in the docs.
  - JP: **環境変数による ROI 予算:** ROI 計画レシピは `DOWNSIZED_ROI_BUDGET` などの環境変数を読み込み、総労力を制限します。ドキュメントにはデフォルト値を記載できます。
- **Mermaid diagrams in BirdEye‑Lite:**  The tool should generate diagrams using simple node labels (module or file names) and collapse deeply nested paths.  Edges should be ranked by importance (e.g., frequency or centrality) to stay within the token budget.
  - JP: **BirdEye-Lite の Mermaid 図:** ツールはシンプルなノードラベル（モジュール名やファイル名）を使用し、深いパスを折りたたみます。エッジは重要度（頻度や中心性など）でランク付けし、トークン予算内に収めます。

## Limitations
_JP: 制限事項_

- This kit does **not** reproduce all governance and CI features of the full Workflow Cookbook; it omits large BirdEye capsules, ADR management, detailed security processes and extensive checklists.  Users who need those features must refer back to the full repository.
  - JP: このキットはフル版 Workflow Cookbook のすべてのガバナンスと CI 機能を再現するものではありません。大型の BirdEye カプセル、ADR 管理、詳細なセキュリティプロセス、広範なチェックリストは含まれません。これらが必要な場合はフルリポジトリを参照してください。
- The downsized recipes assume that tasks can be handled in a single or very few turns.  Complex tasks requiring long conversations or large contexts may need manual intervention or splitting into multiple recipes.
  - JP: ダウンサイザードレシピは単発またはごく少数ターンで扱えるタスクを前提とします。長い対話や巨大なコンテキストを必要とする複雑なタスクは、手動介入や複数レシピへの分割が必要となる場合があります。
- The design capacity suggestion (≈50 k lines of code) is a soft limit intended to highlight when tasks may become unmanageable; exceeding it will not block execution but may require additional oversight.
  - JP: 約 50k 行という設計キャパシティは、タスクが手に負えなくなる兆候を示すソフトリミットです。超過しても実行はブロックされませんが、追加の監督が求められる可能性があります。

## Glossary
_JP: 用語集_

- **Blueprint** – A single‑page document that captures a problem statement, scope, constraints, I/O contract, minimal flow and interface definitions.  It forms the starting point for all tasks.
  - JP: **Blueprint** – 課題記述、スコープ、制約、I/O 契約、最小フロー、インターフェース定義を一枚にまとめたドキュメント。すべてのタスクの出発点となります。
- **Runbook** – A procedural document describing how to set up the environment and execute a workflow, including verification steps.
  - JP: **Runbook** – 環境のセットアップ方法とワークフロー実行手順、検証ステップを説明する手順書。
- **Guardrails** – Behavioural guidelines and minimal context ingestion rules that protect against exceeding model limits and ensure safe operation.
  - JP: **Guardrails** – モデルの制限を超えない、長文は取り込み前に要約するなど、安全な運用を確保するための行動ガイドラインと最小限のコンテキスト取り込みルール。
- **BirdEye‑Lite** – A simplified dependency graph of the codebase that lists only the most important nodes and edges, designed to fit within small context windows.
  - JP: **BirdEye-Lite** – コードベースの最重要ノードとエッジのみを列挙し、小さなコンテキストウィンドウに収まるよう設計された簡易依存グラフ。
- **ROI (Return on Investment)** – A computed metric combining value, effort, risk and confidence to prioritise stories or features under limited resource budgets.
  - JP: **ROI (Return on Investment)** – 限られたリソース予算の下でストーリーや機能に優先順位を付けるため、価値、労力、リスク、確信度を組み合わせて算出する指標。
