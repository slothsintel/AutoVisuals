#!/usr/bin/env python3
"""
autovisuals.upscale

Calls the RealESRGAN inference script located in:

    AutoVisuals/Real-ESRGAN/inference_realesrgan.py

We *ignore* REALESRGAN_BIN environment variable to avoid stale paths.
"""

import subprocess
from pathlib import Path
from typing import Iterable


def _get_project_root() -> Path:
    # upscale.py is inside AutoVisuals/autovisuals/
    return Path(__file__).resolve().parent.parent


def _get_default_realesrgan_bin() -> Path:
    root = _get_project_root()
    return root / "Real-ESRGAN" / "inference_realesrgan.py"


def run_realesrgan(
    input_images: Iterable[Path],
    output_dir: Path,
    model: str | None = None,
    scale: int | None = None,
    tile: int | None = None,
    realesrgan_bin: str | None = None,
    python_exe: str = "python3",
) -> None:
    """
    Run RealESRGAN on a list of images.

    Defaults:
        realesrgan_bin = AutoVisuals/Real-ESRGAN/inference_realesrgan.py
        model = RealESRGAN_x4plus
        scale = 4
        tile = 256
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # ALWAYS use local Real-ESRGAN unless user explicitly passed another path
    default_bin = _get_default_realesrgan_bin()
    realesrgan_bin = realesrgan_bin or str(default_bin)

    if not Path(realesrgan_bin).is_file():
        raise FileNotFoundError(
            f"[upscale] RealESRGAN not found at {realesrgan_bin}\n"
            f"Expected here: {default_bin}"
        )

    model = model or "RealESRGAN_x4plus"
    scale = scale or 4
    tile = 256 if tile is None else tile

    for img in input_images:
        img = Path(img)
        if not img.is_file():
            print(f"[upscale] skip (not a file): {img}")
            continue

        cmd = [
            python_exe,
            realesrgan_bin,
            "-i", str(img),
            "-o", str(output_dir),
            "-n", model,
            "-s", str(scale),
        ]
        if tile > 0:
            cmd.extend(["-t", str(tile)])

        print(f"[upscale] RealESRGAN {img.name} → {output_dir}")
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"[upscale] RealESRGAN failed on {img}: {e}")
