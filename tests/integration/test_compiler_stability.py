"""验证 Compiler 在格式往返、等价变换与受控破坏下的稳定性。"""

from __future__ import annotations

import json
from pathlib import Path
from subprocess import run
from tempfile import TemporaryDirectory
import unittest

from idfgenx.compiler.compile import CompilationArtifact, compile_scenario
from idfgenx.compiler.epjson import build_epjson, canonical_epjson_bytes
from idfgenx.compiler.toolchain import EnergyPlusToolchain
from idfgenx.config import IDFGenXConfig
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import BuildingUse, ZoneLayout
from idfgenx.validation.artifact import validate_artifact_contract
from idfgenx.validation.geometry import validate_geometry
from idfgenx.validation.service import validate_artifact


class CompilerStabilityTests(unittest.TestCase):
    """证明受支持场景的工件可往返、变换关系稳定且篡改可定位。"""

    @classmethod
    def setUpClass(cls) -> None:
        """构造固定的 EnergyPlus v23.1 工具链。"""

        cls.toolchain = EnergyPlusToolchain.from_config(
            IDFGenXConfig(energyplus_path=Path(r"C:\EnergyPlusV23-1-0"))
        )

    def test_epjson_idf_epjson_round_trip_preserves_canonical_document_and_v0_to_v6(
        self,
    ) -> None:
        """single 与 perimeter_core 经双向转换后保持规范 epJSON 与全量质量门禁。"""

        for spec in (_single_spec(), _perimeter_core_spec()):
            with self.subTest(layout=spec.zone_layout.value), TemporaryDirectory() as temporary_directory:
                work_dir = Path(temporary_directory)
                artifact = compile_scenario(spec, self.toolchain, work_dir)
                report = validate_artifact(artifact, spec, self.toolchain, work_dir)

                self.assertTrue(all(stage.status.value == "passed" for stage in report.stages))
                round_tripped_path = _convert_idf_to_epjson(artifact, self.toolchain, work_dir)
                original = json.loads(artifact.epjson_path.read_text(encoding="utf-8"))
                restored = json.loads(round_tripped_path.read_text(encoding="utf-8"))

                self.assertEqual(
                    canonical_epjson_bytes(_round_trip_semantic_document(restored)),
                    canonical_epjson_bytes(_round_trip_semantic_document(original)),
                )

    def test_metamorphic_name_wwr_and_story_changes_follow_declared_invariants(self) -> None:
        """命名不改变几何，WWR 面积单调，single 层数使对象计数线性扩展。"""

        named = _single_spec(building_name="Stability Name Variant")
        baseline_document = build_epjson(_single_spec())
        named_document = build_epjson(named)
        self.assertEqual(_summary(named_document), _summary(baseline_document))

        low_wwr_document = build_epjson(_single_spec(window_to_wall_ratio=0.2))
        high_wwr_document = build_epjson(_single_spec(window_to_wall_ratio=0.6))
        self.assertEqual(_summary(low_wwr_document), _summary(high_wwr_document))
        self.assertGreater(_window_area(high_wwr_document), _window_area(low_wwr_document))

        one_story_document = build_epjson(_single_spec(stories=1))
        three_story_document = build_epjson(_single_spec(stories=3))
        self.assertEqual(
            _summary(three_story_document),
            tuple(value * 3 for value in _summary(one_story_document)),
        )

    def test_mutation_reports_v4_hash_and_v3_window_host_failures(self) -> None:
        """工件字节篡改与窗越界必须分别触发 V4、V3 的稳定失败码。"""

        with TemporaryDirectory() as temporary_directory:
            work_dir = Path(temporary_directory)
            spec = _single_spec()
            artifact = compile_scenario(spec, self.toolchain, work_dir)
            artifact.epjson_path.write_bytes(artifact.epjson_path.read_bytes() + b"\n")

            artifact_report = validate_artifact_contract(artifact, spec)

            self.assertEqual(artifact_report.status.value, "failed")
            self.assertTrue(
                any(finding.code == "V4_EPJSON_HASH_MISMATCH" for finding in artifact_report.findings)
            )

            document = build_epjson(spec)
            window = next(iter(document["FenestrationSurface:Detailed"].values()))
            window["vertex_1_x_coordinate"] = -1.0
            geometry_report = validate_geometry(document)

            self.assertEqual(geometry_report.status.value, "failed")
            self.assertTrue(
                any(finding.code == "V3_WINDOW_OUTSIDE_HOST" for finding in geometry_report.findings)
            )


