---
report_id: 2026-08-28-IDFGX-X-006
task_id: IDFGX-X-006
status: completed
started: 2026-08-28T14:09:27+08:00
finished: 2026-08-28T14:38:22+08:00
executor: Codex
related_commits:
  - 7b1c1f6
related_runs: []
---

# IDFGX-X-006 执行报告：分阶段 Qwen 训练策略

## 1. 结果摘要

训练架构已从固定 Qwen3-4B/RTX 4090 路线调整为本地 RTX 4060 8GB 的
Qwen3-0.6B Smoke、Qwen3-1.7B 效果候选与云端 Qwen3-8B 正式
Pilot/Scale。Qwen3-4B 保留为可选成本对照或资源回退，14B 及以上仅在 8B
显示容量瓶颈且收益覆盖成本时开展。ADR-0002、仓库规则、主计划、状态、
设计和实施计划已完成；本任务未下载模型、运行训练或生成权重。

## 2. 实际变更

| 文件/目录 | 变更 |
| --- | --- |
| `AGENTS.md` | 把固定 4B 约束改为 0.6B/1.7B→8B+ 分阶段 BF16 LoRA |
| `docs/notes/idfgenx/decisions/ADR-0002-staged-qwen-training.md` | 固化模型职责、晋级门、公平比较和回退条件 |
| `docs/notes/idfgenx/MASTER_PLAN.md` | 新增 X-006，重排 M2-003 至 M2-010 |
| `docs/notes/idfgenx/STATUS.md` | 登记决策、边界、验证证据和后续 M1 任务 |
| `docs/notes/idfgenx/tasks/IDFGX-X-006-分阶段Qwen训练策略.md` | 记录范围、步骤、风险、验证和完成状态 |
| `docs/superpowers/specs/2026-08-28-staged-qwen-training-design.md` | 保存经用户批准的架构设计 |
| `docs/superpowers/plans/2026-08-28-staged-qwen-training.md` | 保存并跟踪实施计划 |
| `docs/notes/IDFGenX总体的方案规划.md`、模块索引、M2/M3/M5 | 同步本地方案笔记中的模型、硬件、评估和部署事实 |

最后一组 `docs/notes/IDFGenX*.md` 继续遵守既有 `.gitignore`，只作为本地
方案笔记维护；本任务没有擅自扩大父目录的 Git 跟踪范围。可推送的 ADR、
任务、主计划、状态和报告包含完整决策与执行顺序。

## 3. 关键实现

- L0：0.6B 在 RTX 4060 8GB 上验证 loader、tokenizer、loss mask、反向传播、
  checkpoint、小评估和端到端调用；
- L1：1.7B 只有实际显存 smoke 通过后才进入本地效果迭代，其结果不替代
  8B 正式成绩；
- C1/C2：8B 在云端重新校准超参，完成 10K Pilot、同基座 Spec/Direct 比较
  和 50K Scale；
- C3：100K 数据或 14B+ 模型都由 8B 的明确边际收益或容量瓶颈触发；
- 继续使用 BF16 标准 LoRA，不默认使用 4-bit/8-bit 量化，不允许静默截断；
- M3 明确 E2/E3/E4 正式 Pilot 必须同一 8B revision 和匹配预算；
- M5 区分本地 Transformers 开发档与云端 vLLM 正式服务档。

## 4. 验证证据

| 命令/检查 | 结果 | 备注 |
| --- | --- | --- |
| `uv run python -m unittest discover -s tests -v` | PASS | 提交前复验 115/115，57.364 秒；代码未变 |
| 11 个受影响文档必需术语扫描 | PASS | 每个文件均包含 0.6B、1.7B、8B 分层 |
| 旧约束扫描 | PASS | 未发现仍生效的固定 4B/4090 主线表述 |
| 占位符扫描 | PASS | 未发现 TBD、TODO、待定或实现占位符 |
| 尾随空白检查 | PASS | 仅命中既有 Markdown 双空格换行；无非预期尾随空白 |
| `git diff --check` | PASS | 退出码 0 |
| Git 状态与敏感文件检查 | PASS | 无模型权重、数据集、`.env`、runtime 或训练产物 |

## 5. 数据和兼容性影响

- 不修改 ScenarioSpec、Compiler、Validator、API 或 dataset release；
- 不修改 Python/前端代码和依赖锁，无迁移要求；
- 后续训练配置名和 Model Manifest 将按新模型分层创建；
- 已存在的模型产物为零，因此不存在 Adapter 迁移或兼容负担。

## 6. 未完成项与风险

- RTX 4060 8GB 上的 1.7B BF16 LoRA、目标序列长度和吞吐尚未实测，不能把
  本文档决策解读为训练已通过；
- 云端 8B 的具体 GPU、并行方式和成本必须在 M2 实施时通过显存/吞吐 smoke
  选择，不能预先假定单卡或多卡方案；
- 小模型最优超参不会直接作为 8B 最优超参，8B Pilot 必须重新验证；
- `docs/notes/IDFGenX*.md` 是按既有策略忽略的本地笔记，远端以 ADR-0002、
  主计划和任务报告为版本事实源。

## 7. 后续任务

- `IDFGX-M1-008`：实现单位、语序、专家表达和受控噪声 Prompt；
- `IDFGX-M1-009`：实现 Prompt 数值、单位和实体反向标定；
- `IDFGX-M1-010`：实现 Canonical Sample 与内容哈希对象存储；
- `IDFGX-M2-003`：在 M1 1K release 完成后执行 0.6B/RTX 4060 本地训练 smoke。

## 8. 关联记录

- Task：`docs/notes/idfgenx/tasks/IDFGX-X-006-分阶段Qwen训练策略.md`
- ADR：`docs/notes/idfgenx/decisions/ADR-0002-staged-qwen-training.md`
- Design：`docs/superpowers/specs/2026-08-28-staged-qwen-training-design.md`
- Plan：`docs/superpowers/plans/2026-08-28-staged-qwen-training.md`
- Commit/PR：`7b1c1f6`（设计）与本报告所在最终文档提交；未创建 PR
- Dataset/Model/Eval run：无
