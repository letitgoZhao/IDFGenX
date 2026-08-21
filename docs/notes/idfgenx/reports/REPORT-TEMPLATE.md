---
report_id: YYYY-MM-DD-IDFGX-M0-000
task_id: IDFGX-M0-000
status: completed
started: YYYY-MM-DDTHH:MM:SS+08:00
finished: YYYY-MM-DDTHH:MM:SS+08:00
executor: ai-or-human-name
related_commits: []
related_runs: []
---

# <task-id> 执行报告：<title>

## 1. 结果摘要

用三到五句话说明最终结果，以及是否达到任务完成标准。

## 2. 实际变更

| 文件/目录 | 变更 |
| --- | --- |
| `path/to/file` | 具体做了什么 |

## 3. 关键实现

- 说明重要设计选择；
- 说明与原计划的偏差及原因；
- 说明没有做什么。

## 4. 验证证据

| 命令/检查 | 结果 | 备注 |
| --- | --- | --- |
| `command` | PASS/FAIL | 数量、耗时或关键输出 |

## 5. 数据和兼容性影响

- Schema/API/数据 release/模型/部署是否变化；
- 向后兼容和迁移要求；
- 不涉及则写“无”。

## 6. 未完成项与风险

- 明确剩余问题；
- 若无，写“本任务范围内无”。

## 7. 后续任务

- `IDFGX-...`：下一步及原因。

## 8. 关联记录

- Task：`docs/notes/idfgenx/tasks/...`
- Commit/PR：填写真实引用
- Dataset/Model/Eval run：如适用
