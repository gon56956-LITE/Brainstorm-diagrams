"""Business-simple roadmap/timeline SVG renderer."""

from __future__ import annotations

import math
import re
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any
from xml.etree import ElementTree
from xml.sax.saxutils import escape


ROOT = Path(__file__).resolve().parents[2]
LUCIDE_ICON_DIR = ROOT / "assets" / "lucide-candidates"
WIDTH = 1920
HEIGHT = 1080
FONT_STACK = "Arial"
SWIMLANE_BASE_H = 76
SWIMLANE_ROW_GAP = 36
SWIMLANE_MARKER_SLOT_GAP = 28
SWIMLANE_MARKER_NEAR_GAP = 14

PALETTE = {
    "background": "#FFFFFF",
    "soft": "#F7FAFD",
    "navy": "#0B3A75",
    "dark_navy": "#082B59",
    "text": "#0B234A",
    "muted": "#5F6F86",
    "grid": "#D8E1EE",
    "border": "#9DBCE8",
    "blue": "#2F6BFF",
    "blue_bg": "#DCEBFF",
    "teal": "#2C9C96",
    "teal_bg": "#DDF4F1",
    "purple": "#7A5CCB",
    "purple_bg": "#ECE7FF",
    "orange": "#F0A22E",
    "orange_bg": "#FFF1D6",
    "green": "#2E9D5B",
    "green_bg": "#E2F6EA",
    "red": "#D64545",
    "red_bg": "#FFE4E4",
    "gray": "#8A96A8",
    "gray_bg": "#EEF2F7",
}

ACCENTS = ["blue", "teal", "purple", "orange", "green", "gray"]
LANE_TYPE_ICONS = {
    "product_model": "package",
    "product": "package",
    "model": "package",
    "theme": "layers",
    "workstream": "workflow",
    "team": "users",
    "phase": "route",
}
LANE_NAME_ICONS = {
    "platform": "layers",
    "firmware": "circuit-board",
    "validation": "clipboard-check",
    "operations": "factory",
    "launch": "rocket",
    "customer": "users",
    "design": "component",
}
STATUS_COLORS = {
    "planned": "gray",
    "in_progress": "blue",
    "completed": "green",
    "at_risk": "orange",
    "blocked": "red",
    "delayed": "orange",
}


@dataclass
class Period:
    id: str
    label: str
    subtitle: str
    start: date
    end: date


@dataclass
class Lane:
    id: str
    name: str
    subtitle: str
    color: str
    icon: str
    row_count: int = 1
    marker_slot_count: int = 0
    y: float = 0
    height: float = 0


@dataclass
class Initiative:
    id: str
    lane_id: str
    name: str
    owner: str
    status: str
    start: date
    end: date
    milestone: str
    row: int = 0


@dataclass
class Marker:
    id: str
    lane_id: str
    name: str
    date: date
    marker_type: str
    owner: str
    status: str
    output: str


@dataclass
class MilestoneCardPlacement:
    marker_id: str
    node_x: float
    card_x: float
    row: int
    card_h: float
    title_lines: list[str]
    detail_lines: list[str]


@dataclass
class SwimlaneMarkerPlacement:
    marker_id: str
    marker_kind: str
    lane_id: str
    x: float
    slot: int
    y: float = 0


def render_roadmap_timeline_to_file(data: dict[str, Any], output_path: Path) -> dict[str, Any]:
    normalized = normalize_input(data)
    svg = render_roadmap_timeline(normalized)
    validate_svg(svg)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(svg, encoding="utf-8")
    return {
        "path": str(output_path),
        "format": "svg",
        "diagram_type": "roadmap_timeline",
        "theme": normalized["theme"],
        "diagnostics": normalized["diagnostics"],
    }


def normalize_input(data: dict[str, Any]) -> dict[str, Any]:
    if canonical(data.get("diagram_type", "roadmap_timeline")) != "roadmap_timeline":
        raise ValueError('Roadmap timeline renderer requires diagram_type="roadmap_timeline".')
    if clean_text(data.get("output", "svg")).lower() != "svg":
        raise ValueError("The roadmap_timeline renderer outputs SVG only.")

    diagnostics = list(data.get("_diagnostics", [])) if isinstance(data.get("_diagnostics"), list) else []
    preset = normalize_preset(data)
    language = normalize_language(data.get("language", "auto"), data)
    title = localized(data, "title", language) or ("Roadmap / Timeline" if preset == "swimlane_roadmap" else "Milestone Timeline")
    subtitle = localized(data, "subtitle", language)
    goal = clean_text(data.get("goal") or data.get("goal_zh") or "")
    notes = normalize_notes(data.get("notes", data.get("note", [])))

    if preset == "milestone_timeline":
        markers = normalize_markers(data.get("milestones", []), language, diagnostics)
        phases = normalize_phases(data.get("phases", []), diagnostics)
        periods = normalize_periods(data, markers=markers, phases=phases, initiatives=[], diagnostics=diagnostics)
        return {
            "diagram_type": "roadmap_timeline",
            "preset": preset,
            "title": title,
            "subtitle": subtitle,
            "goal": goal,
            "notes": notes,
            "language": language,
            "theme": clean_text(data.get("style", "business_simple")) or "business_simple",
            "time_granularity": canonical(data.get("time_granularity", "month")) or "month",
            "periods": periods,
            "milestones": markers,
            "phases": phases,
            "show_detail_cards": as_bool(data.get("show_detail_cards", True)),
            "show_table": as_bool(data.get("show_table", True)),
            "diagnostics": diagnostics,
        }

    lanes = normalize_lanes(data.get("lanes", []), language, diagnostics)
    lane_type = canonical(data.get("lane_type", "theme")) or "theme"
    apply_lane_icons(lanes, lane_type)
    initiatives = normalize_initiatives(data.get("initiatives", []), lanes, language, diagnostics)
    milestones = normalize_markers(data.get("milestones", []), language, diagnostics)
    decisions = normalize_markers(data.get("decision_points", []), language, diagnostics, default_type="decision")
    periods = normalize_periods(
        data,
        markers=milestones + decisions,
        phases=[],
        initiatives=initiatives,
        diagnostics=diagnostics,
    )
    assign_initiative_rows(initiatives, lanes, periods)
    return {
        "diagram_type": "roadmap_timeline",
        "preset": preset,
        "lane_type": lane_type,
        "title": title,
        "subtitle": subtitle,
        "goal": goal,
        "notes": notes,
        "language": language,
        "theme": clean_text(data.get("style", "business_simple")) or "business_simple",
        "time_granularity": canonical(data.get("time_granularity", "quarter")) or "quarter",
        "periods": periods,
        "lanes": lanes,
        "initiatives": initiatives,
        "milestones": milestones,
        "decision_points": decisions,
        "show_table": as_bool(data.get("show_table", True)),
        "show_summary_panel": as_bool(data.get("show_summary_panel", True)),
        "diagnostics": diagnostics,
    }


def normalize_preset(data: dict[str, Any]) -> str:
    preset = canonical(data.get("preset", ""))
    if preset in {"swimlane_roadmap", "milestone_timeline"}:
        return preset
    lanes = data.get("lanes", [])
    initiatives = data.get("initiatives", [])
    if isinstance(lanes, list) and len(lanes) > 1:
        return "swimlane_roadmap"
    if isinstance(initiatives, list) and initiatives:
        return "swimlane_roadmap"
    return "milestone_timeline"


def normalize_lanes(raw_lanes: Any, language: str, diagnostics: list[str]) -> list[Lane]:
    lanes: list[Lane] = []
    if not isinstance(raw_lanes, list) or not raw_lanes:
        diagnostics.append("No lanes were provided; a default Roadmap lane was used.")
        raw_lanes = [{"id": "lane_1", "name": "Roadmap"}]
    for index, raw in enumerate(raw_lanes, start=1):
        if not isinstance(raw, dict):
            raw = {"name": raw}
        lane_id = clean_text(raw.get("id", "")) or f"L{index}"
        color = canonical(raw.get("color", "")) or ACCENTS[(index - 1) % len(ACCENTS)]
        if color not in PALETTE:
            color = ACCENTS[(index - 1) % len(ACCENTS)]
        lanes.append(
            Lane(
                id=lane_id,
                name=localized(raw, "name", language) or f"Lane {index}",
                subtitle=localized(raw, "subtitle", language),
                color=color,
                icon=clean_text(raw.get("icon", "")),
            )
        )
    return lanes


