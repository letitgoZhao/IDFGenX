"""IDFGenX 统一配置加载测试。"""

from __future__ import annotations

import unittest
from pathlib import Path

from idfgenx.config import IDFGenXConfig, load_config
from idfgenx.errors import ConfigurationError, ErrorCode


class IDFGenXConfigTests(unittest.TestCase):
    """验证配置只接受规范变量并固定 EnergyPlus 版本。"""

    def test_load_config_normalizes_explicit_environment(self) -> None:
        """规范变量应去除外围空白，且同义变量不能覆盖它们。"""

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
        """未配置本机工具链时仍应得到可用于纯逻辑任务的配置。"""

        config = load_config({})

        self.assertIsNone(config.energyplus_path)
        self.assertEqual(config.energyplus_version, "23.1")

    def test_unsupported_version_raises_stable_configuration_error(self) -> None:
        """非 23.1 版本必须在进入 Compiler 前被稳定分类。"""

        with self.assertRaises(ConfigurationError) as caught:
            load_config({"ENERGYPLUS_VERSION": "24.1"})

        self.assertEqual(caught.exception.code, ErrorCode.CONFIGURATION_INVALID)
        self.assertEqual(
            caught.exception.context,
            {"actual": "24.1", "expected": "23.1"},
        )


if __name__ == "__main__":
    unittest.main()
