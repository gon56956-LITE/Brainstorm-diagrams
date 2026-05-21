#!/usr/bin/env python3
"""Render simplified FMEA table diagrams as deterministic SVG."""

from __future__ import annotations

import html
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[2]
LUCIDE_CANDIDATES = ROOT / "assets" / "lucide-candidates"

WIDTH = 1920
MIN_HEIGHT = 1080
MARGIN_X = 28
FONT = "Arial"
NAVY = "#0B3A78"
TEXT = "#062B5F"
MUTED = "#536781"
GRID = "#C6D5EA"
GRID_STRONG = "#AFC1DA"
HEADER_FILL = "#103A70"
ROW_ALT = "#F4F8FD"
PANEL_FILL = "#F7FAFF"
HIGH_FILL = "#FCE8E8"
HIGH_STROKE = "#D12B2B"
MED_FILL = "#FFF2D6"
MED_STROKE = "#D79200"
LOW_FILL = "#E8F5EA"
LOW_STROKE = "#2F8C46"
SCORE_LOW = "#2F8C46"
SCORE_MED = "#D79200"
SCORE_HIGH = "#D12B2B"


@dataclass(frozen=True)
class Column:
    key: str
    label: str
    width: int
    align: str = "left"


@dataclass(frozen=True)
class DensityProfile:
    name: str
    min_row_h: int
    max_row_h: int
    vertical_padding: int
    line_h: int
    text_font: float
    item_font: float


DENSITY_PROFILES = {
    "normal": DensityProfile("normal", 88, 190, 28, 16, 12.5, 13),
    "compact": DensityProfile("compact", 74, 172, 22, 15, 12.5, 13),
    "dense": DensityProfile("dense", 64, 156, 16, 14, 12, 12.5),
}


COLUMNS = [
    Column("item_function", "Item / Function", 150),
    Column("failure_mode", "Potential Failure Mode", 155),
    Column("failure_effects", "Effects", 180),
    Column("failure_causes", "Causes", 235),
    Column("prevention_controls", "Prevention Controls", 210),
    Column("detection_controls", "Detection Controls", 200),
    Column("severity", "S", 55, "center"),
    Column("occurrence", "O", 55, "center"),
    Column("detection", "D", 55, "center"),
    Column("rpn", "RPN", 70, "center"),
    Column("recommended_actions", "Recommended Actions", 220),
    Column("owner", "Owner", 85, "center"),
    Column("target_completion", "Target", 105, "center"),
    Column("status", "Status", 113, "center"),
]
TABLE_W = sum(column.width for column in COLUMNS)


LABELS = {
    "en": {
        "goal": "Goal",
        "rating": "Rating Scale",
        "rpn_guide": "RPN Guide",
        "priority": "RPN Priority Guide",
        "notes": "Notes",
        "review": "Review Info",
        "high": "High",
        "medium": "Medium",
        "low": "Low",
    },
    "zh": {
        "goal": "目标",
        "rating": "评分说明",
        "rpn_guide": "RPN 指南",
        "priority": "RPN 优先级指南",
        "notes": "备注",
        "review": "评审信息",
        "high": "高",
        "medium": "中",
        "low": "低",
    },
}


HEADER_ZH = {
    "item_function": "对象 / 功能",
    "failure_mode": "潜在失效模式",
    "failure_effects": "影响",
    "failure_causes": "原因",
    "prevention_controls": "预防控制",
    "detection_controls": "探测控制",
    "severity": "S",
    "occurrence": "O",
    "detection": "D",
    "rpn": "RPN",
    "recommended_actions": "建议措施",
    "owner": "负责人",
    "target_completion": "目标日期",
    "status": "状态",
}


ICON_KEYWORDS = [
    ("power", "circuit-board"),
    ("voltage", "circuit-board"),
    ("connector", "plug"),
    ("cable", "cable"),
    ("thermal", "thermometer"),
    ("temperature", "thermometer"),
    ("firmware", "cpu"),
    ("software", "cpu"),
    ("memory", "memory-stick"),
    ("optical", "aperture"),
    ("fiber", "aperture"),
    ("lens", "aperture"),
    ("package", "package"),
    ("mechanical", "package"),
    ("inspection", "clipboard-check"),
    ("test", "clipboard-check"),
    ("cooling", "fan"),
    ("fan", "fan"),
]

ICON_COLORS = {
    "aperture": "#155CB4",
    "circuit-board": "#164DAD",
    "plug": "#258C6B",
    "cable": "#258C6B",
    "thermometer": "#6E49C9",
    "fan": "#D98600",
    "cpu": "#1686A7",
    "memory-stick": "#1686A7",
    "package": "#8A61D1",
    "clipboard-check": "#2F8C46",
    "component": "#245C9A",
}


def render_fmea_table_to_file(data: dict[str, Any], output_path: Path | str) -> dict[str, Any]:
    output = Path(output_path)
    normalized = normalize_data(data)
    svg = render_svg(normalized)
    ET.fromstring(svg)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(svg, encoding="utf-8", newline="\n")
    return {
        "path": str(output),
        "format": "svg",
        "diagram_type": "fmea_table",
        "theme": "clean_presentation",
        "diagnostics": normalized["diagnostics"],
    }