def apply_lane_icons(lanes: list[Lane], lane_type: str) -> None:
    fallback = LANE_TYPE_ICONS.get(canonical(lane_type), "layers")
    for lane in lanes:
        if lane.icon:
            continue
        lookup = canonical(lane.name)
        lane.icon = LANE_NAME_ICONS.get(lookup, fallback)


def normalize_initiatives(raw_items: Any, lanes: list[Lane], language: str, diagnostics: list[str]) -> list[Initiative]:
    if not isinstance(raw_items, list):
        raw_items = []
    lane_ids = {lane.id for lane in lanes}
    fallback_lane = lanes[0].id
    initiatives: list[Initiative] = []
    for index, raw in enumerate(raw_items, start=1):
        if not isinstance(raw, dict):
            raw = {"name": raw}
        lane_id = clean_text(raw.get("lane_id", raw.get("lane", ""))) or fallback_lane
        if lane_id not in lane_ids:
            diagnostics.append(f"Initiative {raw.get('id', index)} used an unknown lane; it was placed in {fallback_lane}.")
            lane_id = fallback_lane
        start = parse_date_like(raw.get("start") or raw.get("start_date")) or parse_date_like(raw.get("start_period"))
        end = parse_date_like(raw.get("end") or raw.get("end_date")) or parse_date_like(raw.get("end_period")) or start
        if start is None:
            start = date.today()
            diagnostics.append(f"Initiative {raw.get('id', index)} had no start date; today's date was used.")
        if end is None or end < start:
            end = start
        initiatives.append(
            Initiative(
                id=clean_text(raw.get("id", "")) or f"I{index}",
                lane_id=lane_id,
                name=localized(raw, "name", language) or f"Initiative {index}",
                owner=clean_text(raw.get("owner", "")),
                status=normalize_status(raw.get("status", "planned")),
                start=start,
                end=end,
                milestone=clean_text(raw.get("key_milestone", raw.get("milestone", ""))),
            )
        )
    return initiatives


def normalize_markers(raw_items: Any, language: str, diagnostics: list[str], default_type: str = "milestone") -> list[Marker]:
    if not isinstance(raw_items, list):
        return []
    markers: list[Marker] = []
    for index, raw in enumerate(raw_items, start=1):
        if not isinstance(raw, dict):
            raw = {"name": raw}
        marker_date = parse_date_like(raw.get("date") or raw.get("target_date") or raw.get("period"))
        if marker_date is None:
            diagnostics.append(f"Milestone {raw.get('id', index)} had no date and was skipped.")
            continue
        markers.append(
            Marker(
                id=clean_text(raw.get("id", "")) or f"M{index}",
                lane_id=clean_text(raw.get("lane_id", raw.get("lane", ""))),
                name=localized(raw, "name", language) or f"Milestone {index}",
                date=marker_date,
                marker_type=canonical(raw.get("type", default_type)) or default_type,
                owner=clean_text(raw.get("owner", "")),
                status=normalize_status(raw.get("status", "planned")),
                output=clean_text(raw.get("output", raw.get("description", ""))),
            )
        )
    return sorted(markers, key=lambda marker: marker.date)


def normalize_phases(raw_items: Any, diagnostics: list[str]) -> list[dict[str, Any]]:
    if not isinstance(raw_items, list):
        return []
    phases = []
    for index, raw in enumerate(raw_items, start=1):
        if not isinstance(raw, dict):
            continue
        start = parse_date_like(raw.get("start") or raw.get("start_date"))
        end = parse_date_like(raw.get("end") or raw.get("end_date"))
        if start is None or end is None:
            diagnostics.append(f"Phase {index} was skipped because it needs start and end dates.")
            continue
        phases.append({"name": clean_text(raw.get("name", f"Phase {index}")), "start": start, "end": max(start, end)})
    return phases


def normalize_periods(
    data: dict[str, Any],
    *,
    markers: list[Marker],
    phases: list[dict[str, Any]],
    initiatives: list[Initiative],
    diagnostics: list[str],
) -> list[Period]:
    raw_periods = data.get("time_periods", [])
    periods: list[Period] = []
    if isinstance(raw_periods, list) and raw_periods:
        for index, raw in enumerate(raw_periods, start=1):
            if not isinstance(raw, dict):
                raw = {"label": str(raw)}
            start = parse_date_like(raw.get("start")) or date(2025, index, 1)
            end = parse_date_like(raw.get("end")) or start
            periods.append(
                Period(
                    id=clean_text(raw.get("id", "")) or clean_text(raw.get("label", "")) or f"P{index}",
                    label=clean_text(raw.get("label", "")) or f"Period {index}",
                    subtitle=clean_text(raw.get("subtitle", "")),
                    start=start,
                    end=max(start, end),
                )
            )
        return sorted(periods, key=lambda period: period.start)

    dates: list[date] = []
    for item in initiatives:
        dates.extend([item.start, item.end])
    dates.extend(marker.date for marker in markers)
    for phase in phases:
        dates.extend([phase["start"], phase["end"]])
    if not dates:
        diagnostics.append("No dates were provided; a four-quarter planning horizon was used.")
        return [
            Period("P1", "Phase 1", "", date(2025, 1, 1), date(2025, 3, 31)),
            Period("P2", "Phase 2", "", date(2025, 4, 1), date(2025, 6, 30)),
            Period("P3", "Phase 3", "", date(2025, 7, 1), date(2025, 9, 30)),
            Period("P4", "Phase 4", "", date(2025, 10, 1), date(2025, 12, 31)),
        ]
    minimum = min(dates)
    maximum = max(dates)
    granularity = canonical(data.get("time_granularity", "quarter"))
    return generate_periods(minimum, maximum, granularity)


def generate_periods(start: date, end: date, granularity: str) -> list[Period]:
    if granularity == "year":
        return [Period(str(year), str(year), "", date(year, 1, 1), date(year, 12, 31)) for year in range(start.year, end.year + 1)]
    if granularity == "half_year":
        periods = []
        for year in range(start.year, end.year + 1):
            periods.append(Period(f"{year}H1", f"{year} H1", "Jan - Jun", date(year, 1, 1), date(year, 6, 30)))
            periods.append(Period(f"{year}H2", f"{year} H2", "Jul - Dec", date(year, 7, 1), date(year, 12, 31)))
        return [period for period in periods if period.end >= start and period.start <= end]
    if granularity == "month":
        periods = []
        current = date(start.year, start.month, 1)
        while current <= end:
            next_month = date(current.year + (1 if current.month == 12 else 0), 1 if current.month == 12 else current.month + 1, 1)
            period_end = date.fromordinal(next_month.toordinal() - 1)
            periods.append(Period(current.strftime("%Y-%m"), current.strftime("%b"), str(current.year), current, period_end))
            current = next_month
        return periods
    periods = []
    for year in range(start.year, end.year + 1):
        quarters = [
            ("Q1", "Jan - Mar", date(year, 1, 1), date(year, 3, 31)),
            ("Q2", "Apr - Jun", date(year, 4, 1), date(year, 6, 30)),
            ("Q3", "Jul - Sep", date(year, 7, 1), date(year, 9, 30)),
            ("Q4", "Oct - Dec", date(year, 10, 1), date(year, 12, 31)),
        ]
        for quarter, subtitle, q_start, q_end in quarters:
            periods.append(Period(f"{year}{quarter}", f"{year} {quarter}", subtitle, q_start, q_end))
    return [period for period in periods if period.end >= start and period.start <= end]


