# 精选官方 IDF

本目录保存从 EnergyPlus v23.1 官方 ExampleFiles 和 DataSets 中筛选的 68 个
IDF，用于 IDFGenX 的模板审核、几何研究和回归验证。文件保持官方原文；选择
清单、哈希和验证证据位于 `metadata/`。

## 目录说明

| 目录 | 作用与选择理由 |
| --- | --- |
| `idf/simple/` | 单区或基础建筑案例，结构清晰，适合最小 Compiler、Golden 和基础对象回归。 |
| `idf/complex/` | 包含多区、复杂表面、采光、遮阳或窗系统组合，用于复杂能力与对象引用回归。 |
| `idf/geometry_references/` | 保存有代表性的复杂几何，仅供几何研究；可能包含项目永久不支持的真实 HVAC，不作为正向 SFT 标签。 |
| `idf/templates/` | 保存经审核的材料、构造、日程和窗系统候选，供 Compiler 模板设计参考。 |
| `metadata/` | 保存全量 inventory、精选 manifest、选择策略、统计和质量门禁结果，是机器可读的追溯依据。 |

## 使用限制

- 官方 IDF 不是训练标签，不能原样加入正向 SFT；
- 生产标签只能由 `ScenarioSpec → Resolver → Compiler` 确定性生成；
- 扩充或替换文件时必须重新生成 manifest，并通过哈希、转换和最小仿真门禁。
