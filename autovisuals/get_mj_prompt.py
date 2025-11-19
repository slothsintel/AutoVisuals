#!/usr/bin/env python3
"""
autovisuals.get_mj_prompt

Part of the AutoVisuals project.

Script to:
- load THEMES + WEIGHTS from a csv (theme list)
- generate adobe-stock-style metadata + midjourney prompts
- support providers: openai / anthropic / gemini / llama / deepseek
- use one env var: API_KEY
- flags:
    -p provider       (openai / anthropic / gemini / llama / deepseek)
    -l list           (theme list csv, theme,weight)
    -m mode           (random/manual theme)
    -t title          (random/manual title; manual only used in manual theme mode)
    -d records        (number of records)
    -r repeat         (midjourney --r value)
    -o out            (output root folder; default: prompt/)
"""

import os
import json
import random
import csv
from pathlib import Path
import argparse
from datetime import datetime

from openai import OpenAI
from anthropic import Anthropic
import google.generativeai as genai
import requests


# ==========================================================
# 1. configuration
# ==========================================================

DEFAULT_PROVIDER = "openai"
DEFAULT_MODEL_OPENAI = "gpt-5.1"
DEFAULT_MODEL_CLAUDE = "claude-3-sonnet-latest"
DEFAULT_MODEL_GEMINI = "gemini-1.5-flash"
DEFAULT_MODEL_LLAMA = "llama-4-maverick"
DEFAULT_MODEL_DEEPSEEK = "deepseek-v3"


DEFAULT_NUM_ITEMS = 3
DEFAULT_REPEAT = 5
DEFAULT_LIST_FILE = "adobe_cat.csv"  # under ./data/ by default (theme,weight)
DEFAULT_OUT_DIR = "prompt"

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
# BASE_DIR is the autovisuals/ package directory when this file is placed at autovisuals/get_mj_prompt.py
BASE_DIR = Path(__file__).resolve().parent

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


# ==========================================================
# 2. theme reader (theme, weight)
# ==========================================================
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

            # handle single-cell like "theme,5"
            if len(row) == 1 and "," in row[0]:
                row = [p.strip() for p in row[0].split(",", 1)]

            if len(row) < 2:
                continue

            theme = row[0].strip()
            weight_raw = row[1].strip()

            try:
                w = float(weight_raw)
            except ValueError:
                # treat row 1 as header if weight is not numeric
                if row_num == 1:
                    continue
                raise ValueError(f"invalid weight '{weight_raw}' in row {row_num}")

            if not theme:
                raise ValueError(f"empty theme text in row {row_num}")

            themes.append(theme)
            weights.append(w)

    if not themes:
        raise ValueError(f"no valid themes found in {csv_path}")

    return themes, weights