def assign_initiative_rows(initiatives: list[Initiative], lanes: list[Lane], periods: list[Period]) -> None:
    starts: dict[str, list[date]] = {lane.id: [] for lane in lanes}
    for lane in lanes:
        rows: list[date] = []
        for item in sorted([item for item in initiatives if item.lane_id == lane.id], key=lambda value: value.start):
            for row_index, row_end in enumerate(rows):
                if item.start > row_end:
                    item.row = row_index
                    rows[row_index] = item.end
                    break
            else:
                item.row = len(rows)
                rows.append(item.end)
        lane.row_count = max(1, len(rows))
        starts[lane.id] = rows


def render_roadmap_timeline(data: dict[str, Any]) -> str:
    if data["preset"] == "milestone_timeline":
        return render_milestone_timeline(data)
    return render_swimlane_roadmap(data)


def swimlane_label_width(lanes: list[Lane]) -> float:
    longest = max((visual_len(lane.name) for lane in lanes), default=12)
    subtitle_longest = max((visual_len(lane.subtitle) for lane in lanes if lane.subtitle), default=0)
    return max(240, 86 + max(longest * 8.3, subtitle_longest * 6.5))


def swimlane_marker_lane_ids(markers: list[Marker], lane_ids: set[str], fallback_lane_id: str) -> set[str]:
    return {
        marker.lane_id if marker.lane_id in lane_ids else fallback_lane_id
        for marker in markers
        if marker.lane_id or fallback_lane_id
    }


def plan_swimlane_marker_placements(
    data: dict[str, Any],
    periods: list[Period],
    grid_x: float,
    period_w: float,
) -> dict[str, SwimlaneMarkerPlacement]:
    lanes: list[Lane] = data["lanes"]
    lane_ids = {lane.id for lane in lanes}
    fallback_lane_id = lanes[0].id if lanes else ""
    lane_markers: dict[str, list[tuple[str, Marker, float, float, float]]] = {lane.id: [] for lane in lanes}
    for marker_kind, markers in [("milestone", data["milestones"]), ("decision", data["decision_points"])]:
        for marker in markers:
            lane_id = marker.lane_id if marker.lane_id in lane_ids else fallback_lane_id
            if not lane_id:
                continue
            x = date_to_x(marker.date, periods, grid_x, period_w)
            label_w = visual_len(marker.name) * 7.0
            left = x - 12
            right = x + 18 + label_w
            lane_markers.setdefault(lane_id, []).append((marker_kind, marker, x, left, right))

    placements: dict[str, SwimlaneMarkerPlacement] = {}
    for lane_id, entries in lane_markers.items():
        slot_right_edges: list[float] = []
        for marker_kind, marker, x, left, right in sorted(entries, key=lambda entry: (entry[3], entry[1].date, entry[0], entry[1].id)):
            slot = 0
            while slot < len(slot_right_edges) and left < slot_right_edges[slot] + SWIMLANE_MARKER_NEAR_GAP:
                slot += 1
            if slot == len(slot_right_edges):
                slot_right_edges.append(right)
            else:
                slot_right_edges[slot] = right
            placements[swimlane_marker_key(marker_kind, marker.id)] = SwimlaneMarkerPlacement(marker.id, marker_kind, lane_id, x, slot)
    return placements


def assign_swimlane_marker_y(placements: dict[str, SwimlaneMarkerPlacement], lanes: list[Lane]) -> None:
    lane_map = {lane.id: lane for lane in lanes}
    for placement in placements.values():
        lane = lane_map.get(placement.lane_id)
        if lane is None:
            continue
        placement.y = lane.y + 20 + lane.row_count * SWIMLANE_ROW_GAP + 18 + placement.slot * SWIMLANE_MARKER_SLOT_GAP


def swimlane_marker_key(marker_kind: str, marker_id: str) -> str:
    return f"{marker_kind}:{marker_id}"


def render_swimlane_roadmap(data: dict[str, Any]) -> str:
    periods: list[Period] = data["periods"]
    lanes: list[Lane] = data["lanes"]
    period_w = 210
    label_w = swimlane_label_width(lanes)
    grid_x = label_w + 30
    grid_y = 205
    header_h = 60
    lane_gap = 0
    grid_w = max(900, len(periods) * period_w)
    summary_w = 360 if data["show_summary_panel"] else 0
    canvas_w = max(WIDTH, grid_x + grid_w + summary_w + 80)

    lane_ids = {lane.id for lane in lanes}
    fallback_lane_id = lanes[0].id if lanes else ""
    marker_lane_ids = swimlane_marker_lane_ids(data["milestones"] + data["decision_points"], lane_ids, fallback_lane_id)
    marker_placements = plan_swimlane_marker_placements(data, periods, grid_x, period_w)
    lane_y = grid_y + header_h
    for lane in lanes:
        lane.y = lane_y
        lane.marker_slot_count = max((placement.slot + 1 for placement in marker_placements.values() if placement.lane_id == lane.id), default=0)
        lane.height = SWIMLANE_BASE_H + (lane.row_count - 1) * SWIMLANE_ROW_GAP + lane.marker_slot_count * SWIMLANE_MARKER_SLOT_GAP
        lane_y += lane.height + lane_gap
    assign_swimlane_marker_y(marker_placements, lanes)
    grid_h = lane_y - (grid_y + header_h)
    table_y = lane_y + 28
    table_w = min(1280, canvas_w - summary_w - 90)
    table_h = 0
    if data["show_table"]:
        table_h = initiative_table_height(data, table_w)
    summary_h = summary_panel_height(data) if data["show_summary_panel"] else 0
    canvas_h = max(HEIGHT, table_y + max(table_h, summary_h) + 70)

    parts = [
        svg_header(canvas_w, canvas_h),
        defs(),
        f'<rect width="{canvas_w}" height="{canvas_h}" fill="{PALETTE["background"]}"/>',
        render_title(data),
        render_roadmap_legend(canvas_w - 520, 32, include_lanes=True),
        '<g id="roadmap-timeline" class="roadmap-timeline roadmap-swimlane">',
        render_time_header(periods, grid_x, grid_y, period_w, header_h),
        render_lane_panel(lanes, grid_x - label_w, grid_y + header_h, label_w, grid_h, marker_lane_ids),
        render_grid(periods, lanes, grid_x, grid_y + header_h, period_w, grid_h),
        render_initiatives(data, grid_x, period_w, periods),
        render_markers(data["milestones"], lanes, periods, grid_x, period_w, "milestone", marker_placements),
        render_markers(data["decision_points"], lanes, periods, grid_x, period_w, "decision", marker_placements),
        "</g>",
    ]
    if data["show_table"]:
        parts.append(render_initiative_table(data, 36, table_y, table_w))
    if data["show_summary_panel"]:
        parts.append(render_summary_panel(data, canvas_w - summary_w - 36, table_y, summary_w, max(summary_h, table_h)))
    parts.append("</svg>")
    return "\n".join(parts)


