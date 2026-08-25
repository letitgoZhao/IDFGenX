"""验证 Validator 入口收到的 Compiler 规范化输入契约。"""

from __future__ import annotations

from idfgenx.schemas.resolved import ResolvedScenarioSpec
from idfgenx.validation.models import Finding, StageReport, ValidationStatus


def validate_spec(spec: object) -> StageReport:
    """执行 V0，确认输入是 Compiler 唯一允许的已解析场景。

    Args:
        spec: 调用方传入的候选场景对象。

    Returns:
        V0 阶段报告；非 ResolvedScenarioSpec 会携带稳定错误码失败。
    """

    if isinstance(spec, ResolvedScenarioSpec):
        return StageReport("V0", ValidationStatus.PASSED)
    return StageReport(
        "V0",
        ValidationStatus.FAILED,
        (
            Finding(
                "V0_INVALID_RESOLVED_SPEC",
                "Validator 只接受完整的 ResolvedScenarioSpec。",
                {"received_type": type(spec).__name__},
            ),
        ),
    )
