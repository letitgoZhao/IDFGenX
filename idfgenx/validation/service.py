"""按固定次序编排 Compiler 工件的 V0–V6 质量门禁。"""

from __future__ import annotations

import json
from pathlib import Path

from idfgenx.compiler.compile import CompilationArtifact
from idfgenx.compiler.toolchain import EnergyPlusToolchain
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.validation.artifact import validate_artifact_contract
from idfgenx.validation.geometry import validate_geometry
from idfgenx.validation.models import Finding, StageReport, ValidationReport, ValidationStatus
from idfgenx.validation.objects import validate_objects
from idfgenx.validation.references import validate_references
from idfgenx.validation.sanity import validate_sanity
from idfgenx.validation.simulation import run_design_day_simulation
from idfgenx.validation.spec import validate_spec


def validate_artifact(artifact: CompilationArtifact, spec: ResolvedScenarioSpec, toolchain: EnergyPlusToolchain, work_dir: Path, *, run_simulation: bool = True) -> ValidationReport:
    """执行 V0–V6；前置门禁失败时以 not_run 明确记录后续阶段。"""

    stages: list[StageReport] = [validate_spec(spec), validate_artifact_contract(artifact, spec)]
    if any(stage.status is ValidationStatus.FAILED for stage in stages):
        return ValidationReport(tuple(stages + [_not_run(stage) for stage in ("V1", "V2", "V3", "V5", "V6")]))
    try:
        document = json.loads(artifact.epjson_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        stages.append(StageReport("V1", ValidationStatus.FAILED, (Finding("V1_EPJSON_UNREADABLE", "无法读取 canonical epJSON。", {"error": str(error)}),)))
        return ValidationReport(tuple(stages + [_not_run(stage) for stage in ("V2", "V3", "V5", "V6")]))
    for validator in (validate_objects, validate_references, validate_geometry):
        report = validator(document)
        stages.append(report)
        if report.status is ValidationStatus.FAILED:
            return ValidationReport(tuple(stages + [_not_run(stage) for stage in ("V5", "V6")]))
    stages.append(run_design_day_simulation(artifact, toolchain, work_dir) if run_simulation else _not_run("V5"))
    stages.append(validate_sanity(document, spec))
    return ValidationReport(tuple(stages))


def _not_run(stage: str) -> StageReport:
    """创建说明短路或显式关闭的阶段报告。"""

    return StageReport(stage, ValidationStatus.NOT_RUN, (Finding(f"{stage}_NOT_RUN", "前置质量门禁未通过或调用方关闭了该阶段。", {}),))
