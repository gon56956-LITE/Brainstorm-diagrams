#!/usr/bin/env python3
"""Verify natural-language extraction examples stay structurally useful."""

from __future__ import annotations

import subprocess
import sys
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NATURALCASES_ROOT = ROOT / "naturalcases"
FISHBONE_NATURALCASES = NATURALCASES_ROOT / "fishbone"
FAULT_TREE_NATURALCASES = NATURALCASES_ROOT / "fault-tree"
EXCLUSION_TREE_NATURALCASES = NATURALCASES_ROOT / "exclusion-tree"
TWO_BY_TWO_NATURALCASES = NATURALCASES_ROOT / "two-by-two-matrix"
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
    if not NATURALCASES_ROOT.exists():
        raise AssertionError("Missing naturalcases directory")

    allowed_dirs = {"fishbone", "fault-tree", "exclusion-tree", "two-by-two-matrix"}
    for path in NATURALCASES_ROOT.iterdir():
        if path.name == "README.md":
            continue
        if not path.is_dir() or path.name not in allowed_dirs:
            raise AssertionError(f"Unexpected entry in naturalcases: {path.name}")

    for directory in [FISHBONE_NATURALCASES, FAULT_TREE_NATURALCASES, EXCLUSION_TREE_NATURALCASES, TWO_BY_TWO_NATURALCASES]:
        if not directory.exists():
            raise AssertionError(f"Missing naturalcase directory: {directory.name}")
        for path in directory.iterdir():
            if path.is_dir():
                raise AssertionError(f"Unexpected subdirectory in naturalcases/{directory.name}: {path.name}")
            if path.name == "README.md":
                continue
            if path.suffix.lower() in {".svg", ".png"}:
                raise AssertionError(f"Generated output does not belong in naturalcases/{directory.name}: {path.name}")
            if not (path.name.endswith(".source.txt") or path.name.endswith(".expected.md")):
                raise AssertionError(f"Unexpected file in naturalcases/{directory.name}: {path.name}")


def verify_prompt_template() -> None:
    if not PROMPT_TEMPLATE.exists():
        raise AssertionError("Missing natural-language prompt template")
    text = PROMPT_TEMPLATE.read_text(encoding="utf-8")
    required_phrases = [
        "Choose `fishbone` when the source asks for broad cause brainstorming",
        "Choose `fault_tree` when the source asks for logical failure decomposition",
        "Choose `exclusion_tree` when the source asks for sequential troubleshooting",
        "Choose `two_by_two_matrix` when the source asks to compare or prioritize options across two scoring dimensions",
        "do not start from default fishbone categories",
        "Extract 4-8 domain-specific categories",
        "Extract one specific top event",
        "Extract one target problem",
        "Include 4-20 scored items",
        "Do not add `Subtitle:` unless the user explicitly asks for a subtitle",
        "Do not add an item-level `Notes` column",
        "Use `Gate: AND` only when the source states that child conditions must occur together",
        "If the source is too thin",
        "Write structured Markdown to `work/<diagram-type>/<safe-name>.md`",
        "references/natural_language_review_checklist.md",
    ]
    for phrase in required_phrases:
        if phrase not in text:
            raise AssertionError(f"Natural-language prompt template missing required phrase: {phrase}")


def verify_case_pairs() -> None:
    verify_fishbone_case_pairs()
    verify_fault_tree_case_pairs()
    verify_exclusion_tree_case_pairs()
    verify_two_by_two_case_pairs()


def verify_fishbone_case_pairs() -> None:
    sources = sorted(FISHBONE_NATURALCASES.glob("*.source.txt"))
    if not sources:
        raise AssertionError("No fishbone naturalcase sources found")

    for source_path in sources:
        stem = source_path.name.removesuffix(".source.txt")
        expected_path = FISHBONE_NATURALCASES / f"{stem}.expected.md"
        verify_source_expected_pair(source_path, expected_path)
        verify_expected_markdown_renders(expected_path)
        verify_expected_badge_mappings(stem, expected_path)


def verify_fault_tree_case_pairs() -> None:
    sources = sorted(FAULT_TREE_NATURALCASES.glob("*.source.txt"))
    if not sources:
        raise AssertionError("No fault-tree naturalcase sources found")

    for source_path in sources:
        stem = source_path.name.removesuffix(".source.txt")
        expected_path = FAULT_TREE_NATURALCASES / f"{stem}.expected.md"
        verify_source_expected_pair(source_path, expected_path)
        verify_expected_markdown_renders(expected_path)
        verify_fault_tree_expected_structure(expected_path)


