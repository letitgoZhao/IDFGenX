---
task_id: IDFGX-M1-007
title: 中英文 clean Prompt 模板
module: M1
status: done
owner: Codex
created: 2026-08-28
updated: 2026-08-28
depends_on: [IDFGX-M1-006]
related_decisions: []
expected_report: docs/notes/idfgenx/reports/2026-08-28-IDFGX-M1-007-Clean-Prompts.md
---

# IDFGX-M1-007：中英文 clean Prompt 模板

## 1. 背景

M1-006 已冻结 `DisclosurePlan` 与诚实 Draft 派生规则，但数据工厂尚不能从同一建筑事实生成可审计的中英文 clean Prompt。M1-007 建立无噪声 Prompt 基线，供 M1-008 的鲁棒表达和 M1-009 的反向标定复用。

## 2. 目标

实现版本化 `prompt config v0.1`，确定性生成中文简洁、中文专家、英文简洁和英文专家四类 clean Prompt，并让每条输出同时携带唯一目标 Draft 与配置哈希。

## 3. 非目标

- 不实现语序扰动、单位变体、同义改写或受控噪声；
- 不实现 Prompt 反向解析与标定报告；
- 不创建 Canonical Sample、staging 或 data release；
- 不修改 ScenarioSpec、Resolver、Compiler 或 Validator 协议。

## 4. 输入与前置条件

- `IDFGX-M1-006` 已完成；
- 输入为已验证的 `ResolvedScenarioSpec`；
- `DisclosurePlan` 是决定哪些事实可写入 Prompt 和目标 Draft 的唯一来源；
- Python 固定为 3.11，配置文件采用 UTF-8 JSON。

## 5. 影响文件

| 文件/目录 | 预期变更 |
| --- | --- |
| `configs/prompts/clean_v0_1.json` | 冻结四个 clean family、字段顺序与披露集合 |
| `idfgenx/data_factory/prompts.py` | 配置模型、加载/哈希、确定性渲染与结构化输出 |
| `tests/unit/data_factory/test_prompts.py` | 配置门禁、四类渲染、披露边界和确定性测试 |
| `docs/notes/idfgenx/STATUS.md` | 登记活动任务与完成证据 |
| `docs/notes/idfgenx/MASTER_PLAN.md` | 同步 M1-007 状态 |

## 6. 详细执行步骤

- [x] 1. 核对 M1 方案、M1-006 接口与现有数据工厂约定；
- [x] 2. 先增加配置和渲染行为的失败测试；
- [x] 3. 实现最小配置模型、哈希和四类 clean Prompt 渲染；
- [x] 4. 运行 Prompt 专项测试并重构注释、类型和错误边界；
- [x] 5. 运行全量 Python 测试和语法编译；
- [x] 6. 检查 diff、敏感文件、运行时产物和兼容性；
- [x] 7. 写执行报告并更新任务、总计划和状态页。

## 7. 数据与接口变更

- 新增内部配置协议 `prompt config v0.1` 和结构化 `CleanPromptRecord`；
- 不改变现有 Schema/API；
- 不生成或修改数据 release，因此无迁移要求。

## 8. 风险与回滚

| 风险 | 预防/检测 | 回滚方式 |
| --- | --- | --- |
| Prompt 泄露未声明默认值 | 渲染只消费 `derive_draft` 的 requested 字段，并测试部分披露 | 删除新增模块和配置即可回滚 |
| 中英文枚举或单位语义不一致 | 四个 family 使用同一字段序列并以字面期望测试 | 恢复配置与渲染映射 |
| 配置变化不可追溯 | 规范 JSON SHA-256 与确定性测试 | 恢复 `clean_v0_1.json` |

## 9. 验证命令

```text
uv run python -m unittest tests.unit.data_factory.test_prompts -v
uv run python -m unittest discover -s tests -v
uv run python -m compileall -q idfgenx tests
git diff --check
git status --short
```

## 10. 完成标准

- [x] 四个 clean family 均可确定性渲染；
- [x] Prompt 仅包含 DisclosurePlan 标记为 requested 的事实；
- [x] 输出 Draft、语言、风格、family 和配置哈希可审计；
- [x] 无噪声、反向标定或 release 范围扩张；
- [x] 公共接口具有类型和中文工业级 docstring；
- [x] 专项与全量验证通过；
- [x] 无敏感数据和非预期生成文件；
- [x] 报告已生成，`STATUS.md` 与 `MASTER_PLAN.md` 已更新。

## 11. 执行记录

- 2026-08-28：确认采用 Draft-first 渲染边界；Prompt 不直接读取未披露的 ResolvedSpec 字段。
- 2026-08-28：独立审查发现建筑名称分隔符、空披露和 Draft 版本追溯边界；均以失败测试复现并修复，复核结论为可合并。
- 2026-08-28：Prompt 专项 13/13、全量 115/115、语法编译和 diff 检查通过。

## 12. 结果

- 报告：`docs/notes/idfgenx/reports/2026-08-28-IDFGX-M1-007-Clean-Prompts.md`
- Commit/PR：本任务提交（SHA 见提交后 `git log`）；未创建 PR
