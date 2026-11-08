"""Command-line entry point: `nbl-desk`."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence
from pathlib import Path

from nbl_media_desk import __version__
from nbl_media_desk.cache import GameCache
from nbl_media_desk.config import Settings
from nbl_media_desk.facts import build_fact_sheet
from nbl_media_desk.sources import FixtureSource, GameSource, LiveStatsSource, SourceError

DEFAULT_FIXTURES = Path("evals/golden")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nbl-desk", description="AI post-game newsroom with a fact-check gate."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    sub = parser.add_subparsers(dest="command")

    facts = sub.add_parser("facts", help="Print the verified fact sheet for a game.")
    facts.add_argument("game_id", help="Fixture folder name or numeric LiveStats game ID.")
    facts.add_argument("--source", choices=["fixture", "livestats"], default="fixture")
    facts.add_argument("--fixtures-dir", type=Path, default=DEFAULT_FIXTURES)
    facts.add_argument("--json", action="store_true", help="Output the full fact sheet as JSON.")
    return parser


def _source(args: argparse.Namespace, settings: Settings) -> GameSource:
    if args.source == "livestats":
        return LiveStatsSource(
            GameCache(Path(settings.cache_dir)), user_agent=settings.http_user_agent
        )
    return FixtureSource(args.fixtures_dir)


def _facts(args: argparse.Namespace) -> int:
    settings = Settings()
    try:
        game = _source(args, settings).get_game(args.game_id)
    except SourceError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    sheet = build_fact_sheet(game)
    if args.json:
        print(json.dumps(sheet.model_dump(mode="json"), indent=2))
    else:
        print(sheet.to_prompt_lines())
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if args.command == "facts":
        return _facts(args)
    parser.print_help()
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
