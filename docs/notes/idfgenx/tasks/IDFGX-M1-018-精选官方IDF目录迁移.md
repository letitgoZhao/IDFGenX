---
task_id: IDFGX-M1-018
title: 迁移精选官方 IDF 目录并补充中文说明
module: M1
status: in_progress
owner: Codex
created: 2026-08-25
updated: 2026-08-25
depends_on:
  - IDFGX-M1-001
related_decisions:
  - ADR-0001
expected_report: docs/notes/idfgenx/reports/2026-08-25-IDFGX-M1-018-精选官方IDF目录迁移.md
---

# IDFGX-M1-018：迁移精选官方 IDF 目录并补充中文说明

## 1. 背景

`data/official_idf_v23_1` 实际保存的是经过 allowlist 审核和质量门禁的精选官方 IDF，而不是完整官方安装目录。现有名称容易让读者误解数据范围，并把 EnergyPlus 版本固化在路径中。

## 2. 目标

将唯一数据目录迁移为 `data/selected_official_idfs`，在根部用简洁中文说明版本、目录作用、选择理由和使用限制，同时保持 68 个官方 IDF 字节与 manifest 数据结构不变。

## 3. 非目标

- 不逐个解释 68 个 IDF；
- 不增加或删除精选文件；
- 不修改 `selected_manifest.jsonl` 的字段或记录；
- 不重新筛选、转换或修补官方 IDF；
- 不把几何参考升级为训练标签；
- 不修改 `data/releases`。

## 4. 输入与前置条件

- `IDFGX-M1-001` 已完成；
- 当前快照包含 68 个逐字节保留的 EnergyPlus v23.1 官方 IDF；
- 当前 manifest、哈希和角色分类验证通过；
- 目录命名决策见 `ADR-0001`。

## 5. 影响文件

| 文件/目录 | 预期变更 |
| --- | --- |
| `data/official_idf_v23_1/` | 整体迁移，不保留并行副本 |
| `data/selected_official_idfs/` | 成为唯一规范目录 |
| `data/selected_official_idfs/README.md` | 新增简洁中文目录说明 |
| `tests/unit/data_factory/` | 新增目录契约、README 和完整性回归测试 |
| `docs/notes/idfgenx/MASTER_PLAN.md` | 登记 M1-018 |
| `docs/notes/idfgenx/STATUS.md` | 登记任务进展和新规范路径 |
| M1-001 历史任务与报告 | 保留原执行事实，补充迁移说明和 ADR 链接 |

## 6. README 设计

根 README 只说明：

- 目录是 EnergyPlus v23.1 官方资源的精选快照；
- `idf/simple/` 用于最小建筑、基础对象和简单 Golden 参考；
- `idf/complex/` 用于复杂几何、采光、遮阳和对象组合回归；
- `idf/geometry_references/` 只供几何研究，可能含永久不支持的真实 HVAC，不作为正向 SFT 标签；
- `idf/templates/` 保存经审核的材料、构造、日程和窗系统候选；
- `metadata/` 保存 inventory、精选清单、策略、汇总和验证证据；
- 官方 IDF 保持原文，正式标签只能由 ScenarioSpec 与 Compiler 生成。

README 不复制 68 条 manifest，也不成为机器可读事实源。

## 7. 详细执行步骤

- [ ] 1. 先增加目录契约和 README 内容的失败测试；
- [ ] 2. 运行测试并确认旧路径/缺失 README 导致预期失败；
- [ ] 3. 验证旧目录绝对路径和新目录不存在后执行单次目录迁移；
- [ ] 4. 使用 `apply_patch` 新增中文 README；
- [ ] 5. 更新当前文档引用，并给历史任务/报告增加迁移说明；
- [ ] 6. 验证 68/68 副本哈希、32/32 核心转换和目录契约；
- [ ] 7. 运行现有全量单测和 Python 编译；
- [ ] 8. 检查 diff、敏感文件和非预期生成物；
- [ ] 9. 输出执行报告并更新任务与 `STATUS.md`。

## 8. 数据与接口变更

规范数据路径从 `data/official_idf_v23_1` 变为 `data/selected_official_idfs`。EnergyPlus 版本从路径移至 README 和现有元数据；内部 `idf/...` 相对路径、manifest schema 和 68 个 IDF 内容不变。不提供旧路径兼容副本。

## 9. 风险与回滚

| 风险 | 预防/检测 | 回滚方式 |
| --- | --- | --- |
| 遗漏旧路径引用 | 受控全仓库文本扫描 | 将目录移回并恢复引用 |
| 移动过程中复制或丢失文件 | 移动前后计数和 SHA-256 验证 | 从当前 Git 提交恢复旧目录 |
| README 被误认为训练许可 | 明确角色与禁止事项 | 修正文案，不改数据 |
| 历史报告被改写 | 只增加迁移注记 | 删除注记并保留 ADR 链接 |

## 10. 验证命令

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_selected_official_idfs_layout -v
.\.venv\Scripts\python.exe -m idfgenx.data_factory.validate_official_corpus --corpus-root data\selected_official_idfs --energyplus-root C:\EnergyPlusV23-1-0
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
.\.venv\Scripts\python.exe -m compileall -q idfgenx tests
git diff --check
```

## 11. 完成标准

- [ ] `data/selected_official_idfs` 是唯一规范目录，旧目录不存在；
- [ ] README 简洁说明版本、五类目录作用、选择理由和限制；
- [ ] 68 个 IDF 和 manifest 数据结构保持不变；
- [ ] 68/68 哈希、32/32 转换与全量单测通过；
- [ ] 当前引用已迁移，历史记录具有迁移说明；
- [ ] 报告已生成，任务与 `STATUS.md` 已更新。

## 12. 执行记录

- 2026-08-25：从 `ADR-0001` 和已批准设计 commit `5b7c67c` 开始实施；
  自动测试保护规范路径与快照完整性，README 人类文案采用交付审查，不写固定文本断言。
- 2026-08-25：迁移前后均为 68 个 IDF，工作区 SHA-256 不匹配为 0；发现旧
  `.gitattributes` 路径会在新位置暂存时规范化 CRLF，增加 Git clean filter
  回归测试并迁移 `-text` 规则后，68/68 新旧 Git blob 完全一致。
- 2026-08-25：新规范路径的完整门禁通过，结果为 68/68 哈希、32/32 转换、
  8/8 设计日仿真；全量 24 项单测和 Python 语法编译通过。

## 13. 结果

- 报告：`docs/notes/idfgenx/reports/2026-08-25-IDFGX-M1-018-精选官方IDF目录迁移.md`
- Commit/PR：待完成后填写
