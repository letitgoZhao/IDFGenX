---
task_id: IDFGX-M1-008
title: 实现可审计的鲁棒 Prompt family
module: M1
status: done
owner: Codex
created: 2026-08-29
updated: 2026-08-29
depends_on: [IDFGX-M1-007]
related_decisions: [ADR-0001, ADR-0002]
expected_report: docs/notes/idfgenx/reports/2026-08-29-IDFGX-M1-008-Robust-Prompts.md
---

# IDFGX-M1-008：可审计的鲁棒 Prompt family

## 1. 背景

M1-007 已冻结四类中英文 clean Prompt，但所有数值仍使用 SI、字段顺序固定，
且没有显式受控噪声。M1-008 在不改变 clean v0.1 输出的前提下，增加可供
M1-009 反向标定覆盖的单位、语序、专家表达和表层噪声变体。

## 2. 目标

实现由版本化配置和显式变体计划驱动的确定性鲁棒 Prompt 渲染，使每条记录
都能追溯单位、语序、表达和最多一种不改变建筑语义的受控噪声。

## 3. 非目标

- 不实现 Prompt 反向解析或标定报告；
- 不引入拼写错误、数值扰动、矛盾条件或 unsupported 请求；
- 不创建 Canonical Sample、staging、quarantine 或数据 release；
- 不修改 ScenarioSpec、Resolver、Compiler、Validator 或 clean v0.1 契约；
- 不在渲染器内部使用随机数或隐式选择变体。

## 4. 输入与前置条件

- `IDFGX-M1-007` 已完成，四类 clean Prompt 和 DisclosurePlan 已冻结；
- 输入为 `ResolvedScenarioSpec`，单位变体目标仍须经现有 Resolver 还原为同一事实；
- Python 固定为 3.11，配置为 UTF-8 JSON；
- 2026-08-29 用户已批准有界设计：显式变体计划、英制 Draft 同步和表层噪声边界。

## 5. 影响文件

| 文件/目录 | 预期变更 |
| --- | --- |
| `configs/prompts/robust_v0_1.json` | 冻结单位、语序、专家表达和噪声选项 |
| `idfgenx/data_factory/robust_prompts.py` | 实现配置、追溯模型、单位转换和确定性渲染 |
| `idfgenx/data_factory/robust_prompt_renderers.py` | 隔离四类 standard/alternate 文本渲染 |
| `idfgenx/data_factory/prompts.py` | 提升从诚实 Draft 渲染 clean 文本的窄复用边界 |
| `tests/unit/data_factory/test_robust_prompts.py` | 配置、字面输出、往返、披露和错误门禁测试 |
| `docs/notes/idfgenx/decisions/ADR-0001-*.md` | 标明模型规模由 ADR-0002 更新 |
| `docs/notes/idfgenx/MASTER_PLAN.md`、`STATUS.md` | 修正训练口径并登记任务状态 |
| `docs/notes/IDFGenX-M1-数据获取与标定.md` | 修正 10K Pilot 的 8B 模型口径 |

## 6. 详细执行步骤

- [x] 1. 核对 M1 设计、M1-007 接口、Draft 原始单位和 Resolver 换算边界；
- [x] 2. 创建任务记录并纠正 X-006 遗留的固定 4B 文档表述；
- [x] 3. 先为配置、公共契约和鲁棒渲染写失败测试；
- [x] 4. 实现最小配置、显式变体计划、单位目标 Draft 和渲染器；
- [x] 5. 补齐确定性、DisclosurePlan、单噪声和 Resolver 往返门禁；
- [x] 6. 运行专项、全量测试、语法编译和 diff 检查；
- [x] 7. 独立代码审查并处理 Critical/Important 问题；
- [x] 8. 写执行报告并更新任务、主计划和状态页。

## 7. 数据与接口变更

- 新增内部 `robust prompt config v0.1`、显式变体计划和鲁棒 Prompt 记录；
- clean Prompt v0.1、ScenarioSpecDraft v0.1 和现有 API 保持兼容；
- 未生成数据 release，无迁移要求。

## 8. 风险与回滚

| 风险 | 预防/检测 | 回滚方式 |
| --- | --- | --- |
| Prompt 单位与目标 Draft 不一致 | 对英尺/华氏度做字面断言和 Resolver 往返测试 | 删除鲁棒模块和配置 |
| 噪声改变建筑语义 | 仅允许配置列举的表层噪声并限制最多一种 | 禁用对应噪声 ID |
| 变体组合不可复现 | 所有选择由冻结的显式计划给出，禁止内部 RNG | 恢复单一 clean 渲染入口 |
| 未披露默认值泄漏 | 渲染只消费按 DisclosurePlan 生成的目标 Draft | 删除泄漏分支并保留回归测试 |

## 9. 验证命令

```text
.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_robust_prompts -v
.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_prompts -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q idfgenx tests
git diff --check
git status --short
```

## 10. 完成标准

- [x] 单位、语序、专家表达和表层噪声均由显式计划确定性生成；
- [x] 英制 Prompt 的目标 Draft 保留 `ft/degF`，Resolver 还原同一 SI 事实；
- [x] 每条记录包含配置哈希和完整变体追溯元数据；
- [x] clean v0.1 输出和披露边界保持兼容；
- [x] 公共接口具有类型和中文工业级 docstring；
- [x] 专项与全量验证通过；
- [x] 无敏感数据和非预期生成文件；
- [x] 报告已生成，`STATUS.md` 与 `MASTER_PLAN.md` 已更新。

## 11. 执行记录

- 2026-08-29：用户批准显式变体计划、英制 Draft 同步和仅表层噪声的短设计。
- 2026-08-29：完成 48 个显式计划、192 条 family 记录的确定性和 Resolver
  往返矩阵；Prompt 专项 29/29、全量 131/131、语法编译和 diff 检查通过。
- 2026-08-29：独立初审的 4 个 Important 均以失败测试修复；复核无剩余问题，
  结论为 Ready to merge: Yes。

## 12. 结果

- 报告：`docs/notes/idfgenx/reports/2026-08-29-IDFGX-M1-008-Robust-Prompts.md`
- Commit/PR：本任务与报告所在提交；未创建 PR
