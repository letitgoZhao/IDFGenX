---
task_id: IDFGX-SETUP-001
title: 提交代码基线并建立 AI 工程工作流
module: SETUP
status: done
owner: Codex
created: 2026-08-21
updated: 2026-08-21
depends_on: []
related_decisions: []
expected_report: docs/notes/idfgenx/reports/2026-08-21-IDFGX-SETUP-001-仓库基线与AI工作流.md
---

# IDFGX-SETUP-001：提交代码基线并建立 AI 工程工作流

## 1. 背景

仓库当前只有 `.gitignore` 被 Git 跟踪，仿真、3D 和 Web 代码尚未形成代码基线；项目已有详细总体方案，但缺少 AI 可持续执行的任务、报告和规则闭环。

## 2. 目标

把现有可运行代码提交到 GitHub，并建立覆盖 M0–M5 的仓库内 AI 任务系统、执行报告和工业级 Python 注释规则。

## 3. 非目标

- 不实施 ScenarioSpec、Compiler 或数据工厂业务代码；
- 不重构现有大体量 Python/Vue 文件；
- 不提交 EnergyPlus 安装、论文 PDF、`.env`、数据和模型；
- 不解决当前前端 bundle 体积警告。

## 4. 影响文件

- 当前 `server/`、`web/`、Python/Node 依赖与锁文件；
- `.gitignore`；
- `AGENTS.md`；
- `docs/notes/idfgenx/`；
- `docs/notes/` 规划文档。

## 5. 执行步骤

- [x] 审计 Git 分支、远端、跟踪状态和敏感文件；
- [x] 补齐生成数据、模型、runtime、node_modules 和构建产物忽略；
- [x] 运行 Python 语法编译；
- [x] 安装前端锁定依赖并运行类型检查/生产构建；
- [x] 提交代码基线并推送 `origin/main`；
- [x] 安装官方 `obra/superpowers` 核心技能集；
- [x] 创建 `docs/notes/idfgenx/` 总计划、状态、任务、报告和 ADR 规则；
- [x] 创建 `AGENTS.md` 工业级注释和工程约束；
- [x] 在 `docs/notes/idfgenx/` 建立本地项目计划、任务和报告工作区；
- [x] 验证 Markdown、链接、Git diff 和敏感文件；
- [x] 生成执行报告，更新任务和状态；
- [x] 提交并推送工作流/规则。

## 6. 验证命令

```powershell
python -m compileall -q server
cd web
npm.cmd run check
npm.cmd run build
```

另外检查全部 Markdown fence、任务/报告链接、Git 暂存清单以及 `.env`/模型/数据是否未进入提交。

## 7. 完成标准

- [x] 当前代码基线在 `origin/main`；
- [x] M0–M5 均在 `MASTER_PLAN.md` 拆成可跟踪任务；
- [x] 任务和报告模板存在；
- [x] Python 注释和工程规则明确；
- [x] 工作流文件验证通过并进入提交；
- [x] 执行报告存在且任务状态为 `done`。

## 8. 结果

- 代码基线 commit：`c896d9b`；
- 报告：`docs/notes/idfgenx/reports/2026-08-21-IDFGX-SETUP-001-仓库基线与AI工作流.md`；
- 项目规则 commit：`2554e75`。
