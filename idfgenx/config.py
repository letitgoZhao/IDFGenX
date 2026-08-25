"""提供 IDFGenX 全项目唯一的基础配置入口。

本模块只把规范环境变量转换为带类型的不可变配置，不在导入时读取环境，也不检查
EnergyPlus 安装目录或可执行文件。实际工具链健康检查属于 M0 的进程适配边界。
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from idfgenx.errors import ConfigurationError


SUPPORTED_ENERGYPLUS_VERSION = "23.1"


@dataclass(frozen=True, slots=True)
class IDFGenXConfig:
    """保存跨数据、编译、验证和服务复用的基础配置。

    Attributes:
        energyplus_path: EnergyPlus 安装根目录；未配置时为 ``None``。
        energyplus_version: 项目允许使用的 EnergyPlus 主次版本。
    """

    energyplus_path: Path | None
    energyplus_version: str = SUPPORTED_ENERGYPLUS_VERSION


def load_config(environ: Mapping[str, str] | None = None) -> IDFGenXConfig:
    """从规范环境变量加载不可变项目配置。

    只识别 ``EPLUS_PATH`` 与 ``ENERGYPLUS_VERSION``。路径在此仅转换为
    :class:`~pathlib.Path`，不会检查其是否存在；版本必须保持项目首版固定的
    EnergyPlus 23.1。

    Args:
        environ: 可注入的只读环境映射；未提供时读取当前进程环境。

    Returns:
        已去除外围空白并完成版本约束检查的项目配置。

    Raises:
        ConfigurationError: 配置的 EnergyPlus 版本不是 23.1。
    """

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
