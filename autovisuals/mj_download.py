"""
Midjourney image downloader for AutoVisuals.

Downloads MJ images, splits grids, and maps them into:

    PROJECT_ROOT/mj_downloads/YYYY-MM-DD/<category>/

Category is resolved via [av:xxxx] ID tags from prompt metadata.
All tunable parameters (idle timeout, limits, paths) are passed in
from autovisuals.cli for tidiness.
"""

import logging
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional

import discord
from PIL import Image


def _get_project_root() -> Path:
    here = Path(__file__).resolve().parent  # autovisuals/
    return here.parent  # AutoVisuals/


PROJECT_ROOT = _get_project_root()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def slug_from_content(content: str) -> str:
    """Fallback category slug from MJ prompt text."""
    if not content:
        return "image"

    text = content.lower().strip()
    for p in [
        "/imagine prompt:",
        "/imagine prompt",
        "imagine prompt:",
        "imagine prompt",
    ]:
        if text.startswith(p):
            text = text[len(p) :].strip()
            break

    if "--" in text:
        text = text.split("--", 1)[0]

    words = text.split()
    if not words:
        return "image"

    slug = "-".join(words[:2])

    import re as _re

    slug = _re.sub(r"[^a-z0-9\-]+", "", slug)
    return slug or "image"


def split_grid_image(path: Path, delete_original: bool = True):
    """Split a 2×2 grid into 4 tiles and optionally delete original."""
    img = Image.open(path)
    w, h = img.size
    tile_w = w // 2
    tile_h = h // 2

    coords = [
        (0, 0),
        (tile_w, 0),
        (0, tile_h),
        (tile_w, tile_h),
    ]

    stem = path.stem
    ext = path.suffix

    for idx, (x, y) in enumerate(coords, start=1):
        tile = img.crop((x, y, x + tile_w, y + tile_h))
        out_path = path.with_name(f"{stem}_{idx:02d}{ext}")
        tile.save(out_path)
        logging.info("  ↳ saved tile %d: %s", idx, out_path)

    if delete_original:
        try:
            path.unlink()
            logging.info("  ↳ deleted original grid: %s", path)
        except Exception as e:
            logging.warning("  ↳ failed to delete original grid %s: %s", path, e)


