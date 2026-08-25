"""V1 对象白名单测试。"""

from __future__ import annotations

import unittest

from idfgenx.validation.objects import validate_objects


class ObjectValidationTests(unittest.TestCase):
    """限制 Validator 接受的 Compiler 对象域。"""

    def test_rejects_unsupported_epjson_object(self) -> None:
        """未知顶层对象不得进入支持域。"""

        report = validate_objects({"Version": {"Version 1": {"version_identifier": "23.1"}}, "AirLoopHVAC": {"Unexpected": {}}})

        self.assertEqual(report.status.value, "failed")
        self.assertEqual(report.findings[0].code, "V1_UNSUPPORTED_OBJECT")
