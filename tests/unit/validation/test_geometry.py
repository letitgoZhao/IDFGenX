"""V3 独立几何检查测试。"""

from __future__ import annotations

import unittest

from idfgenx.compiler.epjson import build_epjson
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import BuildingUse, ZoneLayout
from idfgenx.validation.geometry import validate_geometry


class GeometryValidationTests(unittest.TestCase):
    """验证退化建筑表面不会进入 Golden。"""

    def test_rejects_zero_area_surface(self) -> None:
        """四个共线顶点没有面积，必须被拒绝。"""

        report = validate_geometry({"BuildingSurface:Detailed": {"Degenerate": {"vertices": [{"vertex_x_coordinate": 0, "vertex_y_coordinate": 0, "vertex_z_coordinate": 0}, {"vertex_x_coordinate": 1, "vertex_y_coordinate": 0, "vertex_z_coordinate": 0}, {"vertex_x_coordinate": 2, "vertex_y_coordinate": 0, "vertex_z_coordinate": 0}, {"vertex_x_coordinate": 3, "vertex_y_coordinate": 0, "vertex_z_coordinate": 0}]}}})

        self.assertEqual(report.status.value, "failed")
        self.assertEqual(report.findings[0].code, "V3_DEGENERATE_SURFACE")

    def test_rejects_unpaired_internal_surface(self) -> None:
        """内部面必须由相邻 Zone 的对应面反向引用。"""
        report = validate_geometry({"BuildingSurface:Detailed": {"A": {"outside_boundary_condition": "Surface", "outside_boundary_condition_object": "Missing", "vertices": []}}})
        self.assertEqual(report.status.value, "failed")
        self.assertEqual(report.findings[0].code, "V3_UNPAIRED_SURFACE")

    def test_rejects_same_normal_internal_surface_pair(self) -> None:
        """相邻面互相引用但法向同向时，EnergyPlus 边界仍然无效。"""

        vertices = [
            {"vertex_x_coordinate": 0, "vertex_y_coordinate": 0, "vertex_z_coordinate": 0},
            {"vertex_x_coordinate": 1, "vertex_y_coordinate": 0, "vertex_z_coordinate": 0},
            {"vertex_x_coordinate": 1, "vertex_y_coordinate": 0, "vertex_z_coordinate": 1},
            {"vertex_x_coordinate": 0, "vertex_y_coordinate": 0, "vertex_z_coordinate": 1},
        ]
        report = validate_geometry(
            {
                "BuildingSurface:Detailed": {
                    "A": {
                        "outside_boundary_condition": "Surface",
                        "outside_boundary_condition_object": "B",
                        "vertices": vertices,
                    },
                    "B": {
                        "outside_boundary_condition": "Surface",
                        "outside_boundary_condition_object": "A",
                        "vertices": vertices,
                    },
                }
            }
        )

        self.assertEqual(report.status.value, "failed")
        self.assertTrue(any(finding.code == "V3_INTERNAL_NORMAL_DIRECTION" for finding in report.findings))

    def test_accepts_compiler_output(self) -> None:
        """独立检查器必须接受 Compiler 生成的有效单区几何。"""

        report = validate_geometry(build_epjson(_single_zone_spec()))

        self.assertEqual(report.status.value, "passed")

    def test_rejects_window_outside_host_surface(self) -> None:
        """窗户顶点落在宿主墙外时，不能通过几何质量门禁。"""

        document = build_epjson(_single_zone_spec())
        window = next(iter(document["FenestrationSurface:Detailed"].values()))
        window["vertex_1_x_coordinate"] = -1.0

        report = validate_geometry(document)

        self.assertEqual(report.status.value, "failed")
        self.assertTrue(
            any(finding.code == "V3_WINDOW_OUTSIDE_HOST" for finding in report.findings)
        )


def _single_zone_spec() -> ResolvedScenarioSpec:
    """创建用于几何验证的最小合法单区场景。"""

    return ResolvedScenarioSpec(
        building_name="Geometry Validation",
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
