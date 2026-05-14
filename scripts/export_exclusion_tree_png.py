#!/usr/bin/env python3
"""Export a work/exclusion-tree/ SVG to PNG using the bundled Python runtime."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

from export_png import export_svg_to_png


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work" / "exclusion-tree"
SAFE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export work/exclusion-tree/<name>.svg to work/exclusion-tree/<name>.png.")
    parser.add_argument("name", help="Diagram name, such as startup-troubleshooting")
    parser.add_argument("--scale", type=float, default=1.0, help="PNG scale factor (default: 1.0)")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stem = validate_work_name(args.name)
    if stem is None:
        return 1
    if args.scale <= 0 or args.scale > 4:
        print("Error: --scale must be greater than 0 and no more than 4.", file=sys.stderr)
        return 1

    svg_path = WORK / f"{stem}.svg"
    png_path = WORK / f"{stem}.png"
    if not svg_path.exists():
        print(f"Error: missing work SVG {svg_path.relative_to(ROOT)}", file=sys.stderr)
        return 1

    try:
        export_svg_to_png(svg_path, png_path, scale=args.scale)
    except Exception as exc:
        print(f"Error: failed to export PNG: {exc}", file=sys.stderr)
        return 1

    print(f"Exported PNG: {png_path.relative_to(ROOT)}")
    return 0


def validate_work_name(value: str) -> str | None:
    name = value.strip()
    if "\\" in name or "/" in name or Path(name).is_absolute():
        print("Error: diagram name must be a simple file name, not a path.", file=sys.stderr)
        return None
    if not SAFE_NAME_PATTERN.fullmatch(name):
        print(
            "Error: diagram name may use only lowercase letters, numbers, hyphen, and underscore; "
            "start with a letter or number; maximum length is 64. Example: startup-troubleshooting",
            file=sys.stderr,
        )
        return None
    return name


if __name__ == "__main__":
    raise SystemExit(main())
