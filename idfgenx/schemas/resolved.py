"""定义可直接输入 Compiler 的 ResolvedScenarioSpec v0.1 协议。

本模块只容纳已由 Resolver 完成单位换算、默认填充与能力确认后的 SI 数据。Compiler
不得接受 ScenarioSpecDraft 或自行补齐缺失值，以保证数据、服务与评估共享同一事实源。
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from idfgenx.schemas.scenario import BuildingUse, ZoneLayout


class ResolvedScenarioSpec(BaseModel):
    """包含完整 SI 工程参数且可由首版 Compiler 确定性编译的场景。

    坐标和长度均为米，温度均为摄氏度。`perimeter_core` 分区要求核心边界与外墙
    之间留出正宽度的周边区域，避免产生零面积 Zone。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal["0.1"] = "0.1"
    compiler_version: Literal["0.1"] = "0.1"
    building_name: str = Field(min_length=1, max_length=80)
    length_m: float = Field(gt=2.0, le=200.0)
    width_m: float = Field(gt=2.0, le=200.0)
    floor_to_floor_height_m: float = Field(gt=2.0, le=8.0)
    stories: int = Field(ge=1, le=10)
    zone_layout: ZoneLayout
    perimeter_depth_m: float | None = Field(default=None, gt=0.0)
    window_to_wall_ratio: float = Field(ge=0.1, le=0.8)
    heating_setpoint_c: float = Field(ge=10.0, le=26.0)
    cooling_setpoint_c: float = Field(ge=18.0, le=35.0)
    building_use: BuildingUse

    @model_validator(mode="after")
    def validate_cross_field_constraints(self) -> ResolvedScenarioSpec:
        """确保温控、分区与矩形尺寸可生成物理有效的几何。"""

        if self.heating_setpoint_c >= self.cooling_setpoint_c:
            raise ValueError("供暖设定温度必须低于制冷设定温度。")
        if self.zone_layout is ZoneLayout.SINGLE:
            if self.perimeter_depth_m is not None:
                raise ValueError("single 分区不得提供 perimeter_depth_m。")
            return self
        if self.perimeter_depth_m is None:
            raise ValueError("perimeter_core 分区必须提供 perimeter_depth_m。")
        if self.perimeter_depth_m >= min(self.length_m, self.width_m) / 2:
            raise ValueError("perimeter_depth_m 必须小于最短边的一半。")
        return self
