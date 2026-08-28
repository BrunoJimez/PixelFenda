from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path


def find_ffmpeg() -> str:
    system = shutil.which("ffmpeg")
    if system:
        return system
    try:
        import imageio_ffmpeg  # type: ignore

        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "FFmpeg não foi encontrado. Instale o FFmpeg ou execute: pip install imageio-ffmpeg"
        ) from exc


def nvenc_works(ffmpeg: str | None = None) -> bool:
    ffmpeg = ffmpeg or find_ffmpeg()
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-f",
        "lavfi",
        "-i",
        "color=size=64x64:rate=1:duration=0.1",
        "-frames:v",
        "1",
        "-c:v",
        "h264_nvenc",
        "-f",
        "null",
        "-",
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=10)
        return result.returncode == 0
    except Exception:
        return False


def make_output_path(input_path: str, effect_key: str, suffix: str = "") -> str:
    p = Path(input_path)
    name = f"{p.stem}_pixelfenda_{effect_key}{suffix}.mp4"
    return str(p.with_name(name))


def ensure_parent(path: str) -> None:
    parent = os.path.dirname(os.path.abspath(path))
    os.makedirs(parent, exist_ok=True)
