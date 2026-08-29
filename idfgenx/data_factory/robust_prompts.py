"""生成显式配置、可追溯且语义不变的鲁棒 Prompt。

本模块承载 M1-008 的单位、语序、专家表达和表层噪声变体。它不负责随机
采样、Prompt 反向解析、默认值推导或数据 release 写入。
"""

from __future__ import annotations

from enum import StrEnum
from hashlib import sha256
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from idfgenx.data_factory.disclosure import DisclosurePlan, derive_draft
from idfgenx.data_factory.robust_prompt_renderers import (
    render_alternate_prompt,
    render_standard_prompt,
)
from idfgenx.data_factory.prompts import (
    DRAFT_FIELD_ORDER,
    PromptFamily,
    PromptLanguage,
    PromptStyle,
    render_prompt_from_draft,
    validate_prompt_building_name,
)
from idfgenx.errors import ConfigurationError
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import (
    DraftQuantity,
    FieldStatus,
    LengthUnit,
    ScenarioSpecDraft,
    TemperatureUnit,
    ZoneLayout,
)


CONSTRAINTS_FIRST_FIELD_ORDER = (
    "building_name",
    "building_use",
    "heating_setpoint",
    "cooling_setpoint",
    "window_to_wall_ratio",
    "zone_layout",
    "stories",
    "length",
    "width",
    "floor_to_floor_height",
)


class ClauseOrder(StrEnum):
    """列出鲁棒 Prompt 支持的确定性字段语序。"""

    CANONICAL = "canonical"
    CONSTRAINTS_FIRST = "constraints_first"


class ExpressionVariant(StrEnum):
    """区分基准术语和等价的领域表达。"""

    STANDARD = "standard"
    ALTERNATE = "alternate"


class ControlledNoise(StrEnum):
    """列出不会改变建筑事实的单一表层噪声。"""

    NONE = "none"
    POLITE_FILLER = "polite_filler"
    CONTEXT_FILLER = "context_filler"


class ClauseOrderConfig(BaseModel):
    """保存一个语序标识及其完整 Draft 字段排列。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: ClauseOrder = Field(description="语序的稳定标识。")
    fields: tuple[str, ...] = Field(description="Draft 字段的完整确定性排列。")


class RobustPromptConfig(BaseModel):
    """冻结 robust prompt config v0.1 的全部可审计变体。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    config_version: Literal["0.1"] = Field(description="鲁棒 Prompt 配置版本。")
    draft_schema_version: Literal["0.1"] = Field(
        description="兼容的 ScenarioSpecDraft 版本。"
    )
    families: tuple[PromptFamily, ...] = Field(
        description="允许生成鲁棒变体的 clean family。"
    )
    clause_orders: tuple[ClauseOrderConfig, ...] = Field(
        description="可选择的完整字段语序。"
    )
    length_units: tuple[LengthUnit, ...] = Field(
        description="长度字段允许保留的原始单位。"
    )
    temperature_units: tuple[TemperatureUnit, ...] = Field(
        description="温度字段允许保留的原始单位。"
    )
    expression_variants: tuple[ExpressionVariant, ...] = Field(
        description="等价表达的允许集合。"
    )
    controlled_noises: tuple[ControlledNoise, ...] = Field(
        description="单条记录允许声明的表层噪声集合。"
    )

    @model_validator(mode="after")
    def validate_v0_1_contract(self) -> RobustPromptConfig:
        """拒绝缺项、重复项和未经批准的 v0.1 变体。

        Returns:
            已通过完整集合与字段排列校验的配置。

        Raises:
            ValueError: 配置与冻结的 robust v0.1 契约不一致。
        """

        expected_families = tuple(PromptFamily)
        if self.families != expected_families:
            raise ValueError("鲁棒 Prompt family 集合或顺序不符合 v0.1。")
        expected_orders = (
            ClauseOrderConfig(id=ClauseOrder.CANONICAL, fields=DRAFT_FIELD_ORDER),
            ClauseOrderConfig(
                id=ClauseOrder.CONSTRAINTS_FIRST,
                fields=CONSTRAINTS_FIRST_FIELD_ORDER,
            ),
        )
        if self.clause_orders != expected_orders:
            raise ValueError("鲁棒 Prompt 字段语序不符合 v0.1。")
        if self.length_units != tuple(LengthUnit):
            raise ValueError("鲁棒 Prompt 长度单位集合不符合 v0.1。")
        if self.temperature_units != tuple(TemperatureUnit):
            raise ValueError("鲁棒 Prompt 温度单位集合不符合 v0.1。")
        if self.expression_variants != tuple(ExpressionVariant):
            raise ValueError("鲁棒 Prompt 表达变体集合不符合 v0.1。")
        if self.controlled_noises != tuple(ControlledNoise):
            raise ValueError("鲁棒 Prompt 受控噪声集合不符合 v0.1。")
        return self