def verify_exclusion_tree_case_pairs() -> None:
    sources = sorted(EXCLUSION_TREE_NATURALCASES.glob("*.source.txt"))
    if not sources:
        raise AssertionError("No exclusion-tree naturalcase sources found")

    for source_path in sources:
        stem = source_path.name.removesuffix(".source.txt")
        expected_path = EXCLUSION_TREE_NATURALCASES / f"{stem}.expected.md"
        verify_source_expected_pair(source_path, expected_path)
        verify_expected_markdown_renders(expected_path)
        verify_exclusion_tree_expected_structure(expected_path)


def verify_two_by_two_case_pairs() -> None:
    sources = sorted(TWO_BY_TWO_NATURALCASES.glob("*.source.txt"))
    if not sources:
        raise AssertionError("No two-by-two naturalcase sources found")

    for source_path in sources:
        stem = source_path.name.removesuffix(".source.txt")
        expected_path = TWO_BY_TWO_NATURALCASES / f"{stem}.expected.md"
        verify_source_expected_pair(source_path, expected_path)
        verify_expected_markdown_renders(expected_path)
        verify_two_by_two_expected_structure(expected_path)


def verify_source_expected_pair(source_path: Path, expected_path: Path) -> None:
    if not expected_path.exists():
        raise AssertionError(f"Missing expected Markdown for {source_path.name}")
    if not source_path.read_text(encoding="utf-8").strip():
        raise AssertionError(f"Empty source: {source_path.name}")
    if not expected_path.read_text(encoding="utf-8").strip():
        raise AssertionError(f"Empty expected Markdown: {expected_path.name}")


def verify_expected_markdown_renders(path: Path) -> None:
    output_path = path.parent / f"{path.stem}.tmp.svg"
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


def verify_fault_tree_expected_structure(path: Path) -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from generate_diagram import parse_input

    data = parse_input(path)
    if data.get("diagram_type") != "fault_tree":
        raise AssertionError(f"{path.name}: expected diagram_type=fault_tree")
    if not str(data.get("top_event", {}).get("label", "")).strip():
        raise AssertionError(f"{path.name}: fault-tree naturalcase must include a top event")
    if not data.get("event_detail"):
        raise AssertionError(f"{path.name}: fault-tree naturalcase must include event_detail")

    children = data.get("tree", {}).get("children", [])
    if not isinstance(children, list) or len(children) < 2:
        raise AssertionError(f"{path.name}: fault-tree naturalcase should include at least two first-level events")

    gates: set[str] = {str(data.get("tree", {}).get("gate", "OR")).upper()}
    basic_count = 0
    nested_intermediate_count = 0
    for child in children:
        if not isinstance(child, dict):
            continue
        gates.add(str(child.get("gate", "OR")).upper())
        for grandchild in child.get("children", []):
            if not isinstance(grandchild, dict):
                continue
            if grandchild.get("type") == "basic_event":
                basic_count += 1
            elif grandchild.get("type") == "intermediate_event":
                nested_intermediate_count += 1
                gates.add(str(grandchild.get("gate", "OR")).upper())
                basic_count += sum(
                    1
                    for leaf in grandchild.get("children", [])
                    if isinstance(leaf, dict) and leaf.get("type") == "basic_event"
                )

    if not gates <= {"AND", "OR"}:
        raise AssertionError(f"{path.name}: fault-tree gates must be AND or OR only: {sorted(gates)}")
    if not {"AND", "OR"} <= gates:
        raise AssertionError(f"{path.name}: fault-tree naturalcase should demonstrate both AND and OR gates")
    if nested_intermediate_count < 1:
        raise AssertionError(f"{path.name}: fault-tree naturalcase should include one nested intermediate event")
    if basic_count < 4:
        raise AssertionError(f"{path.name}: fault-tree naturalcase should include several basic event leaves")


