---
task_id: IDFGX-X-005
title: 消除前端 TypeScript 配置的外部 extends 依赖
module: X
status: done
owner: Codex
created: 2026-08-21
updated: 2026-08-21
depends_on:
  - IDFGX-SETUP-001
related_decisions: []
expected_report: docs/notes/idfgenx/reports/2026-08-21-IDFGX-X-005-前端TypeScript配置自包含.md
---

# IDFGX-X-005：前端 TypeScript 配置自包含

## 目标

消除 `tsconfig.app.json` 对 `@vue/tsconfig/tsconfig.dom.json` 的解析依赖，使 Vue/Vite 编译选项在仓库内完整可见，并解决未安装依赖时编辑器持续报告 extends 路径不存在的问题。

## 变更范围

- 将 Vue 3 + Vite 5 所需编译选项直接写入 `web/tsconfig.app.json`；
- 从 `package.json` 和 lockfile 移除不再使用的 `@vue/tsconfig`；
- 将触碰到的 TypeScript 配置注释改为中文；
- 不修改 `.gitignore`，不提交 `node_modules` 或 `dist`。

## 验收命令

```powershell
cd web
npm.cmd ci
npm.cmd run check
npm.cmd run build
```

## 完成标准

- [x] `tsconfig.app.json` 不再包含外部 `extends`；
- [x] package 与 lockfile 一致；
- [x] `vue-tsc -b` 通过；
- [x] Vite 生产构建通过；
- [x] 不遗留依赖目录或构建产物到 Git 变更中。
