"""
Midjourney downloader for AutoVisuals.

Listens to a single Discord channel (and its threads),
and downloads any image attachments into a local folder,
with date-based subfolders and slugged filenames.
"""

import os
import re
import logging
from pathlib import Path

import discord

# ---------- logging setup ----------

logger = logging.getLogger("autovisuals.mj_download")
logger.setLevel(logging.INFO)

if not logger.handlers:
    _h = logging.StreamHandler()
    _h.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s"))
    logger.addHandler(_h)


IMAGE_EXTS = (".png", ".jpg", ".jpeg", ".webp")


def slug_from_content(content: str) -> str:
    """
    Build a short slug from the message content (usually the MJ prompt text).
    """
    if not content:
        return "image"

    text = content.strip()
    low = text.lower()

    # Strip common Midjourney prefixes
    for prefix in ("/imagine prompt:", "/imagine prompt", "imagine prompt:", "imagine prompt"):
        if low.startswith(prefix):
            text = text[len(prefix):].lstrip()
            break

    # Cut off any parameter block starting with --
    if "--" in text:
        text = text.split("--", 1)[0]

    words = text.strip().lower().split()
    if not words:
        return "image"

    short = "-".join(words[:4])
    slug = re.sub(r"[^a-z0-9\-]+", "", short)
    return slug or "image"


def next_index_for_day(day_dir: Path) -> int:
    """
    Count existing files in the day folder and return next index (1-based).
    """
    if not day_dir.exists():
        return 1
    count = sum(1 for p in day_dir.iterdir() if p.is_file())
    return count + 1


# ---------- Discord downloader client ----------


def make_client(channel_id: int, download_root: Path, limit: int | None):
    """
    Create a Discord Client that listens to:
    - the specified channel_id, and
    - any threads whose parent is that channel.
    """

    intents = discord.Intents.default()
    # Make sure "Message Content Intent" is enabled in the Dev Portal.
    intents.message_content = True

    class MJDownloader(discord.Client):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.count = 0
            self.limit = limit

        async def on_ready(self):
            logger.info("Logged in as %s (ID: %s)", self.user, self.user.id)
            logger.info("Watching Discord channel: %s", channel_id)
            logger.info("Download root: %s", download_root)
            if self.limit:
                logger.info("Will stop after %s images.", self.limit)
            else:
                logger.info("No limit — running until Ctrl+C.")
            download_root.mkdir(parents=True, exist_ok=True)

        async def on_message(self, message: discord.Message):
            """
            Called for every message the bot can see.
            We:
            - Filter to the target channel or its threads
            - Download image attachments
            """
            ch = message.channel
            parent = getattr(ch, "parent", None)

            # Filter: only our target channel (or threads under it)
            target = False
            if ch.id == channel_id:
                target = True
            elif parent is not None and parent.id == channel_id:
                target = True

            if not target:
                return

            if not message.attachments:
                return

            # Date-based subfolder
            date_str = message.created_at.date().isoformat()
            day_dir = download_root / date_str
            day_dir.mkdir(parents=True, exist_ok=True)

            slug = slug_from_content(message.content)

            for attachment in message.attachments:
                filename = attachment.filename or "image"
                ext = Path(filename).suffix.lower()
                if not ext:
                    # Midjourney images are typically PNG; fall back to .png
                    ext = ".png"

                idx = next_index_for_day(day_dir)
                out_name = f"{slug}_{idx:03d}{ext}"
                save_path = day_dir / out_name

                logger.info("Downloading %s -> %s", attachment.url, save_path)
                await attachment.save(save_path)
                logger.info("Saved: %s", save_path)

                self.count += 1
                if self.limit and self.count >= self.limit:
                    logger.info(
                        "Download limit reached (%s images). Shutting down...", self.limit
                    )
                    await self.close()
                    return

    return MJDownloader(intents=intents)


def run_downloader(
    token: str | None = None,
    channel_id: int | None = None,
    download_dir: str | Path = "mj_downloads",
    limit: int | None = None,
) -> None:
    """
    Entry point used by the CLI.

    token        – Discord bot token (from DISCORD_BOT_TOKEN env if None)
    channel_id   – Discord channel ID (from MJ_CHANNEL_ID env if None)
    download_dir – root folder to save images (date-based subfolders inside)
    limit        – stop after N images (None means run forever)
    """

    # Token
    token = token or os.environ.get("DISCORD_BOT_TOKEN")
    if not token:
        raise RuntimeError(
            "DISCORD_BOT_TOKEN not set. Please export it, e.g.\n"
            '  export DISCORD_BOT_TOKEN="your-bot-token-here"'
        )

    # Channel ID
    if channel_id is None:
        env_channel = os.environ.get("MJ_CHANNEL_ID")
        if not env_channel:
            raise RuntimeError(
                "MJ_CHANNEL_ID not set. Please export it, e.g.\n"
                "  export MJ_CHANNEL_ID=123456789012345678"
            )
        channel_id = int(env_channel)

    download_root = Path(download_dir)

    logger.info("Starting MJ downloader...")
    client = make_client(channel_id=channel_id, download_root=download_root, limit=limit)
    client.run(token)
