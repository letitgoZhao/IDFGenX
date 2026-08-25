---
task_id: IDFGX-M0-016
title: Compiler round-trip、metamorphic 与 mutation 稳定性测试
module: M0
status: done
owner: Codex
created: 2026-08-25
updated: 2026-08-25
depends_on:
  - IDFGX-M0-013
  - IDFGX-M0-015
related_decisions:
  - ADR-0001
expected_report: docs/notes/idfgenx/reports/2026-08-25-IDFGX-M0-016-Stability.md
---

# IDFGX-M0-016：Compiler 稳定性测试

## 目标

以真实 EnergyPlus v23.1 验证 canonical epJSON→IDF→epJSON 语义
round-trip、支持域内的 metamorphic 不变量和受控工件破坏的 V 阶段失败。

## 非目标

- 不扩展 Compiler 支持域，不实现 AirLoopHVAC、PlantLoop 或设备拓扑。
- 不生成训练数据、Prompt 或 Direct-IDF 数据集。
- 不把 IDF 文件或哈希加入生产 LoRA 记录。

## 影响文件

| 文件 | 变更 |
| --- | --- |
| `tests/integration/test_compiler_stability.py` | 新增 round-trip、metamorphic、mutation 集成测试 |
| `docs/notes/idfgenx/decisions/ADR-0001-spec-lora-artifact-isolation.md` | 冻结训练与工件隔离边界 |
| `docs/notes/idfgenx/decisions/ADR-0001-spec-lora-artifact-isolation.md` | 作为可追踪训练边界的唯一权威来源 |

## 验收命令

`uv run python -m unittest tests.integration.test_compiler_stability -v`  
`uv run python -m unittest discover -v`  
`uv run python -m compileall -q idfgenx tests`  
`uv lock --check`  
`git diff --check`

## 执行清单

- [x] 写出并验证 round-trip、metamorphic、mutation 的失败测试。
- [x] 用最小测试辅助实现使测试通过；生产代码未改动。
- [x] 以 single 与 perimeter_core 两种布局运行真实 V0–V6。
- [x] 更新 ADR、状态、报告和提交记录；未版本化 M1 本地笔记不作为交付文件。

## 完成标准

- [x] ADR-0001 已接受且明确禁止生产 Spec-LoRA 绑定 IDF 工件。
- [x] round-trip 比较规范化 epJSON 语义并通过 V0–V6。
- [x] metamorphic 覆盖命名无关性、WWR 单调性和楼层扩展关系。
- [x] mutation 覆盖工件哈希和几何宿主边界的明确失败码。
- [x] 全量验收命令通过且未提交运行时产物。
