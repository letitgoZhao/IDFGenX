"""ResolvedScenarioSpec v0.1 的 Compiler 输入契约测试。"""

from __future__ import annotations

import unittest

from pydantic import ValidationError

from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import BuildingUse, ZoneLayout


class ResolvedScenarioSpecTests(unittest.TestCase):
    """验证 Compiler 输入只含完整、规范化且可生成几何的 SI 值。"""

    def test_single_zone_spec_serializes_explicit_si_values(self) -> None:
        """若 ResolvedSpec 保留原始单位或遗漏默认值，此测试应失败。"""

        spec = ResolvedScenarioSpec(
            building_name="Office-01",
            length_m=12.0,
            width_m=8.0,
            floor_to_floor_height_m=3.2,
            stories=2,
            zone_layout=ZoneLayout.SINGLE,
            window_to_wall_ratio=0.35,
            heating_setpoint_c=20.0,
            cooling_setpoint_c=26.0,
            building_use=BuildingUse.OFFICE,
        )

        self.assertEqual(
            spec.model_dump(mode="json"),
            {
                "schema_version": "0.1",
                "compiler_version": "0.1",
                "building_name": "Office-01",
                "length_m": 12.0,
                "width_m": 8.0,
                "floor_to_floor_height_m": 3.2,
                "stories": 2,
                "zone_layout": "single",
                "perimeter_depth_m": None,
                "window_to_wall_ratio": 0.35,
                "heating_setpoint_c": 20.0,
                "cooling_setpoint_c": 26.0,
                "building_use": "office",
            },
        )

    def test_perimeter_core_requires_a_fitting_positive_depth(self) -> None:
        """缺失或越界核心深度会导致几何退化，必须在 Compiler 前拒绝。"""

        common = {
            "building_name": "Office-02",
            "length_m": 20.0,
            "width_m": 16.0,
            "floor_to_floor_height_m": 3.5,
            "stories": 1,
            "zone_layout": ZoneLayout.PERIMETER_CORE,
            "window_to_wall_ratio": 0.4,
            "heating_setpoint_c": 20.0,
            "cooling_setpoint_c": 26.0,
            "building_use": BuildingUse.OFFICE,
        }

        with self.assertRaises(ValidationError):
            ResolvedScenarioSpec(**common)
        with self.assertRaises(ValidationError):
            ResolvedScenarioSpec(**common, perimeter_depth_m=8.0)

    def test_invalid_ranges_and_cross_field_temperature_order_are_rejected(self) -> None:
        """移除范围或温控排序检查会使不可能的 IDF 进入 Compiler。"""

        common = {
            "building_name": "Office-03",
            "length_m": 12.0,
            "width_m": 8.0,
            "floor_to_floor_height_m": 3.2,
            "stories": 1,
            "zone_layout": ZoneLayout.SINGLE,
            "window_to_wall_ratio": 0.35,
            "heating_setpoint_c": 20.0,
            "cooling_setpoint_c": 26.0,
            "building_use": BuildingUse.OFFICE,
        }

        with self.assertRaises(ValidationError):
            ResolvedScenarioSpec(**{**common, "length_m": 0.0})
        with self.assertRaises(ValidationError):
            ResolvedScenarioSpec(**{**common, "window_to_wall_ratio": 0.81})
        with self.assertRaises(ValidationError):
            ResolvedScenarioSpec(
                **{
                    **common,
                    "heating_setpoint_c": 27.0,
                    "cooling_setpoint_c": 26.0,
                }
            )


if __name__ == "__main__":
    unittest.main()
