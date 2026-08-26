---
task_id: IDFGX-M1-004
title: 冻结 S1–S5/C1–C5 场景桶与约束
module: M1
status: done
owner: Codex
created: 2026-08-26
updated: 2026-08-26
depends_on:
  - IDFGX-M0-002
related_decisions: []
expected_report: docs/notes/idfgenx/reports/2026-08-26-IDFGX-M1-004-Scenario-Buckets.md
---

# IDFGX-M1-004：冻结 S1–S5/C1–C5 场景桶与约束

## 目标

交付一个可审阅、可哈希、可由 M1-005 直接消费的场景配置 v0.1；它只覆盖
当前 M0 Compiler 支持域，并明确隔离 Hard/OOD 与 unsupported 请求。

## 范围

- 新增场景桶 JSON、Pydantic 载入/分配校验和单元测试；
- 固定数值范围、布局/用途允许集、复杂度、训练资格和组合规则；
- 不采样、不渲染 Prompt、不创建数据 release。

## 设计依据

`docs/superpowers/specs/2026-08-26-m1-scenario-buckets-design.md`

## 验收命令

```text
.\\.venv\\Scripts\\python.exe -m unittest tests.unit.data_factory.test_scenarios -v
.\\.venv\\Scripts\\python.exe -m unittest discover -v
.\\.venv\\Scripts\\python.exe -m compileall -q idfgenx tests
C:\\Users\\LEGION\\.local\\bin\\uv.exe lock --check
git diff --check
```

## 完成标准

- [x] S1–S5/C1–C5 与数值/组合约束可由版本化配置加载；
- [x] C5 仅评估、unsupported feature 不可进入正向 SFT；
- [x] 校验逻辑与 `ResolvedScenarioSpec v0.1` 能力边界一致；
- [x] 单元测试、全量测试和任务报告具备实际证据；
- [x] `STATUS.md` 与 `MASTER_PLAN.md` 已同步。
