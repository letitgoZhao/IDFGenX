"""为 M1 数据工厂提供确定性分层与低差异采样。

本模块只消费已验证的场景桶和采样策略，输出完整 SI 制式的
``ResolvedScenarioSpec``。它不生成 Prompt、EnergyPlus 对象或数据 release。
"""

from __future__ import annotations

import json
from enum import StrEnum
from hashlib import sha256
from itertools import product
from math import ceil, floor, isclose, log2
from pathlib import Path
from typing import Literal, cast

import numpy as np
from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator
from scipy.stats import qmc

from idfgenx.data_factory.scenarios import (
    ScenarioBucket,
    ScenarioCatalog,
    scenario_catalog_sha256,
    validate_bucket_assignment,
)
from idfgenx.errors import ConfigurationError
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.schemas.scenario import BuildingUse, ZoneLayout


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


class SamplingDistribution(StrEnum):
    """区分现实训练分布与隔离的 Hard/OOD 评估分布。"""

    REALISTIC = "realistic"
    HARD_OOD = "hard_ood"


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


class SamplingRecord(BaseModel):
    """保存一个已接受场景及其完整采样追溯信息。

    Attributes:
        sample_index: 当前返回批次中从零开始的稳定序号。
        bucket_id: 产生该场景的冻结桶 ID。
        engine: 连续字段使用的 QMC 引擎。
        distribution: 现实训练分布或 Hard/OOD 评估分布。
        seed: 当前单桶请求实际使用的 32 位随机种子。
        attempt_count: 接受该记录时已检查的累计候选数。
        rejection_counts: 接受该记录时各稳定原因的累计拒绝次数快照。
        scenario_catalog_sha256: 场景目录规范哈希。
        sampling_config_sha256: 采样策略规范哈希。
        spec: 可直接输入 Compiler 的完整 SI 场景事实。
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    sample_index: int = Field(ge=0)
    bucket_id: str
    engine: SamplingEngine
    distribution: SamplingDistribution
    seed: int = Field(ge=0, le=2**32 - 1)
    attempt_count: int = Field(ge=1)
    rejection_counts: dict[str, int]
    scenario_catalog_sha256: str = Field(min_length=64, max_length=64)
    sampling_config_sha256: str = Field(min_length=64, max_length=64)
    spec: ResolvedScenarioSpec


def sample_bucket(
    catalog: ScenarioCatalog,
    config: SamplingConfig,
    bucket_id: str,
    count: int,
    *,
    seed: int,
    engine: SamplingEngine | None = None,
) -> tuple[SamplingRecord, ...]:
    """从单个场景桶确定性生成完整工程场景。

    连续字段由固定大小的 QMC 候选池产生；离散字段遍历经局部 RNG 排列的
    合法笛卡尔积。候选即使被拒绝也会消耗对应离散组合，防止根据验证结果
    选择性重排类别。

    Args:
        catalog: 已验证的 v0.1 场景桶目录。
        config: 已验证的 v0.1 采样策略。
        bucket_id: 要采样的稳定场景桶 ID。
        count: 必须完整返回的正整数记录数。
        seed: 范围为 ``[0, 2**32 - 1]`` 的局部随机种子。
        engine: 连续采样引擎；省略时使用配置默认值。

    Returns:
        按接受顺序排列的不可变采样记录。

    Raises:
        ConfigurationError: 请求、版本、桶或候选资源无效，或候选池不足。
    """

    _validate_sampling_request(catalog, config, bucket_id, count, seed)
    bucket = catalog.bucket(bucket_id)
    selected_engine = _coerce_engine(engine or config.default_engine)
    candidate_count = _candidate_count(config, count, selected_engine)
    continuous_candidates = _continuous_candidates(
        bucket,
        config,
        candidate_count,
        seed,
        selected_engine,
    )
    discrete_combinations = _discrete_combinations(bucket, seed)
    rejection_counts: dict[str, int] = {}
    accepted: list[SamplingRecord] = []
    catalog_hash = scenario_catalog_sha256(catalog)
    config_hash = sampling_config_sha256(config)
    distribution = (
        SamplingDistribution.REALISTIC
        if bucket.training_eligible
        else SamplingDistribution.HARD_OOD
    )

    for candidate_index, continuous in enumerate(continuous_candidates):
        discrete = discrete_combinations[candidate_index % len(discrete_combinations)]
        spec, rejection_reason = _build_candidate_spec(
            bucket,
            continuous,
            discrete,
            seed=seed,
            sample_index=len(accepted),
        )
        if rejection_reason is not None:
            rejection_counts[rejection_reason] = (
                rejection_counts.get(rejection_reason, 0) + 1
            )
            continue
        spec = cast(ResolvedScenarioSpec, spec)
        try:
            validate_bucket_assignment(spec, bucket)
        except ValueError:
            rejection_counts["bucket_assignment"] = (
                rejection_counts.get("bucket_assignment", 0) + 1
            )
            continue
        if (
            bucket.id in catalog.evaluation_only_bucket_ids
            and not _is_outside_training_envelope(spec, catalog)
        ):
            reason = "c5_not_outside_training_envelope"
            rejection_counts[reason] = rejection_counts.get(reason, 0) + 1
            continue
        accepted.append(
            SamplingRecord(
                sample_index=len(accepted),
                bucket_id=bucket.id,
                engine=selected_engine,
                distribution=distribution,
                seed=seed,
                attempt_count=candidate_index + 1,
                rejection_counts=dict(rejection_counts),
                scenario_catalog_sha256=catalog_hash,
                sampling_config_sha256=config_hash,
                spec=spec,
            )
        )
        if len(accepted) == count:
            return tuple(accepted)

    raise ConfigurationError(
        "候选池不足，无法完整生成请求的场景数量。",
        context={
            "bucket_id": bucket_id,
            "requested_count": count,
            "seed": seed,
            "engine": selected_engine.value,
            "attempt_count": candidate_count,
            "accepted_count": len(accepted),
            "rejection_counts": rejection_counts,
        },
    )


def sample_training_catalog(
    catalog: ScenarioCatalog,
    config: SamplingConfig,
    count: int,
    *,
    seed: int,
    engine: SamplingEngine | None = None,
) -> tuple[SamplingRecord, ...]:
    """按冻结配额从全部训练桶生成确定性建筑事实批次。

    simple 数量取 ``floor(count * share)``，complex 获得余数。组内配额保持
    最大差不超过 1，余数起点和每桶子 seed 均由根 seed 稳定派生；C5 等评估
    专用桶不会被读取。

    Args:
        catalog: 已验证的 v0.1 场景桶目录。
        config: 已验证的 v0.1 采样策略。
        count: 必须完整返回的训练记录总数。
        seed: 范围为 ``[0, 2**32 - 1]`` 的根 seed。
        engine: 连续采样引擎；省略时使用配置默认值。

    Returns:
        确定性合并并重新编号的不可变训练采样记录。

    Raises:
        ConfigurationError: 请求、配置、训练桶或任一子采样失败。
    """

    _validate_training_request(catalog, config, count, seed)
    selected_engine = _coerce_engine(engine or config.default_engine)
    training_buckets = tuple(
        catalog.bucket(bucket_id) for bucket_id in catalog.training_bucket_ids
    )
    grouped_ids = {
        complexity: tuple(
            sorted(
                bucket.id
                for bucket in training_buckets
                if bucket.complexity == complexity
            )
        )
        for complexity in TRAINING_COMPLEXITIES
    }
    simple_count = floor(
        count * config.training_complexity_shares["simple"]
    )
    group_totals = {"simple": simple_count, "complex": count - simple_count}
    bucket_counts: dict[str, int] = {}
    for complexity in ("simple", "complex"):
        bucket_counts.update(
            _allocate_group_counts(
                grouped_ids[complexity],
                group_totals[complexity],
                seed,
                complexity,
            )
        )

    records: list[SamplingRecord] = []
    for bucket_id in sorted(bucket_counts):
        bucket_count = bucket_counts[bucket_id]
        if bucket_count == 0:
            continue
        child_seed = _derive_seed(seed, bucket_id, selected_engine.value)
        records.extend(
            sample_bucket(
                catalog,
                config,
                bucket_id,
                bucket_count,
                seed=child_seed,
                engine=selected_engine,
            )
        )
    merge_seed = _derive_seed(seed, "training", "merge", selected_engine.value)
    order = np.random.default_rng(merge_seed).permutation(len(records))
    return tuple(
        records[int(source_index)].model_copy(update={"sample_index": output_index})
        for output_index, source_index in enumerate(order)
    )


def _validate_training_request(
    catalog: ScenarioCatalog,
    config: SamplingConfig,
    count: int,
    seed: int,
) -> None:
    """在分配训练配额前确认请求、版本与桶资格完整有效。

    Args:
        catalog: 场景目录。
        config: 采样策略。
        count: 请求训练记录数。
        seed: 根 seed。

    Raises:
        ConfigurationError: 请求或训练桶目录违反 v0.1 契约。
    """

    context = {"count": count, "seed": seed}
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        raise ConfigurationError("采样数量必须为正整数。", context=context)
    if (
        not isinstance(seed, int)
        or isinstance(seed, bool)
        or seed < 0
        or seed > 2**32 - 1
    ):
        raise ConfigurationError("采样 seed 必须是有效的 32 位无符号整数。", context=context)
    if catalog.config_version != config.scenario_catalog_version:
        raise ConfigurationError(
            "采样策略与场景目录版本不匹配。",
            context={
                **context,
                "catalog_version": catalog.config_version,
                "expected_catalog_version": config.scenario_catalog_version,
            },
        )
    training_buckets = tuple(
        catalog.bucket(bucket_id) for bucket_id in catalog.training_bucket_ids
    )
    invalid = tuple(
        bucket.id
        for bucket in training_buckets
        if not bucket.training_eligible
        or bucket.complexity not in TRAINING_COMPLEXITIES
    )
    complexities = {bucket.complexity for bucket in training_buckets}
    if invalid or complexities != TRAINING_COMPLEXITIES:
        raise ConfigurationError(
            "训练桶资格或复杂度分组无效。",
            context={
                **context,
                "invalid_bucket_ids": invalid,
                "complexities": sorted(complexities),
            },
        )


def _allocate_group_counts(
    bucket_ids: tuple[str, ...],
    total: int,
    seed: int,
    complexity: str,
) -> dict[str, int]:
    """在一个复杂度组内均匀分配整数配额并稳定轮转余数。

    Args:
        bucket_ids: 已稳定排序的同复杂度训练桶 ID。
        total: 该组应生成的记录总数。
        seed: 训练请求根 seed。
        complexity: 用于派生余数轮转起点的组名。

    Returns:
        覆盖组内每个桶的非负整数配额。

    Raises:
        ConfigurationError: 组需要样本却没有可用桶。
    """

    if not bucket_ids:
        if total == 0:
            return {}
        raise ConfigurationError(
            "训练复杂度组没有可用场景桶。",
            context={"complexity": complexity, "requested_count": total},
        )
    quotient, remainder = divmod(total, len(bucket_ids))
    allocation = {bucket_id: quotient for bucket_id in bucket_ids}
    start = _derive_seed(seed, complexity, "allocation") % len(bucket_ids)
    for offset in range(remainder):
        bucket_id = bucket_ids[(start + offset) % len(bucket_ids)]
        allocation[bucket_id] += 1
    return allocation


def _is_outside_training_envelope(
    spec: ResolvedScenarioSpec,
    catalog: ScenarioCatalog,
) -> bool:
    """判断评估场景是否至少一个字段位于全部训练桶包络外。

    包络从配置动态计算而非复制 8–60 等常量，使场景目录范围变化时 C5 门禁
    不会静默沿用旧边界。

    Args:
        spec: 已通过目标评估桶校验的候选场景。
        catalog: 同时包含训练桶和评估桶的冻结目录。

    Returns:
        任一数值或离散字段超出训练桶并集时为 ``True``。
    """

    training_buckets = tuple(
        catalog.bucket(bucket_id) for bucket_id in catalog.training_bucket_ids
    )
    numeric_values = {
        "length_m": spec.length_m,
        "width_m": spec.width_m,
        "floor_to_floor_height_m": spec.floor_to_floor_height_m,
        "stories": spec.stories,
        "window_to_wall_ratio": spec.window_to_wall_ratio,
        "heating_setpoint_c": spec.heating_setpoint_c,
        "cooling_setpoint_c": spec.cooling_setpoint_c,
    }
    for field, value in numeric_values.items():
        lower = min(bucket.ranges[field][0] for bucket in training_buckets)
        upper = max(bucket.ranges[field][1] for bucket in training_buckets)
        if value < lower or value > upper:
            return True
    training_layouts = {
        layout for bucket in training_buckets for layout in bucket.layouts
    }
    training_uses = {use for bucket in training_buckets for use in bucket.uses}
    return (
        spec.zone_layout.value not in training_layouts
        or spec.building_use.value not in training_uses
    )


def _validate_sampling_request(
    catalog: ScenarioCatalog,
    config: SamplingConfig,
    bucket_id: str,
    count: int,
    seed: int,
) -> None:
    """在分配候选池前拒绝类型、范围和配置版本错误。

    Args:
        catalog: 场景目录。
        config: 采样策略。
        bucket_id: 请求桶 ID。
        count: 请求数量。
        seed: 请求 seed。

    Raises:
        ConfigurationError: 任一请求字段不满足稳定运行边界。
    """

    context = {"bucket_id": bucket_id, "count": count, "seed": seed}
    if not isinstance(count, int) or isinstance(count, bool) or count <= 0:
        raise ConfigurationError("采样数量必须为正整数。", context=context)
    if (
        not isinstance(seed, int)
        or isinstance(seed, bool)
        or seed < 0
        or seed > 2**32 - 1
    ):
        raise ConfigurationError("采样 seed 必须是有效的 32 位无符号整数。", context=context)
    if catalog.config_version != config.scenario_catalog_version:
        raise ConfigurationError(
            "采样策略与场景目录版本不匹配。",
            context={
                **context,
                "catalog_version": catalog.config_version,
                "expected_catalog_version": config.scenario_catalog_version,
            },
        )
    catalog.bucket(bucket_id)


def _coerce_engine(engine: SamplingEngine | str) -> SamplingEngine:
    """把调用方输入归一为受支持引擎并稳定归类错误。

    Args:
        engine: 枚举或等价字符串。

    Returns:
        受支持的采样引擎枚举。

    Raises:
        ConfigurationError: 引擎名称不属于 v0.1 契约。
    """

    try:
        return SamplingEngine(engine)
    except ValueError as error:
        raise ConfigurationError(
            "未知连续采样引擎。",
            context={"engine": str(engine)},
            cause=error,
        ) from error


def _candidate_count(
    config: SamplingConfig,
    requested_count: int,
    engine: SamplingEngine,
) -> int:
    """计算固定候选池大小，并在分配前执行资源上限。

    Sobol 必须一次使用 ``random_base2`` 生成二次幂长度；LHS 保留配置倍率的
    精确长度。两者均不得静默截断为最大候选数，否则会返回不可预测的部分批次。
    """

    required = requested_count * config.candidate_multiplier
    candidate_count = (
        1 << ceil(log2(required)) if engine is SamplingEngine.SOBOL else required
    )
    if candidate_count > config.maximum_candidate_count:
        raise ConfigurationError(
            "请求超过单次采样候选资源上限。",
            context={
                "requested_count": requested_count,
                "candidate_count": candidate_count,
                "maximum_candidate_count": config.maximum_candidate_count,
                "engine": engine.value,
            },
        )
    return candidate_count


def _continuous_candidates(
    bucket: ScenarioBucket,
    config: SamplingConfig,
    candidate_count: int,
    seed: int,
    engine: SamplingEngine,
) -> np.ndarray:
    """生成并按桶闭区间缩放六维 QMC 连续候选。

    Args:
        bucket: 提供各连续字段范围的目标桶。
        config: 提供字段顺序和舍入精度的采样策略。
        candidate_count: 已通过资源校验的候选数。
        seed: 当前请求的局部 seed。
        engine: LHS 或 Sobol。

    Returns:
        形状为 ``(candidate_count, 6)`` 的浮点数组。
    """

    dimension = len(config.continuous_fields)
    if engine is SamplingEngine.SOBOL:
        sampler = qmc.Sobol(d=dimension, scramble=True, seed=seed)
        unit_points = sampler.random_base2(m=int(log2(candidate_count)))
    else:
        sampler = qmc.LatinHypercube(d=dimension, scramble=True, seed=seed)
        unit_points = sampler.random(n=candidate_count)
    lower = np.asarray(
        [bucket.ranges[field][0] for field in config.continuous_fields],
        dtype=float,
    )
    upper = np.asarray(
        [bucket.ranges[field][1] for field in config.continuous_fields],
        dtype=float,
    )
    # 手工线性缩放允许受控测试使用零宽范围；结果再次夹取，避免舍入越界。
    scaled = lower + unit_points * (upper - lower)
    rounded = np.round(scaled, decimals=config.continuous_precision)
    return np.clip(rounded, lower, upper)


def _discrete_combinations(
    bucket: ScenarioBucket,
    seed: int,
) -> tuple[tuple[int, str, str], ...]:
    """构造并确定性排列目标桶允许的完整离散笛卡尔积。

    Args:
        bucket: 提供层数范围、布局和用途的目标桶。
        seed: 当前单桶请求 seed。

    Returns:
        ``(stories, zone_layout, building_use)`` 组合元组。

    Raises:
        ConfigurationError: 层数范围内不存在整数或离散允许集为空。
    """

    stories_low, stories_high = bucket.ranges["stories"]
    stories = tuple(range(ceil(stories_low), floor(stories_high) + 1))
    combinations = tuple(product(stories, bucket.layouts, bucket.uses))
    if not combinations:
        raise ConfigurationError(
            "场景桶没有可采样的离散组合。",
            context={"bucket_id": bucket.id},
        )
    local_seed = _derive_seed(seed, bucket.id, "discrete")
    order = np.random.default_rng(local_seed).permutation(len(combinations))
    return tuple(combinations[int(index)] for index in order)


def _derive_seed(seed: int, *parts: str) -> int:
    """使用稳定 SHA-256 派生与 Python hash 随机化无关的子 seed。"""

    payload = "\x1f".join((str(seed), *parts)).encode("utf-8")
    return int.from_bytes(sha256(payload).digest()[:4], byteorder="big")


def _build_candidate_spec(
    bucket: ScenarioBucket,
    continuous: np.ndarray,
    discrete: tuple[int, str, str],
    *,
    seed: int,
    sample_index: int,
) -> tuple[ResolvedScenarioSpec | None, str | None]:
    """把连续点和离散层合并为场景，并返回稳定拒绝原因。

    Args:
        bucket: 当前目标桶。
        continuous: 按固定维度排列的六个工程连续值。
        discrete: 层数、布局和用途组合。
        seed: 当前单桶 seed，用于稳定建筑名。
        sample_index: 当前已接受记录数。

    Returns:
        成功时返回 ``(spec, None)``；失败时返回 ``(None, reason)``。
    """

    (
        length_m,
        width_m,
        floor_to_floor_height_m,
        window_to_wall_ratio,
        heating_setpoint_c,
        cooling_setpoint_c,
    ) = (float(value) for value in continuous)
    stories, layout_value, use_value = discrete
    minimum_ratio, maximum_ratio = (
        (0.2, 5.0) if bucket.complexity == "hard_ood" else (0.4, 2.5)
    )
    ratio = length_m / width_m
    if ratio < minimum_ratio or ratio > maximum_ratio:
        return None, "aspect_ratio"
    if heating_setpoint_c >= cooling_setpoint_c:
        return None, "setpoint_order"
    layout = ZoneLayout(layout_value)
    if layout is ZoneLayout.PERIMETER_CORE and min(length_m, width_m) < 12.0:
        return None, "perimeter_core_minimum"
    try:
        spec = ResolvedScenarioSpec(
            building_name=(
                f"IDFGenX-{bucket.id}-{seed:010d}-{sample_index:06d}"
            ),
            length_m=length_m,
            width_m=width_m,
            floor_to_floor_height_m=floor_to_floor_height_m,
            stories=stories,
            zone_layout=layout,
            perimeter_depth_m=(
                min(length_m, width_m) / 4.0
                if layout is ZoneLayout.PERIMETER_CORE
                else None
            ),
            window_to_wall_ratio=window_to_wall_ratio,
            heating_setpoint_c=heating_setpoint_c,
            cooling_setpoint_c=cooling_setpoint_c,
            building_use=BuildingUse(use_value),
        )
    except (ValidationError, ValueError):
        return None, "resolved_schema"
    return spec, None
