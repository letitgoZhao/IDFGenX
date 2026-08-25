"""在外墙局部坐标系中确定性生成 WWR 外窗。

窗的顶点沿用宿主详细表面的底边和竖边方向，因此无论外墙朝向如何，都保持与宿主
相同的法向约定。内部 `Surface` 边界不会生成开口。
"""

from __future__ import annotations

from dataclasses import dataclass

from idfgenx.compiler.geometry import BuildingGeometry, Surface, Vertex
from idfgenx.compiler.naming import stable_name
from idfgenx.schemas.resolved import ResolvedScenarioSpec


EDGE_CLEARANCE_M = 0.2


@dataclass(frozen=True, slots=True)
class Window:
    """描述嵌入一个外墙宿主表面的确定性四边形窗。"""

    name: str
    host_surface_name: str
    zone_name: str
    vertices: tuple[Vertex, Vertex, Vertex, Vertex]


def build_windows(
    geometry: BuildingGeometry,
    spec: ResolvedScenarioSpec,
) -> tuple[Window, ...]:
    """按每个外墙独立 WWR 生成居中且完整位于宿主内的窗。

    Args:
        geometry: 已建立邻接条件的 Zone 和表面几何。
        spec: 提供目标窗墙比的完整 Compiler 输入。

    Returns:
        按 Zone 和表面稳定排序的外窗元组。

    Raises:
        ValueError: 目标 WWR 在边界留量后无法放入宿主墙。
    """

    windows: list[Window] = []
    for zone in geometry.zones:
        for surface in zone.surfaces:
            if surface.surface_type != "Wall" or surface.outside_boundary_condition != "Outdoors":
                continue
            windows.append(_window_for_wall(surface, spec.window_to_wall_ratio))
    return tuple(windows)


def _window_for_wall(surface: Surface, window_to_wall_ratio: float) -> Window:
    """使用宿主底边和竖边计算居中开窗的四个顶点。"""

    origin, horizontal_end, _top_far, vertical_end = surface.vertices
    horizontal = _subtract(horizontal_end, origin)
    vertical = _subtract(vertical_end, origin)
    wall_width = _length(horizontal)
    wall_height = _length(vertical)
    opening_width = wall_width - 2 * EDGE_CLEARANCE_M
    opening_height = window_to_wall_ratio * wall_width * wall_height / opening_width
    if opening_width <= 0 or opening_height > wall_height - 2 * EDGE_CLEARANCE_M:
        raise ValueError(f"墙面 {surface.name} 无法在边界留量内放置目标 WWR 窗。")
    horizontal_start = EDGE_CLEARANCE_M / wall_width
    vertical_start = (wall_height - opening_height) / (2 * wall_height)
    horizontal_end_ratio = 1 - horizontal_start
    vertical_end_ratio = vertical_start + opening_height / wall_height
    return Window(
        name=stable_name("Window", surface.name),
        host_surface_name=surface.name,
        zone_name=surface.zone_name,
        vertices=(
            _point(origin, horizontal, vertical, horizontal_start, vertical_start),
            _point(origin, horizontal, vertical, horizontal_end_ratio, vertical_start),
            _point(origin, horizontal, vertical, horizontal_end_ratio, vertical_end_ratio),
            _point(origin, horizontal, vertical, horizontal_start, vertical_end_ratio),
        ),
    )


def _subtract(end: Vertex, start: Vertex) -> Vertex:
    """返回两个三维点之间的向量。"""

    return (end[0] - start[0], end[1] - start[1], end[2] - start[2])


def _length(vector: Vertex) -> float:
    """计算轴对齐宿主边的欧氏长度。"""

    return (vector[0] ** 2 + vector[1] ** 2 + vector[2] ** 2) ** 0.5


def _point(
    origin: Vertex,
    horizontal: Vertex,
    vertical: Vertex,
    horizontal_ratio: float,
    vertical_ratio: float,
) -> Vertex:
    """从宿主局部坐标比例转换为全局顶点。"""

    return tuple(
        round(
            origin[index]
            + horizontal[index] * horizontal_ratio
            + vertical[index] * vertical_ratio,
            6,
        )
        for index in range(3)
    )  # type: ignore[return-value]