def parse_fmea_table_markdown(text: str) -> dict[str, Any]:
    metadata, body = split_front_matter(text)
    rows: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    current_field = ""
    title = metadata.get("title", "")
    goal = metadata.get("goal", "")
    notes: list[str] = []
    project: dict[str, str] = {}

    for raw_line in body.splitlines():
        line = raw_line.rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("# "):
            title = stripped[2:].strip()
            current = None
            current_field = ""
            continue
        if stripped.startswith("## "):
            current = {}
            rows.append(current)
            current_field = ""
            continue
        parsed = parse_key_value(stripped)
        if parsed:
            key, value = parsed
            canonical = canonical_field(key)
            if canonical == "goal":
                goal = value
            elif canonical == "note":
                notes.append(value)
            elif canonical.startswith("project."):
                project[canonical.split(".", 1)[1]] = value
            elif current is None and canonical == "owner":
                project["owner"] = value
            elif current is not None and canonical:
                if canonical in LIST_FIELDS:
                    current[canonical] = split_inline_list(value)
                    current_field = canonical
                else:
                    current[canonical] = value
                    current_field = canonical
            else:
                current_field = ""
            continue
        bullet = parse_bullet(stripped)
        if bullet is not None and current is not None and current_field in LIST_FIELDS:
            current.setdefault(current_field, []).append(bullet)
        elif bullet is not None:
            notes.append(bullet)

    return {
        "diagram_type": "fmea_table",
        "fmea_type": metadata.get("fmea_type", "process"),
        "language": metadata.get("language", "auto"),
        "title": title or "FMEA Table",
        "goal": goal,
        "project": project,
        "rows": rows,
        "notes": notes,
    }


LIST_FIELDS = {
    "failure_effects",
    "failure_causes",
    "prevention_controls",
    "detection_controls",
    "recommended_actions",
}


def split_front_matter(text: str) -> tuple[dict[str, str], str]:
    lines = text.lstrip("\ufeff").splitlines()
    metadata: dict[str, str] = {}
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                for raw in lines[1:index]:
                    parsed = parse_key_value(raw.strip())
                    if parsed:
                        metadata[parsed[0].lower().replace("-", "_")] = parsed[1]
                return metadata, "\n".join(lines[index + 1 :])
    return metadata, text


def parse_key_value(line: str) -> tuple[str, str] | None:
    match = re.match(r"^([A-Za-z][A-Za-z0-9_ /.-]*?)\s*:\s*(.*?)\s*$", line)
    if not match:
        return None
    return match.group(1).strip(), match.group(2).strip().strip("\"'")


def canonical_field(key: str) -> str:
    normalized = key.strip().lower().replace("-", " ").replace("_", " ")
    normalized = re.sub(r"\s+", " ", normalized)
    mapping = {
        "goal": "goal",
        "note": "note",
        "notes": "note",
        "project": "project.name",
        "review frequency": "project.review_frequency",
        "last review date": "project.last_review_date",
        "owner": "owner",
        "item": "item_function",
        "function": "item_function",
        "item function": "item_function",
        "item / function": "item_function",
        "icon": "icon",
        "failure mode": "failure_mode",
        "potential failure mode": "failure_mode",
        "effects": "failure_effects",
        "failure effects": "failure_effects",
        "causes": "failure_causes",
        "failure causes": "failure_causes",
        "prevention controls": "prevention_controls",
        "current prevention controls": "prevention_controls",
        "detection controls": "detection_controls",
        "current detection controls": "detection_controls",
        "severity": "severity",
        "s": "severity",
        "occurrence": "occurrence",
        "o": "occurrence",
        "detection": "detection",
        "d": "detection",
        "rpn": "rpn",
        "recommended actions": "recommended_actions",
        "actions": "recommended_actions",
        "target": "target_completion",
        "target completion": "target_completion",
        "status": "status",
    }
    return mapping.get(normalized, normalized.replace(" ", "_"))


def parse_bullet(line: str) -> str | None:
    match = re.match(r"^(?:[-*+]|\d+[.)])\s+(.+)$", line)
    if not match:
        return None
    return match.group(1).strip()


def split_inline_list(value: str) -> list[str]:
    if not value:
        return []
    parts = re.split(r"\s*(?:;|\n)\s*", value)
    return [part.strip() for part in parts if part.strip()]


