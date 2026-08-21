# IDFGenX AI 开发当前状态

> 更新时间：2026-08-21

## 当前阶段

Phase 0 工程基线和本地环境已经完成。下一步进入 `IDFGX-X-001`、`IDFGX-M0-001` 和 `IDFGX-M1-006`：先建立核心包，再冻结 ScenarioSpecDraft/ResolvedScenarioSpec 与 DisclosurePlan，为 20 个 Golden 标定样本建立稳定格式。

## 活动任务

当前没有 `in_progress` 任务。下一任务应从 `IDFGX-X-001` 开始；在其骨架稳定后实施 ScenarioSpec 与 Golden 标定格式。

## 下一批 Ready

| 任务 | 内容 | 前置条件 |
| --- | --- | --- |
| IDFGX-X-001 | 建立根目录 `idfgenx` 包与配置/错误骨架 | SETUP-001 完成 |
| IDFGX-M0-001 | ScenarioSpecDraft v0.1 | X-001 完成 |
| IDFGX-M0-002 | ResolvedScenarioSpec v0.1 | M0-001 完成 |
| IDFGX-M1-001 | 扫描 EnergyPlus v23.1 官方资产 | M0-004 工具链完成 |
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

- `IDFGX-SETUP-002`：配置 uv Python 3.11.15、本地 EnergyPlus v23.1，并通过转换和设计日仿真 smoke；
- `IDFGX-SETUP-001`：建立 Git 代码基线、AI 总计划、任务/报告/ADR 工作流和项目规则；
- `c896d9b`：提交现有仿真与三维可视化代码基线并推送 `origin/main`；
- `2554e75`：新增根目录 AI 开发规则，并恢复原有 `.gitignore`；
- Python 语法编译、Vue 类型检查和 Vite 生产构建通过。
