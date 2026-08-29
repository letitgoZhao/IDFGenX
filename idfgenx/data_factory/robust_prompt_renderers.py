"""渲染鲁棒 Prompt 的中英文 standard 与 alternate 文本。

本模块只消费已完成披露和单位转换的 ``ScenarioSpecDraft``，不读取
``ResolvedScenarioSpec``、不选择变体、不注入噪声，也不修改训练目标。
"""

from __future__ import annotations

from idfgenx.data_factory.prompts import (
    EN_BUILDING_USE,
    EN_ZONE_LAYOUT,
    PromptFamily,
)
from idfgenx.schemas.scenario import (
    BuildingUse,
    FieldStatus,
    LengthUnit,
    ScenarioSpecDraft,
    TemperatureUnit,
    ZoneLayout,
)


def render_alternate_prompt(
    target: ScenarioSpecDraft,
    family: PromptFamily,
    field_order: tuple[str, ...],
) -> str:
    """按 family 以等价且可逆的领域术语渲染 Prompt。

    Args:
        target: 已完成诚实披露和原始单位转换的目标 Draft。
        family: 目标语言和表达风格。
        field_order: 当前变体选择的完整字段排列。

    Returns:
        不含表层噪声的 alternate Prompt。
    """

    clauses: list[str] = []
    for field_name in field_order:
        field = getattr(target, field_name)
        if field.status is not FieldStatus.REQUESTED:
            continue
        clauses.append(_alternate_clause(target, family, field_name))
    if family is PromptFamily.ZH_CONCISE:
        return f"请按这些条件建立模型：{'、'.join(clauses)}；其他字段沿用系统默认值。"
    if family is PromptFamily.ZH_EXPERT:
        return (
            "请创建 EnergyPlus v23.1 建筑场景。"
            f"{'；'.join(clauses)}。未明确字段按系统默认处理。"
        )
    if family is PromptFamily.EN_CONCISE:
        return (
            f"Build a model for {_join_english_clauses(clauses)}. "
            "Keep system defaults for fields not stated."
        )
    return (
        "Create an EnergyPlus v23.1 building scenario. "
        f"{'; '.join(clauses)}. Apply system defaults to unspecified fields."
    )


def render_standard_prompt(
    target: ScenarioSpecDraft,
    family: PromptFamily,
    field_order: tuple[str, ...],
) -> str:
    """以 clean 术语渲染可组合单位和语序的 standard Prompt。

    Args:
        target: 已完成诚实披露和原始单位转换的目标 Draft。
        family: 目标语言和表达风格。
        field_order: 当前变体选择的完整字段排列。

    Returns:
        不含表层噪声的 standard Prompt。
    """

    clauses = [
        _standard_clause(target, family, field_name)
        for field_name in field_order
        if getattr(target, field_name).status is FieldStatus.REQUESTED
    ]
    if family is PromptFamily.ZH_CONCISE:
        return f"请生成一栋{'、'.join(clauses)}的建筑模型；其余参数使用系统默认值。"
    if family is PromptFamily.ZH_EXPERT:
        return (
            "请为 EnergyPlus v23.1 建立建筑场景。"
            f"{'；'.join(clauses)}。未明确字段按系统默认处理。"
        )
    if family is PromptFamily.EN_CONCISE:
        return (
            f"Generate a building model {_join_english_clauses(clauses)}. "
            "Use system defaults for unspecified parameters."
        )
    return (
        "Create an EnergyPlus v23.1 building scenario. "
        f"{'; '.join(clauses)}. Apply system defaults to unspecified fields."
    )


