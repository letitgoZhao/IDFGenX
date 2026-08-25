"""将 ScenarioSpecDraft 确定性解析为 SI-only Compiler 输入。

Resolver 是唯一允许填充默认值、换算单位和派生核心分区深度的模块。它不生成几何、
对象引用或 EnergyPlus 文件，因而可被数据、服务和评估共享。
"""

from __future__ import annotations

from typing import TypeVar, cast

from pydantic import ValidationError

from idfgenx.errors import ResolutionError
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import (
    BuildingUse,
    DraftQuantity,
    DraftValue,
    FieldStatus,
    LengthUnit,
    ScenarioSpecDraft,
    TemperatureUnit,
    ZoneLayout,
)


ValueT = TypeVar("ValueT")

DEFAULT_BUILDING_NAME = "IDFGenX Building"
DEFAULT_LENGTH_M = 10.0
DEFAULT_WIDTH_M = 8.0
DEFAULT_FLOOR_TO_FLOOR_HEIGHT_M = 3.0
DEFAULT_STORIES = 1
DEFAULT_ZONE_LAYOUT = ZoneLayout.SINGLE
DEFAULT_WINDOW_TO_WALL_RATIO = 0.4
DEFAULT_HEATING_SETPOINT_C = 20.0
DEFAULT_COOLING_SETPOINT_C = 26.0
DEFAULT_BUILDING_USE = BuildingUse.OFFICE


def resolve_scenario(draft: ScenarioSpecDraft) -> ResolvedScenarioSpec:
    """将 Draft 的状态、原始单位和默认策略解析为唯一 Compiler 输入。

    Args:
        draft: 仅包含用户原始表达与字段状态的场景草案。

    Returns:
        所有长度为米、温度为摄氏度且字段完整的 ResolvedScenarioSpec。

    Raises:
        ResolutionError: Draft 存在歧义、不支持字段、非法单位或超出支持范围的值。
    """

    length_m = _resolve_length(draft.length, "length", DEFAULT_LENGTH_M)
    width_m = _resolve_length(draft.width, "width", DEFAULT_WIDTH_M)
    zone_layout = _resolve_value(
        draft.zone_layout,
        "zone_layout",
        DEFAULT_ZONE_LAYOUT,
    )
    try:
        return ResolvedScenarioSpec(
            building_name=_resolve_value(
                draft.building_name,
                "building_name",
                DEFAULT_BUILDING_NAME,
            ),
            length_m=length_m,
            width_m=width_m,
            floor_to_floor_height_m=_resolve_length(
                draft.floor_to_floor_height,
                "floor_to_floor_height",
                DEFAULT_FLOOR_TO_FLOOR_HEIGHT_M,
            ),
            stories=_resolve_value(draft.stories, "stories", DEFAULT_STORIES),
            zone_layout=zone_layout,
            perimeter_depth_m=(
                min(length_m, width_m) / 4
                if zone_layout is ZoneLayout.PERIMETER_CORE
                else None
            ),
            window_to_wall_ratio=_resolve_value(
                draft.window_to_wall_ratio,
                "window_to_wall_ratio",
                DEFAULT_WINDOW_TO_WALL_RATIO,
            ),
            heating_setpoint_c=_resolve_temperature(
                draft.heating_setpoint,
                "heating_setpoint",
                DEFAULT_HEATING_SETPOINT_C,
            ),
            cooling_setpoint_c=_resolve_temperature(
                draft.cooling_setpoint,
                "cooling_setpoint",
                DEFAULT_COOLING_SETPOINT_C,
            ),
            building_use=_resolve_value(
                draft.building_use,
                "building_use",
                DEFAULT_BUILDING_USE,
            ),
        )
    except ValidationError as exc:
        raise ResolutionError(
            "场景参数超出首版 Compiler 支持范围。",
            context={"errors": exc.errors()},
            cause=exc,
        ) from exc


def _resolve_value(
    field: DraftValue[ValueT],
    field_name: str,
    default: ValueT,
) -> ValueT:
    """读取 requested 值或确定性默认值，并拒绝未处理状态。"""

    if field.status is FieldStatus.REQUESTED:
        return cast(ValueT, field.value)
    if field.status is FieldStatus.DEFAULTED:
        return default
    raise ResolutionError(
        "场景字段尚未得到确定性解析。",
        context={"field": field_name, "status": field.status.value},
    )


def _resolve_length(
    field: DraftQuantity,
    field_name: str,
    default_m: float,
) -> float:
    """将 Draft 长度换算为米，默认值已按米定义。"""

    value = _resolve_value(field, field_name, default_m)
    if field.status is FieldStatus.DEFAULTED:
        return value
    if field.unit is LengthUnit.METER:
        return value
    if field.unit is LengthUnit.FOOT:
        return round(value * 0.3048, 6)
    raise ResolutionError(
        "长度字段使用了不受支持的单位。",
        context={"field": field_name, "unit": str(field.unit)},
    )


def _resolve_temperature(
    field: DraftQuantity,
    field_name: str,
    default_c: float,
) -> float:
    """将 Draft 温度换算为摄氏度，默认值已按摄氏度定义。"""

    value = _resolve_value(field, field_name, default_c)
    if field.status is FieldStatus.DEFAULTED:
        return value
    if field.unit is TemperatureUnit.CELSIUS:
        return value
    if field.unit is TemperatureUnit.FAHRENHEIT:
        return round((value - 32.0) * 5.0 / 9.0, 6)
    raise ResolutionError(
        "温度字段使用了不受支持的单位。",
        context={"field": field_name, "unit": str(field.unit)},
    )
