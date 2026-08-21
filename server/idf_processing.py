import os
import tempfile
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from dotenv import load_dotenv
from geomeppy import IDF

load_dotenv()
logger = logging.getLogger("server.idf_processing")


@dataclass
class ParsedActuator:
    alias: str
    component_type: str
    control_type: str
    actuator_key: str
    zone_name: str
    role: str


@dataclass
class ParsedIDFOptions:
    indoor_variables: Dict[str, Tuple[str, str]]
    meters: Dict[str, str]
    actuators: Dict[str, ParsedActuator]
    warnings: List[str]


class IDFParserException(Exception):
    def __init__(
        self,
        code: str,
        message: str,
        hint: Optional[str] = None,
        status_code: int = 400,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.hint = hint
        self.status_code = status_code


# Backward-compatible name used by existing tests and callers.
IDFParserIssue = IDFParserException


def get_idd_path() -> str:
    """Get the path to Energy+.idd based on environment variables or local fallback."""
    eplus_path = os.environ.get("EPLUS_PATH")
    if eplus_path:
        idd_path = os.path.join(eplus_path, "Energy+.idd")
        if os.path.exists(idd_path):
            return idd_path

    common_paths = [
        "/usr/local/EnergyPlus-23-1-0/Energy+.idd",
    ]
    for path in common_paths:
        if os.path.exists(path):
            return path

    logger.error("EnergyPlus IDD file not found. Checked EPLUS_PATH and common paths.")
    raise FileNotFoundError(
        "Could not find Energy+.idd. Please export EPLUS_PATH before startup."
    )


def decode_idf_bytes(idf_bytes: bytes) -> str:
    for encoding in ("utf-8", "latin-1"):
        try:
            return idf_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise IDFParserException(
        code="idf_decode_failed",
        message="Failed to decode IDF file content.",
        hint="Please save the IDF file in UTF-8 or Latin-1 encoding and upload again.",
    )


def parse_geometry_safe(idf_content: str) -> Dict[str, object]:
    try:
        return parse_idf_geometry(idf_content)
    except FileNotFoundError as exc:
        logger.exception("IDD lookup failed during IDF geometry parsing.")
        raise IDFParserException(
            code="idd_not_found",
            message="EnergyPlus IDD file was not found on the server.",
            hint="Set EPLUS_PATH correctly or install EnergyPlus with Energy+.idd available.",
            status_code=500,
        ) from exc
    except Exception as exc:
        logger.exception("Unhandled geometry parsing exception.")
        raise IDFParserException(
            code="idf_geometry_parse_failed",
            message="Failed to parse IDF geometry.",
            hint="Please validate the IDF syntax and ensure surface definitions are complete.",
        ) from exc


def parse_idf_options(idf_path: Path) -> ParsedIDFOptions:
    if not _ensure_idd_available():
        logger.warning(
            "EnergyPlus IDD not found. Falling back to lightweight IDF option parsing."
        )
        return _parse_idf_options_lightweight(idf_path.read_text(encoding="utf-8"))
    try:
        idf = IDF(str(idf_path))
    except FileNotFoundError as exc:
        logger.warning(
            "EnergyPlus IDD read failed. Falling back to lightweight IDF option parsing."
        )
        return _parse_idf_options_lightweight(idf_path.read_text(encoding="utf-8"))
    except Exception as exc:
        logger.exception("Failed to load IDF file for option extraction: %s", idf_path)
        raise IDFParserException(
            code="idf_load_failed",
            message="Failed to load IDF model for option extraction.",
            hint="Check if the uploaded IDF is compatible with current EnergyPlus IDD version.",
        ) from exc

    zones = [
        str(z.Name).strip()
        for z in idf.idfobjects.get("ZONE", [])
        if str(z.Name).strip()
    ]
    if not zones:
        raise IDFParserException(
            code="zone_missing",
            message="No valid Zone object was found in the IDF.",
            hint="At least one Zone object is required before simulation can start.",
        )

    indoor_variables: Dict[str, Tuple[str, str]] = {}
    for idx, zone_name in enumerate(zones, start=1):
        indoor_variables[f"zone_temp_{idx}"] = ("Zone Air Temperature", zone_name)

    warnings: List[str] = []
    if not idf.idfobjects.get("THERMOSTATSETPOINT:DUALSETPOINT", []):
        warnings.append(
            "DualSetpoint thermostat objects are missing. Default zone temperature actuators are generated as a fallback."
        )

    meters = _extract_electricity_meters(idf)
    actuators = _build_default_dual_setpoint_actuators(zones)
    return ParsedIDFOptions(
        indoor_variables=indoor_variables,
        meters=meters,
        actuators=actuators,
        warnings=warnings,
    )


def parse_idf_geometry(idf_content: str) -> Dict[str, Any]:
    """
    Parse an EnergyPlus IDF model from an in-memory string and extract flattened
    geometry dictionaries for WebGL rendering.
    """
    if not _ensure_idd_available():
        logger.warning(
            "EnergyPlus IDD not found. Falling back to lightweight IDF geometry parsing."
        )
        return _parse_idf_geometry_lightweight(idf_content)

    with tempfile.NamedTemporaryFile(mode="w", suffix=".idf", delete=False) as f:
        f.write(idf_content)
        temp_path = f.name

    try:
        try:
            idf = IDF(temp_path)
        except FileNotFoundError:
            logger.warning(
                "EnergyPlus IDD read failed. Falling back to lightweight IDF geometry parsing."
            )
            return _parse_idf_geometry_lightweight(idf_content)

        zone_list: Dict[str, Dict[str, Any]] = {}
        surf_list: Dict[str, Dict[str, Any]] = {}
        fen_list: Dict[str, Dict[str, Any]] = {}
        shade_list: Dict[str, Dict[str, Any]] = {}

        min_x = min_y = min_z = float("inf")
        max_x = max_y = max_z = float("-inf")

        def update_bounds(x: float, y: float, z: float) -> None:
            nonlocal min_x, min_y, min_z, max_x, max_y, max_z
            min_x, max_x = min(min_x, x), max(max_x, x)
            min_y, max_y = min(min_y, y), max(max_y, y)
            min_z, max_z = min(min_z, z), max(max_z, z)

        is_relative = False
        try:
            rules = idf.idfobjects["GLOBALGEOMETRYRULES"]
            if rules and rules[0].Coordinate_System.lower() == "relative":
                is_relative = True
        except Exception:
            pass

        for zone in idf.idfobjects["ZONE"]:
            zone_name = zone.Name
            x_origin = zone.X_Origin if zone.X_Origin else 0.0
            y_origin = zone.Y_Origin if zone.Y_Origin else 0.0
            z_origin = zone.Z_Origin if zone.Z_Origin else 0.0
            zone_list[zone_name] = {
                "Origin": [x_origin, y_origin, z_origin],
                "Surfaces": [],
                "ZBoundary": [float("inf"), float("-inf")],
            }

        def get_zone_origin(z_name: str) -> List[float]:
            if is_relative and z_name in zone_list:
                return zone_list[z_name]["Origin"]
            return [0.0, 0.0, 0.0]

        for surf in idf.idfobjects["BUILDINGSURFACE:DETAILED"]:
            surf_name = surf.Name
            zone_name = surf.Zone_Name
            z_ox, z_oy, z_oz = get_zone_origin(zone_name)

            vertices = []
            try:
                poly = surf.coords
                if poly:
                    for x, y, z in poly:
                        ax = float(x) + z_ox
                        ay = float(y) + z_oy
                        az = float(z) + z_oz
                        vertices.append([ax, ay, az])
                        update_bounds(ax, ay, az)

                        if zone_name in zone_list:
                            zone_list[zone_name]["ZBoundary"][0] = min(
                                zone_list[zone_name]["ZBoundary"][0], az
                            )
                            zone_list[zone_name]["ZBoundary"][1] = max(
                                zone_list[zone_name]["ZBoundary"][1], az
                            )
            except AttributeError:
                pass

            if zone_name in zone_list:
                zone_list[zone_name]["Surfaces"].append(surf_name)

            surf_list[surf_name] = {
                "Vertices": vertices,
                "Fenestrations": [],
                "OutsideBC": surf.Outside_Boundary_Condition,
                "SurfaceType": surf.Surface_Type,
                "Construction": surf.Construction_Name,
                "ZoneName": zone_name,
            }

        for fen in idf.idfobjects["FENESTRATIONSURFACE:DETAILED"]:
            fen_name = fen.Name
            base_surf = fen.Building_Surface_Name
            z_ox, z_oy, z_oz = 0.0, 0.0, 0.0
            if is_relative and base_surf in surf_list:
                z_name = surf_list[base_surf]["ZoneName"]
                z_ox, z_oy, z_oz = get_zone_origin(z_name)

            vertices = []
            try:
                poly = fen.coords
                if poly:
                    for x, y, z in poly:
                        vertices.append(
                            [float(x) + z_ox, float(y) + z_oy, float(z) + z_oz]
                        )
            except AttributeError:
                pass

            if base_surf in surf_list:
                surf_list[base_surf]["Fenestrations"].append(fen_name)

            fen_list[fen_name] = {
                "Vertices": vertices,
                "Type": fen.Surface_Type,
                "Construction": fen.Construction_Name,
                "BuildingSurfaceName": base_surf,
            }

        for shade in idf.idfobjects["SHADING:BUILDING:DETAILED"]:
            shade_name = shade.Name
            vertices = []
            try:
                poly = shade.coords
                if poly:
                    for x, y, z in poly:
                        vertices.append([float(x), float(y), float(z)])
                        update_bounds(float(x), float(y), float(z))
            except AttributeError:
                pass

            shade_list[shade_name] = {
                "Vertices": vertices,
                "TransmittanceSchedule": shade.Transmittance_Schedule_Name,
            }

        if min_x == float("inf"):
            boundary = [[0, 0, 0], [0, 0, 0]]
            bldg_center = [0, 0, 0]
            bldg_radius = 0
        else:
            boundary = [[min_x, min_y, min_z], [max_x, max_y, max_z]]
            bldg_center = [
                (min_x + max_x) / 2,
                (min_y + max_y) / 2,
                (min_z + max_z) / 2,
            ]
            bldg_radius = max(max_x - min_x, max_y - min_y, max_z - min_z) / 2

        for zone_data in zone_list.values():
            if zone_data["ZBoundary"][0] == float("inf"):
                zone_data["ZBoundary"] = [0, 0]

        return {
            "zoneList": zone_list,
            "surfList": surf_list,
            "fenList": fen_list,
            "shadeList": shade_list,
            "boundary": boundary,
            "bldgCenter": bldg_center,
            "bldgRadius": bldg_radius,
        }
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _ensure_idd_available() -> bool:
    current_idd = IDF.getiddname()
    if current_idd and os.path.exists(str(current_idd)):
        return True
    if current_idd:
        logger.warning("Configured EnergyPlus IDD path does not exist: %s", current_idd)
    try:
        IDF.setiddname(get_idd_path())
    except FileNotFoundError:
        return False
    selected_idd = IDF.getiddname()
    return bool(selected_idd and os.path.exists(str(selected_idd)))


def _build_default_dual_setpoint_actuators(
    zones: List[str],
) -> Dict[str, ParsedActuator]:
    actuators: Dict[str, ParsedActuator] = {}
    for idx, zone_name in enumerate(zones, start=1):
        heat_alias = f"heat_sp_{idx}"
        cool_alias = f"cool_sp_{idx}"
        actuators[heat_alias] = ParsedActuator(
            alias=heat_alias,
            component_type="Zone Temperature Control",
            control_type="Heating Setpoint",
            actuator_key=zone_name,
            zone_name=zone_name,
            role="heating",
        )
        actuators[cool_alias] = ParsedActuator(
            alias=cool_alias,
            component_type="Zone Temperature Control",
            control_type="Cooling Setpoint",
            actuator_key=zone_name,
            zone_name=zone_name,
            role="cooling",
        )
    return actuators


def _parse_idf_options_lightweight(idf_content: str) -> ParsedIDFOptions:
    objects = _parse_idf_objects(idf_content)
    zones = [
        fields[0]
        for fields in objects.get("ZONE", [])
        if fields and fields[0].strip()
    ]
    if not zones:
        raise IDFParserException(
            code="zone_missing",
            message="No valid Zone object was found in the IDF.",
            hint="At least one Zone object is required before simulation can start.",
        )

    indoor_variables = {
        f"zone_temp_{idx}": ("Zone Air Temperature", zone_name)
        for idx, zone_name in enumerate(zones, start=1)
    }
    warnings: List[str] = []
    if not objects.get("THERMOSTATSETPOINT:DUALSETPOINT"):
        warnings.append(
            "DualSetpoint thermostat objects are missing. Default zone temperature actuators are generated as a fallback."
        )

    meter_names = []
    for object_type in ("OUTPUT:METER", "OUTPUT:METER:METERFILEONLY"):
        for fields in objects.get(object_type, []):
            if fields and fields[0].strip():
                meter_names.append(fields[0].strip())
    meters = _build_meter_aliases(meter_names)
    return ParsedIDFOptions(
        indoor_variables=indoor_variables,
        meters=meters,
        actuators=_build_default_dual_setpoint_actuators(zones),
        warnings=warnings,
    )


def _parse_idf_geometry_lightweight(idf_content: str) -> Dict[str, Any]:
    objects = _parse_idf_objects(idf_content)
    zone_list: Dict[str, Dict[str, Any]] = {}
    surf_list: Dict[str, Dict[str, Any]] = {}
    fen_list: Dict[str, Dict[str, Any]] = {}
    shade_list: Dict[str, Dict[str, Any]] = {}

    bounds = _GeometryBounds()
    geometry_rules = objects.get("GLOBALGEOMETRYRULES", [])
    is_relative = bool(
        geometry_rules
        and len(geometry_rules[0]) >= 3
        and geometry_rules[0][2].lower() == "relative"
    )

    for fields in objects.get("ZONE", []):
        if not fields or not fields[0]:
            continue
        zone_name = fields[0]
        origin = [
            _float_field(fields, 2),
            _float_field(fields, 3),
            _float_field(fields, 4),
        ]
        zone_list[zone_name] = {
            "Origin": origin,
            "Surfaces": [],
            "ZBoundary": [float("inf"), float("-inf")],
        }

    def zone_origin(zone_name: str) -> List[float]:
        if is_relative and zone_name in zone_list:
            return zone_list[zone_name]["Origin"]
        return [0.0, 0.0, 0.0]

    for fields in objects.get("BUILDINGSURFACE:DETAILED", []):
        if len(fields) < 11:
            continue
        surf_name = fields[0]
        zone_name = fields[3]
        origin = zone_origin(zone_name)
        vertices = _vertices_from_fields(fields, 11, origin, bounds)
        if zone_name in zone_list:
            zone_list[zone_name]["Surfaces"].append(surf_name)
            for _x, _y, z_value in vertices:
                zone_list[zone_name]["ZBoundary"][0] = min(
                    zone_list[zone_name]["ZBoundary"][0], z_value
                )
                zone_list[zone_name]["ZBoundary"][1] = max(
                    zone_list[zone_name]["ZBoundary"][1], z_value
                )
        surf_list[surf_name] = {
            "Vertices": vertices,
            "Fenestrations": [],
            "OutsideBC": _field_at(fields, 5),
            "SurfaceType": _field_at(fields, 1),
            "Construction": _field_at(fields, 2),
            "ZoneName": zone_name,
        }

    for fields in objects.get("FENESTRATIONSURFACE:DETAILED", []):
        if len(fields) < 9:
            continue
        fen_name = fields[0]
        base_surf = fields[3]
        origin = [0.0, 0.0, 0.0]
        if is_relative and base_surf in surf_list:
            origin = zone_origin(surf_list[base_surf]["ZoneName"])
        vertices = _vertices_from_fields(fields, 9, origin)
        if base_surf in surf_list:
            surf_list[base_surf]["Fenestrations"].append(fen_name)
        fen_list[fen_name] = {
            "Vertices": vertices,
            "Type": _field_at(fields, 1),
            "Construction": _field_at(fields, 2),
            "BuildingSurfaceName": base_surf,
        }

    for fields in objects.get("SHADING:BUILDING:DETAILED", []):
        if len(fields) < 3:
            continue
        shade_name = fields[0]
        shade_vertices = _vertices_from_fields(fields, 3, None, bounds)
        shade_list[shade_name] = {
            "Vertices": shade_vertices,
            "TransmittanceSchedule": _field_at(fields, 1),
        }

    for zone_data in zone_list.values():
        if zone_data["ZBoundary"][0] == float("inf"):
            zone_data["ZBoundary"] = [0, 0]

    return {
        "zoneList": zone_list,
        "surfList": surf_list,
        "fenList": fen_list,
        "shadeList": shade_list,
        "boundary": bounds.boundary,
        "bldgCenter": bounds.center,
        "bldgRadius": bounds.radius,
    }


@dataclass
class _GeometryBounds:
    min_x: float = float("inf")
    min_y: float = float("inf")
    min_z: float = float("inf")
    max_x: float = float("-inf")
    max_y: float = float("-inf")
    max_z: float = float("-inf")

    def update(self, x_value: float, y_value: float, z_value: float) -> None:
        self.min_x = min(self.min_x, x_value)
        self.min_y = min(self.min_y, y_value)
        self.min_z = min(self.min_z, z_value)
        self.max_x = max(self.max_x, x_value)
        self.max_y = max(self.max_y, y_value)
        self.max_z = max(self.max_z, z_value)

    @property
    def boundary(self) -> List[List[float]]:
        if self.min_x == float("inf"):
            return [[0, 0, 0], [0, 0, 0]]
        return [
            [self.min_x, self.min_y, self.min_z],
            [self.max_x, self.max_y, self.max_z],
        ]

    @property
    def center(self) -> List[float]:
        if self.min_x == float("inf"):
            return [0, 0, 0]
        return [
            (self.min_x + self.max_x) / 2,
            (self.min_y + self.max_y) / 2,
            (self.min_z + self.max_z) / 2,
        ]

    @property
    def radius(self) -> float:
        if self.min_x == float("inf"):
            return 0
        return max(
            self.max_x - self.min_x,
            self.max_y - self.min_y,
            self.max_z - self.min_z,
        ) / 2


def _parse_idf_objects(idf_content: str) -> Dict[str, List[List[str]]]:
    objects: Dict[str, List[List[str]]] = {}
    cleaned_lines = []
    for line in idf_content.splitlines():
        cleaned_lines.append(line.split("!", 1)[0])
    for raw_object in "\n".join(cleaned_lines).split(";"):
        fields = [field.strip() for field in raw_object.split(",")]
        if not fields or not fields[0]:
            continue
        object_type = fields[0].upper()
        object_fields = fields[1:]
        objects.setdefault(object_type, []).append(object_fields)
    return objects


def _field_at(fields: List[str], index: int) -> str:
    if index >= len(fields):
        return ""
    return fields[index]


def _float_field(fields: List[str], index: int) -> float:
    try:
        return float(_field_at(fields, index) or 0.0)
    except ValueError:
        return 0.0


def _vertices_from_fields(
    fields: List[str],
    start_index: int,
    origin: Optional[List[float]] = None,
    bounds: Optional[_GeometryBounds] = None,
) -> List[List[float]]:
    origin = origin or [0.0, 0.0, 0.0]
    values = fields[start_index:]
    vertices: List[List[float]] = []
    for index in range(0, len(values) - 2, 3):
        try:
            x_value = float(values[index]) + origin[0]
            y_value = float(values[index + 1]) + origin[1]
            z_value = float(values[index + 2]) + origin[2]
        except ValueError:
            continue
        vertices.append([x_value, y_value, z_value])
        if bounds:
            bounds.update(x_value, y_value, z_value)
    return vertices


def _extract_electricity_meters(idf: IDF) -> Dict[str, str]:
    meter_names: List[str] = []
    for meter_obj in idf.idfobjects.get("OUTPUT:METER", []):
        key_name = str(getattr(meter_obj, "Key_Name", "")).strip()
        if key_name and "electricity" in key_name.lower():
            meter_names.append(key_name)
    for meter_obj in idf.idfobjects.get("OUTPUT:METER:METERFILEONLY", []):
        key_name = str(getattr(meter_obj, "Key_Name", "")).strip()
        if key_name and "electricity" in key_name.lower():
            meter_names.append(key_name)
    return _build_meter_aliases(meter_names)


def _build_meter_aliases(meter_names: List[str]) -> Dict[str, str]:
    if "Electricity:Facility" not in meter_names:
        meter_names.insert(0, "Electricity:Facility")

    unique: List[str] = []
    for name in meter_names:
        if name not in unique:
            unique.append(name)
    selected = unique[:5]
    meters: Dict[str, str] = {}
    for idx, meter_name in enumerate(selected, start=1):
        alias = "elec" if idx == 1 else f"elec_{idx}"
        meters[alias] = meter_name
    return meters


__all__ = [
    "IDFParserException",
    "IDFParserIssue",
    "ParsedActuator",
    "ParsedIDFOptions",
    "decode_idf_bytes",
    "get_idd_path",
    "parse_geometry_safe",
    "parse_idf_geometry",
    "parse_idf_options",
]
