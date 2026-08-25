"""比较 epJSON 摘要与 ResolvedScenarioSpec 的独立常识门禁。"""

from __future__ import annotations

from typing import Any

from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import ZoneLayout
from idfgenx.validation.models import Finding, StageReport, ValidationStatus
from idfgenx.validation.geometry import _fenestration_vertices, _polygon_area


def validate_sanity(document: dict[str, Any], spec: ResolvedScenarioSpec) -> StageReport:
    """执行 V6 Zone 数量一致性检查。"""

    multiplier = 1 if spec.zone_layout is ZoneLayout.SINGLE else 9
    expected = spec.stories * multiplier
    actual = len(document.get("Zone", {}))
    findings: list[Finding] = []
    if actual != expected:
        findings.append(Finding("V6_ZONE_COUNT_MISMATCH", "epJSON Zone 数量与场景分区不一致。", {"expected": expected, "actual": actual}))
    floor_area = sum(_polygon_area(surface.get("vertices", [])) for surface in document.get("BuildingSurface:Detailed", {}).values() if surface.get("surface_type") == "Floor")
    expected_area = spec.length_m * spec.width_m * spec.stories
    if abs(floor_area - expected_area) > 1e-6:
        findings.append(Finding("V6_FLOOR_AREA_MISMATCH", "楼板面积与场景尺寸不一致。", {"expected": expected_area, "actual": floor_area}))
    all_vertices = [
        vertex
        for surface in document.get("BuildingSurface:Detailed", {}).values()
        for vertex in surface.get("vertices", [])
    ]
    actual_volume = _bounding_volume(all_vertices)
    expected_volume = expected_area * spec.floor_to_floor_height_m
    if abs(actual_volume - expected_volume) > 1e-6:
        findings.append(
            Finding(
                "V6_VOLUME_MISMATCH",
                "建筑表面顶点定义的包围体积与场景尺寸不一致。",
                {"expected": expected_volume, "actual": actual_volume},
            )
        )
    exterior_wall_area = sum(
        _polygon_area(surface.get("vertices", []))
        for surface in document.get("BuildingSurface:Detailed", {}).values()
        if surface.get("surface_type") == "Wall"
        and surface.get("outside_boundary_condition") == "Outdoors"
    )
    window_area = sum(
        _polygon_area(_fenestration_vertices(window))
        for window in document.get("FenestrationSurface:Detailed", {}).values()
    )
    actual_wwr = window_area / exterior_wall_area if exterior_wall_area else 0.0
    if abs(actual_wwr - spec.window_to_wall_ratio) > 1e-4:
        findings.append(
            Finding(
                "V6_WINDOW_TO_WALL_RATIO_MISMATCH",
                "窗面积与外墙面积之比偏离已解析场景的 WWR。",
                {"expected": spec.window_to_wall_ratio, "actual": actual_wwr},
            )
        )
    return StageReport("V6", ValidationStatus.PASSED if not findings else ValidationStatus.FAILED, tuple(findings))


def _bounding_volume(vertices: list[dict[str, float]]) -> float:
    """从 epJSON 顶点的三轴范围计算矩形 MVP 建筑的独立体积摘要。"""

    if not vertices:
        return 0.0
    x_values = [vertex["vertex_x_coordinate"] for vertex in vertices]
    y_values = [vertex["vertex_y_coordinate"] for vertex in vertices]
    z_values = [vertex["vertex_z_coordinate"] for vertex in vertices]
    return (max(x_values) - min(x_values)) * (max(y_values) - min(y_values)) * (max(z_values) - min(z_values))
