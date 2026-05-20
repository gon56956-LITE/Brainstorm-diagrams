#!/usr/bin/env python3
"""Export a work/fishbone/ SVG to PNG using the bundled Python runtime."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

from PIL import Image, ImageColor, ImageDraw, ImageFont


ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT / "work" / "fishbone"
SAFE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
NUMBER_RE = re.compile(r"-?(?:\d+(?:\.\d+)?|\.\d+)")
PATH_TOKEN_RE = re.compile(r"[MLHVCSQTAZmlhvcsqtaz]|-?(?:\d+(?:\.\d+)?|\.\d+)")
STYLE_ATTRS = ("fill", "stroke", "stroke-width", "font-family", "font-size", "font-weight")
Transform = tuple[float, float, float]
ANTIALIAS_FACTOR = 2

SOLID_PAINTS = {
    "url(#topCardGradient)": "#174B86",
    "url(#bottomCardGradient)": "#C9DFF2",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export work/fishbone/<name>.svg to work/fishbone/<name>.png.")
    parser.add_argument("name", help="Diagram name, such as my-analysis")
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
            "start with a letter or number; maximum length is 64. Example: my-analysis",
            file=sys.stderr,
        )
        return None
    return name


def export_svg_to_png(svg_path: Path, png_path: Path, *, scale: float) -> None:
    root = ET.parse(svg_path).getroot()
    width = int(float(root.attrib["width"]))
    height = int(float(root.attrib["height"]))
    render_scale = scale * ANTIALIAS_FACTOR
    target_size = (round(width * scale), round(height * scale))
    image = Image.new("RGB", (round(width * render_scale), round(height * render_scale)), "#FFFFFF")
    draw = ImageDraw.Draw(image)
    render_children(draw, image, root, render_scale)
    if ANTIALIAS_FACTOR > 1:
        image = image.resize(target_size, Image.Resampling.LANCZOS)
    png_path.parent.mkdir(parents=True, exist_ok=True)
    image.save(png_path)


def render_children(
    draw: ImageDraw.ImageDraw,
    image: Image.Image,
    element: ET.Element,
    scale: float,
    inherited_style: dict[str, str] | None = None,
    transform: Transform = (1.0, 0.0, 0.0),
) -> None:
    style = effective_style(element, inherited_style)
    transform = combine_transform(transform, parse_transform(element.attrib.get("transform", "")))
    for child in list(element):
        tag = local_name(child.tag)
        if tag in {"defs", "linearGradient", "stop", "filter", "feDropShadow"}:
            continue
        render_element(draw, image, child, scale, style, transform)
        render_children(draw, image, child, scale, style, transform)


def render_element(
    draw: ImageDraw.ImageDraw,
    image: Image.Image,
    element: ET.Element,
    scale: float,
    inherited_style: dict[str, str],
    transform: Transform,
) -> None:
    tag = local_name(element.tag)
    style = effective_style(element, inherited_style)
    transform = combine_transform(transform, parse_transform(element.attrib.get("transform", "")))
    if tag == "rect":
        draw_rect(draw, element, scale, style, transform)
    elif tag == "circle":
        draw_circle(draw, element, scale, style, transform)
    elif tag == "line":
        draw_line(draw, element, scale, style, transform)
    elif tag == "polyline":
        draw_polyline(draw, element, scale, style, transform, close=False)
    elif tag == "polygon":
        draw_polyline(draw, element, scale, style, transform, close=True)
    elif tag == "path":
        draw_path(draw, element, scale, style, transform)
    elif tag == "text":
        draw_text(draw, image, element, scale, style, transform)


def draw_rect(draw: ImageDraw.ImageDraw, element: ET.Element, scale: float, style: dict[str, str], transform: Transform) -> None:
    factor = transform[0]
    x, y = transform_point(number_attr(element, "x"), number_attr(element, "y"), scale, transform)
    w = number_attr(element, "width") * factor * scale
    h = number_attr(element, "height") * factor * scale
    rx = number_attr(element, "rx", 0) * factor * scale
    box = [x, y, x + w, y + h]
    fill = paint(style.get("fill"))
    outline = paint(style.get("stroke"))
    width = stroke_width(style, scale, transform)
    if rx > 0:
        draw.rounded_rectangle(box, radius=rx, fill=fill, outline=outline, width=width)
    else:
        draw.rectangle(box, fill=fill, outline=outline, width=width)


def draw_circle(draw: ImageDraw.ImageDraw, element: ET.Element, scale: float, style: dict[str, str], transform: Transform) -> None:
    cx, cy = transform_point(number_attr(element, "cx"), number_attr(element, "cy"), scale, transform)
    r = number_attr(element, "r") * transform[0] * scale
    box = [cx - r, cy - r, cx + r, cy + r]
    draw.ellipse(box, fill=paint(style.get("fill")), outline=paint(style.get("stroke")), width=stroke_width(style, scale, transform))


def draw_line(draw: ImageDraw.ImageDraw, element: ET.Element, scale: float, style: dict[str, str], transform: Transform) -> None:
    points = [
        transform_point(number_attr(element, "x1"), number_attr(element, "y1"), scale, transform),
        transform_point(number_attr(element, "x2"), number_attr(element, "y2"), scale, transform),
    ]
    draw.line(points, fill=paint(style.get("stroke")) or "#000000", width=stroke_width(style, scale, transform))


def draw_polyline(draw: ImageDraw.ImageDraw, element: ET.Element, scale: float, style: dict[str, str], transform: Transform, *, close: bool) -> None:
    points = parse_points(element.attrib.get("points", ""), scale, transform)
    if not points:
        return
    fill = paint(style.get("fill"))
    stroke = paint(style.get("stroke"))
    width = stroke_width(style, scale, transform)
    if close:
        if fill:
            draw.polygon(points, fill=fill)
        if stroke:
            draw.line(points + [points[0]], fill=stroke, width=width)
    else:
        draw.line(points, fill=stroke or fill or "#000000", width=width)


def draw_path(draw: ImageDraw.ImageDraw, element: ET.Element, scale: float, style: dict[str, str], transform: Transform) -> None:
    points = path_points(element.attrib.get("d", ""), scale, transform)
    if len(points) < 2:
        return
    fill = paint(style.get("fill"))
    stroke = paint(style.get("stroke"))
    width = stroke_width(style, scale, transform)
    if fill:
        draw.polygon(points, fill=fill)
    if stroke:
        draw.line(points, fill=stroke, width=width)


def draw_text(draw: ImageDraw.ImageDraw, image: Image.Image, element: ET.Element, scale: float, style: dict[str, str], transform: Transform) -> None:
    runs = text_runs(element, style, scale)
    if not runs:
        return
    x, y = transform_point(number_attr(element, "x"), number_attr(element, "y"), scale, transform)
    text_anchor = baseline_anchor(element.attrib.get("text-anchor", "start"))
    rotation = parse_rotate(element.attrib.get("transform", ""))
    if rotation is None:
        draw_text_runs_with_baseline(draw, (x, y), runs, anchor=text_anchor)
        return
    angle, cx, cy = rotation
    overlay = Image.new("RGBA", image.size, (255, 255, 255, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    draw_text_runs_with_baseline(overlay_draw, (x, y), runs, anchor=text_anchor)
    rotated = overlay.rotate(angle, center=(cx * scale, cy * scale), resample=Image.Resampling.BICUBIC)
    image.paste(Image.alpha_composite(image.convert("RGBA"), rotated).convert("RGB"))


def path_points(path_data: str, scale: float, transform: Transform = (1.0, 0.0, 0.0)) -> list[tuple[float, float]]:
    tokens = PATH_TOKEN_RE.findall(path_data.replace(",", " "))
    points: list[tuple[float, float]] = []
    index = 0
    command = ""
    current = (0.0, 0.0)
    start = (0.0, 0.0)

    def next_number() -> float:
        nonlocal index
        value = float(tokens[index])
        index += 1
        return value

    while index < len(tokens):
        token = tokens[index]
        if token.isalpha():
            command = token
            index += 1
            if command in {"Z", "z"}:
                points.append(transform_point(start[0], start[1], scale, transform))
                current = start
                continue

        relative = command.islower()
        upper = command.upper()
        if upper in {"M", "L"}:
            x, y = next_number(), next_number()
            if relative:
                x += current[0]
                y += current[1]
            current = (x, y)
            if upper == "M":
                start = current
            points.append(transform_point(x, y, scale, transform))
            command = "l" if relative else "L"
        elif upper == "H":
            x = next_number()
            if relative:
                x += current[0]
            current = (x, current[1])
            points.append(transform_point(current[0], current[1], scale, transform))
        elif upper == "V":
            y = next_number()
            if relative:
                y += current[1]
            current = (current[0], y)
            points.append(transform_point(current[0], current[1], scale, transform))
        elif upper == "C":
            c1 = read_point(next_number, current, relative)
            c2 = read_point(next_number, current, relative)
            end = read_point(next_number, current, relative)
            points.extend(sample_cubic(current, c1, c2, end, scale, transform))
            current = end
        elif upper == "S":
            c1 = current
            c2 = read_point(next_number, current, relative)
            end = read_point(next_number, current, relative)
            points.extend(sample_cubic(current, c1, c2, end, scale, transform))
            current = end
        elif upper == "Q":
            control = read_point(next_number, current, relative)
            end = read_point(next_number, current, relative)
            points.extend(sample_quadratic(current, control, end, scale, transform))
            current = end
        elif upper == "T":
            end = read_point(next_number, current, relative)
            points.extend(sample_quadratic(current, current, end, scale, transform))
            current = end
        elif upper == "A":
            _rx = next_number()
            _ry = next_number()
            _rotation = next_number()
            _large_arc = next_number()
            _sweep = next_number()
            x, y = next_number(), next_number()
            if relative:
                x += current[0]
                y += current[1]
            current = (x, y)
            points.append(transform_point(x, y, scale, transform))
        else:
            break
    return points


def read_point(next_number, current: tuple[float, float], relative: bool) -> tuple[float, float]:
    x, y = next_number(), next_number()
    if relative:
        return current[0] + x, current[1] + y
    return x, y


def sample_cubic(
    start: tuple[float, float],
    c1: tuple[float, float],
    c2: tuple[float, float],
    end: tuple[float, float],
    scale: float,
    transform: Transform = (1.0, 0.0, 0.0),
) -> list[tuple[float, float]]:
    samples = []
    for step in range(1, 13):
        t = step / 12
        x = (1 - t) ** 3 * start[0] + 3 * (1 - t) ** 2 * t * c1[0] + 3 * (1 - t) * t**2 * c2[0] + t**3 * end[0]
        y = (1 - t) ** 3 * start[1] + 3 * (1 - t) ** 2 * t * c1[1] + 3 * (1 - t) * t**2 * c2[1] + t**3 * end[1]
        samples.append(transform_point(x, y, scale, transform))
    return samples


def sample_quadratic(
    start: tuple[float, float],
    control: tuple[float, float],
    end: tuple[float, float],
    scale: float,
    transform: Transform = (1.0, 0.0, 0.0),
) -> list[tuple[float, float]]:
    samples = []
    for step in range(1, 13):
        t = step / 12
        x = (1 - t) ** 2 * start[0] + 2 * (1 - t) * t * control[0] + t**2 * end[0]
        y = (1 - t) ** 2 * start[1] + 2 * (1 - t) * t * control[1] + t**2 * end[1]
        samples.append(transform_point(x, y, scale, transform))
    return samples


def parse_points(value: str, scale: float, transform: Transform = (1.0, 0.0, 0.0)) -> list[tuple[float, float]]:
    numbers = [float(item) for item in NUMBER_RE.findall(value)]
    return [transform_point(numbers[index], numbers[index + 1], scale, transform) for index in range(0, len(numbers) - 1, 2)]


def number_attr(element: ET.Element, name: str, default: float = 0) -> float:
    value = element.attrib.get(name)
    if value is None:
        return default
    return float(value)


def stroke_width(style: dict[str, str], scale: float, transform: Transform = (1.0, 0.0, 0.0)) -> int:
    return max(1, round(float(style.get("stroke-width", "1")) * transform[0] * scale))


def effective_style(element: ET.Element, inherited_style: dict[str, str] | None) -> dict[str, str]:
    style = dict(inherited_style or {})
    for attr in STYLE_ATTRS:
        if attr in element.attrib:
            style[attr] = element.attrib[attr]
    return style


def parse_transform(value: str) -> Transform:
    factor = 1.0
    tx = 0.0
    ty = 0.0
    for name, args in re.findall(r"(translate|scale)\(([^)]*)\)", value):
        numbers = [float(item) for item in NUMBER_RE.findall(args)]
        if name == "translate" and numbers:
            tx += numbers[0]
            ty += numbers[1] if len(numbers) > 1 else 0.0
        elif name == "scale" and numbers:
            factor *= numbers[0]
    return factor, tx, ty


def parse_rotate(value: str) -> tuple[float, float, float] | None:
    match = re.search(r"rotate\(([^)]*)\)", value)
    if not match:
        return None
    numbers = [float(item) for item in NUMBER_RE.findall(match.group(1))]
    if not numbers:
        return None
    angle = numbers[0]
    cx = numbers[1] if len(numbers) > 2 else 0.0
    cy = numbers[2] if len(numbers) > 2 else 0.0
    return angle, cx, cy


def combine_transform(parent: Transform, child: Transform) -> Transform:
    parent_factor, parent_tx, parent_ty = parent
    child_factor, child_tx, child_ty = child
    return parent_factor * child_factor, parent_tx + parent_factor * child_tx, parent_ty + parent_factor * child_ty


def transform_point(x: float, y: float, scale: float, transform: Transform) -> tuple[float, float]:
    factor, tx, ty = transform
    return ((x * factor + tx) * scale, (y * factor + ty) * scale)


def paint(value: str | None) -> str | None:
    if value is None or value == "none":
        return None
    value = SOLID_PAINTS.get(value, value)
    if value.startswith("#"):
        return value
    try:
        return ImageColor.getrgb(value)
    except ValueError:
        return "#000000"


def text_runs(element: ET.Element, base_style: dict[str, str], scale: float) -> list[dict[str, object]]:
    runs: list[dict[str, object]] = []

    def append_run(text: str | None, run_style: dict[str, str]) -> None:
        if not text:
            return
        font_size = int(float(run_style.get("font-size", "16")) * scale)
        font_weight = run_style.get("font-weight", "")
        font_family = run_style.get("font-family", "")
        font = load_font(font_size, bold=is_bold_weight(font_weight), text=text, font_family=font_family)
        runs.append({"text": text, "font": font, "fill": paint(run_style.get("fill")) or "#000000"})

    append_run(element.text, base_style)
    for child in list(element):
        if local_name(child.tag) != "tspan":
            continue
        child_style = effective_style(child, base_style)
        append_run(child.text, child_style)
        append_run(child.tail, base_style)
    return runs


def draw_text_runs_with_baseline(draw: ImageDraw.ImageDraw, xy: tuple[float, float], runs: list[dict[str, object]], *, anchor: str) -> None:
    x, y = xy
    total_width = sum(text_width(draw, str(run["text"]), run["font"]) for run in runs)
    if anchor == "ms":
        x -= total_width / 2
    elif anchor == "rs":
        x -= total_width
    for run in runs:
        text = str(run["text"])
        font = run["font"]
        draw_text_with_baseline(draw, (x, y), text, font=font, fill=str(run["fill"]), anchor="ls")
        x += text_width(draw, text, font)


def text_width(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont) -> float:
    try:
        return float(draw.textlength(text, font=font))
    except AttributeError:
        bbox = draw.textbbox((0, 0), text, font=font)
        return float(bbox[2] - bbox[0])


def load_font(
    size: int,
    *,
    bold: bool,
    text: str = "",
    font_family: str = "",
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    families = [family.strip().strip("'\"").lower() for family in font_family.split(",") if family.strip()]
    wants_cjk = contains_cjk(text)
    family_names: list[str] = []
    if wants_cjk:
        family_names.extend(["microsoft yahei", "noto sans cjk sc", "arial"])
    family_names.extend(families or ["arial", "microsoft yahei"])
    if "microsoft yahei" not in family_names:
        family_names.append("microsoft yahei")
    font_names = font_file_candidates(family_names, bold)
    font_dirs = [Path(r"C:\Windows\Fonts")]
    for font_dir in font_dirs:
        for name in font_names:
            path = font_dir / name
            if path.exists():
                return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


def font_file_candidates(families: list[str], bold: bool) -> list[str]:
    candidates: list[str] = []
    for family in families:
        if family in {"arial", "helvetica", "sans-serif"}:
            candidates.append("arialbd.ttf" if bold else "arial.ttf")
        elif family in {"microsoft yahei", "yahei", "微软雅黑"}:
            candidates.append("msyhbd.ttc" if bold else "msyh.ttc")
        elif family in {"noto sans cjk sc", "noto sans sc"}:
            candidates.append("NotoSansCJK-Regular.ttc")
    candidates.extend(["arialbd.ttf" if bold else "arial.ttf", "msyhbd.ttc" if bold else "msyh.ttc"])
    return list(dict.fromkeys(candidates))


def baseline_anchor(text_anchor: str) -> str:
    if text_anchor == "middle":
        return "ms"
    if text_anchor == "end":
        return "rs"
    return "ls"


def draw_text_with_baseline(
    draw: ImageDraw.ImageDraw,
    xy: tuple[float, float],
    text: str,
    *,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    fill: str,
    anchor: str,
) -> None:
    try:
        draw.text(xy, text, font=font, fill=fill, anchor=anchor)
    except (TypeError, ValueError):
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_h = bbox[3] - bbox[1]
        x, y = xy
        if anchor == "ms":
            x -= text_w / 2
        elif anchor == "rs":
            x -= text_w
        draw.text((x, y - text_h), text, font=font, fill=fill)


def is_bold_weight(value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"bold", "bolder"}:
        return True
    try:
        return int(float(normalized)) >= 600
    except ValueError:
        return False


def contains_cjk(text: str) -> bool:
    return any("\u4e00" <= char <= "\u9fff" for char in text)


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


if __name__ == "__main__":
    raise SystemExit(main())
