"""验证 M1 确定性采样配置与采样行为。"""

from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from idfgenx.data_factory.sample import load_sampling_config
from idfgenx.data_factory.scenarios import (
    load_scenario_catalog,
    validate_bucket_assignment,
)
from idfgenx.errors import ConfigurationError


class SamplingConfigTests(unittest.TestCase):
    """验证采样策略能够被版本化载入和审计。"""

    def _load_api(self) -> tuple[object, object, object]:
        """延迟导入目标接口，使缺失实现表现为明确的断言失败。"""

        try:
            from idfgenx.data_factory.sample import (
                SamplingEngine,
                load_sampling_config,
                sampling_config_sha256,
            )
        except ImportError as error:
            self.fail(f"M1-005 采样配置接口尚未实现: {error}")
        return SamplingEngine, load_sampling_config, sampling_config_sha256

    def test_loads_frozen_policy_and_hash_is_stable(self) -> None:
        """删除默认引擎、配额或规范哈希都会破坏配置追溯契约。"""

        SamplingEngine, load_sampling_config, sampling_config_sha256 = self._load_api()
        config = load_sampling_config(Path("configs/data/sampling_v0_1.json"))

        self.assertEqual(config.default_engine, SamplingEngine.LATIN_HYPERCUBE)
        self.assertEqual(
            config.training_complexity_shares,
            {"simple": 0.4, "complex": 0.6},
        )
        self.assertEqual(
            sampling_config_sha256(config),
            sampling_config_sha256(config),
        )

    def test_rejects_complexity_shares_that_do_not_sum_to_one(self) -> None:
        """接受总和不为一的配额会让训练批次数量与配置不一致。"""

        _, load_sampling_config, _ = self._load_api()
        payload = json.loads(
            Path("configs/data/sampling_v0_1.json").read_text(encoding="utf-8")
        )
        payload["training_complexity_shares"] = {"simple": 0.5, "complex": 0.6}
        with tempfile.TemporaryDirectory() as directory:
            invalid = Path(directory) / "invalid.json"
            invalid.write_text(json.dumps(payload), encoding="utf-8")
            with self.assertRaises(ConfigurationError):
                load_sampling_config(invalid)


