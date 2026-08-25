"""受控模板对象图测试。"""

from __future__ import annotations

import unittest

from idfgenx.compiler.epjson import build_epjson
from idfgenx.compiler.templates import add_system_templates
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import BuildingUse, ZoneLayout


class TemplateTests(unittest.TestCase):
    """验证每个 Zone 都得到闭合的构造、温控和 IdealLoads 引用。"""

    def test_templates_add_materials_constructions_and_ideal_loads_per_zone(self) -> None:
        """删除任一引用层会使表面或 ZoneHVAC 对象图断开。"""

        spec = ResolvedScenarioSpec(
            building_name="Office-Templates",
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
        document = add_system_templates(build_epjson(spec), spec)

        self.assertIn("Wall Construction", document["Construction"])
        self.assertIn("Window Construction", document["Construction"])
        self.assertEqual(len(document["ZoneHVAC:IdealLoadsAirSystem"]), 1)
        self.assertEqual(len(document["ZoneControl:Thermostat"]), 1)
        self.assertEqual(len(document["People"]), 1)
        self.assertEqual(document["Schedule:Compact"]["Always On"]["data"][0], {"field": "Through: 12/31"})


if __name__ == "__main__":
    unittest.main()
