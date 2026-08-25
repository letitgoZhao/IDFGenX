"""编排 ResolvedScenarioSpec 到 canonical epJSON 和 EnergyPlus IDF 的转换。"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
from pathlib import Path
from subprocess import CompletedProcess, TimeoutExpired, run

from idfgenx.compiler.epjson import build_epjson, canonical_epjson_bytes
from idfgenx.compiler.templates import add_system_templates
from idfgenx.compiler.toolchain import EnergyPlusToolchain
from idfgenx.errors import ConversionError
from idfgenx.schemas.resolved import ResolvedScenarioSpec


CONVERSION_TIMEOUT_SECONDS = 120


@dataclass(frozen=True, slots=True)
class CompilationArtifact:
    """描述一次可追溯转换生成的 canonical epJSON 和 IDF 工件。"""

    epjson_path: Path
    idf_path: Path
    epjson_sha256: str
    idf_sha256: str


def compile_scenario(spec: ResolvedScenarioSpec, toolchain: EnergyPlusToolchain, work_dir: Path) -> CompilationArtifact:
    """在调用者独占目录中生成 epJSON 并用 v23.1 ConvertInputFormat 转换为 IDF。"""

    if not work_dir.is_dir():
        raise ConversionError("转换工作目录不存在。", context={"work_dir": str(work_dir)})
    epjson_path = work_dir / "scenario.epJSON"
    document = add_system_templates(build_epjson(spec), spec)
    epjson_bytes = canonical_epjson_bytes(document)
    epjson_path.write_bytes(epjson_bytes)
    try:
        completed: CompletedProcess[str] = run(
            [str(toolchain.convert_input_format), "-o", str(work_dir), str(epjson_path)],
            cwd=work_dir,
            text=True,
            capture_output=True,
            timeout=CONVERSION_TIMEOUT_SECONDS,
            check=False,
        )
    except TimeoutExpired as exc:
        raise ConversionError("ConvertInputFormat 执行超时。", context={"timeout_seconds": CONVERSION_TIMEOUT_SECONDS}, cause=exc) from exc
    idf_path = work_dir / "scenario.idf"
    if completed.returncode != 0 or not idf_path.is_file():
        raise ConversionError(
            "ConvertInputFormat 未生成预期 IDF。",
            context={"return_code": completed.returncode, "stdout": completed.stdout[-2000:], "stderr": completed.stderr[-2000:]},
        )
    return CompilationArtifact(epjson_path=epjson_path, idf_path=idf_path, epjson_sha256=sha256(epjson_bytes).hexdigest(), idf_sha256=sha256(idf_path.read_bytes()).hexdigest())