# ==========================================================
# 3. system prompt
# ==========================================================
def make_system_prompt(repeat: int) -> str:
    return f"""
you generate metadata and midjourney prompt content.

you must return valid json:

{{
  "category": "string",
  "theme": "string",
  "prompt": "string",             # do NOT include '/imagine prompt:' prefix — we add it automatically
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
    - include subject, environment, composition, style, lighting, mood, camera hints
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


# ==========================================================
# 4. multi-provider model caller
# ==========================================================
def call_model(provider: str, system_prompt: str, user_prompt: str) -> dict:
    """
    call the chosen provider (openai / anthropic / gemini)
    and return a normalized metadata dict.
    """

    provider = provider.lower()

    # ---------- openai (gpt-5.1) ----------
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

    # ---------- anthropic (claude 3) ----------
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

    # ---------- gemini 1.5 ----------
    elif provider == "gemini":
        global gemini_client
        if gemini_client is None:
            genai.configure(api_key=API_KEY)
            gemini_client = genai.GenerativeModel(DEFAULT_MODEL_GEMINI)

        result = gemini_client.generate_content(system_prompt + "\n" + user_prompt)
        raw = result.text

    # ---------- llama 4 maverick ----------
    elif provider == "llama":
        # Free Llama 4 Maverick endpoint
        payload = {
            "model": DEFAULT_MODEL_LLAMA,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        resp = requests.post(
            "https://api.llama-api.com/chat/completions", json=payload, timeout=60
        ).json()

        raw = resp["choices"][0]["message"]["content"]

    # ---------- deepseek v3 ----------
    elif provider == "deepseek":
        # Free Deepseek v3 endpoint
        payload = {
            "model": DEFAULT_MODEL_DEEPSEEK,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        }

        resp = requests.post(
            "https://api.deepseek.ai/v1/chat/completions", json=payload, timeout=60
        ).json()

        raw = resp["choices"][0]["message"]["content"]

    else:
        raise ValueError(f"unknown provider: {provider}")

    # parse json
    try:
        data = json.loads(raw)
    except Exception:
        print("\nmodel raw output (not valid json):\n", raw)
        raise RuntimeError("model did not return valid json")

    # normalize keywords to exactly 45, last = "generative ai"
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


# ==========================================================
# 5. wrappers: random/manual theme
# ==========================================================
def generate_for_theme(provider: str, theme: str, repeat: int) -> dict:
    """
    common generator for both random and manual theme modes.
    """
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

    # normalize prompt to have correct /imagine prompt: prefix
    if "prompt" in data and isinstance(data["prompt"], str):
        data["prompt"] = normalize_mj_prefix(data["prompt"])

    # ensure the 'theme' field exists and is at least the given theme if model forgot
    if (
        "theme" not in data
        or not isinstance(data["theme"], str)
        or not data["theme"].strip()
    ):
        data["theme"] = theme

    return data


# ==========================================================
# 6. writers
# ==========================================================
def save_json(items, path: Path):
    path.write_text(json.dumps(items, indent=2, ensure_ascii=False), encoding="utf-8")
    print("saved json:", path)


def save_csv(items, path: Path):
    fields = ["category", "theme", "prompt", "title", "description", "keywords"]
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fields)
        w.writeheader()
        for it in items:
            w.writerow(
                {
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
    lines = [
        normalize_mj_prefix(it.get("prompt", "")) for it in items if it.get("prompt")
    ]
    path.write_text("\n".join(lines), encoding="utf-8")
    print("saved prompts:", path)


# ==========================================================
# 7. path helpers
# ==========================================================
def resolve_list_path(list_arg: str) -> Path:
    """
    list csv:
    - if absolute path → use directly
    - if relative path → resolve under ./data/ (inside the autovisuals package)
    """
    p = Path(list_arg)
    if p.is_absolute():
        return p
    return BASE_DIR / "data" / list_arg


def resolve_output_root(out_arg: str) -> Path:
    """
    output root:
    - if absolute path → use directly
    - if relative path → resolve under BASE_DIR (autovisuals/)
    """
    p = Path(out_arg)
    if p.is_absolute():
        return p
    return BASE_DIR / out_arg


# ==========================================================
# 8. main orchestration
# ==========================================================
def main(provider, list_arg, mode, title_mode, n, repeat, out_arg):
    """
    Orchestrate generation from CLI-style arguments.

    This function can be imported and called from downstream scripts,
    e.g.:

        from autovisuals.get_mj_prompt import main as generate_prompts

        generate_prompts(
            provider="openai",
            list_arg="adobe_cat.csv",
            mode="r",
            title_mode="r",
            n=10,
            repeat=5,
            out_arg="prompt",
        )
    """

    provider = provider.lower()
    mode = "manual" if mode.lower().startswith("m") else "random"
    title_mode = "manual" if title_mode.lower().startswith("m") else "random"

    csv_path = resolve_list_path(list_arg)
    if not csv_path.exists():
        raise FileNotFoundError(f"theme list csv not found: {csv_path}")

    out_root = resolve_output_root(out_arg)
    out_dir = out_root / TIMESTAMP

    print(f"provider      : {provider}")
    print(f"theme list    : {csv_path}")
    print(f"theme mode    : {mode}")
    print(f"title mode    : {title_mode}")
    print(f"records       : {n}")
    print(f"--r repeat    : {repeat}")
    print(f"output root   : {out_root}")
    print(f"api key loaded: yes\n")

    themes, weights = load_themes_with_weights(csv_path)

    print("loaded themes with weights:")
    for t, w in zip(themes, weights):
        print(f"  - {t} (weight={w})")
    print()

    items = []

    # manual theme mode
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
            items.append(rec)

    # random theme mode (weighted by theme weights)
    else:
        for i in range(n):
            theme = random.choices(themes, weights=weights, k=1)[0]
            print(f"[{i+1}/{n}] theme = {theme!r}")
            rec = generate_for_theme(provider, theme, repeat)
            items.append(rec)

    out_dir.mkdir(parents=True, exist_ok=True)

    save_json(items, out_dir / "meta.json")
    save_csv(items, out_dir / "meta.csv")
    save_prompts(items, out_dir / "prompt.txt")

    print("\nall done.")


# ==========================================================
# 9. cli
# ==========================================================
def parse_args():
    p = argparse.ArgumentParser(
        prog="python -m autovisuals.get_mj_prompt",
        description="generate metadata + midjourney prompts from theme list",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
api key usage
=============
export API_KEY="sk-openai-xxxxx"   # openai gpt-5.1
export API_KEY="sk-ant-xxxxx"      # claude 3
export API_KEY="AIza-xxxxx"        # gemini 1.5

theme list (-l)
===============
- csv format: theme,weight
- default: data/{DEFAULT_LIST_FILE} (inside the autovisuals package)
- if path is relative → resolved under autovisuals/data/
- if path is absolute → used directly

output root (-o)
================
- default: {DEFAULT_OUT_DIR}/
- actual output stored in: <out>/<timestamp>/
- if relative → resolved under the autovisuals/ package directory

examples
========
python -m autovisuals.get_mj_prompt -p openai    -l adobe_cat.csv -m r -t r -d 10 -r 5 -o prompt
python -m autovisuals.get_mj_prompt -p anthropic -l my_themes.csv  -m m -t m -d 5  -r 4 -o results
python -m autovisuals.get_mj_prompt -p gemini    -l /abs/list.csv  -m r -t r -d 3  -r 2 -o out
""",
    )

    # order: -p, -l, -m, -t, -d, -r, -o
    p.add_argument(
        "-p",
        "--provider",
        choices=["openai", "anthropic", "gemini"],
        default=DEFAULT_PROVIDER,
        help="chatbot api provider",
    )

    p.add_argument(
        "-l",
        "--list",
        default=DEFAULT_LIST_FILE,
        help="theme list csv (theme,weight); relative paths are under autovisuals/data/",
    )

    p.add_argument(
        "-m",
        "--mode",
        choices=["r", "m", "random", "manual"],
        default="r",
        help="theme mode: random (weighted by csv) or manual",
    )

    p.add_argument(
        "-t",
        "--title",
        choices=["r", "m", "random", "manual"],
        default="r",
        help="title mode: random or manual (manual only used when theme is manual)",
    )

    p.add_argument(
        "-d",
        "--records",
        type=int,
        default=DEFAULT_NUM_ITEMS,
        help=f"number of records to generate (default {DEFAULT_NUM_ITEMS})",
    )

    p.add_argument(
        "-r",
        "--repeat",
        type=int,
        default=DEFAULT_REPEAT,
        help=f"value for midjourney --r flag (default {DEFAULT_REPEAT})",
    )

    p.add_argument(
        "-o",
        "--out",
        default=DEFAULT_OUT_DIR,
        help=f"output root folder (default: {DEFAULT_OUT_DIR}/)",
    )

    return p.parse_args()


