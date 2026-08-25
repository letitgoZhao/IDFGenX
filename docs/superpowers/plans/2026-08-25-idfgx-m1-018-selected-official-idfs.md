# IDFGX-M1-018 Selected Official IDFs Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将精选 EnergyPlus 官方 IDF 快照迁移到无版本规范目录，并增加简洁中文目录说明而不改变数据内容或 manifest schema。

**Architecture:** 目录采用一次性原子式同盘移动，不保留旧副本；机器事实继续来自现有 metadata，README 只解释文件夹角色和使用限制。迁移前后使用 manifest SHA-256、完整官方验证器和回归测试证明数据不变。

**Tech Stack:** PowerShell、Python 3.11、标准库 `unittest`/`pathlib`、EnergyPlus v23.1 ConvertInputFormat 与设计日仿真。

**Spec:** `docs/notes/idfgenx/tasks/IDFGX-M1-018-精选官方IDF目录迁移.md`；命名决策见 `docs/notes/idfgenx/decisions/ADR-0001-selected-official-idfs-directory.md`。

## Global Constraints

- 唯一规范目录是 `data/selected_official_idfs`，不保留旧目录副本或兼容别名。
- EnergyPlus `23.1` 只写入 README 和 metadata，不进入目录名称。
- 不增加、删除或修改 68 个官方 IDF，不修改 `selected_manifest.jsonl` 字段和记录。
- README 只说明文件夹，不逐个叙述 IDF，也不复制 manifest。
- `geometry_references` 不作为正向 SFT 标签；正式标签只能由 ScenarioSpec 与 Compiler 生成。
- 目录移动前必须校验绝对源/目标均位于仓库 `data` 下，且目标不存在。

---

### Task 1: 新目录契约、安全迁移与 README

**Files:**
- Create: `tests/unit/data_factory/test_selected_official_idfs_layout.py`
- Move: `data/official_idf_v23_1/` → `data/selected_official_idfs/`
- Create: `data/selected_official_idfs/README.md`
- Modify: `docs/notes/idfgenx/tasks/IDFGX-M1-018-精选官方IDF目录迁移.md`

**Interfaces:**
- Consumes: `load_selected_manifest()`、`verify_copy_hashes()`、旧快照目录、68 条 manifest 与副本 SHA-256。
- Produces: 唯一规范目录、人类可读目录说明，以及 README 文案边界和 68 个副本完整性的回归门禁。

- [ ] **Step 1: 将任务状态改为进行中**

把任务 frontmatter 的 `status` 改为 `in_progress`，执行记录注明从 `ADR-0001` 和 commit `5b7c67c` 开始。

- [ ] **Step 2: 编写目录契约失败测试**

创建 `tests/unit/data_factory/test_selected_official_idfs_layout.py`：

```python
"""精选官方 IDF 规范目录、说明和快照完整性测试。"""

from __future__ import annotations

import unittest
from pathlib import Path

from idfgenx.data_factory.validate_official_corpus import (
    load_selected_manifest,
    verify_copy_hashes,
)


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
CORPUS_ROOT = REPOSITORY_ROOT / "data" / "selected_official_idfs"
OLD_CORPUS_ROOT = REPOSITORY_ROOT / "data" / "official_idf_v23_1"


class SelectedOfficialIdfsLayoutTests(unittest.TestCase):
    """验证精选快照只有一个规范位置且说明边界清晰。"""

    def test_only_canonical_corpus_directory_exists(self) -> None:
        self.assertTrue(CORPUS_ROOT.is_dir())
        self.assertFalse(OLD_CORPUS_ROOT.exists())

    def test_readme_documents_version_roles_and_training_boundary(self) -> None:
        readme = (CORPUS_ROOT / "README.md").read_text(encoding="utf-8")

        for expected in (
            "EnergyPlus v23.1",
            "idf/simple/",
            "idf/complex/",
            "idf/geometry_references/",
            "idf/templates/",
            "metadata/",
            "不作为正向 SFT 标签",
            "ScenarioSpec",
            "Compiler",
        ):
            with self.subTest(expected=expected):
                self.assertIn(expected, readme)

    def test_manifest_resolves_all_68_unchanged_copies(self) -> None:
        records = load_selected_manifest(CORPUS_ROOT)
        hash_results = verify_copy_hashes(CORPUS_ROOT, records)

        self.assertEqual(len(records), 68)
        self.assertEqual(len(list(CORPUS_ROOT.glob("idf/**/*.idf"))), 68)
        self.assertTrue(all(bool(result["passed"]) for result in hash_results))


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 运行测试并确认 RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_selected_official_idfs_layout -v
```