class RobustPromptPlan(BaseModel):
    """显式声明单条鲁棒 Prompt 使用的全部变体维度。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    length_unit: LengthUnit = Field(description="长度在 Prompt 和目标 Draft 中的单位。")
    temperature_unit: TemperatureUnit = Field(
        description="温度在 Prompt 和目标 Draft 中的单位。"
    )
    clause_order: ClauseOrder = Field(description="已披露字段的稳定语序。")
    expression_variant: ExpressionVariant = Field(
        description="标准或等价领域表达。"
    )
    controlled_noise: ControlledNoise = Field(
        description="最多一个不改变建筑事实的表层噪声。"
    )


class RobustPromptRecord(BaseModel):
    """保存鲁棒 Prompt、唯一目标 Draft 和完整变体追溯信息。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    config_version: Literal["0.1"] = Field(description="鲁棒 Prompt 配置版本。")
    draft_schema_version: Literal["0.1"] = Field(
        description="目标 Draft 的协议版本。"
    )
    prompt_config_sha256: str = Field(
        min_length=64,
        max_length=64,
        description="规范化鲁棒 Prompt 配置的 SHA-256。",
    )
    family: PromptFamily = Field(description="继承的 clean Prompt family。")
    language: PromptLanguage = Field(description="Prompt 输出语言。")
    style: PromptStyle = Field(description="Prompt 表达风格。")
    length_unit: LengthUnit = Field(description="长度原始单位。")
    temperature_unit: TemperatureUnit = Field(description="温度原始单位。")
    clause_order: ClauseOrder = Field(description="字段语序。")
    expression_variant: ExpressionVariant = Field(description="等价表达变体。")
    controlled_noise: ControlledNoise = Field(description="声明的单一表层噪声。")
    variant_id: str = Field(min_length=1, description="完整变体组合的稳定标识。")
    prompt: str = Field(min_length=1, description="确定性生成的鲁棒 Prompt。")
    scenario_spec_draft_target: ScenarioSpecDraft = Field(
        description="与 Prompt 数值和原始单位一致的唯一训练目标。"
    )


def load_robust_prompt_config(path: Path) -> RobustPromptConfig:
    """从 UTF-8 JSON 加载冻结的鲁棒 Prompt 配置。

    Args:
        path: robust prompt config v0.1 文件路径。

    Returns:
        已通过全部可选维度门禁的不可变配置。

    Raises:
        ConfigurationError: 文件不可读、JSON 无效或配置违反 v0.1。
    """

    try:
        return RobustPromptConfig.model_validate_json(
            path.read_text(encoding="utf-8")
        )
    except (OSError, ValueError) as error:
        raise ConfigurationError(
            "鲁棒 Prompt 配置无效。",
            context={"path": str(path)},
            cause=error,
        ) from error


