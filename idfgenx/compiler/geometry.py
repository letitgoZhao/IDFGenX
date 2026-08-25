"""生成首版矩形建筑的绝对坐标 Zone 与详细表面。

坐标系为右手系米单位：x 为长度、y 为宽度、z 向上。每个表面顶点从外侧观察为
逆时针，使其法向朝向室外或相邻 Zone；这一约定是 EnergyPlus 边界和窗几何的基础。
"""

from __future__ import annotations

from dataclasses import dataclass

from idfgenx.compiler.naming import stable_name
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import ZoneLayout


Vertex = tuple[float, float, float]


@dataclass(slots=True)
class Surface:
    """描述一个带确定性边界条件的四边形建筑表面。"""

    name: str
    surface_type: str
    zone_name: str
    vertices: tuple[Vertex, Vertex, Vertex, Vertex]
    outside_boundary_condition: str
    outside_boundary_condition_object: str = ""


@dataclass(slots=True)
class ZoneGeometry:
    """描述一个热区及其全部建筑表面。"""

    name: str
    floor_index: int
    surfaces: list[Surface]

    def surface_named(self, name: str) -> Surface:
        """按稳定名称返回 Zone 内表面，不存在时抛出 KeyError。"""

        for surface in self.surfaces:
            if surface.name == name:
                return surface
        raise KeyError(name)


@dataclass(frozen=True, slots=True)
class BuildingGeometry:
    """描述一个 ResolvedSpec 生成的所有 Zone 几何。"""

    zones: tuple[ZoneGeometry, ...]


def build_geometry(spec: ResolvedScenarioSpec) -> BuildingGeometry:
    """为首版支持的单区矩形建筑生成详细表面和楼层邻接。

    Args:
        spec: 完整且已规范化的 Compiler 输入。

    Returns:
        绝对坐标的 Zone 和详细表面集合。

    Raises:
        ValueError: 当前实现尚未处理 perimeter_core 分区。
    """

    if spec.zone_layout is ZoneLayout.SINGLE:
        zones = tuple(
            _build_single_zone(spec, floor_index)
            for floor_index in range(1, spec.stories + 1)
        )
    else:
        zones = tuple(
            zone
            for floor_index in range(1, spec.stories + 1)
            for zone in _build_perimeter_core_floor(spec, floor_index)
        )
    _pair_coincident_surfaces(zones)
    return BuildingGeometry(zones=zones)


def _build_single_zone(
    spec: ResolvedScenarioSpec,
    floor_index: int,
) -> ZoneGeometry:
    """生成一层单区盒体，所有顶点均使用绝对坐标。"""

    zone_name = stable_name("Zone", f"F{floor_index:02d}", "Single")
    z0 = (floor_index - 1) * spec.floor_to_floor_height_m
    z1 = floor_index * spec.floor_to_floor_height_m
    x1 = spec.length_m
    y1 = spec.width_m
    surfaces = [
        _surface(zone_name, "Floor", "Floor", ((0.0, 0.0, z0), (0.0, y1, z0), (x1, y1, z0), (x1, 0.0, z0)), "Ground"),
        _surface(zone_name, "Roof", "Roof", ((0.0, 0.0, z1), (x1, 0.0, z1), (x1, y1, z1), (0.0, y1, z1)), "Outdoors"),
        _surface(zone_name, "South", "Wall", ((0.0, 0.0, z0), (x1, 0.0, z0), (x1, 0.0, z1), (0.0, 0.0, z1)), "Outdoors"),
        _surface(zone_name, "East", "Wall", ((x1, 0.0, z0), (x1, y1, z0), (x1, y1, z1), (x1, 0.0, z1)), "Outdoors"),
        _surface(zone_name, "North", "Wall", ((x1, y1, z0), (0.0, y1, z0), (0.0, y1, z1), (x1, y1, z1)), "Outdoors"),
        _surface(zone_name, "West", "Wall", ((0.0, y1, z0), (0.0, 0.0, z0), (0.0, 0.0, z1), (0.0, y1, z1)), "Outdoors"),
    ]
    return ZoneGeometry(name=zone_name, floor_index=floor_index, surfaces=surfaces)


