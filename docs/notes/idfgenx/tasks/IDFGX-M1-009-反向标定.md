---
task_id: IDFGX-M1-009
title: Prompt 数值、单位与实体反向标定
module: M1
status: ready
owner: Codex
created: 2026-08-29
updated: 2026-08-29
depends_on: [IDFGX-M1-007, IDFGX-M1-008]
related_decisions: []
expected_report: docs/notes/idfgenx/reports/2026-08-29-IDFGX-M1-009-Prompt-Calibration.md
---

# IDFGX-M1-009：Prompt 数值、单位与实体反向标定

## 1. 背景

M1-007/M1-008 已冻结四类 clean Prompt 和 48 个 robust 变体计划。M1-009 为这些项目自产文本提供独立反向检查，保证 Prompt、ScenarioSpecDraft 和后续数据标签保持一致。

## 2. 目标

对当前四个 clean family 和 192 个 robust record 组合执行确定性字段提取与 Draft 逐字段比对，并为失败记录返回可审计错误码。

## 3. 非目标

- 不解析任意用户自由文本；
- 不调用 LLM，不自动纠错；
- 不创建 release，不改变 Resolver、Compiler 或 Draft schema。

## 4. 输入与前置条件

- Prompt config v0.1、robust config v0.1；
- `CleanPromptRecord`、`RobustPromptRecord` 与 Draft schema v0.1；
- M1-007、M1-008 已通过现有专项与全量测试。

## 5. 影响文件

| 文件/目录 | 预期变更 |
| --- | --- |
| `idfgenx/data_factory/calibrate.py` | 新增独立提取、比较和报告边界 |
| `tests/unit/data_factory/test_calibrate.py` | 新增正向、负向、确定性和 192 组合门禁 |
| `docs/notes/idfgenx/reports/2026-08-29-IDFGX-M1-009-Prompt-Calibration.md` | 执行报告 |

## 6. 详细执行步骤

- [ ] 1. 为 CalibrationReport、字段结果和错误码增加失败测试；
- [ ] 2. 实现四个 family 的受限提取器和版本化别名；
- [ ] 3. 实现 Decimal 数值/单位/实体比较与默认值泄漏门禁；
- [ ] 4. 增加 192 组合和文本变异测试；
- [ ] 5. 运行专项、全量、compileall、diff 和敏感文件检查；
- [ ] 6. 生成报告，更新 STATUS 和任务状态。

## 7. 数据与接口变更

新增校准结果 Pydantic 协议；不改变 ScenarioSpec、Prompt record、Resolver、Compiler 或 release 格式。

## 8. 风险与回滚

| 风险 | 预防/检测 | 回滚方式 |
| --- | --- | --- |
| 同义词扩张导致误匹配 | 版本化别名、重复候选检测和负向测试 | 移除校准模块并保留 Prompt 代码 |
| 数值精度误判 | Decimal 和显示值契约测试 | 回退校准协议实现，不改生成器 |
| 模板新增字段未校准 | family/schema 版本门禁 | 拒绝新协议直到补齐解析器 |

## 9. 验证命令

```text
.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_calibrate -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m compileall -q idfgenx tests
git diff --check
```

## 10. 完成标准

- [ ] clean 与 robust 正向标定通过；
- [ ] 192 个 robust 组合全部通过；
- [ ] 失败边界返回稳定错误码；
- [ ] 公共接口有类型标注和中文 docstring；
- [ ] 报告已生成，STATUS 已更新；
- [ ] 无敏感数据和运行产物。

## 11. 结果

- 报告：`docs/notes/idfgenx/reports/2026-08-29-IDFGX-M1-009-Prompt-Calibration.md`
- Commit/PR：待完成后填写
