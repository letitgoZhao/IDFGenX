"""运行并解析 EnergyPlus v23.1 设计日最小仿真。"""

from __future__ import annotations

from pathlib import Path
from subprocess import TimeoutExpired, run

from idfgenx.compiler.compile import CompilationArtifact
from idfgenx.compiler.toolchain import EnergyPlusToolchain
from idfgenx.validation.models import Finding, StageReport, ValidationStatus


SIMULATION_TIMEOUT_SECONDS = 180


def count_energyplus_errors(error_text: str) -> tuple[int, int]:
    """统计 EnergyPlus `.err` 文本中的 Severe 与 Fatal 标记。

    Args:
        error_text: 使用替换策略解码后的 `eplusout.err` 内容。

    Returns:
        依次为 Severe 和 Fatal 的出现次数。
    """

    severe_count = error_text.count("** Severe  **")
    fatal_count = error_text.count("**  Fatal  **") + error_text.count("** Fatal  **")
    return severe_count, fatal_count


def run_design_day_simulation(
    artifact: CompilationArtifact,
    toolchain: EnergyPlusToolchain,
    work_dir: Path,
) -> StageReport:
    """执行 EnergyPlus v23.1 设计日仿真并返回 V5 阶段报告。

    Args:
        artifact: 已由 Compiler 转换且具有 IDF 的工件。
        toolchain: 已完成安装完整性检查的 v23.1 工具链。
        work_dir: 当前调用独占的可写工作目录。

    Returns:
        V5 报告；进程返回码、输出缺失、Severe/Fatal 与超时均为失败。
    """

    if not artifact.idf_path.is_file():
        return _failed("V5_IDF_MISSING", "设计日仿真输入 IDF 不存在。", {"path": str(artifact.idf_path)})
    if not toolchain.energyplus.is_file():
        return StageReport("V5", ValidationStatus.NOT_RUN, (Finding("V5_TOOLCHAIN_UNAVAILABLE", "EnergyPlus 模拟器不可用，未执行设计日仿真。", {"path": str(toolchain.energyplus)}),))
    if not work_dir.is_dir():
        return _failed("V5_WORK_DIR_MISSING", "设计日仿真工作目录不存在。", {"path": str(work_dir)})

    output_dir = work_dir / "simulation"
    output_dir.mkdir(exist_ok=True)
    try:
        completed = run(
            [
                str(toolchain.energyplus),
                "--design-day",
                "--output-directory",
                str(output_dir),
                str(artifact.idf_path),
            ],
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=SIMULATION_TIMEOUT_SECONDS,
            check=False,
        )
    except TimeoutExpired:
        return _failed(
            "V5_TIMEOUT",
            "EnergyPlus 设计日仿真超过时间限制。",
            {"timeout_seconds": SIMULATION_TIMEOUT_SECONDS},
        )
    error_path = output_dir / "eplusout.err"
    error_text = error_path.read_text(encoding="utf-8", errors="replace") if error_path.is_file() else ""
    severe_count, fatal_count = count_energyplus_errors(error_text)
    evidence = {
        "return_code": completed.returncode,
        "error_file_exists": error_path.is_file(),
        "severe_count": severe_count,
        "fatal_count": fatal_count,
        "stdout_tail": completed.stdout[-2000:],
        "stderr_tail": completed.stderr[-2000:],
    }
    if completed.returncode != 0 or not error_path.is_file() or severe_count or fatal_count:
        return _failed("V5_SIMULATION_FAILED", "EnergyPlus 设计日仿真未满足 Severe=0、Fatal=0 的门禁。", evidence)
    return StageReport("V5", ValidationStatus.PASSED)


def _failed(code: str, message: str, evidence: dict[str, object]) -> StageReport:
    """创建包含稳定发现码的 V5 失败报告。"""

    return StageReport("V5", ValidationStatus.FAILED, (Finding(code, message, evidence),))
