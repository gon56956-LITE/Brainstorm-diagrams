"""Business-simple exclusion tree SVG renderer."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
from xml.sax.saxutils import escape


WIDTH = 1920
HEIGHT = 1080
FONT_STACK = "Arial, Helvetica, Microsoft YaHei, Noto Sans CJK SC, sans-serif"
ROOT = Path(__file__).resolve().parents[2]
LUCIDE_ICON_DIR = ROOT / "assets" / "lucide-candidates"
LUCIDE_ICON_CACHE: dict[str, str] = {}

MAX_CHECKS = 6
CHECK_GAP_Y = 150
TOP_Y = 72
MAIN_X = 760
FAIL_X = 1190
PASS_X_OFFSET = -285
TREE_LEFT_MARGIN = 60
BOTTOM_MARGIN = 80
DETAIL_X = 48
DETAIL_Y = 46
DETAIL_W = 500
DETAIL_H = 220
LEGEND_H = 462
HOW_TO_USE_W = 620
HOW_TO_USE_H = 286

TOP_W = 300
TOP_H = 96
CHECK_W = 360
CHECK_H = 86
FAIL_W = 420
FAIL_H = 150
FINAL_W = 500
FINAL_H = 160
CAUSE_CARD_BASE_X = 1120
CAUSE_CARD_STEP_X = 150
CAUSE_CARD_MIN_X = 540
CAUSE_CARD_TOP_GAP = 44
CAUSE_CARD_MIN_GAP = 24
CARD_PAD_TOP = 34
CARD_PAD_BOTTOM = 28
CARD_TITLE_GAP = 24
CARD_DETAIL_GAP = 20
CARD_TITLE_LINE_H = 24
CARD_DETAIL_LINE_H = 20
CARD_TEXT_X_OFFSET = 76
CARD_TEXT_RIGHT_PAD = 30
CARD_TITLE_CHAR_PX = 8.2
CARD_DETAIL_CHAR_PX = 6.6
CARD_HEADING_BASELINE_Y = 42
CARD_TITLE_BASELINE_Y = 66
CARD_DETAIL_BASELINE_GAP = 2
CARD_BOTTOM_AFTER_TEXT = 24
DETAIL_TEXT_X_OFFSET = 28
DETAIL_TEXT_RIGHT_PAD = 28
DETAIL_TITLE_BASELINE_Y = 44
DETAIL_RULE_Y = 64
DETAIL_BODY_BASELINE_Y = 96
DETAIL_BODY_LINE_H = 27
DETAIL_BULLET_LINE_H = 24
DETAIL_BOTTOM_AFTER_TEXT = 30
MAIN_PATH_STEP_X = 165
MAIN_PATH_TAIL_STEP_X = 70
CONNECTOR_CLEARANCE = 32
FAIL_LANE_MIN_OFFSET = 36
FAIL_LANE_PREFERRED_OFFSET = 80
FAIL_LANE_MAX_OFFSET = 160
FAIL_ARROW_INSET_Y = 12

PALETTE = {
    "background": "#FFFFFF",
    "navy": "#0B2E63",
    "navy_2": "#0B3A75",
    "blue": "#2F6FB6",
    "light_blue": "#EAF3FF",
    "pale_blue": "#F8FBFF",
    "line_blue": "#6E93BD",
    "gray_text": "#5B677A",
    "gray_line": "#CBD5E1",
    "border_gray": "#9AA9BD",
    "green": "#2E7D32",
    "green_bg": "#EAF6EA",
    "red": "#C62828",
    "red_bg": "#FDECEC",
}

ICON_LUCIDE_MAP = {
    "bolt": "zap",
    "module": "component",
    "chip": "cpu",
    "signal": "chart-no-axes-column-increasing",
    "thermometer": "thermometer",
    "gear": "cog",
    "document": "clipboard-check",
    "material": "boxes",
    "operator": "activity",
    "question": "activity",
}

DEFAULT_CHECKS = [
    {
        "id": "1",
        "text_en": "Power Input OK?",
        "text_zh": "æ˜¯å¦æœ‰ç”µæºè¾“å…¥ï¼Ÿ",
        "icon": "bolt",
        "fail_conclusion": {
            "text_en": "No Power Input",
            "text_zh": "æ— ç”µæºè¾“å…¥",
            "detail_en": "Check power cord, connector, and outlet.",
            "detail_zh": "æ£€æŸ¥ç”µæºçº¿ã€è¿žæŽ¥å™¨å’Œæ’åº§ä¾›ç”µã€‚",
        },
    },
    {
        "id": "2",
        "text_en": "Power Module Output OK?",
        "text_zh": "ç”µæºæ¨¡å—è¾“å‡ºæ˜¯å¦æ­£å¸¸ï¼Ÿ",
        "icon": "module",
        "fail_conclusion": {
            "text_en": "Power Module Fault",
            "text_zh": "ç”µæºæ¨¡å—æ•…éšœ",
        },
    },
    {
        "id": "3",
        "text_en": "Control Board OK?",
        "text_zh": "æŽ§åˆ¶æ¿æ˜¯å¦æ­£å¸¸å·¥ä½œï¼Ÿ",
        "icon": "chip",
        "fail_conclusion": {
            "text_en": "Control Board Fault",
            "text_zh": "æŽ§åˆ¶æ¿æ•…éšœ",
        },
    },
    {
        "id": "4",
        "text_en": "Start Signal OK?",
        "text_zh": "å¯åŠ¨ä¿¡å·æ˜¯å¦æ­£å¸¸ï¼Ÿ",
        "icon": "signal",
        "fail_conclusion": {
            "text_en": "Start Signal Issue",
            "text_zh": "å¯åŠ¨ä¿¡å·å¼‚å¸¸",
        },
    },
]


@dataclass
class Conclusion:
    text_en: str
    text_zh: str
    detail_en: str
    detail_zh: str


@dataclass
class CheckPoint:
    id: str
    text_en: str
    text_zh: str
    icon: str
    pass_label_en: str
    pass_label_zh: str
    fail_label_en: str
    fail_label_zh: str
    fail_conclusion: Conclusion


@dataclass
class EventDetail:
    title: str
    text: str
    bullets: list[str]


@dataclass
class CardLayout:
    title_lines: list[str]
    detail_lines: list[str]
    height: float


@dataclass
class TextBoxLayout:
    lines: list[str]
    height: float


@dataclass
class LayoutRect:
    x: float
    y: float
    w: float
    h: float
    kind: str
    index: int

    @property
    def right(self) -> float:
        return self.x + self.w

    @property
    def bottom(self) -> float:
        return self.y + self.h


def render_exclusion_tree_to_file(data: dict[str, Any], output_path: Path) -> dict[str, Any]:
    normalized = normalize_input(data)
    svg = render_exclusion_tree(normalized)
    validate_svg(svg)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    return {
        "path": str(output_path),
        "format": "svg",
        "diagram_type": "exclusion_tree",
        "theme": normalized["theme"],
        "diagnostics": normalized["diagnostics"],
    }


def normalize_input(data: dict[str, Any]) -> dict[str, Any]:
    diagram_type = canonical_diagram_type(data.get("diagram_type", "exclusion_tree"))
    if diagram_type != "exclusion_tree":
        raise ValueError('Exclusion tree renderer requires diagram_type="exclusion_tree".')

    output = clean_text(data.get("output", "svg")).lower() or "svg"
    if output != "svg":
        raise ValueError("The exclusion_tree renderer outputs SVG only.")

    diagnostics = list(data.get("_diagnostics", [])) if isinstance(data.get("_diagnostics"), list) else []
    problem_raw = data.get("problem", {})
    if not isinstance(problem_raw, dict):
        problem_raw = {"text_en": problem_raw}

    checks_raw = data.get("checks", [])
    if not isinstance(checks_raw, list) or not checks_raw:
        diagnostics.append("No exclusion-tree checks were provided; default example checks were used.")
        checks_raw = DEFAULT_CHECKS
    if len(checks_raw) > MAX_CHECKS:
        diagnostics.append(f"Only the first {MAX_CHECKS} checks were rendered to preserve readability.")
        checks_raw = checks_raw[:MAX_CHECKS]

    checks = [normalize_check(raw, index) for index, raw in enumerate(checks_raw, start=1)]
    final_raw = data.get("final_pass_conclusion", {})
    if not isinstance(final_raw, dict):
        final_raw = {"text_en": final_raw}
    event_detail = normalize_event_detail(data.get("event_detail"), data, problem_raw)
    problem_en = first_present(problem_raw.get("text_en"), problem_raw.get("label"), data.get("topic"))
    problem_zh = clean_text(problem_raw.get("text_zh", ""))
    if not problem_en and not problem_zh:
        problem_en = "Target Problem"
    final_text_en = clean_text(final_raw.get("text_en", ""))
    final_text_zh = clean_text(final_raw.get("text_zh", ""))
    if not final_text_en and not final_text_zh:
        final_text_en = "No issue found in this path. Consider other rare causes or deeper analysis."

    return {
        "diagram_type": "exclusion_tree",
        "title": clean_text(data.get("title", "Sequential Exclusion Tree")) or "Sequential Exclusion Tree",
        "subtitle": clean_text(data.get("subtitle", "")),
        "problem_en": problem_en,
        "problem_zh": problem_zh,
        "language": normalize_language(data.get("language", "auto")),
        "theme": clean_text(data.get("theme", data.get("style", "business_simple"))) or "business_simple",
        "show_legend": as_bool(data.get("show_legend", True)),
        "show_how_to_use": as_bool(data.get("show_how_to_use", True)),
        "event_detail": event_detail,
        "checks": checks,
        "final_pass_conclusion": Conclusion(
            text_en=final_text_en,
            text_zh=final_text_zh,
            detail_en=clean_text(final_raw.get("detail_en", "")),
            detail_zh=clean_text(final_raw.get("detail_zh", "")),
        ),
        "diagnostics": diagnostics,
    }


def normalize_check(raw: Any, index: int) -> CheckPoint:
    if not isinstance(raw, dict):
        raw = {"text_en": raw}
    conclusion_raw = raw.get("fail_conclusion", {})
    if not isinstance(conclusion_raw, dict):
        conclusion_raw = {"text_en": conclusion_raw}
    text_en = first_present(raw.get("text_en"), raw.get("label"), raw.get("question"))
    text_zh = clean_text(raw.get("text_zh", ""))
    if not text_en and not text_zh:
        text_en = f"Check {index} OK?"
    pass_label_en = clean_text(raw.get("pass_label_en", ""))
    pass_label_zh = clean_text(raw.get("pass_label_zh", ""))
    if not pass_label_en and not pass_label_zh:
        pass_label_en = "Yes"
    fail_label_en = clean_text(raw.get("fail_label_en", ""))
    fail_label_zh = clean_text(raw.get("fail_label_zh", ""))
    if not fail_label_en and not fail_label_zh:
        fail_label_en = "No"
    conclusion_en = clean_text(conclusion_raw.get("text_en", ""))
    conclusion_zh = clean_text(conclusion_raw.get("text_zh", ""))
    if not conclusion_en and not conclusion_zh:
        conclusion_en = "Likely Cause"
    return CheckPoint(
        id=clean_text(raw.get("id", str(index))) or str(index),
        text_en=text_en,
        text_zh=text_zh,
        icon=normalize_icon(raw.get("icon") or infer_icon(text_zh, text_en)),
        pass_label_en=pass_label_en,
        pass_label_zh=pass_label_zh,
        fail_label_en=fail_label_en,
        fail_label_zh=fail_label_zh,
        fail_conclusion=Conclusion(
            text_en=conclusion_en,
            text_zh=conclusion_zh,
            detail_en=clean_text(conclusion_raw.get("detail_en", "")),
            detail_zh=clean_text(conclusion_raw.get("detail_zh", "")),
        ),
    )


def normalize_event_detail(raw_detail: Any, data: dict[str, Any], problem_raw: dict[str, Any]) -> EventDetail:
    if raw_detail is None:
        raw_detail = {}
    if isinstance(raw_detail, str):
        raw_detail = {"text": raw_detail}
    if not isinstance(raw_detail, dict):
        raw_detail = {}

    title = clean_text(raw_detail.get("title") or raw_detail.get("heading") or "Event Detail")
    text = clean_text(
        raw_detail.get("text")
        or raw_detail.get("description")
        or problem_raw.get("description")
        or problem_raw.get("detail")
        or data.get("subtitle")
        or ""
    )
    bullets_raw = raw_detail.get("bullets", [])
    if isinstance(bullets_raw, str):
        bullets = [clean_text(bullets_raw)]
    elif isinstance(bullets_raw, list):
        bullets = [clean_text(item) for item in bullets_raw if clean_text(item)]
    else:
        bullets = []
    return EventDetail(title=title, text=text, bullets=bullets)


def render_exclusion_tree(data: dict[str, Any]) -> str:
    checks: list[CheckPoint] = data["checks"]
    path_shift_x = main_path_shift_x(len(checks))
    top_layout = measure_top_event(data)
    check_layouts = [measure_checkpoint(check, index + 1, data["language"]) for index, check in enumerate(checks)]
    event_detail_height = measure_event_detail_panel(data["event_detail"])
    first_check_y = max(TOP_Y + top_layout.height + 62, DETAIL_Y + event_detail_height + 64)
    fail_w = FAIL_W
    final_w = FINAL_W
    fail_layouts = [measure_conclusion_card(check.fail_conclusion, fail_w, data["language"]) for check in checks]
    final_layout = measure_conclusion_card(data["final_pass_conclusion"], final_w, data["language"])
    positions: list[dict[str, float]] = []
    previous_fail_bottom = first_check_y
    previous_check_y = first_check_y
    previous_check_height = 0.0
    for index, layout in enumerate(fail_layouts):
        check_x = checkpoint_x(index, path_shift_x)
        if index == 0:
            check_y = first_check_y
        else:
            check_y = previous_check_y + previous_check_height + (CHECK_GAP_Y - CHECK_H)
        check_height = check_layouts[index].height
        card_x = cause_card_x(check_x, index)
        desired_y = check_y + check_height + CAUSE_CARD_TOP_GAP
        card_y = max(desired_y, previous_fail_bottom + CAUSE_CARD_MIN_GAP)
        positions.append({"check_x": check_x, "check_y": check_y, "check_height": check_height, "card_x": card_x, "card_y": card_y})
        previous_fail_bottom = card_y + layout.height
        previous_check_y = check_y
        previous_check_height = check_height
    last_check_y = positions[-1]["check_y"]
    last_check_height = positions[-1]["check_height"]
    final_y = last_check_y + last_check_height + 104
    fail_rects = [
        LayoutRect(position["card_x"], position["card_y"], fail_w, layout.height, "fail", index)
        for index, (position, layout) in enumerate(zip(positions, fail_layouts))
    ]
    checkpoint_rects = [
        LayoutRect(
            position["check_x"] - CHECK_W / 2,
            position["check_y"],
            CHECK_W,
            check_layouts[index].height,
            "checkpoint",
            index,
        )
        for index, position in enumerate(positions)
    ]
    fail_right = max(rect.right for rect in fail_rects)
    canvas_width = max(WIDTH, int(max(fail_right + 80, WIDTH)))
    last_check_x = positions[-1]["check_x"]
    final_card_x = final_card_left(last_check_x, final_w, canvas_width)
    final_rect = LayoutRect(final_card_x, final_y, final_w, final_layout.height, "final", 0)
    adjust_fail_positions_for_final(positions, fail_layouts, fail_w, final_rect)
    fail_rects = [
        LayoutRect(position["card_x"], position["card_y"], fail_w, layout.height, "fail", index)
        for index, (position, layout) in enumerate(zip(positions, fail_layouts))
    ]
    route_obstacles = fail_rects + checkpoint_rects + [final_rect]
    fail_lanes = [
        choose_fail_lane(checks[index], data["language"], position, fail_rects[index], index, route_obstacles)
        for index, position in enumerate(positions)
    ]
    how_to_use_x = canvas_width - 650
    how_to_use_y = compute_how_to_use_y(how_to_use_x, positions, fail_layouts, data["show_legend"])
    fail_bottom = max(
        position["card_y"] + layout.height
        for position, layout in zip(positions, fail_layouts)
    )
    canvas_height = max(
        HEIGHT,
        DETAIL_Y + event_detail_height + BOTTOM_MARGIN,
        fail_bottom + BOTTOM_MARGIN,
        final_y + final_layout.height + BOTTOM_MARGIN,
        how_to_use_y + HOW_TO_USE_H + BOTTOM_MARGIN,
    )

    parts = [
        svg_header(canvas_width, canvas_height),
        defs(),
        f'<rect width="{canvas_width}" height="{canvas_height}" fill="{PALETTE["background"]}"/>',
        render_event_detail_panel(data["event_detail"], event_detail_height),
        render_top_event(data, MAIN_X + path_shift_x, TOP_Y, top_layout),
    ]

    top_bottom = TOP_Y + top_layout.height
    parts.append(connector(MAIN_X + path_shift_x, top_bottom, MAIN_X + path_shift_x, first_check_y, arrow=True))

    check_positions: list[tuple[CheckPoint, float, float]] = []
    for index, check in enumerate(checks):
        position = positions[index]
        x = position["check_x"]
        y = position["check_y"]
        check_height = position["check_height"]
        check_positions.append((check, x, y))
        parts.append(render_checkpoint(check, x, y, check_layouts[index]))
        parts.append(
            render_fail_branch(
                check,
                x,
                y,
                check_height,
                position["card_x"],
                position["card_y"],
                fail_layouts[index],
                data["language"],
                fail_w,
                fail_lanes[index],
            )
        )

        if index < len(checks) - 1:
            next_x = checkpoint_x(index + 1, path_shift_x)
            next_y = positions[index + 1]["check_y"]
            parts.append(render_pass_branch(check, x, y, check_height, next_x, next_y, data["language"]))

    if check_positions:
        last_check, last_x, last_y = check_positions[-1]
        parts.append(render_final_pass_branch(data["final_pass_conclusion"], last_check, last_x, last_y, last_check_height, final_y, final_layout, data["language"], final_w, final_card_x))

    if data["show_legend"]:
        parts.append(render_legend(canvas_width - 390, 38))
    if data["show_how_to_use"]:
        parts.append(render_how_to_use(how_to_use_x, how_to_use_y))

    parts.append("</svg>")
    return "\n".join(parts)


def render_event_detail_panel(detail: EventDetail, height: float) -> str:
    chunks = [
        f'<g id="exclusion-event-detail-panel">',
        f'<rect x="{DETAIL_X}" y="{DETAIL_Y}" width="{DETAIL_W}" height="{height:.1f}" rx="14" fill="#FFFFFF" stroke="{PALETTE["line_blue"]}" stroke-width="1.8" filter="url(#subtleShadow)"/>',
        f'<text x="{DETAIL_X + DETAIL_TEXT_X_OFFSET}" y="{DETAIL_Y + DETAIL_TITLE_BASELINE_Y}" font-family="{FONT_STACK}" font-size="26" font-weight="700" fill="{PALETTE["navy"]}">{escape(detail.title)}</text>',
        f'<line x1="{DETAIL_X + DETAIL_TEXT_X_OFFSET}" y1="{DETAIL_Y + DETAIL_RULE_Y}" x2="{DETAIL_X + DETAIL_W - DETAIL_TEXT_RIGHT_PAD}" y2="{DETAIL_Y + DETAIL_RULE_Y}" stroke="{PALETTE["gray_line"]}" stroke-width="1.5"/>',
    ]
    body_chars, bullet_chars = detail_text_chars()
    current_y = DETAIL_Y + DETAIL_BODY_BASELINE_Y
    for line in wrap_text(detail.text, body_chars, max_lines=None):
        chunks.append(f'<text x="{DETAIL_X + DETAIL_TEXT_X_OFFSET}" y="{current_y}" font-family="{FONT_STACK}" font-size="18" fill="{PALETTE["gray_text"]}">{escape(line)}</text>')
        current_y += DETAIL_BODY_LINE_H
    for bullet in detail.bullets:
        for index, line in enumerate(wrap_text(bullet, bullet_chars, max_lines=None)):
            prefix = "- " if index == 0 else "  "
            chunks.append(f'<text x="{DETAIL_X + DETAIL_TEXT_X_OFFSET}" y="{current_y}" font-family="{FONT_STACK}" font-size="17" fill="{PALETTE["gray_text"]}">{escape(prefix + line)}</text>')
            current_y += DETAIL_BULLET_LINE_H
    chunks.append("</g>")
    return "\n".join(chunks)


def render_top_event(data: dict[str, Any], cx: float, y: float, layout: TextBoxLayout) -> str:
    x = cx - TOP_W / 2
    lines = layout.lines
    text_y = y + layout.height / 2 - (len(lines) - 1) * 15
    chunks = [
        f'<g class="exclusion-top-event">',
        f'<rect id="exclusion-top-event-block" x="{x:.1f}" y="{y:.1f}" width="{TOP_W}" height="{layout.height:.1f}" rx="14" fill="{PALETTE["navy"]}" filter="url(#softShadow)"/>',
    ]
    for i, line in enumerate(lines):
        chunks.append(f'<text x="{cx:.1f}" y="{text_y + i * 30:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="24" font-weight="700" fill="#FFFFFF">{escape(line)}</text>')
    chunks.append("</g>")
    return "\n".join(chunks)


def render_checkpoint(check: CheckPoint, cx: float, y: float, layout: TextBoxLayout) -> str:
    x = cx - CHECK_W / 2
    lines = layout.lines
    text_y = y + layout.height / 2 - (len(lines) - 1) * 13
    chunks = [
        f'<g class="exclusion-checkpoint" data-check-id="{escape(check.id)}">',
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{CHECK_W}" height="{layout.height:.1f}" rx="11" fill="{PALETTE["light_blue"]}" stroke="{PALETTE["navy_2"]}" stroke-width="2"/>',
        render_icon(check.icon, x + 44, y + layout.height / 2, PALETTE["navy_2"], 34),
    ]
    for i, line in enumerate(lines):
        chunks.append(f'<text x="{x + 92:.1f}" y="{text_y + i * 27:.1f}" font-family="{FONT_STACK}" font-size="19" font-weight="700" fill="{PALETTE["navy"]}">{escape(line)}</text>')
    chunks.append("</g>")
    return "\n".join(chunks)


def render_pass_branch(check: CheckPoint, x: float, y: float, check_height: float, next_x: float, next_y: float, language: str) -> str:
    sx = x - CHECK_W / 2 + 84
    sy = y + check_height
    mid_y = chip_center_y(y, check_height)
    tx = sx if abs(next_x - x) < 0.1 else next_x - CHECK_W / 2 + 84
    ty = next_y
    label = display_text(check.pass_label_zh, check.pass_label_en, language)
    return "\n".join(
        [
            pass_connector_path(sx, sy, mid_y, tx, ty),
            render_chip(label, sx, chip_top_y(y, check_height), "pass"),
        ]
    )


def pass_connector_path(sx: float, sy: float, mid_y: float, tx: float, ty: float) -> str:
    if abs(sx - tx) < 0.1:
        path = f"M {sx:.1f} {sy:.1f} L {sx:.1f} {ty:.1f}"
    else:
        path = f"M {sx:.1f} {sy:.1f} L {sx:.1f} {mid_y:.1f} L {tx:.1f} {mid_y:.1f} L {tx:.1f} {ty:.1f}"
    return f'<path class="exclusion-pass-connector" d="{path}" fill="none" stroke="{PALETTE["navy_2"]}" stroke-width="2" marker-end="url(#arrowNavy)"/>'


def render_fail_branch(check: CheckPoint, x: float, y: float, check_height: float, fail_x: float, fail_y: float, layout: CardLayout, language: str, fail_w: float, lane_x: float) -> str:
    cx = x + CHECK_W / 2 - 42
    mid_y = chip_center_y(y, check_height)
    label = display_text(check.fail_label_zh, check.fail_label_en, language)
    chip_w = chip_width(label)
    sx = cx + chip_w / 2
    card_x = fail_x
    card_y = fail_y
    entry_x = lane_x
    entry_y = card_y + FAIL_ARROW_INSET_Y
    return "\n".join(
        [
            connector(cx, y + check_height, cx, chip_top_y(y, check_height), arrow=False),
            f'<path class="exclusion-fail-connector exclusion-fail-drop-connector" d="M {sx:.1f} {mid_y:.1f} L {entry_x:.1f} {mid_y:.1f} L {entry_x:.1f} {entry_y:.1f}" fill="none" stroke="{PALETTE["navy_2"]}" stroke-width="2" marker-end="url(#arrowNavy)"/>',
            render_chip(label, cx, chip_top_y(y, check_height), "fail"),
            render_conclusion_card(check.fail_conclusion, card_x, card_y, fail_w, layout, "fail", language),
        ]
    )


def render_final_pass_branch(conclusion: Conclusion, check: CheckPoint, x: float, y: float, check_height: float, final_y: float, layout: CardLayout, language: str, final_w: float, card_x: float) -> str:
    sx = x - CHECK_W / 2 + 78
    sy = y + check_height
    label = display_text(check.pass_label_zh, check.pass_label_en, language)
    mid_y = chip_center_y(y, check_height)
    return "\n".join(
        [
            f'<path class="exclusion-final-pass-connector" d="M {sx:.1f} {sy:.1f} L {sx:.1f} {mid_y:.1f} L {sx:.1f} {final_y:.1f}" fill="none" stroke="{PALETTE["navy_2"]}" stroke-width="2" marker-end="url(#arrowNavy)"/>',
            render_chip(label, sx, chip_top_y(y, check_height), "pass"),
            render_conclusion_card(conclusion, card_x, final_y, final_w, layout, "final", language),
        ]
    )


def render_chip(label: str, cx: float, y: float, kind: str) -> str:
    fill = PALETTE["green_bg"] if kind == "pass" else PALETTE["red_bg"]
    stroke = PALETTE["green"] if kind == "pass" else PALETTE["red"]
    cls = "exclusion-pass-chip" if kind == "pass" else "exclusion-fail-chip"
    w = chip_width(label)
    x = cx - w / 2
    return (
        f'<g class="{cls}"><rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="38" rx="7" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
        f'<text x="{cx:.1f}" y="{y + 25:.1f}" text-anchor="middle" font-family="{FONT_STACK}" font-size="16" font-weight="700" fill="{stroke}">{escape(label)}</text></g>'
    )


def chip_width(label: str) -> float:
    return max(72, min(112, 18 + len(label) * 8))


def chip_top_y(check_y: float, check_height: float = CHECK_H) -> float:
    return check_y + check_height + 14


def chip_center_y(check_y: float, check_height: float = CHECK_H) -> float:
    return chip_top_y(check_y, check_height) + 19


def cause_card_x(check_x: float, index: int) -> float:
    fail_label_center = check_x + CHECK_W / 2 - 42
    local_x = fail_label_center + 210
    stepped_x = CAUSE_CARD_BASE_X - index * CAUSE_CARD_STEP_X
    return max(local_x, stepped_x, CAUSE_CARD_MIN_X)


def final_card_left(last_check_x: float, final_w: float, canvas_width: float) -> float:
    checkpoint_left = last_check_x - CHECK_W / 2
    return max(0, min(checkpoint_left, canvas_width - final_w - 36))


def adjust_fail_positions_for_final(
    positions: list[dict[str, float]],
    fail_layouts: list[CardLayout],
    fail_w: float,
    final_rect: LayoutRect,
) -> None:
    for index, (position, layout) in enumerate(zip(positions, fail_layouts)):
        if index > 0:
            previous = positions[index - 1]
            previous_bottom = previous["card_y"] + fail_layouts[index - 1].height
            position["card_y"] = max(position["card_y"], previous_bottom + CAUSE_CARD_MIN_GAP)
        rect = LayoutRect(position["card_x"], position["card_y"], fail_w, layout.height, "fail", index)
        if rects_overlap(rect, final_rect, 24):
            min_y = final_rect.bottom + 32
            if index > 0:
                previous = positions[index - 1]
                previous_bottom = previous["card_y"] + fail_layouts[index - 1].height
                min_y = max(min_y, previous_bottom + CAUSE_CARD_MIN_GAP)
            if position["card_y"] < min_y:
                position["card_y"] = min_y


def rects_overlap(first: LayoutRect, second: LayoutRect, margin: float = 0.0) -> bool:
    return (
        first.x < second.right + margin
        and first.right > second.x - margin
        and first.y < second.bottom + margin
        and first.bottom > second.y - margin
    )


def choose_fail_lane(check: CheckPoint, language: str, position: dict[str, float], target: LayoutRect, index: int, obstacles: list[LayoutRect]) -> float:
    chip_center_x = position["check_x"] + CHECK_W / 2 - 42
    label = display_text(check.fail_label_zh, check.fail_label_en, language)
    sx = chip_center_x + chip_width(label) / 2
    mid_y = chip_center_y(position["check_y"], position["check_height"])
    lane_min = target.x + FAIL_LANE_MIN_OFFSET
    lane_max = min(target.right - 54, target.x + FAIL_LANE_MAX_OFFSET)
    preferred = max(lane_min, min(target.x + FAIL_LANE_PREFERRED_OFFSET, lane_max))
    candidates = lane_candidates(preferred, lane_min, lane_max)
    route_obstacles = [
        rect
        for rect in obstacles
        if not (rect.kind == "fail" and rect.index == index)
        and not (rect.kind == "checkpoint" and rect.index == index)
    ]
    for candidate in candidates:
        if connector_segments_clear(sx, mid_y, candidate, target.y, route_obstacles):
            return candidate

    lane_max = target.right - 54
    candidates = lane_candidates(preferred, lane_min, lane_max)
    for candidate in candidates:
        if connector_segments_clear(sx, mid_y, candidate, target.y, route_obstacles):
            return candidate
    return preferred


def lane_candidates(preferred: float, lane_min: float, lane_max: float) -> list[float]:
    values = {round(lane_min, 1), round(lane_max, 1), round(preferred, 1)}
    step = 4
    distance = 0
    while distance <= int(max(preferred - lane_min, lane_max - preferred)) + step:
        values.add(round(max(lane_min, preferred - distance), 1))
        values.add(round(min(lane_max, preferred + distance), 1))
        distance += step
    return sorted(values, key=lambda value: (abs(value - preferred), value))


def connector_segments_clear(sx: float, y: float, lane_x: float, target_y: float, obstacles: list[LayoutRect]) -> bool:
    for obstacle in obstacles:
        if horizontal_segment_hits_rect(sx, lane_x, y, obstacle, CONNECTOR_CLEARANCE):
            return False
        if vertical_segment_hits_rect(lane_x, y, target_y, obstacle, CONNECTOR_CLEARANCE):
            return False
    return True


def horizontal_segment_hits_rect(x1: float, x2: float, y: float, rect: LayoutRect, margin: float) -> bool:
    left = min(x1, x2)
    right = max(x1, x2)
    return rect.y - margin < y < rect.bottom + margin and left < rect.right + margin and right > rect.x - margin


def vertical_segment_hits_rect(x: float, y1: float, y2: float, rect: LayoutRect, margin: float) -> bool:
    top = min(y1, y2)
    bottom = max(y1, y2)
    return rect.x - margin < x < rect.right + margin and top < rect.bottom + margin and bottom > rect.y - margin


def main_path_shift_x(check_count: int) -> float:
    if check_count < MAX_CHECKS:
        return 0.0
    last_x = checkpoint_x(check_count - 1)
    left_edge = last_x - CHECK_W / 2
    return max(0.0, TREE_LEFT_MARGIN - left_edge)


def checkpoint_x(index: int, shift_x: float = 0.0) -> float:
    base_steps = min(index, 3) * MAIN_PATH_STEP_X
    tail_steps = max(0, index - 3) * MAIN_PATH_TAIL_STEP_X
    return MAIN_X + shift_x - base_steps - tail_steps


def compute_how_to_use_y(panel_x: float, positions: list[dict[str, float]], fail_layouts: list[CardLayout], show_legend: bool) -> float:
    y = 38 + LEGEND_H + 36 if show_legend else 80
    panel_right = panel_x + HOW_TO_USE_W
    margin = 28
    for position, layout in zip(positions, fail_layouts):
        card_x = position["card_x"]
        card_right = card_x + FAIL_W
        if card_x < panel_right + margin and card_right > panel_x - margin:
            y = max(y, position["card_y"] + layout.height + 36)
    return y


def measure_top_event(data: dict[str, Any]) -> TextBoxLayout:
    label = display_text(data["problem_zh"], data["problem_en"], data["language"])
    lines = wrap_text(label, 18, max_lines=None)
    height = max(TOP_H, 34 + len(lines) * 30)
    return TextBoxLayout(lines=lines, height=height)


def measure_checkpoint(check: CheckPoint, index: int, language: str) -> TextBoxLayout:
    label = display_text(check.text_zh, check.text_en, language)
    lines = wrap_text(f"{index}. {label}", 24, max_lines=None)
    height = max(CHECK_H, 30 + len(lines) * 27)
    return TextBoxLayout(lines=lines, height=height)


def measure_conclusion_card(conclusion: Conclusion, width: float, language: str) -> CardLayout:
    title = display_text(conclusion.text_zh, conclusion.text_en, language)
    detail = display_text(conclusion.detail_zh, conclusion.detail_en, language)
    title_chars = card_text_chars(width, CARD_TITLE_CHAR_PX, 20)
    detail_chars = card_text_chars(width, CARD_DETAIL_CHAR_PX, 24)
    title_lines = wrap_text(title, title_chars, max_lines=None)
    detail_lines = wrap_text(detail, detail_chars, max_lines=None)
    last_baseline = CARD_HEADING_BASELINE_Y
    if title_lines:
        last_baseline = CARD_TITLE_BASELINE_Y + (len(title_lines) - 1) * CARD_TITLE_LINE_H
    if detail_lines:
        first_detail_y = CARD_TITLE_BASELINE_Y + len(title_lines) * CARD_TITLE_LINE_H + CARD_DETAIL_BASELINE_GAP
        last_baseline = first_detail_y + (len(detail_lines) - 1) * CARD_DETAIL_LINE_H
    height = last_baseline + CARD_BOTTOM_AFTER_TEXT
    return CardLayout(
        title_lines=title_lines,
        detail_lines=detail_lines,
        height=max(96, height),
    )


def measure_event_detail_panel(detail: EventDetail) -> float:
    body_chars, bullet_chars = detail_text_chars()
    text_lines = wrap_text(detail.text, body_chars, max_lines=None)
    bullet_lines: list[str] = []
    for bullet in detail.bullets:
        bullet_lines.extend(wrap_text(bullet, bullet_chars, max_lines=None))
    last_baseline = DETAIL_TITLE_BASELINE_Y
    if text_lines:
        last_baseline = DETAIL_BODY_BASELINE_Y + (len(text_lines) - 1) * DETAIL_BODY_LINE_H
    if bullet_lines:
        bullet_start_y = DETAIL_BODY_BASELINE_Y + len(text_lines) * DETAIL_BODY_LINE_H
        last_baseline = bullet_start_y + (len(bullet_lines) - 1) * DETAIL_BULLET_LINE_H
    height = last_baseline + DETAIL_BOTTOM_AFTER_TEXT
    return max(DETAIL_H, height)


def card_text_chars(width: float, char_px: float, minimum: int) -> int:
    text_width = max(120, width - CARD_TEXT_X_OFFSET - CARD_TEXT_RIGHT_PAD)
    return max(minimum, int(text_width / char_px))


def detail_text_chars() -> tuple[int, int]:
    text_width = max(120, DETAIL_W - DETAIL_TEXT_X_OFFSET - DETAIL_TEXT_RIGHT_PAD)
    body_chars = max(34, int(text_width / 8.0))
    bullet_chars = max(32, int((text_width - 14) / 8.0))
    return body_chars, bullet_chars


def render_conclusion_card(conclusion: Conclusion, x: float, y: float, w: float, layout: CardLayout, kind: str, language: str) -> str:
    is_final = kind == "final"
    fill = PALETTE["green_bg"] if is_final else "#FFFFFF"
    stroke = PALETTE["green"] if is_final else PALETTE["border_gray"]
    icon_color = PALETTE["green"] if is_final else PALETTE["red"]
    cls = "exclusion-final-pass" if is_final else "exclusion-fail-conclusion"
    text_x = x + CARD_TEXT_X_OFFSET
    chunks = [
        f'<g class="{cls}">',
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w}" height="{layout.height:.1f}" rx="13" fill="{fill}" stroke="{stroke}" stroke-width="1.5" filter="url(#subtleShadow)"/>',
        status_icon(x + 38, y + 43, icon_color, is_final),
    ]
    heading = "No Issue Found" if is_final else "Root Cause:"
    chunks.append(f'<text x="{text_x:.1f}" y="{y + CARD_HEADING_BASELINE_Y:.1f}" font-family="{FONT_STACK}" font-size="17" font-weight="700" fill="{PALETTE["navy"]}">{heading}</text>')
    current_y = y + CARD_TITLE_BASELINE_Y
    for line in layout.title_lines:
        chunks.append(f'<text x="{text_x:.1f}" y="{current_y:.1f}" font-family="{FONT_STACK}" font-size="16" font-weight="700" fill="{PALETTE["navy"]}">{escape(line)}</text>')
        current_y += CARD_TITLE_LINE_H
    if layout.detail_lines:
        current_y += CARD_DETAIL_BASELINE_GAP
        for line in layout.detail_lines:
            chunks.append(f'<text x="{text_x:.1f}" y="{current_y:.1f}" font-family="{FONT_STACK}" font-size="14" fill="{PALETTE["gray_text"]}">{escape(line)}</text>')
            current_y += CARD_DETAIL_LINE_H
    chunks.append("</g>")
    return "\n".join(chunks)


def render_legend(x: float, y: float) -> str:
    rows = [
        ("checkpoint", "Test Step / Check Point"),
        ("pass", "Yes (Pass)"),
        ("fail", "No (Fail)"),
        ("cause", "Excluded Cause"),
        ("final", "No Issue Found"),
    ]
    chunks = [
        f'<g id="exclusion-tree-legend">',
        f'<rect x="{x}" y="{y}" width="340" height="462" rx="12" fill="#FFFFFF" stroke="{PALETTE["line_blue"]}" stroke-width="1.6" stroke-dasharray="7 6"/>',
        f'<text x="{x + 24}" y="{y + 45}" font-family="{FONT_STACK}" font-size="23" font-weight="700" fill="{PALETTE["navy"]}">Legend</text>',
    ]
    row_y = y + 88
    for kind, label in rows:
        chunks.append(render_legend_symbol(kind, x + 58, row_y))
        chunks.append(f'<text x="{x + 112}" y="{row_y + 6}" font-family="{FONT_STACK}" font-size="16" font-weight="700" fill="{PALETTE["navy"]}">{escape(label)}</text>')
        row_y += 76
    chunks.append("</g>")
    return "\n".join(chunks)


def render_legend_symbol(kind: str, cx: float, cy: float) -> str:
    if kind == "checkpoint":
        return f'<rect x="{cx - 32}" y="{cy - 16}" width="64" height="32" rx="5" fill="{PALETTE["light_blue"]}" stroke="{PALETTE["navy_2"]}"/>'
    if kind == "pass":
        return f'<rect x="{cx - 32}" y="{cy - 16}" width="64" height="32" rx="5" fill="{PALETTE["green_bg"]}" stroke="{PALETTE["green"]}"/><text x="{cx}" y="{cy + 6}" text-anchor="middle" font-family="{FONT_STACK}" font-size="15" font-weight="700" fill="{PALETTE["green"]}">Yes</text>'
    if kind == "fail":
        return f'<rect x="{cx - 32}" y="{cy - 16}" width="64" height="32" rx="5" fill="{PALETTE["red_bg"]}" stroke="{PALETTE["red"]}"/><text x="{cx}" y="{cy + 6}" text-anchor="middle" font-family="{FONT_STACK}" font-size="15" font-weight="700" fill="{PALETTE["red"]}">No</text>'
    if kind == "cause":
        return f'<rect x="{cx - 32}" y="{cy - 18}" width="64" height="36" rx="6" fill="#FFFFFF" stroke="{PALETTE["border_gray"]}"/>{status_icon(cx, cy, PALETTE["red"], False)}'
    return f'<rect x="{cx - 32}" y="{cy - 18}" width="64" height="36" rx="6" fill="{PALETTE["green_bg"]}" stroke="{PALETTE["gray_line"]}"/>{status_icon(cx, cy, PALETTE["green"], True)}'


def render_how_to_use(x: float, y: float) -> str:
    rows = [
        "Start from the top event and run each check in order.",
        "Follow the Yes/No result downward along the arrows.",
        "When a check fails, treat the side card as the priority cause to verify.",
        "If all checks pass, investigate other paths or deeper causes.",
    ]
    chunks = [
        f'<g id="exclusion-how-to-use">',
        f'<rect x="{x}" y="{y}" width="{HOW_TO_USE_W}" height="{HOW_TO_USE_H}" rx="12" fill="#FFFFFF" stroke="{PALETTE["line_blue"]}" stroke-width="1.6" stroke-dasharray="7 6"/>',
        f'<text x="{x + 24}" y="{y + 42}" font-family="{FONT_STACK}" font-size="20" font-weight="700" fill="{PALETTE["navy"]}">How to Use</text>',
    ]
    row_y = y + 80
    for index, text in enumerate(rows, start=1):
        chunks.append(f'<rect x="{x + 24}" y="{row_y - 22}" width="28" height="28" rx="4" fill="{PALETTE["navy"]}"/>')
        chunks.append(f'<text x="{x + 38}" y="{row_y - 2}" text-anchor="middle" font-family="{FONT_STACK}" font-size="15" font-weight="700" fill="#FFFFFF">{index}</text>')
        chunks.append(f'<rect x="{x + 62}" y="{row_y - 28}" width="532" height="46" fill="#FFFFFF" stroke="{PALETTE["gray_line"]}" stroke-width="1"/>')
        chunks.append(f'<text x="{x + 82}" y="{row_y}" font-family="{FONT_STACK}" font-size="16" fill="{PALETTE["gray_text"]}">{escape(text)}</text>')
        row_y += 48
    chunks.append("</g>")
    return "\n".join(chunks)


def render_icon(name: str, cx: float, cy: float, color: str, size: float) -> str:
    icon_name = ICON_LUCIDE_MAP.get(name, ICON_LUCIDE_MAP["question"])
    inner = lucide_inner_svg(icon_name)
    if not inner:
        return ""
    scale = size / 24
    x = cx - 12 * scale
    y = cy - 12 * scale
    return (
        f'<g class="lucide-icon" transform="translate({x:.1f} {y:.1f}) scale({scale:.2f})" '
        f'fill="none" stroke="{color}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f"{inner}</g>"
    )


def lucide_inner_svg(name: str) -> str:
    if name in LUCIDE_ICON_CACHE:
        return LUCIDE_ICON_CACHE[name]
    path = LUCIDE_ICON_DIR / f"{name}.svg"
    if not path.exists():
        LUCIDE_ICON_CACHE[name] = ""
        return ""
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"^.*?<svg[^>]*>", "", text, flags=re.S)
    text = re.sub(r"</svg>\s*$", "", text, flags=re.S)
    LUCIDE_ICON_CACHE[name] = text.strip()
    return LUCIDE_ICON_CACHE[name]


def status_icon(cx: float, cy: float, color: str, is_check: bool) -> str:
    if is_check:
        path = f'<path d="M {cx - 9} {cy} L {cx - 2} {cy + 8} L {cx + 12} {cy - 9}" fill="none" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round" stroke-linejoin="round"/>'
    else:
        path = f'<line x1="{cx - 8}" y1="{cy - 8}" x2="{cx + 8}" y2="{cy + 8}" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/><line x1="{cx + 8}" y1="{cy - 8}" x2="{cx - 8}" y2="{cy + 8}" stroke="#FFFFFF" stroke-width="4" stroke-linecap="round"/>'
    return f'<g><circle cx="{cx}" cy="{cy}" r="17" fill="{color}"/>{path}</g>'


def connector(x1: float, y1: float, x2: float, y2: float, arrow: bool = False) -> str:
    marker = ' marker-end="url(#arrowNavy)"' if arrow else ""
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{PALETTE["navy_2"]}" stroke-width="2"{marker}/>'


def svg_header(width: int, height: int) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="Exclusion tree diagram">'
    )


def defs() -> str:
    return f"""<defs>
  <filter id="softShadow" x="-20%" y="-20%" width="140%" height="160%">
    <feDropShadow dx="6" dy="8" stdDeviation="6" flood-color="#0B2E63" flood-opacity="0.10"/>
  </filter>
  <filter id="subtleShadow" x="-20%" y="-20%" width="140%" height="160%">
    <feDropShadow dx="3" dy="5" stdDeviation="5" flood-color="#0B2E63" flood-opacity="0.08"/>
  </filter>
  <marker id="arrowNavy" viewBox="0 0 10 10" refX="8.5" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M 0 0 L 10 5 L 0 10 z" fill="{PALETTE["navy_2"]}"/>
  </marker>
