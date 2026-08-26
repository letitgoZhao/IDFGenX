---
task_id: IDFGX-M0-017
title: Windows 代表样本 Compiler 工件可复现性验证
module: M0
status: done
owner: Codex
created: 2026-08-26
updated: 2026-08-26
depends_on:
  - IDFGX-M0-013
  - IDFGX-M0-015
  - IDFGX-M0-016
related_decisions:
  - ADR-0001
expected_report: docs/notes/idfgenx/reports/2026-08-26-IDFGX-M0-017-Windows-Reproducibility.md
---

# IDFGX-M0-017：Windows 代表样本 Compiler 工件可复现性验证

## 1. 背景

原计划将本任务定义为 Windows/Linux 一致性验证。根据当前明确范围，Linux
验证不执行也不作为验收条件；本任务改为验证 Windows 上相同输入的可重复
Compiler 产物，并为后续任何跨平台工作保留可复用的比较口径。

## 2. 目标

在 Windows EnergyPlus v23.1 上，证明 `single` 和 `perimeter_core` 两类代表
`ResolvedScenarioSpec` 的两次独立编译均通过 V0–V6，且 canonical epJSON、
normalized IDF 的 SHA-256 与 V0–V6 阶段结论完全一致。

## 3. 非目标

- 不安装、配置或验证 Linux、WSL、容器或远程 CI；
- 不宣称 Windows 结果可以证明跨平台一致性；
- 不修改 Compiler 支持域、EnergyPlus 版本、Schema 或训练工件边界。

## 4. 输入与前置条件

- 已完成的 M0-013、M0-015、M0-016；
- Windows Python 3.11.15、EnergyPlus v23.1 和 `C:\\EnergyPlusV23-1-0`；
- 每次运行使用独立临时目录，避免固定输出文件名造成共享状态。

## 5. 影响文件

| 文件/目录 | 预期变更 |
| --- | --- |
| `tests/integration/test_compiler_reproducibility.py` | 新增 Windows 双次独立编译的可复现性门禁 |
| `docs/notes/idfgenx/tasks/IDFGX-M0-017-Windows-Reproducibility.md` | 本任务计划与执行记录 |
| `docs/notes/idfgenx/reports/2026-08-26-IDFGX-M0-017-Windows-Reproducibility.md` | 实际验证证据与允许差异口径 |
| `docs/notes/idfgenx/STATUS.md` | 记录 M0-017 的 Windows 范围完成状态 |
| `docs/notes/idfgenx/MASTER_PLAN.md` | 将 M0-017 的交付物改为 Windows 可复现性报告 |

## 6. 详细执行步骤

- [x] 1. 确认 Windows 工具链与既有 stability 基线。
- [x] 2. 新增 `single` 和 `perimeter_core` 双次独立编译比较测试。
- [x] 3. 运行局部测试，确认 epJSON/IDF 哈希与 V0–V6 阶段结论一致。
- [x] 4. 运行全量 Python 测试、语法编译、lock 与 diff 检查。
- [x] 5. 输出执行报告，更新状态、总计划和任务状态。

## 7. 数据与接口变更

无。新增的测试只读取既有 Compiler 与 Validator 公共接口，不改变产物格式。

## 8. 风险与回滚

| 风险 | 预防/检测 | 回滚方式 |
| --- | --- | --- |
| 临时目录污染结果 | 每次编译使用独立 `TemporaryDirectory` | 删除测试；无需迁移数据 |
| 将 Windows 结论误写为跨平台结论 | 文档明确排除 Linux 和跨平台声明 | 恢复任务/计划文档描述 |

## 9. 验证命令

```text
.\\.venv\\Scripts\\python.exe -m unittest tests.integration.test_compiler_reproducibility -v
.\\.venv\\Scripts\\python.exe -m unittest tests.integration.test_compiler_stability -v
.\\.venv\\Scripts\\python.exe -m unittest discover -v
.\\.venv\\Scripts\\python.exe -m compileall -q idfgenx tests
uv lock --check  # 若 uv 可用；当前 PATH 不包含 uv，记录为环境限制
git diff --check
```

## 10. 完成标准

- [x] `single` 和 `perimeter_core` 均在两次独立 Windows 运行中通过 V0–V6；
- [x] 同一 Spec 的 canonical epJSON 和 normalized IDF SHA-256 完全相同；
- [x] V0–V6 阶段名称与状态完全相同；
- [x] 允许差异明确限为临时工作目录路径，不参与哈希或成功阶段报告；
- [x] 报告、`STATUS.md`、`MASTER_PLAN.md` 已更新，且不含跨平台完成声明。

## 11. 执行记录

- 2026-08-26：Windows 既有稳定性测试 3/3 通过；WSL 2 已启用但无发行版。
  本任务按明确范围排除 Linux，不将该环境状态作为阻塞项。
- 2026-08-26：新增可复现性测试 2/2 通过；全量 `unittest discover` 81/81
  通过，`compileall`、`uv lock --check` 和 `git diff --check` 均通过。

## 12. 结果

- 报告：`docs/notes/idfgenx/reports/2026-08-26-IDFGX-M0-017-Windows-Reproducibility.md`。
- Commit/PR：未创建（未获授权自动提交）。