def robust_prompt_config_sha256(config: RobustPromptConfig) -> str:
    """返回鲁棒 Prompt 配置规范 JSON 的稳定 SHA-256。

    Args:
        config: 已通过 v0.1 门禁的配置。

    Returns:
        64 位小写十六进制哈希。
    """

    payload = json.dumps(
        config.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def render_robust_prompt(
    spec: ResolvedScenarioSpec,
    disclosure_plan: DisclosurePlan,
    family: PromptFamily,
    plan: RobustPromptPlan,
    config: RobustPromptConfig,
) -> RobustPromptRecord:
    """按显式计划生成一条单位与目标 Draft 一致的鲁棒 Prompt。

    Args:
        spec: 完整且只含 SI 数值的建筑事实。
        disclosure_plan: 决定哪些字段可声明为用户请求的披露计划。
        family: 目标语言和表达风格。
        plan: 单位、语序、表达和表层噪声的显式选择。
        config: 已验证的 robust prompt config v0.1。

    Returns:
        包含文本、目标 Draft、配置哈希和变体 ID 的冻结记录。

    Raises:
        ConfigurationError: family、披露字段或变体不在冻结配置中。
    """

    if not disclosure_plan.requested_fields:
        raise ConfigurationError(
            "鲁棒 Prompt 至少需要披露一个 Draft 字段。",
            context={"requested_fields": []},
        )
    unknown_fields = sorted(
        disclosure_plan.requested_fields.difference(DRAFT_FIELD_ORDER)
    )
    if unknown_fields:
        raise ConfigurationError(
            "DisclosurePlan 包含未知 Draft 字段。",
            context={"unknown_fields": unknown_fields},
        )
    try:
        selected_family = PromptFamily(family)
        family_index = config.families.index(selected_family)
        order_config = next(
            item for item in config.clause_orders if item.id is plan.clause_order
        )
    except (ValueError, StopIteration) as error:
        raise ConfigurationError(
            "鲁棒 Prompt 选择不在当前配置中。",
            context={"family": str(family), "clause_order": plan.clause_order.value},
            cause=error,
        ) from error
    source_target = derive_draft(spec, disclosure_plan)
    _validate_representable_perimeter_depth(spec, source_target)
    _validate_requested_numeric_round_trip(
        source_target,
        plan.length_unit,
        plan.temperature_unit,
    )
    if source_target.building_name.status is FieldStatus.REQUESTED:
        validate_prompt_building_name(
            str(_requested_value(source_target, "building_name"))
        )
    languages = (
        PromptLanguage.ZH,
        PromptLanguage.ZH,
        PromptLanguage.EN,
        PromptLanguage.EN,
    )
    styles = (
        PromptStyle.CONCISE,
        PromptStyle.EXPERT,
        PromptStyle.CONCISE,
        PromptStyle.EXPERT,
    )
    is_clean_baseline = (
        plan.length_unit is LengthUnit.METER
        and plan.temperature_unit is TemperatureUnit.CELSIUS
        and plan.clause_order is ClauseOrder.CANONICAL
        and plan.expression_variant is ExpressionVariant.STANDARD
        and plan.controlled_noise is ControlledNoise.NONE
    )
    target = (
        source_target
        if is_clean_baseline
        else _target_with_requested_units(
            source_target,
            plan.length_unit,
            plan.temperature_unit,
        )
    )
    if is_clean_baseline:
        prompt = render_prompt_from_draft(
            target,
            selected_family,
            order_config.fields,
        )
    elif plan.expression_variant is ExpressionVariant.ALTERNATE:
        prompt = render_alternate_prompt(
            target,
            selected_family,
            order_config.fields,
        )
        prompt = _apply_controlled_noise(
            prompt,
            languages[family_index],
            plan.controlled_noise,
        )
    else:
        prompt = render_standard_prompt(
            target,
            selected_family,
            order_config.fields,
        )
        prompt = _apply_controlled_noise(
            prompt,
            languages[family_index],
            plan.controlled_noise,
        )
    return RobustPromptRecord(
        config_version=config.config_version,
        draft_schema_version=config.draft_schema_version,
        prompt_config_sha256=robust_prompt_config_sha256(config),
        family=selected_family,
        language=languages[family_index],
        style=styles[family_index],
        length_unit=plan.length_unit,
        temperature_unit=plan.temperature_unit,
        clause_order=plan.clause_order,
        expression_variant=plan.expression_variant,
        controlled_noise=plan.controlled_noise,
        variant_id=(
            f"{selected_family.value}.{plan.length_unit.value}."
            f"{plan.temperature_unit.value}.{plan.clause_order.value}."
            f"{plan.expression_variant.value}.{plan.controlled_noise.value}"
        ),
        prompt=prompt,
        scenario_spec_draft_target=target,
    )


def render_all_robust_prompts(
    spec: ResolvedScenarioSpec,
    disclosure_plan: DisclosurePlan,
    plan: RobustPromptPlan,
    config: RobustPromptConfig,
) -> tuple[RobustPromptRecord, ...]:
    """按配置顺序为同一建筑事实生成四个鲁棒 family。

    Args:
        spec: 完整且只含 SI 数值的建筑事实。
        disclosure_plan: 四个 family 共用的诚实披露计划。
        plan: 四个 family 共用且显式的鲁棒变体选择。
        config: 已验证的 robust prompt config v0.1。

    Returns:
        与配置 family 顺序一致的冻结记录元组。
    """

    return tuple(
        render_robust_prompt(spec, disclosure_plan, family, plan, config)
        for family in config.families
    )


def _display_number(value: float) -> float:
    """把换算值量化为 Prompt 实际输出的 12 位有效数字。"""

    return float(format(value, ".12g"))


def _validate_representable_perimeter_depth(
    spec: ResolvedScenarioSpec,
    target: ScenarioSpecDraft,
) -> None:
    """拒绝全披露 Draft 无法表达的自定义周边区深度。

    ScenarioSpecDraft v0.1 没有 ``perimeter_depth`` 字段。只有布局、长度和宽度
    都来自用户请求时，记录才声称完整保留该几何事实；此时深度必须等于现有
    Resolver 的 ``min(length, width) / 4`` 派生规则。

    Args:
        spec: Prompt 派生来源的完整 SI 建筑事实。
        target: 由 DisclosurePlan 生成、尚未改写单位的目标 Draft。

    Raises:
        ConfigurationError: 全披露 perimeter-core 深度无法由 Draft 往返表达。
    """

    required_fields = (target.length, target.width, target.zone_layout)
    if not all(field.status is FieldStatus.REQUESTED for field in required_fields):
        return
    if target.zone_layout.value is not ZoneLayout.PERIMETER_CORE:
        return
    expected_depth_m = min(spec.length_m, spec.width_m) / 4.0
    if spec.perimeter_depth_m != expected_depth_m:
        raise ConfigurationError(
            "perimeter-core 深度无法由 ScenarioSpecDraft v0.1 无损表达。",
            context={
                "actual_depth_m": spec.perimeter_depth_m,
                "expected_depth_m": expected_depth_m,
            },
        )


def _validate_requested_numeric_round_trip(
    target: ScenarioSpecDraft,
    length_unit: LengthUnit,
    temperature_unit: TemperatureUnit,
) -> None:
    """拒绝无法由 Prompt 文本和 Resolver 无损表达的 requested 数值。

    robust v0.1 以 12 位有效数字输出工程数值；英制数量随后还会经过 Resolver
    的 6 位小数 SI 归一化。门禁在渲染前验证这两个边界，避免文本、Draft 和
    Compiler 输入之间发生静默漂移。

    Args:
        target: 尚未改写单位的诚实 SI Draft。
        length_unit: 当前计划选择的长度原始单位。
        temperature_unit: 当前计划选择的温度原始单位。

    Raises:
        ConfigurationError: 任一 requested 数值不能无损通过当前文本或 Resolver。
    """

    failures: dict[str, str] = {}
    for field_name in ("length", "width", "floor_to_floor_height"):
        quantity = getattr(target, field_name)
        if quantity.status is not FieldStatus.REQUESTED:
            continue
        value_m = float(quantity.value)
        if _display_number(value_m) != value_m:
            failures[field_name] = "prompt_precision"
            continue
        if length_unit is LengthUnit.FOOT:
            displayed_ft = _display_number(value_m / 0.3048)
            if round(displayed_ft * 0.3048, 6) != value_m:
                failures[field_name] = "resolver_round_trip"
    for field_name in ("heating_setpoint", "cooling_setpoint"):
        quantity = getattr(target, field_name)
        if quantity.status is not FieldStatus.REQUESTED:
            continue
        value_c = float(quantity.value)
        if _display_number(value_c) != value_c:
            failures[field_name] = "prompt_precision"
            continue
        if temperature_unit is TemperatureUnit.FAHRENHEIT:
            displayed_f = _display_number(value_c * 9.0 / 5.0 + 32.0)
            if round((displayed_f - 32.0) * 5.0 / 9.0, 6) != value_c:
                failures[field_name] = "resolver_round_trip"
    ratio = target.window_to_wall_ratio
    if ratio.status is FieldStatus.REQUESTED:
        ratio_value = float(ratio.value)
        if _display_number(ratio_value) != ratio_value:
            failures["window_to_wall_ratio"] = "prompt_precision"
    if failures:
        raise ConfigurationError(
            "场景数值超出鲁棒 Prompt v0.1 的可逆精度。",
            context={
                "fields": sorted(failures),
                "reasons": dict(sorted(failures.items())),
            },
        )


def _target_with_requested_units(
    target: ScenarioSpecDraft,
    length_unit: LengthUnit,
    temperature_unit: TemperatureUnit,
) -> ScenarioSpecDraft:
    """把 requested SI 数量改写为计划声明的原始单位。

    Draft 负责保留用户原始表达，因此换算值在写入 Draft 前先按 Prompt 的
    实际文本精度量化。Resolver 随后仍是恢复 SI Compiler 输入的唯一边界。
    """

    updates: dict[str, DraftQuantity] = {}
    for field_name in ("length", "width", "floor_to_floor_height"):
        quantity = getattr(target, field_name)
        if quantity.status is FieldStatus.REQUESTED:
            value_m = float(quantity.value)
            converted = (
                value_m
                if length_unit is LengthUnit.METER
                else value_m / 0.3048
            )
            updates[field_name] = DraftQuantity(
                value=_display_number(converted),
                unit=length_unit,
                status=FieldStatus.REQUESTED,
            )
    for field_name in ("heating_setpoint", "cooling_setpoint"):
        quantity = getattr(target, field_name)
        if quantity.status is FieldStatus.REQUESTED:
            value_c = float(quantity.value)
            converted = (
                value_c
                if temperature_unit is TemperatureUnit.CELSIUS
                else value_c * 9.0 / 5.0 + 32.0
            )
            updates[field_name] = DraftQuantity(
                value=_display_number(converted),
                unit=temperature_unit,
                status=FieldStatus.REQUESTED,
            )
    return target.model_copy(update=updates)


def _requested_value(target: ScenarioSpecDraft, field_name: str) -> object:
    """读取 requested 值，并拒绝违反 Draft 状态不变量的空值。"""

    value = getattr(target, field_name).value
    if value is None:
        raise ValueError(f"requested 字段缺少值: {field_name}")
    return value


def _apply_controlled_noise(
    prompt: str,
    language: PromptLanguage,
    noise: ControlledNoise,
) -> str:
    """只在完整 Prompt 外层加入一个已声明且无语义的表层噪声。"""

    if noise is ControlledNoise.NONE:
        return prompt
    if noise is ControlledNoise.POLITE_FILLER:
        if language is PromptLanguage.ZH:
            return f"麻烦{prompt[1:]}"
        return f"Please {prompt[0].lower()}{prompt[1:]}"
    suffix = (
        "这是概念设计阶段的输入。"
        if language is PromptLanguage.ZH
        else "This is conceptual-design context."
    )
    separator = "" if language is PromptLanguage.ZH else " "
    return f"{prompt}{separator}{suffix}"
