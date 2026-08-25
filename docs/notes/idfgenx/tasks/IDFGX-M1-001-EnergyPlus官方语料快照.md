---
task_id: IDFGX-M1-001
title: 建立 EnergyPlus v23.1 一次性官方语料快照
module: M1
status: done
owner: Codex
created: 2026-08-21
updated: 2026-08-21
depends_on:
  - IDFGX-SETUP-002
related_decisions: []
expected_report: docs/notes/idfgenx/reports/2026-08-21-IDFGX-M1-001-EnergyPlus官方语料快照.md
---

# IDFGX-M1-001：建立 EnergyPlus v23.1 一次性官方语料快照

> 路径迁移：自 2026-08-25 起，本快照的规范位置为
> `data/selected_official_idfs`，见 `ADR-0001`。本文保留的旧路径用于记录
> 2026-08-21 的实际执行事实。

## 1. 背景

本机 EnergyPlus v23.1 包含 731 个 Example IDF 和 47 个 DataSet IDF。项目需要在自动标定前一次性保存有用、非重复、可追溯的官方模型，避免后续反复从安装目录人工挑选；同时必须隔离永久不支持的真实 HVAC 和其他超范围对象。

## 2. 目标

实现可复现扫描器，对全部官方 IDF 建立 inventory，筛选并复制本项目可用的简单/复杂模型、去重复杂几何参考和审核过的模板，生成许可证、哈希、分类理由和统计报告。

## 3. 非目标

- 不把全部 178 MB ExampleFiles 无差别复制；
- 不把真实 AirLoopHVAC/PlantLoop/设备拓扑作为训练候选；
- 不修改官方文件内容；
- 不把 geometry-only reference 当作 SFT 标签；
- 不生成 Prompt、ScenarioSpec 或正式数据 release；
- 不复制 EnergyPlus 可执行文件、IDD、schema 或天气文件。

## 4. 输出结构

```text
data/official_idf_v23_1/
├─ LICENSE.txt
├─ idf/
│  ├─ simple/                  # 12 个核心简单种子
│  ├─ complex/                 # 20 个核心复杂种子
│  ├─ geometry_references/     # 25 个仅供几何学习的参考
│  └─ templates/               # 11 个 DataSets 模板
└─ metadata/
   ├─ selection_policy.json
   ├─ inventory.jsonl
   ├─ selected_manifest.jsonl
   ├─ summary.json
   └─ validation.json
```

## 5. 筛选边界

### 正式模型候选

- 必须包含 `Zone` 和 `BuildingSurface:Detailed`；
- HVAC 必须为空、IdealLoads，或仅包含本项目允许的 Zone 连接/温控对象；
- 不含 AirLoopHVAC、PlantLoop、设备拓扑、EMS、PythonPlugin、FMU；
- 不依赖外部 Schedule/File、FMU 或插件文件；
- 不含 AirflowNetwork、GroundHeatTransfer 等首版超范围高级系统；
- 通过语义去重后保留一个代表。

### Geometry-only reference

- 必须有本项目尚未覆盖的有价值复杂几何、多区、遮阳或邻接；
- 即使包含不支持 HVAC，也只按 geometry hash 保留一个代表；
- 目录和 manifest 明确标记 `training_eligible=false`。

### DataSets 模板

只复制显式 allowlist 中的材料、构造、日程、节假日和窗材料/构造库；不复制 HVAC 设备、性能曲线、经济、制冷和环境影响数据。

## 6. 详细执行步骤

- [x] 统计 ExampleFiles/DataSets 数量、体积和许可证；
- [x] 实现无第三方依赖的 IDF 对象扫描器；
- [x] 为注释、对象解析、HVAC 范围、外部依赖和分类编写单元测试；
- [x] 计算 source/normalized/semantic/geometry SHA-256；
- [x] 全量扫描 731 个 Example IDF 和 47 个 DataSet IDF；
- [x] 对正式候选执行语义去重；
- [x] 对 geometry-only reference 执行几何去重；
- [x] 人工审核并固化 12/20/25/11 四类 allowlist；
- [x] 复制正式模型、参考模型、模板和许可证；
- [x] 验证目标文件哈希和 manifest 一致；
- [x] 对全部正式候选执行 ConvertInputFormat；
- [x] 抽取 simple/complex 代表执行最小设计日仿真；
- [x] 将全部 JSON 集中到 `metadata/`，不生成重复 README；
- [x] 生成 summary、validation 和执行报告。

## 7. 验证命令

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py"
.\.venv\Scripts\python.exe -m idfgenx.data_factory.official_corpus `
  --energyplus-root C:\EnergyPlusV23-1-0 `
  --output-root data\official_idf_v23_1
.\.venv\Scripts\python.exe -m idfgenx.data_factory.validate_official_corpus `
  --corpus-root data\official_idf_v23_1 `
  --energyplus-root C:\EnergyPlusV23-1-0
```

## 8. 完成标准

- [x] 731 个 Example IDF 全部有 inventory 记录；
- [x] 47 个 DataSet IDF 全部有 inventory 或 allowlist 结果；
- [x] 所有 68 个复制文件哈希与来源一致；
- [x] 32 个核心种子不含禁止对象和外部文件依赖；
- [x] semantic/geometry duplicate 有明确代表和映射；
- [x] 32 个核心种子 ConvertInputFormat 全部通过；
- [x] 3 个 simple、5 个 complex 代表最小仿真全部通过；
- [x] 许可证和 EnergyPlus v23.1 来源可追溯；
- [x] 精选集为 68 个且设置 90 个硬上限；
- [x] 以后无需再从安装目录人工搬运官方 IDF。
