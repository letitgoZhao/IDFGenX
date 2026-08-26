# M1 Deterministic Sampling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a deterministic, auditable M1 sampler that stratifies discrete scenario fields and uses SciPy LHS or Sobol for continuous fields.

**Architecture:** Keep scenario ranges in the existing scenario catalog and sampling policy in a new versioned config. A focused `sample.py` module loads and hashes policy, generates fixed QMC candidate pools, consumes deterministic discrete strata, applies domain gates, and returns frozen records with provenance.

**Tech Stack:** Python 3.11, Pydantic 2.13.4, NumPy 2.4.6, SciPy 1.17.0, unittest, uv.

**Spec:** `docs/superpowers/specs/2026-08-26-m1-deterministic-sampling-design.md`

## Global Constraints

- EnergyPlus remains fixed at v23.1; this task does not invoke it.
- `ResolvedScenarioSpec` is the only Compiler input and the sampler's engineering output.
- Scenario ranges come only from `scenario_buckets_v0_1.json`.
- C5 is explicit evaluation-only sampling and never enters training batches.
- Public Python APIs and non-obvious business helpers require Chinese Google-style docstrings and full typing.
- No Prompt, dataset release, model, runtime artifact, `.env`, or EnergyPlus installation file is created.

---

### Task 1: Versioned sampling configuration and direct dependencies

**Files:**
- Create: `configs/data/sampling_v0_1.json`
- Create: `idfgenx/data_factory/sample.py`
- Create: `tests/unit/data_factory/test_sample.py`
- Modify: `pyproject.toml`
- Modify: `uv.lock`

**Interfaces:**
- Consumes: `ScenarioCatalog.config_version: str`
- Produces: `SamplingEngine`, `SamplingConfig`, `load_sampling_config(Path)`, `sampling_config_sha256(SamplingConfig)`

- [x] **Step 1: Write failing configuration tests**

```python
class SamplingConfigTests(unittest.TestCase):
    def test_loads_frozen_policy_and_hash_is_stable(self) -> None:
        config = load_sampling_config(Path("configs/data/sampling_v0_1.json"))
        self.assertEqual(config.default_engine, SamplingEngine.LATIN_HYPERCUBE)
        self.assertEqual(config.training_complexity_shares, {"simple": 0.4, "complex": 0.6})
        self.assertEqual(sampling_config_sha256(config), sampling_config_sha256(config))

    def test_rejects_complexity_shares_that_do_not_sum_to_one(self) -> None:
        payload = json.loads(Path("configs/data/sampling_v0_1.json").read_text(encoding="utf-8"))
        payload["training_complexity_shares"] = {"simple": 0.5, "complex": 0.6}
        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / "invalid.json"
            invalid.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ConfigurationError):
                load_sampling_config(invalid)
```

- [x] **Step 2: Run the focused test and verify RED**

Run: `.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_sample.SamplingConfigTests -v`

Expected: import failure because `idfgenx.data_factory.sample` does not exist.

- [x] **Step 3: Add exact dependencies and lock them**

Add to `pyproject.toml`:

```toml
"numpy==2.4.6",
"scipy==1.17.0",
```

Run: `C:\Users\LEGION\.local\bin\uv.exe lock && C:\Users\LEGION\.local\bin\uv.exe sync --locked`

- [x] **Step 4: Add the policy JSON and minimal immutable config models**

Implement the JSON fields exactly as specified in the design. In `sample.py`, define frozen Pydantic models, validate field sets/shares/resource limits, wrap I/O or Pydantic failures in `ConfigurationError`, and hash canonical JSON:

```python
def sampling_config_sha256(config: SamplingConfig) -> str:
    payload = json.dumps(
        config.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(payload.encode("utf-8")).hexdigest()
```

- [x] **Step 5: Run tests and verify GREEN**

Run: `.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_sample.SamplingConfigTests -v`

Expected: both configuration tests pass.

- [x] **Step 6: Commit the configuration slice**

```text
git add pyproject.toml uv.lock configs/data/sampling_v0_1.json idfgenx/data_factory/sample.py tests/unit/data_factory/test_sample.py
git commit -m "feat(data): add versioned sampling policy"
```

