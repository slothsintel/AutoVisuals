#!/usr/bin/env python3
"""
autovisuals.upscale

Upscaling helpers (currently RealESRGAN only).

Behaviour:
- Calls a RealESRGAN inference script (inference_realesrgan.py).
- For each input image, we:
    1) Record which files already exist in output_dir
    2) Run RealESRGAN
    3) Detect the NEW file created in output_dir (whatever its name is)
    4) Rename that file so the filename is based on the prompt title from:

           PROJECT_ROOT/prompt/YYYY-MM-DD/<category>/meta.json

       If multiple images share the same title, we append _01, _02, etc.
"""

import os
import json
import subprocess
from pathlib import Path
from typing import Iterable, Tuple


def _get_project_root() -> Path:
    """Assume this file lives in AutoVisuals/autovisuals/."""
    here = Path(__file__).resolve().parent  # autovisuals/
    return here.parent  # AutoVisuals/


PROJECT_ROOT = _get_project_root()


def _load_title_for_image(img_path: Path) -> Tuple[str, Tuple[str, str, str]]:
    """
    Given an image path from mj_downloads (or similar), try to find the
    matching meta.json and return a (base_title, key).

    key is a tuple (date, category, title) used to group images for numbering.

    Fallbacks:
      - if meta.json missing or invalid → use image stem
      - if title missing/blank          → use image stem
    """
    try:
        date = img_path.parents[2].name   # YYYY-MM-DD
        category = img_path.parents[1].name
    except IndexError:
        base_title = img_path.stem
        return base_title, ("", "", base_title)

    meta_path = PROJECT_ROOT / "prompt" / date / category / "meta.json"
    base_title = img_path.stem

    print(f"[upscale] meta.json → {meta_path} (exists={meta_path.exists()})")

    if meta_path.exists():
        try:
            raw = json.loads(meta_path.read_text(encoding="utf-8"))
            if isinstance(raw, list) and raw:
                rec = raw[0]
            elif isinstance(raw, dict):
                rec = raw
            else:
                rec = None

            if isinstance(rec, dict):
                title = str(rec.get("title", "")).strip()
                if title:
                    base_title = title
        except Exception as e:
            print(f"[upscale] ERROR reading meta.json: {e!r}")

    key = (date, category, base_title)
    return base_title, key


def _sanitize_filename(name: str) -> str:
    """Convert an arbitrary title into a safe filename stem."""
    safe = "".join(c for c in name if c.isalnum() or c in (" ", "-", "_")).strip()
    if not safe:
        safe = "image"
    safe = safe.replace(" ", "_")
    return safe


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
    Run RealESRGAN over images and rename outputs based on titles.
    """

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    realesrgan_bin = Path(
        realesrgan_bin
        or os.getenv("REALESRGAN_BIN")
        or "/Real-ESRGAN/inference_realesrgan.py"
    )
    realesrgan_bin = str(realesrgan_bin)

    model = model or os.getenv("REALESRGAN_MODEL", "RealESRGAN_x4plus")
    scale = scale or int(os.getenv("REALESRGAN_SCALE", "4"))
    tile = tile if tile is not None else int(os.getenv("REALESRGAN_TILE", "256"))

    counters: dict[tuple[str, str, str], int] = {}

    for img in input_images:
        img = Path(img)
        if not img.is_file():
            print(f"[upscale] skip (not a file): {img}")
            continue

        # snapshot BEFORE
        before = {p.resolve() for p in output_dir.iterdir() if p.is_file()}

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
            continue

        # snapshot AFTER
        after = {p.resolve() for p in output_dir.iterdir() if p.is_file()}
        new_files = list(after - before)

        if not new_files:
            print(f"[upscale] WARNING: no new file detected for {img.name}")
            continue

        generated = max(new_files, key=lambda p: p.stat().st_mtime)

        # load title & debug print
        base_title, key = _load_title_for_image(img)
        print(f"[upscale] title → {base_title}")

        safe_title = _sanitize_filename(base_title)

        # numbering
        count = counters.get(key, 0) + 1
        counters[key] = count
        new_stem = safe_title if count == 1 else f"{safe_title}_{count:02d}"

        new_path = output_dir / f"{new_stem}{generated.suffix}"

        # avoid accidental overwrite
        if new_path.exists() and new_path.resolve() != generated:
            alt_idx = 1
            tmp = new_path
            while tmp.exists():
                alt_idx += 1
                tmp = output_dir / f"{new_stem}_{alt_idx:02d}{generated.suffix}"
            new_path = tmp

        if generated.resolve() != new_path.resolve():
            generated.rename(new_path)
            print(f"[upscale] renamed → {new_path.name}")
        else:
            print(f"[upscale] already named as → {new_path.name}")
