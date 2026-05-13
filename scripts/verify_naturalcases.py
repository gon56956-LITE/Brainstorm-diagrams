#!/usr/bin/env python3
"""Verify natural-language extraction examples stay structurally useful."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NATURALCASES = ROOT / "naturalcases"
PROMPT_TEMPLATE = ROOT / "references" / "natural_language_prompt_template.md"
GENERATE = ROOT / "scripts" / "generate_diagram.py"
PYTHON = Path(sys.executable)

EXPECTED_LUCIDE_CASE_ICONS = {
    "optical-module-stability": {
        "lucide:network",
        "lucide:aperture",
        "lucide:thermometer",
        "lucide:cog",
        "lucide:circuit-board",
        "lucide:boxes",
        "lucide:wrench",
    }
}


def main() -> int:
    verify_directory()
    verify_prompt_template()
    verify_case_pairs()
    print("Naturalcase verification passed")
    return 0


def verify_directory() -> None:
    if not NATURALCASES.exists():
        raise AssertionError("Missing naturalcases directory")

    for path in NATURALCASES.iterdir():
        if path.is_dir():
            raise AssertionError(f"Unexpected subdirectory in naturalcases: {path.name}")
        if path.name == "README.md":
            continue
        if path.suffix.lower() in {".svg", ".png"}:
            raise AssertionError(f"Generated output does not belong in naturalcases: {path.name}")
        if not (path.name.endswith(".source.txt") or path.name.endswith(".expected.md")):
            raise AssertionError(f"Unexpected file in naturalcases: {path.name}")


def verify_prompt_template() -> None:
    if not PROMPT_TEMPLATE.exists():
        raise AssertionError("Missing natural-language prompt template")
    text = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    required_phrases = [
        "do not start from default fishbone categories",
        "Extract 4-8 domain-specific categories",
        "Put 2-5 primary causes",
        "Do not create subcategories or second-level causes",
        "If the source is too thin",
        "Write structured Markdown to `work/<safe-name>.md`",
        "references/natural_language_review_checklist.md",
    ]
    for phrase in required_phrases:
        if phrase not in text:
            raise AssertionError(f"Natural-language prompt template missing required phrase: {phrase}")


def verify_case_pairs() -> None:
    sources = sorted(NATURALCASES.glob("*.source.txt"))
    if not sources:
        raise AssertionError("No naturalcase sources found")

    for source_path in sources:
        stem = source_path.name.removesuffix(".source.txt")
        expected_path = NATURALCASES / f"{stem}.expected.md"
        if not expected_path.exists():
            raise AssertionError(f"Missing expected Markdown for {source_path.name}")
        if not source_path.read_text(encoding="utf-8").strip():
            raise AssertionError(f"Empty source: {source_path.name}")
        if not expected_path.read_text(encoding="utf-8").strip():
            raise AssertionError(f"Empty expected Markdown: {expected_path.name}")
        verify_expected_markdown_renders(expected_path)
        verify_expected_badge_mappings(stem, expected_path)


def verify_expected_markdown_renders(path: Path) -> None:
    output_path = NATURALCASES / f"{path.stem}.tmp.svg"
    try:
        result = subprocess.run(
            [str(PYTHON), str(GENERATE), str(path), str(output_path)],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if result.returncode != 0:
            raise AssertionError(f"Expected Markdown did not render: {path.name}\n{result.stderr}")
        if not output_path.exists():
            raise AssertionError(f"Expected Markdown did not create temporary SVG: {path.name}")
    finally:
        output_path.unlink(missing_ok=True)


def verify_expected_badge_mappings(stem: str, path: Path) -> None:
    expected_icons = EXPECTED_LUCIDE_CASE_ICONS.get(stem)
    if not expected_icons:
        return

    sys.path.insert(0, str(ROOT / "scripts"))
    from generate_diagram import parse_structured_markdown
    from renderers.fishbone import icon_for_category, normalize_input

    data = normalize_input(parse_structured_markdown(path.read_text(encoding="utf-8")))
    actual_icons = {icon_for_category(category) for category in data["categories"]}
    missing_icons = expected_icons - actual_icons
    if missing_icons:
        raise AssertionError(f"{path.name}: missing expected Lucide badge mappings: {sorted(missing_icons)}")


if __name__ == "__main__":
    raise SystemExit(main())
