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
from dotenv import load_dotenv

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
# Utility helpers
# ------------------------------------------------------------------


def generate_id(used_ids: set[str]) -> str:
    """
    Generate a short unique ID that doesn't collide with existing ones.
    """
    while True:
        uid = uuid.uuid4().hex[:8]
        if uid not in used_ids:
            used_ids.add(uid)
            return uid


def normalize_mj_prefix(s: str) -> str:
    """
    Ensure the prompt starts with `/imagine prompt:` exactly once.
    If the model already added it in some variant, normalise it.
    """
    if not s:
        return "/imagine prompt:"

    s = s.strip()
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

    slug = "-".join(re.sub(r"[^a-z0-9]+", "", w) for w in words)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "category"


def attach_id_tag(prompt: str, uid: str) -> str:
    """
    Attach an ID tag before the Midjourney flags so we can trace outputs.

    Final shape:
        /imagine prompt: ... [av:abcd1234] --v 7 --ar 16:9 --s 5 --c 20 --raw --r N
    """
    prompt = prompt.rstrip()
    tag = f"[av:{uid}]"

    # Look for the standard flag tail at the end of the prompt
    flag_pattern = re.compile(
        r"(\s*--v\s+7\s+--ar\s+16:9\s+--s\s+5\s+--c\s+20\s+--raw\s+--r\s+\d+\s*)$"
    )
    m = flag_pattern.search(prompt)
    if m:
        head = prompt[: m.start(1)].rstrip()
        flags = m.group(1).lstrip()
        # /imagine prompt: ... [av:xxxx] --v 7 ...
        return f"{head} {tag} {flags}"

    # Fallback: no recognised flags, just append tag at the end
    if prompt.endswith(" " + tag) or prompt.endswith(tag):
        return prompt
    return f"{prompt} {tag}"


# ------------------------------------------------------------------
# System prompt construction
# ------------------------------------------------------------------


def make_system_prompt(repeat: int) -> str:
    return f"""
you generate stock-photo metadata and midjourney prompt content.

you must return valid json:

{{
  "category": "string",
  "theme": "string",
  "prompt": "string",
  "title": "string",
  "description": "string",
  "keywords": ["string", ...]
}}

============================================================
VARIANT SYSTEM (IMPORTANT — CREATES REAL DIVERSITY)
============================================================

you will sometimes receive a "variant" object in the user input:

"variant": {{
  "viewpoint": "...",         # e.g. macro close-up, high angle, telephoto, overhead
  "time_of_day": "...",       # e.g. dawn, golden hour, midday, blue hour
  "season": "...",            # e.g. spring, autumn, winter
  "weather": "...",           # e.g. misty air, clear sky, drizzle, snowfall
  "palette": "...",           # e.g. warm gold, cool blue, pastel, monochrome
  "style_family": "...",      # e.g. photography, illustration, 3d render, vector
  "complexity": "...",        # e.g. minimal composition, moderate composition
  "variant_id": "int"         # unique per run to force structural variation
}}

rules for "variant":
- treat ALL variant fields as HARD CONSTRAINTS.
- the "prompt" MUST clearly reflect viewpoint, time_of_day, weather, palette, style_family, etc.
- different variant values for the SAME theme must produce noticeably different:
  - composition
  - lighting behaviour
  - environment cues
  - colour palette
  - mood
  - camera perspective
  - style vocabulary

============================================================
CATEGORY / THEME
============================================================

rules for "category":
- broad stock-photo category matching the theme (nature, business, travel, animal, food, architecture, technology, abstract, lifestyle).
- must be lowercase.
- must NOT repeat the theme.

rules for "theme":
- EXACTLY match the theme string provided in the user message.
- no rephrasing, no added adjectives.

============================================================
MIDJOURNEY PROMPT RULES
============================================================

the "prompt" field:
- DO NOT include '/imagine prompt:'.
- describe ONE simple, clean subject suitable for stock.
- no human faces, no full human characters.
- avoid detailed anatomy (fingers, teeth).
- no copyrighted characters, no brands, no logos, no text.

content requirements:
- reflect the chosen theme PLUS the "variant" fields.
- use rich sensory detail: light behaviour, materials, textures, atmosphere.
- must incorporate at least ONE camera / lens / perspective hint.
- must incorporate the palette, weather, viewpoint, and time_of_day from variant.
- must be positive or neutral in mood.

style rules:
- style must align with "style_family" from variant.
- inside that family, pick a fresh, distinct style:
  - photography → cinema still, macro realism, long-exposure landscape, bokeh-like background (no faces)
  - illustration → watercolor, gouache, ink, soft pastel
  - 3d render → glossy cyberpunk, soft claymation, clean minimal render
  - vector → flat lighting, gradient minimalism
- never reuse the same style wording for different variant_id values within the same theme.

STRUCTURAL ANTI-REPETITION:
- prompts for the SAME theme but different variant_id must NOT follow the same sentence structure.
- vary ordering of elements: sometimes begin with light, sometimes atmosphere, sometimes subject, sometimes texture.
- do NOT reuse the same opening phrase ("a", "an image of", "a scene of", etc.).
- vary sentence length: sometimes one long descriptive sentence, sometimes two short ones.
- no template-like repetition across runs.

END OF PROMPT (MANDATORY):
the prompt must end with:
  --v 7 --ar 16:9 --s 5 --c 20 --raw --r {repeat}

============================================================
TITLE RULES
============================================================

- <= 60 characters
- must be stock-friendly, natural, clean
- reflect theme AND variant
- no prompt words, no MJ flags

============================================================
DESCRIPTION RULES
============================================================

- 1–2 natural sentences
- describe the subject, environment, light, and mood
- reflect theme AND variant
- no technical flags, no “AI”, no “midjourney”

============================================================
KEYWORDS RULES
============================================================

- exactly 45 items
- items 1–44 must relate to:
  - theme
  - variant (viewpoint, light, palette, etc.)
  - subject
  - environment
  - mood
  - style family
- item 45 must be: "generative ai"
- no duplicates
- all lowercase
- short phrases (1–3 words)
- no technical flags (no "--ar 16:9")
- no quotation marks inside keywords

============================================================
FINAL INSTRUCTIONS
============================================================

- return ONLY the json object, nothing else.
- output must be valid JSON: double quotes, no trailing commas.
"""


