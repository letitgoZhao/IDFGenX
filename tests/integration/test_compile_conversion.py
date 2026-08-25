"""ResolvedSpec 到 EnergyPlus v23.1 IDF 的真实转换测试。"""

from __future__ import annotations

import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from idfgenx.compiler.compile import compile_scenario
from idfgenx.compiler.toolchain import EnergyPlusToolchain
from idfgenx.config import IDFGenXConfig
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import BuildingUse, ZoneLayout


class CompileConversionTests(unittest.TestCase):
    """验证 Compiler 用独占工作目录生成真实 v23.1 IDF。"""

    def test_compile_scenario_writes_canonical_epjson_and_converted_idf(self) -> None:
        """删除转换调用、写错输出路径或缺少模板引用都会使真实工具链失败。"""

        spec = ResolvedScenarioSpec(
            building_name="Office-Integration",
            length_m=10.0,
            width_m=8.0,
            floor_to_floor_height_m=3.0,
            stories=1,
            zone_layout=ZoneLayout.SINGLE,
            window_to_wall_ratio=0.4,
            heating_setpoint_c=20.0,
            cooling_setpoint_c=26.0,
            building_use=BuildingUse.OFFICE,
        )
        toolchain = EnergyPlusToolchain.from_config(
            IDFGenXConfig(energyplus_path=Path(r"C:\EnergyPlusV23-1-0"))
        )
        with TemporaryDirectory() as temp_dir:
            artifact = compile_scenario(spec, toolchain, Path(temp_dir))

            self.assertTrue(artifact.epjson_path.is_file())
            self.assertTrue(artifact.idf_path.is_file())
            self.assertEqual(artifact.idf_path.parent, Path(temp_dir))
            self.assertEqual(len(artifact.epjson_sha256), 64)
            self.assertEqual(len(artifact.idf_sha256), 64)


if __name__ == "__main__":
    unittest.main()
