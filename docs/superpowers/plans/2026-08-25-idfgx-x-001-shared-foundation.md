# IDFGX-X-001 Shared Foundation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 建立 Python 3.11 下唯一的 IDFGenX 配置入口、稳定错误码和项目异常基类。

**Architecture:** `idfgenx.config` 只把显式环境映射规范化为不可变配置，不在导入时读取环境或访问文件系统；`idfgenx.errors` 只描述领域错误，不耦合 HTTP。包根导出稳定基础接口，现有 `server/` 迁移保留给后续任务。

**Tech Stack:** Python 3.11、标准库 `dataclasses`/`enum`/`pathlib`/`unittest`、uv。

**Spec:** `docs/notes/idfgenx/tasks/IDFGX-X-001-共享配置与错误骨架.md`

## Global Constraints

- Python 固定为 `>=3.11,<3.12`，依赖事实源是 `pyproject.toml` 和 `uv.lock`。
- 配置只识别 `EPLUS_PATH` 与 `ENERGYPLUS_VERSION`，EnergyPlus 首版固定 `23.1`。
- 公共类、函数和方法必须有中文 Google 风格 docstring 与完整类型。
- 配置导入不得读取环境、验证安装目录或启动外部进程。
- 错误对象不得包含 HTTP 状态码；FastAPI 映射由 M4 适配层负责。
- 不迁移或重构现有 `server/` 业务。

---

### Task 1: 统一错误码与项目异常

**Files:**
- Create: `idfgenx/errors.py`
- Create: `tests/unit/test_errors.py`
- Modify: `docs/notes/idfgenx/tasks/IDFGX-X-001-共享配置与错误骨架.md`

**Interfaces:**
- Consumes: Python 3.11 `StrEnum` 与 `Mapping[str, object]`。
- Produces: `ErrorCode`、`IDFGenXError`、`ConfigurationError`、`IDFGenXError.to_dict()`。

- [ ] **Step 1: 将任务状态改为进行中**

把任务 frontmatter 的 `status` 改为 `in_progress`，执行记录注明从 commit `5b7c67c` 的已批准设计开始。

- [ ] **Step 2: 编写错误接口失败测试**

创建 `tests/unit/test_errors.py`：

```python
"""IDFGenX 统一错误码和项目异常测试。"""

from __future__ import annotations

import unittest

from idfgenx.errors import ConfigurationError, ErrorCode, IDFGenXError


class IDFGenXErrorTests(unittest.TestCase):
    """验证领域错误保留稳定机器字段和原始原因。"""

    def test_base_error_preserves_payload_context_and_cause(self) -> None:
        cause = ValueError("bad input")
        error = IDFGenXError(
            ErrorCode.COMPILATION_FAILED,
            "编译失败",
            context={"sample_id": "sample-001"},
            cause=cause,
        )

        self.assertEqual(str(error), "编译失败")
        self.assertIs(error.__cause__, cause)
        self.assertEqual(
            error.to_dict(),
            {
                "code": "compilation_failed",
                "message": "编译失败",
                "context": {"sample_id": "sample-001"},
            },
        )

    def test_configuration_error_uses_configuration_code(self) -> None:
        error = ConfigurationError(
            "版本不受支持",
            context={"actual": "24.1", "expected": "23.1"},
        )

        self.assertEqual(error.code, ErrorCode.CONFIGURATION_INVALID)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 3: 运行测试并确认 RED**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.test_errors -v
```

Expected: FAIL，原因是 `idfgenx.errors` 尚不存在；不得因测试导入路径或语法错误失败。

- [ ] **Step 4: 实现最小错误骨架**

创建 `idfgenx/errors.py`，实现以下接口；所有公共对象补齐中文 docstring：

```python
from enum import StrEnum
from typing import Mapping


class ErrorCode(StrEnum):
    CONFIGURATION_INVALID = "configuration_invalid"
    SCHEMA_INVALID = "schema_invalid"
    RESOLUTION_FAILED = "resolution_failed"
    COMPILATION_FAILED = "compilation_failed"
    CONVERSION_FAILED = "conversion_failed"
    VALIDATION_FAILED = "validation_failed"
    SIMULATION_FAILED = "simulation_failed"
    EXTERNAL_PROCESS_TIMEOUT = "external_process_timeout"
    INTERNAL_ERROR = "internal_error"


class IDFGenXError(RuntimeError):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        context: Mapping[str, object] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.context = dict(context or {})
        if cause is not None:
            self.__cause__ = cause

    def to_dict(self) -> dict[str, object]:
        return {
            "code": self.code.value,
            "message": self.message,
            "context": dict(self.context),
        }


class ConfigurationError(IDFGenXError):
    def __init__(
        self,
        message: str,
        *,
        context: Mapping[str, object] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(
            ErrorCode.CONFIGURATION_INVALID,
            message,
            context=context,
            cause=cause,
        )
```

