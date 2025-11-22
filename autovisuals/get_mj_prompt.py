#!/usr/bin/env python3
"""
autovisuals.get_mj_prompt

Core generator: given a theme list, generate Adobe-style metadata +
Midjourney prompts.

This file exposes:

    main(provider, list_arg, mode, title_mode, n, repeat, out_arg)

CLI defaults live in autovisuals.cli (for the `autovisuals` entrypoint).
You can still run this module directly:

    python -m autovisuals.get_mj_prompt  ...

but the recommended way is via:

    autovisuals generate ...
"""

import os
import json
import random
import csv
import re
import uuid
from pathlib import Path
import argparse
from datetime import datetime
from collections import defaultdict

from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai
import requests


# ------------------------------------------------------------------
# Project / paths
# ------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent  # autovisuals/
PROJECT_ROOT = BASE_DIR.parent  # AutoVisuals/

DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL_OPENAI = "gpt-5.1"
DEFAULT_MODEL_CLAUDE = "claude-3-sonnet-latest"
DEFAULT_MODEL_GEMINI = "gemini-1.5-flash"
DEFAULT_MODEL_LLAMA = "llama-4-maverick"
DEFAULT_MODEL_DEEPSEEK = "deepseek-v3"

DEFAULT_NUM_ITEMS = 3
DEFAULT_REPEAT = 5
DEFAULT_LIST_FILE = "adobe_cat.csv"  # inside autovisuals/data
DEFAULT_OUT_DIR = "prompt"

API_KEY = os.getenv("API_KEY")
if not API_KEY:
    raise RuntimeError(
        "please export API_KEY before running.\n"
        "examples:\n"
        '  export API_KEY="sk-openai-xxxxx"   # openai gpt-5.1\n'
        '  export API_KEY="sk-ant-xxxxx"      # claude 3\n'
        '  export API_KEY="AIza-xxxxx"        # gemini 1.5\n'
    )

openai_client = None
claude_client = None
gemini_client = None


# ------------------------------------------------------------------
# Theme loader
# ------------------------------------------------------------------


def load_themes_with_weights(csv_path: Path):
    """
    CSV format:
        theme,weight
        "snowy mountain at sunrise", 3
        "business teamwork in office", 5
    """
    themes, weights = [], []

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for row_num, row in enumerate(reader, start=1):
            if not row:
                continue

            if len(row) == 1 and "," in row[0]:
                row = [p.strip() for p in row[0].split(",", 1)]

            if len(row) < 2:
                continue

            theme = row[0].strip()
            weight_raw = row[1].strip()

            try:
                w = float(weight_raw)
            except ValueError:
                if row_num == 1:
                    # header
                    continue
                raise ValueError(f"invalid weight '{weight_raw}' in row {row_num}")

            if not theme:
                raise ValueError(f"empty theme text in row {row_num}")

            themes.append(theme)
            weights.append(w)

    if not themes:
        raise ValueError(f"no valid themes found in {csv_path}")

    return themes, weights


# ------------------------------------------------------------------
# MJ helpers
# ------------------------------------------------------------------


def normalize_mj_prefix(prompt: str) -> str:
    """
    Ensure the prompt begins with exactly '/imagine prompt:' (no trailing space).
    Accepts content with or without prefix.
    """
    s = prompt.strip()
    low = s.lower()

    if low.startswith("/imagine prompt:"):
        rest = s[len("/imagine prompt:") :].lstrip()
        return f"/imagine prompt:{rest}"

    if low.startswith("/imagine prompt"):
        rest = s[len("/imagine prompt") :].lstrip(": ").lstrip()
        return f"/imagine prompt:{rest}"

    if low.startswith("imagine prompt:"):
        rest = s[len("imagine prompt:") :].lstrip()
        return f"/imagine prompt:{rest}"

    if low.startswith("imagine prompt"):
        rest = s[len("imagine prompt") :].lstrip(": ").lstrip()
        return f"/imagine prompt:{rest}"

    return f"/imagine prompt:{s}"


