"""V2 引用闭合测试。"""

from __future__ import annotations

import unittest

from idfgenx.validation.references import validate_references


class ReferenceValidationTests(unittest.TestCase):
    """悬空 Zone 引用必须被明确拒绝。"""

    def test_rejects_surface_with_unknown_zone(self) -> None:
        """删除 Zone 声明会让建筑表面引用失效。"""

        report = validate_references({"Zone": {}, "BuildingSurface:Detailed": {"Wall": {"zone_name": "Missing Zone", "construction_name": "Wall Construction"}}, "Construction": {"Wall Construction": {}}})

        self.assertEqual(report.status.value, "failed")
        self.assertEqual(report.findings[0].code, "V2_UNKNOWN_ZONE")

    def test_rejects_window_with_unknown_host_surface(self) -> None:
        """删除窗宿主墙会留下不可转换的几何引用。"""

        report = validate_references({"Zone": {}, "Construction": {"Window Construction": {}}, "FenestrationSurface:Detailed": {"Window": {"building_surface_name": "Missing Wall", "construction_name": "Window Construction"}}})

        self.assertEqual(report.status.value, "failed")
        self.assertEqual(report.findings[0].code, "V2_UNKNOWN_HOST_SURFACE")

    def test_rejects_load_with_unknown_schedule(self) -> None:
        """内部负荷的日程引用必须闭合。"""

        report = validate_references({"Zone": {"Zone 1": {}}, "Schedule:Compact": {}, "People": {"People 1": {"zone_or_zonelist_or_space_or_spacelist_name": "Zone 1", "number_of_people_schedule_name": "Missing"}}})

        self.assertEqual(report.status.value, "failed")
        self.assertEqual(report.findings[0].code, "V2_UNKNOWN_SCHEDULE")

    def test_rejects_thermostat_with_unknown_setpoint(self) -> None:
        """温控器必须引用已声明的双设定点。"""
        report = validate_references({"ZoneControl:Thermostat": {"T": {"control_1_name": "Missing"}}, "ThermostatSetpoint:DualSetpoint": {}})
        self.assertEqual(report.status.value, "failed")
        self.assertEqual(report.findings[0].code, "V2_UNKNOWN_THERMOSTAT_SETPOINT")

    def test_rejects_connection_with_unknown_equipment_list(self) -> None:
        """设备连接必须引用已声明的 EquipmentList。"""
        report = validate_references({"Zone": {"Zone 1": {}}, "ZoneHVAC:EquipmentConnections": {"C": {"zone_name": "Zone 1", "zone_conditioning_equipment_list_name": "Missing"}}, "ZoneHVAC:EquipmentList": {}})
        self.assertEqual(report.status.value, "failed")
        self.assertEqual(report.findings[0].code, "V2_UNKNOWN_EQUIPMENT_LIST")

    def test_rejects_equipment_list_with_unknown_ideal_loads(self) -> None:
        """EquipmentList 不得指向未声明的 IdealLoads。"""
        report = validate_references({"ZoneHVAC:EquipmentList": {"List": {"equipment": [{"zone_equipment_object_type": "ZoneHVAC:IdealLoadsAirSystem", "zone_equipment_name": "Missing"}]}}, "ZoneHVAC:IdealLoadsAirSystem": {}})
        self.assertEqual(report.status.value, "failed")
        self.assertEqual(report.findings[0].code, "V2_UNKNOWN_IDEAL_LOADS")
