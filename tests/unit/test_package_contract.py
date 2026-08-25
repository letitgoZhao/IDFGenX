"""IDFGenX 包根公共接口测试。"""

from __future__ import annotations

import unittest

import idfgenx


class PackageContractTests(unittest.TestCase):
    """验证共享基础类型可从稳定包根导入。"""

    def test_shared_foundation_is_exported(self) -> None:
        """包根必须提供下游模块使用的唯一公共导入路径。"""

        self.assertIs(idfgenx.load_config, idfgenx.config.load_config)
        self.assertIs(idfgenx.IDFGenXError, idfgenx.errors.IDFGenXError)
        self.assertIn("IDFGenXConfig", idfgenx.__all__)
        self.assertIn("ErrorCode", idfgenx.__all__)


if __name__ == "__main__":
    unittest.main()
