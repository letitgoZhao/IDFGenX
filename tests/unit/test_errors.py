"""IDFGenX 统一错误码和项目异常测试。"""

from __future__ import annotations

import unittest

from idfgenx.errors import ConfigurationError, ErrorCode, IDFGenXError


class IDFGenXErrorTests(unittest.TestCase):
    """验证领域错误保留稳定机器字段和原始原因。"""

    def test_base_error_preserves_payload_context_and_cause(self) -> None:
        """错误载荷必须保留稳定字段，避免服务层解析异常文本。"""

        cause = ValueError("bad input")
        error = IDFGenXError(
            ErrorCode.COMPILATION_FAILED,
            "编译失败",
            context={"sample_id": "sample-001"},
            cause=cause,
        )

        self.assertEqual(str(error), "编译失败")
        self.assertIs(error.__cause__, cause)
        self.assertEqual(
            error.to_dict(),
            {
                "code": "compilation_failed",
                "message": "编译失败",
                "context": {"sample_id": "sample-001"},
            },
        )

    def test_configuration_error_uses_configuration_code(self) -> None:
        """配置异常必须使用固定错误码，供 CLI 和 HTTP 适配层复用。"""

        error = ConfigurationError(
            "版本不受支持",
            context={"actual": "24.1", "expected": "23.1"},
        )

        self.assertEqual(error.code, ErrorCode.CONFIGURATION_INVALID)


if __name__ == "__main__":
    unittest.main()
