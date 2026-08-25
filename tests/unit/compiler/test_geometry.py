"""确定性矩形几何与命名器的契约测试。"""

from __future__ import annotations

import unittest

from idfgenx.compiler.geometry import build_geometry
from idfgenx.compiler.naming import stable_name
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import BuildingUse, ZoneLayout


def _single_zone_spec(*, stories: int = 1) -> ResolvedScenarioSpec:
    return ResolvedScenarioSpec(
        building_name="Office-01",
        length_m=10.0,
        width_m=8.0,
        floor_to_floor_height_m=3.0,
        stories=stories,
        zone_layout=ZoneLayout.SINGLE,
        window_to_wall_ratio=0.4,
        heating_setpoint_c=20.0,
        cooling_setpoint_c=26.0,
        building_use=BuildingUse.OFFICE,
    )


class NamingTests(unittest.TestCase):
    """验证 EnergyPlus 对象名在跨平台输入下稳定且无空白。"""

    def test_stable_name_normalizes_text_and_uses_fixed_parts(self) -> None:
        """改变替换规则或丢失序号会破坏对象引用与 Golden 可重复性。"""

        self.assertEqual(
            stable_name("Zone", "办公 楼/A", 2),
            "Zone-办公_楼_A-02",
        )


class GeometryTests(unittest.TestCase):
    """验证绝对坐标矩形 Zone 的面、顶点和楼层边界。"""

    def test_single_zone_rectangle_has_six_outward_surfaces(self) -> None:
        """错误面数或反转顶点顺序会破坏法向与后续边界条件。"""

        geometry = build_geometry(_single_zone_spec())
        zone = geometry.zones[0]
        surfaces = {surface.name: surface for surface in zone.surfaces}

        self.assertEqual(len(geometry.zones), 1)
        self.assertEqual(len(surfaces), 6)
        self.assertEqual(
            surfaces["Surface-Zone-F01-Single-Floor"].vertices,
            ((0.0, 0.0, 0.0), (0.0, 8.0, 0.0), (10.0, 8.0, 0.0), (10.0, 0.0, 0.0)),
        )
        self.assertEqual(
            surfaces["Surface-Zone-F01-Single-Roof"].vertices,
            ((0.0, 0.0, 3.0), (10.0, 0.0, 3.0), (10.0, 8.0, 3.0), (0.0, 8.0, 3.0)),
        )
        self.assertEqual(surfaces["Surface-Zone-F01-Single-South"].outside_boundary_condition, "Outdoors")

    def test_stacked_single_zones_pair_floor_and_roof_adjacency(self) -> None:
        """遗漏楼板配对会让多层模型错误地向室外散热。"""

        geometry = build_geometry(_single_zone_spec(stories=2))
        first_roof = geometry.zones[0].surface_named("Surface-Zone-F01-Single-Roof")
        second_floor = geometry.zones[1].surface_named("Surface-Zone-F02-Single-Floor")

        self.assertEqual(first_roof.outside_boundary_condition, "Surface")
        self.assertEqual(first_roof.outside_boundary_condition_object, second_floor.name)
        self.assertEqual(second_floor.outside_boundary_condition_object, first_roof.name)


if __name__ == "__main__":
    unittest.main()
