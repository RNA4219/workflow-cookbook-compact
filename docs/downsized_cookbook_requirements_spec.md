# Downsized Workflow Cookbook: Requirements & Specification

## Purpose & Goals

- **Simplify the original Workflow Cookbook for local execution:** The downsized version targets local CPUs (1–3 B models) and modest GPUs (≈7 B) or inexpensive API endpoints.  It provides a lean set of workflows for summarisation, requirements‐to‐SRS conversion and SRS‐to‐design translation, ensuring that tasks can run within limited context windows and hardware budgets.
- **Preserve core governance and guardrails:**  While the large cookbook supports extensive documents and automated checks, this version retains the essential templates—Blueprint, Runbook, Evaluation, Guardrails and Design—so that users still define problems, scopes, constraints, flows and acceptance criteria before implementation.
- **Use ROI to focus effort:**  The new pipelines incorporate a return‑on‑investment (ROI) methodology to break down requirements into epics/stories with value, effort, risk and confidence scores; only high‑ROI stories are implemented within the available budget.

## Scope

- **In scope:**
  - A minimal set of markdown templates (Blueprint, Runbook, Evaluation, Guardrails, Spec and Design) to describe tasks, constraints and acceptance criteria.
  - YAML recipes to drive tasks such as summarising input text, converting requirements to SRS (with ROI), creating a scope plan and translating SRS into design artefacts.  Each recipe defines inputs, outputs and budgets.
  - Lightweight scripts to run recipes through pluggable LLM clients (e.g., OpenAI compatible API or Ollama), enforce optional token budgets and output JSON.
  - A “BirdEye‑Lite” tool that scans a repository for import/use relations and produces a mermaid graph limited to the top N nodes/edges, avoiding large context ingestion【172882294315981†L18-L32】.
  - Optional tools to compute line‑of‑code budgets and warn when input sizes exceed the recommended guidelines.

- **Out of scope:**
  - Managing large BirdEye graphs or the full suite of governance documents (e.g., ADR management, security review, extensive checklist operations).
  - Tasks requiring more than ~1 k tokens of input on a 7 B model or ~500 tokens on CPU‑only models.
  - Automatic enforcement of budgets; the kit warns but does not block tasks that exceed the suggested limits.

## Assumptions & Constraints

- **Limited context budgets:**  The practical input context for local CPU models is about 500 tokens, and for 7 B models about 1 000 tokens; outputs are similarly constrained (≈200–300 tokens).  These limits include the system prompt, task instructions, digests of documents and any code snippets.  Users should summarise or chunk inputs accordingly.
- **Hardware constraints:**  The kit assumes users may lack GPUs or run small quantised models.  Pipelines and recipes must therefore avoid token‑heavy conversations and rely on single‑turn or few‑turn interactions.
- **JSON‑only outputs:**  All LLM outputs must conform to a JSON schema, facilitating downstream processing and validation.
- **ROI budget:**  When breaking requirements into stories, an environment variable (e.g., `ROI_BUDGET`) controls the total effort points to implement.  Stories exceeding this budget are deferred.
- **Design capacity:**  This version does not set a strict daily line limit, but it suggests a design capacity equivalent to ≈50 k lines of code to signal when tasks might need manual intervention.

## Key Components

1. **Directory structure:**  Following the original cookbook’s design, the downsized kit places templates and deliverables under `docs/`, sample inputs/outputs under `examples/` and helper scripts under `tools/`【706646524446654†L10-L18】.  Recipes live in a `recipes/` folder, and configuration in `config/`.  This structure ensures CI or scripts can find mandatory files and simplifies navigation.
2. **Templates:**
   - **BLUEPRINT.md** – captures the problem statement, scope (in/out), constraints/assumptions, I/O contract, minimal flow and interfaces.  It follows the original blueprint template but encourages brevity.
   - **RUNBOOK.md** – lists environment setup, execution steps and verification checks; it emphasises differences between local CPU/GPU models and cheap API usage.
   - **EVALUATION.md** – defines acceptance criteria, KPIs and test/checklist items.  It draws inspiration from the original evaluation document, which ensures that each recipe declares success and failure conditions【134465174200610†L10-L22】.
   - **GUARDRAILS.md** – outlines behaviour principles (e.g., safe model usage, summarising long inputs before ingestion) and minimal context ingestion rules, aligning with the original guardrails and BirdEye guidelines【172882294315981†L18-L32】.
   - **SPEC.md & DESIGN.md** – summarise the specification (inputs, outputs, states, error handling) and the high‑level directory/architecture design.  They summarise the primary I/O of each recipe, the step states and error handling, as described in the original spec【134465174200610†L10-L22】.
3. **Recipes:**  A set of YAML files define tasks using a common schema (`name`, `inputs`, `steps`, `budget`, `outputs`).  Key recipes include:
   - **summarize.yaml** – summarises a text into key bullets; ensures output fits within the JSON schema (e.g., five bullets) and budget.
   - **req_to_srs_roi.yaml** – converts a requirement document into a structured SRS with ROI data, computing `roi_score` for each story and capturing acceptance criteria.
   - **srs_scope_plan.yaml** – selects high‑ROI stories under a budget (`ROI_BUDGET`) and produces a scope plan.
   - **srs_to_design_roi.yaml** – takes the SRS and scope plan and generates a minimal design, mapping stories to modules and interfaces while referencing story IDs.
   - **birdseye_summary.yaml** – runs the BirdEye‑Lite tool to produce a mermaid diagram of the repository’s top dependencies.
