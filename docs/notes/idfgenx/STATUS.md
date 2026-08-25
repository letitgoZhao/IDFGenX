# IDFGenX AI 开发当前状态

> 更新时间：2026-08-25

## 当前阶段

Draft → ResolvedScenarioSpec → Resolver → Compiler 最小闭环已经完成。Compiler 从受控 ScenarioSpec 生成 EnergyPlus v23.1 可转换 IDF；Validator 与 Golden 仍是后续独立工作。

## 活动任务

| 任务 | 状态 | 当前工作 | 下一出口 |
| --- | --- | --- | --- |
| 无 | 无 | 本轮目标已在 Compiler 阶段结束 | 后续可独立启动 M0-013 Validator |

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
