"""为 M1 数据工厂提供确定性分层与低差异采样。

本模块只消费已验证的场景桶和采样策略，输出完整 SI 制式的
``ResolvedScenarioSpec``。它不生成 Prompt、EnergyPlus 对象或数据 release。
"""

from __future__ import annotations

import json
from enum import StrEnum
from hashlib import sha256
from math import isclose
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from idfgenx.errors import ConfigurationError


CONTINUOUS_FIELDS = (
    "length_m",
    "width_m",
    "floor_to_floor_height_m",
    "window_to_wall_ratio",
    "heating_setpoint_c",
    "cooling_setpoint_c",
)
DISCRETE_FIELDS = ("stories", "zone_layout", "building_use")
TRAINING_COMPLEXITIES = frozenset({"simple", "complex"})


class SamplingEngine(StrEnum):
    """列出首版数据工厂允许的连续低差异采样引擎。"""

    LATIN_HYPERCUBE = "latin_hypercube"
    SOBOL = "sobol"


class SamplingConfig(BaseModel):
    """保存可哈希且不可变的 M1 采样策略。

    数值范围仍由 ``ScenarioCatalog`` 唯一管理；本模型只约束字段顺序、训练
    配额、数值精度和单次采样资源上限。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    config_version: Literal["0.1"] = "0.1"
    scenario_catalog_version: Literal["0.1"] = "0.1"
    default_engine: SamplingEngine
    continuous_fields: tuple[str, ...]
    discrete_fields: tuple[str, ...]
    training_complexity_shares: dict[str, float]
    continuous_precision: int = Field(ge=0, le=12)
    candidate_multiplier: int = Field(ge=2)
    maximum_candidate_count: int = Field(ge=2)

    @model_validator(mode="after")
    def validate_sampling_contract(self) -> "SamplingConfig":
        """确保字段维度、训练配额和候选资源边界不会相互矛盾。

        Returns:
            已通过交叉字段校验的当前配置。

        Raises:
            ValueError: 字段集合、配额或候选资源边界不符合 v0.1 契约。
        """

        if self.continuous_fields != CONTINUOUS_FIELDS:
            raise ValueError("连续采样字段及顺序必须与 v0.1 QMC 维度一致。")
        if self.discrete_fields != DISCRETE_FIELDS:
            raise ValueError("离散分层字段及顺序必须与 v0.1 契约一致。")
        if set(self.training_complexity_shares) != TRAINING_COMPLEXITIES:
            raise ValueError("训练复杂度配额只能包含 simple 和 complex。")
        shares = tuple(self.training_complexity_shares.values())
        if any(share < 0.0 or share > 1.0 for share in shares) or not isclose(
            sum(shares),
            1.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError("训练复杂度配额之和必须为 1。")
        if self.maximum_candidate_count < self.candidate_multiplier:
            raise ValueError("最大候选数不得小于候选倍率。")
        return self


def load_sampling_config(path: Path) -> SamplingConfig:
    """从 JSON 文件载入冻结的 M1 采样策略。

    Args:
        path: UTF-8 编码的采样配置路径。

    Returns:
        已通过 v0.1 契约校验的不可变配置。

    Raises:
        ConfigurationError: 文件不可读、JSON 无效或字段违反采样契约。
    """

    try:
        return SamplingConfig.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise ConfigurationError(
            "采样配置无效。",
            context={"path": str(path)},
            cause=error,
        ) from error


def sampling_config_sha256(config: SamplingConfig) -> str:
    """返回采样配置规范 JSON 的稳定 SHA-256。

    Args:
        config: 已验证的采样策略。

    Returns:
        64 位小写十六进制 SHA-256，用于后续 build/release 追溯。
    """

    payload = json.dumps(
        config.model_dump(mode="json"),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return sha256(payload.encode("utf-8")).hexdigest()
