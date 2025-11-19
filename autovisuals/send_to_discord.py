import os
import requests
from pathlib import Path


def get_latest_prompt_file() -> Path:
    """
    Return the path to the latest prompt.txt inside:
        <project_root>/autovisuals/prompt/<timestamp>/prompt.txt

    This is resolved relative to this file's location, so it works
    no matter where you run `autovisuals` from.
    """
    # Directory containing this file = AutoVisuals/autovisuals/
    here = Path(__file__).resolve().parent

    # autovisuals/prompt
    base = here / "prompt"

    if not base.exists():
        raise FileNotFoundError(f"No prompt folder found at {base}")

    # All timestamp folders
    folders = [p for p in base.iterdir() if p.is_dir()]
    if not folders:
        raise FileNotFoundError(f"No timestamped folders found under {base}")

    # Timestamp folders lexicographically sorted -> newest is last
    latest = sorted(folders)[-1]
    prompt_file = latest / "prompt.txt"

    if not prompt_file.exists():
        raise FileNotFoundError(f"No prompt.txt found in: {latest}")

    return prompt_file


def send_to_discord(prompt: str, webhook: str):
    data = {"content": prompt}
    r = requests.post(webhook, json=data)
    r.raise_for_status()


def send_prompt_file(path: Path, webhook: str):
    lines = path.read_text(encoding="utf-8").strip().splitlines()
    for line in lines:
        if line.strip():
            send_to_discord(line.strip(), webhook)
            print(f"Sent: {line.strip()}")
