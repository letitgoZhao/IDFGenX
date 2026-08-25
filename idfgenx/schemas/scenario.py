"""定义保留用户原始表达的 ScenarioSpecDraft v0.1 协议。

本模块是语言模型与确定性 Resolver 之间的唯一数据边界。Draft 不执行单位换算、
默认值派生或几何推导，因而能明确区分用户请求、系统默认、歧义和不支持字段。
"""

from __future__ import annotations

from enum import StrEnum
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field, model_validator


ValueT = TypeVar("ValueT")


class FieldStatus(StrEnum):
    """描述 Draft 字段是否来自用户、默认策略或未处理状态。"""

    REQUESTED = "requested"
    DEFAULTED = "defaulted"
    AMBIGUOUS = "ambiguous"
    UNSUPPORTED = "unsupported"


class LengthUnit(StrEnum):
    """Draft 允许保留的长度单位。"""

    METER = "m"
    FOOT = "ft"


class TemperatureUnit(StrEnum):
    """Draft 允许保留的干球温度单位。"""

    CELSIUS = "degC"
    FAHRENHEIT = "degF"


class ZoneLayout(StrEnum):
    """首版 Compiler 支持的确定性热区布置方式。"""

    SINGLE = "single"
    PERIMETER_CORE = "perimeter_core"


class BuildingUse(StrEnum):
    """首版内置负荷与日程模板覆盖的建筑用途。"""

    OFFICE = "office"
    RESIDENTIAL = "residential"
    CLASSROOM = "classroom"


class DraftValue(BaseModel, Generic[ValueT]):
    """保存一个带来源状态的原始 Draft 字段。

    ``requested`` 必须有值；其余状态必须没有已经解释过的值，以避免 Draft 把
    默认或猜测伪装成用户输入。

    Attributes:
        value: 用户原始值；非 requested 状态时为 ``None``。
        status: 字段来源和处理状态。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    value: ValueT | None = None
    status: FieldStatus

    @model_validator(mode="after")
    def validate_value_for_status(self) -> DraftValue[ValueT]:
        """确保字段状态不会与已解释的值相互矛盾。"""

        if self.status is FieldStatus.REQUESTED and self.value is None:
            raise ValueError("requested 字段必须保留用户给出的值。")
        if self.status is not FieldStatus.REQUESTED and self.value is not None:
            raise ValueError("非 requested 字段不得携带已解释的值。")
        return self


class DraftQuantity(DraftValue[float]):
    """保存带原始单位的数值 Draft 字段。"""

    unit: LengthUnit | TemperatureUnit | None = None

    @model_validator(mode="after")
    def validate_unit_for_status(self) -> DraftQuantity:
        """确保单位只与用户实际给出的数值一起存在。"""

        if self.status is FieldStatus.REQUESTED and self.unit is None:
            raise ValueError("requested 数值字段必须提供原始单位。")
        if self.status is not FieldStatus.REQUESTED and self.unit is not None:
            raise ValueError("非 requested 数值字段不得携带单位。")
        return self


def _default_value() -> DraftValue[object]:
    """构造尚待 Resolver 按策略填充的通用字段。"""

    return DraftValue[object](status=FieldStatus.DEFAULTED)


def _default_quantity() -> DraftQuantity:
    """构造尚待 Resolver 按策略填充的数值字段。"""

    return DraftQuantity(status=FieldStatus.DEFAULTED)


class ScenarioSpecDraft(BaseModel):
    """语言模型输出且可由 Resolver 处理的建筑场景草案。

    所有字段均使用 ``DraftValue`` 或 ``DraftQuantity`` 保留来源；Resolver 是把
    `defaulted` 字段变成具体工程值、把单位换成 SI 的唯一位置。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["0.1"] = "0.1"
    building_name: DraftValue[str] = Field(default_factory=_default_value)
    length: DraftQuantity = Field(default_factory=_default_quantity)
    width: DraftQuantity = Field(default_factory=_default_quantity)
    floor_to_floor_height: DraftQuantity = Field(default_factory=_default_quantity)
    stories: DraftValue[int] = Field(default_factory=_default_value)
    zone_layout: DraftValue[ZoneLayout] = Field(default_factory=_default_value)
    window_to_wall_ratio: DraftValue[float] = Field(default_factory=_default_value)
    heating_setpoint: DraftQuantity = Field(default_factory=_default_quantity)
    cooling_setpoint: DraftQuantity = Field(default_factory=_default_quantity)
    building_use: DraftValue[BuildingUse] = Field(default_factory=_default_value)

    @model_validator(mode="after")
    def validate_quantity_dimensions(self) -> ScenarioSpecDraft:
        """拒绝在 Draft 层把长度和温度单位混用的模型输出。"""

        for field_name in ("length", "width", "floor_to_floor_height"):
            quantity = getattr(self, field_name)
            if (
                quantity.status is FieldStatus.REQUESTED
                and not isinstance(quantity.unit, LengthUnit)
            ):
                raise ValueError(f"{field_name} 必须使用长度单位。")
        for field_name in ("heating_setpoint", "cooling_setpoint"):
            quantity = getattr(self, field_name)
            if (
                quantity.status is FieldStatus.REQUESTED
                and not isinstance(quantity.unit, TemperatureUnit)
            ):
                raise ValueError(f"{field_name} 必须使用温度单位。")
        return self