def render_milestone_timeline(data: dict[str, Any]) -> str:
    markers: list[Marker] = data["milestones"]
    periods: list[Period] = data["periods"]
    slot_w = 190
    axis_margin = 120
    axis_x = axis_margin
    desired_axis_w = max(1500, max(1, len(markers) - 1) * slot_w)
    canvas_w = max(WIDTH, axis_margin * 2 + desired_axis_w)
    axis_w = canvas_w - axis_margin * 2
    card_placements = plan_milestone_card_placements(markers, periods, axis_x, axis_w, data["show_detail_cards"])
    card_row_count = 1 + max((placement.row for placement in card_placements), default=0)
    legend_bottom = 32 + 142
    card_h = max((placement.card_h for placement in card_placements), default=72)
    card_to_axis = 54
    card_row_gap = card_h + 18
    axis_y = legend_bottom + 24 + card_h + card_to_axis + max(0, card_row_count - 1) * card_row_gap
    phase_y = axis_y + 78
    phase_h = len(data.get("phases", [])) * 28
    table_y = phase_y + phase_h + 42
    summary_w = 360
    summary_x = canvas_w - summary_w - 36
    table_h = 0
    if data["show_table"]:
        table_h = 42 + len(markers) * 32
    summary_h = milestone_info_panel_height(data)
    canvas_h = max(HEIGHT, table_y + max(table_h, summary_h) + 80)

    parts = [
        svg_header(canvas_w, canvas_h),
        defs(),
        f'<rect width="{canvas_w}" height="{canvas_h}" fill="{PALETTE["background"]}"/>',
        render_title(data),
        render_roadmap_legend(canvas_w - 460, 32, include_lanes=False),
        '<g id="roadmap-timeline" class="roadmap-timeline roadmap-milestone">',
        render_phase_bands(data.get("phases", []), periods, axis_x, phase_y, axis_w),
        f'<line x1="{axis_x}" y1="{axis_y}" x2="{axis_x + axis_w}" y2="{axis_y}" stroke="{PALETTE["navy"]}" stroke-width="4" marker-end="url(#arrowNavy)"/>',
        render_milestone_nodes(markers, periods, axis_x, axis_y, axis_w, data["show_detail_cards"], card_placements, card_row_gap),
        "</g>",
    ]
    if data["show_table"]:
        table_w = max(980, min(1420, summary_x - 78))
        parts.append(render_milestone_table(data, 42, table_y, table_w))
        parts.append(render_milestone_summary(data, summary_x, table_y, summary_w, summary_h))
    else:
        parts.append(render_milestone_summary(data, max(1260, canvas_w - 540), table_y, 500, summary_h))
    parts.append("</svg>")
    return "\n".join(parts)


def render_title(data: dict[str, Any]) -> str:
    chunks = [
        f'<text x="36" y="72" font-family="{FONT_STACK}" font-size="40" font-weight="700" fill="{PALETTE["navy"]}">{escape(data["title"])}</text>',
    ]
    if data["goal"]:
        chunks.append(f'<text x="38" y="112" font-family="{FONT_STACK}" font-size="18" font-weight="700" fill="{PALETTE["navy"]}">Goal: <tspan font-weight="500">{escape(data["goal"])}</tspan></text>')
    return "\n".join(chunks)


def render_roadmap_legend(x: float, y: float, *, include_lanes: bool) -> str:
    w = 500 if include_lanes else 440
    h = 142
    chunks = [
        '<g id="roadmap-legend" class="roadmap-legend">',
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" fill="{PALETTE["soft"]}" stroke="{PALETTE["border"]}" stroke-width="1.2"/>',
        f'<text x="{x + 18}" y="{y + 28}" font-family="{FONT_STACK}" font-size="16" font-weight="700" fill="{PALETTE["text"]}">Legend</text>',
    ]
    if include_lanes:
        labels = [("blue", "Lane / Initiative"), ("green", "Completed"), ("orange", "At Risk"), ("red", "Blocked")]
        for index, (color, label) in enumerate(labels):
            col = index % 2
            row = index // 2
            cx = x + 24 + col * 170
            cy = y + 52 + row * 30
            chunks.append(f'<rect x="{cx}" y="{cy - 10}" width="20" height="14" rx="3" fill="{PALETTE[color]}" />')
            chunks.append(f'<text x="{cx + 32}" y="{cy + 2}" font-family="{FONT_STACK}" font-size="13" font-weight="700" fill="{PALETTE["text"]}">{escape(label)}</text>')
    markers = [("circle", "Milestone"), ("star", "Key Milestone"), ("diamond", "Decision Point")]
    for index, (shape, label) in enumerate(markers):
        cx = x + (330 if include_lanes else 28)
        cy = y + 54 + index * 30
        chunks.append(marker_shape(shape, cx, cy, 10, PALETTE["navy"]))
        chunks.append(f'<text x="{cx + 24}" y="{cy + 5}" font-family="{FONT_STACK}" font-size="13" font-weight="700" fill="{PALETTE["text"]}">{escape(label)}</text>')
    chunks.append("</g>")
    return "\n".join(chunks)


def render_time_header(periods: list[Period], x: float, y: float, period_w: float, height: float) -> str:
    chunks = ['<g id="roadmap-time-header" class="roadmap-time-header">']
    for index, period in enumerate(periods):
        px = x + index * period_w
        chunks.append(f'<rect x="{px}" y="{y}" width="{period_w}" height="{height}" fill="{PALETTE["navy"]}" stroke="{PALETTE["border"]}" stroke-width="1"/>')
        chunks.append(f'<text x="{px + period_w / 2}" y="{y + 24}" text-anchor="middle" font-family="{FONT_STACK}" font-size="16" font-weight="700" fill="#FFFFFF">{escape(period.label)}</text>')
        if period.subtitle:
            chunks.append(f'<text x="{px + period_w / 2}" y="{y + 46}" text-anchor="middle" font-family="{FONT_STACK}" font-size="13" font-weight="700" fill="#FFFFFF">{escape(period.subtitle)}</text>')
    chunks.append("</g>")
    return "\n".join(chunks)


def render_lane_panel(lanes: list[Lane], x: float, y: float, width: float, height: float, marker_lane_ids: set[str]) -> str:
    chunks = [
        '<g id="roadmap-lanes" class="roadmap-lanes">',
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" fill="{PALETTE["soft"]}" stroke="{PALETTE["grid"]}" stroke-width="1"/>',
    ]
    for lane in lanes:
        cy = lane.y + lane.height / 2
        marker_band = "true" if lane.id in marker_lane_ids else "false"
        chunks.append(
            f'<g class="roadmap-lane" data-lane-id="{escape(lane.id)}" data-marker-band="{marker_band}" '
            f'data-row-count="{lane.row_count}" data-marker-slot-count="{lane.marker_slot_count}" data-lane-height="{lane.height:.1f}">'
        )
        chunks.append(f'<circle cx="{x + 34}" cy="{cy}" r="16" fill="{PALETTE[lane.color]}"/>')
        chunks.append(render_lucide_icon(lane.icon or "layers", x + 34, cy, "#FFFFFF", size=18))
        chunks.append(f'<text x="{x + 60}" y="{cy - (5 if lane.subtitle else -5)}" font-family="{FONT_STACK}" font-size="15" font-weight="700" fill="{PALETTE["text"]}">{escape(lane.name)}</text>')
        if lane.subtitle:
            chunks.append(f'<text x="{x + 60}" y="{cy + 16}" font-family="{FONT_STACK}" font-size="12" font-weight="700" fill="{PALETTE["muted"]}">{escape(lane.subtitle)}</text>')
        chunks.append("</g>")
    chunks.append("</g>")
    return "\n".join(chunks)


def render_grid(periods: list[Period], lanes: list[Lane], x: float, y: float, period_w: float, height: float) -> str:
    width = len(periods) * period_w
    chunks = [
        '<g id="roadmap-grid" class="roadmap-grid">',
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" fill="#FFFFFF" stroke="{PALETTE["grid"]}" stroke-width="1"/>',
    ]
    for index in range(len(periods) + 1):
        px = x + index * period_w
        chunks.append(f'<line x1="{px}" y1="{y}" x2="{px}" y2="{y + height}" stroke="{PALETTE["grid"]}" stroke-width="1"/>')
    for lane in lanes:
        chunks.append(f'<line x1="{x}" y1="{lane.y + lane.height}" x2="{x + width}" y2="{lane.y + lane.height}" stroke="{PALETTE["grid"]}" stroke-width="1"/>')
    chunks.append("</g>")
    return "\n".join(chunks)


