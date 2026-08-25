"""定义可序列化的验证报告值对象。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Mapping


class ValidationStatus(StrEnum):
    """表示单个质量门禁的执行结论。"""

    PASSED = "passed"
    FAILED = "failed"
    NOT_RUN = "not_run"


@dataclass(frozen=True, slots=True)
class Finding:
    """记录可由调用方稳定处理的验证发现。"""

    code: str
    message: str
    evidence: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class StageReport:
    """记录一个 V0–V6 阶段的状态和发现。"""

    stage: str
    status: ValidationStatus
    findings: tuple[Finding, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidationReport:
    """汇总 V0–V6 阶段报告并给出整体状态。"""

    stages: tuple[StageReport, ...]

    @property
    def status(self) -> ValidationStatus:
        """只要任一阶段失败，整体即失败。"""

        return ValidationStatus.FAILED if any(item.status is ValidationStatus.FAILED for item in self.stages) else ValidationStatus.PASSED
