---
task_id: IDFGX-SETUP-002
title: 配置 Windows 本地开发与 EnergyPlus v23.1 环境
module: SETUP
status: done
owner: Codex
created: 2026-08-21
updated: 2026-08-21
depends_on:
  - IDFGX-SETUP-001
related_decisions: []
expected_report: docs/notes/idfgenx/reports/2026-08-21-IDFGX-SETUP-002-本地开发环境.md
---

# IDFGX-SETUP-002：配置 Windows 本地开发与 EnergyPlus v23.1 环境

## 1. 背景

系统默认 Python 为 Anaconda 3.12.4，而项目确定使用 Python 3.11 和 uv。本机已安装 EnergyPlus v23.1，但空 `.env` 尚未向服务声明安装路径。

## 2. 目标

建立可复现的 `.venv` Python 3.11 环境，配置本地 EnergyPlus 路径，并验证 Python 依赖、EnergyPlus CLI/转换器/Python API 和 FastAPI 应用可用。

## 3. 非目标

- 不实现 ScenarioSpec、Compiler 或数据 Catalog；
- 不运行完整年度仿真；
- 不修改服务器 Miniconda 环境；
- 不开始 1K/10K 数据生产；
- 不覆盖任何已有非空密钥配置。

## 4. 影响文件

| 文件/目录 | 预期变更 |
| --- | --- |
| `.env` | 本地写入 `EPLUS_PATH`，保持 Git 忽略 |
| `.env.example` | 新增可公开的本地配置示例 |
| `.venv/` | uv 创建的 Python 3.11 环境，保持 Git 忽略 |
| `docs/notes/idfgenx/` | 更新任务、状态和环境报告 |

## 5. 详细执行步骤

- [x] 检查 uv、系统 Python、Node/npm；
- [x] 检查 `.env` 键，不输出任何值；
- [x] 检查 v23.1 CLI、ConvertInputFormat、IDD 和 Python API；
- [x] 安装 uv 管理的 Python 3.11；
- [x] 写入 `.env` 和 `.env.example`；
- [x] 执行 `uv sync`；
- [x] 验证 Python 3.11 和核心依赖导入；
- [x] 验证 EnergyPlus CLI/转换器版本；
- [x] 验证 `pyenergyplus.api` 和 `server.app` 导入；
- [x] 使用官方样本完成 epJSON 转换和最小设计日仿真；
- [x] 输出报告并更新状态；
- [x] 提交并推送可公开配置与任务记录。

## 6. 风险与回滚

| 风险 | 预防/检测 | 回滚方式 |
| --- | --- | --- |
| uv 误用系统 3.12 | 检查 `.venv` 的 `sys.version` | 删除并重建 `.venv` |
| pyenergyplus 不在 site-packages | 使用 `EPLUS_PATH` 注入官方 API 路径并验证 | 保留明确错误，不复制官方包 |
| `.env` 暴露敏感信息 | 只写公开安装路径，提交前检查 Git 状态 | `.env` 始终不提交 |
| 依赖与 Python 3.11 不兼容 | 严格按 `uv.lock` 安装并 smoke | 修订依赖任务，不临时跳过锁 |

## 7. 验证命令

```powershell
uv run python --version
uv run python -c "import fastapi, eppy, geomeppy; print('imports ok')"
uv run python -c "from server.app import app; print(app.title)"
& 'C:\EnergyPlusV23-1-0\energyplus.exe' --version
& 'C:\EnergyPlusV23-1-0\ConvertInputFormat.exe' --help
```

## 8. 完成标准

- [x] `.venv` 使用 Python 3.11；
- [x] `uv sync` 成功；
- [x] 核心 Python 依赖和 FastAPI app 可导入；
- [x] EnergyPlus v23.1 CLI、IDD、转换器和 Python API 可定位；
- [x] `.env` 未进入 Git；
- [x] 环境报告已输出；
- [x] 下一任务明确为 Schema/Compiler/Golden，而非盲目批量标定。

## 9. 结果

- 报告：`docs/notes/idfgenx/reports/2026-08-21-IDFGX-SETUP-002-本地开发环境.md`；
- Commit：包含本任务报告的后续提交。
