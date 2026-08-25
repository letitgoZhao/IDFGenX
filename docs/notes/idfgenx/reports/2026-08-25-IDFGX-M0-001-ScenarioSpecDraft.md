---
report_id: 2026-08-25-IDFGX-M0-001
task_id: IDFGX-M0-001
status: completed
started: 2026-08-25T16:00:00+08:00
finished: 2026-08-25T16:12:00+08:00
executor: Codex
related_commits:
  - e2baad3
related_runs: []
---

# IDFGX-M0-001 执行报告：ScenarioSpecDraft v0.1

## 1. 结果摘要

已建立 Pydantic v2 `ScenarioSpecDraft` 协议。Draft 保留用户原始值、单位和字段
状态，禁止在模型输出边界提前换算、默认或猜测；协议固定为 `0.1` 并拒绝未知字段。

## 2. 实际变更

| 文件/目录 | 变更 |
| --- | --- |
| `idfgenx/schemas/scenario.py` | 新增 Draft、数量、单位、状态、用途与分区模型 |
| `idfgenx/schemas/__init__.py` | 导出稳定 schema 公共类型 |
| `tests/unit/schemas/test_scenario.py` | 覆盖保真、状态语义和 JSON Schema 契约 |
| `pyproject.toml`、`uv.lock` | 明确声明 Pydantic v2 直接依赖 |

## 3. 关键实现

- `requested` 字段必须保留值；`defaulted`、`ambiguous` 与 `unsupported` 不得携带
  已解释值，确保 Resolver 能可靠判断是否需要默认或拒绝；
- 长度仅允许 `m`/`ft`，温度仅允许 `degC`/`degF`，但 Draft 不进行换算；
- 本任务不实现 Resolver、几何、模板、IDF 或 API。

## 4. 验证证据

| 命令/检查 | 结果 | 备注 |
| --- | --- | --- |
| Draft 失败测试 | PASS | 初始因模块缺失 RED，后 4/4 GREEN |
| `python -m unittest discover -s tests -p "test_*.py"` | PASS | 31/31 |
| `python -m compileall -q idfgenx tests` | PASS | 退出码 0 |
| `uv lock --check` | PASS | 50 packages |
| `git diff --check` | PASS | 无空白错误 |

## 5. 数据和兼容性影响

新增内部 schema 协议，不修改官方 IDF、manifest、release、HTTP API 或既有 `server/`。

## 6. 未完成项与风险

本任务范围内无。Draft 的默认值、单位换算和能力拒绝由下一任务 Resolver 处理。

## 7. 后续任务

- `IDFGX-M0-002`：定义 ResolvedScenarioSpec，作为 Compiler 的唯一输入；
- `IDFGX-M0-003`：实现单位、默认值、派生值和错误的确定性 Resolver。

## 8. 关联记录

- Task：`docs/notes/idfgenx/tasks/IDFGX-M0-001-ScenarioSpecDraft.md`
- Commit：`e2baad3`