4. **Tools:**  Helper scripts power the recipes and checks:
   - A recipe runner (e.g., in TypeScript or Python) loads YAML, composes prompts, calls an LLM client (OpenAI API or Ollama), validates JSON against a schema and writes results to disk.
   - A BirdEye‑Lite extractor scans code for import/use edges, ranks them and outputs a mermaid diagram limited to a fixed number of nodes/edges, reducing context consumption.
   - A LOC budget checker (optional) counts lines in specified directories and warns when the suggested design capacity is exceeded.
   - An ROI planner calculates ROI scores and selects stories under a given effort budget.
5. **Configuration:**  Profiles for different models (e.g., CPU, 7 B, cheap API) and budgets reside in `config/`.  Budgets define `max_input` and `max_output` tokens per recipe; profiles specify base URLs and model names.

## Functional Requirements

1. **Simplified template management:**  Users must be able to copy the provided markdown templates, fill them out for their project and commit them.  CI or local scripts should verify the presence of mandatory sections (e.g., problem statement, scope, constraints).
2. **Minimal pipeline execution:**  The CLI runner must execute recipes in a single turn wherever possible, reading input files (text or JSON), sending prompts to the chosen LLM and producing JSON output.  It should respect the `budget` section for token limits and apply guardrails for safe input construction.
3. **Context budgeting:**  For each recipe the runner should cap the concatenated system prompt, instructions, references and user input according to the configured `max_input`.  The default budgets (~500 tokens for CPU and ~1 000 tokens for 7 B) should be overridable via configuration.
4. **ROI prioritisation:**  The requirement‑to‑SRS recipe must attach `value`, `effort`, `risk` and `confidence` to each story and compute an `roi_score`; the subsequent scope planning recipe must select stories whose cumulative effort does not exceed `ROI_BUDGET`.
5. **BirdEye‑Lite extraction:**  A tool must read code from the target repository, identify import or usage relationships and produce a mermaid graph summarising the top dependencies.  The graph should be small enough (e.g., ≤30 nodes and ≤60 edges) to be embedded in prompts without breaking token budgets, and must align with the minimal context intake guidelines【172882294315981†L18-L32】.
6. **Guardrails and evaluation:**  The GUARDRAILS.md document must list behavioural guidelines for interacting with LLMs (e.g., summarising long documents before ingestion, not exceeding model capabilities).  The evaluation checklist must specify schema validation, acceptance criteria and ROI compliance tests so outputs can be automatically verified.

## Non‑Functional Requirements

- **Portability:**  The downsized kit must avoid heavy dependencies and should run on common platforms (Node.js or Python) without requiring GPUs.  Scripts should be platform‑agnostic and support both local LLM back‑ends and remote API calls.
- **Extensibility:**  Although simplified, the design must allow the addition of new recipes, budgets and templates.  The directory structure and configuration files must be generic enough to support custom tasks.
- **Maintainability:**  Using markdown and YAML ensures that documentation and recipes can be easily reviewed and version‑controlled.  All changes must be traceable through a changelog.
- **Usability:**  Provide clear instructions in `README.md`, sample inputs/outputs in `examples/` and sensible defaults in `config/` so users can start quickly.

## Proposed File Structure

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

## Implementation Notes

- **Token budgets are advisory:**  The downsized kit proposes default budgets (e.g., 500 input tokens for CPU models, 1 000 for 7 B) but does not strictly enforce them.  Warnings should alert users when they exceed recommended sizes.
- **JSON output enforcement:**  Recipes must set `response_format` or similar options to ensure that LLM responses are valid JSON.  Schema validation should run after each call.
- **Environment configuration:**  Users should be able to switch between local and remote models by editing `config/profiles.yaml` without changing recipes.  Credentials (e.g., API keys) must be stored outside of the repository.
- **ROI budgets via environment variables:**  The ROI planning recipes should read an environment variable (e.g., `DOWNSIZED_ROI_BUDGET`) to cap total effort.  A default value can be provided in the docs.
- **Mermaid diagrams in BirdEye‑Lite:**  The tool should generate diagrams using simple node labels (module or file names) and collapse deeply nested paths.  Edges should be ranked by importance (e.g., frequency or centrality) to stay within the token budget.

## Limitations

- This kit does **not** reproduce all governance and CI features of the full Workflow Cookbook; it omits large BirdEye capsules, ADR management, detailed security processes and extensive checklists.  Users who need those features must refer back to the full repository.
- The downsized recipes assume that tasks can be handled in a single or very few turns.  Complex tasks requiring long conversations or large contexts may need manual intervention or splitting into multiple recipes.
- The design capacity suggestion (≈50 k lines of code) is a soft limit intended to highlight when tasks may become unmanageable; exceeding it will not block execution but may require additional oversight.

## Glossary

- **Blueprint** – A single‑page document that captures a problem statement, scope, constraints, I/O contract, minimal flow and interface definitions.  It forms the starting point for all tasks.
- **Runbook** – A procedural document describing how to set up the environment and execute a workflow, including verification steps.
- **Guardrails** – Behavioural guidelines and minimal context ingestion rules that protect against exceeding model limits and ensure safe operation.
- **BirdEye‑Lite** – A simplified dependency graph of the codebase that lists only the most important nodes and edges, designed to fit within small context windows.
- **ROI (Return on Investment)** – A computed metric combining value, effort, risk and confidence to prioritise stories or features under limited resource budgets.
