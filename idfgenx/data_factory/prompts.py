"""生成可追溯的中英文 clean Prompt。

本模块只负责把 DisclosurePlan 已披露的 Draft 字段转换为自然语言，不执行
默认值推导、单位换算、噪声注入或 Prompt 反向解析。
"""

from __future__ import annotations

from enum import StrEnum
from hashlib import sha256
import json
from pathlib import Path
import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from idfgenx.data_factory.disclosure import DisclosurePlan, derive_draft
from idfgenx.errors import ConfigurationError
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import (
    BuildingUse,
    FieldStatus,
    ScenarioSpecDraft,
    ZoneLayout,
)


DRAFT_FIELD_ORDER = (
    "building_name",
    "building_use",
    "length",
    "width",
    "floor_to_floor_height",
    "stories",
    "zone_layout",
    "window_to_wall_ratio",
    "heating_setpoint",
    "cooling_setpoint",
)
ZH_BUILDING_USE = {
    BuildingUse.OFFICE: "办公",
    BuildingUse.RESIDENTIAL: "住宅",
    BuildingUse.CLASSROOM: "教室",
}
EN_BUILDING_USE = {
    BuildingUse.OFFICE: "office",
    BuildingUse.RESIDENTIAL: "residential building",
    BuildingUse.CLASSROOM: "classroom",
}
ZH_ZONE_LAYOUT = {
    ZoneLayout.SINGLE: "单区",
    ZoneLayout.PERIMETER_CORE: "周边-核心分区",
}
EN_ZONE_LAYOUT = {
    ZoneLayout.SINGLE: "single zone",
    ZoneLayout.PERIMETER_CORE: "perimeter-and-core zoning",
}


class PromptLanguage(StrEnum):
    """列出 clean Prompt 支持的语言。"""

    ZH = "zh"
    EN = "en"


class PromptStyle(StrEnum):
    """区分简洁表达和专家表达。"""

    CONCISE = "concise"
    EXPERT = "expert"


class PromptFamily(StrEnum):
    """列出 prompt config v0.1 的四个无噪声模板族。"""

    ZH_CONCISE = "zh_concise"
    ZH_EXPERT = "zh_expert"
    EN_CONCISE = "en_concise"
    EN_EXPERT = "en_expert"


class PromptFamilyConfig(BaseModel):
    """描述单个 clean Prompt family 的稳定元数据。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: PromptFamily = Field(description="clean Prompt family 的稳定标识。")
    language: PromptLanguage = Field(description="模板输出语言。")
    style: PromptStyle = Field(description="简洁或专家表达风格。")


class PromptConfig(BaseModel):
    """保存 prompt config v0.1 的模板集合和披露顺序。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    config_version: Literal["0.1"] = Field(description="Prompt 配置协议版本。")
    draft_schema_version: Literal["0.1"] = Field(
        description="配置兼容的 ScenarioSpecDraft 版本。"
    )
    families: tuple[PromptFamilyConfig, ...] = Field(
        description="按确定性输出顺序排列的四个 clean family。"
    )
    field_order: tuple[str, ...] = Field(
        description="Prompt 中各 Draft 字段的稳定出现顺序。"
    )
    requested_fields: tuple[str, ...] = Field(
        description="默认 clean Prompt 明确披露的 Draft 字段集合。"
    )

    @model_validator(mode="after")
    def validate_v0_1_contract(self) -> PromptConfig:
        """冻结四个 family 的顺序、元数据和可披露 Draft 字段。

        Returns:
            已通过 prompt config v0.1 交叉字段校验的当前配置。

        Raises:
            ValueError: family 集合、语言/风格映射或字段集合不符合 v0.1。
        """

        expected_families = (
            (PromptFamily.ZH_CONCISE, PromptLanguage.ZH, PromptStyle.CONCISE),
            (PromptFamily.ZH_EXPERT, PromptLanguage.ZH, PromptStyle.EXPERT),
            (PromptFamily.EN_CONCISE, PromptLanguage.EN, PromptStyle.CONCISE),
            (PromptFamily.EN_EXPERT, PromptLanguage.EN, PromptStyle.EXPERT),
        )
        actual_families = tuple(
            (family.id, family.language, family.style) for family in self.families
        )
        if actual_families != expected_families:
            raise ValueError("clean Prompt family 集合、顺序或元数据不符合 v0.1。")
        if self.field_order != DRAFT_FIELD_ORDER:
            raise ValueError("Prompt 字段顺序不符合 Draft v0.1 契约。")
        if self.requested_fields != DRAFT_FIELD_ORDER:
            raise ValueError("clean Prompt 必须披露 Draft v0.1 的完整字段集合。")
        return self


