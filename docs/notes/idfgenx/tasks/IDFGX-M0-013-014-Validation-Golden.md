---
task_id: IDFGX-M0-013-014
title: 实现 Validator 与 20 个 MVP Golden
module: M0
status: done
owner: Codex
created: 2026-08-25
depends_on:
  - IDFGX-M0-012
related_decisions: []
expected_report: docs/notes/idfgenx/reports/2026-08-25-IDFGX-M0-013-014-Validation-Golden.md
---

# IDFGX-M0-013/014：Validator 与 Golden

## 目标

实现独立 V0–V6 质量报告，并冻结 20 个全部通过 EnergyPlus v23.1 设计日仿真的 Golden。

## 范围

以 `docs/superpowers/specs/2026-08-25-m0-validation-golden-design.md` 为准；不进入 M1 数据生成或真实 HVAC。

## 验收命令

`python -m unittest discover -v`、`python -m compileall -q idfgenx tests`、`uv lock --check`、`git diff --check`。

## 执行记录

- [x] V0 输入契约、V1/V2 对象与引用、V3 几何、V4 工件、V6 摘要门禁的单元测试与实现。
- [x] V5 EnergyPlus v23.1 设计日仿真与总编排。
- [x] 20 个 Golden、全量验证、执行报告和状态收尾。
