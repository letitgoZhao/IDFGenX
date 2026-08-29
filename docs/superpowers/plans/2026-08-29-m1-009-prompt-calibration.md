# M1-009 Prompt Calibration Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 对四个 clean family 和 192 个 robust Prompt 组合执行独立、确定性、可审计的 Draft 反向标定。

**Architecture:** 新增 `idfgenx/data_factory/calibrate.py`，将受限文本提取、Draft 比对和报告生成分成清晰边界。解析器按记录 family/variant 选择语法，使用显式别名与 Decimal；报告只返回结果，不写 release 或 quarantine。

**Tech Stack:** Python 3.11、Pydantic v2、`Decimal`、标准 `re`、`unittest`。

**Spec:** `docs/superpowers/specs/2026-08-29-m1-009-prompt-calibration-design.md`

## Global Constraints

- EnergyPlus 版本固定为 v23.1；标定器不调用 EnergyPlus、Resolver、Compiler 或 LLM。
- `ScenarioSpecDraft` v0.1 是唯一比较目标；只允许 requested 字段出现在 Prompt 中，defaulted 字段出现即失败。
- 仅接受当前四个 clean family 和 M1-008 robust v0.1；不解析任意自由文本。
- 数字使用 `Decimal` 严格比较，不使用宽松相对误差；失败必须 fail-closed 并保留稳定错误码。
- 新增 Python 公共类型/函数必须有类型标注和中文 Google 风格 docstring；模型使用 `extra="forbid"`。
- 不修改 Prompt 渲染、Resolver、Compiler、Schema 和 release 格式；不提交数据、模型、`.env` 或运行产物。

### Task 1: Freeze calibration result contracts and positive/negative test matrix

**Files:**
- Create: `tests/unit/data_factory/test_calibrate.py`
- Create: `idfgenx/data_factory/calibrate.py`

**Interfaces:**
- Consumes: `CleanPromptRecord`、`RobustPromptRecord`、`ScenarioSpecDraft`。
- Produces: `CalibrationErrorCode`、`CalibrationStatus`、`CalibrationFieldResult`、`CalibrationReport`、`calibrate_prompt(record)`。

- [ ] **Step 1: Write the failing contract tests**

Add tests that import the four public types and call `calibrate_prompt` with a clean record. Assert the report has `status == "passed"`, an ordered tuple of field results, and a 64-character summary hash. Add a mutation test replacing one numeric token and assert `numeric_mismatch`; add a defaulted-field disclosure case and assert `default_leakage`.

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\\.venv\\Scripts\\python.exe -m unittest tests.unit.data_factory.test_calibrate -v`

Expected: FAIL because `idfgenx.data_factory.calibrate` and its public contracts do not exist.

- [ ] **Step 3: Implement the immutable result models**

Define:

```python
class CalibrationStatus(StrEnum):
    PASSED = "passed"
    FAILED = "failed"
    CONFIGURATION_ERROR = "configuration_error"

class CalibrationErrorCode(StrEnum):
    MISSING_REQUESTED_FIELD = "missing_requested_field"
    DUPLICATE_FIELD = "duplicate_field"
    UNKNOWN_ENTITY = "unknown_entity"
    ENTITY_MISMATCH = "entity_mismatch"
    UNIT_MISSING = "unit_missing"
    UNIT_MISMATCH = "unit_mismatch"
    NUMERIC_MISMATCH = "numeric_mismatch"
    DEFAULT_LEAKAGE = "default_leakage"
    SYNTAX_UNRECOGNIZED = "syntax_unrecognized"
    CONFIGURATION_ERROR = "configuration_error"

class CalibrationFieldResult(BaseModel):
    field_name: str
    status: Literal["matched", "missing", "unexpected", "mismatched"]
    extracted_value: str | None = None
    expected_value: str | None = None
    unit: str | None = None
    spans: tuple[tuple[int, int], ...] = ()
    error_codes: tuple[CalibrationErrorCode, ...] = ()

class CalibrationReport(BaseModel):
    protocol_version: Literal["0.1"] = "0.1"
    status: CalibrationStatus
    record_variant_id: str
    field_results: tuple[CalibrationFieldResult, ...]
    error_codes: tuple[CalibrationErrorCode, ...]
    summary_sha256: str
