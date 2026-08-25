"""WWR 外窗几何契约测试。"""

from __future__ import annotations

import unittest

from idfgenx.compiler.fenestration import build_windows
from idfgenx.compiler.geometry import build_geometry
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import BuildingUse, ZoneLayout


class FenestrationTests(unittest.TestCase):
    """验证窗仅生成于外墙且严格位于宿主表面内。"""

    def test_windows_are_centered_on_exterior_walls_with_edge_clearance(self) -> None:
        """改变 WWR 面积、宿主平面或边界留量会使此真实几何断言失败。"""

        spec = ResolvedScenarioSpec(
            building_name="Office-Window",
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
        geometry = build_geometry(spec)
        windows = build_windows(geometry, spec)
        south = next(window for window in windows if window.host_surface_name.endswith("South"))

        self.assertEqual(len(windows), 4)
        self.assertEqual(
            south.vertices,
            ((0.2, 0.0, 0.875), (9.8, 0.0, 0.875), (9.8, 0.0, 2.125), (0.2, 0.0, 2.125)),
        )
        self.assertTrue(all(window.host_surface_name for window in windows))

    def test_internal_surfaces_do_not_receive_windows(self) -> None:
        """若对 Surface 边界开窗，会让相邻 Zone 的几何引用失效。"""

        spec = ResolvedScenarioSpec(
            building_name="Office-Core-Window",
            length_m=20.0,
            width_m=16.0,
            floor_to_floor_height_m=3.0,
            stories=1,
            zone_layout=ZoneLayout.PERIMETER_CORE,
            perimeter_depth_m=4.0,
            window_to_wall_ratio=0.4,
            heating_setpoint_c=20.0,
            cooling_setpoint_c=26.0,
            building_use=BuildingUse.OFFICE,
        )

        geometry = build_geometry(spec)
        windows = build_windows(geometry, spec)
        hosts = {
            surface.name
            for zone in geometry.zones
            for surface in zone.surfaces
            if surface.outside_boundary_condition == "Surface"
        }

        self.assertTrue(windows)
        self.assertFalse(any(window.host_surface_name in hosts for window in windows))


if __name__ == "__main__":
    unittest.main()
