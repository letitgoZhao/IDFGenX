"""验证 Windows 上代表性 Compiler 工件的独立运行可复现性。"""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from idfgenx.compiler.compile import CompilationArtifact, compile_scenario
from idfgenx.compiler.toolchain import EnergyPlusToolchain
from idfgenx.config import IDFGenXConfig
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.validation.models import ValidationReport
from idfgenx.validation.service import validate_artifact
from tests.integration.test_compiler_stability import _perimeter_core_spec, _single_spec


class CompilerReproducibilityTests(unittest.TestCase):
    """确保两个独占 Windows 工作目录不会改变成功 Compiler 工件的语义或字节。"""

    @classmethod
    def setUpClass(cls) -> None:
        """加载固定的 Windows EnergyPlus v23.1 工具链。"""

        cls.toolchain = EnergyPlusToolchain.from_config(
            IDFGenXConfig(energyplus_path=Path(r"C:\EnergyPlusV23-1-0"))
        )

    def test_repeated_single_compilations_have_identical_artifacts_and_validation(self) -> None:
        """single 在两个独立工作目录中保持工件哈希和 V0–V6 结论一致。"""

        self._assert_reproducible(_single_spec())

    def test_repeated_perimeter_core_compilations_have_identical_artifacts_and_validation(self) -> None:
        """perimeter_core 在两个独立工作目录中保持工件哈希和 V0–V6 结论一致。"""

        self._assert_reproducible(_perimeter_core_spec())

    def _assert_reproducible(self, spec: ResolvedScenarioSpec) -> None:
        """编译同一 Spec 两次，并比较可移植的工件与门禁摘要。

        临时目录绝对路径只属于调用运行时，不参与 `CompilationArtifact` 哈希，
        成功的 V0–V6 阶段也不携带路径型 finding。因此这里比较哈希与阶段
        名称/状态，而不是比较瞬态工作目录。
        """

        with TemporaryDirectory() as first_directory, TemporaryDirectory() as second_directory:
            first_artifact, first_report = self._compile_and_validate(spec, Path(first_directory))
            second_artifact, second_report = self._compile_and_validate(spec, Path(second_directory))

        self.assertEqual(first_artifact.epjson_sha256, second_artifact.epjson_sha256)
        self.assertEqual(first_artifact.idf_sha256, second_artifact.idf_sha256)
        self.assertEqual(_stage_summary(first_report), _stage_summary(second_report))
        self.assertEqual(
            _stage_summary(first_report),
            (("V0", "passed"), ("V4", "passed"), ("V1", "passed"), ("V2", "passed"), ("V3", "passed"), ("V5", "passed"), ("V6", "passed")),
        )

    def _compile_and_validate(
        self,
        spec: ResolvedScenarioSpec,
        work_dir: Path,
    ) -> tuple[CompilationArtifact, ValidationReport]:
        """在调用方独占目录执行一次完整 Compiler 与 V0–V6 流程。"""

        artifact = compile_scenario(spec, self.toolchain, work_dir)
        return artifact, validate_artifact(artifact, spec, self.toolchain, work_dir)


def _stage_summary(report: ValidationReport) -> tuple[tuple[str, str], ...]:
    """提取不含瞬态路径的 V0–V6 阶段和状态摘要。"""

    return tuple((stage.stage, stage.status.value) for stage in report.stages)
