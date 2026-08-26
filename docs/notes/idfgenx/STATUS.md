# IDFGenX AI 开发当前状态

> 2026-08-26：`IDFGX-M0-017` 已按当前范围完成 Windows 代表样本可复现性验证。single/perimeter_core 均在独立工作目录的两次 Compiler 运行中通过 V0–V6，canonical epJSON、normalized IDF 哈希和阶段结论一致。Linux 与跨平台验证明确不在本任务范围，未作完成声明；下一项为 M1-004/M1-006。

> 2026-08-26：`IDFGX-M1-004` 已完成。S1–S5/C1–C5 场景桶、参数范围、训练资格与组合约束已冻结；C5 仅评估，unsupported feature 不进入正向 SFT。下一项为 M1-006 与 M1-005。

> 2026-08-25：`IDFGX-M0-016` 已完成。ADR-0001 冻结生产 Spec-LoRA 与 IDF 工件隔离；single/perimeter_core 的 epJSON→IDF→epJSON 语义 round-trip、metamorphic 与 mutation 稳定性测试均已通过。下一项为 M0-017 跨平台一致性验证。

> 2026-08-25：`IDFGX-M0-015` 已完成。Compiler Golden 已扩展至 100 项（single 50、perimeter_core 50），100/100 通过真实 EnergyPlus v23.1 设计日 V0–V6 验证；下一项为 M0-016 稳定性测试。

> 2026-08-25：`IDFGX-M0-013/014` 已完成。独立 V0–V6 Validator、20 个 MVP Golden 与 EnergyPlus v23.1 设计日门禁均已验证；全量 76/76 测试通过。后续进入 M0-015（100 Golden 扩展）。

> 更新时间：2026-08-26

## 当前阶段

Draft → ResolvedScenarioSpec → Resolver → Compiler 的 Windows 验证闭环已经完成。Compiler 从受控 ScenarioSpec 生成 EnergyPlus v23.1 可转换 IDF；100 Golden、V0–V6、稳定性和代表样本重复性均已有独立证据。下一阶段进入 M1 数据配置与 Prompt 契约。

## 活动任务

| 任务 | 状态 | 当前工作 | 下一出口 |
| --- | --- | --- | --- |
| 无 | 无 | M0 Windows Compiler 可复现性验证已结束 | 启动 M1-004 或 M1-006 |

## 下一批 Ready

| 任务 | 内容 | 前置条件 |
| --- | --- | --- |
| IDFGX-M1-004 | 冻结场景桶和约束 | M0-002 完成 |
| IDFGX-M1-006 | DisclosurePlan | M0-001/002 完成 |

## 当前阻塞

无。

## 已知风险

- `server/` 现有仿真/几何代码体量较大，迁移前必须先建立回归测试；
- 当前前端生产 bundle 约 1.9 MB，后期应在独立任务中做路由和 Three.js/ECharts 按需拆分；
- `docs/notes/idfgenx` 通过显式 force-add 纳入版本管理；父目录的其他本地笔记仍保持忽略；
- Compiler 与 Validator 不能共享所有几何计算逻辑，否则会出现相关性错误。

## 最近完成

- `IDFGX-M0-004 至 M0-012`：完成 v23.1 工具链、几何、窗洞、模板、canonical epJSON 与真实 IDF 转换；48/48 测试通过；
- `IDFGX-M0-003`：完成 Draft 到 SI-only ResolvedScenarioSpec 的确定性 Resolver；单位、默认值、派生值和失败边界均有测试；
- `IDFGX-M0-001`：冻结 Pydantic ScenarioSpecDraft v0.1，保留原始单位和字段状态；31/31 单测通过；
- `IDFGX-M0-002`：冻结仅含 SI 值的 ResolvedScenarioSpec v0.1，覆盖矩形、多层、分区与温控边界；34/34 单测通过；
- `IDFGX-M1-018`：规范目录迁移为 `data/selected_official_idfs`，新增中文 README；68/68 哈希、32/32 转换、8/8 仿真和 27/27 单测通过；
- `IDFGX-X-001`：新增统一配置、错误码和项目异常基类，固定 Python 3.11；9 项相关测试、全量 27/27 通过；
- `IDFGX-X-005`：前端 tsconfig 改为自包含配置，移除 `@vue/tsconfig`，类型检查和生产构建通过；
- `IDFGX-M1-001`：全量扫描 778 个官方 IDF，冻结 68 个精选文件；68/68 哈希、32/32 转换和 8/8 设计日仿真通过；
- `IDFGX-SETUP-002`：配置 uv Python 3.11.15、本地 EnergyPlus v23.1，并通过转换和设计日仿真 smoke；
- `IDFGX-SETUP-001`：建立 Git 代码基线、AI 总计划、任务/报告/ADR 工作流和项目规则；
- `c896d9b`：提交现有仿真与三维可视化代码基线并推送 `origin/main`；
- `2554e75`：新增根目录 AI 开发规则，并恢复原有 `.gitignore`；
- Python 语法编译、Vue 类型检查和 Vite 生产构建通过。
