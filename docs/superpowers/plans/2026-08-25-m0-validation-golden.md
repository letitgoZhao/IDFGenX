# M0 Validator and Golden Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现 V0–V6 独立 Validator，并冻结 20 个全部通过设计日仿真的 Compiler Golden。

**Architecture:** `idfgenx.validation` 只读取 `CompilationArtifact` 与 canonical epJSON，以独立几何和引用检查输出冻结的 `ValidationReport`。仿真适配器在独占目录调用 v23.1 `energyplus.exe -D`；Golden 目录保存可审阅输入与期望摘要，不提交 IDF。

**Tech Stack:** Python 3.11、标准库 dataclasses/json/subprocess/unittest、Pydantic v2、EnergyPlus v23.1。

**Spec:** `docs/superpowers/specs/2026-08-25-m0-validation-golden-design.md`

## Global Constraints

- Compiler 仅接受 `ResolvedScenarioSpec`；Validator 不调用 Compiler 几何构建函数。
- EnergyPlus 固定 v23.1；每个外部进程有独占目录、超时和结构化错误证据。
- 不实现真实 AirLoopHVAC、PlantLoop、全年天气仿真、M1 数据生成或 API。
- Golden 20/20 必须 V0–V6 通过，V5 不得为 `not_run`，且 Severe/Fatal 均为 0。
- 所有新增生产接口具中文 docstring 和类型标注；代码遵循 RED → GREEN。

---

### Task 1: 验证报告契约与 V0/V4

**Files:**
- Create: `idfgenx/validation/__init__.py`, `idfgenx/validation/models.py`, `idfgenx/validation/artifact.py`
- Modify: `idfgenx/errors.py`
- Test: `tests/unit/validation/test_models.py`, `tests/unit/validation/test_artifact.py`

**Interfaces:**
- Produces `ValidationStatus`, `Finding`, `StageReport`, `ValidationReport`, `validate_artifact_contract(artifact, spec)`.

- [ ] Write tests asserting frozen report serialization, valid hashes, and tampered/missing epJSON or IDF failures.
- [ ] Run focused tests; expect missing-module import failure.
- [ ] Implement frozen report models and V0/V4 artifact hash/path checks with stable findings.
- [ ] Rerun focused tests and commit `feat(validation): add report contract and artifact gates`.

### Task 2: V1/V2 对象与引用检查

**Files:**
- Create: `idfgenx/validation/objects.py`, `idfgenx/validation/references.py`
- Test: `tests/unit/validation/test_objects.py`, `tests/unit/validation/test_references.py`

**Interfaces:**
- Consumes canonical epJSON document.
- Produces `validate_objects(document)` and `validate_references(document)` returning `StageReport`.

- [ ] Write failing tests for unsupported object, wrong Version, dangling Zone/Construction/Schedule/host-surface/equipment references.
- [ ] Run focused tests; expect imports to fail.
- [ ] Implement explicit v23.1 object allowlist and closed-reference traversal for all Compiler-created object types.
- [ ] Rerun focused tests and commit `feat(validation): validate objects and references`.

### Task 3: V3/V6 独立几何与常识检查

**Files:**
- Create: `idfgenx/validation/geometry.py`, `idfgenx/validation/sanity.py`
- Test: `tests/unit/validation/test_geometry.py`, `tests/unit/validation/test_sanity.py`

**Interfaces:**
- Consumes epJSON document and `ResolvedScenarioSpec`.
- Produces `validate_geometry(document)` and `validate_sanity(document, spec)`.

- [ ] Write failing tests for degenerate/reversed host surfaces, window outside host, missing reciprocal Surface pair, incorrect zone count/area/volume/WWR.
- [ ] Run focused tests; expect imports to fail.
- [ ] Implement standalone vector math, host-plane containment, reciprocal adjacency, and Spec-derived summaries.
- [ ] Rerun focused tests and commit `feat(validation): add geometry and sanity gates`.

### Task 4: V5 仿真与总编排

**Files:**
- Create: `idfgenx/validation/simulation.py`, `idfgenx/validation/service.py`
- Modify: `idfgenx/compiler/toolchain.py`, `idfgenx/compiler/compile.py`
- Test: `tests/unit/validation/test_simulation.py`, `tests/unit/validation/test_service.py`, `tests/integration/test_validation_simulation.py`

**Interfaces:**
- Produces `run_design_day_simulation(artifact, toolchain, work_dir)` and `validate_artifact(artifact, spec, toolchain, work_dir, run_simulation=True)`.

- [ ] Write failing tests for no-run status, `.err` Severe/Fatal parsing, aggregation stop semantics, and a real single-zone design-day simulation.
- [ ] Run focused tests; expect missing interfaces.
- [ ] Extend toolchain with `energyplus.exe`, implement timeout/error capture and V0–V6 ordered aggregation.
- [ ] Rerun focused and real integration tests; commit `feat(validation): run v231 design-day quality gates`.

### Task 5: 20 个 Golden 与任务闭环

**Files:**
- Create: `tests/golden/compiler/<20 case directories>/spec.json`, `expected.json`, `tests/integration/test_compiler_goldens.py`
- Modify: `docs/notes/idfgenx/tasks/IDFGX-M0-013-014-Validation-Golden.md`, `docs/notes/idfgenx/STATUS.md`, `docs/notes/idfgenx/MASTER_PLAN.md`
- Create: `docs/notes/idfgenx/reports/2026-08-25-IDFGX-M0-013-014-Validation-Golden.md`

**Interfaces:**
- Consumes Golden directories; compiles and validates every case.
- Produces 20/20 V0–V6 evidence without storing generated IDF.

- [ ] Write discovery test asserting exactly 20 fixtures, 10 single and 10 perimeter-core, and requiring every stage to pass.
- [ ] Run it; expect absent fixture failure.
- [ ] Add human-readable `spec.json`/`expected.json` fixtures; compute and review expected epJSON SHA/geometry summary once.
- [ ] Run full Golden suite, then full project suite, compileall, lock and diff checks.
- [ ] Write report/status updates and commit `feat(validation): freeze twenty validated compiler goldens`.
