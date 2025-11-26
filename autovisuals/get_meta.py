from __future__ import annotations

"""
autovisuals.get_meta

Generate stock metadata CSVs for:
  - Adobe Stock
  - Shutterstock
  - Freepik

based on:
  - mj_downloads/YYYY-MM-DD/<category>/* image files
  - prompt/YYYY-MM-DD/<category>/meta.json  (from get_mj_prompt.py)

This module exposes:

    generate_stock_metadata(...)
    main()  # for python -m autovisuals.get_meta

Typical CLI usage (once wired in cli.py):

    autovisuals meta -d 2025-11-26
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import csv
import json
import logging
import re
import argparse
from datetime import date


def _get_project_root() -> Path:
    here = Path(__file__).resolve().parent  # autovisuals/
    return here.parent  # AutoVisuals/


PROJECT_ROOT = _get_project_root()
DEFAULT_DOWNLOAD_DIR = PROJECT_ROOT / "mj_downloads"
DEFAULT_OUT_PROMPT = PROJECT_ROOT / "prompt"
DEFAULT_OUT_ROOT = PROJECT_ROOT / "meta"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def slugify_title(title: str) -> str:
    """
    Slugify a title in the same way mj_download.py does for filenames.
    """
    if not title:
        return ""
    slug = re.sub(r"[^a-zA-Z0-9\-]+", "_", title).strip("_")
    return slug


def extract_title_slug_from_filename(stem: str) -> str:
    """
    Given an image stem like:
        "golden_sunrise_over_misty_mountains_0003_02"
    return:
        "golden_sunrise_over_misty_mountains"

    If no numeric suffix is present, return the stem as-is.
    """
    m = re.match(r"(.+)_\d{4}(?:_\d{2})?$", stem)
    if m:
        return m.group(1)
    return stem


def find_latest_date_dir(root: Path) -> str:
    """
    Find the latest YYYY-MM-DD directory name under root.
    """
    candidates: List[str] = []
    for p in root.iterdir():
        if not p.is_dir():
            continue
        name = p.name
        try:
            _ = date.fromisoformat(name)
            candidates.append(name)
        except ValueError:
            continue

    if not candidates:
        raise FileNotFoundError(f"No dated subdirectories found under {root}")

    return sorted(candidates)[-1]


def load_category_meta(
    prompt_root: Path, date_str: str, category: str
) -> Tuple[Dict[str, dict], Optional[dict]]:
    """
    Load meta.json for a single category and build:
        slug -> record

    Returns (mapping, default_record)
    """
    cat_dir = prompt_root / date_str / category
    meta_path = cat_dir / "meta.json"
    mapping: Dict[str, dict] = {}
    default_rec: Optional[dict] = None

    if not meta_path.exists():
        return mapping, default_rec

    try:
        records = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception as e:
        logging.warning("Could not read meta.json for %s/%s: %s", date_str, category, e)
        return mapping, default_rec

    if not isinstance(records, list):
        logging.warning("meta.json for %s/%s is not a list", date_str, category)
        return mapping, default_rec

    for rec in records:
        if not isinstance(rec, dict):
            continue
        title = str(rec.get("title", "")).strip()
        if not title:
            title = str(rec.get("theme", "")).strip()
        slug = slugify_title(title) or category
        if slug not in mapping:
            mapping[slug] = rec
        if default_rec is None:
            default_rec = rec

    return mapping, default_rec


def join_keywords(rec: dict) -> str:
    kw = rec.get("keywords", [])
    if isinstance(kw, list):
        return ", ".join(str(k).strip() for k in kw if str(k).strip())
    if isinstance(kw, str):
        return kw.strip()
    return ""


def trim_description(text: str, max_chars: int = 200) -> str:
    text = (text or "").strip()
    if len(text) <= max_chars:
        return text
    trimmed = text[: max_chars - 1].rstrip()
    return trimmed + "…"


def clean_prompt_for_freepik(prompt: str) -> str:
    """
    Remove '/imagine prompt:' and MJ technical flags/id from the prompt.
    """
    if not prompt:
        return ""
    txt = prompt.strip()

    # Drop leading /imagine prompt variants
    for p in [
        "/imagine prompt:",
        "/imagine prompt",
        "imagine prompt:",
        "imagine prompt",
    ]:
        if txt.lower().startswith(p):
            txt = txt[len(p) :].strip()
            break

    # Remove id tag at the end [id:xxxx]
    txt = re.sub(r"\s*\[id:[0-9a-fA-F]+\]$", "", txt)

    # Remove MJ flags starting with --
    if " --" in txt:
        txt = txt.split(" --", 1)[0].strip()

    return txt


# ---------------------------------------------------------------------------
# Row builders for each platform
# ---------------------------------------------------------------------------


def make_adobe_row(filename: str, rec: dict, category: str) -> dict:
    title = (
        str(rec.get("title", "")).strip()
        or str(rec.get("theme", "")).strip()
        or category
    )
    # Adobe "Title" is the main short description (limit to 200 chars)
    title = trim_description(title, max_chars=200)
    keywords = join_keywords(rec)

    return {
        "Filename": filename,
        "Title": title,
        "Keywords": keywords,
        "Category": category,
        "Releases": "",  # no releases by default
    }


def make_shutterstock_row(filename: str, rec: dict, category: str) -> dict:
    desc = str(rec.get("description", "")).strip()
    if not desc:
        desc = str(rec.get("title", "")).strip() or category
    desc = trim_description(desc, max_chars=200)
    keywords = join_keywords(rec)

    return {
        "Filename": filename,
        "Description": desc,
        "Keywords": keywords,
        "Categories": category,
        "Editorial": "no",
        "Mature content": "no",
        "illustration": "no",
    }


def make_freepik_row(filename: str, rec: dict, category: str) -> dict:
    title = str(rec.get("title", "")).strip() or category
    keywords = join_keywords(rec)
    prompt = clean_prompt_for_freepik(str(rec.get("prompt", "")).strip())

    return {
        "File name": filename,
        "Title": title,
        "Keywords": keywords,
        "Prompt": prompt,
        "Model": "Midjourney v7",
    }


# ---------------------------------------------------------------------------
# Core generation
# ---------------------------------------------------------------------------


def generate_stock_metadata(
    date_str: Optional[str] = None,
    download_root: Path | str = DEFAULT_DOWNLOAD_DIR,
    prompt_root: Path | str = DEFAULT_OUT_PROMPT,
    out_root: Path | str = DEFAULT_OUT_ROOT,
) -> Path:
    """
    Generate three CSV files under:

        out_root/<date_str>/
            adobe_meta.csv
            shutterstock_meta.csv
            freepik_meta.csv

    based on all images under:

        download_root/<date_str>/<category>/*

    and metadata from:

        prompt_root/<date_str>/<category>/meta.json
    """
    download_root = Path(download_root)
    prompt_root = Path(prompt_root)
    out_root = Path(out_root)

    if date_str is None or date_str == "latest":
        date_str = find_latest_date_dir(download_root)

    day_dir = download_root / date_str
    if not day_dir.exists():
        raise FileNotFoundError(
            f"Download directory for {date_str} not found: {day_dir}"
        )

    logging.info("Generating stock metadata for date %s", date_str)
    logging.info("Download root: %s", day_dir)
    logging.info("Prompt root  : %s", prompt_root)

    adobe_rows: List[dict] = []
    shutter_rows: List[dict] = []
    freepik_rows: List[dict] = []

    image_exts = {".png", ".jpg", ".jpeg", ".webp", ".tif", ".tiff"}

    # Iterate categories in mj_downloads/date
    for cat_dir in sorted(p for p in day_dir.iterdir() if p.is_dir()):
        category = cat_dir.name
        meta_map, default_rec = load_category_meta(prompt_root, date_str, category)

        logging.info("Category %s: %d meta entries", category, len(meta_map))

        # For each image file, find corresponding meta record via title slug
        for img_path in sorted(cat_dir.iterdir()):
            if img_path.suffix.lower() not in image_exts:
                continue

            stem = img_path.stem
            title_slug = extract_title_slug_from_filename(stem)

            rec = meta_map.get(title_slug) or default_rec or {}
            filename = img_path.name

            adobe_rows.append(make_adobe_row(filename, rec, category))
            shutter_rows.append(make_shutterstock_row(filename, rec, category))
            freepik_rows.append(make_freepik_row(filename, rec, category))

    if not adobe_rows:
        raise RuntimeError(f"No image files found under {day_dir}")

    out_dir = out_root / date_str
    out_dir.mkdir(parents=True, exist_ok=True)

    # Write CSVs
    adobe_path = out_dir / "adobe_meta.csv"
    shutter_path = out_dir / "shutterstock_meta.csv"
    freepik_path = out_dir / "freepik_meta.csv"

    def write_csv(path: Path, fieldnames: List[str], rows: List[dict]):
        with path.open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                writer.writerow(r)
        logging.info("Wrote %s (%d rows)", path, len(rows))

    write_csv(
        adobe_path,
        ["Filename", "Title", "Keywords", "Category", "Releases"],
        adobe_rows,
    )
    write_csv(
        shutter_path,
        [
            "Filename",
            "Description",
            "Keywords",
            "Categories",
            "Editorial",
            "Mature content",
            "illustration",
        ],
        shutter_rows,
    )
    write_csv(
        freepik_path,
        ["File name", "Title", "Keywords", "Prompt", "Model"],
        freepik_rows,
    )

    return out_dir


