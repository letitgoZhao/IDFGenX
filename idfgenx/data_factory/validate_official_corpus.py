"""验证 EnergyPlus v23.1 官方 IDF 精选快照。

本模块检查清单哈希，对全部简单/复杂核心种子执行官方格式转换，并对显式选择的
代表模型执行设计日仿真。所有 EnergyPlus 产物均写入临时目录，项目内只保留紧凑的
JSON 验证报告。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Sequence


SIMULATION_REPRESENTATIVES = (
    "ExampleFiles/1ZoneUncontrolled.idf",
    "ExampleFiles/BasicsFiles/Exercise1D-Solution.idf",
    "ExampleFiles/EquivalentLayerWindow.idf",
    "ExampleFiles/BasicsFiles/Exercise2.idf",
    "ExampleFiles/Flr_Rf_8Sides.idf",
    "ExampleFiles/GeometryTest.idf",
    "ExampleFiles/SolarShadingTest.idf",
    "ExampleFiles/StackedZonesWithInterzoneIRTLayers.idf",
)


def load_selected_manifest(corpus_root: Path) -> list[dict[str, object]]:
    """读取精选语料清单，并保持文件中的确定性顺序。"""

    manifest_path = corpus_root / "metadata" / "selected_manifest.jsonl"
    records: list[dict[str, object]] = []
    with manifest_path.open(encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"清单第 {line_number} 行不是 JSON 对象")
            records.append(payload)
    return records


def select_seed_records(
    records: Sequence[dict[str, object]],
) -> list[dict[str, object]]:
    """只返回需要执行转换门禁的简单和复杂核心种子。"""

    return [
        record
        for record in records
        if record.get("selected_role") in {"seed_simple", "seed_complex"}
    ]


def _sha256_file(path: Path) -> str:
    """以流式方式计算文件 SHA-256，避免一次加载大型参考模型。"""

    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def verify_copy_hashes(
    corpus_root: Path,
    records: Sequence[dict[str, object]],
) -> list[dict[str, object]]:
    """核对所有精选副本是否仍与清单和官方源哈希一致。"""

    results: list[dict[str, object]] = []
    for record in records:
        copied_relative_path = str(record["copied_relative_path"])
        copied_path = corpus_root / copied_relative_path
        actual_hash = _sha256_file(copied_path) if copied_path.is_file() else None
        manifest_copy_hash = record.get("copied_sha256")
        source_hash = record.get("source_sha256")
        passed = (
            actual_hash is not None
            and actual_hash == manifest_copy_hash
            and actual_hash == source_hash
        )
        results.append(
            {
                "source_relative_path": record["source_relative_path"],
                "copied_relative_path": copied_relative_path,
                "actual_sha256": actual_hash,
                "passed": passed,
            }
        )
    return results


def _output_tail(text: str | None, maximum_characters: int = 2000) -> str:
    """限制外部工具输出长度，避免验证报告被日志淹没。"""

    return (text or "")[-maximum_characters:]


def run_conversion_validation(
    corpus_root: Path,
    energyplus_root: Path,
    records: Sequence[dict[str, object]],
    *,
    timeout_seconds: int = 60,
) -> list[dict[str, object]]:
    """逐个调用 ConvertInputFormat，验证核心种子可以解析为 epJSON。"""

    converter_path = energyplus_root / "ConvertInputFormat.exe"
    if not converter_path.is_file():
        raise FileNotFoundError(f"找不到 ConvertInputFormat: {converter_path}")

    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="idfgenx-convert-") as temp_dir:
        temporary_root = Path(temp_dir)
        for index, record in enumerate(records):
            copied_path = corpus_root / str(record["copied_relative_path"])
            output_root = temporary_root / f"case-{index:03d}"
            output_root.mkdir(parents=True, exist_ok=False)
            command = [
                str(converter_path),
                "--output",
                str(output_root),
                str(copied_path),
            ]
            started_at = time.perf_counter()
            try:
                completed = subprocess.run(
                    command,
                    cwd=temporary_root,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
                expected_output = output_root / f"{copied_path.stem}.epJSON"
                passed = completed.returncode == 0 and expected_output.is_file()
                result = {
                    "source_relative_path": record["source_relative_path"],
                    "return_code": completed.returncode,
                    "output_exists": expected_output.is_file(),
                    "passed": passed,
                    "stdout_tail": _output_tail(completed.stdout),
                    "stderr_tail": _output_tail(completed.stderr),
                }
            except subprocess.TimeoutExpired as error:
                result = {
                    "source_relative_path": record["source_relative_path"],
                    "return_code": None,
                    "output_exists": False,
                    "passed": False,
                    "timeout": True,
                    "stdout_tail": _output_tail(error.stdout),
                    "stderr_tail": _output_tail(error.stderr),
                }
            result["duration_seconds"] = round(time.perf_counter() - started_at, 3)
            results.append(result)
    return results


def _count_energyplus_errors(error_text: str) -> tuple[int, int]:
    """统计 EnergyPlus 错误文件中的 Severe 和 Fatal 标记。"""

    severe_count = error_text.count("** Severe  **")
    fatal_count = error_text.count("**  Fatal  **") + error_text.count("** Fatal  **")
    return severe_count, fatal_count


def run_simulation_validation(
    corpus_root: Path,
    energyplus_root: Path,
    records: Sequence[dict[str, object]],
    *,
    timeout_seconds: int = 180,
) -> list[dict[str, object]]:
    """对指定简单/复杂代表执行 EnergyPlus 设计日最小仿真。"""

    energyplus_path = energyplus_root / "energyplus.exe"
    if not energyplus_path.is_file():
        raise FileNotFoundError(f"找不到 EnergyPlus: {energyplus_path}")

    records_by_source = {
        str(record["source_relative_path"]): record for record in records
    }
    missing_sources = set(SIMULATION_REPRESENTATIVES).difference(records_by_source)
    if missing_sources:
        raise ValueError(f"仿真代表不在精选清单中: {sorted(missing_sources)}")

    results: list[dict[str, object]] = []
    with tempfile.TemporaryDirectory(prefix="idfgenx-simulate-") as temp_dir:
        temporary_root = Path(temp_dir)
        for index, source_path in enumerate(SIMULATION_REPRESENTATIVES):
            record = records_by_source[source_path]
            copied_path = corpus_root / str(record["copied_relative_path"])
            output_root = temporary_root / f"case-{index:03d}"
            command = [
                str(energyplus_path),
                "--design-day",
                "--output-directory",
                str(output_root),
                str(copied_path),
            ]
            started_at = time.perf_counter()
            try:
                completed = subprocess.run(
                    command,
                    cwd=temporary_root,
                    capture_output=True,
                    text=True,
                    timeout=timeout_seconds,
                    check=False,
                )
                error_path = output_root / "eplusout.err"
                error_text = (
                    error_path.read_text(encoding="utf-8", errors="replace")
                    if error_path.is_file()
                    else ""
                )
                severe_count, fatal_count = _count_energyplus_errors(error_text)
                passed = (
                    completed.returncode == 0
                    and error_path.is_file()
                    and severe_count == 0
                    and fatal_count == 0
                )
                result = {
                    "source_relative_path": source_path,
                    "selected_role": record["selected_role"],
                    "return_code": completed.returncode,
                    "error_file_exists": error_path.is_file(),
                    "severe_count": severe_count,
                    "fatal_count": fatal_count,
                    "passed": passed,
                    "stdout_tail": _output_tail(completed.stdout),
                    "stderr_tail": _output_tail(completed.stderr),
                }
            except subprocess.TimeoutExpired as error:
                result = {
                    "source_relative_path": source_path,
                    "selected_role": record["selected_role"],
                    "return_code": None,
                    "error_file_exists": False,
                    "severe_count": None,
                    "fatal_count": None,
                    "passed": False,
                    "timeout": True,
                    "stdout_tail": _output_tail(error.stdout),
                    "stderr_tail": _output_tail(error.stderr),
                }
            result["duration_seconds"] = round(time.perf_counter() - started_at, 3)
            results.append(result)
    return results


def build_validation_report(corpus_root: Path, energyplus_root: Path) -> dict[str, object]:
    """执行完整质量门禁并返回适合持久化的验证报告。"""

    records = load_selected_manifest(corpus_root)
    seed_records = select_seed_records(records)
    hash_results = verify_copy_hashes(corpus_root, records)
    conversion_results = run_conversion_validation(
        corpus_root, energyplus_root, seed_records
    )
    simulation_results = run_simulation_validation(
        corpus_root, energyplus_root, records
    )
    summary = {
        "selected_idf_count": len(records),
        "seed_count": len(seed_records),
        "hash_passed": sum(bool(result["passed"]) for result in hash_results),
        "hash_total": len(hash_results),
        "conversion_passed": sum(
            bool(result["passed"]) for result in conversion_results
        ),
        "conversion_total": len(conversion_results),
        "simulation_passed": sum(
            bool(result["passed"]) for result in simulation_results
        ),
        "simulation_total": len(simulation_results),
    }
    summary["passed"] = all(
        summary[passed_key] == summary[total_key]
        for passed_key, total_key in (
            ("hash_passed", "hash_total"),
            ("conversion_passed", "conversion_total"),
            ("simulation_passed", "simulation_total"),
        )
    )
    return {
        "energyplus_version": "23.1",
        "summary": summary,
        "hash_results": hash_results,
        "conversion_results": conversion_results,
        "simulation_results": simulation_results,
    }


def build_argument_parser() -> argparse.ArgumentParser:
    """创建官方语料质量门禁命令行解析器。"""

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--corpus-root", type=Path, required=True)
    parser.add_argument("--energyplus-root", type=Path, required=True)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """运行验证流程，将报告集中写入语料 metadata 目录。"""

    args = build_argument_parser().parse_args(argv)
    corpus_root = args.corpus_root.resolve()
    report = build_validation_report(corpus_root, args.energyplus_root.resolve())
    report_path = corpus_root / "metadata" / "validation.json"
    report_path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report["summary"], ensure_ascii=False, indent=2, sort_keys=True))
    return 0 if report["summary"]["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
