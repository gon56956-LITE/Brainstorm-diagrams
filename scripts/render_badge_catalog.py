#!/usr/bin/env python3
"""Render the built-in fishbone badge icon catalog."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree

from renderers.fishbone import FONT_STACK, PALETTE, render_icon


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work" / "fishbone"

BADGES = [
    ("people", "People / operators / users"),
    ("process", "Process / control loop"),
    ("tools", "Tools / equipment / fixtures"),
    ("layers", "System / architecture / functions"),
    ("gauge", "Performance / test / measurement"),
    ("shield", "Reliability / protection / quality"),
    ("coin", "Cost / budget"),
    ("environment", "Environment / field conditions"),
    ("methods", "Methods / workflow / documents"),
    ("materials", "Materials / components / supply"),
    ("generic", "Generic fallback"),
]


def main() -> int:
    WORK.mkdir(parents=True, exist_ok=True)
    output_path = WORK / "badge-catalog.svg"
    svg = render_catalog()
    ElementTree.fromstring(svg)
    output_path.write_text(svg, encoding="utf-8")
    print(f"Generated: {output_path.relative_to(ROOT)}")
    return 0


def render_catalog() -> str:
    width = 1320
    height = 620
    cols = 3
    cell_w = 400
    cell_h = 132
    start_x = 110
    start_y = 130
    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Fishbone badge catalog">',
        "<defs>",
        '<filter id="softShadow" x="-20%" y="-20%" width="140%" height="140%">',
        '<feDropShadow dx="0" dy="7" stdDeviation="8" flood-color="#16324F" flood-opacity="0.12"/>',
        "</filter>",
        "</defs>",
        f'<rect x="0" y="0" width="{width}" height="{height}" fill="{PALETTE["background"]}"/>',
        f'<text x="70" y="62" font-family="{FONT_STACK}" font-size="28" font-weight="700" fill="{PALETTE["navy"]}">Built-in Fishbone Badge Catalog</text>',
        f'<text x="70" y="94" font-family="{FONT_STACK}" font-size="15" fill="{PALETTE["muted_text"]}">These are hand-drawn SVG icons embedded in the renderer, not an external icon library.</text>',
    ]

    for index, (name, description) in enumerate(BADGES):
        col = index % cols
        row = index // cols
        x = start_x + col * cell_w
        y = start_y + row * cell_h
        cx = x + 44
        cy = y + 43
        parts.extend(
            [
                f'<rect x="{x - 26}" y="{y - 28}" width="342" height="100" rx="10" fill="#F8FBFF" stroke="{PALETTE["soft_blue"]}" stroke-width="1.5" filter="url(#softShadow)"/>',
                f'<circle cx="{cx}" cy="{cy}" r="34" fill="#FFFFFF" stroke="{PALETTE["light_blue"]}" stroke-width="2"/>',
                render_icon(name, cx, cy),
                f'<text x="{x + 98}" y="{y + 31}" font-family="{FONT_STACK}" font-size="20" font-weight="700" fill="{PALETTE["navy"]}">{name}</text>',
                f'<text x="{x + 98}" y="{y + 56}" font-family="{FONT_STACK}" font-size="13" fill="{PALETTE["muted_text"]}">{description}</text>',
            ]
        )

    parts.append("</svg>")
    return "\n".join(parts)


if __name__ == "__main__":
    raise SystemExit(main())