class CleanPromptRecord(BaseModel):
    """保存一条 clean Prompt、唯一目标 Draft 和追溯元数据。"""

    model_config = ConfigDict(extra="forbid", frozen=True)

    config_version: Literal["0.1"] = Field(description="生成记录所用配置版本。")
    draft_schema_version: Literal["0.1"] = Field(
        description="生成目标兼容的 ScenarioSpecDraft 版本。"
    )
    prompt_config_sha256: str = Field(
        min_length=64,
        max_length=64,
        description="规范化 Prompt 配置的 SHA-256。",
    )
    family: PromptFamily = Field(description="生成文本使用的模板族。")
    language: PromptLanguage = Field(description="生成文本的语言。")
    style: PromptStyle = Field(description="生成文本的表达风格。")
    prompt: str = Field(min_length=1, description="确定性生成的 clean Prompt。")
    scenario_spec_draft_target: ScenarioSpecDraft = Field(
        description="Prompt 唯一对应且保留字段来源状态的训练目标。"
    )


def load_prompt_config(path: Path) -> PromptConfig:
    """从 UTF-8 JSON 文件加载冻结的 clean Prompt 配置。

    Args:
        path: prompt config v0.1 文件路径。

    Returns:
        已通过版本、family 和字段契约校验的不可变配置。

    Raises:
        ConfigurationError: 文件不可读、JSON 无效或配置违反 v0.1 契约。
    """

    try:
        return PromptConfig.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ConfigurationError(
            "clean Prompt 配置无效。",
            context={"path": str(path)},
            cause=error,
        ) from error


