---
report_id: 2026-08-21-IDFGX-M1-001
task_id: IDFGX-M1-001
status: completed
started: 2026-08-21T21:30:00+08:00
finished: 2026-08-21T23:17:20+08:00
executor: Codex
related_commits: []
related_runs:
  - energyplus-v23.1-official-corpus
---

# IDFGX-M1-001 执行报告：EnergyPlus v23.1 官方语料快照

> 路径迁移：自 2026-08-25 起，本快照的规范位置为
> `data/selected_official_idfs`，见 `ADR-0001`。本文保留的旧路径用于记录
> 2026-08-21 的实际执行事实。

## 1. 结果摘要

已全量扫描 EnergyPlus v23.1 的 731 个 Example IDF 和 47 个 DataSet IDF，并冻结 68 个精心筛选的官方文件。最终集合包含 12 个简单种子、20 个复杂种子、25 个仅供几何学习的参考和 11 个模板，总体积约 15.9 MiB；全部元数据集中存放，不生成重复 README。68 个副本哈希、32 个核心种子格式转换和 8 个代表模型设计日仿真全部通过。

## 2. 实际变更

| 文件/目录 | 变更 |
| --- | --- |
| `data/official_idf_v23_1/idf/` | 保存 68 个逐字节不变的官方 IDF |
| `data/official_idf_v23_1/metadata/` | 保存全量 inventory、精选 manifest、策略、汇总和验证报告 |
| `data/official_idf_v23_1/LICENSE.txt` | 保存 EnergyPlus v23.1 原始许可证 |
| `idfgenx/data_factory/official_corpus.py` | 实现扫描、范围检查、哈希、去重、显式名单和原子构建 |
| `idfgenx/data_factory/validate_official_corpus.py` | 实现副本哈希、官方转换和设计日仿真门禁 |
| `tests/unit/data_factory/` | 增加解析、范围、外部依赖、目录契约和完整性测试 |

## 3. 关键实现

- 不把 778 个官方 IDF 当作训练数据，只保留完整可检索清单；
- 用 12/20/25/11 四类显式 allowlist 代替仅依赖哈希的自动选择；
- 识别真实风水环、区级特殊设备、GroundDomain、EMS、插件、FMU 和外部数据文件；
- 语义哈希用于识别输出配置变体，几何哈希用于建立几何重复关联；
- 精选 manifest 中不存在 `duplicate_of` 标记，几何相同但事实不同的核心种子不会被误报为重复；
- 默认集合固定为 68 个，硬上限为 90 个；
- 官方文件不作 SFT 标签，后续训练标签只由 ScenarioSpec 和 Compiler 自动生成。

## 4. 验证证据

| 命令/检查 | 结果 | 备注 |
| --- | --- | --- |
| `python -m unittest discover -s tests -p "test_*.py" -v` | PASS | 15 项测试通过 |
| `python -m compileall -q idfgenx tests` | PASS | Python 语法通过 |
| 官方语料构建器 | PASS | 778 条 inventory、68 个精选 IDF |
| 精选副本 SHA-256 | PASS | 68/68 一致 |
| ConvertInputFormat | PASS | 32/32 核心种子成功转换 |
| EnergyPlus 设计日仿真 | PASS | 3 个简单 + 5 个复杂代表均无 Severe/Fatal |
| 目录检查 | PASS | JSON 仅在 `metadata/`，README 数量为 0 |

## 5. 数据和兼容性影响

新增 EnergyPlus v23.1 官方语料快照 schema `energyplus-official-corpus-1.0`。快照只面向 v23.1，不承诺跨版本直接复用；扩充名单必须重新生成 manifest 和 validation。

## 6. 未完成项与风险

本任务范围内无。几何参考可能包含项目永久不支持的真实 HVAC，因此已通过目录和 `selected_role=reference_geometry` 与核心种子隔离。

## 7. 后续任务

- `IDFGX-X-001`：补齐共享包配置和错误骨架；
- `IDFGX-M0-001`：冻结 ScenarioSpecDraft v0.1；
- `IDFGX-M0-010`：从 11 个官方模板中审核 Compiler v23.1 模板。

## 8. 关联记录

- Task：`docs/notes/idfgenx/tasks/IDFGX-M1-001-EnergyPlus官方语料快照.md`
- Dataset：`data/official_idf_v23_1/metadata/selected_manifest.jsonl`
- Validation：`data/official_idf_v23_1/metadata/validation.json`