def _standard_clause(
    target: ScenarioSpecDraft,
    family: PromptFamily,
    field_name: str,
) -> str:
    """返回一个 requested 字段在指定 family 中的 clean 术语表达。"""

    value = _requested_value(target, field_name)
    number = format(float(value), ".12g") if isinstance(value, (float, int)) else ""
    if family is PromptFamily.ZH_CONCISE:
        clauses = {
            "building_name": lambda: f"名称为“{value}”",
            "building_use": lambda: f"用途为{_zh_building_use(value)}",
            "length": lambda: f"长{number} {_unit_text(target.length.unit)}",
            "width": lambda: f"宽{number} {_unit_text(target.width.unit)}",
            "floor_to_floor_height": lambda: (
                f"层高{number} {_unit_text(target.floor_to_floor_height.unit)}"
            ),
            "stories": lambda: f"共{int(value)}层",
            "zone_layout": lambda: f"采用{_zh_zone_layout(value)}布局",
            "window_to_wall_ratio": lambda: f"窗墙比为{number}",
            "heating_setpoint": lambda: (
                f"供暖设定温度为{number} {_unit_text(target.heating_setpoint.unit)}"
            ),
            "cooling_setpoint": lambda: (
                f"制冷设定温度为{number} {_unit_text(target.cooling_setpoint.unit)}"
            ),
        }
    elif family is PromptFamily.ZH_EXPERT:
        clauses = {
            "building_name": lambda: f"建筑名称：“{value}”",
            "building_use": lambda: f"建筑用途：{_zh_building_use(value)}",
            "length": lambda: f"建筑长度：{number} {_unit_text(target.length.unit)}",
            "width": lambda: f"建筑宽度：{number} {_unit_text(target.width.unit)}",
            "floor_to_floor_height": lambda: (
                f"层高：{number} {_unit_text(target.floor_to_floor_height.unit)}"
            ),
            "stories": lambda: f"层数：{int(value)}",
            "zone_layout": lambda: f"热区布局：{_zh_zone_layout(value)}",
            "window_to_wall_ratio": lambda: f"窗墙比（WWR）：{number}",
            "heating_setpoint": lambda: (
                f"供暖设定温度：{number} {_unit_text(target.heating_setpoint.unit)}"
            ),
            "cooling_setpoint": lambda: (
                f"制冷设定温度：{number} {_unit_text(target.cooling_setpoint.unit)}"
            ),
        }
    elif family is PromptFamily.EN_CONCISE:
        clauses = {
            "building_name": lambda: f'named "{value}"',
            "building_use": lambda: f"used as {_english_use_with_article(value)}",
            "length": lambda: f"{number} {_unit_text(target.length.unit)} long",
            "width": lambda: f"{number} {_unit_text(target.width.unit)} wide",
            "floor_to_floor_height": lambda: (
                f"with a {number} {_unit_text(target.floor_to_floor_height.unit)} "
                "floor-to-floor height"
            ),
            "stories": lambda: f"{int(value)} stories",
            "zone_layout": lambda: f"a {_en_zone_layout(value)} layout",
            "window_to_wall_ratio": lambda: f"a window-to-wall ratio of {number}",
            "heating_setpoint": lambda: (
                f"a heating setpoint of {number} {_unit_text(target.heating_setpoint.unit)}"
            ),
            "cooling_setpoint": lambda: (
                f"a cooling setpoint of {number} {_unit_text(target.cooling_setpoint.unit)}"
            ),
        }
    else:
        clauses = {
            "building_name": lambda: f'Building name: "{value}"',
            "building_use": lambda: (
                f"building use: {EN_BUILDING_USE[BuildingUse(value)]}"
            ),
            "length": lambda: (
                f"building length: {number} {_unit_text(target.length.unit)}"
            ),
            "width": lambda: (
                f"building width: {number} {_unit_text(target.width.unit)}"
            ),
            "floor_to_floor_height": lambda: (
                "floor-to-floor height: "
                f"{number} {_unit_text(target.floor_to_floor_height.unit)}"
            ),
            "stories": lambda: f"story count: {int(value)}",
            "zone_layout": lambda: (
                f"zone layout: {EN_ZONE_LAYOUT[ZoneLayout(value)]}"
            ),
            "window_to_wall_ratio": lambda: (
                f"window-to-wall ratio (WWR): {number}"
            ),
            "heating_setpoint": lambda: (
                f"heating setpoint: {number} {_unit_text(target.heating_setpoint.unit)}"
            ),
            "cooling_setpoint": lambda: (
                f"cooling setpoint: {number} {_unit_text(target.cooling_setpoint.unit)}"
            ),
        }
    return clauses[field_name]()


