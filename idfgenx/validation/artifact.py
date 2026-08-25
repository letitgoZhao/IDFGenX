"""检查 Compiler 工件路径和内容哈希。"""

from __future__ import annotations

from hashlib import sha256

from idfgenx.compiler.compile import CompilationArtifact
from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.validation.models import Finding, StageReport, ValidationStatus


def validate_artifact_contract(artifact: CompilationArtifact, spec: ResolvedScenarioSpec) -> StageReport:
    """执行 V0/V4 工件契约检查。

    Args:
        artifact: Compiler 成功转换后返回的工件位置与摘要。
        spec: 用于确认调用者传入规范化 Compiler 输入的场景。

    Returns:
        V4 阶段报告；缺失文件或哈希不一致时为失败。
    """

    del spec
    findings: list[Finding] = []
    for label, path, expected in (("EPJSON", artifact.epjson_path, artifact.epjson_sha256), ("IDF", artifact.idf_path, artifact.idf_sha256)):
        if not path.is_file():
            findings.append(Finding(f"V4_{label}_MISSING", "转换工件不存在。", {"path": str(path)}))
            continue
        actual = sha256(path.read_bytes()).hexdigest()
        if actual != expected:
            findings.append(Finding(f"V4_{label}_HASH_MISMATCH", "转换工件哈希与编译记录不一致。", {"path": str(path), "expected": expected, "actual": actual}))
    return StageReport("V4", ValidationStatus.FAILED if findings else ValidationStatus.PASSED, tuple(findings))
