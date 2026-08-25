---
task_id: IDFGX-M0-003
title: 实现 Resolver 的单位、默认值、派生值和错误
module: M0
status: in_progress
owner: Codex
created: 2026-08-25
updated: 2026-08-25
depends_on:
  - IDFGX-M0-002
related_decisions: []
expected_report: docs/notes/idfgenx/reports/2026-08-25-IDFGX-M0-003-Resolver.md
---

# IDFGX-M0-003：实现 Resolver

## 目标

将合法且无歧义的 `ScenarioSpecDraft` 确定性解析为唯一 `ResolvedScenarioSpec`。

## 范围

- 单位换算、默认值、核心深度派生；
- ambiguous/unsupported/范围错误转为稳定 `ResolutionError`；
- 不读取环境、不生成几何、不调用 EnergyPlus。

## 验证命令

```powershell
D:\GithubProject\IDFGenX\.venv\Scripts\python.exe -m unittest tests.unit.compiler.test_resolve -v
D:\GithubProject\IDFGenX\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
D:\GithubProject\IDFGenX\.venv\Scripts\python.exe -m compileall -q idfgenx tests
uv lock --check
git diff --check
```

## 完成标准

- [ ] 英制/华氏输入规范化为 SI；
- [ ] 默认策略、派生值与失败边界均有测试；
- [ ] 相关测试先 RED 再 GREEN；
- [ ] 报告与 `STATUS.md` 已更新。