class BucketSamplingTests(unittest.TestCase):
    """验证单桶采样的确定性、覆盖和失败边界。"""

    def setUp(self) -> None:
        """载入每项测试共享的冻结场景与采样配置。"""

        self.catalog = load_scenario_catalog(
            Path("configs/data/scenario_buckets_v0_1.json")
        )
        self.config = load_sampling_config(Path("configs/data/sampling_v0_1.json"))

    def _load_api(self) -> tuple[object, object, object]:
        """延迟导入目标接口，使缺失实现表现为明确的断言失败。"""

        try:
            from idfgenx.data_factory.sample import (
                SamplingDistribution,
                SamplingEngine,
                sample_bucket,
            )
        except ImportError as error:
            self.fail(f"M1-005 单桶采样接口尚未实现: {error}")
        return SamplingDistribution, SamplingEngine, sample_bucket

    def test_same_seed_reproduces_lhs_records_and_different_seed_changes_fields(
        self,
    ) -> None:
        """使用全局 RNG 或忽略 seed 会破坏同请求复现和不同请求区分。"""

        _, _, sample_bucket = self._load_api()
        first = sample_bucket(self.catalog, self.config, "S1", 12, seed=42)
        repeated = sample_bucket(self.catalog, self.config, "S1", 12, seed=42)
        changed = sample_bucket(self.catalog, self.config, "S1", 12, seed=43)

        self.assertEqual(first, repeated)
        self.assertNotEqual(
            [row.spec.length_m for row in first],
            [row.spec.length_m for row in changed],
        )

    def test_sobol_records_pass_bucket_and_domain_gates(self) -> None:
        """漏掉缩放、纵横比或分区校验会产生不可用的 C2 场景。"""

        SamplingDistribution, SamplingEngine, sample_bucket = self._load_api()
        records = sample_bucket(
            self.catalog,
            self.config,
            "C2",
            16,
            seed=7,
            engine=SamplingEngine.SOBOL,
        )

        self.assertEqual(len(records), 16)
        for index, record in enumerate(records):
            self.assertEqual(record.sample_index, index)
            self.assertEqual(record.bucket_id, "C2")
            self.assertEqual(
                record.spec.building_name,
                f"IDFGenX-C2-{7:010d}-{index:06d}",
            )
            self.assertEqual(record.engine, SamplingEngine.SOBOL)
            self.assertEqual(record.distribution, SamplingDistribution.REALISTIC)
            self.assertEqual(len(record.scenario_catalog_sha256), 64)
            self.assertEqual(len(record.sampling_config_sha256), 64)
            validate_bucket_assignment(record.spec, self.catalog.bucket("C2"))
            ratio = record.spec.length_m / record.spec.width_m
            self.assertGreaterEqual(ratio, 0.4)
            self.assertLessEqual(ratio, 2.5)
            self.assertLess(
                record.spec.heating_setpoint_c,
                record.spec.cooling_setpoint_c,
            )

    def test_discrete_combinations_are_balanced_when_candidates_are_valid(self) -> None:
        """按随机独立抽取离散字段会破坏合法组合的分层覆盖。"""

        _, _, sample_bucket = self._load_api()
        safe_ranges = {
            "length_m": (20.0, 20.0),
            "width_m": (20.0, 20.0),
            "floor_to_floor_height_m": (3.0, 3.0),
            "stories": (1.0, 2.0),
            "window_to_wall_ratio": (0.4, 0.4),
            "heating_setpoint_c": (20.0, 20.0),
            "cooling_setpoint_c": (26.0, 26.0),
        }
        safe_bucket = self.catalog.bucket("S1").model_copy(
            update={"ranges": safe_ranges}
        )
        safe_catalog = self.catalog.model_copy(
            update={
                "buckets": tuple(
                    safe_bucket if bucket.id == "S1" else bucket
                    for bucket in self.catalog.buckets
                )
            }
        )

        records = sample_bucket(safe_catalog, self.config, "S1", 6, seed=11)
        combinations = Counter(
            (
                row.spec.stories,
                row.spec.zone_layout.value,
                row.spec.building_use.value,
            )
            for row in records
        )

        self.assertEqual(len(combinations), 6)
        self.assertEqual(set(combinations.values()), {1})

    def test_rejects_invalid_request_version_and_candidate_budget(self) -> None:
        """非法数量、seed、配置版本或候选预算不得返回部分样本。"""

        _, _, sample_bucket = self._load_api()
        requests = (
            (self.config, 0, 1),
            (self.config, 1, -1),
            (self.config, 1, 2**32),
            (
                self.config.model_copy(update={"scenario_catalog_version": "9.9"}),
                1,
                1,
            ),
            (
                self.config.model_copy(
                    update={"candidate_multiplier": 2, "maximum_candidate_count": 4}
                ),
                3,
                1,
            ),
        )
        for config, count, seed in requests:
            with self.subTest(count=count, seed=seed, config=config):
                with self.assertRaises(ConfigurationError) as captured:
                    sample_bucket(self.catalog, config, "S1", count, seed=seed)
                self.assertTrue(captured.exception.context)

    def test_reports_rejections_when_no_candidate_can_pass_domain_gates(self) -> None:
        """候选耗尽时返回部分批次会掩盖桶范围与组合门禁的冲突。"""

        _, _, sample_bucket = self._load_api()
        impossible_bucket = self.catalog.bucket("S1").model_copy(
            update={
                "ranges": {
                    **self.catalog.bucket("S1").ranges,
                    "length_m": (8.0, 8.0),
                    "width_m": (40.0, 40.0),
                }
            }
        )
        impossible_catalog = self.catalog.model_copy(
            update={
                "buckets": tuple(
                    impossible_bucket if bucket.id == "S1" else bucket
                    for bucket in self.catalog.buckets
                )
            }
        )

        with self.assertRaises(ConfigurationError) as captured:
            sample_bucket(impossible_catalog, self.config, "S1", 1, seed=5)

        self.assertEqual(captured.exception.context["accepted_count"], 0)
        self.assertEqual(captured.exception.context["attempt_count"], 8)
        self.assertEqual(
            captured.exception.context["rejection_counts"],
            {"aspect_ratio": 8},
        )

    def test_sampling_does_not_advance_numpy_global_rng(self) -> None:
        """读取 NumPy 全局随机状态会让采样结果受其他模块调用顺序影响。"""

        _, _, sample_bucket = self._load_api()
        np.random.seed(123)
        expected = np.random.random()
        np.random.seed(123)

        sample_bucket(self.catalog, self.config, "S1", 4, seed=9)

        self.assertEqual(np.random.random(), expected)


if __name__ == "__main__":
    unittest.main()