# ------------------------------------------------------------------
# Core validation helpers
# ------------------------------------------------------------------


def ensure_string(data: dict, key: str, default: str = "") -> None:
    v = data.get(key, default)
    if not isinstance(v, str):
        v = default
    v = v.strip()
    data[key] = v


def ensure_keywords(data: dict) -> dict:
    """
    Normalise and validate keywords to exactly 45 items with last = "generative ai".
    """
    if "keywords" not in data:
        raise ValueError("missing 'keywords' in model output")

    kw = data["keywords"]
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


def make_variant(variant_id: int) -> dict:
    """
    Generate a random variant to force visual and structural diversity
    between runs for the same theme.
    """
    viewpoints = [
        "macro close-up",
        "eye-level view",
        "low-angle view",
        "high-angle view",
        "overhead top-down view",
        "distant telephoto view",
    ]

    times_of_day = [
        "dawn",
        "golden hour",
        "midday",
        "overcast afternoon",
        "blue hour",
        "night",
    ]

    seasons = [
        "spring",
        "summer",
        "autumn",
        "winter",
    ]

    weather_options = [
        "clear sky",
        "light mist",
        "hazy air",
        "soft drizzle",
        "snowfall",
        "after-rain wet surfaces",
    ]

    palettes = [
        "warm golden palette",
        "cool blue palette",
        "soft pastel palette",
        "high-contrast palette",
        "monochrome palette",
        "earth tones palette",
    ]

    style_families = [
        "photography",
        "illustration",
        "3d render",
        "vector",
    ]

    complexities = [
        "minimal composition",
        "moderate composition",
    ]

    return {
        "viewpoint": random.choice(viewpoints),
        "time_of_day": random.choice(times_of_day),
        "season": random.choice(seasons),
        "weather": random.choice(weather_options),
        "palette": random.choice(palettes),
        "style_family": random.choice(style_families),
        "complexity": random.choice(complexities),
        "variant_id": variant_id,
    }


def generate_for_theme(provider: str, theme: str, repeat: int, variant_id: int) -> dict:
    """
    Call the model for a single theme + variant and return validated data.
    """
    system_prompt = make_system_prompt(repeat)
    variant = make_variant(variant_id)

    user_prompt = f"""
theme: "{theme}"

variant:
{json.dumps(variant, indent=2)}

tasks:
1. use the theme EXACTLY as given for the "theme" field.
2. choose a broad stock-photo category as "category".
3. generate prompt, title, description, keywords following the schema.
4. the prompt MUST clearly reflect ALL fields in "variant".
5. respect keywords and --r rules.

return only the json object.
"""
    data = call_model(provider, system_prompt, user_prompt)

    # if the model forgets or alters the theme, force it back
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
            row = {k: it.get(k, "") for k in fields}
            if isinstance(row["keywords"], list):
                row["keywords"] = ", ".join(row["keywords"])
            w.writerow(row)
    print("saved csv:", path)


