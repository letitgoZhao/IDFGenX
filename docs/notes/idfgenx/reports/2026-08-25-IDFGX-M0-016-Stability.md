# IDFGX-M0-016：Compiler 稳定性与训练工件隔离报告

日期：2026-08-25  
任务：IDFGX-M0-016  
状态：done

## 实际完成

- 接受 ADR-0001：生产 Spec-LoRA 训练记录只包含 Prompt→ScenarioSpecDraft，
  不含 IDF/epJSON 路径、文件名、内容、哈希或官方 IDF 外键。
- Direct-All/Direct-Fragment 被固定为独立论文基线，必须使用独立 release、
  模型和切分。
- 新增 3 项稳定性集成测试：
  - single 与 perimeter_core 的真实 epJSON→IDF→epJSON 语义 round-trip；
  - 建筑名无关性、WWR 面积单调性、single 楼层对象计数线性扩展；
  - epJSON 哈希篡改触发 `V4_EPJSON_HASH_MISMATCH`，窗顶点越界触发
    `V3_WINDOW_OUTSIDE_HOST`。

## Round-trip 说明

EnergyPlus v23.1 的 `ConvertInputFormat` 会自动重命名
`GlobalGeometryRules` 和 `ZoneHVAC:EquipmentConnections` 的实例键。
诊断确认两个对象的字段载荷完全相同；测试仅对这两类无语义实例键按载荷排序
并稳定重命名，其他对象键、引用和字段仍逐字比较。两个原始场景均通过真实
V0–V6 设计日验证。

## 验证证据

| 命令 | 结果 |
| --- | --- |
| `uv run python -m unittest tests.integration.test_compiler_stability -v` | 3/3 通过，2 个布局的真实 round-trip 与 V0–V6 |
| `uv run python -m unittest discover -v` | 79/79 通过，72.083 秒 |
| `uv run python -m compileall -q idfgenx tests` | 通过 |
| `uv lock --check` | 通过；50 包 |
| `git diff --check` | 通过 |

## 风险与后续

- 本次证据运行于 Windows 和 EnergyPlus v23.1；Linux 一致性仍由 M0-017
  负责验证。
- `docs/notes/IDFGenX-M1-数据获取与标定.md` 为未版本化本地笔记，未在
  本任务修改；ADR-0001 是可追踪的权威训练边界。
- 下一步：M0-017 跨平台一致性，然后按 ADR-0001 推进 M1 场景采样与
  Prompt→Draft 反向标定。

## 相关提交

- `4613437 docs(architecture): isolate spec lora from idf artifacts`
- `f81b93e test(validation): add compiler stability evidence`
