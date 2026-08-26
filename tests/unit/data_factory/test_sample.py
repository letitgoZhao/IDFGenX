"""验证 M1 确定性采样配置与采样行为。"""

from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

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


if __name__ == "__main__":
    unittest.main()