def render_initiatives(data: dict[str, Any], grid_x: float, period_w: float, periods: list[Period]) -> str:
    lanes = {lane.id: lane for lane in data["lanes"]}
    chunks = ['<g id="roadmap-initiatives" class="roadmap-initiatives">']
    for item in data["initiatives"]:
        lane = lanes[item.lane_id]
        x1 = date_to_x(item.start, periods, grid_x, period_w)
        x2 = date_to_x(item.end, periods, grid_x, period_w)
        bar_x = min(x1, x2)
        bar_w = max(42, abs(x2 - x1))
        y = lane.y + 20 + item.row * 36
        color = lane.color
        label = fit_label_with_ellipsis(f"{item.id} {item.name}", max(4, int((bar_w - 36) / 7.3)))
        chunks.append(f'<g class="roadmap-initiative" data-id="{escape(item.id)}" data-lane-id="{escape(item.lane_id)}">')
        chunks.append(f'<rect x="{bar_x}" y="{y}" width="{bar_w}" height="28" rx="6" fill="{PALETTE[color + "_bg"]}" stroke="{PALETTE[color]}" stroke-width="1.2"/>')
        chunks.append(f'<text x="{bar_x + bar_w / 2}" y="{y + 18}" text-anchor="middle" font-family="{FONT_STACK}" font-size="13" font-weight="700" fill="{PALETTE["text"]}">{escape(label)}</text>')
        status_color = PALETTE[STATUS_COLORS.get(item.status, "gray")]
        chunks.append(f'<circle cx="{bar_x + bar_w - 8}" cy="{y + 14}" r="7" fill="{status_color}" stroke="#FFFFFF" stroke-width="1"/>')
        chunks.append("</g>")
    chunks.append("</g>")
    return "\n".join(chunks)


def render_markers(
    markers: list[Marker],
    lanes: list[Lane],
    periods: list[Period],
    grid_x: float,
    period_w: float,
    marker_kind: str,
    placements: dict[str, SwimlaneMarkerPlacement],
) -> str:
    lane_map = {lane.id: lane for lane in lanes}
    default_lane = lanes[0] if lanes else None
    chunks = [f'<g id="roadmap-{marker_kind}s" class="roadmap-{marker_kind}s">']
    for marker in markers:
        lane = lane_map.get(marker.lane_id) or default_lane
        if lane is None:
            continue
        placement = placements.get(swimlane_marker_key(marker_kind, marker.id))
        x = placement.x if placement else date_to_x(marker.date, periods, grid_x, period_w)
        y = placement.y if placement else lane.y + 20 + lane.row_count * SWIMLANE_ROW_GAP + 18
        shape = "diamond" if marker_kind == "decision" or marker.marker_type == "decision" else ("star" if marker.marker_type in {"launch", "key_milestone"} else "circle")
        chunks.append(f'<g class="roadmap-milestone roadmap-{marker_kind}" data-id="{escape(marker.id)}" data-lane-id="{escape(lane.id)}">')
        chunks.append(marker_shape(shape, x, y, 10, PALETTE["navy"]))
        chunks.append(f'<text x="{x + 14}" y="{y + 5}" font-family="{FONT_STACK}" font-size="12" font-weight="700" fill="{PALETTE["navy"]}">{escape(marker.name)}</text>')
        chunks.append("</g>")
    chunks.append("</g>")
    return "\n".join(chunks)


def render_initiative_table(data: dict[str, Any], x: float, y: float, width: float) -> str:
    layout = initiative_table_layout(data, width)
    rows = layout["rows"]
    row_heights = layout["row_heights"]
    columns = layout["columns"]
    headers = layout["headers"]
    header_h = layout["header_h"]
    total_h = layout["height"]
    chunks = ['<g id="roadmap-table" class="roadmap-table">']
    chunks.append(f'<rect x="{x}" y="{y}" width="{width}" height="{total_h}" rx="8" fill="#FFFFFF" stroke="{PALETTE["grid"]}" stroke-width="1"/>')
    chunks.append(f'<rect x="{x}" y="{y}" width="{width}" height="{header_h}" rx="8" fill="{PALETTE["navy"]}"/>')
    cx = x
    for header, col_w in zip(headers, columns):
        chunks.append(f'<text x="{cx + 10}" y="{y + 26}" font-family="{FONT_STACK}" font-size="13" font-weight="700" fill="#FFFFFF">{escape(fit_text(header, int((col_w - 16) / 7.2)))}</text>')
        cx += col_w
    row_y = y + header_h
    for row_index, (values, row_h) in enumerate(zip(rows, row_heights)):
        if row_index % 2:
            chunks.append(f'<rect x="{x}" y="{row_y}" width="{width}" height="{row_h}" fill="{PALETTE["soft"]}"/>')
        cx = x
        for value, col_w in zip(values, columns):
            lines = initiative_table_cell_lines(value, col_w)
            text_y = row_y + 17
            for line_index, line in enumerate(lines):
                chunks.append(f'<text x="{cx + 10}" y="{text_y + line_index * 15}" font-family="{FONT_STACK}" font-size="13" font-weight="600" fill="{PALETTE["text"]}">{escape(line)}</text>')
            cx += col_w
        chunks.append(f'<line x1="{x}" y1="{row_y + row_h}" x2="{x + width}" y2="{row_y + row_h}" stroke="{PALETTE["grid"]}" stroke-width="1"/>')
        row_y += row_h
    cx = x
    for col_w in columns:
        cx += col_w
        chunks.append(f'<line x1="{cx}" y1="{y}" x2="{cx}" y2="{y + total_h}" stroke="{PALETTE["grid"]}" stroke-width="1"/>')
    chunks.append("</g>")
    return "\n".join(chunks)


def initiative_table_height(data: dict[str, Any], width: float) -> float:
    return initiative_table_layout(data, width)["height"]


def initiative_table_layout(data: dict[str, Any], width: float) -> dict[str, Any]:
    headers = ["ID", "Initiative", "Lane", "Owner", "Start", "End", "Duration", "Key Milestone", "Status"]
    rows = initiative_table_values(data)
    min_columns = [44, 170, 110, 92, 96, 96, 74, 138, 86]
    max_columns = [64, 320, 220, 160, 112, 112, 92, 240, 118]
    desired_columns = []
    for index, header in enumerate(headers):
        max_len = visual_len(header)
        for row in rows:
            max_len = max(max_len, visual_len(row[index]))
        desired = max(min_columns[index], min(max_columns[index], max_len * 7.2 + 24))
        desired_columns.append(desired)

    columns = fit_table_columns(desired_columns, min_columns, width)
    row_heights = []
    for row in rows:
        line_count = max(len(initiative_table_cell_lines(value, col_w)) for value, col_w in zip(row, columns))
        row_heights.append(max(30, 12 + line_count * 15))
    header_h = 40
    return {
        "headers": headers,
        "rows": rows,
        "columns": columns,
        "row_heights": row_heights,
        "header_h": header_h,
        "height": header_h + sum(row_heights),
    }


def initiative_table_values(data: dict[str, Any]) -> list[list[str]]:
    lanes = {lane.id: lane for lane in data["lanes"]}
    milestones: list[Marker] = data["milestones"]
    rows: list[list[str]] = []
    for item in data["initiatives"]:
        rows.append(
            [
                item.id,
                item.name,
                lanes.get(item.lane_id, Lane("", item.lane_id, "", "gray", "")).name,
                item.owner,
                item.start.isoformat(),
                item.end.isoformat(),
                duration_label(item.start, item.end),
                initiative_milestone_label(item, milestones),
                status_label(item.status),
            ]
        )
    return rows


def fit_table_columns(desired_columns: list[float], min_columns: list[float], width: float) -> list[float]:
    desired_total = sum(desired_columns)
    if desired_total <= width:
        columns = desired_columns[:]
        slack = width - desired_total
        for index in [1, 2, 7]:
            add = min(slack, 60)
            columns[index] += add
            slack -= add
            if slack <= 0:
                break
        if slack > 0:
            columns[-1] += slack
        return columns

    min_total = sum(min_columns)
    if min_total >= width:
        scale = width / min_total
        return [value * scale for value in min_columns]

    shrink_total = desired_total - width
    shrink_capacity = sum(desired - minimum for desired, minimum in zip(desired_columns, min_columns))
    columns = []
    for desired, minimum in zip(desired_columns, min_columns):
        shrink = shrink_total * ((desired - minimum) / shrink_capacity) if shrink_capacity else 0
        columns.append(max(minimum, desired - shrink))
    return columns


