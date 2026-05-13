#!/usr/bin/env python3
"""Render a fishbone SVG from a work/ input file."""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work"
GENERATE = ROOT / "scripts" / "generate_diagram.py"
PYTHON = Path(sys.executable)
SAFE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render work/<name>.md or work/<name>.json to work/<name>.svg."
    )
    parser.add_argument("name", help="Diagram name or work file stem")
    parser.add_argument(
        "--format",
        choices=["md", "json"],
        help="Input format when both work/<name>.md and work/<name>.json exist",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stem = validate_work_name(args.name)
    if stem is None:
        return 1

    input_path = resolve_input_path(stem, args.format)
    if input_path is None:
        return 1

    output_path = WORK / f"{stem}.svg"
    result = subprocess.run(
        [str(PYTHON), str(GENERATE), str(input_path), str(output_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.stdout:
        print(result.stdout, end="")
    if result.stderr:
        print(result.stderr, file=sys.stderr, end="")
    if result.returncode != 0:
        return result.returncode

    print(f"Rendered work SVG: {output_path.relative_to(ROOT)}")
    return 0


def resolve_input_path(stem: str, requested_format: str | None) -> Path | None:
    if requested_format:
        path = WORK / f"{stem}.{requested_format}"
        if not path.exists():
            print(f"Error: missing work input {path.relative_to(ROOT)}", file=sys.stderr)
            return None
        return path

    candidates = [WORK / f"{stem}.md", WORK / f"{stem}.json"]
    existing = [path for path in candidates if path.exists()]
    if len(existing) == 1:
        return existing[0]
    if not existing:
        print(f"Error: no work input found for '{stem}'. Expected work/{stem}.md or work/{stem}.json.", file=sys.stderr)
        return None

    print(
        f"Error: both work/{stem}.md and work/{stem}.json exist. Use --format md or --format json.",
        file=sys.stderr,
    )
    return None


def validate_work_name(value: str) -> str | None:
    name = value.strip()
    if "\\" in name or "/" in name or Path(name).is_absolute():
        print("Error: diagram name must be a simple file name, not a path.", file=sys.stderr)
        return None
    if not SAFE_NAME_PATTERN.fullmatch(name):
        print(
            "Error: diagram name may use only lowercase letters, numbers, hyphen, and underscore; "
            "start with a letter or number; maximum length is 64. Example: my-analysis",
            file=sys.stderr,
        )
        return None
    return name


if __name__ == "__main__":
    raise SystemExit(main())
