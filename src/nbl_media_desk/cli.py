"""Command-line entry point. Subcommands arrive in Phase 3."""

import argparse
from collections.abc import Sequence

from nbl_media_desk import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nbl-desk", description="AI post-game newsroom with a fact-check gate."
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    build_parser().parse_args(argv)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
