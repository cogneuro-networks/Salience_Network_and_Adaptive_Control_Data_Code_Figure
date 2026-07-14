"""InferenceData NetCDF I/O with a Windows Unicode-path workaround."""

from __future__ import annotations

import os
import shutil
import tempfile
from pathlib import Path

import arviz as az

_CACHE_DIR = Path(tempfile.gettempdir()) / "hddm_analysis_idata"


def _has_non_ascii(path: Path) -> bool:
    try:
        str(path).encode("ascii")
    except UnicodeEncodeError:
        return True
    return False


def _shadow_copy(src: Path) -> Path:
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    dst = _CACHE_DIR / src.name
    if not dst.exists() or dst.stat().st_mtime < src.stat().st_mtime:
        shutil.copy2(src, dst)
    return dst


def from_netcdf(path: str | os.PathLike) -> az.InferenceData:
    """Load InferenceData from NetCDF, staging via %TEMP% on Windows if needed."""
    src = Path(path)
    if not src.is_file():
        raise FileNotFoundError(f"InferenceData not found: {src}")

    load_path: Path = src
    if os.name == "nt" and _has_non_ascii(src):
        load_path = _shadow_copy(src)

    try:
        return az.from_netcdf(load_path)
    except (FileNotFoundError, OSError):
        if load_path == src:
            return az.from_netcdf(_shadow_copy(src))
        raise


def stage_netcdf(path: str | os.PathLike) -> str:
    """Return an ASCII-safe path for a NetCDF file (copying to %TEMP% if needed)."""
    src = Path(path)
    if not src.is_file():
        raise FileNotFoundError(f"InferenceData not found: {src}")
    if os.name == "nt" and _has_non_ascii(src):
        return str(_shadow_copy(src))
    return str(src)