Expected: 目录契约测试因 `data/selected_official_idfs` 尚不存在而 FAIL；失败不能来自导入或语法错误。

- [ ] **Step 4: 验证绝对路径并在同一进程完成移动与哈希核对**

在一个 PowerShell 会话运行：

```powershell
$repositoryRoot = (Resolve-Path '.').Path
$dataRoot = (Resolve-Path 'data').Path
$sourceRoot = (Resolve-Path 'data\official_idf_v23_1').Path
$targetRoot = [System.IO.Path]::GetFullPath((Join-Path $dataRoot 'selected_official_idfs'))
if (-not $sourceRoot.StartsWith($dataRoot + [System.IO.Path]::DirectorySeparatorChar)) { throw '源目录不在仓库 data 下' }
if (-not $targetRoot.StartsWith($dataRoot + [System.IO.Path]::DirectorySeparatorChar)) { throw '目标目录不在仓库 data 下' }
if (Test-Path -LiteralPath $targetRoot) { throw '目标目录已存在' }
$before = Get-ChildItem -LiteralPath (Join-Path $sourceRoot 'idf') -Recurse -File -Filter '*.idf' | ForEach-Object { [PSCustomObject]@{ Relative=$_.FullName.Substring($sourceRoot.Length + 1); Hash=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } }
if ($before.Count -ne 68) { throw "迁移前 IDF 数量不是 68：$($before.Count)" }
Move-Item -LiteralPath $sourceRoot -Destination $targetRoot
$after = Get-ChildItem -LiteralPath (Join-Path $targetRoot 'idf') -Recurse -File -Filter '*.idf' | ForEach-Object { [PSCustomObject]@{ Relative=$_.FullName.Substring($targetRoot.Length + 1); Hash=(Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash } }
$beforeMap = @{}; $before | ForEach-Object { $beforeMap[$_.Relative] = $_.Hash }
$mismatches = $after | Where-Object { -not $beforeMap.ContainsKey($_.Relative) -or $beforeMap[$_.Relative] -ne $_.Hash }
if ($after.Count -ne 68 -or $mismatches.Count -ne 0) { throw '目录迁移后的 IDF 数量或 SHA-256 不一致' }
```

Expected: 源和目标均在 `D:\GithubProject\IDFGenX\data` 下；迁移前后均为 68 个 IDF；逐相对路径 SHA-256 全部一致；旧目录不存在。

- [ ] **Step 5: 使用 apply_patch 新增简洁中文 README**

创建 `data/selected_official_idfs/README.md`，正文固定为以下范围：

```markdown
# 精选官方 IDF

本目录保存从 EnergyPlus v23.1 官方 ExampleFiles 和 DataSets 中筛选的 68 个 IDF，用于 IDFGenX 的模板审核、几何研究和回归验证。文件保持官方原文；选择清单、哈希和验证证据位于 `metadata/`。

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
```

- [ ] **Step 6: 运行目录契约并确认 GREEN**

Run: `.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_selected_official_idfs_layout -v`

Expected: 3 tests，全部 PASS。

- [ ] **Step 7: 提交绿色目录迁移**

```powershell
git add -A -- data/official_idf_v23_1 data/selected_official_idfs tests/unit/data_factory/test_selected_official_idfs_layout.py docs/notes/idfgenx/tasks/IDFGX-M1-018-精选官方IDF目录迁移.md
git commit -m "refactor(data): 迁移精选官方IDF目录"
```

### Task 2: 更新受控文档引用与历史迁移说明

**Files:**
- Modify: `docs/notes/idfgenx/tasks/IDFGX-M1-001-EnergyPlus官方语料快照.md`
- Modify: `docs/notes/idfgenx/reports/2026-08-21-IDFGX-M1-001-EnergyPlus官方语料快照.md`
- Modify: `docs/notes/idfgenx/STATUS.md`
- Modify: `docs/notes/idfgenx/tasks/IDFGX-M1-018-精选官方IDF目录迁移.md`

**Interfaces:**
- Consumes: ADR-0001 和新规范路径。
- Produces: 当前状态只指向新路径，历史事实具有明确迁移链。

- [ ] **Step 1: 给 M1-001 历史任务和报告增加迁移说明**

在两个文件标题下增加：

```markdown
> 路径迁移：自 2026-08-25 起，本快照的规范位置为 `data/selected_official_idfs`，见 `ADR-0001`。本文保留的旧路径用于记录 2026-08-21 的实际执行事实。
```

不得把历史命令和“实际变更”表中的旧路径直接替换为新路径。