def initiative_table_cell_lines(value: str, col_w: float) -> list[str]:
    max_chars = max(4, int((col_w - 18) / 7.2))
    lines = wrap_text(value, max_chars, max_lines=2)
    if not lines:
        return [""]
    if len(lines) == 2 and visual_len(lines[-1]) > max_chars:
        lines[-1] = fit_text(lines[-1], max_chars)
    return lines


def initiative_milestone_label(item: Initiative, milestones: list[Marker]) -> str:
    if item.milestone:
        return item.milestone
    related = [
        marker
        for marker in milestones
        if marker.lane_id == item.lane_id
        and item.start <= marker.date <= item.end
        and marker.marker_type in {"launch", "key_milestone", "milestone"}
    ]
    if not related:
        return "-"
    marker = sorted(related, key=lambda value: value.date)[0]
    return f"{marker.id}: {marker.name}"


def render_summary_panel(data: dict[str, Any], x: float, y: float, width: float, height: float) -> str:
    chunks = [
        '<g id="roadmap-summary-panel" class="roadmap-summary-panel">',
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" fill="{PALETTE["soft"]}" stroke="{PALETTE["border"]}" stroke-width="1.2"/>',
        f'<text x="{x + 22}" y="{y + 34}" font-family="{FONT_STACK}" font-size="16" font-weight="700" fill="{PALETTE["text"]}">Key Milestones</text>',
    ]
    cy = y + 64
    for marker in data["milestones"][:5]:
        chunks.append(marker_shape("star" if marker.marker_type in {"launch", "key_milestone"} else "circle", x + 26, cy - 5, 7, PALETTE["navy"]))
        chunks.append(f'<text x="{x + 46}" y="{cy}" font-family="{FONT_STACK}" font-size="12" font-weight="700" fill="{PALETTE["text"]}">{escape(marker.date.isoformat())}  {escape(marker.name)}</text>')
        cy += 28
    if data["decision_points"]:
        cy += 10
        chunks.append(f'<line x1="{x + 22}" y1="{cy}" x2="{x + width - 22}" y2="{cy}" stroke="{PALETTE["grid"]}" stroke-width="1"/>')
        cy += 32
        chunks.append(f'<text x="{x + 22}" y="{cy}" font-family="{FONT_STACK}" font-size="16" font-weight="700" fill="{PALETTE["text"]}">Decision Points</text>')
        cy += 28
        for marker in data["decision_points"][:4]:
            chunks.append(marker_shape("diamond", x + 26, cy - 5, 7, PALETTE["navy"]))
            chunks.append(f'<text x="{x + 46}" y="{cy}" font-family="{FONT_STACK}" font-size="12" font-weight="700" fill="{PALETTE["text"]}">{escape(marker.date.isoformat())}  {escape(marker.name)}</text>')
            cy += 28
    if data["notes"]:
        cy += 10
        chunks.append(f'<line x1="{x + 22}" y1="{cy}" x2="{x + width - 22}" y2="{cy}" stroke="{PALETTE["grid"]}" stroke-width="1"/>')
        cy += 34
        chunks.append(f'<text x="{x + 22}" y="{cy}" font-family="{FONT_STACK}" font-size="16" font-weight="700" fill="{PALETTE["text"]}">Notes</text>')
        cy += 28
        for note in data["notes"][:4]:
            for line in wrap_text(note, max(28, int((width - 60) / 7.2)), max_lines=2):
                chunks.append(f'<text x="{x + 28}" y="{cy}" font-family="{FONT_STACK}" font-size="12" font-weight="600" fill="{PALETTE["text"]}">- {escape(line)}</text>')
                cy += 20
    chunks.append("</g>")
    return "\n".join(chunks)


def summary_panel_height(data: dict[str, Any]) -> int:
    height = 58 + 28 * len(data["milestones"][:5])
    if data["decision_points"]:
        height += 72 + 28 * len(data["decision_points"][:4])
    if data["notes"]:
        height += 74
        for note in data["notes"][:4]:
            height += 20 * len(wrap_text(note, 42, max_lines=2))
    return max(260, height + 28)


def render_phase_bands(phases: list[dict[str, Any]], periods: list[Period], x: float, y: float, axis_w: float) -> str:
    if not phases:
        return ""
    chunks = ['<g id="roadmap-phases" class="roadmap-phases">']
    for index, phase in enumerate(phases):
        x1 = date_to_x_continuous(phase["start"], periods, x, axis_w)
        x2 = date_to_x_continuous(phase["end"], periods, x, axis_w)
        chunks.append(f'<rect x="{min(x1, x2)}" y="{y + index * 28}" width="{max(40, abs(x2 - x1))}" height="22" rx="5" fill="{PALETTE["blue_bg"]}" stroke="{PALETTE["border"]}" stroke-width="1"/>')
        chunks.append(f'<text x="{min(x1, x2) + 10}" y="{y + 16 + index * 28}" font-family="{FONT_STACK}" font-size="12" font-weight="700" fill="{PALETTE["text"]}">{escape(phase["name"])}</text>')
    chunks.append("</g>")
    return "\n".join(chunks)


def render_milestone_nodes(
    markers: list[Marker],
    periods: list[Period],
    x: float,
    y: float,
    axis_w: float,
    show_cards: bool,
    placements: list[MilestoneCardPlacement],
    card_row_gap: float,
) -> str:
    chunks = ['<g id="roadmap-milestones" class="roadmap-milestones">']
    placement_by_id = {placement.marker_id: placement for placement in placements}
    for index, marker in enumerate(markers):
        node_x = date_to_x_continuous(marker.date, periods, x, axis_w)
        shape = "star" if marker.marker_type in {"launch", "key_milestone"} else ("diamond" if marker.marker_type in {"review", "decision"} else "circle")
        chunks.append(f'<g class="roadmap-milestone" data-id="{escape(marker.id)}">')
        if show_cards:
            card_w = 150
            placement = placement_by_id.get(marker.id)
            card_h = placement.card_h if placement else 72
            card_x = placement.card_x if placement else min(max(node_x - card_w / 2, x), x + axis_w - card_w)
            card_center_x = card_x + card_w / 2
            row_index = placement.row if placement else 0
            title_lines = placement.title_lines if placement else wrap_text(marker.name, 18, max_lines=2)
            detail_lines = placement.detail_lines if placement else wrap_text(marker.output, 22, max_lines=3)
            card_y = y - card_h - 54 - row_index * card_row_gap
            chunks.append(f'<line x1="{node_x}" y1="{card_y + card_h}" x2="{node_x}" y2="{y}" stroke="{PALETTE["border"]}" stroke-width="1"/>')
        chunks.append(marker_shape(shape, node_x, y, 12, PALETTE["navy"]))
        date_y = y + 42
        chunks.append(f'<text x="{node_x}" y="{date_y}" text-anchor="middle" font-family="{FONT_STACK}" font-size="13" font-weight="700" fill="{PALETTE["text"]}">{escape(marker.date.strftime("%b %d"))}</text>')
        if show_cards:
            chunks.append(f'<rect x="{card_x}" y="{card_y}" width="{card_w}" height="{card_h}" rx="8" fill="{PALETTE["soft"]}" stroke="{PALETTE["border"]}" stroke-width="1.1"/>')
            for line_index, line in enumerate(title_lines):
                chunks.append(f'<text x="{card_center_x}" y="{card_y + 20 + line_index * 15}" text-anchor="middle" font-family="{FONT_STACK}" font-size="13" font-weight="700" fill="{PALETTE["text"]}">{escape(line)}</text>')
            detail_start_y = card_y + 24 + len(title_lines) * 15
            for line_index, line in enumerate(detail_lines):
                chunks.append(f'<text x="{card_center_x}" y="{detail_start_y + line_index * 16}" text-anchor="middle" font-family="{FONT_STACK}" font-size="11" font-weight="600" fill="{PALETTE["muted"]}">{escape(line)}</text>')
        chunks.append("</g>")
    chunks.append("</g>")
    return "\n".join(chunks)


