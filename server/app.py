"""FastAPI entrypoint for the standalone visualization demo."""

import logging
from typing import Any, Dict

from fastapi import FastAPI, File, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse

from .idf_processing import IDFParserException, decode_idf_bytes, parse_geometry_safe
from .simulation import (
    SimulationServiceException,
    energyplus_runtime_available,
    run_simulation,
)

logger = logging.getLogger(__name__)
MAX_IDF_BYTES = 25 * 1024 * 1024
MAX_EPW_BYTES = 50 * 1024 * 1024


def create_app() -> FastAPI:
    """Create the standalone FastAPI application."""
    application = FastAPI(
        title="EnergyPlus Visualization Demo",
        version="0.1.0",
    )

    @application.exception_handler(IDFParserException)
    async def handle_idf_exception(
        _request: Request,
        exc: IDFParserException,
    ) -> JSONResponse:
        return _failure_response(exc.status_code, exc.code, exc.message, exc.hint)

    @application.exception_handler(SimulationServiceException)
    async def handle_simulation_exception(
        _request: Request,
        exc: SimulationServiceException,
    ) -> JSONResponse:
        status_code = 503 if exc.code == "simulation_failed" else 400
        return _failure_response(status_code, exc.code, exc.message, exc.hint)

    @application.get("/api/health")
    async def health() -> Dict[str, Any]:
        return {"status": "ready", "energyplus_runtime": _runtime_available()}

    @application.post("/api/render")
    async def render(idf_file: UploadFile = File(...)) -> Dict[str, Any]:
        _validate_filename(idf_file, (".idf", ".expidf"), "IDF")
        content = await _read_upload(idf_file, MAX_IDF_BYTES, "IDF")
        geometry = await run_in_threadpool(
            parse_geometry_safe,
            decode_idf_bytes(content),
        )
        return {"geometry": geometry}

    @application.post("/api/simulation")
    async def simulate(
        idf_file: UploadFile = File(...),
        epw_file: UploadFile = File(...),
    ) -> Dict[str, Any]:
        _validate_filename(idf_file, (".idf", ".expidf"), "IDF")
        _validate_filename(epw_file, (".epw",), "EPW")
        idf_content = await _read_upload(idf_file, MAX_IDF_BYTES, "IDF")
        epw_content = await _read_upload(epw_file, MAX_EPW_BYTES, "EPW")
        return await run_in_threadpool(run_simulation, idf_content, epw_content)

    return application


async def _read_upload(
    upload: UploadFile,
    size_limit: int,
    label: str,
) -> bytes:
    content = await upload.read(size_limit + 1)
    if len(content) > size_limit:
        raise IDFParserException(
            "upload_too_large",
            f"The {label} file exceeds the {size_limit // (1024 * 1024)} MB limit.",
        )
    if not content:
        raise IDFParserException("upload_empty", f"The {label} file is empty.")
    return content


def _validate_filename(
    upload: UploadFile,
    suffixes: tuple[str, ...],
    label: str,
) -> None:
    filename = upload.filename or ""
    if not filename.lower().endswith(suffixes):
        expected = " or ".join(suffixes)
        raise IDFParserException(
            "upload_type_invalid",
            f"The {label} file must end with {expected}.",
        )


def _runtime_available() -> bool:
    return energyplus_runtime_available()


def _failure_response(
    status_code: int,
    code: str,
    message: str,
    hint: str,
) -> JSONResponse:
    payload = {"code": code, "message": message}
    if hint:
        payload["hint"] = hint
    return JSONResponse(status_code=status_code, content=payload)


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
app = create_app()
