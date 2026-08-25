"""EnergyPlus v23.1 设计日 V0–V6 集成测试。"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from idfgenx.compiler.compile import compile_scenario
from idfgenx.compiler.toolchain import EnergyPlusToolchain
from idfgenx.config import IDFGenXConfig
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import BuildingUse, ZoneLayout
from idfgenx.validation.service import validate_artifact


class ValidationSimulationIntegrationTests(unittest.TestCase):
    """确认真实 v23.1 设计日不会将 Compiler 产物留在 not_run 或失败状态。"""

    def test_single_zone_artifact_passes_all_quality_gates(self) -> None:
        """最小单区模型必须通过 V0–V6，且 V5 的 Severe/Fatal 均为零。"""

        spec = ResolvedScenarioSpec(
            building_name="Validation Integration",
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
        with TemporaryDirectory() as temporary_directory:
            work_dir = Path(temporary_directory)
            artifact = compile_scenario(spec, toolchain, work_dir)
            report = validate_artifact(artifact, spec, toolchain, work_dir)

        self.assertEqual(
            [(stage.stage, stage.status.value) for stage in report.stages],
            [
                ("V0", "passed"),
                ("V4", "passed"),
                ("V1", "passed"),
                ("V2", "passed"),
                ("V3", "passed"),
                ("V5", "passed"),
                ("V6", "passed"),
            ],
        )