def plan_milestone_card_placements(markers: list[Marker], periods: list[Period], x: float, axis_w: float, show_cards: bool) -> list[MilestoneCardPlacement]:
    if not show_cards:
        return []
    card_w = 150
    rows: list[list[tuple[float, float]]] = []
    placements: list[MilestoneCardPlacement] = []
    for marker in markers:
        node_x = date_to_x_continuous(marker.date, periods, x, axis_w)
        card_x = min(max(node_x - card_w / 2, x), x + axis_w - card_w)
        row = milestone_card_row(card_x, card_w, rows)
        title_lines = wrap_text(marker.name, 18, max_lines=3)
        detail_lines = wrap_text(marker.output, 22, max_lines=3) if marker.output else []
        if detail_lines:
            last_baseline = 24 + len(title_lines) * 15 + (len(detail_lines) - 1) * 16
            card_h = max(72, last_baseline + 13)
        else:
            last_baseline = 20 + (len(title_lines) - 1) * 15
            card_h = max(58, last_baseline + 15)
        placements.append(MilestoneCardPlacement(marker.id, node_x, card_x, row, card_h, title_lines, detail_lines))
    return placements


def milestone_card_row(card_x: float, card_w: float, rows: list[list[tuple[float, float]]]) -> int:
    gap = 14
    candidate = (card_x, card_x + card_w)
    for row_index, row in enumerate(rows):
        if all(candidate[1] + gap <= placed[0] or candidate[0] - gap >= placed[1] for placed in row):
            row.append(candidate)
            return row_index
    rows.append([candidate])
    return len(rows) - 1


def render_milestone_table(data: dict[str, Any], x: float, y: float, width: float) -> str:
    rows: list[Marker] = data["milestones"]
    row_h = 32
    header_h = 38
    columns = [58, 54, 230, 360, 132, 126, 150]
    scale = width / sum(columns)
    columns = [value * scale for value in columns]
    headers = ["ID", "Type", "Milestone", "Description", "Target Date", "Owner", "Status"]
    chunks = ['<g id="roadmap-table" class="roadmap-table">']
    chunks.append(f'<rect x="{x}" y="{y}" width="{width}" height="{header_h + len(rows) * row_h}" rx="8" fill="#FFFFFF" stroke="{PALETTE["grid"]}" stroke-width="1"/>')
    chunks.append(f'<rect x="{x}" y="{y}" width="{width}" height="{header_h}" rx="8" fill="{PALETTE["navy"]}"/>')
    cx = x
    for header, col_w in zip(headers, columns):
        chunks.append(f'<text x="{cx + 10}" y="{y + 24}" font-family="{FONT_STACK}" font-size="13" font-weight="700" fill="#FFFFFF">{escape(header)}</text>')
        cx += col_w
    for row_index, marker in enumerate(rows):
        row_y = y + header_h + row_index * row_h
        if row_index % 2:
            chunks.append(f'<rect x="{x}" y="{row_y}" width="{width}" height="{row_h}" fill="{PALETTE["soft"]}"/>')
        values = [marker.id, "", marker.name, marker.output or "-", marker.date.isoformat(), marker.owner, status_label(marker.status)]
        cx = x
        for col_index, (value, col_w) in enumerate(zip(values, columns)):
            if col_index == 1:
                chunks.append(marker_shape(milestone_table_marker_shape(marker), cx + col_w / 2, row_y + row_h / 2, 7, PALETTE["navy"]))
            else:
                chunks.append(f'<text x="{cx + 10}" y="{row_y + 21}" font-family="{FONT_STACK}" font-size="13" font-weight="600" fill="{PALETTE["text"]}">{escape(fit_text(value, int(col_w / 7.5)))}</text>')
            cx += col_w
        chunks.append(f'<line x1="{x}" y1="{row_y + row_h}" x2="{x + width}" y2="{row_y + row_h}" stroke="{PALETTE["grid"]}" stroke-width="1"/>')
    chunks.append("</g>")
    return "\n".join(chunks)


def milestone_table_marker_shape(marker: Marker) -> str:
    if marker.marker_type in {"launch", "key_milestone"}:
        return "star"
    if marker.marker_type in {"decision", "review"}:
        return "diamond"
    return "circle"


def render_milestone_summary(data: dict[str, Any], x: float, y: float, width: float, height: float) -> str:
    return render_milestone_info_panel(data, x, y, width, max(height, milestone_info_panel_height(data)))


def render_milestone_info_panel(data: dict[str, Any], x: float, y: float, width: float, height: float) -> str:
    chunks = [
        '<g id="roadmap-summary-panel" class="roadmap-summary-panel roadmap-milestone-info-panel">',
        f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" fill="{PALETTE["soft"]}" stroke="{PALETTE["border"]}" stroke-width="1.2"/>',
        f'<text x="{x + 22}" y="{y + 34}" font-family="{FONT_STACK}" font-size="16" font-weight="700" fill="{PALETTE["text"]}">Phase Plan</text>',
    ]
    cy = y + 64
    phases = data.get("phases", [])
    for phase in phases[:5]:
        label = f'{phase["start"].isoformat()} - {phase["end"].isoformat()}'
        chunks.append(f'<text x="{x + 24}" y="{cy}" font-family="{FONT_STACK}" font-size="12" font-weight="700" fill="{PALETTE["text"]}">{escape(phase["name"])}</text>')
        chunks.append(f'<text x="{x + 24}" y="{cy + 18}" font-family="{FONT_STACK}" font-size="11" font-weight="600" fill="{PALETTE["muted"]}">{escape(label)}</text>')
        cy += 42
    if len(phases) > 5:
        chunks.append(f'<text x="{x + 24}" y="{cy}" font-family="{FONT_STACK}" font-size="11" font-weight="700" fill="{PALETTE["muted"]}">+{len(phases) - 5} more phases</text>')
        cy += 24
    if data["notes"]:
        cy += 6
        chunks.append(f'<line x1="{x + 22}" y1="{cy}" x2="{x + width - 22}" y2="{cy}" stroke="{PALETTE["grid"]}" stroke-width="1"/>')
        cy += 34
        chunks.append(f'<text x="{x + 22}" y="{cy}" font-family="{FONT_STACK}" font-size="16" font-weight="700" fill="{PALETTE["text"]}">Notes</text>')
        cy += 28
        for note in data["notes"][:4]:
            for line in wrap_text(note, max(28, int((width - 60) / 7.2)), max_lines=2):
                chunks.append(f'<text x="{x + 28}" y="{cy}" font-family="{FONT_STACK}" font-size="12" font-weight="600" fill="{PALETTE["text"]}">- {escape(line)}</text>')
                cy += 20
    chunks.append("</g>")
    return "\n".join(chunks)


def milestone_info_panel_height(data: dict[str, Any]) -> int:
    phases = data.get("phases", [])
    height = 58 + 42 * min(5, len(phases))
    if len(phases) > 5:
        height += 24
    if data["notes"]:
        height += 74
        for note in data["notes"][:4]:
            height += 20 * len(wrap_text(note, 42, max_lines=2))
    return max(260, height + 28)


def date_to_x(value: date, periods: list[Period], grid_x: float, period_w: float) -> float:
    for index, period in enumerate(periods):
        if period.start <= value <= period.end:
            span = max(1, period.end.toordinal() - period.start.toordinal())
            ratio = (value.toordinal() - period.start.toordinal()) / span
            return grid_x + index * period_w + ratio * period_w
    if value < periods[0].start:
        return grid_x
    return grid_x + len(periods) * period_w


def date_to_x_continuous(value: date, periods: list[Period], x: float, width: float) -> float:
    start = periods[0].start
    end = periods[-1].end
    span = max(1, end.toordinal() - start.toordinal())
    ratio = min(1, max(0, (value.toordinal() - start.toordinal()) / span))
    return x + ratio * width


