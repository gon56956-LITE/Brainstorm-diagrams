#!/usr/bin/env python3
"""Render a review catalog of curated Lucide badge candidates."""

from __future__ import annotations

import re
from pathlib import Path
from xml.etree import ElementTree

from renderers.fishbone import FONT_STACK, PALETTE


ROOT = Path(__file__).resolve().parents[1]
ICON_DIR = ROOT / "assets" / "lucide-candidates"
WORK = ROOT / "work" / "fishbone"

GROUPS = [
    ("Confirmed Core", ["workflow", "network", "aperture", "thermometer", "cog"]),
    ("Confirmed Core", ["circuit-board", "boxes", "wrench", "shield-check", "map-pin"]),
    ("Confirmed Core", ["gauge", "chart-line", "circle-dollar-sign", "chart-no-axes-column-increasing"]),
    ("Product Design", ["component", "puzzle", "blocks", "orbit", "telescope"]),
    ("Optical / Scan", ["eye", "scan-eye", "scan", "crosshair", "microscope"]),
    ("Thermal / Environment", ["thermometer-sun", "fan", "flame", "waves", "wind"]),
    ("Mechanical / Assembly", ["box", "package", "settings", "hammer", "anvil"]),
    ("Industrial / Manufacturing", ["factory", "warehouse", "construction", "traffic-cone", "wrench"]),
    ("Logistics / Supply", ["package-open", "package-search", "package-check", "truck", "route"]),
    ("Electrical / Power", ["zap", "plug", "cpu", "circuit-board", "memory-stick"]),
    ("Comms / Network", ["router", "radio-tower", "satellite-dish", "wifi", "ethernet-port"]),
    ("Network / Signals", ["cable", "signal", "waypoints", "share-2", "rss"]),
    ("Network / Wireless", ["wifi-high", "wifi-low", "wifi-off", "wifi-cog", "wifi-sync"]),
    ("Cloud Core", ["cloud", "cloud-cog", "cloud-check", "cloud-alert", "cloud-off"]),
    ("Cloud Transfer", ["cloud-upload", "cloud-download", "cloud-backup", "cloud-sync", "cloud-lightning"]),
    ("Cloud Context", ["cloudy", "cloud-sun", "cloud-rain", "download-cloud", "upload-cloud"]),
    ("Data Center / Compute", ["server", "server-cog", "server-crash", "server-off", "pc-case"]),
    ("Data Center / Storage", ["database", "database-zap", "database-backup", "database-search", "hard-drive"]),
    ("Data Center / Devices", ["hard-drive-download", "hard-drive-upload", "monitor-cloud", "monitor-cog", "monitor-check"]),
    ("Compute / Operations", ["computer", "laptop", "cpu", "memory-stick", "terminal"]),
    ("Integration / Services", ["container", "webhook", "radio-receiver", "monitor-dot", "monitor-up"]),
    ("Security / Reliability", ["lock-keyhole", "shield-check", "shield-alert", "activity", "badge-check"]),
    ("Validation / Quality", ["gauge", "chart-line", "chart-column", "clipboard-check", "list-checks"]),
    ("Defect / Investigation", ["bug", "flask-conical", "microscope", "activity", "receipt"]),
    ("Field / Application", ["map-pin", "radar", "sun", "cloud-rain", "waves"]),
    ("Business / Cost", ["coins", "circle-dollar-sign", "receipt", "chart-no-axes-column-increasing"]),
]


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    svg_path = WORK / "lucide-badge-candidates.svg"
    svg = render_catalog()
    ElementTree.fromstring(svg)
    svg_path.write_text(svg, encoding="utf-8")
    print(f"Generated: {svg_path.relative_to(ROOT)}")
    return 0


def render_catalog() -> str:
    row_h = 154
    left = 72
    top = 138
    card_w = 380
    group_label_w = 430
    card_box_w = 320
    bottom_margin = 70
    right_margin = 72
    max_icons = max(len(icons) for _group_name, icons in GROUPS)
    width = left + group_label_w + (max_icons - 1) * card_w + card_box_w + right_margin
    height = top + (len(GROUPS) - 1) * row_h + 102 + bottom_margin
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Lucide badge candidate catalog">',
        "<defs>",
        '<filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">',
        '<feDropShadow dx="0" dy="7" stdDeviation="8" flood-color="#16324F" flood-opacity="0.12"/>',
        "</filter>",
        "</defs>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{PALETTE["background"]}"/>',
        f'<text x="{left}" y="58" font-family="{FONT_STACK}" font-size="30" font-weight="700" fill="{PALETTE["navy"]}">Lucide Badge Candidates</text>',
        f'<text x="{left}" y="91" font-family="{FONT_STACK}" font-size="15" fill="{PALETTE["muted_text"]}">Curated from Lucide Static v1.14.0 (ISC). Review candidates only; active renderer mapping has not been changed.</text>',
    ]

    for row, (group_name, icons) in enumerate(GROUPS):
        y = top + row * row_h
        parts.append(
            f'<text x="{left}" y="{y + 48}" font-family="{FONT_STACK}" font-size="20" font-weight="700" fill="{PALETTE["navy"]}">{escape_xml(group_name)}</text>'
        )
        for index, icon_name in enumerate(icons):
            x = left + group_label_w + index * card_w
            cx = x + 44
            cy = y + 34
            parts.extend(
                [
                    f'<rect x="{x - 24}" y="{y - 24}" width="320" height="102" rx="10" fill="#F8FBFF" stroke="{PALETTE["soft_blue"]}" stroke-width="1.5" filter="url(#softShadow)"/>',
                    f'<circle cx="{cx}" cy="{cy}" r="34" fill="#FFFFFF" stroke="{PALETTE["light_blue"]}" stroke-width="2"/>',
                    render_lucide_icon(icon_name, cx, cy),
                    f'<text x="{x + 94}" y="{y + 29}" font-family="{FONT_STACK}" font-size="18" font-weight="700" fill="{PALETTE["navy"]}">{escape_xml(icon_name)}</text>',
                    f'<text x="{x + 94}" y="{y + 53}" font-family="{FONT_STACK}" font-size="12" fill="{PALETTE["muted_text"]}">{row + 1}.{index + 1}</text>',
                ]
            )

    parts.append("</svg>")
    return "\n".join(parts)


def render_lucide_icon(name: str, cx: float, cy: float) -> str:
    inner = lucide_inner_svg(name)
    scale = 2.05
    x = cx - 12 * scale
    y = cy - 12 * scale
    return (
        f'<g transform="translate({x:.1f} {y:.1f}) scale({scale:.2f})" '
        f'fill="none" stroke="{PALETTE["blue"]}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">'
        f"{inner}</g>"
    )


def lucide_inner_svg(name: str) -> str:
    path = ICON_DIR / f"{name}.svg"
    if not path.exists():
        raise FileNotFoundError(f"Missing Lucide candidate icon: {path.relative_to(ROOT)}")
    text = path.read_text(encoding="utf-8")
    text = re.sub(r"<!--.*?-->", "", text, flags=re.S)
    text = re.sub(r"^.*?<svg\b[^>]*>", "", text, flags=re.S)
    text = re.sub(r"</svg>\s*$", "", text, flags=re.S)
    return text.strip()


def escape_xml(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    raise SystemExit(main())