def slug_from_text(text: str) -> str:
    """
    Slugify category names (used as folder names).
    """
    if not text:
        return "category"

    t = text.strip().lower()
    words = t.split()
    if not words:
        return "category"

    short = "-".join(words[:4])
    slug = re.sub(r"[^a-z0-9\-]+", "", short)
    return slug or "category"


def attach_id_tag(full_prompt: str, uid: str) -> str:
    """
    Insert ID tag [av:uid] before MJ parameter block.
    """
    tag = f" [av:{uid}]"
    s = full_prompt.rstrip()

    if "--" in s:
        base, rest = s.split("--", 1)
        return base.rstrip() + tag + " --" + rest.lstrip()
    else:
        return s + tag


def generate_id(existing_ids: set[str]) -> str:
    while True:
        uid = uuid.uuid4().hex[:4]
        if uid not in existing_ids:
            existing_ids.add(uid)
            return uid


# ------------------------------------------------------------------
# System prompt
# ------------------------------------------------------------------


def make_system_prompt(repeat: int) -> str:
    return f"""
you generate metadata and midjourney prompt content.

you must return valid json:

{{
  "category": "string",
  "theme": "string",
  "prompt": "string",             # do NOT include '/imagine prompt:' prefix — we add it
  "title": "string",
  "description": "string",
  "keywords": [...]
}}

rules:
- category: broad stock-photo category that fits the theme (e.g. nature, business, people)
- theme: keep or lightly refine the given theme text
- prompt:
    - detailed midjourney content to append after '/imagine prompt:'
    - DO NOT include '/imagine prompt:' — only the content itself
    - include simple subject, environment, movement, not too complicated composition, simple style, lighting, positive mood, camera hints
    - DO NOT include people from the front view or many details for example fingers and teeth 
    - must end with: --ar 16:9 --s 20 --c 10 --raw --r {repeat}
- title:
    - stock-photo friendly
    - <= 60 characters
- description:
    - 1–2 natural sentences
- keywords:
    - exactly 45 items
    - items 1–44 must be relevant to the theme
    - item 45 must be "generative ai"
    - no duplicates

return only the json object, nothing else.
"""


# ------------------------------------------------------------------
# Multi-provider call
# ------------------------------------------------------------------


