"""V0–V6 总编排测试。"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from idfgenx.compiler.compile import CompilationArtifact
from idfgenx.compiler.toolchain import EnergyPlusToolchain
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import BuildingUse, ZoneLayout
from idfgenx.validation.service import validate_artifact


class ValidationServiceTests(unittest.TestCase):
    """失败工件不得继续进入对象、几何或仿真阶段。"""

    def test_stops_after_failed_artifact_contract(self) -> None:
        """V4 失败后，其余阶段必须明确为 not_run 而非伪造通过。"""

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            artifact = CompilationArtifact(root / "missing.epJSON", root / "missing.idf", "unused", "unused")
            report = validate_artifact(artifact, _spec(), _toolchain(root), root, run_simulation=False)

        self.assertEqual([(stage.stage, stage.status.value) for stage in report.stages], [("V0", "passed"), ("V4", "failed"), ("V1", "not_run"), ("V2", "not_run"), ("V3", "not_run"), ("V5", "not_run"), ("V6", "not_run")])


def _spec() -> ResolvedScenarioSpec:
    """返回服务编排所需的最小解析场景。"""

    return ResolvedScenarioSpec(
        building_name="Service",
        length_m=10,
        width_m=8,
        floor_to_floor_height_m=3,
        stories=1,
        zone_layout=ZoneLayout.SINGLE,
        window_to_wall_ratio=0.4,
        heating_setpoint_c=20,
        cooling_setpoint_c=26,
        building_use=BuildingUse.OFFICE,
    )


def _toolchain(root: Path) -> EnergyPlusToolchain:
    """构造不会运行外部进程的路径占位工具链。"""

    return EnergyPlusToolchain(root, root / "ConvertInputFormat.exe", root / "energyplus.exe", root / "Energy+.idd", root / "Energy+.schema.epJSON")