def verify_exclusion_tree_expected_structure(path: Path) -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from generate_diagram import parse_input

    data = parse_input(path)
    if data.get("diagram_type") != "exclusion_tree":
        raise AssertionError(f"{path.name}: expected diagram_type=exclusion_tree")

    problem = data.get("problem", {})
    if not isinstance(problem, dict) or not str(problem.get("text_en") or problem.get("text_zh") or "").strip():
        raise AssertionError(f"{path.name}: exclusion-tree naturalcase must include a target problem")

    event_detail = data.get("event_detail", {})
    if not isinstance(event_detail, dict) or not (
        str(event_detail.get("text", "")).strip() or event_detail.get("bullets")
    ):
        raise AssertionError(f"{path.name}: exclusion-tree naturalcase must include event_detail")

    checks = data.get("checks", [])
    if not isinstance(checks, list) or not 3 <= len(checks) <= 6:
        raise AssertionError(f"{path.name}: exclusion-tree naturalcase should include 3-6 checks")

    for index, check in enumerate(checks, start=1):
        if not isinstance(check, dict):
            raise AssertionError(f"{path.name}: exclusion-tree check {index} must be an object")
        if not str(check.get("text_en") or check.get("text_zh") or check.get("label") or "").strip():
            raise AssertionError(f"{path.name}: exclusion-tree check {index} must include a testable question")
        conclusion = check.get("fail_conclusion", {})
        if not isinstance(conclusion, dict) or not str(
            conclusion.get("text_en") or conclusion.get("text_zh") or ""
        ).strip():
            raise AssertionError(f"{path.name}: exclusion-tree check {index} must include a fail conclusion")

    final_pass = data.get("final_pass_conclusion", {})
    if not isinstance(final_pass, dict) or not str(final_pass.get("text_en") or final_pass.get("text_zh") or "").strip():
        raise AssertionError(f"{path.name}: exclusion-tree naturalcase must include final_pass_conclusion")


def verify_two_by_two_expected_structure(path: Path) -> None:
    sys.path.insert(0, str(ROOT / "scripts"))
    from generate_diagram import parse_input

    text = path.read_text(encoding="utf-8")
    if re.search(r"^Subtitle\s*:", text, flags=re.M):
        raise AssertionError(f"{path.name}: two-by-two naturalcase should not include Subtitle unless explicitly requested")
    if re.search(r"\|\s*Notes\s*\|", text, flags=re.I):
        raise AssertionError(f"{path.name}: two-by-two naturalcase should not include item-level Notes column")

    data = parse_input(path)
    if data.get("diagram_type") != "two_by_two_matrix":
        raise AssertionError(f"{path.name}: expected diagram_type=two_by_two_matrix")

    preset = str(data.get("preset", "")).strip()
    if preset not in {"action_priority", "risk_benefit", "evidence_impact", "value_feasibility", "urgency_importance", "custom"}:
        raise AssertionError(f"{path.name}: unexpected matrix preset: {preset}")

    language = str(data.get("language", "auto")).strip()
    if language not in {"auto", "en", "zh"}:
        raise AssertionError(f"{path.name}: language must be auto, en, or zh")

    notes = str(data.get("notes", "")).strip()
    if language == "zh" and visual_len(notes) > 60:
        raise AssertionError(f"{path.name}: Chinese notes should fit the two-line guide card")
    if language != "zh" and visual_len(notes) > 70:
        raise AssertionError(f"{path.name}: English notes should fit the two-line guide card")

    items = data.get("items", [])
    if not isinstance(items, list) or len(items) < 4:
        raise AssertionError(f"{path.name}: two-by-two naturalcase should include at least four scored items")
    if len(items) > 20:
        raise AssertionError(f"{path.name}: two-by-two naturalcase must not exceed 20 items")

    quadrants: set[tuple[bool, bool]] = set()
    for index, item in enumerate(items, start=1):
        if not isinstance(item, dict):
            raise AssertionError(f"{path.name}: item {index} must be an object")
        if not str(item.get("name") or item.get("label") or "").strip():
            raise AssertionError(f"{path.name}: item {index} must include a name")
        if str(item.get("notes", "")).strip():
            raise AssertionError(f"{path.name}: item {index} should not include non-rendered item-level notes")
        try:
            x_score = float(item.get("x_score"))
            y_score = float(item.get("y_score"))
        except (TypeError, ValueError) as exc:
            raise AssertionError(f"{path.name}: item {index} must include numeric x_score and y_score") from exc
        if not (1 <= x_score <= 5 and 1 <= y_score <= 5):
            raise AssertionError(f"{path.name}: item {index} scores must be 1-5")
        quadrants.add((x_score >= 3, y_score >= 3))

    if len(quadrants) < 3:
        raise AssertionError(f"{path.name}: two-by-two naturalcase should exercise at least three quadrants")


def visual_len(text: str) -> int:
    return sum(2 if ord(char) > 127 else 1 for char in text)


if __name__ == "__main__":
    raise SystemExit(main())