### Task 2: Deterministic single-bucket LHS and Sobol sampling

**Files:**
- Modify: `idfgenx/data_factory/sample.py`
- Modify: `tests/unit/data_factory/test_sample.py`

**Interfaces:**
- Consumes: `ScenarioCatalog`, `SamplingConfig`, `ScenarioBucket`, SciPy QMC engines
- Produces: `SamplingDistribution`, `SamplingRecord`, `sample_bucket(...) -> tuple[SamplingRecord, ...]`

- [x] **Step 1: Write failing behavior tests**

Add tests whose expected values are independently checked:

```python
def test_same_seed_reproduces_lhs_records_and_different_seed_changes_fields(self) -> None:
    first = sample_bucket(self.catalog, self.config, "S1", 12, seed=42)
    repeated = sample_bucket(self.catalog, self.config, "S1", 12, seed=42)
    changed = sample_bucket(self.catalog, self.config, "S1", 12, seed=43)
    self.assertEqual(first, repeated)
    self.assertNotEqual([row.spec.length_m for row in first], [row.spec.length_m for row in changed])

def test_sobol_records_pass_bucket_and_domain_gates(self) -> None:
    records = sample_bucket(
        self.catalog, self.config, "C2", 16, seed=7, engine=SamplingEngine.SOBOL
    )
    self.assertEqual(len(records), 16)
    for record in records:
        validate_bucket_assignment(record.spec, self.catalog.bucket("C2"))
        self.assertGreaterEqual(record.spec.length_m / record.spec.width_m, 0.4)
        self.assertLessEqual(record.spec.length_m / record.spec.width_m, 2.5)

def test_sampling_does_not_advance_numpy_global_rng(self) -> None:
    np.random.seed(123)
    expected = np.random.random()
    np.random.seed(123)
    sample_bucket(self.catalog, self.config, "S1", 4, seed=9)
    self.assertEqual(np.random.random(), expected)
```

Also test positive count/seed validation, discrete balance on a controlled no-rejection bucket, stable names, metadata hashes, and candidate exhaustion context.
Add a catalog-version mismatch test here because `sample_bucket` is the first interface that consumes both versioned configurations.

- [x] **Step 2: Run the focused class and verify RED**

Run: `.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_sample.BucketSamplingTests -v`

Expected: failure because `sample_bucket` and record models are missing.

- [x] **Step 3: Implement fixed candidate pools and discrete strata**

Implement private typed helpers for request validation, candidate count, QMC generation/scaling, discrete Cartesian products, stable rejection classification, `ResolvedScenarioSpec` construction and `SamplingRecord` creation. Use `qmc.LatinHypercube.random(n)` for LHS and `qmc.Sobol.random_base2(m)` for Sobol. Reject invalid candidates without changing dimensions or repairing values.

- [x] **Step 4: Run focused tests and verify GREEN**

Run: `.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_sample.BucketSamplingTests -v`

Expected: all single-bucket tests pass with no warnings.

- [x] **Step 5: Refactor while green**

Keep `sample_bucket` orchestration short; extract candidate generation, discrete strata and rejection gates only where each helper has a single business responsibility. Re-run the focused class after refactoring.

- [x] **Step 6: Commit the bucket sampler**

```text
git add idfgenx/data_factory/sample.py tests/unit/data_factory/test_sample.py
git commit -m "feat(data): sample scenario buckets with qmc"
```

### Task 3: Training allocation and explicit C5 Hard/OOD sampling

**Files:**
- Modify: `idfgenx/data_factory/sample.py`
- Modify: `tests/unit/data_factory/test_sample.py`

**Interfaces:**
- Consumes: `sample_bucket`, catalog training/evaluation bucket lists, root seed
- Produces: `sample_training_catalog(...) -> tuple[SamplingRecord, ...]`

- [ ] **Step 1: Write failing allocation and isolation tests**

