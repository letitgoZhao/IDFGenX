"""检查 Compiler 支持域内的 epJSON 对象类型。"""

from __future__ import annotations

from typing import Any

from idfgenx.validation.models import Finding, StageReport, ValidationStatus


SUPPORTED_OBJECTS = frozenset({"Version", "Building", "GlobalGeometryRules", "Zone", "BuildingSurface:Detailed", "FenestrationSurface:Detailed", "Material", "WindowMaterial:SimpleGlazingSystem", "Construction", "ScheduleTypeLimits", "Schedule:Compact", "People", "Lights", "ElectricEquipment", "ThermostatSetpoint:DualSetpoint", "ZoneControl:Thermostat", "ZoneHVAC:IdealLoadsAirSystem", "ZoneHVAC:EquipmentList", "ZoneHVAC:EquipmentConnections"})


def validate_objects(document: dict[str, Any]) -> StageReport:
    """执行 V1 版本和受支持对象类型检查。"""

    findings: list[Finding] = []
    version = document.get("Version", {}).get("Version 1", {}).get("version_identifier")
    if version != "23.1":
        findings.append(Finding("V1_VERSION_INVALID", "epJSON 版本不是固定的 23.1。", {"actual": version}))
    for object_type in document:
        if object_type not in SUPPORTED_OBJECTS:
            findings.append(Finding("V1_UNSUPPORTED_OBJECT", "对象类型不在 Compiler 支持域内。", {"object_type": object_type}))
    return StageReport("V1", ValidationStatus.FAILED if findings else ValidationStatus.PASSED, tuple(findings))
