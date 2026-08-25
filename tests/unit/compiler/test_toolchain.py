"""EnergyPlus v23.1 Toolchain 发现与边界测试。"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from idfgenx.compiler.toolchain import EnergyPlusToolchain
from idfgenx.config import IDFGenXConfig
from idfgenx.errors import ConfigurationError


class EnergyPlusToolchainTests(unittest.TestCase):
    """验证工具链只接受完整且固定版本的本地安装目录。"""

    def test_from_config_discovers_v231_cli_idd_schema_and_simulator(self) -> None:
        """丢失转换程序、IDD 或 epJSON Schema 时必须不能进入 Compiler。"""

        toolchain = EnergyPlusToolchain.from_config(
            IDFGenXConfig(energyplus_path=Path(r"C:\EnergyPlusV23-1-0"))
        )

        self.assertEqual(toolchain.root, Path(r"C:\EnergyPlusV23-1-0"))
        self.assertTrue(toolchain.convert_input_format.is_file())
        self.assertTrue(toolchain.idd_path.is_file())
        self.assertTrue(toolchain.epjson_schema_path.is_file())
        self.assertTrue(toolchain.energyplus.is_file())

    def test_from_config_rejects_incomplete_installation(self) -> None:
        """接受任意目录会让外部进程失败延迟到难以定位的转换阶段。"""

        with TemporaryDirectory() as temp_dir:
            with self.assertRaises(ConfigurationError):
                EnergyPlusToolchain.from_config(
                    IDFGenXConfig(energyplus_path=Path(temp_dir))
                )


if __name__ == "__main__":
    unittest.main()
