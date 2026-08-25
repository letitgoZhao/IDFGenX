"""提供独立于 Compiler 的 IDF 工件质量门禁。"""

from idfgenx.validation.artifact import validate_artifact_contract
from idfgenx.validation.spec import validate_spec

__all__ = ["validate_artifact_contract", "validate_spec"]
