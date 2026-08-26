---
task_id: IDFGX-M1-005
title: 实现离散分层与 LHS/Sobol 连续采样
module: M1
status: in_progress
owner: Codex
created: 2026-08-26
updated: 2026-08-26
depends_on:
  - IDFGX-M1-004
  - IDFGX-M0-003
related_decisions: []
expected_report: docs/notes/idfgenx/reports/2026-08-26-IDFGX-M1-005-Deterministic-Sampling.md
---

# IDFGX-M1-005：实现离散分层与 LHS/Sobol 连续采样

## 1. 背景

M1-004 已冻结 S1–S5/C1–C5 场景桶和 Compiler 支持域。数据工厂下一步需要
把这些声明式范围转成可复现的建筑事实，供后续 Prompt、Canonical Sample 和
Golden/Smoke 数据构建复用。

## 2. 目标

交付一个由版本化配置驱动的确定性采样器：类别字段分层覆盖，连续字段可选择
SciPy LHS 或 Sobol，并输出满足场景桶、Schema 和训练/C5 隔离门禁的
`ResolvedScenarioSpec` 及可追溯元数据。

## 3. 非目标

- 不生成 Prompt、ScenarioSpecDraft、epJSON 或 IDF；
- 不调用 Compiler、Validator 或 EnergyPlus；
- 不创建 staging、quarantine 或只读 release；
- 不实现数据去重、切分和训练视图。

## 4. 输入与前置条件

- `IDFGX-M1-004` 的 `scenario_buckets_v0_1.json` 与 `ScenarioCatalog`；
- `IDFGX-M0-003` 的 Resolver 派生规则和 `ResolvedScenarioSpec v0.1`；
- Python 3.11；
- 设计规格：`docs/superpowers/specs/2026-08-26-m1-deterministic-sampling-design.md`；
- 隔离分支基线 86/86 测试通过。

## 5. 影响文件

| 文件/目录 | 预期变更 |
| --- | --- |
| `pyproject.toml`、`uv.lock` | 固定 NumPy/SciPy 直接依赖 |
| `configs/data/sampling_v0_1.json` | 采样策略、配额与资源边界 |
| `idfgenx/data_factory/sample.py` | 配置模型、追溯模型和采样接口 |
| `tests/unit/data_factory/test_sample.py` | 配置、单桶、训练配额、C5 与失败边界测试 |
| `docs/notes/idfgenx/MASTER_PLAN.md` | M1-005 状态 |
| `docs/notes/idfgenx/STATUS.md` | 当前阶段、下一任务和最近完成 |
| `docs/notes/idfgenx/reports/...` | 实际执行证据与风险 |

## 6. 详细执行步骤

- [ ] 1. 先为采样配置载入、校验和哈希写失败测试；
- [ ] 2. 固定 NumPy/SciPy 依赖并实现不可变配置模型；
- [ ] 3. 先为 LHS/Sobol 单桶采样、分层和确定性写失败测试；
- [ ] 4. 实现候选生成、组合门禁、拒绝统计和结构化错误；
- [ ] 5. 先为训练 40%/60% 配额和 C5 隔离写失败测试；
- [ ] 6. 实现训练目录分配、子 seed、合并排序和 C5 OOD 门禁；
- [ ] 7. 运行局部与全量验证，检查 diff、锁文件和敏感/运行时文件；
- [ ] 8. 写执行报告，更新任务、`MASTER_PLAN.md` 和 `STATUS.md`。

## 7. 数据与接口变更

新增采样配置 v0.1，以及 `SamplingConfig`、`SamplingRecord`、
`SamplingEngine`、`SamplingDistribution`、`load_sampling_config()`、
`sampling_config_sha256()`、`sample_bucket()` 和 `sample_training_catalog()`。
不修改 ScenarioSpec 或 Compiler 输入协议。

## 8. 风险与回滚

| 风险 | 预防/检测 | 回滚方式 |
| --- | --- | --- |
| QMC 在拒绝后失去完整低差异性质 | 一次生成固定候选池并记录拒绝率 | 删除 M1-005 新模块与配置 |
| 离散类别因拒绝发生偏斜 | 拒绝也消耗对应组合并测试受控桶均衡 | 恢复组合排列实现 |
| C5 混入训练 | 训练接口只读 training bucket 清单并做直接断言 | 禁用训练目录接口 |
| 新科学计算依赖与 Python 3.11 不兼容 | 固定有 CPython 3.11 Windows wheel 的版本并运行锁检查 | 恢复依赖与锁文件 |
| 候选池不足时返回部分数据 | 整批失败并保留尝试数/拒绝统计 | 调整版本化候选倍率后发布新配置 |

## 9. 验证命令

```text
.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_sample -v
.\.venv\Scripts\python.exe -m unittest discover -v
.\.venv\Scripts\python.exe -m compileall -q idfgenx tests
C:\Users\LEGION\.local\bin\uv.exe lock --check
git diff --check
git status --short
```

## 10. 完成标准

- [ ] 两种 QMC 引擎对相同 seed 可复现且不修改全局 RNG；
- [ ] 离散字段分层，连续字段和所有返回 Spec 通过范围与组合门禁；
- [ ] 训练批次达到精确数量及 40%/60% 配额，并排除 C5；
- [ ] 显式 C5 每条均位于训练包络外；
- [ ] 配置、公共接口、错误和追溯元数据有类型、中文 docstring 与测试；
- [ ] 全量验证、锁检查和 diff 检查通过；
- [ ] 无敏感数据或采样运行产物；
- [ ] 报告、状态和任务记录完成。

## 11. 执行记录

- 2026-08-26：创建隔离分支 `feat/idfgx-m1-005-sampling`；基线 86/86 通过。
- 2026-08-26：官方 PyPI 表明 SciPy 1.17.0 提供 CPython 3.11 Windows x86-64 wheel；设计采用该版本。

## 12. 结果

- 报告：`docs/notes/idfgenx/reports/2026-08-26-IDFGX-M1-005-Deterministic-Sampling.md`
- Commit/PR：完成后填写。
