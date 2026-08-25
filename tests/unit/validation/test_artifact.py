"""V0/V4 工件契约测试。"""

from __future__ import annotations

from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from idfgenx.compiler.compile import CompilationArtifact
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import BuildingUse, ZoneLayout
from idfgenx.validation.artifact import validate_artifact_contract


class ArtifactValidationTests(unittest.TestCase):
    """验证缺失或篡改的转换工件不会通过质量门禁。"""

    def test_contract_passes_for_existing_hashed_artifacts(self) -> None:
        """删除路径或改动任一字节都会使 V0/V4 失败。"""

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            epjson_path = root / "scenario.epJSON"
            idf_path = root / "scenario.idf"
            epjson_path.write_text('{"Version": {"Version 1": {"version_identifier": "23.1"}}}', encoding="utf-8")
            idf_path.write_text("Version,23.1;\n", encoding="utf-8")
            artifact = CompilationArtifact(epjson_path, idf_path, sha256(epjson_path.read_bytes()).hexdigest(), sha256(idf_path.read_bytes()).hexdigest())

            report = validate_artifact_contract(artifact, _spec())

            self.assertEqual(report.status.value, "passed")

    def test_contract_rejects_tampered_idf_hash(self) -> None:
        """篡改 IDF 后必须记录稳定 V4 哈希错误。"""

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            epjson_path = root / "scenario.epJSON"
            idf_path = root / "scenario.idf"
            epjson_path.write_text("{}", encoding="utf-8")
            idf_path.write_text("Version,23.1;\n", encoding="utf-8")
            artifact = CompilationArtifact(epjson_path, idf_path, sha256(epjson_path.read_bytes()).hexdigest(), sha256(idf_path.read_bytes()).hexdigest())
            idf_path.write_text("tampered", encoding="utf-8")

            report = validate_artifact_contract(artifact, _spec())

            self.assertEqual(report.status.value, "failed")
            self.assertEqual(report.findings[0].code, "V4_IDF_HASH_MISMATCH")


def _spec() -> ResolvedScenarioSpec:
    """返回最小有效 Compiler 输入。"""

    return ResolvedScenarioSpec(building_name="Validation", length_m=10, width_m=8, floor_to_floor_height_m=3, stories=1, zone_layout=ZoneLayout.SINGLE, window_to_wall_ratio=0.4, heating_setpoint_c=20, cooling_setpoint_c=26, building_use=BuildingUse.OFFICE)
