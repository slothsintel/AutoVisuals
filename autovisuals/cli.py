"""
Command-line interface for AutoVisuals.

Examples:
    autovisuals generate -p openai -l adobe_cat.csv -m r -t r -d 5 -r 5 -o prompt
    autovisuals discord
    autovisuals download --limit 5
    autovisuals pipeline -p openai -d 5 --limit 5
    autovisuals gallery
"""

import os
import argparse
from pathlib import Path

from .get_mj_prompt import main as generate_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autovisuals",
        description="AutoVisuals CLI - automated prompt + metadata + Discord tools",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- generate subcommand ---
    gen = subparsers.add_parser(
        "generate",
        help="Generate prompts + metadata from a theme list",
    )

    gen.add_argument(
        "-p", "--provider",
        choices=["openai", "anthropic", "gemini", "llama", "deepseek"],
        default="openai",
        help="LLM provider to use (default: openai)",
    )
    gen.add_argument(
        "-l", "--list",
        default="adobe_cat.csv",
        help="Theme list CSV (theme,weight). Relative paths resolved under autovisuals/data/",
    )
    gen.add_argument(
        "-m", "--mode",
        choices=["r", "m", "random", "manual"],
        default="r",
        help="Theme mode",
    )
    gen.add_argument(
        "-t", "--title",
        choices=["r", "m", "random", "manual"],
        default="r",
        help="Title mode",
    )
    gen.add_argument(
        "-d", "--records",
        type=int,
        default=3,
        help="How many records to generate (default 3)",
    )
    gen.add_argument(
        "-r", "--repeat",
        type=int,
        default=5,
        help="Midjourney --r repeat parameter",
    )
    gen.add_argument(
        "-o", "--out",
        default="prompt",
        help="Output root folder (default: prompt/)",
    )

    # --- discord subcommand ---
    discord_cmd = subparsers.add_parser(
        "discord",
        help="Send prompts to Discord webhook. Defaults to latest folder + WEBHOOK_URL.",
    )

    discord_cmd.add_argument(
        "-f", "--file",
        default=None,
        help="Path to prompt.txt. If omitted, uses latest timestamp folder.",
    )
    discord_cmd.add_argument(
        "-w", "--webhook",
        default=None,
        help="Discord webhook URL. If omitted, reads WEBHOOK_URL env var.",
    )

    # --- download subcommand ---
    download_cmd = subparsers.add_parser(
        "download",
        help="Download Midjourney images from your private Discord server channel.",
    )

    download_cmd.add_argument(
        "--token",
        default=None,
        help="Discord Bot Token. If omitted, uses DISCORD_BOT_TOKEN env var.",
    )
    download_cmd.add_argument(
        "--channel-id",
        type=int,
        default=None,
        help="Discord channel ID. If omitted, uses MJ_CHANNEL_ID env var.",
    )
    download_cmd.add_argument(
        "--out",
        default="mj_downloads",
        help="Folder to save downloaded images (default: mj_downloads/)",
    )
    download_cmd.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Stop after downloading N images. Default: run until Ctrl+C",
    )

    # --- pipeline subcommand ---
    pipeline_cmd = subparsers.add_parser(
        "pipeline",
        help="Generate → send prompts to Discord → start MJ downloader in one go.",
    )

    # generation options (same as generate)
    pipeline_cmd.add_argument(
        "-p", "--provider",
        choices=["openai", "anthropic", "gemini", "llama", "deepseek"],
        default="openai",
        help="LLM provider to use (default: openai)",
    )
    pipeline_cmd.add_argument(
        "-l", "--list",
        default="adobe_cat.csv",
        help="Theme list CSV (theme,weight). Relative paths resolved under autovisuals/data/",
    )
    pipeline_cmd.add_argument(
        "-m", "--mode",
        choices=["r", "m", "random", "manual"],
        default="r",
        help="Theme mode",
    )
    pipeline_cmd.add_argument(
        "-t", "--title",
        choices=["r", "m", "random", "manual"],
        default="r",
        help="Title mode",
    )
    pipeline_cmd.add_argument(
        "-d", "--records",
        type=int,
        default=3,
        help="How many records to generate (default 3)",
    )
    pipeline_cmd.add_argument(
        "-r", "--repeat",
        type=int,
        default=5,
        help="Midjourney --r repeat parameter",
    )
    pipeline_cmd.add_argument(
        "-o", "--out",
        default="prompt",
        help="Output root folder (default: prompt/)",
    )

    # Discord webhook to send prompts
    pipeline_cmd.add_argument(
        "--webhook",
        default=None,
        help="Discord webhook URL for sending prompts. If omitted, uses WEBHOOK_URL env var.",
    )

    # Downloader options
    pipeline_cmd.add_argument(
        "--token",
        default=None,
        help="Discord Bot Token for downloader. If omitted, uses DISCORD_BOT_TOKEN env var.",
    )
    pipeline_cmd.add_argument(
        "--channel-id",
        type=int,
        default=None,
        help="Discord channel ID for MJ output. If omitted, uses MJ_CHANNEL_ID env var.",
    )
    pipeline_cmd.add_argument(
        "--download-out",
        default="mj_downloads",
        help="Root folder for downloaded images (default: mj_downloads/).",
    )
    pipeline_cmd.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Stop downloader after N images (default: no limit).",
    )

    # --- gallery subcommand ---
    gallery_cmd = subparsers.add_parser(
        "gallery",
        help="Build a static HTML gallery from downloaded images.",
    )

    gallery_cmd.add_argument(
        "--download-dir",
        default="mj_downloads",
        help="Root folder of downloaded images (default: mj_downloads/).",
    )
    gallery_cmd.add_argument(
        "--out",
        default="mj_gallery.html",
        help="Path to output HTML file (default: mj_gallery.html).",
    )

    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

    # generate
    if args.command == "generate":
        generate_main(
            provider=args.provider,
            list_arg=args.list,
            mode=args.mode,
            title_mode=args.title,
            n=args.records,
            repeat=args.repeat,
            out_arg=args.out,
        )

    # discord
    elif args.command == "discord":
        from .send_to_discord import send_prompt_file, get_latest_prompt_file

        if args.file:
            prompt_path = Path(args.file)
        else:
            prompt_path = get_latest_prompt_file()
            print(f"Using latest prompt file: {prompt_path}")

        webhook = args.webhook or os.environ.get("WEBHOOK_URL")
        if not webhook:
            raise ValueError("No webhook provided. Use -w or set WEBHOOK_URL env variable.")

        send_prompt_file(prompt_path, webhook)

    # download
    elif args.command == "download":
        from .mj_download import run_downloader

        run_downloader(
            token=args.token,
            channel_id=args.channel_id,
            download_dir=args.out,
            limit=args.limit,
        )

    # pipeline: generate → send → download
    elif args.command == "pipeline":
        from .send_to_discord import send_prompt_file, get_latest_prompt_file
        from .mj_download import run_downloader

        # 1) Generate prompts + metadata
        print("[pipeline] Step 1/3: generate")
        generate_main(
            provider=args.provider,
            list_arg=args.list,
            mode=args.mode,
            title_mode=args.title,
            n=args.records,
            repeat=args.repeat,
            out_arg=args.out,
        )

        # 2) Send latest prompts to Discord webhook
        print("[pipeline] Step 2/3: send prompts to Discord")
        prompt_path = get_latest_prompt_file()
        print(f"[pipeline] Using latest prompt file: {prompt_path}")

        webhook = args.webhook or os.environ.get("WEBHOOK_URL")
        if not webhook:
            raise ValueError(
                "No webhook provided. Use --webhook or set WEBHOOK_URL env variable."
            )

        send_prompt_file(prompt_path, webhook)

        # 3) Start downloader (blocking)
        print("[pipeline] Step 3/3: start MJ downloader")
        print("[pipeline] Now trigger Midjourney in your Discord channel.")
        run_downloader(
            token=args.token,
            channel_id=args.channel_id,
            download_dir=args.download_out,
            limit=args.limit,
        )

    # gallery
    elif args.command == "gallery":
        from .gallery import build_gallery

        out = build_gallery(download_root=args.download_dir, out_file=args.out)
        print(f"Gallery written to: {out}")

    else:
        parser.error(f"Unknown command: {args.command!r}")


if __name__ == "__main__":
    main()
