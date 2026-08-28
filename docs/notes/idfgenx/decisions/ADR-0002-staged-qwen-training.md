---
adr_id: ADR-0002
title: 本地小模型到云端 8B+ 的分阶段 Qwen 训练
status: accepted
date: 2026-08-28
owners:
  - Codex
supersedes: null
superseded_by: null
---

# ADR-0002：本地小模型到云端 8B+ 的分阶段 Qwen 训练

## 背景

原方案使用 Qwen3-1.7B 排查训练管线、Qwen3-4B 完成正式 LoRA，并以
单/双 RTX 4090 为主要训练环境。项目可长期使用的本地设备是 Y7000P、
RTX 4060 Laptop GPU 8GB；若训练代码、数据读取、checkpoint、评估和
端到端 Compiler 链路都等待云端资源，反馈周期和调试成本过高。

Qwen3 官方稠密模型没有名为“1B”的标准档位，因此用户提出的“1B”按
官方模型 `Qwen/Qwen3-1.7B` 落地。模型规模变化不能改变 Spec-LoRA 的
生产边界、冻结数据 release、无静默截断和论文公平比较要求。

## 决策

- L0 本地 Smoke 使用 `Qwen/Qwen3-0.6B`，在 RTX 4060 8GB 上验证数据读取、
  tokenizer、loss mask、反向传播、checkpoint、小评估和端到端调用。
- L1 本地候选使用 `Qwen/Qwen3-1.7B`，用于数据配比、Prompt、LoRA 模块、
  rank/学习率候选和错误分析；其结果是开发证据，不替代 8B 正式成绩。
- C1/C2 云端主线使用 `Qwen/Qwen3-8B` 完成 10K Pilot、50K Scale、正式
  Spec/Direct 公平比较和生产 Adapter 候选。
- Qwen3-4B 不再是必经生产门，仅作为可选成本对照或云端资源不足时的回退。
- Qwen3-14B 及以上只在 8B 仍显示容量瓶颈且预期收益覆盖资源成本时开展；
  不作为项目完成或服务上线的默认条件。
- 默认使用 BF16 标准 LoRA，不启用 4-bit/8-bit 量化训练。RTX 4060 8GB 的
  1.7B 可行性、序列长度和吞吐必须由实际显存 smoke 验证，不能用估算代替。
- OOM 时优先检查实现、使用 micro-batch 1、梯度累积和 gradient checkpointing；
  不允许静默截断。1.7B 无法满足门禁时迁移云端，0.6B 继续承担本地回归门。
- 小模型只迁移已经验证的训练代码、数据门和超参搜索方向；8B Pilot 必须重新
  验证学习率、LoRA rank、目标模块、序列预算和 batch。
- 论文 E2/E3/E4 的正式 Pilot 使用同一 Qwen3-8B revision、同一 split 和匹配
  预算。预算不足时统一缩小样本或统一降档，不混用不同模型规模宣称公平胜负。
- 每个 Adapter 用 Model Manifest 固定基础模型/tokenizer revision、数据版本、
  代码提交、LoRA 配置、硬件环境、峰值显存、吞吐和选择指标。

## 备选方案

| 方案 | 优点 | 缺点 | 未选择原因 |
| --- | --- | --- | --- |
| 保持 1.7B→4B，8B 可选 | 改动少，延续既有计划 | 本地反馈门不完整，4B 仍需较大显存且增加一次正式训练 | 不符合本地优先迭代目标 |
| 0.6B→1.7B→8B+ | 本地调试快，云端成本集中，正式模型容量更高 | 需要重新校准 8B 超参 | 选择；风险和成本边界最清楚 |
| 只用 0.6B 后直接上 8B | 阶段最少 | 缺少较可信的本地效果候选，云端调参风险高 | 跳过了有价值的 1.7B 验证门 |

## 影响

- M2 训练任务重排为 0.6B 本地 Smoke、1.7B 本地候选、8B 云端 Pilot/Scale。
- M3 的正式公平比较基座由固定 4B 改为冻结的 8B revision，小模型结果只作为
  工程验证和模型规模消融。
- M5 支持 RTX 4060 8GB 本地 Transformers 开发档与云端 8B 服务档；最终生产
  模型仍可依据统一指标选择 1.7B 低资源档，但必须在评估报告中说明依据。
- 既有 Schema、Compiler、Validator、数据 release 和 API 不变；无需数据迁移。
- 本决策不授权下载模型、生成权重或把训练产物提交 Git。

## 验证与回退

- 0.6B 必须首先通过 1K Smoke 的完整训练/评估/加载链路。
- 1.7B 必须记录 RTX 4060 的实际峰值显存并相对未微调基线呈现稳定改进；失败
  时迁移到云端，不降低数据门或改用默认量化绕过。
- 8B 只有在 10K Pilot 重新验证超参和端到端指标后才能进入 50K Scale。
- 若 8B 相对 1.7B 的收益不足以覆盖服务成本，允许选择 1.7B 作为生产档；
  若 8B 仍有明确容量瓶颈，再新建任务评估 14B+。
- 若本地小模型阶段不能降低云端调试成本，可通过新 ADR 恢复 4B 中间门；
  不在本 ADR 中预先承诺该回退训练。

## 关联

- Task：`IDFGX-X-006`
- Report：`docs/notes/idfgenx/reports/2026-08-28-IDFGX-X-006-Staged-Qwen-Training.md`
- 方案文档：`docs/superpowers/specs/2026-08-28-staged-qwen-training-design.md`
