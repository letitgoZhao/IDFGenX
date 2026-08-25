"""IDFGenX 可复用领域包。

本包将承载共享模式、确定性编译器、数据工厂、评估代码和服务编排；HTTP 专用适配器
保留在顶层 :mod:`server` 包中。
"""

from idfgenx import config, errors
from idfgenx.config import IDFGenXConfig, load_config
from idfgenx.errors import ConfigurationError, ConversionError, ErrorCode, IDFGenXError, ResolutionError


__all__ = [
    "ConfigurationError",
    "ConversionError",
    "ErrorCode",
    "IDFGenXConfig",
    "IDFGenXError",
    "ResolutionError",
    "__version__",
    "config",
    "errors",
    "load_config",
]

__version__ = "0.1.0"
