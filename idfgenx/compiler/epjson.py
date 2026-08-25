"""将确定性几何转换为 EnergyPlus v23.1 canonical epJSON。"""

from __future__ import annotations

import json
from typing import Any

from idfgenx.compiler.fenestration import build_windows
from idfgenx.compiler.geometry import Surface, build_geometry
from idfgenx.schemas.resolved import ResolvedScenarioSpec


def build_epjson(spec: ResolvedScenarioSpec) -> dict[str, Any]:
    """构建包含版本、建筑、Zone、详细表面和外窗的 canonical epJSON 文档。"""

    geometry = build_geometry(spec)
    windows = build_windows(geometry, spec)
    document: dict[str, Any] = {
        "Version": {"Version 1": {"version_identifier": "23.1"}},
        "Building": {
            spec.building_name: {
                "north_axis": 0.0,
                "terrain": "City",
                "solar_distribution": "FullExterior",
            }
        },
        "GlobalGeometryRules": {
            "Geometry Rules": {
                "starting_vertex_position": "UpperLeftCorner",
                "vertex_entry_direction": "Counterclockwise",
                "coordinate_system": "World",
            }
        },
        "Zone": {zone.name: {} for zone in geometry.zones},
        "BuildingSurface:Detailed": {},
        "FenestrationSurface:Detailed": {},
    }
    surfaces = document["BuildingSurface:Detailed"]
    for zone in geometry.zones:
        for surface in zone.surfaces:
            surfaces[surface.name] = _surface_payload(surface)
    fenestrations = document["FenestrationSurface:Detailed"]
    for window in windows:
        payload: dict[str, Any] = {
            "surface_type": "Window",
            "construction_name": "Window Construction",
            "building_surface_name": window.host_surface_name,
            "number_of_vertices": 4,
        }
        for index, vertex in enumerate(window.vertices, start=1):
            payload[f"vertex_{index}_x_coordinate"] = vertex[0]
            payload[f"vertex_{index}_y_coordinate"] = vertex[1]
            payload[f"vertex_{index}_z_coordinate"] = vertex[2]
        fenestrations[window.name] = payload
    return document


def canonical_epjson_bytes(document: dict[str, Any]) -> bytes:
    """将 epJSON 序列化为排序键、固定缩进和末尾换行的 UTF-8 字节。"""

    return (json.dumps(document, ensure_ascii=False, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _surface_payload(surface: Surface) -> dict[str, Any]:
    """映射内部 Surface 为 v23.1 BuildingSurface:Detailed 字段。"""

    construction = {
        "Wall": "Wall Construction",
        "Floor": "Floor Construction",
        "Roof": "Roof Construction",
    }[surface.surface_type]
    if surface.outside_boundary_condition == "Surface":
        construction = "Internal Construction"
    payload: dict[str, Any] = {
        "surface_type": surface.surface_type,
        "construction_name": construction,
        "zone_name": surface.zone_name,
        "outside_boundary_condition": surface.outside_boundary_condition,
        "number_of_vertices": 4,
        "vertices": [_vertex_payload(vertex) for vertex in surface.vertices],
    }
    if surface.outside_boundary_condition_object:
        payload["outside_boundary_condition_object"] = surface.outside_boundary_condition_object
    if surface.outside_boundary_condition == "Outdoors":
        payload["sun_exposure"] = "SunExposed"
        payload["wind_exposure"] = "WindExposed"
    return payload


def _vertex_payload(vertex: tuple[float, float, float]) -> dict[str, float]:
    """将内部三元坐标映射为 v23.1 epJSON 顶点对象。"""

    return {
        "vertex_x_coordinate": vertex[0],
        "vertex_y_coordinate": vertex[1],
        "vertex_z_coordinate": vertex[2],
    }
