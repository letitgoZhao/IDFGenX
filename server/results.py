"""Convert raw EnergyPlus observations into bounded static chart payloads."""

import math
from dataclasses import dataclass
from typing import Any, Dict, List

MAX_CHART_POINTS = 2400


@dataclass(frozen=True)
class ChartSpec:
    """Describe one observation series returned to the frontend."""

    alias: str
    label: str
    unit: str
    category: str
    scale: float = 1.0


def build_chart_payload(
    rows: List[Dict[str, Any]],
    observations: List[ChartSpec],
) -> Dict[str, Any]:
    """Build weather, indoor, and energy groups for the frontend."""
    sampled_rows = _downsample(rows, MAX_CHART_POINTS)
    labels = [_format_time(row, index) for index, row in enumerate(sampled_rows)]
    groups: Dict[str, Any] = {}
    for category in ("weather", "indoor", "energy"):
        category_specs = [item for item in observations if item.category == category]
        series = []
        for item in category_specs:
            values = [
                _scaled_value(row.get(item.alias), item.scale)
                for row in sampled_rows
            ]
            if not any(value is not None for value in values):
                continue
            series.append(
                {
                    "key": item.alias,
                    "label": item.label,
                    "unit": item.unit,
                    "values": values,
                }
            )
        groups[category] = {"labels": labels, "series": series}

    return {
        "row_count": len(rows),
        "sampled_count": len(sampled_rows),
        "weather": groups["weather"],
        "indoor": groups["indoor"],
        "energy": groups["energy"],
    }


def _downsample(
    rows: List[Dict[str, Any]],
    max_points: int,
) -> List[Dict[str, Any]]:
    if len(rows) <= max_points:
        return rows
    stride = math.ceil(len(rows) / max_points)
    sampled = rows[::stride]
    if sampled[-1] is not rows[-1]:
        sampled.append(rows[-1])
    return sampled


def _format_time(row: Dict[str, Any], index: int) -> str:
    month = _integer(row.get("month"))
    day = _integer(row.get("day"))
    hour = _integer(row.get("hour"))
    minute = _integer(row.get("minute"))
    if month > 0 and day > 0:
        return f"{month:02d}/{day:02d} {hour:02d}:{minute:02d}"
    return f"Step {index + 1}"


def _integer(value: Any) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _scaled_value(value: Any, scale: float) -> float | None:
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        return None
    if not math.isfinite(numeric):
        return None
    return numeric * scale
