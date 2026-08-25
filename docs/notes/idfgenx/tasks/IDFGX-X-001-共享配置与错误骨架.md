---
task_id: IDFGX-X-001
title: 建立共享配置与错误骨架
module: X
status: done
owner: Codex
created: 2026-08-25
updated: 2026-08-25
depends_on:
  - IDFGX-SETUP-001
related_decisions: []
expected_report: docs/notes/idfgenx/reports/2026-08-25-IDFGX-X-001-共享配置与错误骨架.md
---

# IDFGX-X-001：建立共享配置与错误骨架

## 1. 背景

根目录 `idfgenx` 包已由 M1 官方语料任务建立，但尚缺全项目唯一的配置入口、统一错误码和项目异常基类。M0 Schema、Resolver、Compiler、Validator 以及后续服务层都依赖这些稳定边界。

## 2. 目标

建立最小、带类型且可单测的 `idfgenx.config` 与 `idfgenx.errors`，固定 Python 3.11 工程约束，为后续模块提供统一配置和错误表达。

## 3. 非目标

- 不迁移 `server/` 中现有 EnergyPlus、仿真或几何业务；
- 不实现 ScenarioSpec、Resolver、Compiler 或 Validator；
- 不检查 EnergyPlus 可执行文件或安装版本，工具链健康检查由 `IDFGX-M0-004` 实现；
- 不新增 Pydantic Settings 等第三方依赖；
- 不改变现有 FastAPI contract。

## 4. 输入与前置条件

- `IDFGX-SETUP-001` 已完成；
- 本地项目解释器为 Python 3.11；
- 配置只读取 `EPLUS_PATH` 和 `ENERGYPLUS_VERSION`，不接受同义环境变量；
- EnergyPlus 首版固定为 `23.1`。

## 5. 影响文件

| 文件/目录 | 预期变更 |
| --- | --- |
| `idfgenx/config.py` | 新增不可变配置模型和显式环境映射加载函数 |
| `idfgenx/errors.py` | 新增稳定错误码、项目异常基类和配置异常 |
| `idfgenx/__init__.py` | 只导出稳定的包版本和公共基础类型 |
| `tests/unit/test_config.py` | 覆盖路径解析、固定版本和环境隔离 |
| `tests/unit/test_errors.py` | 覆盖错误码、cause、上下文和序列化 |
| `pyproject.toml` | 将项目 Python 约束固定为 3.11 |
| `uv.lock` | 在项目元数据约束变化时同步锁文件 |

## 6. 接口设计

`idfgenx.config` 提供不可变 `IDFGenXConfig` 和 `load_config(environ)`。`environ` 可注入以保证测试不依赖宿主环境；未传入时读取当前进程环境。配置只负责规范化公开配置，不负责访问文件系统或启动外部进程。

`idfgenx.errors` 提供字符串枚举 `ErrorCode`、项目异常基类 `IDFGenXError` 和 `ConfigurationError`。异常保留稳定错误码、人类可读消息、结构化上下文和原始 cause；HTTP 映射留给 M4 适配层。

## 7. 详细执行步骤

- [x] 1. 先为配置加载和错误表达编写最小失败测试；
- [x] 2. 运行局部测试并确认因接口不存在而失败；
- [x] 3. 实现最小 `config.py` 和 `errors.py`；
- [x] 4. 固定 `pyproject.toml` Python 3.11 约束并同步锁文件；
- [x] 5. 运行局部测试、现有全量单测和 Python 编译；
- [x] 6. 检查公共 docstring、类型、diff 和敏感文件；
- [x] 7. 输出执行报告并更新任务与 `STATUS.md`。

## 8. 数据与接口变更

新增内部公共 Python 接口，不修改 API、ScenarioSpec、数据 manifest 或 EnergyPlus 文件。`server/` 后续迁移时只能通过 `idfgenx.config` 读取业务配置。

## 9. 风险与回滚

| 风险 | 预防/检测 | 回滚方式 |
| --- | --- | --- |
| 配置模块导入时访问宿主环境或文件系统 | 使用显式加载函数和注入环境测试 | 恢复为纯数据模型，移除导入副作用 |
| 错误码过早绑定 HTTP | 测试只验证领域错误，不引入状态码 | 删除 HTTP 相关字段 |
| Python 约束与锁文件不一致 | 运行 `uv lock --check` | 同步恢复 `pyproject.toml` 与 `uv.lock` |

## 10. 验证命令

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.test_config tests.unit.test_errors -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
.\.venv\Scripts\python.exe -m compileall -q idfgenx tests
uv lock --check
git diff --check
```

## 11. 完成标准

- [x] 配置和错误公共接口具有中文 Google 风格 docstring 与完整类型；
- [x] 配置只认项目规定的两个环境变量且无导入副作用；
- [x] EnergyPlus 非 `23.1` 配置产生稳定配置错误；
- [x] Python 项目约束固定为 3.11 且锁文件一致；
- [x] 新增测试和现有测试全部通过；
- [x] 报告已生成，任务与 `STATUS.md` 已更新。

## 12. 执行记录

- 2026-08-25：从已批准设计 commit `5b7c67c` 开始实施，使用隔离分支
  `feature/idfgx-x001-m1018`。
- 2026-08-25：三个 TDD 循环均先得到预期 RED，再实现 GREEN；局部 6 项、
  全量 21 项单测、compileall 与 uv 锁文件检查通过。
- 2026-08-25：代码审查后补充直接构造版本约束、波浪线路径宿主隔离和嵌套
  错误上下文防突变回归；3 项测试先 RED 后 GREEN，相关 9 项、全量 27 项
  单测通过。

## 13. 结果

- 报告：`docs/notes/idfgenx/reports/2026-08-25-IDFGX-X-001-共享配置与错误骨架.md`
- Commit：`08b8b1c`、`dacd157`、`b6f35d6`、`074af00`