def build_id_to_category_map(prompt_root: Path, date_str: str) -> Dict[str, str]:
    """
    Map short IDs → category slugs for a given date based on:

        prompt_root/DATE/<category>/meta.json
    """
    date_dir = prompt_root / date_str
    mapping: Dict[str, str] = {}
    if not date_dir.exists():
        return mapping

    import json

    for cat_dir in date_dir.iterdir():
        if not cat_dir.is_dir():
            continue
        meta_path = cat_dir / "meta.json"
        if not meta_path.exists():
            continue
        try:
            records = json.loads(meta_path.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(records, list):
            continue
        for rec in records:
            if not isinstance(rec, dict):
                continue
            uid = rec.get("id")
            if uid:
                mapping[str(uid).lower()] = cat_dir.name

    return mapping


# ------------------------------------------------------------------
# Discord client
# ------------------------------------------------------------------


class MJDownloader(discord.Client):
    def __init__(
        self,
        download_root: Path,
        channel_id: Optional[int],
        limit: Optional[int],
        idle_seconds: Optional[int],
        **options,
    ):
        intents = options.pop("intents", discord.Intents.default())
        super().__init__(intents=intents, **options)

        self.download_root = download_root
        self.channel_id = channel_id
        self.limit = limit
        self.idle_seconds = idle_seconds  # may be None

        self.downloaded_count = 0
        self.last_download_time: Optional[datetime] = None

        self.prompt_root = PROJECT_ROOT / "prompt"
        self._id_map_cache: Dict[str, Dict[str, str]] = {}

    async def on_ready(self):
        logging.info("Logged in as %s", self.user)
        logging.info("Watching channel: %s", self.channel_id or "ALL")
        logging.info("Download root: %s", self.download_root)
        logging.info(
            "Limit: %s | Idle timeout: %s",
            self.limit or "none",
            self.idle_seconds or "disabled",
        )

        self.last_download_time = datetime.utcnow()
        if self.idle_seconds is not None:
            self.loop.create_task(self._idle_task())

    async def _idle_task(self):
        """Close client after idle_seconds with no downloads."""
        assert self.idle_seconds is not None
        while not self.is_closed():
            await discord.utils.sleep_until(datetime.utcnow() + timedelta(seconds=3))
            if self.last_download_time is None:
                continue
            elapsed = (datetime.utcnow() - self.last_download_time).total_seconds()
            if elapsed >= self.idle_seconds:
                logging.info(
                    "No downloads for %.1fs (>= %d). Stopping.",
                    elapsed,
                    self.idle_seconds,
                )
                await self.close()
                break

    def _load_id_map(self, date_str: str) -> Dict[str, str]:
        if date_str not in self._id_map_cache:
            self._id_map_cache[date_str] = build_id_to_category_map(
                self.prompt_root, date_str
            )
        return self._id_map_cache[date_str]

    async def on_message(self, message: discord.Message):
        if message.author == self.user:
            return
        if self.channel_id and message.channel.id != self.channel_id:
            return
        if not message.attachments:
            return
        if self.limit and self.downloaded_count >= self.limit:
            return

        created = message.created_at
        date_str = created.date().isoformat()
        content = message.content or ""

        # map [av:xxxx] → category
        id_map = self._load_id_map(date_str)
        m = re.search(r"\[av:([0-9a-fA-F]{4,})\]", content)
        uid = m.group(1).lower() if m else None

        if uid and uid in id_map:
            cat = id_map[uid]
            logging.info("Matched id=%s → category=%s", uid, cat)
        else:
            cat = slug_from_content(content)
            logging.info("Fallback category=%s", cat)

        day_dir = self.download_root / date_str
        day_dir.mkdir(parents=True, exist_ok=True)
        cat_dir = day_dir / cat
        cat_dir.mkdir(parents=True, exist_ok=True)

        for att in message.attachments:
            if self.limit and self.downloaded_count >= self.limit:
                break

            self.downloaded_count += 1
            idx = self.downloaded_count

            ext = Path(att.filename).suffix or ".png"
            out_path = cat_dir / f"{cat}_{idx:04d}{ext}"

            logging.info("[#%d] Downloading %s → %s", idx, att.filename, out_path)
            data = await att.read()
            out_path.write_bytes(data)
            logging.info("[#%d] Saved (%d bytes)", idx, len(data))

            try:
                logging.info("[#%d] Splitting grid...", idx)
                split_grid_image(out_path, delete_original=True)
            except Exception as e:
                logging.warning("[#%d] Could not split grid: %s", idx, e)

            self.last_download_time = datetime.utcnow()

        if self.limit and self.downloaded_count >= self.limit:
            logging.info("Reached limit=%d, stopping.", self.limit)
            await self.close()


# ------------------------------------------------------------------
# Public runner (CLI passes all parameters)
# ------------------------------------------------------------------


def run_downloader(
    token: Optional[str],
    channel_id: Optional[int],
    download_dir: str | Path,
    limit: Optional[int],
    idle_seconds: Optional[int],
):
    """
    Entry point used by autovisuals.cli.

    All defaults (token source, channel id, idle timeout, etc.) are handled
    in cli.py; this function just applies what it is given.
    """
    import os

    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(message)s",
        )

    token = token or os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise ValueError("Discord bot token missing (DISCORD_BOT_TOKEN).")

    if channel_id is None:
        cid = os.environ.get("MJ_CHANNEL_ID")
        if cid:
            channel_id = int(cid)

    dl_root = Path(download_dir)
    if not dl_root.is_absolute():
        dl_root = PROJECT_ROOT / dl_root

    intents = discord.Intents.default()
    intents.messages = True
    intents.message_content = True

    client = MJDownloader(
        download_root=dl_root,
        channel_id=channel_id,
        limit=limit,
        idle_seconds=idle_seconds,
        intents=intents,
    )
    client.run(token)
