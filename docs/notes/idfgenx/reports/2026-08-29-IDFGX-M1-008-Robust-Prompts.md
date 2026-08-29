---
report_id: 2026-08-29-IDFGX-M1-008
task_id: IDFGX-M1-008
status: completed
started: 2026-08-29
finished: 2026-08-29T13:39:54+08:00
executor: Codex
related_commits: []
related_runs: []
---

# IDFGX-M1-008 执行报告：可审计的鲁棒 Prompt family

## 1. 结果摘要

新增版本化 robust prompt config v0.1 和显式变体计划，支持中英文简洁/专家
四类 family、`m/ft`、`degC/degF`、canonical/constraints-first 语序、
standard/alternate 表达以及 none/polite/context 单一表层噪声。48 个变体计划
可确定性产生 192 条 family 记录；每条记录携带配置哈希、稳定 variant ID、
原始单位和唯一目标 Draft。clean v0.1 基线保持字面与目标兼容，任务未创建
Canonical Sample、数据 release 或模型产物。

## 2. 实际变更

| 文件/目录 | 变更 |
| --- | --- |
| `configs/prompts/robust_v0_1.json` | 冻结 family、语序、单位、表达和噪声集合 |
| `idfgenx/data_factory/robust_prompts.py` | 配置/计划/记录模型、哈希、单位目标、精度与 perimeter 门禁、编排入口 |
| `idfgenx/data_factory/robust_prompt_renderers.py` | 隔离四类 standard/alternate 文本渲染 |
| `idfgenx/data_factory/prompts.py` | 提升 Draft 渲染和名称校验为 clean/robust 共用窄边界 |
| `tests/unit/data_factory/test_robust_prompts.py` | 新增配置、组合、往返、披露、语义和审查回归测试 |
| `docs/notes/idfgenx/MASTER_PLAN.md`、`STATUS.md` | 登记 M1-008 完成状态和下一出口 |
| `docs/notes/idfgenx/decisions/ADR-0001-*.md` | 标明模型规模由 ADR-0002 更新 |
| `docs/notes/IDFGenX-M1-数据获取与标定.md` | 将正式 10K Pilot 口径纠正为 Qwen3-8B |
| `docs/notes/idfgenx/tasks/IDFGX-X-006-*.md` 及报告 | 追加固定 4B 残留表述的 correction 记录 |

## 3. 关键实现

- `RobustPromptPlan` 显式选择每个变体维度，renderer 内无 RNG 或隐式分支；
- 配置规范 SHA-256 为
  `e0311e17b362424fcd30de02beb9736abde69b0b871d8b73016d177ee9fb69c2`；
- 英制值先换算并量化为实际输出精度，再写入 Draft；完整组合矩阵验证 Resolver
  能恢复同一 SI 建筑事实；
- requested 数值若不能由 12 位有效数字文本或 Resolver 的 6 位小数归一化无损
  表达，则以 `ConfigurationError` 拒绝，不静默修改标签；
- 全披露 perimeter-core 若使用 Draft v0.1 无法表达的自定义周边深度，同样在
  渲染前明确拒绝；部分披露仍按既有默认语义处理；
- `polite_filler` 使用无条件 `Please`/`麻烦`，`context_filler` 只附加概念设计
  上下文；不支持拼写、数值、矛盾或 unsupported 噪声；
- 独立审查初次发现 4 个 Important，均通过失败测试修复；复核无剩余问题，
  结论为 Ready to merge: Yes。

## 4. 验证证据

| 命令/检查 | 结果 | 备注 |
| --- | --- | --- |
| `.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_prompts tests.unit.data_factory.test_robust_prompts -v` | PASS | 29/29，0.065 秒 |
| `.\.venv\Scripts\python.exe -m unittest discover -s tests -v` | PASS | 131/131，51.941 秒；包含真实转换、100 Golden、稳定性、V0–V6 和最小仿真 |
| `.\.venv\Scripts\python.exe -m compileall -q idfgenx tests` | PASS | 退出码 0 |
| `git diff --check` | PASS | 退出码 0；仅提示仓库既有 CRLF 转换策略 |
| 敏感词、占位实现和尾随空白扫描 | PASS | 无命中 |
| 独立代码审查与复核 | PASS | 初审 4 Important 已处理；复核无 Critical/Important/Minor |

TDD 证据：模块/配置缺失、配置入口缺失、英制目标缺失、clean 兼容入口缺失、
跨 family 组合缺失、standard 组合缺失和名称门禁绕过均先产生预期 RED；审查
反馈中的条件性礼貌词、净高语义、高精度漂移和 perimeter 深度也分别先失败
后转绿。

## 5. 数据和兼容性影响

- 新增内部 robust prompt config v0.1、`RobustPromptPlan` 和
  `RobustPromptRecord`；ScenarioSpecDraft、Resolver、Compiler、Validator 和
  HTTP API 不变；
- clean prompt config v0.1 及其四类字面输出保持兼容；
- 未生成 staging、quarantine 或只读 release，无数据迁移要求；
- 后续 M1-009 可直接使用 variant ID、配置哈希和目标 Draft 做反向标定。

## 6. 未完成项与风险

- 非 canonical 高精度 requested 数值会被 v0.1 明确拒绝；若未来确有数据需求，
  应升级数值文本协议和配置版本，不得静默放宽；
- ScenarioSpecDraft v0.1 无独立 perimeter depth 字段，因此全披露自定义深度
  不能进入正向鲁棒 Prompt；
- M1-009 的反向解析与标定、M1-010 的 Canonical Sample 均不在本任务范围。

## 7. 后续任务

- `IDFGX-M1-009`：实现 Prompt 数值、单位和实体反向标定；
- `IDFGX-M1-010`：实现 Canonical Sample 与内容哈希对象存储。

## 8. 关联记录

- Task：`docs/notes/idfgenx/tasks/IDFGX-M1-008-鲁棒PromptFamily.md`
- Commit/PR：本报告所在提交；未创建 PR
- Dataset/Model/Eval run：无