def _alternate_clause(
    target: ScenarioSpecDraft,
    family: PromptFamily,
    field_name: str,
) -> str:
    """返回一个 requested 字段在指定 family 中的等价领域表达。"""

    value = _requested_value(target, field_name)
    number = format(float(value), ".12g") if isinstance(value, (float, int)) else ""
    if family is PromptFamily.ZH_CONCISE:
        clauses = {
            "building_name": lambda: f"项目名“{value}”",
            "building_use": lambda: f"使用类型为{_zh_building_use(value)}",
            "length": lambda: f"平面长度{number} {_unit_text(target.length.unit)}",
            "width": lambda: f"平面宽度{number} {_unit_text(target.width.unit)}",
            "floor_to_floor_height": lambda: (
                f"层间高度{number} {_unit_text(target.floor_to_floor_height.unit)}"
            ),
            "stories": lambda: f"楼层数量{int(value)}",
            "zone_layout": lambda: f"热区组织为{_zh_zone_layout(value)}",
            "window_to_wall_ratio": lambda: f"外窗占外墙比例{number}",
            "heating_setpoint": lambda: (
                f"供暖温控点{number} {_unit_text(target.heating_setpoint.unit)}"
            ),
            "cooling_setpoint": lambda: (
                f"制冷温控点{number} {_unit_text(target.cooling_setpoint.unit)}"
            ),
        }
    elif family is PromptFamily.ZH_EXPERT:
        clauses = {
            "building_name": lambda: f"项目标识：“{value}”",
            "building_use": lambda: f"占用类型：{_zh_building_use(value)}",
            "length": lambda: f"平面长度：{number} {_unit_text(target.length.unit)}",
            "width": lambda: f"平面宽度：{number} {_unit_text(target.width.unit)}",
            "floor_to_floor_height": lambda: (
                "楼层层高："
                f"{number} {_unit_text(target.floor_to_floor_height.unit)}"
            ),
            "stories": lambda: f"楼层数量：{int(value)}",
            "zone_layout": lambda: f"热分区方案：{_zh_zone_layout(value)}",
            "window_to_wall_ratio": lambda: f"外窗墙比 WWR：{number}",
            "heating_setpoint": lambda: (
                "供暖恒温器设定点："
                f"{number} {_unit_text(target.heating_setpoint.unit)}"
            ),
            "cooling_setpoint": lambda: (
                "制冷恒温器设定点："
                f"{number} {_unit_text(target.cooling_setpoint.unit)}"
            ),
        }
    elif family is PromptFamily.EN_CONCISE:
        clauses = {
            "building_name": lambda: f'project "{value}"',
            "building_use": lambda: f"{EN_BUILDING_USE[BuildingUse(value)]} occupancy",
            "length": lambda: f"plan length {number} {_unit_text(target.length.unit)}",
            "width": lambda: f"plan width {number} {_unit_text(target.width.unit)}",
            "floor_to_floor_height": lambda: (
                "floor-to-floor distance "
                f"{number} {_unit_text(target.floor_to_floor_height.unit)}"
            ),
            "stories": lambda: f"{int(value)} floors",
            "zone_layout": lambda: f"{_en_zone_layout(value)} thermal zoning",
            "window_to_wall_ratio": lambda: f"WWR {number}",
            "heating_setpoint": lambda: (
                f"heating target {number} {_unit_text(target.heating_setpoint.unit)}"
            ),
            "cooling_setpoint": lambda: (
                f"cooling target {number} {_unit_text(target.cooling_setpoint.unit)}"
            ),
        }
    else:
        clauses = {
            "building_name": lambda: f'Project identifier: "{value}"',
            "building_use": lambda: (
                f"occupancy archetype: {EN_BUILDING_USE[BuildingUse(value)]}"
            ),
            "length": lambda: f"plan length: {number} {_unit_text(target.length.unit)}",
            "width": lambda: f"plan width: {number} {_unit_text(target.width.unit)}",
            "floor_to_floor_height": lambda: (
                "floor-to-floor dimension: "
                f"{number} {_unit_text(target.floor_to_floor_height.unit)}"
            ),
            "stories": lambda: f"floor count: {int(value)}",
            "zone_layout": lambda: (
                f"thermal zoning: {EN_ZONE_LAYOUT[ZoneLayout(value)]}"
            ),
            "window_to_wall_ratio": lambda: f"WWR: {number}",
            "heating_setpoint": lambda: (
                "heating thermostat setpoint: "
                f"{number} {_unit_text(target.heating_setpoint.unit)}"
            ),
            "cooling_setpoint": lambda: (
                "cooling thermostat setpoint: "
                f"{number} {_unit_text(target.cooling_setpoint.unit)}"
            ),
        }
    return clauses[field_name]()


