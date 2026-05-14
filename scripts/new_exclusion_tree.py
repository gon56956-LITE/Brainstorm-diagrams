#!/usr/bin/env python3
"""Create a new exclusion-tree workspace input from a template and render its SVG."""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
WORK = ROOT / "work" / "exclusion-tree"
GENERATE = ROOT / "scripts" / "generate_diagram.py"
PYTHON = Path(sys.executable)
SAFE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Create a new exclusion-tree input in work/exclusion-tree/ and render an initial SVG."
    )
    parser.add_argument("name", help="Diagram name, used as the output file stem")
    parser.add_argument(
        "--format",
        choices=["md", "json"],
        default="md",
        help="Template format to copy into work/exclusion-tree/ (default: md)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing work files for the same name",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    stem = validate_work_name(args.name)
    if stem is None:
        return 1

    template_path = TEMPLATES / f"exclusion-tree.template.{args.format}"
    input_path = WORK / f"{stem}.{args.format}"
    output_path = WORK / f"{stem}.svg"

    if not template_path.exists():
        print(f"Error: missing template {template_path.relative_to(ROOT)}", file=sys.stderr)
        return 1

    existing = [path for path in [input_path, output_path] if path.exists()]
    if existing and not args.force:
        joined = ", ".join(str(path.relative_to(ROOT)) for path in existing)
        print(f"Error: refusing to overwrite existing file(s): {joined}", file=sys.stderr)
        print("Use --force to replace them.", file=sys.stderr)
        return 1

    WORK.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(template_path, input_path)

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

    print(f"Created input: {input_path.relative_to(ROOT)}")
    print(f"Created SVG: {output_path.relative_to(ROOT)}")
    print("Edit the input file, then regenerate with:")
    print(f'& "{PYTHON}" scripts\\render_exclusion_tree_work.py {stem}')
    return 0


def validate_work_name(value: str) -> str | None:
    name = value.strip()
    if "\\" in name or "/" in name or Path(name).is_absolute():
        print("Error: diagram name must be a simple file name, not a path.", file=sys.stderr)
        return None
    if not SAFE_NAME_PATTERN.fullmatch(name):
        print(
            "Error: diagram name may use only lowercase letters, numbers, hyphen, and underscore; "
            "start with a letter or number; maximum length is 64. Example: startup-exclusion-tree",
            file=sys.stderr,
        )
        return None
    return name


if __name__ == "__main__":
    raise SystemExit(main())
