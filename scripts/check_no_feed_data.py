"""Guard for ADR-0006: no third-party game data in the repository.

Fails if a JSON file over the size limit exists outside the allowed synthetic-data folders,
or if any committed file contains a Genius Sports / LiveStats image or data URL.
"""

import subprocess
import sys
from pathlib import Path

MAX_JSON_BYTES = 50_000
ALLOWED_DIRS = ("tests/fixtures/", "evals/golden/")
FORBIDDEN_MARKERS = ("geniussports.com/data/", "se-img.dcd-production")
SELF = "scripts/check_no_feed_data.py"


def tracked_files(root: Path) -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],  # noqa: S607
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    return [Path(line) for line in out.splitlines() if line]


def find_violations(root: Path, files: list[Path]) -> list[str]:
    problems: list[str] = []
    for rel in files:
        path = root / rel
        if not path.is_file():
            continue
        posix = rel.as_posix()
        if (
            path.suffix == ".json"
            and path.stat().st_size > MAX_JSON_BYTES
            and not posix.startswith(ALLOWED_DIRS)
        ):
            problems.append(f"{posix}: JSON over {MAX_JSON_BYTES} bytes outside allowed dirs")
        if posix == SELF or path.suffix not in {".json", ".py", ".md", ".yaml", ".yml", ".txt"}:
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        problems.extend(f"{posix}: contains '{m}'" for m in FORBIDDEN_MARKERS if m in text)
    return problems


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    problems = find_violations(root, tracked_files(root))
    for p in problems:
        print(f"ADR-0006 violation: {p}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