- [ ] **Step 5: 运行测试并确认 GREEN**

Run: `.\.venv\Scripts\python.exe -m unittest tests.unit.test_errors -v`

Expected: 2 tests，全部 PASS。

- [ ] **Step 6: 提交错误骨架**

```powershell
git add idfgenx/errors.py tests/unit/test_errors.py docs/notes/idfgenx/tasks/IDFGX-X-001-共享配置与错误骨架.md
git commit -m "feat(core): 建立统一错误骨架"
```

### Task 2: 不可变项目配置

**Files:**
- Create: `idfgenx/config.py`
- Create: `tests/unit/test_config.py`

**Interfaces:**
- Consumes: `ConfigurationError`、只读环境映射 `Mapping[str, str]`。
- Produces: `SUPPORTED_ENERGYPLUS_VERSION`、不可变 `IDFGenXConfig`、`load_config(environ)`。

- [ ] **Step 1: 编写配置加载失败测试**

创建 `tests/unit/test_config.py`：

```python
"""IDFGenX 统一配置加载测试。"""

from __future__ import annotations

import unittest
from pathlib import Path

from idfgenx.config import IDFGenXConfig, load_config
from idfgenx.errors import ConfigurationError, ErrorCode


class IDFGenXConfigTests(unittest.TestCase):
    """验证配置只接受规范变量并固定 EnergyPlus 版本。"""

    def test_load_config_normalizes_explicit_environment(self) -> None:
        config = load_config(
            {
                "EPLUS_PATH": r" C:\EnergyPlusV23-1-0 ",
                "ENERGYPLUS_VERSION": " 23.1 ",
                "ENERGYPLUS_HOME": r"C:\ignored",
            }
        )

        self.assertEqual(
            config,
            IDFGenXConfig(
                energyplus_path=Path(r"C:\EnergyPlusV23-1-0"),
                energyplus_version="23.1",
            ),
        )

    def test_missing_environment_uses_supported_version_without_path(self) -> None:
        config = load_config({})

        self.assertIsNone(config.energyplus_path)
        self.assertEqual(config.energyplus_version, "23.1")

    def test_unsupported_version_raises_stable_configuration_error(self) -> None:
        with self.assertRaises(ConfigurationError) as caught:
            load_config({"ENERGYPLUS_VERSION": "24.1"})

        self.assertEqual(caught.exception.code, ErrorCode.CONFIGURATION_INVALID)
        self.assertEqual(
            caught.exception.context,
            {"actual": "24.1", "expected": "23.1"},
        )


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试并确认 RED**

Run: `.\.venv\Scripts\python.exe -m unittest tests.unit.test_config -v`

Expected: FAIL，原因是 `idfgenx.config` 尚不存在。

- [ ] **Step 3: 实现最小配置入口**

创建 `idfgenx/config.py`，保持模块导入无副作用：

```python
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from idfgenx.errors import ConfigurationError

SUPPORTED_ENERGYPLUS_VERSION = "23.1"


@dataclass(frozen=True, slots=True)
class IDFGenXConfig:
    energyplus_path: Path | None
    energyplus_version: str = SUPPORTED_ENERGYPLUS_VERSION


def load_config(environ: Mapping[str, str] | None = None) -> IDFGenXConfig:
    source = os.environ if environ is None else environ
    raw_path = source.get("EPLUS_PATH", "").strip()
    raw_version = source.get(
        "ENERGYPLUS_VERSION", SUPPORTED_ENERGYPLUS_VERSION
    ).strip()
    if raw_version != SUPPORTED_ENERGYPLUS_VERSION:
        raise ConfigurationError(
            "EnergyPlus 版本不受支持。",
            context={
                "actual": raw_version,
                "expected": SUPPORTED_ENERGYPLUS_VERSION,
            },
        )
    return IDFGenXConfig(
        energyplus_path=Path(raw_path).expanduser() if raw_path else None,
        energyplus_version=raw_version,
    )
```

为模块、公共类和函数增加中文 Google 风格 docstring，说明这里只规范化配置，不检查路径存在性。

- [ ] **Step 4: 运行配置和错误测试并确认 GREEN**

Run:

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.test_config tests.unit.test_errors -v
```

Expected: 5 tests，全部 PASS。

- [ ] **Step 5: 提交配置入口**

```powershell
git add idfgenx/config.py tests/unit/test_config.py
git commit -m "feat(core): 新增统一项目配置"
```