def call_model(provider: str, system_prompt: str, user_prompt: str) -> dict:
    """
    Call the chosen provider and return parsed JSON dict.
    All provider-specific URLs / models can be tuned in cli.py via args.
    """
    provider = provider.lower()

    # OpenAI
    if provider == "openai":
        global openai_client
        if openai_client is None:
            openai_client = OpenAI(api_key=API_KEY)

        resp = openai_client.responses.create(
            model=DEFAULT_MODEL_OPENAI,
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )

        chunks = []
        for item in resp.output:
            if getattr(item, "content", None):
                for c in item.content:
                    if getattr(c, "text", None):
                        chunks.append(c.text)
        raw = "\n".join(chunks).strip()

    # Claude
    elif provider == "anthropic":
        global claude_client
        if claude_client is None:
            claude_client = Anthropic(api_key=API_KEY)

        msg = claude_client.messages.create(
            model=DEFAULT_MODEL_CLAUDE,
            max_tokens=2000,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        raw = msg.content[0].text

    # Gemini
    elif provider == "gemini":
        global gemini_client
        if gemini_client is None:
            genai.configure(api_key=API_KEY)
            gemini_client = genai.GenerativeModel(DEFAULT_MODEL_GEMINI)

        result = gemini_client.generate_content(system_prompt + "\n" + user_prompt)
        raw = result.text

    # Llama (example endpoint)
    elif provider == "llama":
        payload = {
            "model": DEFAULT_MODEL_LLAMA,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        resp = requests.post(
            "https://api.llama-api.com/chat/completions",
            json=payload,
            timeout=60,
        ).json()
        raw = resp["choices"][0]["message"]["content"]

    # DeepSeek (example endpoint)
    elif provider == "deepseek":
        payload = {
            "model": DEFAULT_MODEL_DEEPSEEK,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }
        resp = requests.post(
            "https://api.deepseek.ai/v1/chat/completions",
            json=payload,
            timeout=60,
        ).json()
        raw = resp["choices"][0]["message"]["content"]

    else:
        raise ValueError(f"unknown provider: {provider}")

    try:
        data = json.loads(raw)
    except Exception:
        print("\nmodel raw output:\n", raw)
        raise RuntimeError("model did not return valid json")

    # normalise keywords to exactly 45 with last = "generative ai"
    kw = data.get("keywords", [])
    if not isinstance(kw, list):
        raise ValueError("keywords must be a list")

    if len(kw) < 45:
        last = kw[-1] if kw else "keyword"
        while len(kw) < 45:
            kw.append(last)
    elif len(kw) > 45:
        kw = kw[:45]

    lowered = [k.lower() for k in kw]
    filtered = [kw[i] for i in range(len(kw)) if lowered[i] != "generative ai"]

    if not filtered:
        filtered = ["keyword"] * 44

    if len(filtered) < 44:
        last = filtered[-1]
        while len(filtered) < 44:
            filtered.append(last)
    elif len(filtered) > 44:
        filtered = filtered[:44]

    filtered.append("generative ai")
    data["keywords"] = filtered

    return data


# ------------------------------------------------------------------
# Core generation
# ------------------------------------------------------------------


def generate_for_theme(provider: str, theme: str, repeat: int) -> dict:
    system_prompt = make_system_prompt(repeat)
    user_prompt = f"""
theme: "{theme}"

tasks:
1. keep or lightly refine the theme as "theme".
2. choose a broad stock-photo category as "category".
3. generate prompt, title, description, keywords following the schema.
4. respect keywords and --r rules.

return only the json object.
"""
    data = call_model(provider, system_prompt, user_prompt)

    if (
        "theme" not in data
        or not isinstance(data["theme"], str)
        or not data["theme"].strip()
    ):
        data["theme"] = theme

    return data


# ------------------------------------------------------------------
# Save helpers
# ------------------------------------------------------------------


def save_json(items, path: Path):
    path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    print("saved json:", path)


def save_csv(items, path: Path):
    fields = ["id", "category", "theme", "prompt", "title", "description", "keywords"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        for it in items:
            w.writerow(
                {
                    "id": it.get("id", ""),
                    "category": it.get("category", ""),
                    "theme": it.get("theme", ""),
                    "prompt": it.get("prompt", ""),
                    "title": it.get("title", ""),
                    "description": it.get("description", ""),
                    "keywords": ", ".join(it.get("keywords", [])),
                }
            )
    print("saved csv :", path)


def save_prompts(items, path: Path):
    lines = []
    for it in items:
        p = it.get("prompt", "")
        if not p:
            continue
        lines.append(normalize_mj_prefix(p))
    path.write_text("\n".join(lines), encoding="utf-8")
    print("saved prompts:", path)


# ------------------------------------------------------------------
# Path helpers
# ------------------------------------------------------------------


def resolve_list_path(list_arg: str) -> Path:
    p = Path(list_arg)
    if p.is_absolute():
        return p
    return BASE_DIR / "data" / list_arg


def resolve_output_root(out_arg: str) -> Path:
    p = Path(out_arg)
    if p.is_absolute():
        return p
    return PROJECT_ROOT / p


# ------------------------------------------------------------------
# Public main() used by cli.py
# ------------------------------------------------------------------


def main(
    provider: str,
    list_arg: str,
    mode: str,
    title_mode: str,
    n: int,
    repeat: int,
    out_arg: str,
):
    """
    Orchestrate generation from CLI-style arguments.

    PROJECT_ROOT/<out>/YYYY-MM-DD/<category-slug>/
        meta.json
        meta.csv
        prompt.txt
    """
    provider = provider.lower()
    mode = "manual" if mode.lower().startswith("m") else "random"
    title_mode = "manual" if title_mode.lower().startswith("m") else "random"

    csv_path = resolve_list_path(list_arg)
    if not csv_path.exists():
        raise FileNotFoundError(f"theme list csv not found: {csv_path}")

    out_root = resolve_output_root(out_arg)
    date_str = datetime.now().date().isoformat()

    print(f"provider      : {provider}")
    print(f"theme list    : {csv_path}")
    print(f"theme mode    : {mode}")
    print(f"title mode    : {title_mode}")
    print(f"records       : {n}")
    print(f"--r repeat    : {repeat}")
    print(f"output root   : {out_root}")
    print(f"date folder   : {date_str}")
    print(f"api key loaded: yes\n")

    themes, weights = load_themes_with_weights(csv_path)

    print("loaded themes with weights:")
    for t, w in zip(themes, weights):
        print(f"  - {t} (weight={w})")
    print()

    items = []
    used_ids: set[str] = set()

    # manual theme
    if mode == "manual":
        theme = input("enter theme: ").strip()
        if not theme:
            raise ValueError("theme cannot be empty in manual mode")

        custom_title = None
        if title_mode == "manual":
            custom_title = input("enter custom title: ").strip()
            if not custom_title:
                raise ValueError("title cannot be empty in manual title mode")

        for i in range(n):
            print(f"[{i+1}/{n}] generating manual-theme record…")
            rec = generate_for_theme(provider, theme, repeat)
            if custom_title:
                rec["title"] = custom_title

            if "category" not in rec or not rec["category"]:
                rec["category"] = "uncategorized"

            content = rec.get("prompt", "")
            full_prompt = normalize_mj_prefix(content)
            uid = generate_id(used_ids)
            rec["id"] = uid
            rec["prompt"] = attach_id_tag(full_prompt, uid)
            items.append(rec)

    # random theme (weighted)
    else:
        for i in range(n):
            theme = random.choices(themes, weights=weights, k=1)[0]
            print(f"[{i+1}/{n}] theme = {theme!r}")
            rec = generate_for_theme(provider, theme, repeat)

            if "category" not in rec or not rec["category"]:
                rec["category"] = "uncategorized"

            content = rec.get("prompt", "")
            full_prompt = normalize_mj_prefix(content)
            uid = generate_id(used_ids)
            rec["id"] = uid
            rec["prompt"] = attach_id_tag(full_prompt, uid)
            items.append(rec)

    date_dir = out_root / date_str
    date_dir.mkdir(parents=True, exist_ok=True)

    by_cat_slug: dict[str, list[dict]] = defaultdict(list)
    for rec in items:
        cat_text = rec.get("category", "") or "uncategorized"
        slug = slug_from_text(cat_text)
        by_cat_slug[slug].append(rec)

    for slug, recs in by_cat_slug.items():
        cat_dir = date_dir / slug
        cat_dir.mkdir(parents=True, exist_ok=True)

        save_json(recs, cat_dir / "meta.json")
        save_csv(recs, cat_dir / "meta.csv")
        save_prompts(recs, cat_dir / "prompt.txt")

    print("\nall done.")


# ------------------------------------------------------------------
# Stand-alone usage (optional)
# ------------------------------------------------------------------


def parse_args():
    p = argparse.ArgumentParser(
        prog="python -m autovisuals.get_mj_prompt",
        description="generate metadata + midjourney prompts from theme list",
    )

    p.add_argument(
        "-p",
        "--provider",
        choices=["openai", "anthropic", "gemini", "llama", "deepseek"],
        default=DEFAULT_PROVIDER,
    )
    p.add_argument("-l", "--list", default=DEFAULT_LIST_FILE)
    p.add_argument("-m", "--mode", default="r", choices=["r", "m", "random", "manual"])
    p.add_argument("-t", "--title", default="r", choices=["r", "m", "random", "manual"])
    p.add_argument("-d", "--records", type=int, default=DEFAULT_NUM_ITEMS)
    p.add_argument("-r", "--repeat", type=int, default=DEFAULT_REPEAT)
    p.add_argument("-o", "--out", default=DEFAULT_OUT_DIR)

    return p.parse_args()


if __name__ == "__main__":
    a = parse_args()
    main(
        provider=a.provider,
        list_arg=a.list,
        mode=a.mode,
        title_mode=a.title,
        n=a.records,
        repeat=a.repeat,
        out_arg=a.out,
    )
