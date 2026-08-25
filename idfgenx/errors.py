"""定义 IDFGenX 跨模块复用的错误码和领域异常。

本模块只描述稳定的机器错误分类、可读消息和结构化上下文，不绑定 FastAPI
状态码或具体传输协议。HTTP、CLI 等适配层应在各自边界完成错误映射。
"""

from __future__ import annotations

from copy import deepcopy
from enum import StrEnum
from typing import Mapping


class ErrorCode(StrEnum):
    """IDFGenX 跨配置、编译、验证和仿真的稳定错误分类。"""

    CONFIGURATION_INVALID = "configuration_invalid"
    SCHEMA_INVALID = "schema_invalid"
    RESOLUTION_FAILED = "resolution_failed"
    COMPILATION_FAILED = "compilation_failed"
    CONVERSION_FAILED = "conversion_failed"
    VALIDATION_FAILED = "validation_failed"
    SIMULATION_FAILED = "simulation_failed"
    EXTERNAL_PROCESS_TIMEOUT = "external_process_timeout"
    INTERNAL_ERROR = "internal_error"


class IDFGenXError(RuntimeError):
    """所有可归类项目错误的公共基类。

    Args:
        code: 稳定的机器错误码，不包含 HTTP 等适配层语义。
        message: 面向日志和用户的可读错误摘要。
        context: 用于定位问题的结构化上下文；构造时会复制，避免外部突变。
        cause: 引发当前错误的原始异常；提供时保存在异常链中。
    """

    def __init__(
        self,
        code: ErrorCode,
        message: str,
        *,
        context: Mapping[str, object] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.context = deepcopy(dict(context or {}))
        if cause is not None:
            self.__cause__ = cause

    def to_dict(self) -> dict[str, object]:
        """返回不含传输层字段的结构化错误载荷。

        Returns:
            包含稳定错误码、可读消息和上下文副本的字典。
        """

        return {
            "code": self.code.value,
            "message": self.message,
            "context": deepcopy(self.context),
        }


class ConfigurationError(IDFGenXError):
    """表示项目配置缺失、格式错误或违反固定能力边界。"""

    def __init__(
        self,
        message: str,
        *,
        context: Mapping[str, object] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        """创建统一配置异常。

        Args:
            message: 面向日志和用户的可读错误摘要。
            context: 具体配置键、实际值和期望值等结构化信息。
            cause: 触发配置错误的原始异常。
        """

        super().__init__(
            ErrorCode.CONFIGURATION_INVALID,
            message,
            context=context,
            cause=cause,
        )


class ResolutionError(IDFGenXError):
    """表示 Draft 无法确定性解析为 Compiler 输入。"""

    def __init__(
        self,
        message: str,
        *,
        context: Mapping[str, object] | None = None,
        cause: BaseException | None = None,
    ) -> None:
        """创建包含字段上下文的统一解析异常。"""

        super().__init__(
            ErrorCode.RESOLUTION_FAILED,
            message,
            context=context,
            cause=cause,
        )