def save_prompts(items, path: Path):
    with path.open("w", encoding="utf-8") as f:
        for it in items:
            p = it.get("prompt", "").strip()
            # keep [av:xxxx] in the prompt so Discord sees it
            f.write(p + "\n")

# ------------------------------------------------------------------
# Theme list loading (weighted)
# ------------------------------------------------------------------


def load_themes_with_weights(csv_path: Path):
    """
    CSV format:

        theme,weight
        forest sunrise,3
        minimal tech background,1
        ...

    First row is a header and will always be skipped.
    """
    themes = []
    weights = []

    with csv_path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    # always skip header row
    if rows:
        rows = rows[1:]

    for row in rows:
        if not row:
            continue
        if len(row) == 1 and "," in row[0]:
            row = [p.strip() for p in row[0].split(",", 1)]

        theme = row[0].strip()
        if not theme:
            continue

        if len(row) > 1:
            try:
                w = float(row[1])
            except ValueError:
                w = 1.0
        else:
            w = 1.0

        themes.append(theme)
        weights.append(w)

    if not themes:
        raise ValueError("no themes loaded from csv")

    return themes, weights



# ------------------------------------------------------------------
# Main orchestration
# ------------------------------------------------------------------


def resolve_output_root(out_arg: str) -> Path:
    """
    Resolve output root relative to project root.
    """
    root = Path(__file__).resolve().parent.parent
    return (root / out_arg).resolve()

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
    csv_path = Path(list_arg).expanduser().resolve()
    if not csv_path.is_file():
        raise FileNotFoundError(f"theme list not found: {csv_path}")

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
            custom_title = input("enter title (<=60 chars, optional): ").strip()
            if len(custom_title) > 60:
                custom_title = custom_title[:60]

        for i in range(n):
            print(f"[{i+1}/{n}] generating manual-theme record…")
            rec = generate_for_theme(provider, theme, repeat, variant_id=i + 1)
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
            rec = generate_for_theme(provider, theme, repeat, variant_id=i + 1)

            if "category" not in rec or not rec["category"]:
                rec["category"] = "uncategorized"

            content = rec.get("prompt", "")
            full_prompt = normalize_mj_prefix(content)
            uid = generate_id(used_ids)
            rec["id"] = uid
            rec["prompt"] = attach_id_tag(full_prompt, uid)
            items.append(rec)

    # Root for this run: PROJECT_ROOT/<out>/YYYY-MM-DD/
    date_dir = out_root / date_str
    date_dir.mkdir(parents=True, exist_ok=True)

    from collections import defaultdict

    # group by THEME (from your CSV), not by model-chosen category
    by_theme_slug: dict[str, list[dict]] = defaultdict(list)

    for rec in items:
        theme_text = rec.get("theme", "") or "theme"
        slug = slug_from_text(theme_text)  # e.g. "business" -> "business"
        by_theme_slug[slug].append(rec)

    for slug, recs in by_theme_slug.items():
        theme_dir = date_dir / slug
        theme_dir.mkdir(parents=True, exist_ok=True)

        # one JSON + CSV per theme
        save_json(recs, theme_dir / "meta.json")
        save_csv(recs, theme_dir / "meta.csv")

        # one prompt.txt per theme (all prompts, one per line)
        save_prompts(recs, theme_dir / "prompt.txt")
        print("saved:", theme_dir / "prompt.txt")

    print("\nall done.")





# ------------------------------------------------------------------
# Stand-alone usage (optional)
# ------------------------------------------------------------------


def parse_args():
    p = argparse.ArgumentParser(description="Generate MJ prompts + metadata from theme list.")

    p.add_argument(
        "--provider",
        choices=["openai", "gemini", "deepseek", "llama"],
        default="openai",
        help="LLM provider to use",
    )

    p.add_argument(
        "--list",
        required=True,
        help="Path to CSV theme list (e.g. data/adobe_cat.csv)",
    )

    p.add_argument(
        "--mode",
        choices=["manual", "random"],
        default="random",
        help="Theme selection mode: 'manual' prompts for a single theme, 'random' uses weighted sampling.",
    )

    p.add_argument(
        "--title",
        choices=["auto", "manual"],
        default="auto",
        help="Title mode: 'auto' lets the model create titles, 'manual' lets you override.",
    )

    p.add_argument(
        "-d",
        "--records",
        type=int,
        default=10,
        help="Number of records to generate.",
    )

    p.add_argument(
        "-r",
        "--repeat",
        type=int,
        default=1,
        help="Value for Midjourney --r (repeat) flag.",
    )

    p.add_argument(
        "-o",
        "--out",
        default="prompt",
        help="Output root folder (relative to project root).",
    )

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
