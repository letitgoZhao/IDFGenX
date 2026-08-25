"""冻结 Compiler MVP Golden 的端到端质量门禁。"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from idfgenx.compiler.compile import compile_scenario
from idfgenx.compiler.toolchain import EnergyPlusToolchain
from idfgenx.config import IDFGenXConfig
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.validation.service import validate_artifact


GOLDEN_ROOT = Path(__file__).parents[1] / "golden" / "compiler"


class CompilerGoldenTests(unittest.TestCase):
    """Golden 必须通过真实 v23.1 设计日和所有独立质量阶段。"""

    def test_discovers_one_hundred_balanced_golden_fixtures(self) -> None:
        """Golden 固定为 50 个 single 与 50 个 perimeter_core 场景。"""

        fixtures = _fixture_directories()

        self.assertEqual(len(fixtures), 100)
        layouts = [_load_spec(path).zone_layout.value for path in fixtures]
        self.assertEqual(layouts.count("single"), 50)
        self.assertEqual(layouts.count("perimeter_core"), 50)

    def test_every_golden_passes_v0_to_v6_and_matches_expected_summary(self) -> None:
        """每项 Golden 必须保持可审阅摘要、epJSON 哈希与 V0–V6 全绿。"""

        toolchain = EnergyPlusToolchain.from_config(
            IDFGenXConfig(energyplus_path=Path(r"C:\EnergyPlusV23-1-0"))
        )
        for fixture in _fixture_directories():
            with self.subTest(case_id=fixture.name), TemporaryDirectory() as temporary_directory:
                spec = _load_spec(fixture)
                expected = json.loads((fixture / "expected.json").read_text(encoding="utf-8"))
                work_dir = Path(temporary_directory)
                artifact = compile_scenario(spec, toolchain, work_dir)
                report = validate_artifact(artifact, spec, toolchain, work_dir)

                self.assertTrue(all(stage.status.value == "passed" for stage in report.stages))
                self.assertEqual(artifact.epjson_sha256, expected["epjson_sha256"])
                document = json.loads(artifact.epjson_path.read_text(encoding="utf-8"))
                self.assertEqual(len(document["Zone"]), expected["zone_count"])
                self.assertEqual(len(document["BuildingSurface:Detailed"]), expected["surface_count"])
                self.assertEqual(len(document["FenestrationSurface:Detailed"]), expected["window_count"])


def _fixture_directories() -> list[Path]:
    """按目录名稳定发现同时具有 spec 与 expected 的 Golden。"""

    return sorted(
        path
        for path in GOLDEN_ROOT.iterdir()
        if path.is_dir() and (path / "spec.json").is_file() and (path / "expected.json").is_file()
    )


def _load_spec(fixture: Path) -> ResolvedScenarioSpec:
    """从单项 Golden 的人类可读 JSON 加载解析后的 Compiler 输入。"""

    return ResolvedScenarioSpec.model_validate_json((fixture / "spec.json").read_text(encoding="utf-8"))
