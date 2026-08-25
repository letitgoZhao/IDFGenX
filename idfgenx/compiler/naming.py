"""提供 EnergyPlus 对象引用使用的稳定名称生成器。"""

from __future__ import annotations

import re


def stable_name(prefix: str, *parts: str | int) -> str:
    """生成去除空白和路径分隔符的稳定对象名称。

    Args:
        prefix: 对象类型前缀，例如 ``Zone`` 或 ``Surface``。
        parts: 参与名称的确定性组成部分；整数固定补齐为两位。

    Returns:
        用连字符拼接且适合 EnergyPlus 引用的稳定名称。
    """

    normalized = [_normalize_part(prefix)]
    for part in parts:
        normalized.append(f"{part:02d}" if isinstance(part, int) else _normalize_part(part))
    return "-".join(normalized)


def _normalize_part(value: str) -> str:
    """保留 Unicode 字符，同时把对象名中不稳定的分隔符替换为下划线。"""

    normalized = re.sub(r"[\\/\s]+", "_", value.strip())
    normalized = re.sub(r"[^\w.-]", "_", normalized, flags=re.UNICODE)
    return normalized.strip("_.-") or "Unnamed"