```python
def test_training_catalog_is_exactly_forty_sixty_and_excludes_c5(self) -> None:
    records = sample_training_catalog(self.catalog, self.config, 100, seed=2026)
    simple = sum(row.bucket_id.startswith("S") for row in records)
    complex_ = sum(row.bucket_id.startswith("C") for row in records)
    self.assertEqual((simple, complex_), (40, 60))
    self.assertNotIn("C5", {row.bucket_id for row in records})

def test_explicit_c5_records_are_outside_training_envelope(self) -> None:
    records = sample_bucket(self.catalog, self.config, "C5", 20, seed=99)
    self.assertEqual(len(records), 20)
    for row in records:
        values = row.spec
        outside = (
            values.length_m < 8 or values.length_m > 60
            or values.width_m < 8 or values.width_m > 60
            or values.floor_to_floor_height_m < 2.7 or values.floor_to_floor_height_m > 4.5
            or values.window_to_wall_ratio < 0.2 or values.window_to_wall_ratio > 0.6
            or values.heating_setpoint_c < 18 or values.heating_setpoint_c > 22
            or values.cooling_setpoint_c < 24 or values.cooling_setpoint_c > 28
            or values.stories > 6
        )
        self.assertTrue(outside)
```

Also test exact requested count, equal-within-group allocation difference at most one, deterministic child seeds/order, and `count=1` behavior.

- [ ] **Step 2: Run tests and verify RED**

Run: `.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_sample.TrainingSamplingTests -v`

Expected: failure because training allocation and C5 OOD filtering are missing.

- [ ] **Step 3: Implement training allocation and C5 gate**

Derive child seeds using SHA-256 over root seed, bucket ID and engine. Allocate `floor(count * 0.4)` to simple and the remainder to complex, distribute within sorted groups from a seed-derived rotation, call `sample_bucket`, deterministically merge, and reindex records. Compute the C5 training envelope from training buckets and reject C5 candidates wholly inside it.

- [ ] **Step 4: Run tests and verify GREEN**

Run: `.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_sample.TrainingSamplingTests -v`

Expected: all training/C5 tests pass.

- [ ] **Step 5: Run the entire sampler test module**

Run: `.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_sample -v`

Expected: all M1-005 tests pass with no errors or warnings.

- [ ] **Step 6: Commit the training/C5 slice**

```text
git add idfgenx/data_factory/sample.py tests/unit/data_factory/test_sample.py
git commit -m "feat(data): allocate training and hard ood samples"
```

### Task 4: Repository closeout and verification evidence

**Files:**
- Modify: `docs/notes/idfgenx/tasks/IDFGX-M1-005-确定性采样.md`
- Create: `docs/notes/idfgenx/reports/2026-08-26-IDFGX-M1-005-Deterministic-Sampling.md`
- Modify: `docs/notes/idfgenx/MASTER_PLAN.md`
- Modify: `docs/notes/idfgenx/STATUS.md`

**Interfaces:**
- Consumes: completed code, tests, dependency lock and Git diff
- Produces: verified task closure and next-task status

- [ ] **Step 1: Run fresh full verification**

```text
.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_sample -v
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m compileall -q idfgenx tests
C:\Users\LEGION\.local\bin\uv.exe lock --check
git diff --check
```

Expected: every command exits 0; record exact test counts and elapsed time.

- [ ] **Step 2: Audit requirements and generated files**

Review the design section by section, inspect `git diff --stat`, `git diff`, and `git status --short`, verify only intended files changed, and confirm no `.env`, cache, dataset, model, EnergyPlus installation or runtime artifact is staged.

- [ ] **Step 3: Write report and update status**

Report actual outputs, incomplete items, risks, follow-up and commits. Mark M1-005 `done`, update `MASTER_PLAN.md`, remove stale Ready entries from `STATUS.md`, and identify M1-007 as the next Prompt task.

- [ ] **Step 4: Re-run documentation-sensitive checks**

Run: `git diff --check && git status --short`

Expected: diff check exits 0 and status lists only intended task files.

- [ ] **Step 5: Commit closeout**

```text
git add -f docs/notes/idfgenx/tasks/IDFGX-M1-005-确定性采样.md docs/notes/idfgenx/reports/2026-08-26-IDFGX-M1-005-Deterministic-Sampling.md docs/notes/idfgenx/MASTER_PLAN.md docs/notes/idfgenx/STATUS.md
git commit -m "docs(m1): close deterministic sampling task"
```
