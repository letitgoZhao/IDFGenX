"""canonical epJSON 几何载荷测试。"""

from __future__ import annotations

import unittest

from idfgenx.compiler.epjson import build_epjson, canonical_epjson_bytes
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import BuildingUse, ZoneLayout


class EpJsonTests(unittest.TestCase):
    """验证对象、引用和 JSON 排序均可重复。"""

    def test_epjson_contains_v231_geometry_and_window_references(self) -> None:
        """丢失版本、Zone、宿主引用或表面顶点会使转换不可用。"""

        spec = ResolvedScenarioSpec(
            building_name="Office-EPJSON",
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

        document = build_epjson(spec)
        payload = canonical_epjson_bytes(document).decode("utf-8")

        self.assertEqual(document["Version"]["Version 1"]["version_identifier"], "23.1")
        self.assertEqual(len(document["Zone"]), 1)
        self.assertEqual(len(document["BuildingSurface:Detailed"]), 6)
        self.assertEqual(len(document["FenestrationSurface:Detailed"]), 4)
        surface = next(iter(document["BuildingSurface:Detailed"].values()))
        self.assertEqual(surface["number_of_vertices"], 4)
        self.assertEqual(
            set(surface["vertices"][0]),
            {"vertex_x_coordinate", "vertex_y_coordinate", "vertex_z_coordinate"},
        )
        self.assertTrue(all("building_surface_name" in item for item in document["FenestrationSurface:Detailed"].values()))
        window = next(iter(document["FenestrationSurface:Detailed"].values()))
        self.assertEqual(window["number_of_vertices"], 4)
        self.assertEqual(window["vertex_1_x_coordinate"], 0.2)
        self.assertNotIn("vertices", window)
        self.assertLess(payload.index('"Building"'), payload.index('"Zone"'))

    def test_interzone_surfaces_use_a_shared_symmetric_construction(self) -> None:
        """跨层 Roof/Floor 必须使用同一构造，避免 v23.1 报反向层错误。"""

        spec = ResolvedScenarioSpec(
            building_name="Office-Interzone",
            length_m=10.0,
            width_m=8.0,
            floor_to_floor_height_m=3.0,
            stories=2,
            zone_layout=ZoneLayout.SINGLE,
            window_to_wall_ratio=0.4,
            heating_setpoint_c=20.0,
            cooling_setpoint_c=26.0,
            building_use=BuildingUse.OFFICE,
        )
        document = build_epjson(spec)
        paired = [
            surface
            for surface in document["BuildingSurface:Detailed"].values()
            if surface["outside_boundary_condition"] == "Surface"
        ]

        self.assertEqual(len(paired), 2)
        self.assertTrue(all(surface["construction_name"] == "Internal Construction" for surface in paired))


if __name__ == "__main__":
    unittest.main()
