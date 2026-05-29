"""Shared text measurement helpers for SVG renderers."""

from __future__ import annotations

import re
import unicodedata


def is_wide_char(char: str) -> bool:
    return unicodedata.east_asian_width(char) in {"F", "W"}


def visual_len(text: str) -> int:
    return sum(2 if is_wide_char(char) else 1 for char in text)


def chars_for_width(width: float, font_size: float, latin_factor: float = 0.52, minimum: int = 4) -> int:
    return max(minimum, int(width / (font_size * latin_factor)))


def estimate_text_width(text: str, font_size: float) -> float:
    width = 0.0
    for char in text:
        if is_wide_char(char):
            width += font_size
        elif char.isupper():
            width += font_size * 0.62
        elif char in {" ", "-", "/", "|"}:
            width += font_size * 0.35
        elif char.isdigit():
            width += font_size * 0.56
        else:
            width += font_size * 0.54
    return width


def clean_inline_text(value: object) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def wrap_text(text: str, max_chars: int, max_lines: int | None = None, punctuation_overflow: int = 0) -> list[str]:
    clean = clean_inline_text(text)
    if not clean:
        return [""]
    max_chars = max(1, max_chars)
    has_wide = any(is_wide_char(char) for char in clean)
    units = list(clean) if has_wide else clean.split()
    if not units:
        return [""]

    lines: list[str] = []
    current = ""
    for unit in units:
        sep = "" if has_wide else " "
        candidate = unit if not current else current + sep + unit
        if visual_len(candidate) <= max_chars:
            current = candidate
            continue
        if current:
            lines.append(current)
        if visual_len(unit) > max_chars:
            chunks = split_long_text(unit, max_chars)
            lines.extend(chunks[:-1])
            current = chunks[-1]
        else:
            current = unit

    if current:
        lines.append(current)

    lines = keep_leading_punctuation_with_previous_line(lines, max_chars + punctuation_overflow)

    if max_lines is not None and len(lines) > max_lines:
        lines = lines[:max_lines]
        source = clean if max_lines == 1 else lines[-1]
        lines[-1] = force_ellipsis(source, max_chars)
    return lines or [clean]


LEADING_PUNCTUATION = set("，。！？；：、,.!?;:")


def keep_leading_punctuation_with_previous_line(lines: list[str], max_chars: int) -> list[str]:
    fixed: list[str] = []
    for line in lines:
        while fixed and line and line[0] in LEADING_PUNCTUATION and visual_len(fixed[-1] + line[0]) <= max_chars:
            fixed[-1] += line[0]
            line = line[1:]
        if line:
            fixed.append(line)
    return fixed


def split_long_text(text: str, max_chars: int) -> list[str]:
    lines: list[str] = []
    current = ""
    current_len = 0
    for char in text:
        char_len = visual_len(char)
        if current and current_len + char_len > max_chars:
            if char in LEADING_PUNCTUATION:
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
    return lines or [text]


def truncate_text(text: str, max_chars: int) -> str:
    clean = clean_inline_text(text)
    if visual_len(clean) <= max_chars:
        return clean
    if max_chars <= 3:
        return "..."
    output = ""
    length = 0
    for char in clean:
        char_len = visual_len(char)
        if length + char_len > max_chars - 3:
            break
        output += char
        length += char_len
    return output.rstrip() + "..."


def force_ellipsis(text: str, max_chars: int) -> str:
    clean = clean_inline_text(text)
    if max_chars <= 3:
        return "..."
    output = ""
    length = 0
    for char in clean:
        char_len = visual_len(char)
        if length + char_len > max_chars - 3:
            break
        output += char
        length += char_len
    return output.rstrip() + "..."
