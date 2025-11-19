"""
Command-line interface for AutoVisuals.

Examples:
    python -m autovisuals generate -p openai -l adobe_cat.csv -m r -t r -d 5 -r 5 -o prompt
"""

import os
import argparse
from .get_mj_prompt import main as generate_main


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="autovisuals",
        description="AutoVisuals CLI - automated prompt and metadata generation.",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- generate subcommand ---
    gen = subparsers.add_parser(
        "generate",
        help="Generate prompts + metadata from a theme list",
    )

    gen.add_argument(
        "-p",
        "--provider",
        choices=["openai", "anthropic", "gemini", "llama", "deepseek"],
        default="openai",
        help="LLM provider to use (default: openai)",
    )
    gen.add_argument(
        "-l",
        "--list",
        default="adobe_cat.csv",
        help="Theme list CSV (theme,weight). Relative paths resolved under autovisuals/data/",
    )
    gen.add_argument(
        "-m",
        "--mode",
        choices=["r", "m", "random", "manual"],
        default="r",
        help="Theme mode: r/random for random, m/manual for manual input (default: r)",
    )
    gen.add_argument(
        "-t",
        "--title",
        choices=["r", "m", "random", "manual"],
        default="r",
        help="Title mode: r/random or m/manual (manual only applies in manual theme mode)",
    )
    gen.add_argument(
        "-d",
        "--records",
        type=int,
        default=3,
        help="Number of records to generate (default: 3)",
    )
    gen.add_argument(
        "-r",
        "--repeat",
        type=int,
        default=5,
        help="Midjourney --r repeat parameter (default: 5)",
    )
    gen.add_argument(
        "-o",
        "--out",
        default="prompt",
        help="Output root folder (default: prompt/)",
    )
    discord_cmd = subparsers.add_parser(
        "discord",
        help="Send prompts to Discord using a webhook. Defaults to latest folder + WEBHOOK_URL env.",
    )
    discord_cmd.add_argument(
        "-f", "--file",
        default=None,
        help="Path to prompt.txt. If omitted, uses the latest timestamp folder automatically."
    )
    discord_cmd.add_argument(
        "-w", "--webhook",
        default=None,
        help="Discord webhook URL. If omitted, reads from WEBHOOK_URL environment variable."
    )
    return parser


def main(argv=None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)

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
    elif args.command == "discord":
        from .send_to_discord import send_prompt_file, get_latest_prompt_file

        # Determine file
        if args.file:
            prompt_path = Path(args.file)
        else:
            prompt_path = get_latest_prompt_file()
            print(f"Using latest prompt file: {prompt_path}")

        # Determine webhook
        webhook = args.webhook or os.environ.get("WEBHOOK_URL")
        if not webhook:
            raise ValueError("No webhook provided. Use -w or set WEBHOOK_URL env variable.")

        send_prompt_file(prompt_path, webhook)

if __name__ == "__main__":
    main()
