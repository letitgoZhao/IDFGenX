---
task_id: IDFGX-M0-002
title: 定义 ResolvedScenarioSpec v0.1 与能力边界
module: M0
status: done
owner: Codex
created: 2026-08-25
updated: 2026-08-25
depends_on:
  - IDFGX-M0-001
related_decisions: []
expected_report: docs/notes/idfgenx/reports/2026-08-25-IDFGX-M0-002-ResolvedScenarioSpec.md
---

# IDFGX-M0-002：定义 ResolvedScenarioSpec v0.1 与能力边界

## 目标

建立只含 SI 单位、完整默认值和已确认能力边界的不可变 Compiler 输入协议。

## 范围

- 创建 `idfgenx.schemas.resolved`；
- 固化矩形建筑、层数、分区、WWR、温控与建筑用途的 SI 约束；
- 明确 Compiler 只接收 `ResolvedScenarioSpec`。

不实现单位换算或默认派生；这些由 M0-003 Resolver 完成。

## 验证命令

```powershell
D:\GithubProject\IDFGenX\.venv\Scripts\python.exe -m unittest tests.unit.schemas.test_resolved -v
D:\GithubProject\IDFGenX\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
D:\GithubProject\IDFGenX\.venv\Scripts\python.exe -m compileall -q idfgenx tests
uv lock --check
git diff --check
```

## 完成标准

- [x] ResolvedSpec 仅含规范化 SI 值；
- [x] 支持域和拒绝边界能由模型验证；
- [x] 相关测试先 RED 再 GREEN；
- [x] 报告与 `STATUS.md` 已更新。

## 执行记录

- 2026-08-25：3 个契约测试先因模块缺失 RED，后转 GREEN；测试夹具中的重复
  关键字参数会在 Pydantic 前触发 Python `TypeError`，已经根因确认后改为字典覆盖。
  全量 34 项单测、compileall、锁文件与 diff 检查通过。

## 结果

- 报告：`docs/notes/idfgenx/reports/2026-08-25-IDFGX-M0-002-ResolvedScenarioSpec.md`
- Commit：`45748a7`
