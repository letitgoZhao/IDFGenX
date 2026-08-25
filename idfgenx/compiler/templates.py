"""向 canonical epJSON 注入首版受控构造、负荷、温控和 IdealLoads 模板。"""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from idfgenx.compiler.naming import stable_name
from idfgenx.schemas.resolved import ResolvedScenarioSpec


def add_system_templates(document: dict[str, Any], spec: ResolvedScenarioSpec) -> dict[str, Any]:
    """返回添加确定性材料、构造、日程、负荷与 IdealLoads 的 epJSON 副本。"""

    result = deepcopy(document)
    result.update(_base_templates(spec))
    for zone_name in result["Zone"]:
        _add_zone_templates(result, zone_name, spec)
    return result


def _base_templates(spec: ResolvedScenarioSpec) -> dict[str, Any]:
    """创建所有 Zone 共用的最小可引用材料、构造和恒定日程。"""

    return {
        "Material": {
            "Generic Wall Material": {"roughness": "MediumSmooth", "thickness": 0.2, "conductivity": 0.8, "density": 1800.0, "specific_heat": 900.0},
            "Generic Floor Material": {"roughness": "MediumRough", "thickness": 0.25, "conductivity": 1.4, "density": 2200.0, "specific_heat": 900.0},
            "Generic Roof Material": {"roughness": "MediumSmooth", "thickness": 0.15, "conductivity": 0.04, "density": 30.0, "specific_heat": 1400.0},
        },
        "WindowMaterial:SimpleGlazingSystem": {"Generic Window Glazing": {"u_factor": 2.7, "solar_heat_gain_coefficient": 0.4, "visible_transmittance": 0.6}},
        "Construction": {
            "Wall Construction": {"outside_layer": "Generic Wall Material"},
            "Floor Construction": {"outside_layer": "Generic Floor Material"},
            "Roof Construction": {"outside_layer": "Generic Roof Material"},
            "Window Construction": {"outside_layer": "Generic Window Glazing"},
        },
        "ScheduleTypeLimits": {"Any Number": {}},
        "Schedule:Compact": {
            "Always On": _compact_schedule(1.0),
            "Heating Setpoint": _compact_schedule(spec.heating_setpoint_c),
            "Cooling Setpoint": _compact_schedule(spec.cooling_setpoint_c),
            "Control Type": _compact_schedule(4.0),
        },
    }


def _compact_schedule(value: float) -> dict[str, Any]:
    """构造符合 epJSON extensible 字段格式的全年恒定日程。"""

    return {
        "schedule_type_limits_name": "Any Number",
        "data": [
            {"field": "Through: 12/31"},
            {"field": "For: AllDays"},
            {"field": "Until: 24:00"},
            {"field": value},
        ],
    }


def _add_zone_templates(document: dict[str, Any], zone_name: str, spec: ResolvedScenarioSpec) -> None:
    """为一个 Zone 建立负荷、温控和 IdealLoads 设备连接引用链。"""

    short = stable_name("", zone_name).lstrip("-")
    document.setdefault("People", {})[f"People-{short}"] = {"zone_or_zonelist_or_space_or_spacelist_name": zone_name, "number_of_people_schedule_name": "Always On", "number_of_people_calculation_method": "People/Area", "people_per_floor_area": 0.05, "activity_level_schedule_name": "Always On"}
    document.setdefault("Lights", {})[f"Lights-{short}"] = {"zone_or_zonelist_or_space_or_spacelist_name": zone_name, "schedule_name": "Always On", "design_level_calculation_method": "Watts/Area", "watts_per_zone_floor_area": 8.0}
    document.setdefault("ElectricEquipment", {})[f"Equipment-{short}"] = {"zone_or_zonelist_or_space_or_spacelist_name": zone_name, "schedule_name": "Always On", "design_level_calculation_method": "Watts/Area", "watts_per_zone_floor_area": 10.0}
    dual = f"DualSetpoint-{short}"
    document.setdefault("ThermostatSetpoint:DualSetpoint", {})[dual] = {"heating_setpoint_temperature_schedule_name": "Heating Setpoint", "cooling_setpoint_temperature_schedule_name": "Cooling Setpoint"}
    thermostat = f"Thermostat-{short}"
    document.setdefault("ZoneControl:Thermostat", {})[thermostat] = {"zone_or_zonelist_name": zone_name, "control_type_schedule_name": "Control Type", "control_1_object_type": "ThermostatSetpoint:DualSetpoint", "control_1_name": dual}
    ideal = f"IdealLoads-{short}"
    document.setdefault("ZoneHVAC:IdealLoadsAirSystem", {})[ideal] = {"availability_schedule_name": "Always On", "zone_supply_air_node_name": f"Supply-{short}", "zone_exhaust_air_node_name": f"Exhaust-{short}", "heating_limit": "NoLimit", "cooling_limit": "NoLimit"}
    equipment = f"Equipment-{short}"
    document.setdefault("ZoneHVAC:EquipmentList", {})[equipment] = {"load_distribution_scheme": "SequentialLoad", "equipment": [{"zone_equipment_object_type": "ZoneHVAC:IdealLoadsAirSystem", "zone_equipment_name": ideal, "zone_equipment_cooling_sequence": 1, "zone_equipment_heating_or_no_load_sequence": 1}]}
    document.setdefault("ZoneHVAC:EquipmentConnections", {})[f"Connections-{short}"] = {"zone_name": zone_name, "zone_conditioning_equipment_list_name": equipment, "zone_air_inlet_node_or_nodelist_name": f"Supply-{short}", "zone_air_exhaust_node_or_nodelist_name": f"Exhaust-{short}", "zone_air_node_name": f"Air-{short}"}