def marker_shape(shape: str, cx: float, cy: float, size: float, color: str) -> str:
    if shape == "diamond":
        points = f"{cx},{cy - size} {cx + size},{cy} {cx},{cy + size} {cx - size},{cy}"
        return f'<polygon points="{points}" fill="#FFFFFF" stroke="{color}" stroke-width="2.2"/>'
    if shape == "star":
        points = []
        for index in range(10):
            radius = size if index % 2 == 0 else size * 0.45
            angle = -90 + index * 36
            x = cx + radius * math.cos(math.radians(angle))
            y = cy + radius * math.sin(math.radians(angle))
            points.append(f"{x:.1f},{y:.1f}")
        return f'<polygon points="{" ".join(points)}" fill="{color}" stroke="{color}" stroke-width="1.4"/>'
    return f'<circle cx="{cx}" cy="{cy}" r="{size}" fill="{color}"/>'


def render_lucide_icon(icon: str, cx: float, cy: float, color: str, *, size: int = 18) -> str:
    inner = lucide_inner_svg(icon)
    if not inner:
        inner = lucide_inner_svg("layers")
    scale = size / 24
    x = cx - 12 * scale
    y = cy - 12 * scale
    return (
        f'<g class="lucide-icon lucide-{escape(icon)}" transform="translate({x:.1f} {y:.1f}) scale({scale:.3f})" '
        f'stroke="{color}" fill="none" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">{inner}</g>'
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


def normalize_language(value: Any, data: dict[str, Any]) -> str:
    language = clean_text(value).lower()
    if language in {"en", "english"}:
        return "en"
    if language in {"zh", "cn", "chinese"}:
        return "zh"
    if language == "bilingual":
        return "bilingual"
    text = " ".join(str(value) for value in data.values())
    return "zh" if contains_cjk(text) else "en"


def localized(raw: dict[str, Any], key: str, language: str) -> str:
    base = clean_text(raw.get(key, ""))
    zh = clean_text(raw.get(f"{key}_zh", ""))
    if language == "zh":
        return zh or base
    if language == "bilingual" and zh and base:
        return f"{base} / {zh}"
    return base or zh


def normalize_notes(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [clean_text(item) for item in raw if clean_text(item)]
    text = clean_text(raw)
    return [text] if text else []


def parse_date_like(value: Any) -> date | None:
    text = clean_text(value)
    if not text:
        return None
    match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", text)
    if match:
        return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
    match = re.search(r"(\d{4})\s*Q([1-4])", text, flags=re.I)
    if match:
        month = (int(match.group(2)) - 1) * 3 + 1
        return date(int(match.group(1)), month, 1)
    match = re.search(r"(\d{4})\s*H([12])", text, flags=re.I)
    if match:
        return date(int(match.group(1)), 1 if match.group(2) == "1" else 7, 1)
    match = re.search(r"(\d{4})-(\d{1,2})", text)
    if match:
        return date(int(match.group(1)), int(match.group(2)), 1)
    return None


def normalize_status(value: Any) -> str:
    status = canonical(value)
    aliases = {"inprogress": "in_progress", "in_progress": "in_progress", "done": "completed", "complete": "completed"}
    return aliases.get(status, status if status in STATUS_COLORS else "planned")


def status_label(status: str) -> str:
    return status.replace("_", " ").title()


def duration_label(start: date, end: date) -> str:
    days = max(1, end.toordinal() - start.toordinal() + 1)
    months = max(1, round(days / 30))
    return f"{months}M"


def parse_roadmap_timeline_markdown(text: str) -> dict[str, Any]:
    metadata, body = split_markdown_front_matter(text)
    data: dict[str, Any] = {
        "diagram_type": "roadmap_timeline",
        "preset": metadata.get("preset", ""),
        "lane_type": metadata.get("lane_type", ""),
        "time_granularity": metadata.get("time_granularity", ""),
        "language": metadata.get("language", "auto"),
        "show_table": as_bool(metadata.get("show_table", True)),
        "show_summary_panel": as_bool(metadata.get("show_summary_panel", True)),
        "show_detail_cards": as_bool(metadata.get("show_detail_cards", True)),
        "time_periods": [],
        "lanes": [],
        "initiatives": [],
        "milestones": [],
        "decision_points": [],
        "phases": [],
        "notes": [],
    }
    section = ""
    tables: dict[str, list[str]] = {}
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
                section = canonical(heading)
                tables.setdefault(section, [])
            continue
        parsed = parse_key_value(line)
        if parsed:
            key, value = parsed
            key = canonical(key)
            if key in {"goal", "subtitle", "title"}:
                data[key] = value
            elif key in {"notes", "note"}:
                data["notes"] = [value]
            continue
        if "|" in raw_line and section:
            tables.setdefault(section, []).append(raw_line)
        elif section in {"notes", "note"}:
            bullet = re.sub(r"^[-*]\s*", "", line)
            data.setdefault("notes", []).append(bullet)
    mapping = {
        "time_periods": "time_periods",
        "periods": "time_periods",
        "lanes": "lanes",
        "initiatives": "initiatives",
        "milestones": "milestones",
        "decision_points": "decision_points",
        "decisions": "decision_points",
        "phases": "phases",
    }
    for section_name, target in mapping.items():
        if section_name in tables:
            data[target] = parse_table(tables[section_name])
    return data


def parse_table(lines: list[str]) -> list[dict[str, str]]:
    rows = []
    for line in lines:
        stripped = line.strip()
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if all(re.fullmatch(r":?-{3,}:?", cell or "") for cell in cells):
            continue
        rows.append(cells)
    if not rows:
        return []
    headers = [canonical(cell) for cell in rows[0]]
    return [{header: cell for header, cell in zip(headers, row)} for row in rows[1:] if any(row)]


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
                        metadata[canonical(parsed[0])] = parsed[1]
                return metadata, "\n".join(lines[index + 1 :])
    return metadata, clean


def parse_key_value(line: str) -> tuple[str, str] | None:
    normalized = re.sub(r"^>\s*", "", line.strip())
    normalized = re.sub(r"^\*\*([^*:]+)\s*:\*\*\s*", r"\1: ", normalized)
    normalized = re.sub(r"^\*\*([^*]+)\*\*\s*:\s*", r"\1: ", normalized)
    match = re.match(r"^([A-Za-z_][A-Za-z0-9_ -]*)\s*:\s*(.*?)\s*$", normalized)
    if not match:
        return None
    return match.group(1).strip(), match.group(2).strip().strip("\"'")


def wrap_text(text: str, max_chars: int, max_lines: int | None = None) -> list[str]:
    clean = clean_text(text)
    if not clean:
        return [""]
    has_cjk = contains_cjk(clean)
    units = list(clean) if has_cjk else clean.split()
    lines: list[str] = []
    current = ""
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
    return lines[:max_lines] if max_lines is not None else lines


def fit_text(text: str, max_chars: int) -> str:
    clean = clean_text(text)
    if visual_len(clean) <= max_chars:
        return clean
    output = ""
    length = 0
    for char in clean:
        char_len = 2 if ord(char) > 127 else 1
        if length + char_len > max_chars - 3:
            break
        output += char
        length += char_len
    return output.rstrip() + "..."


def fit_label_with_ellipsis(text: str, max_chars: int) -> str:
    clean = clean_text(text)
    if visual_len(clean) <= max_chars:
        return clean
    if max_chars <= 3:
        return "..."
    return fit_text(clean, max_chars)


def clean_text(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def canonical(value: Any) -> str:
    return clean_text(value).lower().replace("-", "_").replace(" ", "_")


def as_bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() not in {"false", "0", "no", "off"}
    return bool(value)


def contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def visual_len(text: str) -> int:
    return sum(2 if ord(char) > 127 else 1 for char in text)


def svg_header(width: int | float, height: int | float) -> str:
    return f'<svg xmlns="http://www.w3.org/2000/svg" width="{int(width)}" height="{int(height)}" viewBox="0 0 {int(width)} {int(height)}">'


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
