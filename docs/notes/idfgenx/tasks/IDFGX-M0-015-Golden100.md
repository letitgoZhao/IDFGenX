---
task_id: IDFGX-M0-015
title: 扩展至 100 个 Compiler Golden
module: M0
status: done
owner: Codex
created: 2026-08-25
depends_on:
  - IDFGX-M0-014
expected_report: docs/notes/idfgenx/reports/2026-08-25-IDFGX-M0-015-Golden100.md
---

# IDFGX-M0-015：100 Golden

## 目标与范围

按已批准设计将 Compiler Golden 从 20 扩展为 100，不改变既有支持域；每项必须通过真实 v23.1 V0–V6 设计日门禁。

## 验收命令

`python -m unittest discover -v`、`python -m compileall -q idfgenx tests`、`uv lock --check`、`git diff --check`。

## 执行清单

- [x] 发现测试改为 100 项、50/50 布局平衡。
- [x] 新增 80 项 Spec 与审阅摘要。
- [x] 运行全部 100 项真实 V0–V6 Golden。
- [x] 写报告并更新 STATUS/MASTER_PLAN。
