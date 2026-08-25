# M0-015：100 Golden 设计

## 目标

将现有 20 个 Compiler Golden 扩展至 100 个。每项均以 `ResolvedScenarioSpec` 为唯一输入，经真实 EnergyPlus v23.1 `ConvertInputFormat` 与设计日仿真后通过 V0–V6；不提交生成 IDF。

## 覆盖与组织

保持 `tests/golden/compiler/<case-id>/spec.json` 和 `expected.json` 的无 manifest 组织。保留现有 20 项，新增 80 项：40 个 single、40 个 perimeter_core，使总数各 50 项。

- single：覆盖 1/2/3/4 层、office/residential/classroom、WWR 0.2/0.4/0.6、方形与长宽比 1.25–4、不同层高。
- perimeter_core：覆盖 1/2/3 层、三种用途、WWR 0.2/0.4/0.6、核心深度 2–6 m、方形与长宽比 1.25–3。
- 所有尺寸保持在 `ResolvedScenarioSpec` 的合法范围，核心深度严格小于最短边的一半。

`expected.json` 固定 canonical epJSON SHA-256 与 Zone/Surface/Window 数量。Golden 测试发现恰好 100 个 fixture、布局各 50 个，并对每项执行真实 V0–V6 与期望摘要比较。

## 边界

不扩展 Schema、Compiler 支持域、真实 AirLoopHVAC/PlantLoop、全年天气仿真或跨平台验证。若新增候选触发 Compiler/Validator 缺陷，先写最小失败测试并修复；不得以移除样本或放宽门禁伪造通过。

## 验收

- 100/100 fixture，50 single、50 perimeter_core；
- 每项 V0–V6 都为 `passed`，V5 `.err` Severe=0、Fatal=0；
- 全量测试、`compileall`、`uv lock --check` 和 `git diff --check` 通过；
- 任务报告和项目状态更新完成。
