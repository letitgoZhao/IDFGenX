---
adr_id: ADR-0001
title: 精选官方 IDF 使用无版本规范目录名
status: accepted
date: 2026-08-25
owners:
  - IDFGenX
supersedes: null
superseded_by: null
---

# ADR-0001：精选官方 IDF 使用无版本规范目录名

## 背景

`data/official_idf_v23_1` 只复制了 68 个经审核的官方 IDF，并附带全量 inventory、选择策略和验证证据。名称中的 `official` 容易被理解为完整官方语料，版本后缀也会把资源版本固化在调用路径中。

## 决策

规范目录改为 `data/selected_official_idfs`，不保留旧目录副本或兼容别名。EnergyPlus `23.1`、快照边界、目录角色和使用限制记录在根 README 与现有元数据中。

目录名称使用复数名词和下划线：`selected` 表示内容已经经过人工名单与自动门禁筛选，`official_idfs` 表示来源和文件类型。名称不使用动作式 `select-official-idfs`，也不在路径中携带版本。

## 备选方案

| 方案 | 优点 | 缺点 | 未选择原因 |
| --- | --- | --- | --- |
| `selected_official_idfs` | 语义准确、符合现有下划线风格、路径稳定 | 版本需要读取 README/元数据 | 采用 |
| `official_idf_selection` | 能表达选择过程 | 更像构建工作区，不像冻结结果 | 不符合目录内容性质 |
| `select-official-idfs` | 接近最初提议 | 动作式、连字符风格不一致、像脚本名 | 不适合作为数据目录 |
| 保留 `official_idf_v23_1` | 无迁移成本 | 范围易误解，版本绑定路径 | 不符合新的可读性要求 |

## 影响

- 目录路径、测试参数和当前文档引用需要一次性迁移；
- 68 个 IDF、内部相对路径、manifest schema 和哈希不变；
- README 成为人类可读说明，metadata 继续是机器可读事实源；
- 历史 M1-001 记录保留原执行路径并补充迁移说明；
- 不影响模型、API、部署或 `data/releases` 协议。

## 验证与回退

迁移后必须验证旧目录不存在、新目录包含 68 个 IDF、manifest 中每个副本路径可解析且 68/68 SHA-256 一致；随后运行 32 个核心种子转换和全量单测。任一完整性门禁失败时，将目录和引用恢复到迁移前提交。

## 关联

- Task：`IDFGX-M1-018`
- Report：`docs/notes/idfgenx/reports/2026-08-25-IDFGX-M1-018-精选官方IDF目录迁移.md`
- 方案文档：`docs/notes/IDFGenX-M1-数据获取与标定.md`
