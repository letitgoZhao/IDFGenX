"""验证报告值对象测试。"""

from __future__ import annotations

import unittest

from idfgenx.validation.models import Finding, StageReport, ValidationReport, ValidationStatus


class ValidationReportTests(unittest.TestCase):
    """验证聚合状态不能掩盖任一失败阶段。"""

    def test_failed_stage_makes_aggregate_failed(self) -> None:
        """移除失败传播会错误放行不完整质量门禁。"""

        report = ValidationReport((StageReport("V0", ValidationStatus.PASSED), StageReport("V4", ValidationStatus.FAILED, (Finding("V4_IDF_MISSING", "缺失", {}),))))

        self.assertEqual(report.status, ValidationStatus.FAILED)