- [ ] **Step 2: 更新 STATUS 和 M1-018 执行记录**

把当前规范数据路径写入 `STATUS.md`；在 M1-018 执行记录中登记目录移动、68 个文件迁移前后哈希一致以及 README 范围。

- [ ] **Step 3: 扫描受控文件的旧路径引用**

```powershell
git grep -n "official_idf_v23_1" -- idfgenx tests docs/notes/idfgenx
```

Expected: 旧名称只允许出现在 ADR-0001、M1-018 迁移说明/测试常量以及 M1-001 历史任务和报告中；不得出现在当前默认路径或 README。

- [ ] **Step 4: 提交文档迁移链**

```powershell
git add docs/notes/idfgenx/tasks/IDFGX-M1-001-EnergyPlus官方语料快照.md docs/notes/idfgenx/reports/2026-08-21-IDFGX-M1-001-EnergyPlus官方语料快照.md docs/notes/idfgenx/STATUS.md docs/notes/idfgenx/tasks/IDFGX-M1-018-精选官方IDF目录迁移.md
git commit -m "docs(data): 记录精选IDF路径迁移"
```

### Task 3: 运行官方语料完整门禁

**Files:**
- Modify: `data/selected_official_idfs/metadata/validation.json`
- Modify: `docs/notes/idfgenx/tasks/IDFGX-M1-018-精选官方IDF目录迁移.md`

**Interfaces:**
- Consumes: 新目录、现有 manifest、本机 EnergyPlus v23.1。
- Produces: 68/68 哈希、32/32 转换和 8/8 设计日仿真证据。

- [ ] **Step 1: 运行局部与全量 Python 测试**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.data_factory.test_selected_official_idfs_layout -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
.\.venv\Scripts\python.exe -m compileall -q idfgenx tests
```

Expected: 新增 3 项与原有 15 项测试全部 PASS；compileall 退出码 0。

- [ ] **Step 2: 运行 EnergyPlus v23.1 完整验证器**

```powershell
.\.venv\Scripts\python.exe -m idfgenx.data_factory.validate_official_corpus --corpus-root data\selected_official_idfs --energyplus-root C:\EnergyPlusV23-1-0
```

Expected summary:

```json
{
  "conversion_passed": 32,
  "conversion_total": 32,
  "hash_passed": 68,
  "hash_total": 68,
  "passed": true,
  "simulation_passed": 8,
  "simulation_total": 8
}
```

- [ ] **Step 3: 检查验证报告和非预期产物**

读取 `data/selected_official_idfs/metadata/validation.json`，确认 summary 与控制台一致；运行 `git status --short`，确保临时转换和仿真目录已经清理。

- [ ] **Step 4: 提交验证证据**

```powershell
git add data/selected_official_idfs/metadata/validation.json docs/notes/idfgenx/tasks/IDFGX-M1-018-精选官方IDF目录迁移.md
git commit -m "test(data): 验证精选官方IDF迁移完整性"
```

### Task 4: M1-018 报告与状态闭环

**Files:**
- Modify: `docs/notes/idfgenx/tasks/IDFGX-M1-018-精选官方IDF目录迁移.md`
- Modify: `docs/notes/idfgenx/STATUS.md`
- Create: `docs/notes/idfgenx/reports/2026-08-25-IDFGX-M1-018-精选官方IDF目录迁移.md`

**Interfaces:**
- Consumes: Tasks 1–4 的提交与真实验证输出。
- Produces: 可审计报告、`done` 状态和下一步任务入口。

- [ ] **Step 1: 运行最终仓库检查**

```powershell
git diff --check
git status --short
git diff --stat HEAD~3..HEAD
git grep -n "selected_official_idfs" -- data idfgenx tests docs/notes/idfgenx
```

确认没有 `.env`、EnergyPlus 安装文件、缓存、依赖目录、模型或运行时临时文件进入 Git。

- [ ] **Step 2: 写执行报告并完成任务**

报告记录：目录迁移、README 范围、manifest schema 未变、68/68 哈希、32/32 转换、8/8 仿真、单测数量、风险和后续 `IDFGX-M0-001`。把 M1-018 checklist 更新为完成、状态改为 `done`，并更新 `STATUS.md` 的最近完成和下一步。

- [ ] **Step 3: 提交报告闭环**

```powershell
git add docs/notes/idfgenx/tasks/IDFGX-M1-018-精选官方IDF目录迁移.md docs/notes/idfgenx/STATUS.md docs/notes/idfgenx/reports/2026-08-25-IDFGX-M1-018-精选官方IDF目录迁移.md
git commit -m "docs(data): 完成M1-018执行闭环"
```