def _requested_value(target: ScenarioSpecDraft, field_name: str) -> object:
    """读取 requested 值，并拒绝违反 Draft 状态不变量的空值。"""

    value = getattr(target, field_name).value
    if value is None:
        raise ValueError(f"requested 字段缺少值: {field_name}")
    return value


def _unit_text(unit: LengthUnit | TemperatureUnit | None) -> str:
    """返回用户可见且与 Draft 枚举一一对应的工程单位文本。

    Args:
        unit: requested 数量字段保留的原始单位。

    Returns:
        与 Draft 枚举一一对应的用户可见单位。

    Raises:
        ValueError: requested 数量字段意外缺少单位。
    """

    if unit is None:
        raise ValueError("requested 数量字段缺少单位。")
    return {
        LengthUnit.METER: "m",
        LengthUnit.FOOT: "ft",
        TemperatureUnit.CELSIUS: "°C",
        TemperatureUnit.FAHRENHEIT: "°F",
    }[unit]


def _zh_building_use(value: object) -> str:
    """返回与 clean Prompt 一致的中文建筑用途术语。"""

    return {
        BuildingUse.OFFICE: "办公",
        BuildingUse.RESIDENTIAL: "住宅",
        BuildingUse.CLASSROOM: "教室",
    }[BuildingUse(value)]


def _zh_zone_layout(value: object) -> str:
    """返回与 clean Prompt 一致的中文热区布局术语。"""

    return {
        ZoneLayout.SINGLE: "单区",
        ZoneLayout.PERIMETER_CORE: "周边-核心分区",
    }[ZoneLayout(value)]


def _en_zone_layout(value: object) -> str:
    """返回适合名词短语组合的英文热区布局术语。"""

    layout = ZoneLayout(value)
    return "single-zone" if layout is ZoneLayout.SINGLE else "perimeter-and-core"


def _english_use_with_article(value: object) -> str:
    """返回带稳定冠词的英文建筑用途短语。"""

    building_use = BuildingUse(value)
    article = "an" if building_use is BuildingUse.OFFICE else "a"
    return f"{article} {EN_BUILDING_USE[building_use]}"


def _join_english_clauses(clauses: list[str]) -> str:
    """使用稳定的英文并列规则连接已披露的鲁棒字段。"""

    if len(clauses) == 1:
        return clauses[0]
    if len(clauses) == 2:
        return f"{clauses[0]} and {clauses[1]}"
    return f"{', '.join(clauses[:-1])}, and {clauses[-1]}"
