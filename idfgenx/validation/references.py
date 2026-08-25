"""检查 Compiler 输出 epJSON 的关键对象引用。"""

from __future__ import annotations

from typing import Any

from idfgenx.validation.models import Finding, StageReport, ValidationStatus


def validate_references(document: dict[str, Any]) -> StageReport:
    """执行 V2 Zone 与构造引用闭合检查。"""

    findings: list[Finding] = []
    zones = set(document.get("Zone", {}))
    constructions = set(document.get("Construction", {}))
    surfaces = set(document.get("BuildingSurface:Detailed", {}))
    schedules = set(document.get("Schedule:Compact", {}))
    setpoints = set(document.get("ThermostatSetpoint:DualSetpoint", {}))
    equipment_lists = set(document.get("ZoneHVAC:EquipmentList", {}))
    ideal_loads = set(document.get("ZoneHVAC:IdealLoadsAirSystem", {}))
    for name, surface in document.get("BuildingSurface:Detailed", {}).items():
        if surface.get("zone_name") not in zones:
            findings.append(Finding("V2_UNKNOWN_ZONE", "建筑表面引用了不存在的 Zone。", {"surface": name, "zone_name": surface.get("zone_name")}))
        if surface.get("construction_name") not in constructions:
            findings.append(Finding("V2_UNKNOWN_CONSTRUCTION", "建筑表面引用了不存在的构造。", {"surface": name, "construction_name": surface.get("construction_name")}))
    for name, window in document.get("FenestrationSurface:Detailed", {}).items():
        if window.get("building_surface_name") not in surfaces:
            findings.append(Finding("V2_UNKNOWN_HOST_SURFACE", "窗引用了不存在的宿主建筑表面。", {"window": name, "building_surface_name": window.get("building_surface_name")}))
        if window.get("construction_name") not in constructions:
            findings.append(Finding("V2_UNKNOWN_CONSTRUCTION", "窗引用了不存在的构造。", {"window": name, "construction_name": window.get("construction_name")}))
    for object_type in ("People", "Lights", "ElectricEquipment", "ZoneHVAC:IdealLoadsAirSystem"):
        for name, item in document.get(object_type, {}).items():
            for field, value in item.items():
                if field.endswith("_schedule_name") and value and value not in schedules:
                    findings.append(Finding("V2_UNKNOWN_SCHEDULE", "对象引用了不存在的日程。", {"object_type": object_type, "name": name, "field": field, "schedule_name": value}))
    for name, thermostat in document.get("ZoneControl:Thermostat", {}).items():
        setpoint = thermostat.get("control_1_name")
        if setpoint not in setpoints:
            findings.append(Finding("V2_UNKNOWN_THERMOSTAT_SETPOINT", "温控器引用了不存在的双设定点。", {"thermostat": name, "control_1_name": setpoint}))
    for name, connection in document.get("ZoneHVAC:EquipmentConnections", {}).items():
        zone_name = connection.get("zone_name")
        if zone_name not in zones:
            findings.append(Finding("V2_UNKNOWN_ZONE", "设备连接引用了不存在的 Zone。", {"connection": name, "zone_name": zone_name}))
        equipment_list = connection.get("zone_conditioning_equipment_list_name")
        if equipment_list not in equipment_lists:
            findings.append(Finding("V2_UNKNOWN_EQUIPMENT_LIST", "设备连接引用了不存在的 EquipmentList。", {"connection": name, "equipment_list": equipment_list}))
    for name, equipment_list in document.get("ZoneHVAC:EquipmentList", {}).items():
        for item in equipment_list.get("equipment", []):
            if item.get("zone_equipment_object_type") == "ZoneHVAC:IdealLoadsAirSystem" and item.get("zone_equipment_name") not in ideal_loads:
                findings.append(Finding("V2_UNKNOWN_IDEAL_LOADS", "EquipmentList 引用了不存在的 IdealLoads。", {"equipment_list": name, "ideal_loads": item.get("zone_equipment_name")}))
    return StageReport("V2", ValidationStatus.FAILED if findings else ValidationStatus.PASSED, tuple(findings))
