---
task_id: IDFGX-M0-001
title: 冻结 ScenarioSpecDraft v0.1 字段和状态语义
module: M0
status: done
owner: Codex
created: 2026-08-25
updated: 2026-08-25
depends_on:
  - IDFGX-X-001
related_decisions: []
expected_report: docs/notes/idfgenx/reports/2026-08-25-IDFGX-M0-001-ScenarioSpecDraft.md
---

# IDFGX-M0-001：冻结 ScenarioSpecDraft v0.1 字段和状态语义

## 目标

建立可由模型输出、保留原始单位并携带字段状态的 Pydantic v2 Draft 协议，作为 Resolver 的唯一输入。

## 范围

- 创建 `idfgenx.schemas.scenario` 的版本、字段状态、单位、数量和 Draft 模型；
- 覆盖长度、层数、分区、WWR、温控设定点和建筑用途；
- 导出 JSON Schema 并用单元测试冻结状态语义。

不实现单位换算、默认派生、几何、IDF、API 或 Golden。

## 验证命令

```powershell
D:\GithubProject\IDFGenX\.venv\Scripts\python.exe -m unittest tests.unit.schemas.test_scenario -v
D:\GithubProject\IDFGenX\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
D:\GithubProject\IDFGenX\.venv\Scripts\python.exe -m compileall -q idfgenx tests
uv lock --check
git diff --check
```

## 完成标准

- [x] Draft 模型具有中文 docstring、类型和 `0.1` JSON Schema；
- [x] 状态与原始单位可序列化保留；
- [x] 相关失败测试先 RED 再 GREEN；
- [x] 全量测试、编译和锁文件检查通过；
- [x] 执行报告与 `STATUS.md` 已更新。

## 执行记录

- 2026-08-25：4 个 Draft 契约测试先因 `idfgenx.schemas` 不存在而 RED，随后
  实现 Pydantic v2 模型转为 GREEN；全量 31 项单测、compileall、`uv lock --check`
  和 `git diff --check` 通过。

## 结果

- 报告：`docs/notes/idfgenx/reports/2026-08-25-IDFGX-M0-001-ScenarioSpecDraft.md`
- Commit：`e2baad3`