def _build_perimeter_core_floor(
    spec: ResolvedScenarioSpec,
    floor_index: int,
) -> tuple[ZoneGeometry, ...]:
    """将每层划分为核心、边带和角区，保证所有内部面完整配对。"""

    depth = spec.perimeter_depth_m
    if depth is None:
        raise ValueError("perimeter_core 分区缺少已解析的核心深度。")
    x_ranges = ((0.0, depth), (depth, spec.length_m - depth), (spec.length_m - depth, spec.length_m))
    y_ranges = ((0.0, depth), (depth, spec.width_m - depth), (spec.width_m - depth, spec.width_m))
    labels = (("SouthWest", "South", "SouthEast"), ("West", "Core", "East"), ("NorthWest", "North", "NorthEast"))
    zones: list[ZoneGeometry] = []
    for y_index, (y0, y1) in enumerate(y_ranges):
        for x_index, (x0, x1) in enumerate(x_ranges):
            zones.append(_build_box(spec, floor_index, labels[y_index][x_index], x0, x1, y0, y1))
    return tuple(zones)


def _build_box(
    spec: ResolvedScenarioSpec,
    floor_index: int,
    label: str,
    x0: float,
    x1: float,
    y0: float,
    y1: float,
) -> ZoneGeometry:
    """为矩形子区生成六个绝对坐标详细表面。"""

    zone_name = stable_name("Zone", f"F{floor_index:02d}", label)
    z0 = (floor_index - 1) * spec.floor_to_floor_height_m
    z1 = floor_index * spec.floor_to_floor_height_m
    return ZoneGeometry(
        name=zone_name,
        floor_index=floor_index,
        surfaces=[
            _surface(zone_name, "Floor", "Floor", ((x0, y0, z0), (x0, y1, z0), (x1, y1, z0), (x1, y0, z0)), "Ground"),
            _surface(zone_name, "Roof", "Roof", ((x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)), "Outdoors"),
            _surface(zone_name, "South", "Wall", ((x0, y0, z0), (x1, y0, z0), (x1, y0, z1), (x0, y0, z1)), "Outdoors"),
            _surface(zone_name, "East", "Wall", ((x1, y0, z0), (x1, y1, z0), (x1, y1, z1), (x1, y0, z1)), "Outdoors"),
            _surface(zone_name, "North", "Wall", ((x1, y1, z0), (x0, y1, z0), (x0, y1, z1), (x1, y1, z1)), "Outdoors"),
            _surface(zone_name, "West", "Wall", ((x0, y1, z0), (x0, y0, z0), (x0, y0, z1), (x0, y1, z1)), "Outdoors"),
        ],
    )


def _surface(
    zone_name: str,
    suffix: str,
    surface_type: str,
    vertices: tuple[Vertex, Vertex, Vertex, Vertex],
    boundary_condition: str,
) -> Surface:
    """创建使用统一命名规则的详细表面。"""

    return Surface(
        name=stable_name("Surface", zone_name, suffix),
        surface_type=surface_type,
        zone_name=zone_name,
        vertices=vertices,
        outside_boundary_condition=boundary_condition,
    )


def _pair_vertical_adjacency(zones: tuple[ZoneGeometry, ...]) -> None:
    """将相邻楼层的上表面和下表面建立双向 Surface 引用。"""

    for lower, upper in zip(zones, zones[1:]):
        lower_roof = lower.surface_named(stable_name("Surface", lower.name, "Roof"))
        upper_floor = upper.surface_named(stable_name("Surface", upper.name, "Floor"))
        lower_roof.outside_boundary_condition = "Surface"
        lower_roof.outside_boundary_condition_object = upper_floor.name
        upper_floor.outside_boundary_condition = "Surface"
        upper_floor.outside_boundary_condition_object = lower_roof.name


def _pair_coincident_surfaces(zones: tuple[ZoneGeometry, ...]) -> None:
    """按同一组顶点配对全部内部墙、楼板与屋面，顶点方向可相反。"""

    candidates: dict[frozenset[Vertex], list[Surface]] = {}
    for zone in zones:
        for surface in zone.surfaces:
            candidates.setdefault(frozenset(surface.vertices), []).append(surface)
    for surfaces in candidates.values():
        if len(surfaces) != 2:
            continue
        first, second = surfaces
        first.outside_boundary_condition = "Surface"
        first.outside_boundary_condition_object = second.name
        second.outside_boundary_condition = "Surface"
        second.outside_boundary_condition_object = first.name