def prompt_config_sha256(config: PromptConfig) -> str:
    """返回配置规范 JSON 的稳定 SHA-256。

    Args:
        config: 已验证的 prompt config v0.1。

    Returns:
        64 位小写十六进制哈希，用于数据构建和 release 追溯。
    """

    payload = json.dumps(
        config.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(payload.encode("utf-8")).hexdigest()


def prompt_disclosure_plan(config: PromptConfig) -> DisclosurePlan:
    """按配置的完整 clean 字段集合构造默认披露计划。

    Args:
        config: 已验证的 prompt config v0.1。

    Returns:
        只包含配置声明字段的不可变 DisclosurePlan。
    """

    return DisclosurePlan(frozenset(config.requested_fields))


def render_clean_prompt(
    spec: ResolvedScenarioSpec,
    plan: DisclosurePlan,
    family: PromptFamily,
    config: PromptConfig,
) -> CleanPromptRecord:
    """构造单个 family 的可追溯 clean Prompt 记录。

    Args:
        spec: 完整且只含 SI 数值的建筑事实。
        plan: 决定哪些字段可声明为用户请求的披露计划。
        family: 目标语言和表达风格。
        config: 已验证的 prompt config v0.1。

    Returns:
        包含 Prompt、目标 Draft、family 元数据和配置哈希的记录。

    Raises:
        ConfigurationError: 披露计划包含未知字段或 family 不在配置中。
    """

    if not plan.requested_fields:
        raise ConfigurationError(
            "clean Prompt 至少需要披露一个 Draft 字段。",
            context={"requested_fields": []},
        )
    unknown_fields = sorted(plan.requested_fields.difference(DRAFT_FIELD_ORDER))
    if unknown_fields:
        raise ConfigurationError(
            "DisclosurePlan 包含未知 Draft 字段。",
            context={"unknown_fields": unknown_fields},
        )
    try:
        selected_family = PromptFamily(family)
        family_config = next(
            item for item in config.families if item.id is selected_family
        )
    except (ValueError, StopIteration) as error:
        raise ConfigurationError(
            "clean Prompt family 不在当前配置中。",
            context={"family": str(family)},
            cause=error,
        ) from error
    target = derive_draft(spec, plan)
    if target.schema_version != config.draft_schema_version:
        raise ConfigurationError(
            "Prompt 配置与目标 Draft 的 schema 版本不兼容。",
            context={
                "prompt_draft_schema_version": config.draft_schema_version,
                "target_draft_schema_version": target.schema_version,
            },
        )
    prompt = render_prompt_from_draft(target, family_config.id, config.field_order)
    return CleanPromptRecord(
        config_version=config.config_version,
        draft_schema_version=config.draft_schema_version,
        prompt_config_sha256=prompt_config_sha256(config),
        family=family_config.id,
        language=family_config.language,
        style=family_config.style,
        prompt=prompt,
        scenario_spec_draft_target=target,
    )


def render_all_clean_prompts(
    spec: ResolvedScenarioSpec,
    config: PromptConfig,
) -> tuple[CleanPromptRecord, ...]:
    """按配置顺序渲染同一建筑事实的四个 clean family。

    Args:
        spec: 完整且只含 SI 数值的建筑事实。
        config: 已验证的 prompt config v0.1。

    Returns:
        中文简洁、中文专家、英文简洁、英文专家的稳定记录元组。
    """

    plan = prompt_disclosure_plan(config)
    return tuple(
        render_clean_prompt(spec, plan, family.id, config)
        for family in config.families
    )


def render_prompt_from_draft(
    target: ScenarioSpecDraft,
    family: PromptFamily,
    field_order: tuple[str, ...],
) -> str:
    """仅从目标 Draft 的 requested 字段渲染冻结的 clean 文本。

    Args:
        target: 已按 DisclosurePlan 派生的诚实 Draft。
        family: 目标语言和风格。
        field_order: 配置冻结的字段出现顺序。

    Returns:
        不包含随机改写或隐式默认值的 clean Prompt，可供鲁棒基线复用。
    """

    if target.building_name.status is FieldStatus.REQUESTED:
        validate_prompt_building_name(str(_field_value(target, "building_name")))
    renderers = {
        PromptFamily.ZH_CONCISE: _render_zh_concise,
        PromptFamily.ZH_EXPERT: _render_zh_expert,
        PromptFamily.EN_CONCISE: _render_en_concise,
        PromptFamily.EN_EXPERT: _render_en_expert,
    }
    return renderers[family](target, field_order)


def validate_prompt_building_name(name: str) -> None:
    """拒绝会破坏 Prompt 分隔语法或反向标定的建筑名称。

    v0.1 允许 Unicode 字母和数字、内部空格、下划线及连字符。名称必须至少
    包含一个字母或数字，且不能依赖首尾空白表达语义。

    Args:
        name: DisclosurePlan 已标记为 requested 的原始建筑名称。

    Raises:
        ConfigurationError: 名称无法无歧义地嵌入 clean 或 robust family。
    """

    if (
        name != name.strip()
        or re.fullmatch(r"[\w -]+", name) is None
        or not any(character.isalnum() for character in name)
    ):
        raise ConfigurationError(
            "建筑名称包含 clean Prompt 模板不支持的字符。",
            context={"building_name": name},
        )


def _requested_fields(
    target: ScenarioSpecDraft,
    field_order: tuple[str, ...],
) -> tuple[str, ...]:
    """按配置顺序返回 Draft 中确实来自用户请求的字段名。"""

    return tuple(
        field_name
        for field_name in field_order
        if getattr(target, field_name).status is FieldStatus.REQUESTED
    )


def _format_number(value: float | int) -> str:
    """以稳定十进制文本表达 v0.1 工程数值，去除无意义尾零。"""

    return format(value, ".12g")


def _field_value(target: ScenarioSpecDraft, field_name: str) -> object:
    """读取已确认 requested 的 Draft 值并保持错误边界显式。

    Args:
        target: 当前目标 Draft。
        field_name: 已由 `_requested_fields` 筛选的字段名。

    Returns:
        非空的用户请求原始值。

    Raises:
        ValueError: Draft 违反 requested 字段必须携带值的不变量。
    """

    value = getattr(target, field_name).value
    if value is None:
        raise ValueError(f"requested 字段缺少值: {field_name}")
    return value


def _render_zh_concise(
    target: ScenarioSpecDraft,
    field_order: tuple[str, ...],
) -> str:
    """渲染中文简洁模板，单位固定为 SI 显式文本。"""

    clauses: list[str] = []
    for field_name in _requested_fields(target, field_order):
        value = _field_value(target, field_name)
        if field_name == "building_name":
            clauses.append(f"名称为“{value}”")
        elif field_name == "building_use":
            clauses.append(f"用途为{ZH_BUILDING_USE[BuildingUse(value)]}")
        elif field_name == "length":
            clauses.append(f"长{_format_number(float(value))} m")
        elif field_name == "width":
            clauses.append(f"宽{_format_number(float(value))} m")
        elif field_name == "floor_to_floor_height":
            clauses.append(f"层高{_format_number(float(value))} m")
        elif field_name == "stories":
            clauses.append(f"共{int(value)}层")
        elif field_name == "zone_layout":
            clauses.append(f"采用{ZH_ZONE_LAYOUT[ZoneLayout(value)]}布局")
        elif field_name == "window_to_wall_ratio":
            clauses.append(f"窗墙比为{_format_number(float(value))}")
        elif field_name == "heating_setpoint":
            clauses.append(f"供暖设定温度为{_format_number(float(value))} °C")
        elif field_name == "cooling_setpoint":
            clauses.append(f"制冷设定温度为{_format_number(float(value))} °C")
    details = "、".join(clauses)
    return f"请生成一栋{details}的建筑模型；其余参数使用系统默认值。"


def _render_zh_expert(
    target: ScenarioSpecDraft,
    field_order: tuple[str, ...],
) -> str:
    """渲染包含 EnergyPlus 与 WWR 术语的中文专家模板。"""

    clauses: list[str] = []
    for field_name in _requested_fields(target, field_order):
        value = _field_value(target, field_name)
        if field_name == "building_name":
            clauses.append(f"建筑名称：“{value}”")
        elif field_name == "building_use":
            clauses.append(f"建筑用途：{ZH_BUILDING_USE[BuildingUse(value)]}")
        elif field_name == "length":
            clauses.append(f"建筑长度：{_format_number(float(value))} m")
        elif field_name == "width":
            clauses.append(f"建筑宽度：{_format_number(float(value))} m")
        elif field_name == "floor_to_floor_height":
            clauses.append(f"层高：{_format_number(float(value))} m")
        elif field_name == "stories":
            clauses.append(f"层数：{int(value)}")
        elif field_name == "zone_layout":
            clauses.append(f"热区布局：{ZH_ZONE_LAYOUT[ZoneLayout(value)]}")
        elif field_name == "window_to_wall_ratio":
            clauses.append(f"窗墙比（WWR）：{_format_number(float(value))}")
        elif field_name == "heating_setpoint":
            clauses.append(f"供暖设定温度：{_format_number(float(value))} °C")
        elif field_name == "cooling_setpoint":
            clauses.append(f"制冷设定温度：{_format_number(float(value))} °C")
    details = "；".join(clauses)
    return (
        f"请为 EnergyPlus v23.1 建立建筑场景。{details}。"
        "未明确字段按系统默认处理。"
    )


def _join_english_clauses(clauses: list[str]) -> str:
    """使用稳定的英文并列规则连接任意数量的已披露字段。"""

    if not clauses:
        return ""
    if len(clauses) == 1:
        return clauses[0]
    if len(clauses) == 2:
        return f"{clauses[0]} and {clauses[1]}"
    return f"{', '.join(clauses[:-1])}, and {clauses[-1]}"


def _render_en_concise(
    target: ScenarioSpecDraft,
    field_order: tuple[str, ...],
) -> str:
    """渲染英文简洁模板，并为用途选择稳定冠词。"""

    clauses: list[str] = []
    for field_name in _requested_fields(target, field_order):
        value = _field_value(target, field_name)
        if field_name == "building_name":
            clauses.append(f'named "{value}"')
        elif field_name == "building_use":
            building_use = BuildingUse(value)
            article = "an" if building_use is BuildingUse.OFFICE else "a"
            clauses.append(f"used as {article} {EN_BUILDING_USE[building_use]}")
        elif field_name == "length":
            clauses.append(f"{_format_number(float(value))} m long")
        elif field_name == "width":
            clauses.append(f"{_format_number(float(value))} m wide")
        elif field_name == "floor_to_floor_height":
            clauses.append(
                f"with a {_format_number(float(value))} m floor-to-floor height"
            )
        elif field_name == "stories":
            clauses.append(f"{int(value)} stories")
        elif field_name == "zone_layout":
            layout = ZoneLayout(value)
            layout_text = (
                "single-zone" if layout is ZoneLayout.SINGLE else "perimeter-and-core"
            )
            clauses.append(f"a {layout_text} layout")
        elif field_name == "window_to_wall_ratio":
            clauses.append(
                f"a window-to-wall ratio of {_format_number(float(value))}"
            )
        elif field_name == "heating_setpoint":
            clauses.append(
                f"a heating setpoint of {_format_number(float(value))} °C"
            )
        elif field_name == "cooling_setpoint":
            clauses.append(
                f"a cooling setpoint of {_format_number(float(value))} °C"
            )
    details = _join_english_clauses(clauses)
    separator = " " if details else ""
    return (
        f"Generate a building model{separator}{details}. "
        "Use system defaults for unspecified parameters."
    )


def _render_en_expert(
    target: ScenarioSpecDraft,
    field_order: tuple[str, ...],
) -> str:
    """渲染包含 EnergyPlus 与 WWR 术语的英文专家模板。"""

    clauses: list[str] = []
    for field_name in _requested_fields(target, field_order):
        value = _field_value(target, field_name)
        if field_name == "building_name":
            clauses.append(f'Building name: "{value}"')
        elif field_name == "building_use":
            clauses.append(f"building use: {EN_BUILDING_USE[BuildingUse(value)]}")
        elif field_name == "length":
            clauses.append(f"building length: {_format_number(float(value))} m")
        elif field_name == "width":
            clauses.append(f"building width: {_format_number(float(value))} m")
        elif field_name == "floor_to_floor_height":
            clauses.append(
                f"floor-to-floor height: {_format_number(float(value))} m"
            )
        elif field_name == "stories":
            clauses.append(f"story count: {int(value)}")
        elif field_name == "zone_layout":
            clauses.append(f"zone layout: {EN_ZONE_LAYOUT[ZoneLayout(value)]}")
        elif field_name == "window_to_wall_ratio":
            clauses.append(
                f"window-to-wall ratio (WWR): {_format_number(float(value))}"
            )
        elif field_name == "heating_setpoint":
            clauses.append(
                f"heating setpoint: {_format_number(float(value))} °C"
            )
        elif field_name == "cooling_setpoint":
            clauses.append(
                f"cooling setpoint: {_format_number(float(value))} °C"
            )
    details = "; ".join(clauses)
    separator = " " if details else ""
    return (
        f"Create an EnergyPlus v23.1 building scenario.{separator}{details}. "
        "Apply system defaults to unspecified fields."
    )