def normalize_data(data: dict[str, Any]) -> dict[str, Any]:
    diagnostics: list[str] = []
    language = normalize_language(data.get("language", "auto"), data)
    scoring = data.get("scoring") if isinstance(data.get("scoring"), dict) else {}
    thresholds = scoring.get("thresholds") if isinstance(scoring.get("thresholds"), dict) else {}
    high_threshold = parse_int(thresholds.get("high"), 200) or 200
    medium_threshold = parse_int(thresholds.get("medium"), 100) or 100
    raw_rows = data.get("rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        raise ValueError("fmea_table requires at least one row.")

    rows: list[dict[str, Any]] = []
    for index, raw_row in enumerate(raw_rows, start=1):
        if not isinstance(raw_row, dict):
            diagnostics.append(f"Ignored row {index}: row must be an object.")
            continue
        row = normalize_row(raw_row, index, high_threshold, medium_threshold, diagnostics)
        rows.append(row)
    if not rows:
        raise ValueError("fmea_table has no valid rows.")

    project = data.get("project") if isinstance(data.get("project"), dict) else {}
    return {
        "diagram_type": "fmea_table",
        "language": language,
        "title": collapse(data.get("title")) or default_title(language),
        "goal": collapse(data.get("goal")) or default_goal(language),
        "project": project,
        "rows": rows,
        "notes": normalize_list(data.get("notes")),
        "thresholds": {"high": high_threshold, "medium": medium_threshold},
        "diagnostics": diagnostics,
    }


def normalize_row(
    raw: dict[str, Any],
    index: int,
    high_threshold: int,
    medium_threshold: int,
    diagnostics: list[str],
) -> dict[str, Any]:
    severity = parse_score(raw.get("severity"), "severity", index, diagnostics)
    occurrence = parse_score(raw.get("occurrence"), "occurrence", index, diagnostics)
    detection = parse_score(raw.get("detection"), "detection", index, diagnostics)
    provided_rpn = parse_int(raw.get("rpn"), None)
    if provided_rpn is not None:
        rpn = provided_rpn
    elif severity is not None and occurrence is not None and detection is not None:
        rpn = severity * occurrence * detection
    else:
        rpn = None
        diagnostics.append(f"Row {index}: RPN not calculated because S/O/D is incomplete.")
    return {
        "id": collapse(raw.get("id")) or f"F{index}",
        "item_function": collapse(raw.get("item_function") or raw.get("item") or raw.get("function")),
        "icon": collapse(raw.get("icon")),
        "failure_mode": collapse(raw.get("failure_mode")),
        "failure_effects": normalize_list(raw.get("failure_effects") or raw.get("effects")),
        "failure_causes": normalize_list(raw.get("failure_causes") or raw.get("causes")),
        "prevention_controls": normalize_list(raw.get("prevention_controls")),
        "detection_controls": normalize_list(raw.get("detection_controls")),
        "severity": severity,
        "occurrence": occurrence,
        "detection": detection,
        "rpn": rpn,
        "risk_level": risk_level(rpn, high_threshold, medium_threshold),
        "recommended_actions": normalize_list(raw.get("recommended_actions") or raw.get("actions")),
        "owner": collapse(raw.get("owner")),
        "target_completion": collapse(raw.get("target_completion") or raw.get("target")),
        "status": collapse(raw.get("status")) or "Open",
    }


def parse_score(value: Any, label: str, row_index: int, diagnostics: list[str]) -> int | None:
    if value in (None, ""):
        return None
    parsed = parse_int(value, None)
    if parsed is None or parsed < 1 or parsed > 10:
        diagnostics.append(f"Row {row_index}: {label} should be an integer from 1 to 10.")
        return None
    return parsed


def parse_int(value: Any, default: int | None) -> int | None:
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return default


def risk_level(rpn: int | None, high_threshold: int, medium_threshold: int) -> str:
    if rpn is None:
        return "unknown"
    if rpn >= high_threshold:
        return "high"
    if rpn >= medium_threshold:
        return "medium"
    return "low"


def normalize_language(value: Any, data: dict[str, Any]) -> str:
    language = collapse(value).lower()
    if language in {"zh", "cn", "chinese"}:
        return "zh"
    if language in {"bilingual", "dual"}:
        return "bilingual"
    if language in {"en", "english"}:
        return "en"
    text = repr(data)
    return "zh" if re.search(r"[\u4e00-\u9fff]", text) else "en"


def default_title(language: str) -> str:
    return "FMEA Table" if language != "zh" else "FMEA 表"


def default_goal(language: str) -> str:
    if language == "zh":
        return "识别关键失效风险，按 RPN 优先推进改进措施。"
    return "Identify critical failure risks and prioritize corrective actions by RPN."


def normalize_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [collapse(item) for item in value if collapse(item)]
    if isinstance(value, str):
        return split_inline_list(value)
    return [collapse(value)]


def collapse(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "; ".join(collapse(item) for item in value if collapse(item))
    return " ".join(str(value).split())


def render_svg(data: dict[str, Any]) -> str:
    rows = data["rows"]
    language = data["language"]
    table_x = 16
    table_y = 154
    header_h = 62
    density = density_for_rows(len(rows))
    row_heights = [measure_row_height(row, density) for row in rows]
    table_h = header_h + sum(row_heights)
    bottom_y = table_y + table_h + 18
    bottom_h = 128
    height = max(MIN_HEIGHT, bottom_y + bottom_h + 34)
    parts: list[str] = [
        svg_open(WIDTH, height),
        f'<rect width="{WIDTH}" height="{height}" fill="#FFFFFF"/>',
        f'<g id="fmea-table" font-family="{FONT}" fill="{TEXT}">',
    ]
    render_title(parts, data)
    render_top_panels(parts, data)
    render_main_table(parts, data, table_x, table_y, header_h, row_heights, density)
    render_bottom_panels(parts, data, bottom_y, bottom_h)
    parts.append("</g>")
    parts.append("</svg>")
    return "\n".join(parts)


def svg_open(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="FMEA table diagram">'
    )


def render_title(parts: list[str], data: dict[str, Any]) -> None:
    label = labels(data["language"])
    parts.append(f'<text x="{MARGIN_X}" y="54" font-size="34" font-weight="700">{esc(data["title"])}</text>')
    goal_lines = wrap_text(f"{label['goal']}: {data['goal']}", 116, max_lines=2)
    for idx, line in enumerate(goal_lines):
        parts.append(f'<text x="{MARGIN_X}" y="{96 + idx * 24}" font-size="17" fill="{MUTED}">{esc(line)}</text>')


def render_top_panels(parts: list[str], data: dict[str, Any]) -> None:
    label = labels(data["language"])
    render_rating_scale(parts, 1048, 22, 844, 96, label["rating"])


def render_rating_scale(parts: list[str], x: int, y: int, w: int, h: int, title: str) -> None:
    parts.append(f'<g id="fmea-rating-scale" class="fmea-panel"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{PANEL_FILL}" stroke="#8DA9CC" stroke-width="1.5"/>')
    parts.append(f'<text x="{x + 18}" y="{y + 28}" font-size="17" font-weight="700">{esc(title)} (1-10)</text>')
    metrics = [
        ("S", "Severity", "Customer / product impact", "#D12B2B"),
        ("O", "Occurrence", "Failure likelihood", "#D79200"),
        ("D", "Detection", "Detection difficulty", "#2F8C46"),
    ]
    col_w = (w - 36) / 3
    for index, (letter, name, detail, color) in enumerate(metrics):
        col_x = x + 18 + index * col_w
        if index:
            parts.append(f'<line x1="{col_x - 10:.1f}" y1="{y + 40}" x2="{col_x - 10:.1f}" y2="{y + h - 12}" stroke="{GRID}" stroke-width="1.2"/>')
        parts.append(f'<circle cx="{col_x + 14:.1f}" cy="{y + 55}" r="13" fill="{color}"/>')
        parts.append(f'<text x="{col_x + 14:.1f}" y="{y + 60}" font-size="13" font-weight="700" text-anchor="middle" fill="#FFFFFF">{letter}</text>')
        parts.append(f'<text x="{col_x + 36:.1f}" y="{y + 51}" font-size="13" font-weight="700">{name}</text>')
        parts.append(f'<text x="{col_x + 36:.1f}" y="{y + 70}" font-size="11.5" fill="{TEXT}">{esc(detail)}</text>')
        parts.append(f'<text x="{col_x + 36:.1f}" y="{y + 88}" font-size="11.5" fill="{MUTED}">1 = low / easy, 10 = high</text>')
    parts.append("</g>")


def render_panel(parts: list[str], x: int, y: int, w: int, h: int, title: str, lines: list[str], group_id: str = "") -> None:
    id_attr = f' id="{group_id}"' if group_id else ""
    parts.append(f'<g{id_attr} class="fmea-panel"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{PANEL_FILL}" stroke="#8DA9CC" stroke-width="1.5"/>')
    parts.append(f'<text x="{x + 18}" y="{y + 30}" font-size="18" font-weight="700">{esc(title)}</text>')
    for idx, line in enumerate(lines[:4]):
        parts.append(f'<text x="{x + 18}" y="{y + 58 + idx * 20}" font-size="13" fill="{MUTED}">{esc(line)}</text>')
    parts.append("</g>")


def render_main_table(
    parts: list[str],
    data: dict[str, Any],
    x: int,
    y: int,
    header_h: int,
    row_heights: list[int],
    density: DensityProfile,
) -> None:
    parts.append(f'<g id="fmea-main-table" class="fmea-main-table">')
    parts.append(f'<rect x="{x}" y="{y}" width="{TABLE_W}" height="{header_h + sum(row_heights)}" fill="#FFFFFF" stroke="{GRID}" stroke-width="1.4"/>')
    parts.append(f'<rect x="{x}" y="{y}" width="{TABLE_W}" height="{header_h}" fill="{HEADER_FILL}"/>')
    cursor_x = x
    for column in COLUMNS:
        header = header_label(column, data["language"])
        render_wrapped_text(parts, header, cursor_x + 8, y + 24, column.width - 16, 12, "#FFFFFF", "700", max_lines=2, align="center" if column.align == "center" else "left")
        cursor_x += column.width

    cursor_y = y + header_h
    for index, row in enumerate(data["rows"]):
        row_h = row_heights[index]
        fill = ROW_ALT if index % 2 else "#FFFFFF"
        parts.append(f'<rect x="{x}" y="{cursor_y}" width="{TABLE_W}" height="{row_h}" fill="{fill}"/>')
        render_table_row(parts, row, x, cursor_y, row_h, density)
        cursor_y += row_h
    render_table_grid(parts, x, y, header_h, row_heights)
    parts.append("</g>")


def render_table_grid(parts: list[str], x: int, y: int, header_h: int, row_heights: list[int]) -> None:
    table_h = header_h + sum(row_heights)
    cursor_x = x
    for column in COLUMNS:
        parts.append(f'<line class="fmea-grid-line" x1="{cursor_x}" y1="{y}" x2="{cursor_x}" y2="{y + table_h}" stroke="{GRID_STRONG}" stroke-width="1.15"/>')
        cursor_x += column.width
    parts.append(f'<line class="fmea-grid-line" x1="{x + TABLE_W}" y1="{y}" x2="{x + TABLE_W}" y2="{y + table_h}" stroke="{GRID_STRONG}" stroke-width="1.15"/>')
    parts.append(f'<line class="fmea-grid-line" x1="{x}" y1="{y}" x2="{x + TABLE_W}" y2="{y}" stroke="{GRID_STRONG}" stroke-width="1.25"/>')
    parts.append(f'<line class="fmea-grid-line" x1="{x}" y1="{y + header_h}" x2="{x + TABLE_W}" y2="{y + header_h}" stroke="{GRID_STRONG}" stroke-width="1.25"/>')
    cursor_y = y + header_h
    for row_h in row_heights:
        cursor_y += row_h
        parts.append(f'<line class="fmea-grid-line" x1="{x}" y1="{cursor_y}" x2="{x + TABLE_W}" y2="{cursor_y}" stroke="{GRID_STRONG}" stroke-width="1.15"/>')


def header_label(column: Column, language: str) -> str:
    if language == "zh":
        return HEADER_ZH.get(column.key, column.label)
    if language == "bilingual" and column.key in HEADER_ZH:
        return f"{column.label} / {HEADER_ZH[column.key]}"
    return column.label


def render_table_row(parts: list[str], row: dict[str, Any], x: int, y: int, h: int, density: DensityProfile) -> None:
    cursor_x = x
    for column in COLUMNS:
        content = row.get(column.key)
        cell_x = cursor_x
        cell_w = column.width
        if column.key == "rpn":
            render_rpn_cell(parts, row, cell_x, y, cell_w, h)
        elif column.key == "item_function":
            render_item_cell(parts, row, cell_x, y, cell_w, h, density)
        elif column.key == "status":
            render_status_cell(parts, collapse(content), cell_x, y, cell_w, h, density)
        elif column.key in {"severity", "occurrence", "detection"}:
            render_score_cell(parts, content, cell_x, y, cell_w, h)
        elif column.key in {"owner", "target_completion"}:
            render_owner_target_cell(parts, collapse(content), cell_x, y, cell_w, h)
        elif column.align == "center":
            value = "" if content is None else str(content)
            parts.append(f'<text x="{cell_x + cell_w / 2:.1f}" y="{y + h / 2 + 5:.1f}" font-size="15" font-weight="700" text-anchor="middle">{esc(value)}</text>')
        else:
            lines = content_lines(content)
            block_h = measure_bulleted_block_height(lines, cell_w - 20, density)
            start_y = centered_baseline_start(y, h, block_h, density.text_font)
            render_bulleted_cell(parts, lines, cell_x + 10, start_y, cell_w - 20, y + h - 8, density)
        cursor_x += cell_w


def render_item_cell(parts: list[str], row: dict[str, Any], x: int, y: int, w: int, h: int, density: DensityProfile) -> None:
    icon = row["icon"] or icon_for_text(row["item_function"])
    color = icon_color(icon)
    lines = wrap_text(row["item_function"], chars_for_width(w - 34, density.item_font), max_lines=4)
    block_h = measure_item_block_height(lines, density)
    block_top = y + max(8, (h - block_h) / 2)
    stripe_h = max(34, min(70, block_h + 2))
    parts.append(f'<rect x="{x + 10}" y="{block_top - 2:.1f}" width="4" height="{stripe_h:.1f}" rx="2" fill="{color}"/>')
    parts.append(f'<text x="{x + 24}" y="{block_top + 12:.1f}" font-size="12" fill="{MUTED}" font-weight="700">{esc(row["id"])}</text>')
    for index, line in enumerate(lines):
        parts.append(f'<text x="{x + 24}" y="{block_top + 34 + index * density.line_h:.1f}" font-size="{density.item_font:g}" fill="{TEXT}" font-weight="700">{esc(line)}</text>')


def render_score_cell(parts: list[str], value: Any, x: int, y: int, w: int, h: int) -> None:
    parsed = parse_int(value, None)
    text = "" if value is None else str(value)
    color = score_color(parsed)
    parts.append(f'<text class="fmea-score-cell" data-score="{esc(text)}" x="{x + w / 2:.1f}" y="{y + h / 2 + 6:.1f}" font-size="16" font-weight="700" text-anchor="middle" fill="{color}">{esc(text)}</text>')


def render_rpn_cell(parts: list[str], row: dict[str, Any], x: int, y: int, w: int, h: int) -> None:
    value = "" if row["rpn"] is None else str(row["rpn"])
    level = row["risk_level"]
    fill, stroke = risk_colors(level)
    parts.append(f'<rect class="fmea-risk-cell" data-risk-level="{esc(level)}" data-rpn="{esc(value)}" x="{x}" y="{y}" width="{w}" height="{h}" fill="{fill}" opacity="0.82"/>')
    parts.append(f'<text x="{x + w / 2:.1f}" y="{y + h / 2 + 6:.1f}" font-size="16" font-weight="700" text-anchor="middle" fill="{stroke}">{esc(value)}</text>')


def render_owner_target_cell(parts: list[str], value: str, x: int, y: int, w: int, h: int) -> None:
    lines = compact_cell_lines(value, chars_for_width(w - 14, 12.5), max_lines=2)
    line_gap = 16
    start_y = y + h / 2 - ((len(lines) - 1) * line_gap) / 2 + 4
    for index, line in enumerate(lines):
        parts.append(f'<text x="{x + w / 2:.1f}" y="{start_y + index * line_gap:.1f}" font-size="12.5" font-weight="500" fill="{TEXT}" text-anchor="middle">{esc(line)}</text>')


def render_status_cell(parts: list[str], status: str, x: int, y: int, w: int, h: int, density: DensityProfile) -> None:
    normalized = status.lower()
    if "closed" in normalized or "done" in normalized or "complete" in normalized:
        glyph, color = "check", LOW_STROKE
        label = "Completed"
    elif "progress" in normalized or "working" in normalized:
        glyph, color = "progress", MED_STROKE
        label = status or "In Progress"
    elif "high" in normalized and "risk" in normalized:
        glyph, color = "alert", HIGH_STROKE
        label = status
    elif "delay" in normalized or "late" in normalized or "risk" in normalized:
        glyph, color = "alert", HIGH_STROKE
        label = status
    elif "planned" in normalized or "plan" in normalized:
        glyph, color = "calendar", "#2B6CBF"
        label = status or "Planned"
    else:
        glyph, color = "calendar", "#2B6CBF"
        label = status or "Open"
    cx = x + w / 2
    label_lines = wrap_text(label, chars_for_width(w - 20, 11.5), max_lines=2)
    block_h = 26 + 14 + len(label_lines) * 13
    cy = y + (h - block_h) / 2 + 13
    parts.append(f'<g class="fmea-status-badge" data-status="{esc(status or "Open")}">')
    render_status_symbol(parts, glyph, cx, cy, color)
    render_wrapped_text(parts, label, x + 10, cy + 30, w - 20, 11.5, TEXT, "700", max_lines=2, align="center")
    parts.append("</g>")


def render_status_symbol(parts: list[str], glyph: str, cx: float, cy: float, color: str) -> None:
    parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="13" fill="{color}"/>')
    if glyph == "check":
        parts.append(f'<path d="M {cx - 6:.1f} {cy:.1f} L {cx - 1.5:.1f} {cy + 5:.1f} L {cx + 7:.1f} {cy - 6:.1f}" fill="none" stroke="#FFFFFF" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>')
    elif glyph == "progress":
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="6.5" fill="none" stroke="#FFFFFF" stroke-width="2.5" stroke-dasharray="24 16" stroke-linecap="round"/>')
        parts.append(f'<circle cx="{cx + 5:.1f}" cy="{cy - 5:.1f}" r="2.5" fill="#FFFFFF"/>')
    elif glyph == "alert":
        points = f"{cx:.1f},{cy - 8:.1f} {cx - 8:.1f},{cy + 7:.1f} {cx + 8:.1f},{cy + 7:.1f}"
        parts.append(f'<polygon points="{points}" fill="none" stroke="#FFFFFF" stroke-width="2.4" stroke-linejoin="round"/>')
        parts.append(f'<line x1="{cx:.1f}" y1="{cy - 2:.1f}" x2="{cx:.1f}" y2="{cy + 3:.1f}" stroke="#FFFFFF" stroke-width="2.2" stroke-linecap="round"/>')
        parts.append(f'<circle cx="{cx:.1f}" cy="{cy + 6:.1f}" r="1.4" fill="#FFFFFF"/>')
    else:
        parts.append(f'<rect x="{cx - 6:.1f}" y="{cy - 5:.1f}" width="12" height="11" rx="2" fill="none" stroke="#FFFFFF" stroke-width="2"/>')
        parts.append(f'<line x1="{cx - 6:.1f}" y1="{cy - 1:.1f}" x2="{cx + 6:.1f}" y2="{cy - 1:.1f}" stroke="#FFFFFF" stroke-width="2"/>')
        parts.append(f'<line x1="{cx - 3:.1f}" y1="{cy - 8:.1f}" x2="{cx - 3:.1f}" y2="{cy - 4:.1f}" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/>')
        parts.append(f'<line x1="{cx + 3:.1f}" y1="{cy - 8:.1f}" x2="{cx + 3:.1f}" y2="{cy - 4:.1f}" stroke="#FFFFFF" stroke-width="2" stroke-linecap="round"/>')


def score_color(value: int | None) -> str:
    if value is None:
        return MUTED
    if value >= 7:
        return SCORE_HIGH
    if value >= 4:
        return SCORE_MED
    return SCORE_LOW


def risk_colors(level: str) -> tuple[str, str]:
    if level == "high":
        return HIGH_FILL, HIGH_STROKE
    if level == "medium":
        return MED_FILL, MED_STROKE
    if level == "low":
        return LOW_FILL, LOW_STROKE
    return "#EEF2F6", "#7A8797"


def icon_color(icon: str) -> str:
    return ICON_COLORS.get(icon, "#245C9A")


def content_lines(value: Any) -> list[str]:
    if isinstance(value, list):
        return [collapse(item) for item in value if collapse(item)]
    text = collapse(value)
    return [text] if text else []


def render_bulleted_cell(
    parts: list[str],
    lines: list[str],
    x: float,
    y: float,
    w: float,
    bottom_y: float,
    density: DensityProfile,
) -> None:
    cursor_y = y
    for item_index, item in enumerate(lines):
        wrapped = wrap_text(item, chars_for_width(w - 12, density.text_font), max_lines=3)
        for line_index, line in enumerate(wrapped):
            if cursor_y > bottom_y:
                return
            if line_index == 0 and len(lines) > 1:
                parts.append(f'<circle cx="{x + 3}" cy="{cursor_y - 4}" r="2.4" fill="{NAVY}"/>')
                text_x = x + 12
            else:
                text_x = x + (12 if len(lines) > 1 else 0)
            parts.append(f'<text x="{text_x:.1f}" y="{cursor_y:.1f}" font-size="{density.text_font:g}" fill="{TEXT}">{esc(line)}</text>')
            cursor_y += density.line_h
        if item_index < len(lines) - 1:
            cursor_y += 2


def render_bottom_panels(parts: list[str], data: dict[str, Any], y: int, h: int) -> None:
    label = labels(data["language"])
    thresholds = data["thresholds"]
    render_priority_guide(parts, 24, y, 642, h, label, thresholds)
    notes = data["notes"] or ["Keep row wording concise; update S/O/D after corrective actions are verified."]
    render_panel(parts, 690, y, 722, h, label["notes"], notes[:4])
    project = data["project"]
    review_lines = [
        f"Project: {collapse(project.get('name')) or '-'}",
        f"Owner: {collapse(project.get('owner')) or '-'}",
        f"Review frequency: {collapse(project.get('review_frequency')) or '-'}",
        f"Last review: {collapse(project.get('last_review_date')) or '-'}",
    ]
    render_panel(parts, 1436, y, 456, h, label["review"], review_lines)


def render_priority_guide(
    parts: list[str],
    x: int,
    y: int,
    w: int,
    h: int,
    label: dict[str, str],
    thresholds: dict[str, int],
) -> None:
    parts.append(f'<g id="fmea-priority-guide" class="fmea-panel"><rect x="{x}" y="{y}" width="{w}" height="{h}" rx="10" fill="{PANEL_FILL}" stroke="#8DA9CC" stroke-width="1.5"/>')
    parts.append(f'<text x="{x + 18}" y="{y + 30}" font-size="18" font-weight="700">{esc(label["priority"])}</text>')
    parts.append(f'<text x="{x + 18}" y="{y + 54}" font-size="12.5" font-weight="700" fill="{TEXT}">RPN = S x O x D; RPN cell color shows risk level.</text>')
    guide_rows = [
        (HIGH_FILL, HIGH_STROKE, f"RPN >= {thresholds['high']}", f"{label['high']} Risk", "Immediate action required"),
        (MED_FILL, MED_STROKE, f"{thresholds['medium']} <= RPN < {thresholds['high']}", f"{label['medium']} Risk", "Plan and track actions"),
        (LOW_FILL, LOW_STROKE, f"RPN < {thresholds['medium']}", f"{label['low']} Risk", "Monitor and maintain"),
    ]
    col_w = (w - 36) / 3
    for index, (fill, stroke, range_text, risk_text, action_text) in enumerate(guide_rows):
        card_x = x + 18 + index * col_w
        parts.append(f'<rect x="{card_x:.1f}" y="{y + 68}" width="{col_w - 14:.1f}" height="42" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="1.1"/>')
        parts.append(f'<text x="{card_x + 10:.1f}" y="{y + 86}" font-size="12.5" font-weight="700" fill="{stroke}">{esc(range_text)}</text>')
        parts.append(f'<text x="{card_x + 10:.1f}" y="{y + 103}" font-size="12" font-weight="700" fill="{TEXT}">{esc(risk_text)}</text>')
        parts.append(f'<text x="{card_x + 10:.1f}" y="{y + 124}" font-size="11.5" fill="{MUTED}">{esc(action_text)}</text>')
    parts.append("</g>")


def labels(language: str) -> dict[str, str]:
    return LABELS["zh"] if language == "zh" else LABELS["en"]


def density_for_rows(row_count: int) -> DensityProfile:
    if row_count > 10:
        return DENSITY_PROFILES["dense"]
    if row_count > 5:
        return DENSITY_PROFILES["compact"]
    return DENSITY_PROFILES["normal"]


def measure_row_height(row: dict[str, Any], density: DensityProfile) -> int:
    max_block_h = 0.0
    for column in COLUMNS:
        if column.key in {"severity", "occurrence", "detection", "rpn", "status"}:
            block_h = 44
        elif column.key == "item_function":
            lines = wrap_text(row["item_function"], chars_for_width(column.width - 34, density.item_font), max_lines=4)
            block_h = measure_item_block_height(lines, density)
        elif column.key in {"owner", "target_completion"}:
            lines = compact_cell_lines(collapse(row.get(column.key)), chars_for_width(column.width - 14, 12.5), max_lines=2)
            block_h = max(1, len(lines)) * 16
        else:
            block_h = measure_bulleted_block_height(content_lines(row.get(column.key)), column.width - 20, density)
        max_block_h = max(max_block_h, block_h)
    natural_h = math.ceil(max_block_h + density.vertical_padding)
    return min(density.max_row_h, max(density.min_row_h, natural_h))


def measure_item_block_height(lines: list[str], density: DensityProfile) -> float:
    return 39 + max(0, len(lines) - 1) * density.line_h


def measure_bulleted_block_height(lines: list[str], width: float, density: DensityProfile) -> float:
    if not lines:
        return density.line_h
    rendered_lines = 0
    gaps = 0
    for item_index, item in enumerate(lines):
        rendered_lines += len(wrap_text(item, chars_for_width(width - 12, density.text_font), max_lines=3))
        if item_index < len(lines) - 1:
            gaps += 2
    return max(1, rendered_lines) * density.line_h + gaps


def centered_baseline_start(y: float, h: float, block_h: float, font_size: float) -> float:
    return y + max(8, (h - block_h) / 2) + font_size


def render_wrapped_text(
    parts: list[str],
    text: str,
    x: float,
    y: float,
    width: float,
    font_size: float,
    fill: str,
    weight: str,
    max_lines: int = 2,
    align: str = "left",
) -> None:
    lines = wrap_text(text, chars_for_width(width, font_size), max_lines=max_lines)
    anchor = "middle" if align == "center" else "start"
    text_x = x + width / 2 if align == "center" else x
    for index, line in enumerate(lines):
        parts.append(f'<text x="{text_x:.1f}" y="{y + index * (font_size + 4):.1f}" font-size="{font_size:g}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}">{esc(line)}</text>')


def wrap_text(text: str, max_chars: int, max_lines: int | None = None) -> list[str]:
    text = collapse(text)
    if not text:
        return []
    max_chars = max(6, max_chars)
    words = text.split()
    lines: list[str] = []
    current = ""
    for word in words:
        candidate = word if not current else f"{current} {word}"
        if visual_len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = trim_word(word, max_chars)
        if max_lines and len(lines) >= max_lines:
            break
    if current and (not max_lines or len(lines) < max_lines):
        lines.append(current)
    if max_lines and len(lines) == max_lines and words and visual_len(" ".join(words)) > visual_len(" ".join(lines)):
        lines[-1] = ellipsize(lines[-1], max_chars)
    return lines


def compact_cell_lines(text: str, max_chars: int, max_lines: int) -> list[str]:
    text = collapse(text)
    if not text:
        return []
    if "/" in text:
        parts = [part.strip() for part in text.split("/") if part.strip()]
    else:
        parts = text.split()
    if 1 < len(parts) <= max_lines:
        return [ellipsize(part, max_chars) for part in parts]
    return wrap_text(text, max_chars, max_lines=max_lines)


def chars_for_width(width: float, font_size: float = 12.5) -> int:
    return max(4, int(width / (font_size * 0.52)))


def visual_len(text: str) -> int:
    return sum(2 if "\u4e00" <= char <= "\u9fff" else 1 for char in text)


def trim_word(word: str, max_chars: int) -> str:
    if visual_len(word) <= max_chars:
        return word
    result = ""
    for char in word:
        if visual_len(result + char) > max_chars - 3:
            break
        result += char
    return result + "..."


def ellipsize(text: str, max_chars: int) -> str:
    if visual_len(text) <= max_chars:
        return text
    return trim_word(text, max_chars)


def icon_for_text(text: str) -> str:
    lower = text.lower()
    for keyword, icon in ICON_KEYWORDS:
        if keyword in lower:
            return icon
    return "component"


def render_lucide(parts: list[str], icon: str, x: float, y: float, size: int, color: str) -> None:
    safe_icon = re.sub(r"[^a-z0-9-]", "", icon.lower())
    path = LUCIDE_CANDIDATES / f"{safe_icon}.svg"
    if not path.exists():
        path = LUCIDE_CANDIDATES / "component.svg"
    try:
        raw = path.read_text(encoding="utf-8")
        inner = re.sub(r"^.*?<svg[^>]*>|</svg>\s*$", "", raw, flags=re.S)
        inner = inner.replace('stroke="currentColor"', f'stroke="{color}"')
        parts.append(f'<g transform="translate({x:.1f} {y:.1f}) scale({size / 24:.4f})">{inner}</g>')
    except OSError:
        parts.append(f'<circle cx="{x + size / 2:.1f}" cy="{y + size / 2:.1f}" r="{size / 3:.1f}" fill="{color}"/>')


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)
