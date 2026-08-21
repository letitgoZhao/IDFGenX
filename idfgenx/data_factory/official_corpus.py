"""构建可追溯的 EnergyPlus v23.1 官方 IDF 语料快照。

本模块扫描 ``ExampleFiles`` 和 ``DataSets`` 随附的全部 IDF，仅复制符合项目
范围且完成去重的模型，以及显式允许的模板；同时为每个扫描源保留一条清单记录。
EnergyPlus 原始安装目录始终作为不可变输入，复制文件与源文件逐字节一致，并记录
SHA-256 来源信息。

扫描器有意只依赖 Python 标准库。轻量 IDF 分词仅用于建档和策略检查；后续质量门禁
仍以 EnergyPlus ``ConvertInputFormat`` 作为权威解析器。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import shutil
import sys
import uuid
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Iterable, Iterator, Sequence


CORPUS_SCHEMA_VERSION = "energyplus-official-corpus-1.0"
EXPECTED_ENERGYPLUS_VERSION = "23.1"

# 这些 DataSets 提供可复用的围护结构、日程和窗体定义。
# 设备性能曲线与 HVAC 部件库不属于项目范围，因此明确排除。
TEMPLATE_ALLOWLIST = frozenset(
    {
        "ASHRAE_2005_HOF_Materials.idf",
        "CompositeWallConstructions.idf",
        "Schedules.idf",
        "SurfaceColorSchemes.idf",
        "USHolidays-DST.idf",
        "WindowBlindMaterials.idf",
        "WindowConstructs.idf",
        "WindowGasMaterials.idf",
        "WindowGlassMaterials.idf",
        "WindowScreenMaterials.idf",
        "WindowShadeMaterials.idf",
    }
)

# 核心种子采用人工审核后的显式名单，避免自动评分把同一官方案例家族的功能变体
# 重复带入项目。路径相对于 EnergyPlus 安装根目录，并作为数据快照的稳定契约。
SIMPLE_SEED_ALLOWLIST = frozenset(
    {
        "ExampleFiles/1ZoneUncontrolled.idf",
        "ExampleFiles/1ZoneUncontrolled3SurfaceZone.idf",
        "ExampleFiles/1ZoneUncontrolled_OtherEquipmentWithFuel.idf",
        "ExampleFiles/1ZoneUncontrolled_Win_ASH55_Thermal_Comfort.idf",
        "ExampleFiles/BasicsFiles/Exercise1A.idf",
        "ExampleFiles/BasicsFiles/Exercise1B-Solution.idf",
        "ExampleFiles/BasicsFiles/Exercise1C-Solution.idf",
        "ExampleFiles/BasicsFiles/Exercise1D-Solution.idf",
        "ExampleFiles/CmplxGlz_SchedSurfGains.idf",
        "ExampleFiles/CmplxGlz_SingleZone_DoubleClearAir.idf",
        "ExampleFiles/EquivalentLayerWindow.idf",
        "ExampleFiles/VaryingLocationAndOrientation.idf",
    }
)

COMPLEX_SEED_ALLOWLIST = frozenset(
    {
        "ExampleFiles/BasicsFiles/Exercise2.idf",
        "ExampleFiles/DaylightingDeviceShelf.idf",
        "ExampleFiles/DaylightingDeviceTubular.idf",
        "ExampleFiles/DElight-Detailed-Comparison.idf",
        "ExampleFiles/Flr_Rf_8Sides.idf",
        "ExampleFiles/GeometryTest.idf",
        "ExampleFiles/InternalMass_wZoneList.idf",
        "ExampleFiles/PassiveTrombeWall.idf",
        "ExampleFiles/PurchAirTables_SQL.idf",
        "ExampleFiles/PurchAirWindowBlind.idf",
        "ExampleFiles/PurchAirWithDaylighting.idf",
        "ExampleFiles/PurchAirWithDaylightingAndShadeControl.idf",
        "ExampleFiles/PurchAirWithDoubleFacadeDaylighting.idf",
        "ExampleFiles/ReflectiveAdjacentBuilding.idf",
        "ExampleFiles/SolarShadingTest.idf",
        "ExampleFiles/StackedZonesWithInterzoneIRTLayers.idf",
        "ExampleFiles/StormWindow.idf",
        "ExampleFiles/SurfaceTest.idf",
        "ExampleFiles/UserInputViewFactorFile-LshapedZone.idf",
        "ExampleFiles/WindowTestsSimple.idf",
    }
)

GEOMETRY_REFERENCE_ALLOWLIST = frozenset(
    {
        "ExampleFiles/1ZoneParameterAspect.idf",
        "ExampleFiles/5Zone_IdealLoadsAirSystems_ReturnPlenum.idf",
        "ExampleFiles/5ZoneAirCooledWithSpaces.idf",
        "ExampleFiles/5ZoneCostEst.idf",
        "ExampleFiles/5ZoneSupRetPlenRAB.idf",
        "ExampleFiles/ActiveTrombeWall.idf",
        "ExampleFiles/AirflowNetwork3zVent.idf",
        "ExampleFiles/AirflowNetwork_Attic_Duct.idf",
        "ExampleFiles/ASHRAE901_ApartmentHighRise_STD2019_Denver.idf",
        "ExampleFiles/ASHRAE901_ApartmentMidRise_STD2019_Denver.idf",
        "ExampleFiles/ASHRAE901_OfficeSmall_STD2019_Denver.idf",
        "ExampleFiles/ASHRAE901_Warehouse_STD2019_Denver.idf",
        "ExampleFiles/AtticRoof_RadiantBarriers.idf",
        "ExampleFiles/BasicsFiles/AdultEducationCenter.idf",
        "ExampleFiles/LBuilding-G000.idf",
        "ExampleFiles/MultiStory.idf",
        "ExampleFiles/Plenum.idf",
        "ExampleFiles/RefBldgLargeOfficeNew2004_Chicago.idf",
        "ExampleFiles/RefBldgPrimarySchoolNew2004_Chicago.idf",
        "ExampleFiles/RefBldgSmallHotelNew2004_Chicago.idf",
        "ExampleFiles/RefBldgStand-aloneRetailNew2004_Chicago.idf",
        "ExampleFiles/RefBldgWarehouseNew2004_Chicago.idf",
        "ExampleFiles/SingleFamilyHouse_TwoSpeed_ZoneAirBalance.idf",
        "ExampleFiles/SurfacePropTest_SurfLWR.idf",
        "ExampleFiles/UserDefinedRoomAirPatterns.idf",
    }
)

MAX_SELECTED_IDF_COUNT = 90

GEOMETRY_TYPES = frozenset(
    {
        "globalgeometryrules",
        "zone",
        "space",
        "spacelist",
        "zonesurface:detail",
        "buildingsurface:detailed",
        "fenestrationsurface:detailed",
        "shading:site:detailed",
        "shading:building:detailed",
        "shading:zone:detailed",
        "wall:detailed",
        "roofceiling:detailed",
        "floor:detailed",
    }
)

# 输出请求不会改变 IDFGenX 关心的建筑事实。语义哈希忽略这些对象后，可以合并
# 大量仅报表配置不同的官方变体。
SEMANTIC_HASH_IGNORED_PREFIXES = (
    "output:",
    "outputcontrol:",
    "meter:custom",
    "table:",
)
SEMANTIC_HASH_IGNORED_EXACT = frozenset({"version"})

ALLOWED_ZONE_HVAC_TYPES = frozenset(
    {
        "zonehvac:idealloadsairsystem",
        "zonehvac:equipmentconnections",
        "zonehvac:equipmentlist",
    }
)

# 这些前缀覆盖永久排除在项目范围之外的真实风环、水环和物理设备。
# IDF 对象类型不区分大小写，因此比较时有意统一使用小写。
UNSUPPORTED_HVAC_PREFIXES = (
    "airloophvac",
    "plantloop",
    "branch",
    "connector",
    "airterminal:",
    "airconditioner:",
    "airdistributionunit",
    "fan:",
    "coil:",
    "boiler:",
    "chiller:",
    "pump:",
    "controller:",
    "setpointmanager:",
    "availabilitymanager:",
    "coolingtower:",
    "fluidcooler:",
    "evaporativefluidcooler:",
    "evaporativecooler:",
    "heatexchanger:",
    "districtheating",
    "districtcooling",
    "waterheater:",
    "thermalstorage:",
    "refrigeration:",
    "generator:",
    "electricloadcenter:",
    "groundheatexchanger:",
    "humidifier:",
    "dehumidifier:",
    "unitarysystem",
    "zoneunitarysystem",
    "sizing:system",
    "sizing:plant",
    "zonecooltower:",
    "zoneearthtube",
    "zonethermalchimney",
)

UNSUPPORTED_FEATURE_PREFIXES = (
    "energymanagementsystem:",
    "pythonplugin:",
    "externalinterface:",
    "functionalmockupunit",
    "fmuimport:",
    "airflownetwork:",
    "groundheattransfer:",
    "foundation:",
    "roomair:",
    "site:grounddomain:",
)

EXTERNAL_DEPENDENCY_TYPES = frozenset(
    {
        "schedule:file",
        "schedule:file:shading",
        "construction:windowdatafile",
        "externalinterface:functionalmockupunitimport",
        "externalinterface:functionalmockupunitimport:from:variable",
        "externalinterface:functionalmockupunitimport:to:actuator",
        "externalinterface:functionalmockupunitimport:to:schedule",
        "externalinterface:functionalmockupunitimport:to:variable",
        "pythonplugin:searchpaths",
    }
)


@dataclass(frozen=True)
class IdfObject:
    """用于建档和哈希计算的轻量 IDF 对象。

    属性：
        object_type: 转为小写的 EnergyPlus 对象类型。
        fields: 对象类型之后去除首尾空白的字段值。
    """

    object_type: str
    fields: tuple[str, ...]

    def canonical_text(self) -> str:
        """返回已规范空白且不区分大小写的对象表示。"""

        normalized_fields = [normalize_field(value) for value in self.fields]
        return ",".join((self.object_type, *normalized_fields)) + ";"


@dataclass
class SourceRecord:
    """单个 EnergyPlus 官方 IDF 文件的可序列化清单记录。"""

    source_kind: str
    source_relative_path: str
    source_sha256: str
    size_bytes: int
    detected_encoding: str
    object_count: int
    object_type_counts: dict[str, int]
    normalized_sha256: str
    semantic_sha256: str
    geometry_sha256: str | None
    structure_sha256: str
    zone_count: int
    surface_count: int
    fenestration_count: int
    shading_count: int
    interzone_surface_count: int
    nonquad_surface_count: int
    has_ideal_loads: bool
    unsupported_hvac_types: list[str]
    unsupported_feature_types: list[str]
    external_dependency_types: list[str]
    complexity: str | None
    complexity_reasons: list[str]
    training_eligible: bool
    rejection_reasons: list[str]
    duplicate_of: str | None = None
    selected_role: str | None = None
    copied_relative_path: str | None = None
    copied_sha256: str | None = None

    def to_json(self) -> dict[str, object]:
        """返回字段稳定且兼容 JSON 的字典表示。"""

        return asdict(self)


def normalize_field(value: str) -> str:
    """在不修改源文件的前提下规范 IDF 字段，以便稳定比较。

    参数：
        value: 移除注释后的原始字段文本。

    返回：
        合并内部连续空白并转为小写的文本。
    """

    return " ".join(value.strip().split()).casefold()


def strip_idf_comments(text: str) -> str:
    """移除 IDF 文本中以 ``!`` 开始的 EnergyPlus 行尾注释。

    EnergyPlus 官方样例的对象名不依赖字面量感叹号。这里有意保持分词器足够简单，
    使清单生成不加载 IDD 也能稳定复现；权威语法校验由后续流程单独完成。

    参数：
        text: 原始 IDF 文本。

    返回：
        移除注释后缀、保留原始行结构的文本。
    """

    return "\n".join(line.split("!", 1)[0] for line in text.splitlines())


def parse_idf_objects(text: str) -> list[IdfObject]:
    """从 IDF 文档中解析对象类型及字段。

    参数：
        text: 已解码的 IDF 源文本。

    返回：
        按源文件顺序排列的对象；空片段和纯注释片段会被忽略。
    """

    objects: list[IdfObject] = []
    for segment in strip_idf_comments(text).split(";"):
        if not segment.strip():
            continue
        tokens = [token.strip() for token in segment.split(",")]
        object_type = normalize_field(tokens[0])
        if not object_type:
            continue
        objects.append(IdfObject(object_type, tuple(tokens[1:])))
    return objects


def read_text_with_fallback(path: Path) -> tuple[str, str]:
    """读取官方 IDF，并记录成功使用的文本编码。

    参数：
        path: EnergyPlus 安装目录中的 IDF 文件。

    返回：
        包含解码文本和编码名称的元组。

    异常：
        UnicodeError: 所有受支持编码均无法解码该文件。
    """

    raw = path.read_bytes()
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            return raw.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise UnicodeError(f"Unable to decode official IDF: {path}")


def sha256_bytes(content: bytes) -> str:
    """返回用于不可变来源校验的小写 SHA-256 摘要。"""

    return hashlib.sha256(content).hexdigest()


def sha256_text(parts: Iterable[str]) -> str:
    """计算确定性 UTF-8 字符串序列的哈希。"""

    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.encode("utf-8"))
        digest.update(b"\n")
    return digest.hexdigest()


def is_semantic_hash_ignored(object_type: str) -> bool:
    """判断对象是否仅控制报表或序列化输出。"""

    return object_type in SEMANTIC_HASH_IGNORED_EXACT or object_type.startswith(
        SEMANTIC_HASH_IGNORED_PREFIXES
    )


def unsupported_hvac_types(object_types: Iterable[str]) -> list[str]:
    """查找超出 IDFGenX 范围的真实 HVAC 设备和拓扑。"""

    unsupported: set[str] = set()
    for object_type in object_types:
        if object_type.startswith("zonehvac:"):
            if object_type not in ALLOWED_ZONE_HVAC_TYPES:
                unsupported.add(object_type)
            continue
        if object_type.startswith("hvactemplate:"):
            # 即使 IdealLoads 模板也依赖 ExpandObjects，因此只保留为参考材料，
            # 不作为规范训练标签。
            unsupported.add(object_type)
            continue
        if object_type.startswith(UNSUPPORTED_HVAC_PREFIXES):
            unsupported.add(object_type)
    return sorted(unsupported)


def unsupported_feature_types(object_types: Iterable[str]) -> list[str]:
    """查找首版排除的高级执行特性。"""

    return sorted(
        {
            object_type
            for object_type in object_types
            if object_type.startswith(UNSUPPORTED_FEATURE_PREFIXES)
        }
    )


def find_external_dependency_types(object_types: Iterable[str]) -> list[str]:
    """返回依赖 IDF 外部文件或运行时的对象类型。"""

    return sorted(set(object_types).intersection(EXTERNAL_DEPENDENCY_TYPES))


def _extract_vertex_count(obj: IdfObject) -> int | None:
    """根据末尾坐标字段推断详细表面的顶点数。

    EnergyPlus 增加 Space 支持后调整过 IDD 字段位置。通过查找“有限整数 + 数量恰好
    匹配的数值坐标”，可以避免清单扫描器绑定某一版固定字段位置。
    """

    fields = obj.fields
    candidates: list[int] = []
    for index, raw_value in enumerate(fields):
        try:
            numeric_value = float(raw_value.strip())
        except (TypeError, ValueError):
            continue
        if not math.isfinite(numeric_value) or not numeric_value.is_integer():
            continue
        count = int(numeric_value)
        if count < 3:
            continue
        coordinates = fields[index + 1 : index + 1 + (3 * count)]
        if len(coordinates) != 3 * count:
            continue
        try:
            for coordinate in coordinates:
                float(coordinate.strip())
        except ValueError:
            continue
        candidates.append(count)
    return candidates[-1] if candidates else None


def _is_interzone_surface(obj: IdfObject) -> bool:
    """检测表面对表面的外边界条件。"""

    # 表面类型字段也常出现 Wall、Floor 或 Roof；元数据字段中的精确值 Surface
    # 才是跨版本更稳健的判断信号。
    return any(normalize_field(value) == "surface" for value in obj.fields[:12])


def classify_complexity(
    *,
    zone_count: int,
    surface_count: int,
    fenestration_count: int,
    shading_count: int,
    interzone_surface_count: int,
    nonquad_surface_count: int,
) -> tuple[str, list[str]]:
    """使用可审计的不变量将几何分类为简单或复杂。

    简单模型有意采用严格边界：单热区、最多六个详细围护表面、无热区间配对表面、
    无遮阳且所有表面均为四边形。仅窗户数量较多，不会使原本为盒状的几何变复杂。
    """

    reasons: list[str] = []
    if zone_count > 1:
        reasons.append("multi_zone")
    if surface_count > 6:
        reasons.append("more_than_six_surfaces")
    if shading_count:
        reasons.append("has_detailed_shading")
    if interzone_surface_count:
        reasons.append("has_interzone_surfaces")
    if nonquad_surface_count:
        reasons.append("has_nonquad_surfaces")
    if fenestration_count > 12:
        reasons.append("many_fenestration_surfaces")
    return ("complex" if reasons else "simple"), reasons


def _hash_objects(objects: Iterable[IdfObject], *, sort_objects: bool) -> str:
    canonical = [obj.canonical_text() for obj in objects]
    if sort_objects:
        canonical.sort()
    return sha256_text(canonical)


def build_source_record(path: Path, source_root: Path, source_kind: str) -> SourceRecord:
    """扫描一个官方 IDF，并返回完整清单元数据。

    参数：
        path: 源 IDF 路径。
        source_root: 用于生成相对来源路径的 EnergyPlus 安装根目录。
        source_kind: ``example`` 或 ``dataset``。

    返回：
        可序列化的源记录；此函数不会修改或复制源文件。
    """

    raw = path.read_bytes()
    text, encoding = read_text_with_fallback(path)
    objects = parse_idf_objects(text)
    counts = Counter(obj.object_type for obj in objects)
    object_types = set(counts)

    detailed_surfaces = [
        obj for obj in objects if obj.object_type == "buildingsurface:detailed"
    ]
    fenestration = [
        obj for obj in objects if obj.object_type == "fenestrationsurface:detailed"
    ]
    shading = [
        obj
        for obj in objects
        if obj.object_type
        in {
            "shading:site:detailed",
            "shading:building:detailed",
            "shading:zone:detailed",
        }
    ]
    interzone_count = sum(_is_interzone_surface(obj) for obj in detailed_surfaces)
    vertex_counts = [_extract_vertex_count(obj) for obj in detailed_surfaces]
    nonquad_count = sum(count is not None and count != 4 for count in vertex_counts)

    zone_count = counts.get("zone", 0)
    complexity: str | None = None
    complexity_reasons: list[str] = []
    if zone_count and detailed_surfaces:
        complexity, complexity_reasons = classify_complexity(
            zone_count=zone_count,
            surface_count=len(detailed_surfaces),
            fenestration_count=len(fenestration),
            shading_count=len(shading),
            interzone_surface_count=interzone_count,
            nonquad_surface_count=nonquad_count,
        )

    unsupported_hvac = unsupported_hvac_types(object_types)
    unsupported_features = unsupported_feature_types(object_types)
    external_dependencies = find_external_dependency_types(object_types)
    rejection_reasons: list[str] = []
    if not zone_count:
        rejection_reasons.append("missing_zone")
    if not detailed_surfaces:
        rejection_reasons.append("missing_buildingsurface_detailed")
    if unsupported_hvac:
        rejection_reasons.append("unsupported_hvac")
    if unsupported_features:
        rejection_reasons.append("unsupported_feature")
    if external_dependencies:
        rejection_reasons.append("external_dependency")

    semantic_objects = [
        obj for obj in objects if not is_semantic_hash_ignored(obj.object_type)
    ]
    geometry_objects = [obj for obj in objects if obj.object_type in GEOMETRY_TYPES]
    structure_parts = [
        f"{object_type}:{count}"
        for object_type, count in sorted(counts.items())
        if not is_semantic_hash_ignored(object_type)
    ]

    return SourceRecord(
        source_kind=source_kind,
        source_relative_path=path.relative_to(source_root).as_posix(),
        source_sha256=sha256_bytes(raw),
        size_bytes=len(raw),
        detected_encoding=encoding,
        object_count=len(objects),
        object_type_counts=dict(sorted(counts.items())),
        normalized_sha256=_hash_objects(objects, sort_objects=False),
        semantic_sha256=_hash_objects(semantic_objects, sort_objects=True),
        geometry_sha256=(
            _hash_objects(geometry_objects, sort_objects=True)
            if geometry_objects
            else None
        ),
        structure_sha256=sha256_text(structure_parts),
        zone_count=zone_count,
        surface_count=len(detailed_surfaces),
        fenestration_count=len(fenestration),
        shading_count=len(shading),
        interzone_surface_count=interzone_count,
        nonquad_surface_count=nonquad_count,
        has_ideal_loads="zonehvac:idealloadsairsystem" in object_types,
        unsupported_hvac_types=unsupported_hvac,
        unsupported_feature_types=unsupported_features,
        external_dependency_types=external_dependencies,
        complexity=complexity,
        complexity_reasons=complexity_reasons,
        training_eligible=not rejection_reasons,
        rejection_reasons=rejection_reasons,
    )


def _record_preference(record: SourceRecord) -> tuple[int, int, str]:
    """确定优先级，使体积最小、目录层级最浅的官方代表胜出。"""

    depth = record.source_relative_path.count("/")
    return depth, record.size_bytes, record.source_relative_path.casefold()


def select_records(
    records: list[SourceRecord],
    *,
    simple_seed_paths: set[str] | frozenset[str] = SIMPLE_SEED_ALLOWLIST,
    complex_seed_paths: set[str] | frozenset[str] = COMPLEX_SEED_ALLOWLIST,
    geometry_reference_paths: set[str] | frozenset[str] = GEOMETRY_REFERENCE_ALLOWLIST,
) -> None:
    """按显式审核名单分配入选角色，同时建立重复文件关联。

    参数：
        records: 全量官方文件清单；函数会原地更新选择结果。
        simple_seed_paths: 人工审核的简单种子相对路径。
        complex_seed_paths: 人工审核的复杂种子相对路径。
        geometry_reference_paths: 只供几何学习的参考文件相对路径。

    异常：
        ValueError: 名单重叠、文件缺失、种子不符合范围或总量超过硬上限。
    """

    selected_path_groups = (
        set(simple_seed_paths),
        set(complex_seed_paths),
        set(geometry_reference_paths),
    )
    if any(
        left.intersection(right)
        for index, left in enumerate(selected_path_groups)
        for right in selected_path_groups[index + 1 :]
    ):
        raise ValueError("简单种子、复杂种子和几何参考名单不得重叠")

    records_by_path = {record.source_relative_path: record for record in records}
    requested_paths = set().union(*selected_path_groups)
    missing_paths = requested_paths.difference(records_by_path)
    if missing_paths:
        raise ValueError(f"审核名单中的官方文件不存在: {sorted(missing_paths)}")

    # 语义重复关系覆盖全部合格候选，但人工名单中的文件优先成为该组代表。
    eligible_groups: dict[str, list[SourceRecord]] = defaultdict(list)
    for record in records:
        if record.source_kind == "example" and record.training_eligible:
            eligible_groups[record.semantic_sha256].append(record)
    for group in eligible_groups.values():
        reviewed = [item for item in group if item.source_relative_path in requested_paths]
        if len(reviewed) > 1:
            raise ValueError(
                "审核名单包含语义重复文件: "
                + str(sorted(item.source_relative_path for item in reviewed))
            )
        representative = reviewed[0] if reviewed else min(group, key=_record_preference)
        for duplicate in group:
            if duplicate is representative:
                continue
            duplicate.duplicate_of = representative.source_relative_path
            duplicate.rejection_reasons.append("semantic_duplicate")

    for path in simple_seed_paths:
        record = records_by_path[path]
        if not record.training_eligible or record.complexity != "simple":
            raise ValueError(f"简单种子不符合项目范围或复杂度规则: {path}")
        record.selected_role = "seed_simple"

    for path in complex_seed_paths:
        record = records_by_path[path]
        if not record.training_eligible or record.complexity != "complex":
            raise ValueError(f"复杂种子不符合项目范围或复杂度规则: {path}")
        record.selected_role = "seed_complex"

    # 几何参考允许保留超范围系统，但要求它确实提供复杂几何，且绝不作为训练标签。
    for path in geometry_reference_paths:
        record = records_by_path[path]
        if record.source_kind != "example" or record.complexity != "complex":
            raise ValueError(f"几何参考缺少可用复杂几何: {path}")
        record.selected_role = "reference_geometry"

    geometry_groups: dict[str, list[SourceRecord]] = defaultdict(list)
    for record in records:
        if (
            record.source_kind == "example"
            and not record.training_eligible
            and record.complexity == "complex"
            and record.geometry_sha256
        ):
            geometry_groups[record.geometry_sha256].append(record)
    for group in geometry_groups.values():
        reviewed = [
            item for item in group if item.source_relative_path in geometry_reference_paths
        ]
        representative = reviewed[0] if reviewed else min(group, key=_record_preference)
        for duplicate in group:
            if duplicate is representative or duplicate.duplicate_of is not None:
                continue
            duplicate.duplicate_of = representative.source_relative_path

    for record in records:
        if record.source_kind != "dataset":
            continue
        filename = Path(record.source_relative_path).name
        if filename in TEMPLATE_ALLOWLIST:
            record.selected_role = "template"
        else:
            record.rejection_reasons.append("template_not_allowlisted")

    selected_count = sum(record.selected_role is not None for record in records)
    if selected_count > MAX_SELECTED_IDF_COUNT:
        raise ValueError(
            f"入选官方 IDF 数量 {selected_count} 超过硬上限 {MAX_SELECTED_IDF_COUNT}"
        )


def _copy_target_for(record: SourceRecord) -> Path:
    """返回入选记录在语料目录中的相对目标路径。"""

    source_relative = Path(record.source_relative_path)
    if record.selected_role == "seed_simple":
        relative_under_examples = source_relative.relative_to("ExampleFiles")
        return Path("idf/simple") / relative_under_examples
    if record.selected_role == "seed_complex":
        relative_under_examples = source_relative.relative_to("ExampleFiles")
        return Path("idf/complex") / relative_under_examples
    if record.selected_role == "reference_geometry":
        relative_under_examples = source_relative.relative_to("ExampleFiles")
        return Path("idf/geometry_references") / relative_under_examples
    if record.selected_role == "template":
        return Path("idf/templates") / source_relative.name
    raise ValueError(f"Record is not selected: {record.source_relative_path}")


def _write_json(path: Path, payload: object) -> None:
    """写入确定性、便于人工阅读的 UTF-8 JSON。"""

    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _write_jsonl(path: Path, records: Iterable[SourceRecord]) -> None:
    """按确定性的源路径顺序写入清单记录。"""

    ordered = sorted(records, key=lambda record: record.source_relative_path.casefold())
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        for record in ordered:
            handle.write(
                json.dumps(record.to_json(), ensure_ascii=False, sort_keys=True) + "\n"
            )


def _selection_policy_payload() -> dict[str, object]:
    """导出可执行的筛选常量，供后续审计复现。"""

    return {
        "schema_version": CORPUS_SCHEMA_VERSION,
        "energyplus_version": EXPECTED_ENERGYPLUS_VERSION,
        "simple_seed_allowlist": sorted(SIMPLE_SEED_ALLOWLIST),
        "complex_seed_allowlist": sorted(COMPLEX_SEED_ALLOWLIST),
        "geometry_reference_allowlist": sorted(GEOMETRY_REFERENCE_ALLOWLIST),
        "template_allowlist": sorted(TEMPLATE_ALLOWLIST),
        "maximum_selected_idf_count": MAX_SELECTED_IDF_COUNT,
        "allowed_zone_hvac_types": sorted(ALLOWED_ZONE_HVAC_TYPES),
        "unsupported_hvac_prefixes": list(UNSUPPORTED_HVAC_PREFIXES),
        "unsupported_feature_prefixes": list(UNSUPPORTED_FEATURE_PREFIXES),
        "external_dependency_types": sorted(EXTERNAL_DEPENDENCY_TYPES),
        "semantic_hash_ignored_prefixes": list(SEMANTIC_HASH_IGNORED_PREFIXES),
        "simple_geometry_rule": {
            "zone_count": 1,
            "maximum_surface_count": 6,
            "interzone_surface_count": 0,
            "shading_count": 0,
            "nonquad_surface_count": 0,
        },
    }


def _summary_payload(records: Sequence[SourceRecord]) -> dict[str, object]:
    """汇总清单和入选数量，供报告与持续集成使用。"""

    roles = Counter(record.selected_role or "not_selected" for record in records)
    rejection_reasons = Counter(
        reason for record in records for reason in record.rejection_reasons
    )
    return {
        "schema_version": CORPUS_SCHEMA_VERSION,
        "energyplus_version": EXPECTED_ENERGYPLUS_VERSION,
        "total_records": len(records),
        "example_records": sum(record.source_kind == "example" for record in records),
        "dataset_records": sum(record.source_kind == "dataset" for record in records),
        "training_eligible_before_dedup": sum(
            record.source_kind == "example" and record.training_eligible
            for record in records
        ),
        "selected_roles": dict(sorted(roles.items())),
        "selected_idf_count": sum(
            record.selected_role is not None for record in records
        ),
        "rejection_reasons": dict(sorted(rejection_reasons.items())),
        "selected_bytes": sum(
            record.size_bytes for record in records if record.selected_role
        ),
    }


def build_official_corpus(energyplus_root: Path, output_root: Path) -> dict[str, object]:
    """扫描、筛选、复制并记录 EnergyPlus 官方语料。

    参数：
        energyplus_root: EnergyPlus v23.1 安装目录。
        output_root: 新的不可变语料目录；该目录必须尚不存在。

    返回：
        与 ``summary.json`` 写入内容相同的汇总数据。

    异常：
        FileExistsError: ``output_root`` 已存在。
        FileNotFoundError: 缺少必需的 EnergyPlus 目录或许可证。
        RuntimeError: 复制文件的哈希与源文件不同。
    """

    energyplus_root = energyplus_root.resolve()
    output_root = output_root.resolve()
    example_root = energyplus_root / "ExampleFiles"
    dataset_root = energyplus_root / "DataSets"
    license_path = energyplus_root / "LICENSE.txt"
    for required in (example_root, dataset_root, license_path):
        if not required.exists():
            raise FileNotFoundError(f"Required EnergyPlus v23.1 input is missing: {required}")
    if output_root.exists():
        raise FileExistsError(
            f"Output corpus already exists and is treated as immutable: {output_root}"
        )

    build_root = output_root.with_name(f".{output_root.name}.build-{uuid.uuid4().hex}")
    build_root.mkdir(parents=True, exist_ok=False)
    try:
        records: list[SourceRecord] = []
        for path in sorted(example_root.rglob("*.idf"), key=lambda item: item.as_posix().casefold()):
            records.append(build_source_record(path, energyplus_root, "example"))
        for path in sorted(dataset_root.rglob("*.idf"), key=lambda item: item.as_posix().casefold()):
            records.append(build_source_record(path, energyplus_root, "dataset"))

        select_records(records)
        for record in records:
            if not record.selected_role:
                continue
            source = energyplus_root / Path(record.source_relative_path)
            destination_relative = _copy_target_for(record)
            destination = build_root / destination_relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
            copied_hash = sha256_bytes(destination.read_bytes())
            if copied_hash != record.source_sha256:
                raise RuntimeError(
                    f"Copied file hash mismatch: {record.source_relative_path}"
                )
            record.copied_relative_path = destination_relative.as_posix()
            record.copied_sha256 = copied_hash

        shutil.copyfile(license_path, build_root / "LICENSE.txt")
        summary = _summary_payload(records)
        metadata_root = build_root / "metadata"
        metadata_root.mkdir(parents=True, exist_ok=False)
        _write_json(metadata_root / "selection_policy.json", _selection_policy_payload())
        _write_json(metadata_root / "summary.json", summary)
        _write_jsonl(metadata_root / "inventory.jsonl", records)
        _write_jsonl(
            metadata_root / "selected_manifest.jsonl",
            (record for record in records if record.selected_role),
        )
        build_root.replace(output_root)
        return summary
    except BaseException:
        # 临时目录由本次调用唯一生成，并且确定为目标目录的同级目录，因此递归清理
        # 被严格限制在本次构建产物内。
        if build_root.exists():
            shutil.rmtree(build_root)
        raise


def build_argument_parser() -> argparse.ArgumentParser:
    """创建用于可复现语料生成的命令行解析器。"""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--energyplus-root",
        type=Path,
        required=True,
        help="EnergyPlus v23.1 安装根目录。",
    )
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="新的不可变输出目录；必须尚不存在。",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """运行官方语料构建器并打印 JSON 汇总。"""

    args = build_argument_parser().parse_args(argv)
    summary = build_official_corpus(args.energyplus_root, args.output_root)
    print(json.dumps(summary, ensure_ascii=False, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
