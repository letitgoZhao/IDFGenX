"""载入并校验 M1 数据工厂的场景桶配置。"""

from __future__ import annotations

import json
from hashlib import sha256
from pathlib import Path

from pydantic import BaseModel, ConfigDict, Field, model_validator

from idfgenx.errors import ConfigurationError
from idfgenx.schemas.resolved import ResolvedScenarioSpec


class ScenarioBucket(BaseModel):
    """定义一个可分层采样的 M1 场景桶。"""

    model_config = ConfigDict(frozen=True)
    id: str
    complexity: str
    training_eligible: bool
    layouts: tuple[str, ...]
    uses: tuple[str, ...]
    ranges: dict[str, tuple[float, float]]

    @model_validator(mode="after")
    def validate_ranges(self) -> "ScenarioBucket":
        """确保每个数值范围保持严格递增。"""
        if any(low > high for low, high in self.ranges.values()):
            raise ValueError("场景桶范围下限不得大于上限。")
        return self


class ScenarioCatalog(BaseModel):
    """封装版本化场景桶目录与训练隔离规则。"""

    model_config = ConfigDict(frozen=True)
    config_version: str
    supported_schema_version: str
    supported_compiler_version: str
    training_bucket_ids: tuple[str, ...]
    evaluation_only_bucket_ids: tuple[str, ...]
    unsupported_features: tuple[str, ...]
    buckets: tuple[ScenarioBucket, ...] = Field(min_length=10, max_length=10)

    @model_validator(mode="after")
    def validate_membership(self) -> "ScenarioCatalog":
        """保持桶 ID 唯一，且 C5 不能进入训练集合。"""
        ids = tuple(bucket.id for bucket in self.buckets)
        if len(set(ids)) != len(ids) or set(ids) != set(self.training_bucket_ids + self.evaluation_only_bucket_ids):
            raise ValueError("场景桶与训练/评估清单必须一一对应。")
        if any(self.bucket(bucket_id).training_eligible for bucket_id in self.evaluation_only_bucket_ids):
            raise ValueError("评估专用桶不得标记为训练可用。")
        return self

    def bucket(self, bucket_id: str) -> ScenarioBucket:
        """按稳定 ID 返回场景桶，未知 ID 以配置错误失败。"""
        for bucket in self.buckets:
            if bucket.id == bucket_id:
                return bucket
        raise ConfigurationError("未知场景桶。", context={"bucket_id": bucket_id})


def load_scenario_catalog(path: Path) -> ScenarioCatalog:
    """从 JSON 文件加载冻结的 M1 场景契约。"""
    try:
        return ScenarioCatalog.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ConfigurationError("场景桶配置无效。", context={"path": str(path)}, cause=error) from error


def validate_bucket_assignment(spec: ResolvedScenarioSpec, bucket: ScenarioBucket, *, for_training: bool = False) -> None:
    """确认已解析场景符合桶范围、分区能力和训练隔离规则。"""
    if for_training and not bucket.training_eligible:
        raise ValueError("评估专用场景桶不得用于训练。")
    if spec.zone_layout.value not in bucket.layouts or spec.building_use.value not in bucket.uses:
        raise ValueError("场景布局或用途不属于目标桶。")
    if spec.zone_layout.value == "perimeter_core" and min(spec.length_m, spec.width_m) < 12:
        raise ValueError("perimeter_core 最短边必须至少为 12 m。")
    values = {"length_m": spec.length_m, "width_m": spec.width_m, "floor_to_floor_height_m": spec.floor_to_floor_height_m, "stories": spec.stories, "window_to_wall_ratio": spec.window_to_wall_ratio, "heating_setpoint_c": spec.heating_setpoint_c, "cooling_setpoint_c": spec.cooling_setpoint_c}
    for field, value in values.items():
        low, high = bucket.ranges[field]
        if not low <= value <= high:
            raise ValueError(f"场景字段超出桶范围: {field}")


def scenario_catalog_sha256(catalog: ScenarioCatalog) -> str:
    """返回配置规范 JSON 的稳定 SHA-256，供未来 release manifest 追溯。"""
    payload = json.dumps(catalog.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return sha256(payload.encode("utf-8")).hexdigest()
