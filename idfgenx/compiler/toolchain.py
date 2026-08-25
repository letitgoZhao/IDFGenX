"""发现并验证固定 EnergyPlus v23.1 本地工具链。"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from idfgenx.config import IDFGenXConfig
from idfgenx.errors import ConfigurationError


@dataclass(frozen=True, slots=True)
class EnergyPlusToolchain:
    """描述 Compiler 调用 v23.1 所需的本地可执行文件和规范资源。"""

    root: Path
    convert_input_format: Path
    energyplus: Path
    idd_path: Path
    epjson_schema_path: Path

    @classmethod
    def from_config(cls, config: IDFGenXConfig) -> EnergyPlusToolchain:
        """从统一配置构建经完整性检查的 EnergyPlus 工具链。

        Args:
            config: 仅允许 23.1 的项目基础配置。

        Returns:
            具有转换程序、IDD 和官方 epJSON Schema 的工具链。

        Raises:
            ConfigurationError: 未配置路径或安装目录缺少必须资源。
        """

        if config.energyplus_path is None:
            raise ConfigurationError("未配置 EPLUS_PATH，无法创建 Compiler 工具链。")
        root = config.energyplus_path
        required = {
            "convert_input_format": root / "ConvertInputFormat.exe",
            "energyplus": root / "energyplus.exe",
            "idd_path": root / "Energy+.idd",
            "epjson_schema_path": root / "Energy+.schema.epJSON",
        }
        missing = [name for name, path in required.items() if not path.is_file()]
        if missing:
            raise ConfigurationError(
                "EnergyPlus 安装不完整或路径不正确。",
                context={"root": str(root), "missing": missing},
            )
        return cls(root=root, **required)