def _convert_idf_to_epjson(
    artifact: CompilationArtifact,
    toolchain: EnergyPlusToolchain,
    work_dir: Path,
) -> Path:
    """用同一 v23.1 工具把 IDF 转回独立目录中的 epJSON。"""

    output_dir = work_dir / "round_trip"
    output_dir.mkdir()
    completed = run(
        [str(toolchain.convert_input_format), "-o", str(output_dir), str(artifact.idf_path)],
        cwd=work_dir,
        text=True,
        capture_output=True,
        check=False,
    )
    expected = output_dir / "scenario.epJSON"
    if completed.returncode != 0 or not expected.is_file():
        raise AssertionError(
            f"IDF→epJSON 失败：return_code={completed.returncode}; stderr={completed.stderr[-500:]}"
        )
    return expected


def _round_trip_semantic_document(document: dict[str, object]) -> dict[str, object]:
    """规范 v23.1 在双向转换中自动重命名的无语义实例键。

    ConvertInputFormat 将 GlobalGeometryRules 和 ZoneHVAC:EquipmentConnections
    的对象名改成工具生成的序号。两类名称均不是本项目生成的引用目标；测试仅
    将这两类映射按载荷排序并改为固定键，其他对象名和所有字段仍逐字比较。
    """

    normalized = json.loads(json.dumps(document))
    for object_type in ("GlobalGeometryRules", "ZoneHVAC:EquipmentConnections"):
        objects = normalized.get(object_type, {})
        normalized[object_type] = {
            f"{object_type}-{index}": payload
            for index, payload in enumerate(
                sorted(
                    objects.values(),
                    key=lambda value: json.dumps(value, ensure_ascii=False, sort_keys=True),
                ),
                start=1,
            )
        }
    return normalized


def _summary(document: dict[str, object]) -> tuple[int, int, int]:
    """返回 Zone、表面和窗的对象数量，用于布局不变量。"""

    return tuple(
        len(document[object_type])  # type: ignore[index]
        for object_type in ("Zone", "BuildingSurface:Detailed", "FenestrationSurface:Detailed")
    )


def _window_area(document: dict[str, object]) -> float:
    """计算所有矩形窗面积，以确认 WWR 变换的单调关系。"""

    total = 0.0
    windows = document["FenestrationSurface:Detailed"]  # type: ignore[index]
    for window in windows.values():  # type: ignore[union-attr]
        points = [
            (
                window[f"vertex_{index}_x_coordinate"],
                window[f"vertex_{index}_y_coordinate"],
                window[f"vertex_{index}_z_coordinate"],
            )
            for index in range(1, 5)
        ]
        first = tuple(points[1][axis] - points[0][axis] for axis in range(3))
        second = tuple(points[3][axis] - points[0][axis] for axis in range(3))
        cross = (
            first[1] * second[2] - first[2] * second[1],
            first[2] * second[0] - first[0] * second[2],
            first[0] * second[1] - first[1] * second[0],
        )
        total += sum(component * component for component in cross) ** 0.5
    return total


def _single_spec(**changes: object) -> ResolvedScenarioSpec:
    """返回受支持 single 场景，并允许单项 metamorphic 变换。"""

    values: dict[str, object] = {
        "building_name": "Stability Single",
        "length_m": 18.0,
        "width_m": 12.0,
        "floor_to_floor_height_m": 3.2,
        "stories": 2,
        "zone_layout": ZoneLayout.SINGLE,
        "perimeter_depth_m": None,
        "window_to_wall_ratio": 0.4,
        "heating_setpoint_c": 20.0,
        "cooling_setpoint_c": 26.0,
        "building_use": BuildingUse.OFFICE,
    }
    values.update(changes)
    return ResolvedScenarioSpec(**values)


def _perimeter_core_spec() -> ResolvedScenarioSpec:
    """返回受支持 perimeter_core 场景，覆盖内部邻接与多区几何。"""

    return ResolvedScenarioSpec(
        building_name="Stability Perimeter Core",
        length_m=28.0,
        width_m=20.0,
        floor_to_floor_height_m=3.5,
        stories=2,
        zone_layout=ZoneLayout.PERIMETER_CORE,
        perimeter_depth_m=4.0,
        window_to_wall_ratio=0.4,
        heating_setpoint_c=20.0,
        cooling_setpoint_c=26.0,
        building_use=BuildingUse.CLASSROOM,
    )
