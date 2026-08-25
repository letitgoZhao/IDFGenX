---
adr_id: ADR-0001
title: Spec-LoRA 训练记录与 IDF 工件隔离
status: accepted
date: 2026-08-25
owners:
  - Codex
supersedes: null
superseded_by: null
---

# ADR-0001：Spec-LoRA 训练记录与 IDF 工件隔离

## 背景

生产主线训练 Qwen3-4B Spec-LoRA，使其把自然语言需求转换为
`ScenarioSpecDraft`。官方 IDF 含有未支持 HVAC、外部依赖和多个等价
高层解释；若把文件路径、文件内容或 IDF 哈希绑定为单条训练标签，会让
模型学习文件偶然性而非受控的场景契约。

## 决策

- 生产 `spec_sft` 的唯一学习映射是 `Prompt → ScenarioSpecDraft`。
- 单条生产训练记录不得含 IDF/epJSON 路径、文件名、文件内容、文件哈希，
  或指向某一官方 IDF 的外键。
- `ResolvedScenarioSpec`、epJSON、IDF 和 V0–V6 报告由同一 Draft
  的受控采样与 Compiler 自动生成，仅存于 staging/quarantine 的审计流程，
  不传给 LoRA 训练器。
- 官方 IDF 只自动提取为对象目录、模板候选、支持域约束和回归参考；不得
  直接反解为 SFT 标签。
- Direct-All 与 Direct-Fragment 仅作为论文基线：单独 release、单独
  模型、单独切分，永不与生产 `spec_sft` 混合。
- 生产 release 仅在批次级记录 Compiler/Schema/采样/Prompt 配置版本；
  不以文件级工件建立训练记录依赖。

## 备选方案

| 方案 | 优点 | 缺点 | 未选择原因 |
| --- | --- | --- | --- |
| Prompt→IDF 作为主线 | 输出直观 | 长输出、引用脆弱、不可控 HVAC 混入 | 与确定性 Compiler 主线冲突 |
| 官方 IDF 自动反标注为 Draft | 可复用现有文件 | 高层语义不唯一，支持域不完整 | 会制造歧义或错误标签 |
| Prompt→Draft，工件隔离审计 | 标签短、确定、可验证 | 需要数据工厂 | 选择；与生产架构一致 |

## 影响

- M1 的采样、Prompt 和反向标定必须以 Draft/Spec 为真值。
- 训练导出器必须拒绝任何 artifact/file 字段。
- M0-016 负责证明自动生成工件在语义 round-trip、等价变换和受控破坏下
  保持可验证或明确失败。
- 既有官方语料继续作为离线目录和模板来源，不改变其许可证或原始副本。

## 验证与回退

- M1 导出前检查 `spec_sft` schema 不存在 artifact/file 字段。
- 每个生成样本仍需通过 V0–V6；失败样本进入 quarantine。
- 若未来决定把 Direct 路线用于产品，必须新建 ADR 并改变生产架构，不得
  通过向 `spec_sft` 增加 IDF 字段绕过本决策。

## 关联

- Task：`IDFGX-M0-016`
- 方案：`docs/notes/IDFGenX-M1-数据获取与标定.md`
