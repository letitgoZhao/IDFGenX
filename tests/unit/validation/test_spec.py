"""V0 Compiler 输入契约测试。"""

from __future__ import annotations

import unittest

from idfgenx.validation.spec import validate_spec


class SpecValidationTests(unittest.TestCase):
    """只允许完整的 ResolvedScenarioSpec 进入验证流水线。"""

    def test_rejects_non_resolved_spec(self) -> None:
        """未解析的任意对象不得伪装成 Compiler 的唯一输入。"""

        report = validate_spec({"building_name": "not a resolved spec"})

        self.assertEqual(report.status.value, "failed")
        self.assertEqual(report.findings[0].code, "V0_INVALID_RESOLVED_SPEC")
