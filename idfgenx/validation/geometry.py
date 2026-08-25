"""以独立向量计算检查 epJSON 建筑表面几何。"""

from __future__ import annotations

from math import sqrt
from typing import Any

from idfgenx.validation.models import Finding, StageReport, ValidationStatus


def validate_geometry(document: dict[str, Any]) -> StageReport:
    """执行 V3 非退化建筑表面检查。"""

    findings: list[Finding] = []
    surfaces = document.get("BuildingSurface:Detailed", {})
    for name, surface in surfaces.items():
        vertices = surface.get("vertices", [])
        if surface.get("outside_boundary_condition") == "Surface":
            peer_name = surface.get("outside_boundary_condition_object")
            peer = surfaces.get(peer_name)
            if peer is None or peer.get("outside_boundary_condition_object") != name:
                findings.append(Finding("V3_UNPAIRED_SURFACE", "内部表面没有双向配对。", {"surface": name, "peer": peer_name}))
            elif name < peer_name and not _has_opposed_normals(vertices, peer.get("vertices", [])):
                findings.append(
                    Finding(
                        "V3_INTERNAL_NORMAL_DIRECTION",
                        "成对内部表面的法向必须相反。",
                        {"surface": name, "peer": peer_name},
                    )
                )
        if len(vertices) < 3 or _polygon_area(vertices) <= 1e-9:
            findings.append(Finding("V3_DEGENERATE_SURFACE", "建筑表面退化或没有有效面积。", {"surface": name}))
    for name, window in document.get("FenestrationSurface:Detailed", {}).items():
        host_name = window.get("building_surface_name")
        host = surfaces.get(host_name)
        vertices = _fenestration_vertices(window)
        if host is not None and not _is_within_host(vertices, host.get("vertices", [])):
            findings.append(
                Finding(
                    "V3_WINDOW_OUTSIDE_HOST",
                    "窗户顶点没有完全位于宿主墙面内。",
                    {"window": name, "host_surface": host_name},
                )
            )
    return StageReport("V3", ValidationStatus.FAILED if findings else ValidationStatus.PASSED, tuple(findings))


def _polygon_area(vertices: list[dict[str, float]]) -> float:
    """用 Newell 法计算三维多边形面积，不依赖 Compiler 几何代码。"""

    normal = [0.0, 0.0, 0.0]
    for current, following in zip(vertices, vertices[1:] + vertices[:1], strict=True):
        x1, y1, z1 = current["vertex_x_coordinate"], current["vertex_y_coordinate"], current["vertex_z_coordinate"]
        x2, y2, z2 = following["vertex_x_coordinate"], following["vertex_y_coordinate"], following["vertex_z_coordinate"]
        normal[0] += (y1 - y2) * (z1 + z2)
        normal[1] += (z1 - z2) * (x1 + x2)
        normal[2] += (x1 - x2) * (y1 + y2)
    return sqrt(sum(component * component for component in normal)) / 2


def _fenestration_vertices(window: dict[str, Any]) -> list[dict[str, float]]:
    """从 v23.1 FenestrationSurface:Detailed 的扁平字段读取顶点。"""

    return [
        {
            "vertex_x_coordinate": window[f"vertex_{index}_x_coordinate"],
            "vertex_y_coordinate": window[f"vertex_{index}_y_coordinate"],
            "vertex_z_coordinate": window[f"vertex_{index}_z_coordinate"],
        }
        for index in range(1, int(window.get("number_of_vertices", 0)) + 1)
    ]


def _is_within_host(
    opening_vertices: list[dict[str, float]],
    host_vertices: list[dict[str, float]],
) -> bool:
    """检查开口顶点是否共面且位于四边形宿主的局部 [0, 1] 范围内。"""

    if len(opening_vertices) < 3 or len(host_vertices) != 4:
        return False
    origin = _point(host_vertices[0])
    horizontal = _subtract(_point(host_vertices[1]), origin)
    vertical = _subtract(_point(host_vertices[3]), origin)
    normal = _cross(horizontal, vertical)
    determinant = _dot(horizontal, horizontal) * _dot(vertical, vertical) - _dot(horizontal, vertical) ** 2
    if determinant <= 1e-12:
        return False
    normal_length = sqrt(_dot(normal, normal))
    for vertex in opening_vertices:
        relative = _subtract(_point(vertex), origin)
        if abs(_dot(relative, normal)) > 1e-6 * normal_length:
            return False
        horizontal_ratio = (_dot(relative, horizontal) * _dot(vertical, vertical) - _dot(relative, vertical) * _dot(horizontal, vertical)) / determinant
        vertical_ratio = (_dot(relative, vertical) * _dot(horizontal, horizontal) - _dot(relative, horizontal) * _dot(horizontal, vertical)) / determinant
        if not (-1e-6 <= horizontal_ratio <= 1 + 1e-6 and -1e-6 <= vertical_ratio <= 1 + 1e-6):
            return False
    return True


def _has_opposed_normals(
    first_vertices: list[dict[str, float]], second_vertices: list[dict[str, float]]
) -> bool:
    """判断两组相邻面顶点是否形成方向相反的非退化法向。"""

    first_normal = _newell_normal(first_vertices)
    second_normal = _newell_normal(second_vertices)
    first_length = sqrt(_dot(first_normal, first_normal))
    second_length = sqrt(_dot(second_normal, second_normal))
    return (
        first_length > 1e-9
        and second_length > 1e-9
        and _dot(first_normal, second_normal) / (first_length * second_length) < -0.999999
    )


def _newell_normal(vertices: list[dict[str, float]]) -> tuple[float, float, float]:
    """使用 Newell 法计算未归一化的三维多边形法向。"""

    normal = [0.0, 0.0, 0.0]
    for current, following in zip(vertices, vertices[1:] + vertices[:1], strict=True):
        x1, y1, z1 = _point(current)
        x2, y2, z2 = _point(following)
        normal[0] += (y1 - y2) * (z1 + z2)
        normal[1] += (z1 - z2) * (x1 + x2)
        normal[2] += (x1 - x2) * (y1 + y2)
    return (normal[0], normal[1], normal[2])


def _point(vertex: dict[str, float]) -> tuple[float, float, float]:
    """将 epJSON 顶点映射为验证器内部的三维向量。"""

    return (
        vertex["vertex_x_coordinate"],
        vertex["vertex_y_coordinate"],
        vertex["vertex_z_coordinate"],
    )


def _subtract(
    first: tuple[float, float, float], second: tuple[float, float, float]
) -> tuple[float, float, float]:
    """返回两个三维点的差向量。"""

    return tuple(first[index] - second[index] for index in range(3))  # type: ignore[return-value]


def _dot(
    first: tuple[float, float, float], second: tuple[float, float, float]
) -> float:
    """计算三维向量点积。"""

    return sum(first[index] * second[index] for index in range(3))


def _cross(
    first: tuple[float, float, float], second: tuple[float, float, float]
) -> tuple[float, float, float]:
    """计算三维向量叉积。"""

    return (
        first[1] * second[2] - first[2] * second[1],
        first[2] * second[0] - first[0] * second[2],
        first[0] * second[1] - first[1] * second[0],
    )
