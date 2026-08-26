"""定义 Prompt 可披露字段并从 ResolvedSpec 派生诚实的 Draft。"""
from __future__ import annotations

from dataclasses import dataclass
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import DraftQuantity, DraftValue, FieldStatus, ScenarioSpecDraft


@dataclass(frozen=True)
class DisclosurePlan:
    """声明字段是否应作为用户请求写入 Draft。"""
    requested_fields: frozenset[str]


def default_disclosure_plan() -> DisclosurePlan:
    """返回只披露名称和用途、其余由 Resolver 默认的保守计划。"""
    return DisclosurePlan(frozenset({"building_name", "building_use"}))


def derive_draft(spec: ResolvedScenarioSpec, plan: DisclosurePlan) -> ScenarioSpecDraft:
    """按披露计划从解析结果生成不伪造用户来源的 Draft。"""
    def value(name: str, item: object) -> DraftValue[object]:
        return DraftValue(value=item, status=FieldStatus.REQUESTED) if name in plan.requested_fields else DraftValue(status=FieldStatus.DEFAULTED)
    def quantity(name: str, item: float, unit: str) -> DraftQuantity:
        return DraftQuantity(value=item, unit=unit, status=FieldStatus.REQUESTED) if name in plan.requested_fields else DraftQuantity(status=FieldStatus.DEFAULTED)
    return ScenarioSpecDraft(building_name=value("building_name", spec.building_name), length=quantity("length", spec.length_m, "m"), width=quantity("width", spec.width_m, "m"), floor_to_floor_height=quantity("floor_to_floor_height", spec.floor_to_floor_height_m, "m"), stories=value("stories", spec.stories), zone_layout=value("zone_layout", spec.zone_layout), window_to_wall_ratio=value("window_to_wall_ratio", spec.window_to_wall_ratio), heating_setpoint=quantity("heating_setpoint", spec.heating_setpoint_c, "degC"), cooling_setpoint=quantity("cooling_setpoint", spec.cooling_setpoint_c, "degC"), building_use=value("building_use", spec.building_use))
