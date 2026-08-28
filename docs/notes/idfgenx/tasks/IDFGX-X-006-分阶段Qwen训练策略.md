---
task_id: IDFGX-X-006
title: 面向本地 RTX 4060 与云端 GPU 的分阶段 Qwen 训练策略
module: X
status: done
owner: Codex
created: 2026-08-28
updated: 2026-08-28
depends_on: [IDFGX-SETUP-002]
related_decisions: [ADR-0002]
expected_report: docs/notes/idfgenx/reports/2026-08-28-IDFGX-X-006-Staged-Qwen-Training.md
---

# IDFGX-X-006：面向本地 RTX 4060 与云端 GPU 的分阶段 Qwen 训练策略

## 1. 背景

现有方案以 Qwen3-1.7B 作为 Smoke 模型、Qwen3-4B 作为固定生产主模型，
并主要围绕单/双 RTX 4090 规划训练。项目实际可长期使用的本地设备是
Y7000P、RTX 4060 8GB；若所有训练调试都等待云端资源，训练代码、数据、
指标和端到端链路的迭代成本过高。

## 2. 目标

冻结“本地 0.6B/1.7B 低成本闭环，云端 8B 及以上规模化”的分阶段训练
策略，并使总体方案、模块计划、任务依赖、评估公平性和部署出口保持一致。

## 3. 非目标

- 不在本任务中下载模型或运行训练；
- 不修改训练代码、依赖锁或数据 release；
- 不承诺未经显存 smoke 验证的序列长度、吞吐或训练耗时；
- 不改变 Spec-LoRA 生产主线和 Direct-All/Direct-Fragment 论文基线边界；
- 不默认引入 4-bit/8-bit 量化训练。

## 4. 输入与前置条件

- 本地设备为 RTX 4060 Laptop GPU 8GB；
- Qwen3 官方稠密模型档位包含 0.6B、1.7B、4B、8B、14B 和 32B，
  用户所称“1B”按官方型号落为 Qwen3-1.7B；
- M1 数据 release、M0 Compiler/Validator 和统一评估协议仍是训练入口门禁；
- 基础模型、tokenizer 和 Adapter 必须以精确 revision 与 manifest 追溯。

## 5. 影响文件

| 文件/目录 | 预期变更 |
| --- | --- |
| `AGENTS.md` | 把固定 4B 约束改为分阶段模型策略 |
| `docs/notes/IDFGenX总体的方案规划.md` | 更新模型、硬件、训练阶段、实验和部署主线 |
| `docs/notes/IDFGenX-M2-模型训练.md` | 冻结 0.6B→1.7B→8B+ 训练门 |
| `docs/notes/IDFGenX-M3-实验评估与论文.md` | 更新主实验的同基座公平比较规则 |
| `docs/notes/IDFGenX-M5-部署与运维.md` | 增加 RTX 4060 本地开发与云端 8B+ 部署边界 |
| `docs/notes/IDFGenX的模块文档索引.md` | 更新模型主线摘要 |
| `docs/notes/idfgenx/MASTER_PLAN.md` | 重排 M2 任务与出口 |
| `docs/notes/idfgenx/STATUS.md` | 登记决策与下一步 |
| `docs/notes/idfgenx/decisions/ADR-0002-staged-qwen-training.md` | 固化架构决策 |

## 6. 详细执行步骤

- [x] 1. 核对总体方案、M2/M3/M5、主计划与官方 Qwen3 型号；
- [x] 2. 编写并自检分阶段训练设计；
- [x] 3. 用户审核书面设计；
- [x] 4. 编写实施计划；
- [x] 5. 新增 ADR 并同步全部受影响文档；
- [x] 6. 检查模型、硬件、精度、任务依赖和评估口径的一致性；
- [x] 7. 运行文档、diff、敏感文件和 Git 状态检查；
- [x] 8. 写执行报告，更新任务状态并提交、推送。

## 7. 数据与接口变更

- 不修改 Schema、API、Compiler 或 dataset release；
- 修改训练配置的规划命名、模型规模门和 Model Manifest 要求；
- 后续各模型 Adapter 保持独立，不允许用小模型结果冒充 8B 正式成绩。

## 8. 风险与回滚

| 风险 | 预防/检测 | 回滚方式 |
| --- | --- | --- |
| 1.7B 在 8GB 显存下无法覆盖目标序列 | 先做峰值显存 smoke，禁止静默截断 | 保留 0.6B 本地门，将 1.7B 迁至云端 |
| 小模型超参不能直接迁移到 8B | 云端 Pilot 重新验证学习率、rank 和序列预算 | 仅迁移代码与数据门，不迁移未经验证的超参 |
| 8B Direct 基线成本过高 | 预注册统一预算与停止门 | 缩小 Pilot 样本但保持同基座公平比较 |
| 文档仍残留固定 4B/4090 假设 | 全仓模型与硬件术语扫描 | 恢复本任务提交并重新设计 |

## 9. 验证命令

```text
Select-String 全仓扫描 Qwen3、4B、8B、4090、4060、LoRA 与量化表述
git diff --check
git status --short
git diff --name-only
```

## 10. 完成标准

- [x] 0.6B、1.7B、8B+ 的职责和晋级门明确；
- [x] RTX 4060 8GB 仅作经 smoke 验证的本地训练承诺；
- [x] 4B 不再是固定生产门，仍可作为可选中间对照；
- [x] M3 同基座公平比较和 M5 最终部署出口同步更新；
- [x] 未引入量化训练、模型权重或运行时产物；
- [x] 报告已生成，`STATUS.md` 与 `MASTER_PLAN.md` 已更新。

## 11. 执行记录

- 2026-08-28：用户确认采用 Qwen3-0.6B、官方 Qwen3-1.7B、云端
  Qwen3-8B 及更高模型的分阶段路线。
- 2026-08-28：书面设计和实施计划经用户审核后执行；基线全量 115/115
  测试通过，文档术语、占位符、diff 和敏感文件检查通过。
- 2026-08-28：`docs/notes/IDFGenX*.md` 按既有 `.gitignore` 继续作为本地
  方案笔记维护；可推送的 ADR、任务、主计划、状态和报告已包含完整决策。
- 2026-08-28：`main` 以纯快进方式推送至 `origin/main`，首次推送落点为
  `bb40bd3`；随后补交实施计划完成状态。

## 12. 结果

- 报告：`docs/notes/idfgenx/reports/2026-08-28-IDFGX-X-006-Staged-Qwen-Training.md`
- Commit/PR：`7b1c1f6`（设计）；最终文档提交见本任务完成后的 `git log`；未创建 PR