</defs>"""
def parse_exclusion_tree_markdown(text: str) -> dict[str, Any]:
    metadata, body = split_markdown_front_matter(text)
    checks: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    problem = ""
    final_pass: dict[str, str] = {}
    event_detail = {
        "title": metadata.get("event_detail_title", "Event Detail"),
        "text": metadata.get("event_detail", metadata.get("subtitle", "")),
        "bullets": [],
    }
    in_event_detail = False

    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            heading = line[level:].strip()
            if level == 1:
                problem = heading
                current = None
                in_event_detail = False
            elif level == 2:
                current = {"id": str(len(checks) + 1), "text_en": heading, "fail_conclusion": {}}
                checks.append(current)
                in_event_detail = False
            continue
        bullet = parse_markdown_bullet(line)
        if bullet is not None and in_event_detail:
            event_detail["bullets"].append(bullet)
            continue
        key_value = parse_key_value(line)
        if key_value is None:
            continue
        key, value = key_value
        target = current if current is not None else None
        if key in {"event_detail_title", "detail_title"}:
            event_detail["title"] = value
            current = None
            in_event_detail = True
        elif key in {"event_detail", "description"}:
            event_detail["text"] = value
            current = None
            in_event_detail = True
        elif key in {"icon"} and target is not None:
            target["icon"] = value
        elif key in {"pass", "pass_label"} and target is not None:
            labels = split_dual_label(value)
            target["pass_label_zh"], target["pass_label_en"] = labels
        elif key in {"fail", "fail_label"} and target is not None:
            labels = split_dual_label(value)
            target["fail_label_zh"], target["fail_label_en"] = labels
        elif key in {"fail_conclusion", "conclusion", "root_cause"} and target is not None:
            target.setdefault("fail_conclusion", {})["text_en"] = value
        elif key in {"fail_detail", "detail"} and target is not None:
            target.setdefault("fail_conclusion", {})["detail_en"] = value
        elif key in {"final_pass_conclusion", "final_conclusion"}:
            final_pass["text_en"] = value

    return {
        "diagram_type": "exclusion_tree",
        "title": metadata.get("title", "Sequential Exclusion Tree"),
        "subtitle": metadata.get("subtitle", ""),
        "problem": {"text_en": metadata.get("problem", problem or "Target Problem")},
        "event_detail": event_detail,
        "checks": checks,
        "final_pass_conclusion": final_pass,
        "show_legend": as_bool(metadata.get("show_legend", True)),
        "show_how_to_use": as_bool(metadata.get("show_how_to_use", True)),
    }


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
                        metadata[parsed[0]] = parsed[1]
                return metadata, "\n".join(lines[index + 1 :])
    return metadata, clean


def parse_key_value(line: str) -> tuple[str, str] | None:
    match = re.match(r"^([A-Za-z_][A-Za-z0-9_ -]*)\s*:\s*(.*?)\s*$", line)
    if not match:
        return None
    return match.group(1).strip().lower().replace("-", "_").replace(" ", "_"), match.group(2).strip().strip("\"'")


def parse_markdown_bullet(line: str) -> str | None:
    match = re.match(r"^(?:[-*+]|\d+[.)])\s+(.+)$", line)
    if not match:
        return None
    return match.group(1).strip()


def split_dual_label(value: str) -> tuple[str, str]:
    parts = [part.strip() for part in re.split(r"/|\|", value, maxsplit=1)]
    if len(parts) == 2:
        return parts[0], parts[1]
    return "", value.strip()


def normalize_language(value: Any) -> str:
    language = clean_text(value).lower().replace("-", "_")
    if language in {"zh", "cn", "chinese", "zh_cn"}:
        return "zh"
    if language in {"en", "english"}:
        return "en"
    if language in {"bilingual", "dual", "both", "zh_en"}:
        return "bilingual"
    return "auto"


def first_present(*values: Any) -> str:
    for value in values:
        text = clean_text(value)
        if text:
            return text
    return ""


def display_text(zh: str, en: str, language: str) -> str:
    zh = clean_text(zh)
    en = clean_text(en)
    if language == "zh":
        return zh or en
    if language == "en":
        return en or zh
    if language == "bilingual" and zh and en:
        return f"{zh} / {en}"
    return en or zh


def validate_svg(svg: str) -> None:
    root = ElementTree.fromstring(svg)
    if not root.tag.endswith("svg"):
        raise ValueError("Generated output is not SVG.")


def wrap_text(text: str, max_chars: int, max_lines: int | None = 3) -> list[str]:
    text = clean_text(text)
    if not text:
        return []
    words = text.split()
    if len(words) <= 1:
        return split_long_text(text, max_chars, max_lines)
    lines: list[str] = []
    current = ""
    for word in words:
        if visual_len(word) > max_chars:
            if current:
                lines.append(current)
                current = ""
                if max_lines is not None and len(lines) >= max_lines:
                    break
            for chunk in split_long_text(word, max_chars, None):
                if max_lines is not None and len(lines) >= max_lines:
                    break
                lines.append(chunk)
            continue
        candidate = f"{current} {word}".strip()
        if visual_len(candidate) <= max_chars or not current:
            current = candidate
        else:
            lines.append(current)
            current = word
            if max_lines is not None and len(lines) >= max_lines:
                break
    if current and (max_lines is None or len(lines) < max_lines):
        lines.append(current)
    if max_lines is not None and len(lines) == max_lines and words and visual_len(" ".join(words)) > sum(visual_len(line) for line in lines):
        lines[-1] = trim_ellipsis(lines[-1], max_chars)
    return lines or [text]


def split_long_text(text: str, max_chars: int, max_lines: int | None) -> list[str]:
    lines: list[str] = []
    current = ""
    current_len = 0
    for char in text:
        char_len = visual_len(char)
        if current and current_len + char_len > max_chars:
            if char in "ï¼Œã€‚ï¼ï¼Ÿï¼›ï¼šã€,.!?;:":
                current += char
                lines.append(current)
                current = ""
                current_len = 0
                continue
            lines.append(current)
            current = char
            current_len = char_len
        else:
            current += char
            current_len += char_len
    if current:
        lines.append(current)
    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = trim_ellipsis(lines[-1], max_chars)
    return lines


def trim_ellipsis(text: str, max_chars: int) -> str:
    return text[: max(1, max_chars - 1)].rstrip() + "..."


def visual_len(text: str) -> int:
    return sum(2 if ord(char) > 127 else 1 for char in text)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).strip())


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() not in {"", "0", "false", "no", "off"}


def normalize_icon(value: Any) -> str:
    icon = clean_text(value).lower().replace("_", "-")
    allowed = {
        "bolt",
        "module",
        "chip",
        "signal",
        "thermometer",
        "gear",
        "document",
        "material",
        "operator",
        "question",
    }
    return icon if icon in allowed else "question"


def infer_icon(*values: str) -> str:
    text = " ".join(clean_text(value).lower() for value in values if clean_text(value))
    if any(token in text for token in ["power", "voltage", "input", "supply", "电源", "电压", "供电"]):
        return "bolt"
    if any(token in text for token in ["module", "firmware", "version", "configuration", "config", "模块", "固件", "版本", "配置"]):
        return "module"
    if any(token in text for token in ["board", "controller", "control", "cpu", "mcu", "控制板", "控制器"]):
        return "chip"
    if any(token in text for token in ["signal", "start", "trigger", "ready", "启动", "信号"]):
        return "signal"
    if any(token in text for token in ["thermal", "temperature", "chamber", "heat", "cold", "温度", "升降温", "热", "冷"]):
        return "thermometer"
    if any(token in text for token in ["gear", "mechanical", "motor", "机构", "机械"]):
        return "gear"
    if any(token in text for token in ["document", "record", "log", "procedure", "文件", "记录", "日志"]):
        return "document"
    if any(token in text for token in ["material", "part", "supply", "connector", "cable", "物料", "线缆", "连接器"]):
        return "material"
    if any(token in text for token in ["operator", "training", "people", "user", "人员", "培训", "操作员"]):
        return "operator"
    return "question"


def canonical_diagram_type(value: Any) -> str:
    return clean_text(value).lower().replace("-", "_").replace(" ", "_")