if __name__ == "__main__":
    args = parse_args()
    main(
        provider=args.provider,
        list_arg=args.list,
        mode=args.mode,
        title_mode=args.title,
        n=args.records,
        repeat=args.repeat,
        out_arg=args.out,
    )


# ==========================================================
# 10. mj prompt normalizer
# ==========================================================
def normalize_mj_prefix(prompt: str) -> str:
    """
    Ensure the prompt begins with exactly:
        /imagine prompt:
    Handles:
        - existing /imagine prompt:
        - /imagine prompt (no colon)
        - imagine prompt:
        - imagine prompt
        - no prefix at all
    """
    s = prompt.strip()

    # Lowercase version to check prefix
    low = s.lower()

    # If already correct (any case) — normalize spacing only
    if low.startswith("/imagine prompt:"):
        rest = s[len("/imagine prompt:") :].lstrip()
        return f"/imagine prompt: {rest}"

    # Missing the colon
    if low.startswith("/imagine prompt"):
        rest = s[len("/imagine prompt") :].lstrip(": ").lstrip()
        return f"/imagine prompt: {rest}"

    # Missing the slash but has "imagine prompt:"
    if low.startswith("imagine prompt:"):
        rest = s[len("imagine prompt:") :].lstrip()
        return f"/imagine prompt: {rest}"

    # Missing slash & colon
    if low.startswith("imagine prompt"):
        rest = s[len("imagine prompt") :].lstrip(": ").lstrip()
        return f"/imagine prompt: {rest}"

    # No prefix at all
    return f"/imagine prompt: {s}"
