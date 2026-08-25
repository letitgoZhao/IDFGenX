---
report_id: 2026-08-25-IDFGX-M0-002
task_id: IDFGX-M0-002
status: completed
started: 2026-08-25T16:13:00+08:00
finished: 2026-08-25T16:25:00+08:00
executor: Codex
related_commits:
  - 45748a7
related_runs: []
---

# IDFGX-M0-002 执行报告：ResolvedScenarioSpec v0.1

## 1. 结果摘要

已建立 Compiler 唯一输入 `ResolvedScenarioSpec`。它只接受 SI 长度、摄氏温度和
完整字段，并在构造时拒绝无效尺寸、WWR、温控顺序和退化周边-核心分区。

## 2. 实际变更

| 文件/目录 | 变更 |
| --- | --- |
| `idfgenx/schemas/resolved.py` | 新增不可变、SI-only Compiler 输入模型 |
| `idfgenx/schemas/__init__.py` | 导出 ResolvedScenarioSpec |
| `tests/unit/schemas/test_resolved.py` | 覆盖序列化、分区与交叉字段边界 |

## 3. 关键实现

- 矩形边长、层高、层数、WWR 和温控均有显式范围；
- `perimeter_core` 需要正核心深度，且严格小于短边一半；
- 本任务不进行 Draft 解析或默认填充，保持 Resolver 的唯一职责。

## 4. 验证证据

| 命令/检查 | 结果 | 备注 |
| --- | --- | --- |
| ResolvedSpec 失败测试 | PASS | 初始模块缺失 RED，后 3/3 GREEN |
| `python -m unittest discover -s tests -p "test_*.py"` | PASS | 34/34 |
| `python -m compileall -q idfgenx tests` | PASS | 退出码 0 |
| `uv lock --check` | PASS | 50 packages |
| `git diff --check` | PASS | 无空白错误 |

## 5. 数据和兼容性影响

新增内部 Compiler 协议；不修改官方快照、release、API 或既有 `server/`。

## 6. 未完成项与风险

本任务范围内无。单位换算与默认值由 M0-003 处理。

## 7. 后续任务

- `IDFGX-M0-003`：将 Draft 确定性解析为本协议；
- `IDFGX-M0-004`：封装 EnergyPlus v23.1 工具链。

## 8. 关联记录

- Task：`docs/notes/idfgenx/tasks/IDFGX-M0-002-ResolvedScenarioSpec.md`
- Commit：`45748a7`
