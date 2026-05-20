"""Business-simple two-by-two matrix SVG renderer."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[2]
LUCIDE_ICON_DIR = ROOT / "assets" / "lucide-candidates"
WIDTH = 1920
HEIGHT = 1080
FONT_STACK = "Arial"

MAX_ITEMS_IN_QUADRANT = 5
MAX_ITEMS = 20
DEFAULT_SCALE_MIN = 1.0
DEFAULT_SCALE_MAX = 5.0
NOTES_MAX_LINES = 2
NOTES_LINE_VISUAL_CHARS = 48

MATRIX_X = 84
MATRIX_Y = 158
MATRIX_W = 960
MATRIX_H = 690
AXIS_LEFT = MATRIX_X + 70
AXIS_BOTTOM = MATRIX_Y + MATRIX_H - 42
GRID_X = AXIS_LEFT + 20
GRID_Y = MATRIX_Y + 16
GRID_W = MATRIX_W - 88
GRID_H = MATRIX_H - 84
QUAD_GAP = 18

TABLE_X = 1086
TABLE_Y = 158
TABLE_W = 770
TABLE_H = 840
LEGEND_X = 84
LEGEND_Y = 910
LEGEND_W = 960
LEGEND_H = 88

PALETTE = {
    "background": "#FFFFFF",
    "soft": "#F7FAFD",
    "navy": "#0B2E63",
    "navy_2": "#0B3A75",
    "blue": "#2F6FB6",
    "gray_text": "#5B677A",
    "line": "#CBD5E1",
    "border": "#9AA9BD",
    "green": "#2E8B57",
    "green_bg": "#EAF7F0",
    "green_border": "#B9DCC7",
    "blue_marker": "#2F6CCF",
    "blue_bg": "#EAF3FF",
    "blue_border": "#BCD5F6",
    "amber": "#D99A12",
    "amber_bg": "#FFF6E3",
    "amber_border": "#F1D7A5",
    "red": "#C94040",
    "red_bg": "#FFF0F0",
    "red_border": "#F0B8B8",
}


QUADRANT_ORDER = ["top_left", "top_right", "bottom_left", "bottom_right"]
QUADRANT_SHORT = {
    "top_left": "Q1",
    "top_right": "Q2",
    "bottom_left": "Q3",
    "bottom_right": "Q4",
}
QUADRANT_STYLE = {
    "top_left": ("green", "green_bg", "green_border"),
    "top_right": ("blue_marker", "blue_bg", "blue_border"),
    "bottom_left": ("amber", "amber_bg", "amber_border"),
    "bottom_right": ("red", "red_bg", "red_border"),
}

PRESET_ICON_MAP = {
    "action_priority": {
        "top_left": "star",
        "top_right": "target",
        "bottom_left": "lightbulb",
        "bottom_right": "triangle-alert",
    },
    "risk_benefit": {
        "top_left": "badge-check",
        "top_right": "target",
        "bottom_left": "circle-check",
        "bottom_right": "triangle-alert",
    },
    "evidence_impact": {
        "top_left": "circle-help",
        "top_right": "target",
        "bottom_left": "circle-pause",
        "bottom_right": "circle-alert",
    },
    "value_feasibility": {
        "top_left": "rocket",
        "top_right": "badge-check",
        "bottom_left": "circle-pause",
        "bottom_right": "sparkles",
    },
    "urgency_importance": {
        "top_left": "calendar",
        "top_right": "badge-alert",
        "bottom_left": "trash-2",
        "bottom_right": "users",
    },
    "custom": {
        "top_left": "circle-check",
        "top_right": "target",
        "bottom_left": "circle-pause",
        "bottom_right": "circle-alert",
    },
}


PRESETS: dict[str, dict[str, Any]] = {
    "action_priority": {
        "title": {"en": "Action Priority Matrix", "zh": "行动优先级矩阵"},
        "subtitle": {"en": "Prioritize improvement actions by impact and effort", "zh": "按影响力和执行难度排列行动优先级"},
        "x_axis": {"en": "Effort", "zh": "执行难度"},
        "x_low": {"en": "Low Effort", "zh": "低难度"},
        "x_high": {"en": "High Effort", "zh": "高难度"},
        "y_axis": {"en": "Impact", "zh": "影响力"},
        "y_low": {"en": "Low Impact", "zh": "低影响"},
        "y_high": {"en": "High Impact", "zh": "高影响"},
        "quadrants": {
            "top_left": {"label": {"en": "Quick Wins", "zh": "快速获胜"}, "description": {"en": "High Impact / Low Effort", "zh": "高影响 / 低难度"}, "action": {"en": "Do first", "zh": "优先执行"}, "priority": "P1"},
            "top_right": {"label": {"en": "Major Projects", "zh": "重点项目"}, "description": {"en": "High Impact / High Effort", "zh": "高影响 / 高难度"}, "action": {"en": "Plan and phase", "zh": "计划分阶段推进"}, "priority": "P2"},
            "bottom_left": {"label": {"en": "Fill-ins", "zh": "可选机会"}, "description": {"en": "Low Impact / Low Effort", "zh": "低影响 / 低难度"}, "action": {"en": "Do when possible", "zh": "有余力时执行"}, "priority": "P3"},
            "bottom_right": {"label": {"en": "Time Sinks", "zh": "低效投入"}, "description": {"en": "Low Impact / High Effort", "zh": "低影响 / 高难度"}, "action": {"en": "Defer or drop", "zh": "延后或放弃"}, "priority": "P4"},
        },
        "table_item": {"en": "Action Item", "zh": "行动项"},
        "x_column": {"en": "Effort", "zh": "难度"},
        "y_column": {"en": "Impact", "zh": "影响"},
        "action_column": {"en": "Recommended Action", "zh": "建议行动"},
        "note": {"en": "Best for prioritizing improvement actions, project tasks, and workshop outputs.", "zh": "适合改进行动、项目任务和研讨会输出的优先级排序。"},
    },
    "risk_benefit": {
        "title": {"en": "Risk-Benefit Matrix", "zh": "风险收益矩阵"},
        "subtitle": {"en": "Compare options by expected benefit and risk", "zh": "按预期收益和风险比较方案"},
        "x_axis": {"en": "Risk", "zh": "风险"},
        "x_low": {"en": "Low Risk", "zh": "低风险"},
        "x_high": {"en": "High Risk", "zh": "高风险"},
        "y_axis": {"en": "Benefit", "zh": "收益"},
        "y_low": {"en": "Low Benefit", "zh": "低收益"},
        "y_high": {"en": "High Benefit", "zh": "高收益"},
        "quadrants": {
            "top_left": {"label": {"en": "Attractive", "zh": "优先推进"}, "description": {"en": "High Benefit / Low Risk", "zh": "高收益 / 低风险"}, "action": {"en": "Proceed", "zh": "推进"}, "priority": "Go"},
            "top_right": {"label": {"en": "Strategic Bet", "zh": "战略押注"}, "description": {"en": "High Benefit / High Risk", "zh": "高收益 / 高风险"}, "action": {"en": "Mitigate and review", "zh": "缓释风险后评审"}, "priority": "Review"},
            "bottom_left": {"label": {"en": "Safe but Limited", "zh": "安全但有限"}, "description": {"en": "Low Benefit / Low Risk", "zh": "低收益 / 低风险"}, "action": {"en": "Low priority", "zh": "低优先级"}, "priority": "Low"},
            "bottom_right": {"label": {"en": "Avoid", "zh": "避免"}, "description": {"en": "Low Benefit / High Risk", "zh": "低收益 / 高风险"}, "action": {"en": "Avoid", "zh": "避免"}, "priority": "Avoid"},
        },
        "table_item": {"en": "Option", "zh": "方案"},
        "x_column": {"en": "Risk", "zh": "风险"},
        "y_column": {"en": "Benefit", "zh": "收益"},
        "action_column": {"en": "Decision", "zh": "决策"},
        "note": {"en": "Best for project selection, strategy decisions, and change initiatives.", "zh": "适合项目选择、策略决策和变更方案比较。"},
    },
    "evidence_impact": {
        "title": {"en": "Evidence-Impact Matrix", "zh": "证据影响矩阵"},
        "subtitle": {"en": "Screen possible causes by evidence strength and impact", "zh": "按证据强度和影响筛选可能原因"},
        "x_axis": {"en": "Evidence", "zh": "证据强度"},
        "x_low": {"en": "Weak Evidence", "zh": "证据弱"},
        "x_high": {"en": "Strong Evidence", "zh": "证据强"},
        "y_axis": {"en": "Impact", "zh": "影响程度"},
        "y_low": {"en": "Low Impact", "zh": "低影响"},
        "y_high": {"en": "High Impact", "zh": "高影响"},
        "quadrants": {
            "top_left": {"label": {"en": "Critical Hypotheses", "zh": "关键假设"}, "description": {"en": "High Impact / Weak Evidence", "zh": "高影响 / 证据弱"}, "action": {"en": "Get data", "zh": "补充数据"}, "priority": "Data"},
            "top_right": {"label": {"en": "Priority Causes", "zh": "优先原因"}, "description": {"en": "High Impact / Strong Evidence", "zh": "高影响 / 证据强"}, "action": {"en": "Verify first", "zh": "优先验证"}, "priority": "Verify"},
            "bottom_left": {"label": {"en": "Low Priority", "zh": "低优先级"}, "description": {"en": "Low Impact / Weak Evidence", "zh": "低影响 / 证据弱"}, "action": {"en": "Defer or exclude", "zh": "延后或排除"}, "priority": "Defer"},
            "bottom_right": {"label": {"en": "Known Minor Causes", "zh": "已知次要原因"}, "description": {"en": "Low Impact / Strong Evidence", "zh": "低影响 / 证据强"}, "action": {"en": "Monitor", "zh": "监控"}, "priority": "Monitor"},
        },
        "table_item": {"en": "Possible Cause", "zh": "可能原因"},
        "x_column": {"en": "Evidence", "zh": "证据"},
        "y_column": {"en": "Impact", "zh": "影响"},
        "action_column": {"en": "Next Action", "zh": "下一步"},
        "note": {"en": "Best for root-cause screening and failure-analysis investigation.", "zh": "适合根因筛选和失效分析调查。"},
    },
    "value_feasibility": {
        "title": {"en": "Value-Feasibility Matrix", "zh": "价值可行性矩阵"},
        "subtitle": {"en": "Screen product features by customer value and technical feasibility", "zh": "按客户价值和技术可行性筛选功能"},
        "x_axis": {"en": "Technical Feasibility", "zh": "技术可行性"},
        "x_low": {"en": "Low Feasibility", "zh": "低可行性"},
        "x_high": {"en": "High Feasibility", "zh": "高可行性"},
        "y_axis": {"en": "Customer Value", "zh": "客户价值"},
        "y_low": {"en": "Low Value", "zh": "低价值"},
        "y_high": {"en": "High Value", "zh": "高价值"},
        "quadrants": {
            "top_left": {"label": {"en": "Explore", "zh": "探索"}, "description": {"en": "High Value / Low Feasibility", "zh": "高价值 / 低可行性"}, "action": {"en": "Prototype", "zh": "原型验证"}, "priority": "Explore"},
            "top_right": {"label": {"en": "Build Now", "zh": "优先开发"}, "description": {"en": "High Value / High Feasibility", "zh": "高价值 / 高可行性"}, "action": {"en": "Build", "zh": "开发"}, "priority": "Build"},
            "bottom_left": {"label": {"en": "Avoid", "zh": "不建议"}, "description": {"en": "Low Value / Low Feasibility", "zh": "低价值 / 低可行性"}, "action": {"en": "Drop", "zh": "放弃"}, "priority": "Drop"},
            "bottom_right": {"label": {"en": "Nice to Have", "zh": "可选功能"}, "description": {"en": "Low Value / High Feasibility", "zh": "低价值 / 高可行性"}, "action": {"en": "Backlog", "zh": "进入待办"}, "priority": "Backlog"},
        },
        "table_item": {"en": "Feature", "zh": "功能"},
        "x_column": {"en": "Feasibility", "zh": "可行性"},
        "y_column": {"en": "Value", "zh": "价值"},
        "action_column": {"en": "Product Decision", "zh": "产品决策"},
        "note": {"en": "Best for feature prioritization, concept evaluation, and roadmap planning.", "zh": "适合功能优先级、概念评估和路线图规划。"},
    },
    "urgency_importance": {
        "title": {"en": "Urgency-Importance Matrix", "zh": "紧急重要矩阵"},
        "subtitle": {"en": "Organize tasks by urgency and importance", "zh": "按紧急性和重要性组织任务"},
        "x_axis": {"en": "Urgency", "zh": "紧急性"},
        "x_low": {"en": "Not Urgent", "zh": "不紧急"},
        "x_high": {"en": "Urgent", "zh": "紧急"},
        "y_axis": {"en": "Importance", "zh": "重要性"},
        "y_low": {"en": "Low Importance", "zh": "低重要性"},
        "y_high": {"en": "High Importance", "zh": "高重要性"},
        "quadrants": {
            "top_left": {"label": {"en": "Schedule", "zh": "计划安排"}, "description": {"en": "Important / Not Urgent", "zh": "重要 / 不紧急"}, "action": {"en": "Schedule", "zh": "安排时间"}, "priority": "Schedule"},
            "top_right": {"label": {"en": "Do Now", "zh": "立即处理"}, "description": {"en": "Important / Urgent", "zh": "重要 / 紧急"}, "action": {"en": "Do now", "zh": "立即处理"}, "priority": "Now"},
            "bottom_left": {"label": {"en": "Eliminate", "zh": "删除"}, "description": {"en": "Less Important / Not Urgent", "zh": "不重要 / 不紧急"}, "action": {"en": "Drop", "zh": "删除"}, "priority": "Drop"},
            "bottom_right": {"label": {"en": "Delegate", "zh": "委派"}, "description": {"en": "Less Important / Urgent", "zh": "不重要 / 紧急"}, "action": {"en": "Delegate", "zh": "委派"}, "priority": "Delegate"},
        },
        "table_item": {"en": "Task", "zh": "任务"},
        "x_column": {"en": "Urgency", "zh": "紧急"},
        "y_column": {"en": "Importance", "zh": "重要"},
        "action_column": {"en": "Action", "zh": "行动"},
        "note": {"en": "Best for task management, issue triage, and time-priority decisions.", "zh": "适合任务管理、问题分流和时间优先级决策。"},
    },
}


@dataclass
class MatrixItem:
    id: str
    name: str
    x_score: float | None
    y_score: float | None
    quadrant: str
    notes: str
    extra: dict[str, str]


def render_two_by_two_matrix_to_file(data: dict[str, Any], output_path: Path) -> dict[str, Any]:
    normalized = normalize_input(data)
    svg = render_two_by_two_matrix(normalized)
    validate_svg(svg)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    return {
        "path": str(output_path),
        "format": "svg",
        "diagram_type": "two_by_two_matrix",
        "theme": normalized["theme"],
        "diagnostics": normalized["diagnostics"],
    }


def normalize_input(data: dict[str, Any]) -> dict[str, Any]:
    diagram_type = canonical_diagram_type(data.get("diagram_type", "two_by_two_matrix"))
    if diagram_type != "two_by_two_matrix":
        raise ValueError('Two-by-two renderer requires diagram_type="two_by_two_matrix".')

    output = clean_text(data.get("output", "svg")).lower() or "svg"
    if output != "svg":
        raise ValueError("The two_by_two_matrix renderer outputs SVG only.")

    diagnostics = list(data.get("_diagnostics", [])) if isinstance(data.get("_diagnostics"), list) else []
    preset_name = normalize_preset(data.get("preset", ""), data)
    preset = build_custom_preset(data) if preset_name == "custom" else PRESETS[preset_name]

    raw_items = data.get("items", [])
    if not isinstance(raw_items, list) or not raw_items:
        diagnostics.append("No matrix items were provided; default example items were used.")
        raw_items = default_items(preset_name)
    if len(raw_items) > MAX_ITEMS:
        raise ValueError(f"Two-by-two matrix supports up to {MAX_ITEMS} items; received {len(raw_items)}.")

    scale = normalize_scale(data.get("score_scale", {}), diagnostics)
    language = normalize_language(data.get("language", "auto"), data, raw_items)
    title = clean_text(data.get("title", "")) or localized(preset["title"], language)
    subtitle = clean_text(data.get("subtitle", ""))
    show_subtitle = as_bool(data.get("show_subtitle", False)) and bool(subtitle)
    notes = fit_visible_notes(clean_text(data.get("notes", data.get("note", ""))), diagnostics)

    items = [
        normalize_item(raw, index + 1, preset, scale, language, diagnostics)
        for index, raw in enumerate(raw_items)
    ]
    for quadrant in QUADRANT_ORDER:
        count = sum(1 for item in items if item.quadrant == quadrant)
        if count > MAX_ITEMS_IN_QUADRANT:
            diagnostics.append(f"{QUADRANT_SHORT[quadrant]} has {count} items; the matrix body shows the first 4 plus an ID summary.")

    return {
        "diagram_type": "two_by_two_matrix",
        "preset": preset_name,
        "preset_config": preset,
        "title": title,
        "subtitle": subtitle if show_subtitle else "",
        "notes": notes,
        "language": language,
        "theme": clean_text(data.get("theme", data.get("style", "business_simple"))) or "business_simple",
        "score_scale": scale,
        "items": items,
        "show_side_table": as_bool(data.get("show_side_table", True)),
        "show_legend": as_bool(data.get("show_legend", True)),
        "show_notes": bool(notes),
        "diagnostics": diagnostics,
    }


def render_two_by_two_matrix(data: dict[str, Any]) -> str:
    parts = [
        svg_header(),
        defs(),
        f'<rect width="{WIDTH}" height="{HEIGHT}" fill="{PALETTE["background"]}"/>',
        render_title(data["title"], data["subtitle"]),
        render_matrix(data),
    ]
    if data["show_side_table"]:
        parts.append(render_side_table(data))
    if data["show_legend"]:
        parts.append(render_legend(data))
    if data["show_notes"]:
        parts.append(render_notes(data))
    parts.append("</svg>")
    return "\n".join(parts)


def render_title(title: str, subtitle: str) -> str:
    chunks = [
        f'<text x="70" y="74" font-family="{FONT_STACK}" font-size="40" font-weight="700" fill="{PALETTE["navy"]}">{escape(title)}</text>',
    ]
    if subtitle:
        chunks.append(f'<text x="72" y="112" font-family="{FONT_STACK}" font-size="21" font-weight="500" fill="{PALETTE["gray_text"]}">{escape(subtitle)}</text>')
    return "\n".join(chunks)


def render_matrix(data: dict[str, Any]) -> str:
    preset = data["preset_config"]
    language = data["language"]
    low_label = localized({"en": "Low", "zh": "低"}, language)
    high_label = localized({"en": "High", "zh": "高"}, language)
    chunks = [
        '<g id="two-by-two-matrix">',
        f'<line x1="{AXIS_LEFT}" y1="{AXIS_BOTTOM}" x2="{AXIS_LEFT + GRID_W + 50}" y2="{AXIS_BOTTOM}" stroke="{PALETTE["navy_2"]}" stroke-width="4" marker-end="url(#arrowNavy)"/>',
        f'<line x1="{AXIS_LEFT}" y1="{AXIS_BOTTOM}" x2="{AXIS_LEFT}" y2="{GRID_Y - 24}" stroke="{PALETTE["navy_2"]}" stroke-width="4" marker-end="url(#arrowNavy)"/>',
        f'<text x="{GRID_X + GRID_W / 2}" y="{AXIS_BOTTOM + 58}" text-anchor="middle" font-family="{FONT_STACK}" font-size="22" font-weight="700" fill="{PALETTE["navy"]}">{escape(localized(preset["x_axis"], language))}</text>',
        f'<text transform="rotate(-90 {AXIS_LEFT - 76} {GRID_Y + GRID_H / 2})" x="{AXIS_LEFT - 76}" y="{GRID_Y + GRID_H / 2}" text-anchor="middle" font-family="{FONT_STACK}" font-size="22" font-weight="700" fill="{PALETTE["navy"]}">{escape(localized(preset["y_axis"], language))}</text>',
        f'<text x="{AXIS_LEFT}" y="{AXIS_BOTTOM + 34}" text-anchor="middle" font-family="{FONT_STACK}" font-size="16" font-weight="700" fill="{PALETTE["navy"]}">{escape(low_label)}</text>',
        f'<text x="{AXIS_LEFT + GRID_W}" y="{AXIS_BOTTOM + 34}" text-anchor="middle" font-family="{FONT_STACK}" font-size="16" font-weight="700" fill="{PALETTE["navy"]}">{escape(high_label)}</text>',
        f'<text x="{AXIS_LEFT - 42}" y="{AXIS_BOTTOM - 4}" text-anchor="middle" font-family="{FONT_STACK}" font-size="16" font-weight="700" fill="{PALETTE["navy"]}">{escape(low_label)}</text>',
        f'<text x="{AXIS_LEFT - 42}" y="{GRID_Y + 20}" text-anchor="middle" font-family="{FONT_STACK}" font-size="16" font-weight="700" fill="{PALETTE["navy"]}">{escape(high_label)}</text>',
    ]
    for quadrant in QUADRANT_ORDER:
        chunks.append(render_quadrant_card(quadrant, data))
    chunks.append("</g>")
    return "\n".join(chunks)


def render_quadrant_card(quadrant: str, data: dict[str, Any]) -> str:
    x, y, w, h = quadrant_rect(quadrant)
    marker_key, bg_key, border_key = QUADRANT_STYLE[quadrant]
    icon = icon_for_quadrant(data["preset"], quadrant)
    preset = data["preset_config"]
    language = data["language"]
    config = preset["quadrants"][quadrant]
    items = [item for item in data["items"] if item.quadrant == quadrant]
    visible_items = items[:4] if len(items) > MAX_ITEMS_IN_QUADRANT else items[:MAX_ITEMS_IN_QUADRANT]
    chunks = [
        f'<g class="matrix-quadrant matrix-{quadrant}" data-quadrant="{quadrant}">',
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="14" fill="{PALETTE[bg_key]}" stroke="{PALETTE[border_key]}" stroke-width="1.6"/>',
        f'<circle cx="{x + 54:.1f}" cy="{y + 54:.1f}" r="28" fill="{PALETTE[marker_key]}"/>',
        render_badge_icon(icon, x + 54, y + 54, color="#FFFFFF", size=28),
        f'<text x="{x + 94:.1f}" y="{y + 49:.1f}" font-family="{FONT_STACK}" font-size="23" font-weight="700" fill="{PALETTE["navy"]}">{escape(localized(config["label"], language))}</text>',
        f'<text x="{x + 94:.1f}" y="{y + 80:.1f}" font-family="{FONT_STACK}" font-size="17" font-weight="700" fill="{PALETTE["gray_text"]}">{escape(localized(config["description"], language))}</text>',
    ]
    item_y = y + 120
    for item in visible_items:
        chunks.extend(render_matrix_item(item, x + 54, item_y, w - 96, PALETTE[marker_key]))
        item_y += 38
    hidden = len(items) - len(visible_items)
    if hidden > 0:
        hidden_items = items[4:]
        hidden_ids = ", ".join(item.id for item in hidden_items)
        summary = f"More: {hidden_ids}" if hidden <= 8 else f"More IDs: {hidden_items[0].id}...{hidden_items[-1].id}"
        chunks.append(f'<text class="matrix-item-summary" x="{x + 48:.1f}" y="{item_y + 8:.1f}" font-family="{FONT_STACK}" font-size="15" font-weight="700" fill="{PALETTE["gray_text"]}">{escape(summary)}</text>')
    chunks.append("</g>")
    return "\n".join(chunks)


def render_matrix_item(item: MatrixItem, cx: float, y: float, text_width: float, color: str) -> list[str]:
    label = item.name
    max_chars = max(14, int(text_width / 8.2))
    lines = wrap_text(label, max_chars, max_lines=1)
    return [
        f'<circle class="matrix-item-marker" cx="{cx:.1f}" cy="{y:.1f}" r="13" fill="{color}"/>',
        f'<text x="{cx:.1f}" y="{y + 5:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="12" font-weight="700" fill="#FFFFFF">{escape(item.id[:3])}</text>',
        f'<text class="matrix-item-label" x="{cx + 25:.1f}" y="{y + 6:.1f}" font-family="{FONT_STACK}" font-size="16" font-weight="700" fill="{PALETTE["navy"]}">{escape(lines[0])}</text>',
    ]


def render_side_table(data: dict[str, Any]) -> str:
    preset = data["preset_config"]
    language = data["language"]
    headers = [
        "ID",
        localized(preset["table_item"], language),
        localized(preset["y_column"], language),
        localized(preset["x_column"], language),
        localized({"en": "Quadrant", "zh": "象限"}, language),
        localized(preset["action_column"], language),
    ]
    widths = [52, 260, 70, 70, 138, 180]
    row_count = len(data["items"])
    header_h = 58
    row_h = min(58, (TABLE_H - header_h) / max(1, row_count))
    table_h = header_h + row_h * max(1, row_count)
    header_font_size = 13
    body_font_size = 13
    table_line_gap = 17
    chunks = [
        '<g id="matrix-side-table">',
        f'<text x="{TABLE_X}" y="{TABLE_Y - 18}" font-family="{FONT_STACK}" font-size="24" font-weight="700" fill="{PALETTE["navy"]}">{escape(localized({"en": "Decision Table", "zh": "决策表"}, language))}</text>',
        f'<rect x="{TABLE_X}" y="{TABLE_Y}" width="{TABLE_W}" height="{table_h:.1f}" rx="10" fill="#FFFFFF" stroke="{PALETTE["border"]}" stroke-width="1.3"/>',
        f'<rect x="{TABLE_X}" y="{TABLE_Y}" width="{TABLE_W}" height="{header_h}" rx="10" fill="{PALETTE["navy"]}"/>',
        f'<rect x="{TABLE_X}" y="{TABLE_Y + 29}" width="{TABLE_W}" height="29" fill="{PALETTE["navy"]}"/>',
    ]
    x_cursor = TABLE_X
    for header, width in zip(headers, widths):
        header_lines = wrap_text(header, max(4, int((width - 12) / 7.4)), max_lines=2)
        header_y = TABLE_Y + 27 - (len(header_lines) - 1) * (table_line_gap / 2)
        for line_index, line in enumerate(header_lines):
            chunks.append(f'<text x="{x_cursor + width / 2:.1f}" y="{header_y + line_index * table_line_gap:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="{header_font_size}" font-weight="700" fill="#FFFFFF">{escape(line)}</text>')
        if x_cursor > TABLE_X:
            chunks.append(f'<line x1="{x_cursor:.1f}" y1="{TABLE_Y}" x2="{x_cursor:.1f}" y2="{TABLE_Y + header_h}" stroke="#D8E2EE" stroke-width="1"/>')
        x_cursor += width
    chunks.append(f'<line x1="{TABLE_X}" y1="{TABLE_Y + header_h}" x2="{TABLE_X + TABLE_W}" y2="{TABLE_Y + header_h}" stroke="#D8E2EE" stroke-width="1"/>')

    for row_index, item in enumerate(data["items"]):
        y = TABLE_Y + header_h + row_index * row_h
        is_alt_row = row_index % 2 == 1
        body_grid = "#C5D3E4" if is_alt_row else "#D8E2EE"
        chunks.append(f'<g class="matrix-table-row" data-item-id="{escape(item.id)}">')
        if is_alt_row:
            chunks.append(f'<rect x="{TABLE_X}" y="{y:.1f}" width="{TABLE_W}" height="{row_h:.1f}" fill="#F8FBFF"/>')
        x_cursor = TABLE_X
        for width in widths[:-1]:
            x_cursor += width
            chunks.append(f'<line class="matrix-table-body-grid" x1="{x_cursor:.1f}" y1="{y:.1f}" x2="{x_cursor:.1f}" y2="{y + row_h:.1f}" stroke="{body_grid}" stroke-width="1"/>')
        row = table_row_values(item, data)
        x_cursor = TABLE_X
        for col_index, (value, width) in enumerate(zip(row, widths)):
            text = wrap_text(value, max(4, int((width - 12) / 7.2)), max_lines=2)
            text_y = y + row_h / 2 - (len(text) - 1) * (table_line_gap / 2) + 5
            color = PALETTE["navy"] if col_index in {0, 1} else PALETTE["gray_text"]
            for line_index, line in enumerate(text):
                chunks.append(f'<text x="{x_cursor + width / 2:.1f}" y="{text_y + line_index * table_line_gap:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="{body_font_size}" font-weight="600" fill="{color}">{escape(line)}</text>')
            x_cursor += width
        chunks.append("</g>")
    for index in range(1, row_count + 1):
        y = TABLE_Y + header_h + index * row_h
        chunks.append(f'<line class="matrix-table-row-separator" x1="{TABLE_X}" y1="{y:.1f}" x2="{TABLE_X + TABLE_W}" y2="{y:.1f}" stroke="#C5D3E4" stroke-width="1"/>')
    chunks.append(f'<rect x="{TABLE_X}" y="{TABLE_Y}" width="{TABLE_W}" height="{table_h:.1f}" rx="10" fill="none" stroke="{PALETTE["border"]}" stroke-width="1.3"/>')
    chunks.append("</g>")
    return "\n".join(chunks)


def table_row_values(item: MatrixItem, data: dict[str, Any]) -> list[str]:
    preset = data["preset_config"]
    language = data["language"]
    quadrant_config = preset["quadrants"][item.quadrant]
    return [
        item.id,
        item.name,
        score_text(item.y_score),
        score_text(item.x_score),
        localized(quadrant_config["label"], language),
        localized(quadrant_config["action"], language),
    ]


def render_legend(data: dict[str, Any]) -> str:
    preset = data["preset_config"]
    language = data["language"]
    chunks = [
        '<g id="matrix-legend">',
        f'<rect x="{LEGEND_X}" y="{LEGEND_Y}" width="{LEGEND_W}" height="{LEGEND_H}" rx="12" fill="{PALETTE["soft"]}" stroke="{PALETTE["border"]}" stroke-width="1.3"/>',
        f'<text x="{LEGEND_X + 24}" y="{LEGEND_Y + 36}" font-family="{FONT_STACK}" font-size="20" font-weight="700" fill="{PALETTE["navy"]}">{escape(localized({"en": "Priority Guide", "zh": "优先级说明"}, language))}</text>',
    ]
    for index, quadrant in enumerate(QUADRANT_ORDER):
        marker_key, _, _ = QUADRANT_STYLE[quadrant]
        icon = icon_for_quadrant(data["preset"], quadrant)
        config = preset["quadrants"][quadrant]
        col = index % 2
        row = index // 2
        x = LEGEND_X + 440 + col * 250
        y = LEGEND_Y + 27 + row * 35
        chunks.append(f'<circle cx="{x}" cy="{y}" r="11" fill="{PALETTE[marker_key]}"/>')
        chunks.append(render_badge_icon(icon, x, y, color="#FFFFFF", size=12))
        chunks.append(f'<text x="{x + 20}" y="{y - 4}" font-family="{FONT_STACK}" font-size="12" font-weight="700" fill="{PALETTE["navy"]}">{escape(localized(config["label"], language))}</text>')
        chunks.append(f'<text x="{x + 20}" y="{y + 14}" font-family="{FONT_STACK}" font-size="11" font-weight="600" fill="{PALETTE["gray_text"]}">{escape(localized(config["action"], language))}</text>')
    chunks.append("</g>")
    return "\n".join(chunks)


def render_notes(data: dict[str, Any]) -> str:
    language = data["language"]
    note = data["notes"]
    note_x = LEGEND_X + 18
    note_y = LEGEND_Y + 44
    note_w = 380
    note_h = 34
    chunks = [
        '<g id="matrix-notes">',
        f'<rect x="{note_x}" y="{note_y}" width="{note_w}" height="{note_h}" rx="8" fill="#FFFFFF" stroke="{PALETTE["blue_border"]}" stroke-width="1.2"/>',
        f'<circle cx="{note_x + 18}" cy="{note_y + 17}" r="10" fill="{PALETTE["blue_bg"]}" stroke="{PALETTE["blue"]}" stroke-width="1.5"/>',
        f'<text x="{note_x + 18}" y="{note_y + 22}" text-anchor="middle" font-family="{FONT_STACK}" font-size="14" font-weight="700" fill="{PALETTE["blue"]}">i</text>',
        f'<text x="{note_x + 36}" y="{note_y + 14}" font-family="{FONT_STACK}" font-size="12" font-weight="700" fill="{PALETTE["navy"]}">{escape(localized({"en": "Notes", "zh": "备注"}, language))}</text>',
    ]
    for line_index, line in enumerate(wrap_text(note, NOTES_LINE_VISUAL_CHARS, max_lines=NOTES_MAX_LINES)):
        chunks.append(f'<text x="{note_x + 82}" y="{note_y + 14 + line_index * 14}" font-family="{FONT_STACK}" font-size="11" font-weight="600" fill="{PALETTE["gray_text"]}">{escape(line)}</text>')
    chunks.append("</g>")
    return "\n".join(chunks)


def quadrant_icon(icon: str, cx: float, cy: float, size: int = 24) -> str:
    return render_badge_icon(icon, cx, cy, color="#FFFFFF", size=size)


def icon_for_quadrant(preset_name: str, quadrant: str) -> str:
    return PRESET_ICON_MAP.get(preset_name, PRESET_ICON_MAP["custom"]).get(quadrant, "circle-dot")


def render_badge_icon(icon: str, cx: float, cy: float, *, color: str, size: int = 24) -> str:
    inner = lucide_inner_svg(icon)
    if not inner:
        inner = lucide_inner_svg("circle-dot")
    scale = size / 24
    x = cx - 12 * scale
    y = cy - 12 * scale
    return (
        f'<g class="lucide-icon lucide-{escape(icon)}" transform="translate({x:.1f} {y:.1f}) scale({scale:.3f})" '
        f'stroke="{color}" fill="none" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">{inner}</g>'
    )


def lucide_inner_svg(name: str) -> str:
    path = LUCIDE_ICON_DIR / f"{name}.svg"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    match = re.search(r"<svg\b[^>]*>(.*)</svg>", text, flags=re.S | re.I)
    if not match:
        return ""
    return match.group(1).replace("currentColor", "inherit")


def quadrant_rect(quadrant: str) -> tuple[float, float, float, float]:
    card_w = (GRID_W - QUAD_GAP) / 2
    card_h = (GRID_H - QUAD_GAP) / 2
    left_x = GRID_X
    right_x = GRID_X + card_w + QUAD_GAP
    top_y = GRID_Y
    bottom_y = GRID_Y + card_h + QUAD_GAP
    if quadrant == "top_left":
        return left_x, top_y, card_w, card_h
    if quadrant == "top_right":
        return right_x, top_y, card_w, card_h
    if quadrant == "bottom_left":
        return left_x, bottom_y, card_w, card_h
    return right_x, bottom_y, card_w, card_h


def normalize_item(
    raw: Any,
    fallback_index: int,
    preset: dict[str, Any],
    scale: tuple[float, float],
    language: str,
    diagnostics: list[str],
) -> MatrixItem:
    if not isinstance(raw, dict):
        raw = {"name": raw}
    item_id = clean_text(raw.get("id", "")) or str(fallback_index)
    name = clean_text(raw.get("name") or raw.get("item") or raw.get("label") or f"Item {fallback_index}")
    x_score = optional_float(first_present(raw, ["x_score", "x", "effort", "risk", "urgency", "feasibility"]))
    y_score = optional_float(first_present(raw, ["y_score", "y", "impact", "benefit", "importance", "value"]))
    minimum, maximum = scale
    if x_score is not None and not (minimum <= x_score <= maximum):
        raise ValueError(f"Item {item_id} x_score must be {score_text(minimum)}-{score_text(maximum)}.")
    if y_score is not None and not (minimum <= y_score <= maximum):
        raise ValueError(f"Item {item_id} y_score must be {score_text(minimum)}-{score_text(maximum)}.")
    quadrant = normalize_quadrant(raw.get("quadrant", ""))
    if not quadrant:
        if x_score is None or y_score is None:
            diagnostics.append(f"Item {item_id} has no complete score or quadrant; bottom_left was used.")
            quadrant = "bottom_left"
        else:
            quadrant = quadrant_for_scores(x_score, y_score, scale)
    notes = clean_text(raw.get("notes", raw.get("note", raw.get("recommendation", ""))))
    extra = {str(key): clean_text(value) for key, value in raw.items() if isinstance(value, str)}
    return MatrixItem(id=item_id, name=name, x_score=x_score, y_score=y_score, quadrant=quadrant, notes=notes, extra=extra)


def first_present(raw: dict[str, Any], keys: list[str]) -> Any:
    for key in keys:
        if key in raw and raw[key] not in (None, ""):
            return raw[key]
    return None


def normalize_scale(raw: Any, diagnostics: list[str]) -> tuple[float, float]:
    if not isinstance(raw, dict):
        return DEFAULT_SCALE_MIN, DEFAULT_SCALE_MAX
    minimum = optional_float(raw.get("min")) or DEFAULT_SCALE_MIN
    maximum = optional_float(raw.get("max")) or DEFAULT_SCALE_MAX
    if maximum <= minimum:
        diagnostics.append("Invalid score_scale; 1-5 was used.")
        return DEFAULT_SCALE_MIN, DEFAULT_SCALE_MAX
    return minimum, maximum


def quadrant_for_scores(x_score: float, y_score: float, scale: tuple[float, float]) -> str:
    minimum, maximum = scale
    midpoint = (minimum + maximum) / 2
    high_x = x_score >= midpoint
    high_y = y_score >= midpoint
    if high_y and not high_x:
        return "top_left"
    if high_y and high_x:
        return "top_right"
    if not high_y and not high_x:
        return "bottom_left"
    return "bottom_right"


def normalize_quadrant(value: Any) -> str:
    text = clean_text(value).lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "q1": "top_left",
        "1": "top_left",
        "top_left": "top_left",
        "high_y_low_x": "top_left",
        "q2": "top_right",
        "2": "top_right",
        "top_right": "top_right",
        "high_y_high_x": "top_right",
        "q3": "bottom_left",
        "3": "bottom_left",
        "bottom_left": "bottom_left",
        "low_y_low_x": "bottom_left",
        "q4": "bottom_right",
        "4": "bottom_right",
        "bottom_right": "bottom_right",
        "low_y_high_x": "bottom_right",
    }
    return aliases.get(text, "")


def normalize_preset(value: Any, data: dict[str, Any]) -> str:
    preset = clean_text(value).lower().replace("-", "_").replace(" ", "_")
    if preset in PRESETS or preset == "custom":
        return preset
    text = " ".join(str(data.get(key, "")) for key in ["title", "subtitle", "prompt", "description"]).lower()
    hints = {
        "action_priority": ["action priority", "quick win", "impact effort", "impact vs effort"],
        "risk_benefit": ["risk benefit", "risk return", "risk reward", "benefit risk"],
        "evidence_impact": ["evidence impact", "root cause", "cause screening", "failure cause"],
        "value_feasibility": ["value feasibility", "customer value", "feature priority", "roadmap"],
        "urgency_importance": ["urgency importance", "eisenhower", "task priority"],
    }
    for name, needles in hints.items():
        if any(needle in text for needle in needles):
            return name
    if any(clean_text(data.get(key, "")) for key in ["x_axis", "y_axis"]):
        return "custom"
    return "action_priority"


def build_custom_preset(data: dict[str, Any]) -> dict[str, Any]:
    x_axis = clean_text(data.get("x_axis", "X Axis")) or "X Axis"
    y_axis = clean_text(data.get("y_axis", "Y Axis")) or "Y Axis"
    raw_quadrants = data.get("quadrants", {})
    if not isinstance(raw_quadrants, dict):
        raw_quadrants = {}
    quadrants = {}
    defaults = {
        "top_left": "High Y / Low X",
        "top_right": "High Y / High X",
        "bottom_left": "Low Y / Low X",
        "bottom_right": "Low Y / High X",
    }
    for key in QUADRANT_ORDER:
        value = raw_quadrants.get(key, defaults[key])
        label = clean_text(value.get("label", "")) if isinstance(value, dict) else clean_text(value)
        quadrants[key] = {
            "label": {"en": label or defaults[key], "zh": label or defaults[key]},
            "description": {"en": defaults[key], "zh": defaults[key]},
            "action": {"en": "Review", "zh": "评审"},
            "priority": "Review",
        }
    return {
        "title": {"en": "Two-by-Two Matrix", "zh": "二维矩阵"},
        "subtitle": {"en": "Classify items by two custom dimensions", "zh": "按两个自定义维度分类条目"},
        "x_axis": {"en": x_axis, "zh": x_axis},
        "x_low": {"en": clean_text(data.get("x_low", "Low")), "zh": clean_text(data.get("x_low", "低"))},
        "x_high": {"en": clean_text(data.get("x_high", "High")), "zh": clean_text(data.get("x_high", "高"))},
        "y_axis": {"en": y_axis, "zh": y_axis},
        "y_low": {"en": clean_text(data.get("y_low", "Low")), "zh": clean_text(data.get("y_low", "低"))},
        "y_high": {"en": clean_text(data.get("y_high", "High")), "zh": clean_text(data.get("y_high", "高"))},
        "quadrants": quadrants,
        "table_item": {"en": "Item", "zh": "条目"},
        "x_column": {"en": x_axis, "zh": x_axis},
        "y_column": {"en": y_axis, "zh": y_axis},
        "action_column": {"en": "Recommendation", "zh": "建议"},
        "note": {"en": "Use custom axes to classify items into four decision zones.", "zh": "使用自定义轴把条目划分到四个决策区域。"},
    }


def normalize_language(value: Any, data: dict[str, Any], raw_items: list[Any]) -> str:
    language = clean_text(value).lower()
    if language in {"en", "english"}:
        return "en"
    if language in {"zh", "cn", "chinese"}:
        return "zh"
    text_parts = [str(data.get(key, "")) for key in ["title", "subtitle", "x_axis", "y_axis"]]
    for item in raw_items:
        if isinstance(item, dict):
            text_parts.extend(str(item.get(key, "")) for key in ["name", "notes", "item", "label"])
        else:
            text_parts.append(str(item))
    return "zh" if contains_cjk(" ".join(text_parts)) else "en"


def default_items(preset_name: str) -> list[dict[str, Any]]:
    return [
        {"id": "A1", "name": "Automate weekly report", "x_score": 2, "y_score": 5},
        {"id": "A2", "name": "Redesign approval workflow", "x_score": 5, "y_score": 5},
        {"id": "A3", "name": "Standardize checklist", "x_score": 1, "y_score": 2},
        {"id": "A4", "name": "Build custom dashboard", "x_score": 5, "y_score": 2},
    ]


def fit_visible_notes(note: str, diagnostics: list[str]) -> str:
    if not note:
        return ""
    lines = wrap_text(note, NOTES_LINE_VISUAL_CHARS)
    if len(lines) <= NOTES_MAX_LINES and all(visual_len(line) <= NOTES_LINE_VISUAL_CHARS for line in lines):
        return note
    visible = lines[:NOTES_MAX_LINES]
    visible[-1] = trim_to_visual_len(visible[-1], NOTES_LINE_VISUAL_CHARS - 3).rstrip() + "..."
    diagnostics.append("Notes exceeded the visible two-line area and were shortened for display.")
    return " ".join(visible)


def parse_two_by_two_matrix_markdown(text: str) -> dict[str, Any]:
    metadata, body = split_markdown_front_matter(text)
    data: dict[str, Any] = {
        "diagram_type": "two_by_two_matrix",
        "preset": metadata.get("preset", ""),
        "language": metadata.get("language", "auto"),
        "show_side_table": as_bool(metadata.get("show_side_table", True)),
        "show_legend": as_bool(metadata.get("show_legend", True)),
        "show_subtitle": as_bool(metadata.get("show_subtitle", False)),
        "notes": metadata.get("notes", metadata.get("note", "")),
        "items": [],
    }
    current_section = ""
    table_lines: list[str] = []
    for raw_line in body.splitlines():
        line = raw_line.strip()
        if not line:
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            heading = line[level:].strip()
            if level == 1:
                data["title"] = heading
            elif level == 2:
                current_section = heading.lower()
            continue
        key_value = parse_key_value(line)
        if key_value:
            key, value = key_value
            key = key.lower().replace(" ", "_").replace("-", "_")
            if key in {"subtitle", "preset", "language", "x_axis", "y_axis", "x_low", "x_high", "y_low", "y_high", "notes", "note"}:
                data[key] = value
            elif key == "show_subtitle":
                data[key] = as_bool(value)
            elif key in {"top_left", "top_right", "bottom_left", "bottom_right"}:
                quadrants = data.setdefault("quadrants", {})
                if isinstance(quadrants, dict):
                    quadrants[key] = value
            continue
        if current_section == "items" and "|" in raw_line:
            table_lines.append(raw_line)
    data["items"] = parse_markdown_items_table(table_lines)
    return data


def parse_markdown_items_table(lines: list[str]) -> list[dict[str, Any]]:
    rows = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not cells:
            continue
        if all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        return []
    headers = [normalize_header(cell) for cell in rows[0]]
    items = []
    for cells in rows[1:]:
        if not any(cells):
            continue
        item: dict[str, Any] = {}
        for header, cell in zip(headers, cells):
            if header in {"id", "name", "notes", "quadrant"}:
                item[header] = cell
            elif header in {"item", "action_item", "option", "feature", "task", "possible_cause"}:
                item["name"] = cell
            elif header in {"x", "x_score", "effort", "risk", "evidence", "feasibility", "urgency"}:
                item["x_score"] = cell
            elif header in {"y", "y_score", "impact", "benefit", "value", "importance"}:
                item["y_score"] = cell
            else:
                item[header] = cell
        items.append(item)
    return items


def split_markdown_front_matter(text: str) -> tuple[dict[str, str], str]:
    clean = text.lstrip("\ufeff")
    lines = clean.splitlines()
    metadata: dict[str, str] = {}
    if lines and lines[0].strip() == "---":
        for index in range(1, len(lines)):
            if lines[index].strip() == "---":
                for raw in lines[1:index]:
                    parsed = parse_key_value(raw)
                    if parsed is not None:
                        metadata[parsed[0].lower().replace("-", "_")] = parsed[1]
                return metadata, "\n".join(lines[index + 1 :])
    return metadata, clean


def parse_key_value(line: str) -> tuple[str, str] | None:
    match = re.match(r"^([A-Za-z_][A-Za-z0-9_ -]*)\s*:\s*(.*?)\s*$", line.strip())
    if not match:
        return None
    return match.group(1).strip(), match.group(2).strip().strip("\"'")


def localized(value: Any, language: str) -> str:
    if isinstance(value, dict):
        return clean_text(value.get(language) or value.get("en") or next(iter(value.values()), ""))
    return clean_text(value)


def score_text(value: float | None) -> str:
    if value is None:
        return "-"
    return str(int(value)) if abs(value - int(value)) < 0.001 else f"{value:.1f}"


def normalize_header(value: str) -> str:
    return clean_text(value).lower().replace(" ", "_").replace("-", "_").replace("/", "_")


def optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def int_value(value: Any, fallback: int) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return fallback


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "no", "off"}
    return bool(value)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def visual_len(text: str) -> int:
    return sum(2 if ord(char) > 127 else 1 for char in text)


def wrap_text(text: str, max_chars: int, max_lines: int | None = None) -> list[str]:
    clean = clean_text(text)
    if not clean:
        return [""]
    has_cjk = contains_cjk(clean)
    words = clean.split()
    lines: list[str] = []
    current = ""
    if has_cjk:
        units = list(clean)
    elif len(words) == 1:
        units = [clean]
    else:
        units = words
    for unit in units:
        sep = "" if has_cjk else " "
        candidate = unit if not current else current + sep + unit
        if visual_len(candidate) <= max_chars:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = unit
    if current:
        lines.append(current)
    if max_lines is not None:
        return lines[:max_lines] or [clean[:max_chars]]
    return lines or [clean]


def trim_to_visual_len(text: str, max_chars: int) -> str:
    clean = clean_text(text)
    output = ""
    length = 0
    for char in clean:
        char_len = 2 if ord(char) > 127 else 1
        if length + char_len > max_chars:
            break
        output += char
        length += char_len
    return output


def svg_header() -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">'


def defs() -> str:
    return """
<defs>
  <marker id="arrowNavy" markerWidth="10" markerHeight="10" refX="8" refY="3" orient="auto" markerUnits="strokeWidth">
    <path d="M0,0 L0,6 L9,3 z" fill="#0B3A75"/>
  </marker>
</defs>
""".strip()


def validate_svg(svg: str) -> None:
    ElementTree.fromstring(svg)


def canonical_diagram_type(value: Any) -> str:
    return clean_text(value).lower().replace("-", "_").replace(" ", "_")
