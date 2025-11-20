from pathlib import Path
import os

import requests


def _get_project_root() -> Path:
    """AutoVisuals project root (AutoVisuals/)."""
    here = Path(__file__).resolve().parent      # autovisuals/
    return here.parent                          # AutoVisuals/


def get_latest_prompt_file() -> Path:
    """
    Backwards-compatible helper: return prompt.txt from the latest
    date+category:

        PROJECT_ROOT/prompt/YYYY-MM-DD/<category>/prompt.txt
    """
    project_root = _get_project_root()
    base = project_root / "prompt"

    if not base.exists():
        raise FileNotFoundError(f"No prompt folder found at {base}")

    date_folders = [p for p in base.iterdir() if p.is_dir()]
    if not date_folders:
        raise FileNotFoundError(f"No date folders under {base}")

    latest_date_dir = sorted(date_folders)[-1]
    cat_folders = [p for p in latest_date_dir.iterdir() if p.is_dir()]
    if not cat_folders:
        raise FileNotFoundError(f"No category folders in {latest_date_dir}")

    latest_cat_dir = sorted(cat_folders)[-1]
    prompt_file = latest_cat_dir / "prompt.txt"

    if not prompt_file.exists():
        raise FileNotFoundError(f"No prompt.txt in {latest_cat_dir}")

    return prompt_file


def send_to_discord(prompt: str, webhook: str):
    """Send a single prompt line to Discord via webhook."""
    data = {"content": prompt}
    r = requests.post(webhook, json=data)
    r.raise_for_status()


def send_prompt_file(path: Path, webhook: str):
    """Send each non-empty line from prompt.txt to Discord."""
    lines = path.read_text(encoding="utf-8").splitlines()
    for line in lines:
        msg = line.strip()
        if not msg:
            continue
        send_to_discord(msg, webhook)
        print(f"Sent: {msg}")


__all__ = [
    "_get_project_root",
    "get_latest_prompt_file",
    "send_to_discord",
    "send_prompt_file",
]
