"""Adapt the copied BEM-Nexus simulation core for the standalone demo."""

import csv
import logging
import os
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Tuple, Type

from .idf_processing import decode_idf_bytes, parse_idf_options
from .results import ChartSpec, build_chart_payload

logger = logging.getLogger(__name__)

DEMO_ROOT = Path(__file__).resolve().parents[1]
RUNTIME_ROOT = DEMO_ROOT / "runtime"
SIMULATION_TIMEOUT_SECONDS = 7200.0
DEFAULT_ENERGYPLUS_PATH = Path("/usr/local/EnergyPlus-23-1-0")

WEATHER_VARIABLES = {
    "outdoor_temperature": (
        "Site Outdoor Air Drybulb Temperature",
        "Environment",
    ),
    "outdoor_humidity": (
        "Site Outdoor Air Relative Humidity",
        "Environment",
    ),
    "direct_solar": (
        "Site Direct Solar Radiation Rate per Area",
        "Environment",
    ),
    "wind_speed": ("Site Wind Speed", "Environment"),
}

WEATHER_CHARTS = [
    ChartSpec(
        alias="outdoor_temperature",
        label="Outdoor Dry-Bulb Temperature",
        unit="°C",
        category="weather",
    ),
    ChartSpec(
        alias="outdoor_humidity",
        label="Outdoor Relative Humidity",
        unit="%",
        category="weather",
    ),
    ChartSpec(
        alias="direct_solar",
        label="Direct Solar Radiation",
        unit="W/m²",
        category="weather",
    ),
    ChartSpec(
        alias="wind_speed",
        label="Wind Speed",
        unit="m/s",
        category="weather",
    ),
]


class SimulationServiceException(Exception):
    """Represent a client-safe simulation service failure."""

    def __init__(self, code: str, message: str, hint: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint


def run_simulation(idf_bytes: bytes, epw_bytes: bytes) -> Dict[str, Any]:
    """Run the copied EnergyPlus core and return static chart groups."""
    if not epw_bytes:
        raise SimulationServiceException("epw_empty", "The EPW file is empty.")
    idf_content = decode_idf_bytes(idf_bytes)
    RUNTIME_ROOT.mkdir(parents=True, exist_ok=True)
    runner_type, config_type, controller_type = _load_copied_core()

    try:
        with tempfile.TemporaryDirectory(
            prefix="simulation-",
            dir=RUNTIME_ROOT,
        ) as temp_dir:
            run_root = Path(temp_dir)
            idf_path = run_root / "input.idf"
            epw_path = run_root / "input.epw"
            output_path = run_root / "output"
            idf_path.write_bytes(idf_bytes)
            epw_path.write_bytes(epw_bytes)

            options = parse_idf_options(idf_path)
            chart_specs = _build_chart_specs(options.indoor_variables)
            config = config_type(
                building_path=str(idf_path),
                weather_path=str(epw_path),
                output_path=str(output_path),
                env_name="energyplus-demo",
                mode="empty",
                variables={
                    **WEATHER_VARIABLES,
                    **options.indoor_variables,
                },
                meters={"facility_electricity": "Electricity:Facility"},
                actuators={},
                time_variables=["month", "day_of_month", "hour", "minute"],
                output_csv=True,
                output_log=True,
                max_keep_files=5,
                timesteps_per_hour=_parse_timestep(idf_content),
            )
            runner = runner_type(config, controller_type())
            rows = _run_and_read(runner, output_path)
            payload = build_chart_payload(rows, chart_specs)
            payload["timesteps_per_hour"] = config.timesteps_per_hour
            payload["zone_count"] = len(options.indoor_variables)
            return payload
    except SimulationServiceException:
        raise
    except Exception as exc:
        logger.warning("EnergyPlus run did not complete.", exc_info=True)
        raise SimulationServiceException(
            "simulation_failed",
            "EnergyPlus could not complete with the uploaded files.",
            "Check the EnergyPlus runtime and the uploaded IDF and EPW pair.",
        ) from exc


def _build_chart_specs(
    indoor_variables: Dict[str, tuple[str, str]],
) -> List[ChartSpec]:
    chart_specs = list(WEATHER_CHARTS)
    for alias, (_variable_name, zone_name) in indoor_variables.items():
        chart_specs.append(
            ChartSpec(
                alias=alias,
                label=zone_name,
                unit="°C",
                category="indoor",
            )
        )
    chart_specs.append(
        ChartSpec(
            alias="facility_electricity",
            label="Facility Electricity",
            unit="kWh/timestep",
            category="energy",
            scale=1 / 3_600_000,
        )
    )
    return chart_specs


def _run_and_read(
    runner: Any,
    output_path: Path,
) -> List[Dict[str, Any]]:
    runner.start()
    if runner.thread is None:
        raise SimulationServiceException(
            "simulation_failed",
            "EnergyPlus did not create a runtime thread.",
        )
    runner.thread.join(timeout=SIMULATION_TIMEOUT_SECONDS)
    if runner.thread.is_alive():
        runner.stop()
        raise SimulationServiceException(
            "simulation_failed",
            (
                "EnergyPlus exceeded the "
                f"{int(SIMULATION_TIMEOUT_SECONDS)} second timeout."
            ),
        )
    if runner.failed:
        reason = runner.failure_reason or "runtime failure"
        raise SimulationServiceException(
            "simulation_failed",
            f"EnergyPlus did not complete ({reason}).",
        )

    monitor_path = output_path / "monitor.csv"
    if not monitor_path.is_file():
        raise SimulationServiceException(
            "simulation_failed",
            "EnergyPlus completed without a monitor CSV file.",
        )
    with monitor_path.open("r", encoding="utf-8", newline="") as handle:
        rows = [
            {key: _numeric(value) for key, value in row.items()}
            for row in csv.DictReader(handle)
        ]
    if not rows:
        raise SimulationServiceException(
            "simulation_failed",
            "EnergyPlus completed without usable timestep observations.",
        )
    return rows


def _parse_timestep(idf_content: str) -> int:
    cleaned = "\n".join(line.split("!", 1)[0] for line in idf_content.splitlines())
    match = re.search(r"(?is)\bTimestep\s*,\s*([0-9.]+)\s*;", cleaned)
    if not match:
        return 1
    try:
        value = int(float(match.group(1)))
    except ValueError:
        return 1
    return value if 1 <= value <= 60 else 1


def _numeric(value: Any) -> Any:
    if value in (None, ""):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return value


def energyplus_runtime_available() -> bool:
    """Return whether the copied simulation core can load EnergyPlus."""
    try:
        _load_copied_core()
        return True
    except SimulationServiceException:
        return False


def _load_copied_core() -> Tuple[Type[Any], Type[Any], Type[Any]]:
    runtime_path = Path(os.environ.get("EPLUS_PATH", str(DEFAULT_ENERGYPLUS_PATH)))
    if runtime_path.is_dir() and str(runtime_path) not in sys.path:
        sys.path.insert(0, str(runtime_path))
    try:
        from .controller import EmptyController
        from .modeling import SimulationConfig
        from .runner import EnergyPlusRunner
    except ModuleNotFoundError as exc:
        if exc.name and exc.name.startswith("pyenergyplus"):
            raise SimulationServiceException(
                "simulation_failed",
                "EnergyPlus Python API is unavailable.",
                "Set EPLUS_PATH to the local EnergyPlus installation.",
            ) from exc
        raise
    return EnergyPlusRunner, SimulationConfig, EmptyController
