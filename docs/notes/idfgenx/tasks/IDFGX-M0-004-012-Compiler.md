---
task_id: IDFGX-M0-004-012
title: 完成 EnergyPlus v23.1 确定性 Compiler
module: M0
status: done
owner: Codex
created: 2026-08-25
updated: 2026-08-25
depends_on:
  - IDFGX-M0-003
related_decisions: []
expected_report: docs/notes/idfgenx/reports/2026-08-25-IDFGX-M0-004-012-Compiler.md
---

# IDFGX-M0-004 至 M0-012：Compiler

## 目标

以 `ResolvedScenarioSpec` 为唯一输入，确定性生成可由 EnergyPlus v23.1 转换的 IDF。

## 范围

- v23.1 工具链发现、稳定命名、矩形几何、分区、相邻面和 WWR 开窗；
- 受控材料、构造、日程、内部负荷、温控和 IdealLoads 对象图；
- canonical epJSON、独占工作目录转换和 SHA-256 工件记录；
- 不包含 Validator、Golden、真实 HVAC 拓扑或仿真。

## 验证命令

`python -m unittest discover -v`、`python -m compileall -q idfgenx`、`uv lock --check`、`git diff --check`。

## 完成标准

- [x] 仅接受 `ResolvedScenarioSpec` 并生成固定排序的 epJSON；
- [x] 单区、多层、九区 perimeter-core、相邻面和窗洞均有测试；
- [x] 模板对象引用闭合，且未生成真实 AirLoopHVAC/PlantLoop；
- [x] 用本机 EnergyPlus v23.1 完成 epJSON 到 IDF 的真实转换测试；
- [x] 执行报告、`STATUS.md` 和主计划已更新。