```

Use `ConfigDict(extra="forbid", frozen=True)`. Compute `summary_sha256` from sorted-key canonical JSON excluding the hash itself.

- [ ] **Step 4: Run the contract tests to verify they pass**

Run: `.\\.venv\\Scripts\\python.exe -m unittest tests.unit.data_factory.test_calibrate.CalibrationContractTests -v`

Expected: PASS for model shape and deterministic hash tests.

- [ ] **Step 5: Commit**

```text
git add idfgenx/data_factory/calibrate.py tests/unit/data_factory/test_calibrate.py
git commit -m "test(m1): define prompt calibration contracts"
```

### Task 2: Implement family-aware extraction with explicit aliases

**Files:**
- Modify: `idfgenx/data_factory/calibrate.py`
- Modify: `tests/unit/data_factory/test_calibrate.py`

**Interfaces:**
- Consumes: `CleanPromptRecord`/`RobustPromptRecord` metadata and Prompt text.
- Produces: private `_ExtractedField` records and `extract_prompt_fields(record) -> tuple[_ExtractedField, ...]`.

- [ ] **Step 1: Add red tests for every supported family and variant**

Generate clean records with all Draft fields requested and assert extraction returns exactly the ten `DRAFT_FIELD_ORDER` names. Generate all robust plans from `configs/prompts/robust_v0_1.json` and assert each record extracts the same requested field set, including `ft`, `degF`, constraints-first order, alternate terminology, polite filler and context filler. Assert the extracted spans are within the original prompt and ordered by textual position.

- [ ] **Step 2: Run the focused tests and observe failure**

Run: `.\\.venv\\Scripts\\python.exe -m unittest tests.unit.data_factory.test_calibrate.CalibrationExtractionTests -v`

Expected: FAIL because extraction is not implemented.

- [ ] **Step 3: Implement restricted regex grammars and alias tables**

Implement `_ExtractedField(field_name, value: str | None, unit: str | None, entity: str | None, span: tuple[int, int])`, family-specific clause patterns, and explicit aliases for the three `BuildingUse` values, two `ZoneLayout` values, SI/imperial units, standard/alternate terminology, and both noise wrappers. Select patterns from record metadata; reject unsupported protocol versions with `ConfigurationError`. Detect zero or multiple matches per field and retain all spans for later error classification.

- [ ] **Step 4: Run extraction tests to verify they pass**

Run: `.\\.venv\\Scripts\\python.exe -m unittest tests.unit.data_factory.test_calibrate.CalibrationExtractionTests -v`

Expected: PASS for four clean families, all 192 robust records, aliases, spans and noise wrappers.

- [ ] **Step 5: Commit**

```text
git add idfgenx/data_factory/calibrate.py tests/unit/data_factory/test_calibrate.py
git commit -m "feat(m1): extract prompt calibration fields"
```

### Task 3: Implement strict Draft comparison and stable reports

**Files:**
- Modify: `idfgenx/data_factory/calibrate.py`
- Modify: `tests/unit/data_factory/test_calibrate.py`

**Interfaces:**
- Consumes: `_ExtractedField` tuples and record target Draft.
- Produces: `compare_extracted_fields(record, extracted) -> CalibrationReport` and public `calibrate_prompt(record) -> CalibrationReport`.

- [ ] **Step 1: Add red tests for every failure code**

Mutate a known-good prompt to cover missing requested field, duplicate field, unknown entity, entity mismatch, missing unit, wrong unit, numeric drift, default leakage and unrecognized syntax. Assert each report is failed, contains the expected code, preserves field order, and has a stable hash across repeated calls. Add a schema/config version mutation and assert `configuration_error`.

- [ ] **Step 2: Run the negative tests and observe failure**

Run: `.\\.venv\\Scripts\\python.exe -m unittest tests.unit.data_factory.test_calibrate.CalibrationComparisonTests -v`

Expected: FAIL because comparison and error classification are not implemented.

- [ ] **Step 3: Implement Decimal comparison and fail-closed classification**

Parse numeric text with `Decimal`, compare against the Draft requested value rendered in the record’s declared unit, and compare units exactly. Match names exactly after the existing safe-name validation; map entities only through the explicit alias table. For every Draft field, emit one `CalibrationFieldResult`; mark missing requested fields, unexpected defaulted fields, duplicate spans, and mismatches with the fixed error codes. Build `CalibrationReport` and its canonical summary hash deterministically.

- [ ] **Step 4: Run comparison tests to verify they pass**

Run: `.\\.venv\\Scripts\\python.exe -m unittest tests.unit.data_factory.test_calibrate.CalibrationComparisonTests -v`

Expected: PASS for all error codes, strict numeric/unit behavior, version rejection and report determinism.

- [ ] **Step 5: Commit**

```text
git add idfgenx/data_factory/calibrate.py tests/unit/data_factory/test_calibrate.py
git commit -m "feat(m1): validate prompt labels against draft"
```

### Task 4: Integrate documentation, full 192-combination gate, and delivery evidence

**Files:**
- Modify: `tests/unit/data_factory/test_calibrate.py`
- Modify: `docs/notes/idfgenx/tasks/IDFGX-M1-009-反向标定.md`
- Modify: `docs/notes/idfgenx/STATUS.md`
- Modify: `docs/notes/idfgenx/MASTER_PLAN.md`
- Create: `docs/notes/idfgenx/reports/2026-08-29-IDFGX-M1-009-Prompt-Calibration.md`

**Interfaces:**
- Consumes: `calibrate_prompt`, clean/robust renderers and frozen configs.
- Produces: complete M1-009 validation evidence and task status `done`.

- [ ] **Step 1: Add the end-to-end 192-record and documentation-link tests**

Construct every robust plan from the config, render four families, call `calibrate_prompt`, and assert 192 passed reports. Assert task/report paths exist and the report links the exact verification commands.

- [ ] **Step 2: Run the end-to-end test before final documentation**

Run: `.\\.venv\\Scripts\\python.exe -m unittest tests.unit.data_factory.test_calibrate.CalibrationEndToEndTests -v`

Expected: PASS after Tasks 1–3; if any combination fails, fix the parser or renderer contract before changing the assertion.

- [ ] **Step 3: Update task and status evidence**

Mark all task checklist items complete, set task `status: done`, add actual test counts/timings and commit references to the execution report, update `STATUS.md` active/next-task tables, and keep M1-009 marked `done` in `MASTER_PLAN.md` only after all gates pass.

- [ ] **Step 4: Run all required verification commands**

Run:

```text
.\\.venv\\Scripts\\python.exe -m unittest tests.unit.data_factory.test_calibrate -v
.\\.venv\\Scripts\\python.exe -m unittest discover -s tests -v
.\\.venv\\Scripts\\python.exe -m compileall -q idfgenx tests
git diff --check
```

Expected: all calibration tests and the full suite pass; compileall and diff checks exit 0; sensitive-file scan finds no secrets or runtime artifacts.

- [ ] **Step 5: Commit delivery evidence**

```text
git add idfgenx/data_factory/calibrate.py tests/unit/data_factory/test_calibrate.py docs/notes/idfgenx/MASTER_PLAN.md docs/notes/idfgenx/STATUS.md
git add -f "docs/notes/idfgenx/tasks/IDFGX-M1-009-反向标定.md" "docs/notes/idfgenx/reports/2026-08-29-IDFGX-M1-009-Prompt-Calibration.md"
git commit -m "feat(m1): complete prompt reverse calibration"
```

## Self-Review Checklist

- Spec sections map to Tasks 1–4: architecture/data flow (Tasks 1–3), error codes/Decimal/versioning (Tasks 2–3), tests and delivery (Task 4), non-goals (all tasks).
- No placeholder requirements remain; every step names a file, an interface, a command and an expected result.
- Type names and function signatures are consistent across tasks: `calibrate_prompt` consumes records and returns `CalibrationReport`; extraction remains private; comparison is deterministic.
- The plan does not add release writing, arbitrary free-text parsing, LLM judging, or unrelated refactoring.
