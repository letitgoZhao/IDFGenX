"""V5 设计日仿真结果解析测试。"""

from __future__ import annotations

import unittest
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from idfgenx.compiler.compile import CompilationArtifact
from idfgenx.compiler.toolchain import EnergyPlusToolchain
from idfgenx.validation.simulation import count_energyplus_errors, run_design_day_simulation


class SimulationValidationTests(unittest.TestCase):
    """确保 V5 不会忽略 EnergyPlus 写入的严重错误。"""

    def test_counts_severe_and_fatal_error_markers(self) -> None:
        """`.err` 中任意 Severe/Fatal 都必须被稳定计数。"""

        severe_count, fatal_count = count_energyplus_errors(
            "** Severe  ** malformed surface\n**  Fatal  ** abort\n** Fatal  ** stop\n"
        )

        self.assertEqual(severe_count, 1)
        self.assertEqual(fatal_count, 2)

    def test_reports_missing_idf_without_starting_simulation(self) -> None:
        """缺失 IDF 是工件问题，V5 必须返回可审计失败而非进程异常。"""

        with TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            epjson_path = root / "scenario.epJSON"
            epjson_path.write_text("{}", encoding="utf-8")
            artifact = CompilationArtifact(
                epjson_path=epjson_path,
                idf_path=root / "missing.idf",
                epjson_sha256=sha256(epjson_path.read_bytes()).hexdigest(),
                idf_sha256="unused",
            )
            toolchain = EnergyPlusToolchain(
                root=root,
                convert_input_format=root / "ConvertInputFormat.exe",
                energyplus=root / "energyplus.exe",
                idd_path=root / "Energy+.idd",
                epjson_schema_path=root / "Energy+.schema.epJSON",
            )

            report = run_design_day_simulation(artifact, toolchain, root)

        self.assertEqual(report.status.value, "failed")
        self.assertEqual(report.findings[0].code, "V5_IDF_MISSING")
