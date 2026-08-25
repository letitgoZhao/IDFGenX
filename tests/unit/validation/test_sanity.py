"""V6 场景常识检查测试。"""

from __future__ import annotations

import unittest

from idfgenx.compiler.epjson import build_epjson
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import BuildingUse, ZoneLayout
from idfgenx.validation.sanity import validate_sanity


class SanityValidationTests(unittest.TestCase):
    """Zone 数必须匹配布局和层数。"""

    def test_rejects_wrong_single_zone_count(self) -> None:
        """单区两层应有两个 Zone，少一个必须失败。"""
        spec = ResolvedScenarioSpec(building_name="Test", length_m=10, width_m=8, floor_to_floor_height_m=3, stories=2, zone_layout=ZoneLayout.SINGLE, window_to_wall_ratio=0.4, heating_setpoint_c=20, cooling_setpoint_c=26, building_use=BuildingUse.OFFICE)
        report = validate_sanity({"Zone": {"Only": {}}}, spec)
        self.assertEqual(report.status.value, "failed")
        self.assertEqual(report.findings[0].code, "V6_ZONE_COUNT_MISMATCH")

    def test_rejects_wrong_floor_area(self) -> None:
        """Zone 面积汇总与 Spec 平面面积不一致必须失败。"""
        spec = ResolvedScenarioSpec(building_name="Test", length_m=10, width_m=8, floor_to_floor_height_m=3, stories=1, zone_layout=ZoneLayout.SINGLE, window_to_wall_ratio=0.4, heating_setpoint_c=20, cooling_setpoint_c=26, building_use=BuildingUse.OFFICE)
        report = validate_sanity({"Zone": {"Z": {}}, "BuildingSurface:Detailed": {}}, spec)
        self.assertEqual(report.status.value, "failed")
        self.assertEqual(report.findings[0].code, "V6_FLOOR_AREA_MISMATCH")

    def test_accepts_compiler_output(self) -> None:
        """完整单区 Compiler 输出的 Zone 与面积摘要必须一致。"""

        spec = _single_zone_spec()
        report = validate_sanity(build_epjson(spec), spec)

        self.assertEqual(report.status.value, "passed")

    def test_rejects_wrong_window_to_wall_ratio(self) -> None:
        """窗面积偏离场景 WWR 时必须给出可追踪的失败码。"""

        spec = _single_zone_spec()
        document = build_epjson(spec)
        window = next(iter(document["FenestrationSurface:Detailed"].values()))
        window["vertex_3_z_coordinate"] = window["vertex_2_z_coordinate"]

        report = validate_sanity(document, spec)

        self.assertEqual(report.status.value, "failed")
        self.assertTrue(
            any(finding.code == "V6_WINDOW_TO_WALL_RATIO_MISMATCH" for finding in report.findings)
        )

    def test_rejects_wrong_volume(self) -> None:
        """建筑表面围成的体积偏离场景尺寸时必须失败。"""

        spec = _single_zone_spec()
        document = build_epjson(spec)
        for surface in document["BuildingSurface:Detailed"].values():
            for vertex in surface.get("vertices", []):
                if vertex["vertex_z_coordinate"] == 3.0:
                    vertex["vertex_z_coordinate"] = 2.0

        report = validate_sanity(document, spec)

        self.assertEqual(report.status.value, "failed")
        self.assertTrue(any(finding.code == "V6_VOLUME_MISMATCH" for finding in report.findings))


def _single_zone_spec() -> ResolvedScenarioSpec:
    """创建用于 V6 摘要检查的最小合法单区场景。"""

    return ResolvedScenarioSpec(
        building_name="Sanity Validation",
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