### Task 3: 包出口与 Python 3.11 元数据

**Files:**
- Modify: `idfgenx/__init__.py`
- Modify: `pyproject.toml`
- Modify: `uv.lock`
- Create: `tests/unit/test_package_contract.py`

**Interfaces:**
- Consumes: Task 1–2 的基础类型。
- Produces: 包根稳定导出，以及 `>=3.11,<3.12` 的一致项目元数据。

- [ ] **Step 1: 编写包出口失败测试**

创建 `tests/unit/test_package_contract.py`：

```python
"""IDFGenX 包根公共接口测试。"""

from __future__ import annotations

import unittest

import idfgenx


class PackageContractTests(unittest.TestCase):
    """验证共享基础类型可从稳定包根导入。"""

    def test_shared_foundation_is_exported(self) -> None:
        self.assertIs(idfgenx.load_config, idfgenx.config.load_config)
        self.assertIs(idfgenx.IDFGenXError, idfgenx.errors.IDFGenXError)
        self.assertIn("IDFGenXConfig", idfgenx.__all__)
        self.assertIn("ErrorCode", idfgenx.__all__)


if __name__ == "__main__":
    unittest.main()
```

- [ ] **Step 2: 运行测试并确认 RED**

Run: `.\.venv\Scripts\python.exe -m unittest tests.unit.test_package_contract -v`

Expected: FAIL，原因是包根尚未导出 `load_config` 或异常类型。

- [ ] **Step 3: 更新包根导出**

在 `idfgenx/__init__.py` 显式导入 `config`、`errors` 以及 `IDFGenXConfig`、`load_config`、`ConfigurationError`、`ErrorCode`、`IDFGenXError`，并把这些名称与 `__version__` 写入 `__all__`。不得在包导入过程中调用 `load_config()`。

- [ ] **Step 4: 固定 Python 版本并同步锁文件**

将 `pyproject.toml` 改为：

```toml
requires-python = ">=3.11,<3.12"
```

Run:

```powershell
uv lock
uv lock --check
```

Expected: `uv.lock` 顶部 `requires-python` 与 Python 3.11 单版本策略一致，旧的 `<3.11`/`>=3.12` resolution markers 被移除。

- [ ] **Step 5: 运行局部与全量验证**

```powershell
.\.venv\Scripts\python.exe -m unittest tests.unit.test_package_contract tests.unit.test_config tests.unit.test_errors -v
.\.venv\Scripts\python.exe -m unittest discover -s tests -p "test_*.py" -v
.\.venv\Scripts\python.exe -m compileall -q idfgenx tests
```

Expected: 新增 6 项测试与现有 15 项测试全部 PASS，compileall 退出码 0。

- [ ] **Step 6: 提交包出口和元数据**

```powershell
git add idfgenx/__init__.py pyproject.toml uv.lock tests/unit/test_package_contract.py
git commit -m "chore(core): 固定Python 3.11包契约"
```

### Task 4: X-001 验收与执行报告

**Files:**
- Modify: `docs/notes/idfgenx/tasks/IDFGX-X-001-共享配置与错误骨架.md`
- Modify: `docs/notes/idfgenx/STATUS.md`
- Create: `docs/notes/idfgenx/reports/2026-08-25-IDFGX-X-001-共享配置与错误骨架.md`

**Interfaces:**
- Consumes: Tasks 1–3 的提交和验证输出。
- Produces: 可审计任务报告与 `done` 状态。

- [ ] **Step 1: 运行任务文件中的全部验收命令**

逐条运行局部单测、全量单测、compileall、`uv lock --check` 和 `git diff --check`，记录真实测试数量与退出码。

- [ ] **Step 2: 检查范围与敏感文件**

Run:

```powershell
git status --short
git diff --stat
git diff -- . ":(exclude)docs/notes/idfgenx"
```

确认没有 `.env`、`.venv`、缓存、模型、数据集或构建产物进入变更。

- [ ] **Step 3: 写执行报告并完成任务**

报告必须记录实际变更、测试结果、无 `server/` 迁移这一边界、兼容性和后续 `IDFGX-M0-001`。把任务 checklist 更新为完成、状态改为 `done`，并更新 `STATUS.md`。

- [ ] **Step 4: 提交报告闭环**

```powershell
git add docs/notes/idfgenx/tasks/IDFGX-X-001-共享配置与错误骨架.md docs/notes/idfgenx/STATUS.md docs/notes/idfgenx/reports/2026-08-25-IDFGX-X-001-共享配置与错误骨架.md
git commit -m "docs(core): 完成X-001执行闭环"
```
