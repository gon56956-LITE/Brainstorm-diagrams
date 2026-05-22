#!/usr/bin/env python3
"""Local HTML editor for brainstorm diagrams."""

from __future__ import annotations

import argparse
import html
import json
import mimetypes
import os
import re
import subprocess
import sys
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, quote, urlparse

from generate_diagram import parse_structured_markdown


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
GENERATE = ROOT / "scripts" / "generate_diagram.py"
EXPORT_FISHBONE = ROOT / "scripts" / "export_png.py"
EXPORT_FAULT_TREE = ROOT / "scripts" / "export_fault_tree_png.py"
EXPORT_EXCLUSION_TREE = ROOT / "scripts" / "export_exclusion_tree_png.py"
EXPORT_TWO_BY_TWO = ROOT / "scripts" / "export_two_by_two_matrix_png.py"
EXPORT_ROADMAP = ROOT / "scripts" / "export_roadmap_timeline_png.py"
EXPORT_FMEA = ROOT / "scripts" / "export_fmea_table_png.py"
PYTHON = Path(sys.executable)
SAFE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")
PORT_FALLBACK_ATTEMPTS = 10

DIAGRAMS = {
    "fishbone": {
        "label": "Fishbone",
        "work": ROOT / "work" / "fishbone",
        "template": TEMPLATES / "fishbone.template.json",
        "export": EXPORT_FISHBONE,
    },
    "fault_tree": {
        "label": "Fault Tree",
        "work": ROOT / "work" / "fault-tree",
        "template": TEMPLATES / "fault-tree.template.json",
        "export": EXPORT_FAULT_TREE,
    },
    "exclusion_tree": {
        "label": "Sequential Exclusion Tree",
        "work": ROOT / "work" / "exclusion-tree",
        "template": TEMPLATES / "exclusion-tree.template.json",
        "export": EXPORT_EXCLUSION_TREE,
    },
    "two_by_two_matrix": {
        "label": "Two-by-Two Matrix",
        "work": ROOT / "work" / "two-by-two-matrix",
        "template": TEMPLATES / "two-by-two-matrix.template.json",
        "export": EXPORT_TWO_BY_TWO,
    },
    "roadmap_timeline": {
        "label": "Roadmap Timeline",
        "work": ROOT / "work" / "roadmap-timeline",
        "template": TEMPLATES / "roadmap-timeline.template.json",
        "export": EXPORT_ROADMAP,
    },
    "fmea_table": {
        "label": "FMEA Table",
        "work": ROOT / "work" / "fmea-table",
        "template": TEMPLATES / "fmea-table.template.json",
        "export": EXPORT_FMEA,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the local brainstorm diagram HTML editor.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Preferred port to bind (default: 8765)")
    parser.add_argument("--no-open", action="store_true", help="Do not open the browser automatically")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server, actual_port = bind_server(args.host, args.port)
    url = f"http://{args.host}:{actual_port}/"
    if args.port != 0 and actual_port != args.port:
        print(f"Requested port {args.port} was unavailable; using {actual_port}.")
    print(f"Diagram builder running at {url}")
    print("Press Ctrl+C to stop.")
    if not args.no_open:
        webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping diagram builder.")
    finally:
        server.server_close()
    return 0


def bind_server(host: str, preferred_port: int) -> tuple[ThreadingHTTPServer, int]:
    if preferred_port == 0:
        server = ThreadingHTTPServer((host, 0), DiagramBuilderHandler)
        return server, int(server.server_address[1])

    last_error: OSError | None = None
    final_port = min(65535, preferred_port + PORT_FALLBACK_ATTEMPTS - 1)
    for port in range(preferred_port, final_port + 1):
        try:
            server = ThreadingHTTPServer((host, port), DiagramBuilderHandler)
        except OSError as exc:
            last_error = exc
            continue
        return server, port
    raise OSError(f"Could not bind {host}:{preferred_port}-{final_port}") from last_error


class DiagramBuilderHandler(BaseHTTPRequestHandler):
    server_version = "DiagramBuilder/0.1"

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            if parsed.path == "/":
                self.send_html(INDEX_HTML)
            elif parsed.path == "/api/template":
                query = parse_qs(parsed.query)
                diagram_type = first_query_value(query, "diagram_type", "fishbone")
                self.send_json({"ok": True, "data": load_template(diagram_type)})
            elif parsed.path == "/api/load":
                query = parse_qs(parsed.query)
                diagram_type = first_query_value(query, "diagram_type", "fishbone")
                name = first_query_value(query, "name", "")
                self.send_json({"ok": True, "data": load_work_json(diagram_type, name)})
            elif parsed.path == "/api/svg":
                query = parse_qs(parsed.query)
                diagram_type = first_query_value(query, "diagram_type", "fishbone")
                name = first_query_value(query, "name", "")
                svg_path = work_path(diagram_type, name, ".svg")
                if not svg_path.exists():
                    raise ValueError(f"Missing SVG: {svg_path.relative_to(ROOT)}")
                self.send_text(svg_path.read_text(encoding="utf-8"), "image/svg+xml")
            elif parsed.path == "/api/svg-preview":
                query = parse_qs(parsed.query)
                diagram_type = first_query_value(query, "diagram_type", "fishbone")
                name = first_query_value(query, "name", "")
                zoom = parse_preview_zoom(first_query_value(query, "zoom", "1"))
                svg_path = work_path(diagram_type, name, ".svg")
                if not svg_path.exists():
                    raise ValueError(f"Missing SVG: {svg_path.relative_to(ROOT)}")
                self.send_html(render_svg_preview_html(diagram_type, name, zoom))
            elif parsed.path == "/api/png":
                query = parse_qs(parsed.query)
                diagram_type = first_query_value(query, "diagram_type", "fishbone")
                name = first_query_value(query, "name", "")
                png_path = work_path(diagram_type, name, ".png")
                if not png_path.exists():
                    raise ValueError(f"Missing PNG: {png_path.relative_to(ROOT)}")
                self.send_file(png_path)
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=400)

    def do_POST(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        try:
            payload = self.read_json_body()
            if parsed.path == "/api/save":
                diagram_type, name, data = request_model(payload)
                save_work_json(diagram_type, name, data)
                self.send_json({"ok": True, "message": f"Saved {work_path(diagram_type, name, '.json').relative_to(ROOT)}"})
            elif parsed.path == "/api/render":
                diagram_type, name, data = request_model(payload)
                save_work_json(diagram_type, name, data)
                result = render_work(diagram_type, name)
                self.send_json({"ok": True, "message": result, "svg": read_work_svg(diagram_type, name)})
            elif parsed.path == "/api/parse-file":
                filename = str(payload.get("filename", ""))
                content = str(payload.get("content", ""))
                diagram_type, data = parse_uploaded_file(filename, content)
                self.send_json({"ok": True, "diagram_type": diagram_type, "data": data})
            elif parsed.path == "/api/export":
                diagram_type = canonical_diagram_type(payload.get("diagram_type", "fishbone"))
                name = validate_work_name(str(payload.get("name", "")))
                result = export_png(diagram_type, name)
                self.send_json({"ok": True, "message": result})
            elif parsed.path == "/api/open-folder":
                diagram_type = canonical_diagram_type(payload.get("diagram_type", "fishbone"))
                folder = diagram_config(diagram_type)["work"]
                folder.mkdir(parents=True, exist_ok=True)
                open_folder(folder)
                self.send_json({"ok": True, "message": f"Opened {folder.relative_to(ROOT)}"})
            else:
                self.send_error(HTTPStatus.NOT_FOUND, "Not found")
        except Exception as exc:
            self.send_json({"ok": False, "error": str(exc)}, status=400)

    def read_json_body(self) -> dict[str, Any]:
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length).decode("utf-8")
        data = json.loads(raw or "{}")
        if not isinstance(data, dict):
            raise ValueError("Request body must be a JSON object.")
        return data

    def send_json(self, data: dict[str, Any], *, status: int = 200) -> None:
        body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_html(self, html: str) -> None:
        self.send_text(html, "text/html; charset=utf-8")

    def send_text(self, text: str, content_type: str) -> None:
        body = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def send_file(self, path: Path) -> None:
        body = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", mimetypes.guess_type(path.name)[0] or "application/octet-stream")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, format: str, *args: Any) -> None:
        print(f"{self.address_string()} - {format % args}")


def first_query_value(query: dict[str, list[str]], key: str, default: str) -> str:
    values = query.get(key)
    return values[0] if values else default


def parse_preview_zoom(value: str) -> float:
    try:
        zoom = float(value)
    except ValueError:
        zoom = 1.0
    return max(0.5, min(2.0, zoom))


def render_svg_preview_html(diagram_type: str, name: str, zoom: float) -> str:
    svg_url = (
        f"/api/svg?diagram_type={quote(diagram_type)}"
        f"&name={quote(name)}"
        f"&v={quote(str(os.urandom(4).hex()))}"
    )
    image_width = round(zoom * 100)
    title = html.escape(f"{name}.svg")
    return f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    html, body {{
      margin: 0;
      min-height: 100%;
      background: #f7fafd;
      font-family: Arial, Helvetica, sans-serif;
    }}
    body {{
      padding: 0;
      overflow: auto;
    }}
    img {{
      display: block;
      width: {image_width}%;
      max-width: none;
      height: auto;
      background: #fff;
    }}
  </style>
</head>
<body>
  <img src="{html.escape(svg_url, quote=True)}" alt="{title}">
</body>
</html>
"""


def request_model(payload: dict[str, Any]) -> tuple[str, str, dict[str, Any]]:
    diagram_type = canonical_diagram_type(payload.get("diagram_type", "fishbone"))
    name = validate_work_name(str(payload.get("name", "")))
    data = payload.get("data")
    if not isinstance(data, dict):
        raise ValueError("Missing diagram data.")
    data["diagram_type"] = diagram_type
    return diagram_type, name, data


def canonical_diagram_type(value: Any) -> str:
    diagram_type = str(value).strip().lower().replace("-", "_").replace(" ", "_")
    if diagram_type not in DIAGRAMS:
        raise ValueError("diagram_type must be fishbone, fault_tree, exclusion_tree, two_by_two_matrix, roadmap_timeline, or fmea_table.")
    return diagram_type


def validate_work_name(value: str) -> str:
    name = value.strip()
    if "\\" in name or "/" in name or Path(name).is_absolute():
        raise ValueError("Diagram name must be a simple file name, not a path.")
    if not SAFE_NAME_PATTERN.fullmatch(name):
        raise ValueError(
            "Diagram name may use only lowercase letters, numbers, hyphen, and underscore; "
            "start with a letter or number; maximum length is 64."
        )
    return name


def diagram_config(diagram_type: str) -> dict[str, Path | str]:
    return DIAGRAMS[canonical_diagram_type(diagram_type)]


def load_template(diagram_type: str) -> dict[str, Any]:
    template_path = diagram_config(diagram_type)["template"]
    data = json.loads(Path(template_path).read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Template {Path(template_path).name} must be a JSON object.")
    return data


def work_path(diagram_type: str, name: str, suffix: str) -> Path:
    folder = Path(diagram_config(diagram_type)["work"])
    stem = validate_work_name(name)
    return folder / f"{stem}{suffix}"


def load_work_json(diagram_type: str, name: str) -> dict[str, Any]:
    path = work_path(diagram_type, name, ".json")
    if not path.exists():
        raise ValueError(f"Missing work JSON: {path.relative_to(ROOT)}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.relative_to(ROOT)} must contain a JSON object.")
    return data


def parse_uploaded_file(filename: str, content: str) -> tuple[str, dict[str, Any]]:
    suffix = Path(filename).suffix.lower()
    text = content.lstrip("\ufeff")
    if suffix == ".json":
        data = json.loads(text)
    elif suffix in {".md", ".markdown"}:
        data = parse_structured_markdown(text)
    else:
        raise ValueError("Load File supports .json, .md, and .markdown files.")
    if not isinstance(data, dict):
        raise ValueError("Loaded diagram file must contain a JSON object or structured Markdown diagram.")
    diagram_type = canonical_diagram_type(data.get("diagram_type", "fishbone"))
    data["diagram_type"] = diagram_type
    return diagram_type, data


def save_work_json(diagram_type: str, name: str, data: dict[str, Any]) -> Path:
    path = work_path(diagram_type, name, ".json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def render_work(diagram_type: str, name: str) -> str:
    input_path = work_path(diagram_type, name, ".json")
    output_path = work_path(diagram_type, name, ".svg")
    result = subprocess.run(
        [str(PYTHON), str(GENERATE), str(input_path), str(output_path)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or "Render failed.")
    return (result.stdout or "").strip() or f"Rendered {output_path.relative_to(ROOT)}"


def read_work_svg(diagram_type: str, name: str) -> str:
    return work_path(diagram_type, name, ".svg").read_text(encoding="utf-8")


def export_png(diagram_type: str, name: str) -> str:
    config = diagram_config(diagram_type)
    export_script = Path(config["export"])
    result = subprocess.run(
        [str(PYTHON), str(export_script), validate_work_name(name)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise ValueError(result.stderr.strip() or "PNG export failed.")
    return (result.stdout or "").strip()


def open_folder(folder: Path) -> None:
    if os.name == "nt":
        subprocess.Popen(["explorer", str(folder)])
    else:
        webbrowser.open(folder.as_uri())


INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Brainstorm Diagram Builder</title>
  <style>
    :root {
      --navy: #0b2e63;
      --blue: #2f6fb6;
      --line: #d8e2ee;
      --soft: #f4f8fc;
      --panel: #ffffff;
      --text: #1c2f45;
      --muted: #63758a;
      --danger: #b42318;
      --ok: #167c4a;
    }
    * { box-sizing: border-box; }
    body {
      margin: 0;
      font-family: Arial, Helvetica, "Microsoft YaHei", sans-serif;
      color: var(--text);
      background: #eef4fb;
    }
    header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 16px;
      padding: 16px 22px;
      background: var(--navy);
      color: #fff;
    }
    h1 { margin: 0; font-size: 22px; letter-spacing: 0; }
    header span { color: #dbeaff; font-size: 13px; }
    main {
      display: grid;
      grid-template-columns: minmax(500px, 0.82fr) minmax(640px, 1.18fr);
      gap: 14px;
      padding: 14px;
      height: calc(100vh - 64px);
    }
    .panel {
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      min-height: 0;
      overflow: auto;
    }
    .editor { padding: 16px; }
    .preview {
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .preview-toolbar {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 12px;
      padding: 12px 14px;
      border-bottom: 1px solid var(--line);
      background: #f8fbff;
    }
    .preview-actions {
      display: flex;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
      justify-content: flex-end;
    }
    .zoom-controls {
      display: inline-flex;
      align-items: center;
      gap: 4px;
      padding: 3px;
      border: 1px solid #c8d7e8;
      border-radius: 7px;
      background: #fff;
    }
    .zoom-controls button {
      min-width: 34px;
      padding: 5px 8px;
    }
    #zoomLabel {
      min-width: 48px;
      text-align: center;
      color: var(--navy);
      font-size: 13px;
      font-weight: 700;
    }
    #previewBox {
      flex: 1;
      overflow: auto;
      padding: 14px;
      background: #f7fafd;
    }
    #previewBox iframe {
      width: 100%;
      height: 100%;
      min-height: 760px;
      background: #fff;
      border: 1px solid var(--line);
      display: block;
    }
    .row {
      display: grid;
      grid-template-columns: 160px 1fr;
      gap: 10px;
      align-items: center;
      margin-bottom: 10px;
    }
    label {
      font-weight: 700;
      font-size: 13px;
      color: var(--navy);
    }
    input, select, textarea {
      width: 100%;
      border: 1px solid #b7c7da;
      border-radius: 6px;
      padding: 8px 9px;
      font: inherit;
      color: var(--text);
      background: #fff;
    }
    textarea { min-height: 72px; resize: vertical; }
    .toolbar {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin: 12px 0 16px;
    }
    .main-toolbar {
      flex-wrap: nowrap;
      gap: 6px;
      overflow-x: auto;
      padding-bottom: 2px;
    }
    button {
      border: 1px solid #a9bfda;
      border-radius: 6px;
      padding: 7px 9px;
      background: #fff;
      color: var(--navy);
      font-weight: 700;
      font-size: 13px;
      cursor: pointer;
      white-space: nowrap;
    }
    button.primary {
      background: var(--blue);
      border-color: var(--blue);
      color: #fff;
    }
    button:disabled {
      opacity: .45;
      cursor: not-allowed;
    }
    .recent-row {
      display: grid;
      grid-template-columns: 72px 1fr auto;
      gap: 8px;
      align-items: center;
      margin: 0 0 14px;
    }
    .form-errors {
      display: none;
      margin: 8px 0 12px;
      padding: 10px 12px;
      border: 1px solid #f0b4ae;
      border-radius: 6px;
      background: #fff7f6;
      color: var(--danger);
      font-size: 13px;
      line-height: 1.45;
    }
    .form-errors.has-errors {
      display: block;
    }
    .form-errors.has-warnings {
      display: block;
      border-color: #f3c66d;
      background: #fff9eb;
      color: #835800;
    }
    .form-errors ul {
      margin: 4px 0 0 18px;
      padding: 0;
    }
    .modal-backdrop {
      position: fixed;
      inset: 0;
      display: none;
      align-items: center;
      justify-content: center;
      padding: 20px;
      background: rgba(10, 30, 55, .32);
      z-index: 20;
    }
    .modal-backdrop.open {
      display: flex;
    }
    .modal {
      width: min(420px, 100%);
      padding: 18px;
      border-radius: 8px;
      border: 1px solid #b8cbe1;
      background: #fff;
      box-shadow: 0 18px 45px rgba(17, 45, 78, .25);
    }
    .modal h2 {
      margin-bottom: 8px;
    }
    .modal p {
      margin: 0 0 14px;
      color: var(--muted);
      font-size: 13px;
      line-height: 1.45;
    }
    .modal-actions {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 8px;
    }
    .modal-actions button {
      min-height: 42px;
    }
    .modal-cancel {
      margin-top: 10px;
      width: 100%;
    }
    .help-modal {
      width: min(680px, 100%);
    }
    .help-section {
      margin-top: 14px;
      padding-top: 12px;
      border-top: 1px solid var(--line);
    }
    .help-section:first-of-type {
      margin-top: 0;
      padding-top: 0;
      border-top: 0;
    }
    .help-section h3 {
      margin-bottom: 6px;
    }
    .help-section ul {
      margin: 0 0 0 18px;
      padding: 0;
      color: var(--text);
      font-size: 13px;
      line-height: 1.55;
    }
    .help-section li {
      margin: 3px 0;
    }
    .section {
      border-top: 1px solid var(--line);
      padding-top: 14px;
      margin-top: 14px;
    }
    .section-title {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 10px;
      margin-bottom: 10px;
    }
    h2, h3 {
      margin: 0;
      color: var(--navy);
      letter-spacing: 0;
    }
    h2 { font-size: 18px; }
    h3 { font-size: 15px; }
    .hint {
      padding: 10px 12px;
      border: 1px solid #cbd9ea;
      background: var(--soft);
      border-radius: 6px;
      color: var(--muted);
      font-size: 13px;
      margin: 8px 0 12px;
    }
    .item {
      border: 1px solid var(--line);
      border-radius: 8px;
      background: #fbfdff;
      padding: 12px;
      margin: 10px 0;
    }
    .item-head {
      display: flex;
      align-items: center;
      justify-content: space-between;
      gap: 8px;
      margin-bottom: 10px;
    }
    .inline {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 8px;
      margin: 8px 0;
    }
    .inline-3 {
      display: grid;
      grid-template-columns: 1fr 170px auto;
      gap: 8px;
      margin: 8px 0;
    }
    .matrix-item-row {
      display: grid;
      grid-template-columns: 64px minmax(160px, 1fr) 58px 58px auto;
      gap: 8px;
      align-items: center;
      margin: 8px 0;
    }
    .matrix-item-row input {
      min-width: 0;
    }
    .matrix-item-row .score-input {
      text-align: center;
      font-weight: 700;
    }
    .roadmap-row {
      display: grid;
      grid-template-columns: 64px minmax(130px, 1fr) 112px 112px 102px auto;
      gap: 8px;
      align-items: center;
      margin: 8px 0;
    }
    .roadmap-row input,
    .roadmap-row select {
      min-width: 0;
    }
    .roadmap-period-row {
      grid-template-columns: minmax(150px, 1fr) 132px 132px auto;
    }
    .roadmap-lane-row {
      grid-template-columns: 120px minmax(180px, 1fr) 132px auto;
    }
    .roadmap-checkbox {
      display: flex;
      align-items: center;
      gap: 8px;
      color: var(--text);
      font-size: 13px;
      font-weight: 700;
    }
    .roadmap-checkbox input {
      width: auto;
    }
    .roadmap-card-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .roadmap-card-grid input,
    .roadmap-card-grid select {
      min-width: 0;
    }
    .roadmap-field {
      min-width: 0;
    }
    .roadmap-field.full {
      grid-column: 1 / -1;
    }
    .fmea-project-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 10px;
    }
    .fmea-row-card {
      display: grid;
      gap: 10px;
    }
    .fmea-row-top {
      display: grid;
      grid-template-columns: 72px minmax(180px, 1fr) minmax(240px, 1.5fr);
      gap: 8px;
      align-items: end;
    }
    .fmea-row-meta {
      display: grid;
      grid-template-columns: minmax(150px, 1fr) 122px 146px;
      gap: 8px;
    }
    .fmea-score-strip {
      display: grid;
      grid-template-columns: repeat(3, 72px) 1fr;
      gap: 8px;
      align-items: end;
    }
    .fmea-text-grid {
      display: grid;
      grid-template-columns: repeat(2, minmax(0, 1fr));
      gap: 8px;
    }
    .fmea-field {
      display: grid;
      gap: 4px;
      min-width: 0;
    }
    .fmea-field label {
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
    }
    .fmea-field.full {
      grid-column: 1 / -1;
    }
    .fmea-field input,
    .fmea-field select,
    .fmea-field textarea {
      box-sizing: border-box;
      min-width: 0;
      width: 100%;
    }
    .fmea-score {
      text-align: center;
    }
    .fmea-rpn-preview {
      align-self: center;
      color: var(--navy);
      font-size: 13px;
      font-weight: 800;
      white-space: nowrap;
    }
    @media (max-width: 1350px) {
      .fmea-text-grid,
      .fmea-row-meta,
      .fmea-project-grid {
        grid-template-columns: 1fr;
      }
      .fmea-score-strip {
        grid-template-columns: repeat(3, 72px);
      }
    }
    .roadmap-field label {
      display: block;
      margin-bottom: 4px;
      color: var(--muted);
      font-size: 12px;
    }
    @media (max-width: 1250px) {
      .roadmap-card-grid {
        grid-template-columns: 1fr;
      }
    }
    .matrix-item-label {
      color: var(--muted);
      font-size: 12px;
      font-weight: 800;
      white-space: nowrap;
    }
    .nested {
      margin-left: 18px;
      padding-left: 12px;
      border-left: 3px solid #d7e6f6;
    }
    .fishbone-subcategory {
      margin: 12px 0 12px 18px;
      padding: 0;
      border: 1px solid #b8d2ef;
      border-left: 5px solid var(--blue);
      background: #f6fbff;
    }
    .subcategory-title {
      display: grid;
      grid-template-columns: 122px 1fr auto;
      gap: 8px;
      align-items: center;
      padding: 10px;
      border-bottom: 1px solid #d4e4f6;
      background: #eaf4ff;
      border-radius: 7px 7px 0 0;
    }
    .level-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-height: 30px;
      border-radius: 5px;
      background: var(--navy);
      color: #fff;
      font-size: 12px;
      font-weight: 700;
      white-space: nowrap;
    }
    .child-cause-area {
      margin: 10px 10px 10px 28px;
      padding: 10px 0 0 14px;
      border-left: 3px solid #a9c9eb;
    }
    .child-cause-title {
      margin-bottom: 8px;
      color: var(--muted);
      font-size: 12px;
      font-weight: 700;
      text-transform: uppercase;
    }
    .status {
      font-size: 13px;
      color: var(--muted);
      min-height: 20px;
    }
    .status.error { color: var(--danger); }
    .status.ok { color: var(--ok); }
    .empty {
      color: var(--muted);
      padding: 18px;
      text-align: center;
    }
    @media (max-width: 1050px) {
      main { grid-template-columns: 1fr; height: auto; }
      .preview { min-height: 560px; }
    }
  </style>
</head>
<body>
  <header>
    <div>
      <h1>Brainstorm Diagram Builder</h1>
      <span>Edit JSON-backed fishbone, fault-tree, exclusion-tree, two-by-two matrix, roadmap, and FMEA diagrams without touching Markdown.</span>
    </div>
  </header>
  <main>
    <section class="panel editor">
      <div class="row">
        <label for="diagramType">Diagram type</label>
        <select id="diagramType">
          <option value="fishbone">Fishbone</option>
          <option value="fault_tree">Fault Tree</option>
          <option value="exclusion_tree">Sequential Exclusion Tree</option>
          <option value="two_by_two_matrix">Two-by-Two Matrix</option>
          <option value="roadmap_timeline">Roadmap Timeline</option>
          <option value="fmea_table">FMEA Table</option>
        </select>
      </div>
      <div class="row">
        <label for="diagramName">Diagram name</label>
        <input id="diagramName" value="my-analysis" pattern="[a-z0-9][a-z0-9_-]{0,63}">
      </div>
      <div class="toolbar main-toolbar">
        <button id="newBtn" title="Start a new diagram from the selected template.">New</button>
        <button id="loadBtn" title="Open an existing .json or .md source file from your computer.">Load File</button>
        <button id="saveBtn" title="Save the editable JSON source into this skill's work folder.">Save JSON</button>
        <button id="saveAsBtn" title="Save a copy as .json or .md to a path you choose. This does not include SVG.">Save As</button>
        <button id="renderBtn" class="primary" title="Generate the SVG preview and save it into the work folder.">Render SVG</button>
        <button id="exportBtn" title="Export PNG from the latest rendered work-folder SVG.">Export PNG</button>
        <button id="openBtn" title="Open the work folder for the selected diagram type.">Work Folder</button>
        <button id="helpBtn" title="Show workflow, file type, and diagram limit guidance.">Help</button>
      </div>
      <div class="recent-row">
        <label for="recentSelect">Recent</label>
        <select id="recentSelect"></select>
        <button id="loadRecentBtn" title="Load a JSON source previously saved or rendered in this browser.">Load Recent</button>
      </div>
      <input id="fileInput" type="file" accept=".json,.md,.markdown,application/json,text/markdown,text/plain" hidden>
      <div id="status" class="status"></div>
      <div id="formErrors" class="form-errors"></div>
      <div id="formRoot"></div>
    </section>
    <section class="panel preview">
      <div class="preview-toolbar">
        <strong>SVG Preview</strong>
        <div class="preview-actions">
          <div class="zoom-controls" aria-label="Preview zoom controls">
            <button id="zoomOutBtn" type="button" title="Zoom out">-</button>
            <span id="zoomLabel">100%</span>
            <button id="zoomInBtn" type="button" title="Zoom in">+</button>
            <button id="zoomFitBtn" type="button" title="Fit to width">Fit</button>
          </div>
          <button id="openSvgBtn" type="button" title="Open the current rendered SVG as a standalone document.">Open SVG</button>
          <span id="previewMeta" class="status"></span>
        </div>
      </div>
      <div id="previewBox"><div class="empty">Click Render SVG to preview the diagram.</div></div>
    </section>
  </main>
  <div id="saveAsDialog" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="saveAsTitle">
    <div class="modal">
      <h2 id="saveAsTitle">Save As</h2>
      <p>Choose the source file format first. The save dialog will use the matching file extension automatically.</p>
      <div class="modal-actions">
        <button id="saveAsJsonBtn" type="button" title="Save an editable JSON source file.">JSON Source</button>
        <button id="saveAsMarkdownBtn" type="button" title="Save an editable Markdown source file.">Markdown Source</button>
      </div>
      <button id="saveAsCancelBtn" class="modal-cancel" type="button" title="Close without saving.">Cancel</button>
    </div>
  </div>
  <div id="helpDialog" class="modal-backdrop" role="dialog" aria-modal="true" aria-labelledby="helpTitle">
    <div class="modal help-modal">
      <h2 id="helpTitle">Help</h2>
      <div class="help-section">
        <h3>Workflow</h3>
        <ul>
          <li>Use New for a fresh template, or Load File to open an existing JSON or Markdown source.</li>
          <li>Edit the fields, then Save JSON to keep the source in the work folder.</li>
          <li>Use Render SVG to generate the preview and write the work-folder SVG.</li>
          <li>Use Export PNG after Render SVG when you need a shareable PNG image.</li>
          <li>Use Save As to save a separate JSON or Markdown source copy outside the work folder.</li>
          <li>Recent keeps the latest 12 work files. Saving the same diagram type and name updates one recent entry.</li>
          <li>When old exclusion-tree files are saved in Builder, hidden language, icon, and pass/fail fields are normalized to the current simplified model.</li>
        </ul>
      </div>
      <div class="help-section">
        <h3>File Types</h3>
        <ul>
          <li>JSON and Markdown are editable source files. They do not contain SVG artwork.</li>
          <li>SVG is generated by Render SVG and saved under the selected work folder.</li>
          <li>PNG is exported from the latest generated SVG.</li>
        </ul>
      </div>
      <div class="help-section">
        <h3>Diagram Limits</h3>
        <ul>
          <li>Fishbone: recommended 4-8 categories, up to 5 primary entries per category, up to 3 child causes per subcategory.</li>
          <li>Fault Tree: 1 top event, recommended 3-5 first-level intermediate events, up to 8 first-level intermediate events, up to 4 children per intermediate event, currently supports second-level intermediate events.</li>
          <li>Sequential Exclusion Tree: 1 target problem, recommended 3-6 check points on one main path, each check has one Yes path and one No cause card.</li>
          <li>Two-by-Two Matrix: one preset or custom axis pair, recommended 4-20 scored items, maximum 20. X and Y scores must be 1-5, and the Decision Table shows every item.</li>
          <li>Roadmap Timeline: choose swimlane roadmap or milestone timeline, keep title and goal visible, and use table/summary panels for review-ready detail.</li>
          <li>FMEA Table: use focused rows with S/O/D scores from 1-10. RPN is calculated from S × O × D, and the table can grow downward for dense content.</li>
          <li>Drafts below the recommended count can still render after confirmation, but may not be useful for review.</li>
        </ul>
      </div>
      <button id="helpCloseBtn" class="modal-cancel" type="button" title="Close help.">Close</button>
    </div>
  </div>
  <script>
    const LIMITS = {
      fishbone: { categories: 8, minCategories: 4, entries: 5, children: 3 },
      fault_tree: { first: 8, recommendedFirst: 5, minFirst: 3, children: 4, nestedChildren: 4 },
      exclusion_tree: { checks: 6, minChecks: 3 },
      two_by_two_matrix: { items: 20, minItems: 4 },
      roadmap_timeline: { minPeriods: 2, minLanes: 1, minInitiatives: 1, minMilestones: 1 },
      fmea_table: { rows: 12, minRows: 3, scoreMin: 1, scoreMax: 10 }
    };
    const TWO_BY_TWO_PRESET_TEMPLATES = {
      action_priority: {
        title: "Action Priority Matrix",
        items: [
          { id: "A1", name: "Automate weekly report", x_score: 2, y_score: 5 },
          { id: "A2", name: "Redesign approval workflow", x_score: 5, y_score: 5 },
          { id: "A3", name: "Standardize checklist", x_score: 1, y_score: 3 },
          { id: "A4", name: "Build custom dashboard", x_score: 5, y_score: 2 },
          { id: "A5", name: "Update training material", x_score: 2, y_score: 3 }
        ]
      },
      risk_benefit: {
        title: "Risk-Benefit Matrix",
        items: [
          { id: "O1", name: "Switch supplier", x_score: 4, y_score: 5 },
          { id: "O2", name: "Minor process update", x_score: 1, y_score: 2 },
          { id: "O3", name: "Add automated inspection", x_score: 3, y_score: 4 },
          { id: "O4", name: "Skip incoming validation", x_score: 5, y_score: 1 }
        ]
      },
      evidence_impact: {
        title: "Cause Screening Matrix",
        items: [
          { id: "C1", name: "Power module fault", x_score: 4, y_score: 5 },
          { id: "C2", name: "Firmware timing issue", x_score: 2, y_score: 5 },
          { id: "C3", name: "Connector contamination", x_score: 3, y_score: 4 },
          { id: "C4", name: "Operator handling variation", x_score: 4, y_score: 2 }
        ]
      },
      value_feasibility: {
        title: "Feature Screening Matrix",
        items: [
          { id: "F1", name: "Auto calibration", x_score: 4, y_score: 5 },
          { id: "F2", name: "AI optimization mode", x_score: 2, y_score: 5 },
          { id: "F3", name: "New color theme", x_score: 5, y_score: 2 },
          { id: "F4", name: "Legacy protocol support", x_score: 1, y_score: 1 }
        ]
      },
      urgency_importance: {
        title: "Urgency-Importance Matrix",
        items: [
          { id: "T1", name: "Prepare customer review", x_score: 5, y_score: 5 },
          { id: "T2", name: "Update template library", x_score: 2, y_score: 3 },
          { id: "T3", name: "Answer routine request", x_score: 4, y_score: 2 },
          { id: "T4", name: "Clean obsolete notes", x_score: 1, y_score: 1 }
        ]
      },
      custom: {
        title: "Custom Two-by-Two Matrix",
        x_axis: "X Dimension",
        y_axis: "Y Dimension",
        items: [
          { id: "I1", name: "Item one", x_score: 2, y_score: 5 },
          { id: "I2", name: "Item two", x_score: 5, y_score: 5 },
          { id: "I3", name: "Item three", x_score: 2, y_score: 2 },
          { id: "I4", name: "Item four", x_score: 5, y_score: 2 }
        ]
      }
    };
    const ROADMAP_PRESET_TEMPLATES = {
      swimlane_roadmap: {
        diagram_type: "roadmap_timeline",
        preset: "swimlane_roadmap",
        lane_type: "theme",
        title: "Roadmap / Timeline",
        goal: "Deliver value through coordinated roadmap execution.",
        language: "en",
        time_granularity: "quarter",
        time_periods: [
          { id: "2025Q2", label: "2025 Q2", subtitle: "Apr - Jun", start: "2025-04-01", end: "2025-06-30" },
          { id: "2025Q3", label: "2025 Q3", subtitle: "Jul - Sep", start: "2025-07-01", end: "2025-09-30" },
          { id: "2025Q4", label: "2025 Q4", subtitle: "Oct - Dec", start: "2025-10-01", end: "2025-12-31" },
          { id: "2026Q1", label: "2026 Q1", subtitle: "Jan - Mar", start: "2026-01-01", end: "2026-03-31" }
        ],
        lanes: [
          { id: "customer", name: "Customer Value", color: "blue" },
          { id: "platform", name: "Platform & Tech", color: "teal" },
          { id: "operations", name: "Operational Excellence", color: "purple" }
        ],
        initiatives: [
          { id: "R1", lane_id: "customer", name: "Improve Core Experience", start: "2025-04-15", end: "2025-06-30", owner: "Product", status: "in_progress" },
          { id: "R2", lane_id: "customer", name: "New Personalization", start: "2025-10-15", end: "2026-02-28", owner: "Data & AI", status: "planned" },
          { id: "R3", lane_id: "platform", name: "Cloud Migration", start: "2025-05-01", end: "2025-08-31", owner: "Platform", status: "in_progress" },
          { id: "R4", lane_id: "platform", name: "Data Platform v1", start: "2025-10-01", end: "2026-02-15", owner: "Data", status: "planned" },
          { id: "R5", lane_id: "operations", name: "Process Automation", start: "2025-04-15", end: "2025-08-15", owner: "Operations", status: "in_progress" },
          { id: "R6", lane_id: "operations", name: "Lean Initiative", start: "2025-10-15", end: "2026-01-31", owner: "Operations", status: "planned" }
        ],
        milestones: [
          { id: "M1", lane_id: "customer", name: "App 2.0 Launch", date: "2025-11-01", type: "launch" },
          { id: "M2", lane_id: "platform", name: "Architecture Review", date: "2025-09-15", type: "key_milestone" }
        ],
        decision_points: [
          { id: "D1", lane_id: "platform", name: "Go / No-Go", date: "2025-09-15", type: "decision" }
        ],
        notes: ["Timeline is subject to change based on dependencies and resource availability."],
        show_table: true,
        show_summary_panel: true
      },
      milestone_timeline: {
        diagram_type: "roadmap_timeline",
        preset: "milestone_timeline",
        title: "Milestone Timeline",
        goal: "Launch the next-generation product on time with quality.",
        language: "en",
        time_granularity: "month",
        milestones: [
          { id: "T1", name: "Project Kickoff", date: "2025-04-01", type: "start", owner: "PMO", status: "completed", output: "Define scope, team and plan" },
          { id: "T2", name: "Requirements Sign-off", date: "2025-05-15", type: "milestone", owner: "Product", status: "completed", output: "Finalize product requirements" },
          { id: "T3", name: "Design Review", date: "2025-06-30", type: "review", owner: "R&D", status: "completed", output: "Complete system design review" },
          { id: "T4", name: "Prototype Ready", date: "2025-08-15", type: "milestone", owner: "R&D", status: "planned", output: "Prototype build completed" },
          { id: "T5", name: "EVT Completion", date: "2025-10-31", type: "key_milestone", owner: "R&D", status: "planned", output: "Engineering validation test completed" },
          { id: "T6", name: "Market Launch", date: "2026-04-30", type: "launch", owner: "Product", status: "planned", output: "Official product launch" }
        ],
        phases: [
          { name: "Design Phase", start: "2025-04-01", end: "2025-06-30" },
          { name: "Validation Phase", start: "2025-07-01", end: "2025-12-31" },
          { name: "Launch Phase", start: "2026-01-01", end: "2026-04-30" }
        ],
        notes: ["Dependencies and risks are tracked separately."],
        show_detail_cards: true,
        show_table: true
      }
    };
    const RECENT_KEY = "brainstormDiagramBuilderRecent";
    const NAME_PATTERN = /^[a-z0-9][a-z0-9_-]{0,63}$/;
    let model = {};
    let previewZoom = 1;

    const $ = (id) => document.getElementById(id);
    const typeEl = $("diagramType");
    const nameEl = $("diagramName");
    const formRoot = $("formRoot");
    const statusEl = $("status");
    const formErrors = $("formErrors");
    const previewBox = $("previewBox");
    const previewMeta = $("previewMeta");
    const fileInput = $("fileInput");
    const recentSelect = $("recentSelect");
    const zoomLabel = $("zoomLabel");
    const saveAsDialog = $("saveAsDialog");
    const helpDialog = $("helpDialog");

    function setStatus(message, kind = "") {
      statusEl.textContent = message || "";
      statusEl.className = "status " + kind;
    }

    function safeName() {
      return nameEl.value.trim();
    }

    function currentType() {
      return typeEl.value;
    }

    function diagramTypeLabel(diagramType) {
      if (diagramType === "fault_tree") return "Fault Tree";
      if (diagramType === "exclusion_tree") return "Sequential Exclusion Tree";
      if (diagramType === "two_by_two_matrix") return "Two-by-Two Matrix";
      if (diagramType === "roadmap_timeline") return "Roadmap Timeline";
      return "Fishbone";
    }

    function validateName(value) {
      return NAME_PATTERN.test(value || "");
    }

    function readRecent() {
      try {
        const parsed = JSON.parse(localStorage.getItem(RECENT_KEY) || "[]");
        return Array.isArray(parsed) ? parsed : [];
      } catch (_error) {
        return [];
      }
    }

    function writeRecent(entries) {
      localStorage.setItem(RECENT_KEY, JSON.stringify(entries.slice(0, 12)));
    }

    function rememberRecent() {
      const name = safeName();
      if (!validateName(name)) return;
      const diagramType = currentType();
      const key = `${diagramType}:${name}`;
      const entries = readRecent().filter(item => item.key !== key);
      entries.unshift({ key, diagram_type: diagramType, name, saved_at: new Date().toISOString() });
      writeRecent(entries);
      refreshRecent();
    }

    function refreshRecent() {
      const entries = readRecent();
      recentSelect.innerHTML = "";
      if (!entries.length) {
        const option = document.createElement("option");
        option.value = "";
        option.textContent = "No recent work files yet";
        recentSelect.appendChild(option);
        $("loadRecentBtn").disabled = true;
        return;
      }
      $("loadRecentBtn").disabled = false;
      for (const entry of entries) {
        const option = document.createElement("option");
        option.value = JSON.stringify(entry);
        option.textContent = `[${diagramTypeLabel(entry.diagram_type)}] ${entry.name}`;
        recentSelect.appendChild(option);
      }
    }

    async function loadRecent() {
      if (!recentSelect.value) return;
      const entry = JSON.parse(recentSelect.value);
      typeEl.value = entry.diagram_type;
      nameEl.value = entry.name;
      const data = await api(`/api/load?diagram_type=${encodeURIComponent(entry.diagram_type)}&name=${encodeURIComponent(entry.name)}`);
      model = data.data;
      renderForm();
      await loadSvgIfExists();
      setStatus(`Loaded recent ${entry.name}.`, "ok");
    }

    function setPreviewZoom(value) {
      previewZoom = Math.max(0.5, Math.min(2, value));
      applyPreviewZoom();
    }

    function applyPreviewZoom() {
      zoomLabel.textContent = Math.round(previewZoom * 100) + "%";
      const frame = previewBox.querySelector("iframe");
      if (!frame) return;
      frame.src = previewFrameUrl();
    }

    function svgPreviewUrl(cacheBust = true) {
      const params = new URLSearchParams({
        diagram_type: currentType(),
        name: safeName()
      });
      if (cacheBust) params.set("v", String(Date.now()));
      return `/api/svg?${params.toString()}`;
    }

    function previewFrameUrl() {
      const params = new URLSearchParams({
        diagram_type: currentType(),
        name: safeName(),
        zoom: String(previewZoom),
        v: String(Date.now())
      });
      return `/api/svg-preview?${params.toString()}`;
    }

    function setPreviewFrame() {
      const frame = document.createElement("iframe");
      frame.className = "svg-preview-frame";
      frame.title = "SVG preview";
      frame.src = previewFrameUrl();
      previewBox.replaceChildren(frame);
    }

    function openSvgStandalone() {
      window.open(svgPreviewUrl(false), "_blank", "noopener");
    }

    function requireText(errors, label, value) {
      if (!String(value || "").trim()) errors.push(label + " is required.");
    }

    function collectValidationErrors() {
      const errors = [];
      if (!validateName(safeName())) {
        errors.push("Diagram name must use lowercase letters, numbers, hyphen, or underscore; max 64 characters.");
      }
      if (currentType() === "fishbone") {
        requireText(errors, "Topic", model.topic);
        const categories = Array.isArray(model.categories) ? model.categories : [];
        if (categories.length < 1) errors.push("Fishbone needs at least 1 category.");
        if (categories.length > LIMITS.fishbone.categories) errors.push(`Fishbone supports up to ${LIMITS.fishbone.categories} categories.`);
        categories.forEach((category, categoryIndex) => {
          requireText(errors, `Category ${categoryIndex + 1} name`, category.name_en || category.name);
          const items = Array.isArray(category.items) ? category.items : [];
          if (items.length > LIMITS.fishbone.entries) errors.push(`Category ${categoryIndex + 1} has more than ${LIMITS.fishbone.entries} primary entries.`);
          items.forEach((item, itemIndex) => {
            if (typeof item === "string") {
              requireText(errors, `Category ${categoryIndex + 1} cause ${itemIndex + 1}`, item);
            } else {
              requireText(errors, `Category ${categoryIndex + 1} subcategory ${itemIndex + 1}`, item.subcategory);
              const children = Array.isArray(item.items) ? item.items : [];
              if (children.length > LIMITS.fishbone.children) errors.push(`Subcategory ${item.subcategory || itemIndex + 1} has more than ${LIMITS.fishbone.children} child causes.`);
              children.forEach((child, childIndex) => requireText(errors, `Subcategory ${itemIndex + 1} child ${childIndex + 1}`, child));
            }
          });
        });
      } else if (currentType() === "fault_tree") {
        requireText(errors, "Top Event", model.top_event && model.top_event.label);
        const tree = model.tree || {};
        if (!["OR", "AND"].includes(String(tree.gate || "OR").toUpperCase())) errors.push("Root Gate must be OR or AND.");
        const children = Array.isArray(tree.children) ? tree.children : [];
        if (children.length > LIMITS.fault_tree.first) errors.push(`Fault tree supports up to ${LIMITS.fault_tree.first} first-level events.`);
        children.forEach((event, index) => validateFaultEvent(errors, event, `First-level event ${index + 1}`, true));
      } else if (currentType() === "exclusion_tree") {
        requireText(errors, "Problem", oneLanguageValue(model.problem, "text"));
        const checks = Array.isArray(model.checks) ? model.checks : [];
        if (checks.length < 1) errors.push("Exclusion tree needs at least 1 check point.");
        if (checks.length > LIMITS.exclusion_tree.checks) errors.push(`Exclusion tree supports up to ${LIMITS.exclusion_tree.checks} check points.`);
        checks.forEach((check, index) => {
          requireText(errors, `Check Point ${index + 1} question`, oneLanguageValue(check, "text"));
          requireText(errors, `Check Point ${index + 1} fail cause`, oneLanguageValue(check.fail_conclusion, "text"));
        });
        requireText(errors, "Final Pass Conclusion", oneLanguageValue(model.final_pass_conclusion, "text"));
      } else if (currentType() === "two_by_two_matrix") {
        requireText(errors, "Title", model.title);
        const items = Array.isArray(model.items) ? model.items : [];
        if (items.length < 1) errors.push("Two-by-two matrix needs at least 1 item.");
        if (items.length > LIMITS.two_by_two_matrix.items) errors.push(`Two-by-two matrix supports up to ${LIMITS.two_by_two_matrix.items} items.`);
        items.forEach((item, index) => {
          requireText(errors, `Item ${index + 1} name`, item.name || item.label);
          const x = Number(item.x_score);
          const y = Number(item.y_score);
          if (!Number.isFinite(x) || x < 1 || x > 5) errors.push(`Item ${index + 1} x_score must be 1-5.`);
          if (!Number.isFinite(y) || y < 1 || y > 5) errors.push(`Item ${index + 1} y_score must be 1-5.`);
        });
      } else if (currentType() === "roadmap_timeline") {
        requireText(errors, "Title", model.title);
        requireText(errors, "Goal", model.goal);
        if (!["swimlane_roadmap", "milestone_timeline"].includes(String(model.preset || ""))) {
          errors.push("Roadmap preset must be swimlane_roadmap or milestone_timeline.");
        }
        const milestones = Array.isArray(model.milestones) ? model.milestones : [];
        if (model.preset === "swimlane_roadmap") {
          const periods = Array.isArray(model.time_periods) ? model.time_periods : [];
          const lanes = Array.isArray(model.lanes) ? model.lanes : [];
          const initiatives = Array.isArray(model.initiatives) ? model.initiatives : [];
          if (periods.length < 1) errors.push("Swimlane roadmap needs at least 1 time period.");
          if (lanes.length < 1) errors.push("Swimlane roadmap needs at least 1 lane.");
          if (initiatives.length < 1) errors.push("Swimlane roadmap needs at least 1 initiative.");
          periods.forEach((period, index) => {
            requireText(errors, `Period ${index + 1} label`, period.label);
            requireText(errors, `Period ${index + 1} start`, period.start);
            requireText(errors, `Period ${index + 1} end`, period.end);
          });
          lanes.forEach((lane, index) => {
            requireText(errors, `Lane ${index + 1} id`, lane.id);
            requireText(errors, `Lane ${index + 1} name`, lane.name);
          });
          initiatives.forEach((initiative, index) => {
            requireText(errors, `Initiative ${index + 1} id`, initiative.id);
            requireText(errors, `Initiative ${index + 1} lane`, initiative.lane_id);
            requireText(errors, `Initiative ${index + 1} name`, initiative.name);
            requireText(errors, `Initiative ${index + 1} start`, initiative.start);
            requireText(errors, `Initiative ${index + 1} end`, initiative.end);
          });
          [...milestones, ...(Array.isArray(model.decision_points) ? model.decision_points : [])].forEach((marker, index) => {
            requireText(errors, `Marker ${index + 1} id`, marker.id);
            requireText(errors, `Marker ${index + 1} lane`, marker.lane_id);
            requireText(errors, `Marker ${index + 1} name`, marker.name);
            requireText(errors, `Marker ${index + 1} date`, marker.date);
          });
        } else {
          if (milestones.length < 1) errors.push("Milestone timeline needs at least 1 milestone.");
          milestones.forEach((marker, index) => {
            requireText(errors, `Milestone ${index + 1} id`, marker.id);
            requireText(errors, `Milestone ${index + 1} name`, marker.name);
            requireText(errors, `Milestone ${index + 1} date`, marker.date);
          });
          const phases = Array.isArray(model.phases) ? model.phases : [];
          phases.forEach((phase, index) => {
            requireText(errors, `Phase ${index + 1} name`, phase.name);
            requireText(errors, `Phase ${index + 1} start`, phase.start);
            requireText(errors, `Phase ${index + 1} end`, phase.end);
          });
        }
      } else if (currentType() === "fmea_table") {
        requireText(errors, "Title", model.title);
        requireText(errors, "Goal", model.goal);
        const rows = Array.isArray(model.rows) ? model.rows : [];
        if (rows.length < 1) errors.push("FMEA table needs at least 1 row.");
        if (rows.length > LIMITS.fmea_table.rows) errors.push(`FMEA table supports up to ${LIMITS.fmea_table.rows} rows in the builder.`);
        rows.forEach((item, index) => {
          requireText(errors, `FMEA row ${index + 1} id`, item.id);
          requireText(errors, `FMEA row ${index + 1} item / function`, item.item_function);
          requireText(errors, `FMEA row ${index + 1} failure mode`, item.failure_mode);
          for (const key of ["severity", "occurrence", "detection"]) {
            const score = Number(item[key]);
            if (!Number.isFinite(score) || score < LIMITS.fmea_table.scoreMin || score > LIMITS.fmea_table.scoreMax) {
              errors.push(`FMEA row ${index + 1} ${key} must be ${LIMITS.fmea_table.scoreMin}-${LIMITS.fmea_table.scoreMax}.`);
            }
          }
        });
      }
      return errors;
    }

    function collectValidationWarnings() {
      const warnings = [];
      if (currentType() === "fishbone") {
        const categories = Array.isArray(model.categories) ? model.categories : [];
        if (categories.length > 0 && categories.length < LIMITS.fishbone.minCategories) {
          warnings.push(`Fishbone works best with ${LIMITS.fishbone.minCategories}-${LIMITS.fishbone.categories} categories.`);
        }
      } else if (currentType() === "fault_tree") {
        const children = Array.isArray(model.tree && model.tree.children) ? model.tree.children : [];
        if (children.length > 0 && children.length < LIMITS.fault_tree.minFirst) {
          warnings.push(`Fault tree works best with at least ${LIMITS.fault_tree.minFirst} first-level events.`);
        } else if (children.length > LIMITS.fault_tree.recommendedFirst && children.length <= LIMITS.fault_tree.first) {
          warnings.push(`Fault tree review is clearest with ${LIMITS.fault_tree.minFirst}-${LIMITS.fault_tree.recommendedFirst} first-level events; use up to ${LIMITS.fault_tree.first} when the source needs it.`);
        }
      } else if (currentType() === "exclusion_tree") {
        const checks = Array.isArray(model.checks) ? model.checks : [];
        if (checks.length > 0 && checks.length < LIMITS.exclusion_tree.minChecks) {
          warnings.push(`Exclusion tree works best with ${LIMITS.exclusion_tree.minChecks}-${LIMITS.exclusion_tree.checks} check points.`);
        }
      } else if (currentType() === "two_by_two_matrix") {
        const items = Array.isArray(model.items) ? model.items : [];
        if (items.length > 0 && items.length < LIMITS.two_by_two_matrix.minItems) {
          warnings.push(`Two-by-two matrix works best with at least ${LIMITS.two_by_two_matrix.minItems} scored items.`);
        }
      } else if (currentType() === "roadmap_timeline") {
        const limits = LIMITS.roadmap_timeline;
        if (model.preset === "swimlane_roadmap") {
          const periods = Array.isArray(model.time_periods) ? model.time_periods : [];
          const lanes = Array.isArray(model.lanes) ? model.lanes : [];
          const initiatives = Array.isArray(model.initiatives) ? model.initiatives : [];
          if (periods.length > 0 && periods.length < limits.minPeriods) warnings.push(`Swimlane roadmap works best with at least ${limits.minPeriods} time periods.`);
          if (lanes.length > 0 && lanes.length < limits.minLanes) warnings.push(`Swimlane roadmap works best with at least ${limits.minLanes} lane.`);
          if (initiatives.length > 0 && initiatives.length < limits.minInitiatives) warnings.push(`Swimlane roadmap works best with at least ${limits.minInitiatives} initiative.`);
        } else if (model.preset === "milestone_timeline") {
          const milestones = Array.isArray(model.milestones) ? model.milestones : [];
          if (milestones.length > 0 && milestones.length < limits.minMilestones) warnings.push(`Milestone timeline works best with at least ${limits.minMilestones} milestone.`);
        }
      } else if (currentType() === "fmea_table") {
        const rows = Array.isArray(model.rows) ? model.rows : [];
        if (rows.length > 0 && rows.length < LIMITS.fmea_table.minRows) {
          warnings.push(`FMEA table works best with at least ${LIMITS.fmea_table.minRows} focused rows.`);
        }
      }
      return warnings;
    }

    function validateFaultEvent(errors, event, label, firstLevel) {
      requireText(errors, label, event && event.label);
      if (!["OR", "AND"].includes(String((event && event.gate) || "OR").toUpperCase())) errors.push(`${label} gate must be OR or AND.`);
      const children = Array.isArray(event && event.children) ? event.children : [];
      const limit = firstLevel ? LIMITS.fault_tree.children : LIMITS.fault_tree.nestedChildren;
      if (children.length > limit) errors.push(`${label} has more than ${limit} child events.`);
      children.forEach((child, index) => {
        if (child.type === "intermediate_event") validateFaultEvent(errors, child, `${label} nested event ${index + 1}`, false);
        else requireText(errors, `${label} basic event ${index + 1}`, child.label);
      });
    }

    function updateValidation() {
      const errors = collectValidationErrors();
      const warnings = collectValidationWarnings();
      if (!errors.length && !warnings.length) {
        formErrors.className = "form-errors";
        formErrors.innerHTML = "";
        return true;
      }
      const sections = [];
      if (errors.length) {
        sections.push("<strong>Please fix before saving or rendering:</strong><ul>" +
          errors.map(error => `<li>${escapeHtml(error)}</li>`).join("") +
          "</ul>");
      }
      if (warnings.length) {
        sections.push("<strong>Recommended before review:</strong><ul>" +
          warnings.map(warning => `<li>${escapeHtml(warning)}</li>`).join("") +
          "</ul>");
      }
      formErrors.className = errors.length ? "form-errors has-errors" : "form-errors has-warnings";
      formErrors.innerHTML = sections.join("");
      return !errors.length;
    }

    function ensureValidForAction() {
      syncDiagramType();
      if (updateValidation()) return true;
      setStatus("Fix the highlighted form issues first.", "error");
      return false;
    }

    function confirmValidationWarnings() {
      const warnings = collectValidationWarnings();
      if (!warnings.length) return true;
      return window.confirm(
        "This diagram is below the recommended structure size:\n- " +
        warnings.join("\n- ") +
        "\n\nContinue rendering this draft?"
      );
    }

    function escapeHtml(value) {
      return String(value || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    async function api(path, options = {}) {
      const response = await fetch(path, {
        headers: { "Content-Type": "application/json" },
        ...options
      });
      const data = await response.json();
      if (!data.ok) throw new Error(data.error || "Request failed");
      return data;
    }

    async function loadTemplate() {
      const data = await api(`/api/template?diagram_type=${encodeURIComponent(currentType())}`);
      model = data.data;
      renderForm();
      previewBox.innerHTML = '<div class="empty">Template loaded. Click Render SVG to preview.</div>';
      setStatus("Template loaded.", "ok");
    }

    function nameFromFile(filename) {
      const stem = filename.replace(/\.[^.]+$/, "").toLowerCase();
      const clean = stem.replace(/[^a-z0-9_-]+/g, "-").replace(/^-+|-+$/g, "").slice(0, 64);
      return /^[a-z0-9][a-z0-9_-]{0,63}$/.test(clean) ? clean : "loaded-diagram";
    }

    function loadFile() {
      fileInput.value = "";
      fileInput.click();
    }

    async function loadSelectedFile(file) {
      if (!file) return;
      const content = await file.text();
      const result = await api("/api/parse-file", {
        method: "POST",
        body: JSON.stringify({ filename: file.name, content })
      });
      typeEl.value = result.diagram_type;
      nameEl.value = nameFromFile(file.name);
      model = result.data;
      renderForm();
      previewMeta.textContent = "";
      previewBox.innerHTML = '<div class="empty">File loaded. Click Render SVG to preview.</div>';
      setStatus(`Loaded ${file.name}.`, "ok");
    }

    async function saveJson() {
      if (!ensureValidForAction()) return;
      const result = await api("/api/save", {
        method: "POST",
        body: JSON.stringify({ diagram_type: currentType(), name: safeName(), data: model })
      });
      rememberRecent();
      setStatus(result.message, "ok");
    }

    function openSaveAsDialog() {
      if (!ensureValidForAction()) return;
      saveAsDialog.classList.add("open");
    }

    function closeSaveAsDialog() {
      saveAsDialog.classList.remove("open");
    }

    function openHelpDialog() {
      helpDialog.classList.add("open");
    }

    function closeHelpDialog() {
      helpDialog.classList.remove("open");
    }

    async function saveAsSource(format) {
      if (!ensureValidForAction()) return;
      closeSaveAsDialog();
      const extension = format === "markdown" ? ".md" : ".json";
      const mimeType = format === "markdown" ? "text/markdown" : "application/json";
      const text = sourceTextForFormat(format);
      const filename = safeName() + extension;
      if (!window.showSaveFilePicker) {
        downloadText(filename, text, mimeType);
        setStatus("Browser save dialog unavailable; source file downloaded instead.", "ok");
        return;
      }
      try {
        const handle = await window.showSaveFilePicker({
          suggestedName: filename,
          types: [{
            description: format === "markdown" ? "Markdown source" : "JSON source",
            accept: { [mimeType]: format === "markdown" ? [".md", ".markdown"] : [".json"] },
          }],
          excludeAcceptAllOption: true,
        });
        const writable = await handle.createWritable();
        await writable.write(new Blob([text], { type: mimeType + ";charset=utf-8" }));
        await writable.close();
        setStatus(`Saved ${handle.name}.`, "ok");
      } catch (error) {
        if (error && error.name === "AbortError") return;
        throw error;
      }
    }

    async function renderSvg() {
      if (!ensureValidForAction()) return;
      if (!confirmValidationWarnings()) {
        setStatus("Render canceled.", "");
        return;
      }
      const result = await api("/api/render", {
        method: "POST",
        body: JSON.stringify({ diagram_type: currentType(), name: safeName(), data: model })
      });
      setPreviewFrame();
      previewMeta.textContent = safeName() + ".svg";
      rememberRecent();
      setStatus(result.message, "ok");
    }

    async function exportPng() {
      if (!ensureValidForAction()) return;
      if (!confirmValidationWarnings()) {
        setStatus("Export canceled.", "");
        return;
      }
      setStatus("Rendering current diagram before PNG export...", "");
      const renderResult = await api("/api/render", {
        method: "POST",
        body: JSON.stringify({ diagram_type: currentType(), name: safeName(), data: model })
      });
      setPreviewFrame();
      previewMeta.textContent = safeName() + ".svg";
      rememberRecent();
      setStatus("Exporting PNG...", "");
      const result = await api("/api/export", {
        method: "POST",
        body: JSON.stringify({ diagram_type: currentType(), name: safeName() })
      });
      previewMeta.textContent = safeName() + ".png";
      setStatus(result.message + " Open the work folder to view it.", "ok");
    }

    async function openFolder() {
      setStatus("Opening work folder...", "");
      const result = await api("/api/open-folder", {
        method: "POST",
        body: JSON.stringify({ diagram_type: currentType() })
      });
      setStatus(result.message + " If Explorer stays behind other windows, check the taskbar.", "ok");
    }

    function downloadText(filename, text, mimeType) {
      const blob = new Blob([text], { type: mimeType + ";charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      URL.revokeObjectURL(url);
    }

    function sourceTextForFormat(format) {
      if (format === "markdown") return modelToMarkdown();
      return JSON.stringify(model, null, 2) + "\n";
    }

    function modelToMarkdown() {
      if (currentType() === "fishbone") return fishboneToMarkdown();
      if (currentType() === "fault_tree") return faultTreeToMarkdown();
      if (currentType() === "two_by_two_matrix") return twoByTwoToMarkdown();
      if (currentType() === "roadmap_timeline") return roadmapToMarkdown();
      if (currentType() === "fmea_table") return fmeaToMarkdown();
      return exclusionTreeToMarkdown();
    }

    function yamlHeader(lines) {
      return "---\n" + lines.join("\n") + "\n---\n\n";
    }

    function mdLine(value) {
      return String(value || "").replace(/\r?\n+/g, " ").trim();
    }

    function fishboneToMarkdown() {
      const lines = [yamlHeader(["diagram_type: fishbone"]), `# ${mdLine(model.topic) || "Problem / Topic"}`, ""];
      for (const category of model.categories || []) {
        lines.push(`## ${mdLine(category.name_en || category.name) || "Category"}`);
        for (const item of category.items || []) {
          if (typeof item === "string") {
            lines.push(`- ${mdLine(item) || "Cause"}`);
          } else {
            lines.push(`- ${mdLine(item.subcategory) || "Subcategory"}`);
            for (const child of item.items || []) lines.push(`  - ${mdLine(child) || "Child cause"}`);
          }
        }
        lines.push("");
      }
      return lines.join("\n").replace(/\n{3,}/g, "\n\n");
    }

    function faultTreeToMarkdown() {
      const header = [
        "diagram_type: fault_tree",
        `title: ${mdLine(model.title) || "Fault Tree Analysis"}`,
        `subtitle: ${mdLine(model.subtitle) || "Top Event"}`,
        "show_legend: true",
      ];
      const lines = [yamlHeader(header), `# ${mdLine(model.top_event && model.top_event.label) || "Top Event"}`, `Gate: ${mdLine(model.tree && model.tree.gate).toUpperCase() || "OR"}`, ""];
      const detail = model.event_detail || {};
      if (mdLine(detail.text) || (Array.isArray(detail.bullets) && detail.bullets.length)) {
        lines.push("Event Detail:");
        if (mdLine(detail.text)) lines.push(mdLine(detail.text));
        for (const bullet of detail.bullets || []) lines.push(`- ${mdLine(bullet)}`);
        lines.push("");
      }
      for (const event of (model.tree && model.tree.children) || []) writeFaultMarkdownEvent(lines, event, 2);
      return lines.join("\n").replace(/\n{3,}/g, "\n\n");
    }

    function writeFaultMarkdownEvent(lines, event, level) {
      const heading = "#".repeat(level);
      lines.push(`${heading} ${mdLine(event.label) || "Intermediate Event"}`);
      lines.push(`Gate: ${mdLine(event.gate).toUpperCase() || "OR"}`);
      for (const child of event.children || []) {
        if (child.type === "intermediate_event") writeFaultMarkdownEvent(lines, child, Math.min(level + 1, 3));
        else lines.push(`- ${mdLine(child.label) || "Basic Event"}`);
      }
      lines.push("");
    }

    function exclusionTreeToMarkdown() {
      const lines = [
        yamlHeader(["diagram_type: exclusion_tree", "show_legend: true", "show_how_to_use: true"]),
        `# ${mdLine(oneLanguageValue(model.problem, "text")) || "Target Problem"}`,
        "",
      ];
      const detail = model.event_detail || {};
      lines.push(`Event Detail Title: ${mdLine(detail.title) || "Event Detail"}`);
      if (mdLine(detail.text)) lines.push(`Event Detail: ${mdLine(detail.text)}`);
      for (const bullet of detail.bullets || []) lines.push(`- ${mdLine(bullet)}`);
      lines.push("");
      for (const check of model.checks || []) {
        lines.push(`## ${mdLine(oneLanguageValue(check, "text")) || "Check OK?"}`);
        lines.push(`Fail Conclusion: ${mdLine(oneLanguageValue(check.fail_conclusion, "text")) || "Likely Cause"}`);
        const detailText = mdLine(oneLanguageValue(check.fail_conclusion, "detail"));
        if (detailText) lines.push(`Fail Detail: ${detailText}`);
        lines.push("");
      }
      lines.push(`Final Pass Conclusion: ${mdLine(oneLanguageValue(model.final_pass_conclusion, "text")) || "No issue found in this path. Consider other rare causes or deeper analysis."}`);
      return lines.join("\n").replace(/\n{3,}/g, "\n\n") + "\n";
    }

    function twoByTwoToMarkdown() {
      const header = [
        "diagram_type: two_by_two_matrix",
        `preset: ${mdLine(model.preset) || "action_priority"}`,
        `language: ${mdLine(model.language) || "auto"}`,
        `title: ${mdLine(model.title) || "Two-by-Two Matrix"}`,
      ];
      if (mdLine(model.notes)) header.push(`notes: ${mdLine(model.notes)}`);
      const lines = [yamlHeader(header), "| Item | X Score | Y Score |", "| --- | ---: | ---: |"];
      for (const item of model.items || []) {
        lines.push(`| ${mdLine(item.name || item.label) || "Item"} | ${mdLine(item.x_score) || "3"} | ${mdLine(item.y_score) || "3"} |`);
      }
      return lines.join("\n") + "\n";
    }

    function roadmapToMarkdown() {
      if (model.preset === "milestone_timeline") return roadmapMilestoneToMarkdown();
      return roadmapSwimlaneToMarkdown();
    }

    function roadmapSwimlaneToMarkdown() {
      const header = [
        "diagram_type: roadmap_timeline",
        "preset: swimlane_roadmap",
        `lane_type: ${mdLine(model.lane_type) || "theme"}`,
        `language: ${mdLine(model.language) || "en"}`,
        `time_granularity: ${mdLine(model.time_granularity) || "quarter"}`,
        `show_table: ${model.show_table !== false ? "true" : "false"}`,
        `show_summary_panel: ${model.show_summary_panel !== false ? "true" : "false"}`,
      ];
      const lines = [
        yamlHeader(header),
        `# ${mdLine(model.title) || "Roadmap / Timeline"}`,
        "",
        `**Goal:** ${mdLine(model.goal) || "Align initiatives and milestones over time."}`,
        "",
        "## Time Periods",
        "",
        "| ID | Label | Subtitle | Start | End |",
        "|---|---|---|---|---|",
      ];
      for (const period of model.time_periods || []) {
        lines.push(`| ${mdLine(period.id)} | ${mdLine(period.label)} | ${mdLine(period.subtitle)} | ${mdLine(period.start)} | ${mdLine(period.end)} |`);
      }
      lines.push("", "## Lanes", "", "| ID | Name | Color |", "|---|---|---|");
      for (const lane of model.lanes || []) {
        lines.push(`| ${mdLine(lane.id)} | ${mdLine(lane.name)} | ${mdLine(lane.color) || "blue"} |`);
      }
      lines.push("", "## Initiatives", "", "| ID | Lane ID | Name | Start | End | Owner | Status |", "|---|---|---|---|---|---|---|");
      for (const item of model.initiatives || []) {
        lines.push(`| ${mdLine(item.id)} | ${mdLine(item.lane_id)} | ${mdLine(item.name)} | ${mdLine(item.start)} | ${mdLine(item.end)} | ${mdLine(item.owner)} | ${mdLine(item.status) || "planned"} |`);
      }
      lines.push("", "## Milestones", "", "| ID | Lane ID | Name | Date | Type |", "|---|---|---|---|---|");
      for (const marker of model.milestones || []) {
        lines.push(`| ${mdLine(marker.id)} | ${mdLine(marker.lane_id)} | ${mdLine(marker.name)} | ${mdLine(marker.date)} | ${mdLine(marker.type) || "key_milestone"} |`);
      }
      lines.push("", "## Decision Points", "", "| ID | Lane ID | Name | Date | Type |", "|---|---|---|---|---|");
      for (const marker of model.decision_points || []) {
        lines.push(`| ${mdLine(marker.id)} | ${mdLine(marker.lane_id)} | ${mdLine(marker.name)} | ${mdLine(marker.date)} | ${mdLine(marker.type) || "decision"} |`);
      }
      writeRoadmapNotes(lines);
      return lines.join("\n").replace(/\n{3,}/g, "\n\n") + "\n";
    }

    function roadmapMilestoneToMarkdown() {
      const header = [
        "diagram_type: roadmap_timeline",
        "preset: milestone_timeline",
        `language: ${mdLine(model.language) || "en"}`,
        `time_granularity: ${mdLine(model.time_granularity) || "month"}`,
        `show_detail_cards: ${model.show_detail_cards !== false ? "true" : "false"}`,
        `show_table: ${model.show_table !== false ? "true" : "false"}`,
      ];
      const lines = [
        yamlHeader(header),
        `# ${mdLine(model.title) || "Milestone Timeline"}`,
        "",
        `**Goal:** ${mdLine(model.goal) || "Launch the product on time with quality."}`,
        "",
        "## Milestones",
        "",
        "| ID | Name | Date | Type | Owner | Status | Output |",
        "|---|---|---|---|---|---|---|",
      ];
      for (const marker of model.milestones || []) {
        lines.push(`| ${mdLine(marker.id)} | ${mdLine(marker.name)} | ${mdLine(marker.date)} | ${mdLine(marker.type) || "milestone"} | ${mdLine(marker.owner)} | ${mdLine(marker.status) || "planned"} | ${mdLine(marker.output)} |`);
      }
      lines.push("", "## Phases", "", "| Name | Start | End |", "|---|---|---|");
      for (const phase of model.phases || []) {
        lines.push(`| ${mdLine(phase.name)} | ${mdLine(phase.start)} | ${mdLine(phase.end)} |`);
      }
      writeRoadmapNotes(lines);
      return lines.join("\n").replace(/\n{3,}/g, "\n\n") + "\n";
    }

    function writeRoadmapNotes(lines) {
      const notes = Array.isArray(model.notes)
        ? model.notes
        : String(model.notes || "").split(/\r?\n/).map(note => note.trim()).filter(Boolean);
      if (!notes.length) return;
      lines.push("", "## Notes", "");
      for (const note of notes) lines.push(`- ${mdLine(note)}`);
    }

    function fmeaToMarkdown() {
      const project = model.project || {};
      const header = [
        "diagram_type: fmea_table",
        `fmea_type: ${mdLine(model.fmea_type) || "process"}`,
        `language: ${mdLine(model.language) || "en"}`,
      ];
      const lines = [
        yamlHeader(header),
        `# ${mdLine(model.title) || "Process FMEA"}`,
        "",
        `Goal: ${mdLine(model.goal) || "Identify critical risks, calculate RPN, and prioritize corrective actions."}`,
        `Project: ${mdLine(project.name)}`,
        `Owner: ${mdLine(project.owner)}`,
        `Review Frequency: ${mdLine(project.review_frequency)}`,
        `Last Review Date: ${mdLine(project.last_review_date)}`,
      ];
      for (const note of model.notes || []) lines.push(`Note: ${mdLine(note)}`);
      for (const row of model.rows || []) {
        lines.push("", `## Row ${mdLine(row.id) || "F"}`, "");
        lines.push(`Item / Function: ${mdLine(row.item_function)}`);
        lines.push(`Failure Mode: ${mdLine(row.failure_mode)}`);
        writeFmeaList(lines, "Effects", row.failure_effects);
        writeFmeaList(lines, "Causes", row.failure_causes);
        writeFmeaList(lines, "Prevention Controls", row.prevention_controls);
        writeFmeaList(lines, "Detection Controls", row.detection_controls);
        lines.push(`Severity: ${mdLine(row.severity) || "5"}`);
        lines.push(`Occurrence: ${mdLine(row.occurrence) || "4"}`);
        lines.push(`Detection: ${mdLine(row.detection) || "4"}`);
        writeFmeaList(lines, "Recommended Actions", row.recommended_actions);
        lines.push(`Owner: ${mdLine(row.owner)}`);
        lines.push(`Target Completion: ${mdLine(row.target_completion)}`);
        lines.push(`Status: ${mdLine(row.status) || "Open"}`);
      }
      return lines.join("\n").replace(/\n{3,}/g, "\n\n") + "\n";
    }

    function writeFmeaList(lines, title, values) {
      lines.push(`${title}:`);
      const items = Array.isArray(values) ? values : textareaToList(values);
      for (const item of items) lines.push(`- ${mdLine(item)}`);
    }

    async function loadSvgIfExists() {
      try {
        const response = await fetch(svgPreviewUrl());
        if (response.ok) {
          setPreviewFrame();
          previewMeta.textContent = safeName() + ".svg";
        }
      } catch (_error) {}
    }

    function syncDiagramType() {
      model.diagram_type = currentType();
      if (model.diagram_type === "exclusion_tree") cleanExclusionTreeModel();
      if (model.diagram_type === "roadmap_timeline") delete model.subtitle;
      if (model.diagram_type === "fmea_table") {
        model.rows = Array.isArray(model.rows) ? model.rows : [];
        model.rows.forEach((row, index) => normalizeFmeaRow(row, index));
      }
    }

    function input(value, onInput, placeholder = "") {
      const el = document.createElement("input");
      el.value = value || "";
      el.placeholder = placeholder;
      el.addEventListener("input", () => {
        onInput(el.value);
        updateValidation();
      });
      return el;
    }

    function textarea(value, onInput) {
      const el = document.createElement("textarea");
      el.value = value || "";
      el.addEventListener("input", () => {
        onInput(el.value);
        updateValidation();
      });
      return el;
    }

    function select(value, options, onChange) {
      const el = document.createElement("select");
      for (const option of options) {
        const item = document.createElement("option");
        item.value = option;
        item.textContent = option;
        el.appendChild(item);
      }
      el.value = value || options[0];
      el.addEventListener("change", () => {
        onChange(el.value);
        updateValidation();
      });
      return el;
    }

    function checkbox(labelText, checked, onChange) {
      const label = document.createElement("label");
      label.className = "roadmap-checkbox";
      const el = document.createElement("input");
      el.type = "checkbox";
      el.checked = Boolean(checked);
      el.addEventListener("change", () => {
        onChange(el.checked);
        updateValidation();
      });
      label.append(el, document.createTextNode(labelText));
      return label;
    }

    function button(text, onClick, disabled = false) {
      const el = document.createElement("button");
      el.type = "button";
      el.textContent = text;
      el.disabled = disabled;
      el.addEventListener("click", onClick);
      return el;
    }

    function row(labelText, control) {
      const wrapper = document.createElement("div");
      wrapper.className = "row";
      const label = document.createElement("label");
      label.textContent = labelText;
      wrapper.append(label, control);
      return wrapper;
    }

    function section(title, hintText) {
      const wrapper = document.createElement("div");
      wrapper.className = "section";
      const head = document.createElement("div");
      head.className = "section-title";
      const titleEl = document.createElement("h2");
      titleEl.textContent = title;
      head.appendChild(titleEl);
      wrapper.appendChild(head);
      if (hintText) {
        const hint = document.createElement("div");
        hint.className = "hint";
        hint.textContent = hintText;
        wrapper.appendChild(hint);
      }
      return wrapper;
    }

    function roadmapCard(titleText, onRemove) {
      const box = document.createElement("div");
      box.className = "item";
      const head = document.createElement("div");
      head.className = "item-head";
      const title = document.createElement("h3");
      title.textContent = titleText;
      head.append(title, button("Remove", onRemove));
      box.appendChild(head);
      return box;
    }

    function roadmapField(labelText, control, className = "") {
      const wrapper = document.createElement("div");
      wrapper.className = `roadmap-field ${className}`.trim();
      const label = document.createElement("label");
      label.textContent = labelText;
      wrapper.append(label, control);
      return wrapper;
    }

    function fmeaField(labelText, control, className = "") {
      const wrapper = document.createElement("div");
      wrapper.className = `fmea-field ${className}`.trim();
      const label = document.createElement("label");
      label.textContent = labelText;
      wrapper.append(label, control);
      return wrapper;
    }

    function scoreInput(value, onInput, titleText) {
      const el = input(value, value => onInput(Number(value)), "1-10");
      el.className = "fmea-score";
      el.type = "number";
      el.min = "1";
      el.max = "10";
      el.step = "1";
      el.title = titleText;
      return el;
    }

    function renderForm() {
      formRoot.innerHTML = "";
      if (currentType() === "fishbone") renderFishboneForm();
      else if (currentType() === "fault_tree") renderFaultTreeForm();
      else if (currentType() === "exclusion_tree") renderExclusionTreeForm();
      else if (currentType() === "two_by_two_matrix") renderTwoByTwoForm();
      else if (currentType() === "roadmap_timeline") renderRoadmapForm();
      else renderFmeaForm();
      updateValidation();
    }

    function renderFishboneForm() {
      model.diagram_type = "fishbone";
      model.categories = Array.isArray(model.categories) ? model.categories : [];
      formRoot.appendChild(row("Topic", input(model.topic, value => model.topic = value, "Problem / Topic")));
      const limits = LIMITS.fishbone;
      const categories = section("Categories", `Use ${limits.minCategories}-${limits.categories} categories. Each category supports up to ${limits.entries} primary entries; each subcategory supports up to ${limits.children} child causes.`);
      const addDisabled = model.categories.length >= limits.categories;
      categories.querySelector(".section-title").appendChild(button("Add Category", () => {
        if (model.categories.length < limits.categories) {
          model.categories.push({ name_en: "New Category", items: [] });
          renderForm();
        }
      }, addDisabled));
      model.categories.forEach((category, categoryIndex) => {
        category.items = Array.isArray(category.items) ? category.items : [];
        const box = document.createElement("div");
        box.className = "item";
        const head = document.createElement("div");
        head.className = "item-head";
        head.appendChild(input(category.name_en, value => category.name_en = value, "Category name"));
        head.appendChild(button("Remove", () => {
          model.categories.splice(categoryIndex, 1);
          renderForm();
        }));
        box.appendChild(head);
        category.items.forEach((item, itemIndex) => {
          if (typeof item === "string") {
            const line = document.createElement("div");
            line.className = "inline-3";
            line.append(
              input(item, value => category.items[itemIndex] = value, "Primary cause"),
              button("Make Subcategory", () => {
                category.items[itemIndex] = { subcategory: item || "Subcategory", items: [] };
                renderForm();
              }),
              button("Remove", () => {
                category.items.splice(itemIndex, 1);
                renderForm();
              })
            );
            box.appendChild(line);
          } else {
            item.items = Array.isArray(item.items) ? item.items : [];
            const sub = document.createElement("div");
            sub.className = "item fishbone-subcategory";
            const subHead = document.createElement("div");
            subHead.className = "subcategory-title";
            const badge = document.createElement("span");
            badge.className = "level-badge";
            badge.textContent = "Subcategory";
            subHead.appendChild(badge);
            subHead.appendChild(input(item.subcategory, value => item.subcategory = value, "Subcategory"));
            subHead.appendChild(button("Remove", () => {
              category.items.splice(itemIndex, 1);
              renderForm();
            }));
            sub.appendChild(subHead);
            const childArea = document.createElement("div");
            childArea.className = "child-cause-area";
            const childTitle = document.createElement("div");
            childTitle.className = "child-cause-title";
            childTitle.textContent = "Child causes";
            childArea.appendChild(childTitle);
            item.items.forEach((child, childIndex) => {
              const line = document.createElement("div");
              line.className = "inline";
              line.append(
                input(child, value => item.items[childIndex] = value, "Child cause"),
                button("Remove", () => {
                  item.items.splice(childIndex, 1);
                  renderForm();
                })
              );
              childArea.appendChild(line);
            });
            childArea.appendChild(button("Add Child Cause", () => {
              if (item.items.length < limits.children) {
                item.items.push("New child cause");
                renderForm();
              }
            }, item.items.length >= limits.children));
            sub.appendChild(childArea);
            box.appendChild(sub);
          }
        });
        const itemToolbar = document.createElement("div");
        itemToolbar.className = "toolbar";
        itemToolbar.append(
          button("Add Cause", () => {
            if (category.items.length < limits.entries) {
              category.items.push("New cause");
              renderForm();
            }
          }, category.items.length >= limits.entries),
          button("Add Subcategory", () => {
            if (category.items.length < limits.entries) {
              category.items.push({ subcategory: "New subcategory", items: ["New child cause"] });
              renderForm();
            }
          }, category.items.length >= limits.entries)
        );
        box.appendChild(itemToolbar);
        categories.appendChild(box);
      });
      formRoot.appendChild(categories);
    }

    function renderFaultTreeForm() {
      model.diagram_type = "fault_tree";
      model.top_event = model.top_event || { id: "T0", label: "Top Event" };
      model.event_detail = model.event_detail || { title: "Event Detail", text: "", bullets: [] };
      model.tree = model.tree || { gate: "OR", children: [] };
      model.tree.children = Array.isArray(model.tree.children) ? model.tree.children : [];
      formRoot.appendChild(row("Title", input(model.title, value => model.title = value, "Fault Tree Analysis")));
      formRoot.appendChild(row("Subtitle", input(model.subtitle, value => model.subtitle = value, "Top Event - ...")));
      formRoot.appendChild(row("Top Event", input(model.top_event.label, value => model.top_event.label = value, "Top event")));
      formRoot.appendChild(row("Root Gate", select(model.tree.gate, ["OR", "AND"], value => model.tree.gate = value)));
      const detail = section("Event Detail", "Shown in the upper-left panel. Use bullets for short review notes.");
      detail.appendChild(row("Detail Title", input(model.event_detail.title, value => model.event_detail.title = value, "Event Detail")));
      detail.appendChild(row("Detail Text", textarea(model.event_detail.text, value => model.event_detail.text = value)));
      model.event_detail.bullets = Array.isArray(model.event_detail.bullets) ? model.event_detail.bullets : [];
      model.event_detail.bullets.forEach((bulletText, index) => {
        const line = document.createElement("div");
        line.className = "inline";
        line.append(
          input(bulletText, value => model.event_detail.bullets[index] = value, "Detail bullet"),
          button("Remove", () => {
            model.event_detail.bullets.splice(index, 1);
            renderForm();
          })
        );
        detail.appendChild(line);
      });
      detail.appendChild(button("Add Detail Bullet", () => {
        model.event_detail.bullets.push("New detail note");
        renderForm();
      }));
      formRoot.appendChild(detail);

      const limits = LIMITS.fault_tree;
      const events = section("First-Level Events", `Recommended ${limits.minFirst}-${limits.recommendedFirst} first-level intermediate events; maximum ${limits.first}. Each intermediate event supports up to ${limits.children} direct children. Nested intermediate events can contain up to ${limits.nestedChildren} basic leaves.`);
      events.querySelector(".section-title").appendChild(button("Add Event", () => {
        if (model.tree.children.length < limits.first) {
          model.tree.children.push({ id: String(model.tree.children.length + 1), type: "intermediate_event", label: "New Event", gate: "OR", children: [] });
          renderForm();
        }
      }, model.tree.children.length >= limits.first));
      model.tree.children.forEach((event, index) => {
        events.appendChild(renderFaultEvent(event, index, model.tree.children, true));
      });
      formRoot.appendChild(events);
    }

    function renderFaultEvent(event, index, siblings, firstLevel) {
      event.type = "intermediate_event";
      event.children = Array.isArray(event.children) ? event.children : [];
      const limits = LIMITS.fault_tree;
      const box = document.createElement("div");
      box.className = firstLevel ? "item" : "nested item";
      const head = document.createElement("div");
      head.className = "item-head";
      const title = document.createElement("h3");
      title.textContent = firstLevel ? "Intermediate Event" : "Nested Intermediate Event";
      head.appendChild(title);
      head.appendChild(button("Remove", () => {
        siblings.splice(index, 1);
        renderForm();
      }));
      box.appendChild(head);
      box.appendChild(row("Label", input(event.label, value => event.label = value, "Event label")));
      box.appendChild(row("Gate", select(event.gate, ["OR", "AND"], value => event.gate = value)));
      event.children.forEach((child, childIndex) => {
        if (child.type === "intermediate_event") {
          box.appendChild(renderFaultEvent(child, childIndex, event.children, false));
        } else {
          child.type = "basic_event";
          const line = document.createElement("div");
          line.className = "inline";
          line.append(
            input(child.label, value => child.label = value, "Basic event"),
            button("Remove", () => {
              event.children.splice(childIndex, 1);
              renderForm();
            })
          );
          box.appendChild(line);
        }
      });
      const toolbar = document.createElement("div");
      toolbar.className = "toolbar";
      const childLimit = firstLevel ? limits.children : limits.nestedChildren;
      toolbar.appendChild(button("Add Basic Event", () => {
        if (event.children.length < childLimit) {
          event.children.push({ id: event.id + "." + (event.children.length + 1), type: "basic_event", label: "New basic event" });
          renderForm();
        }
      }, event.children.length >= childLimit));
      if (firstLevel) {
        toolbar.appendChild(button("Add Nested Event", () => {
          if (event.children.length < childLimit) {
            event.children.push({ id: event.id + "." + (event.children.length + 1), type: "intermediate_event", label: "New nested event", gate: "OR", children: [] });
            renderForm();
          }
        }, event.children.length >= childLimit));
      }
      box.appendChild(toolbar);
      return box;
    }

    function oneLanguageValue(obj, base) {
      if (!obj) return "";
      return obj[base] || obj[base + "_en"] || obj[base + "_zh"] || "";
    }

    function setOneLanguageValue(obj, base, value) {
      obj[base + "_en"] = value;
      delete obj[base + "_zh"];
    }

    function cleanExclusionTreeModel() {
      if (currentType() !== "exclusion_tree") return;
      model.problem = model.problem || {};
      setOneLanguageValue(model.problem, "text", oneLanguageValue(model.problem, "text") || "Target Problem");
      delete model.language;
      model.checks = Array.isArray(model.checks) ? model.checks : [];
      model.checks.forEach((check, index) => {
        setOneLanguageValue(check, "text", oneLanguageValue(check, "text") || `Check ${index + 1} OK?`);
        check.pass_label_en = "Yes";
        check.fail_label_en = "No";
        delete check.pass_label_zh;
        delete check.fail_label_zh;
        delete check.icon;
        check.fail_conclusion = check.fail_conclusion || {};
        setOneLanguageValue(check.fail_conclusion, "text", oneLanguageValue(check.fail_conclusion, "text") || "Likely Cause");
        setOneLanguageValue(check.fail_conclusion, "detail", oneLanguageValue(check.fail_conclusion, "detail"));
      });
      model.final_pass_conclusion = model.final_pass_conclusion || {};
      setOneLanguageValue(
        model.final_pass_conclusion,
        "text",
        oneLanguageValue(model.final_pass_conclusion, "text") || "No issue found in this path. Consider other rare causes or deeper analysis."
      );
      setOneLanguageValue(model.final_pass_conclusion, "detail", oneLanguageValue(model.final_pass_conclusion, "detail"));
    }

    function renderExclusionTreeForm() {
      model.diagram_type = "exclusion_tree";
      model.problem = model.problem || { text_en: "Target Problem" };
      model.event_detail = model.event_detail || { title: "Event Detail", text: "", bullets: [] };
      model.checks = Array.isArray(model.checks) ? model.checks : [];
      model.final_pass_conclusion = model.final_pass_conclusion || { text_en: "" };
      cleanExclusionTreeModel();
      formRoot.appendChild(row("Problem", input(oneLanguageValue(model.problem, "text"), value => setOneLanguageValue(model.problem, "text", value), "System Fails to Start")));

      const detail = section("Event Detail", "Shown in the upper-left panel. Use concise context and short bullets.");
      detail.appendChild(row("Detail Title", input(model.event_detail.title, value => model.event_detail.title = value, "Event Detail")));
      detail.appendChild(row("Detail Text", textarea(model.event_detail.text, value => model.event_detail.text = value)));
      model.event_detail.bullets = Array.isArray(model.event_detail.bullets) ? model.event_detail.bullets : [];
      model.event_detail.bullets.forEach((bulletText, index) => {
        const line = document.createElement("div");
        line.className = "inline";
        line.append(
          input(bulletText, value => model.event_detail.bullets[index] = value, "Detail bullet"),
          button("Remove", () => {
            model.event_detail.bullets.splice(index, 1);
            renderForm();
          })
        );
        detail.appendChild(line);
      });
      detail.appendChild(button("Add Detail Bullet", () => {
        model.event_detail.bullets.push("New detail note");
        renderForm();
      }));
      formRoot.appendChild(detail);

      const limits = LIMITS.exclusion_tree;
      const checks = section("Check Points", `Use ${limits.minChecks}-${limits.checks} checks on one sequential path. Each check has one Yes/Pass path and one No/Fail conclusion.`);
      checks.querySelector(".section-title").appendChild(button("Add Check", () => {
        if (model.checks.length < limits.checks) {
          model.checks.push({
            id: String(model.checks.length + 1),
            text_en: "New Check OK?",
            pass_label_en: "Yes",
            fail_label_en: "No",
            fail_conclusion: { text_en: "Likely Cause", detail_en: "" }
          });
          renderForm();
        }
      }, model.checks.length >= limits.checks));
      model.checks.forEach((check, index) => {
        check.fail_conclusion = check.fail_conclusion || { text_en: "", detail_en: "" };
        const box = document.createElement("div");
        box.className = "item";
        const head = document.createElement("div");
        head.className = "item-head";
        const title = document.createElement("h3");
        title.textContent = `Check Point ${index + 1}`;
        head.appendChild(title);
        head.appendChild(button("Remove", () => {
          model.checks.splice(index, 1);
          renderForm();
        }));
        box.appendChild(head);
        box.appendChild(row("Question", input(oneLanguageValue(check, "text"), value => setOneLanguageValue(check, "text", value), "Power Input OK?")));
        box.appendChild(row("Fail Cause", input(oneLanguageValue(check.fail_conclusion, "text"), value => setOneLanguageValue(check.fail_conclusion, "text", value), "Likely Cause")));
        box.appendChild(row("Fail Detail", input(oneLanguageValue(check.fail_conclusion, "detail"), value => setOneLanguageValue(check.fail_conclusion, "detail", value), "Optional detail")));
        checks.appendChild(box);
      });
      formRoot.appendChild(checks);

      const final = section("Final Pass Conclusion", "Shown when all checks pass and this path does not identify the cause.");
      final.appendChild(row("Conclusion", textarea(oneLanguageValue(model.final_pass_conclusion, "text"), value => setOneLanguageValue(model.final_pass_conclusion, "text", value))));
      formRoot.appendChild(final);
    }

    function renderTwoByTwoForm() {
      model.diagram_type = "two_by_two_matrix";
      model.preset = model.preset || "action_priority";
      model.language = model.language || "auto";
      model.items = Array.isArray(model.items) ? model.items : [];
      formRoot.appendChild(row("Title", input(model.title, value => model.title = value, "Two-by-Two Matrix")));
      formRoot.appendChild(row("Preset", select(model.preset, [
        "action_priority",
        "risk_benefit",
        "evidence_impact",
        "value_feasibility",
        "urgency_importance",
        "custom"
      ], value => applyTwoByTwoPreset(value))));
      formRoot.appendChild(row("Notes", input(model.notes || "", value => model.notes = value, "Optional visible note")));

      const limits = LIMITS.two_by_two_matrix;
      const items = section("Matrix Items", `Use ${limits.minItems}-${limits.items} scored items. Maximum ${limits.items}. Scores are 1-5; the Decision Table shows every item.`);
      items.querySelector(".section-title").appendChild(button("Add Item", () => {
        if (model.items.length < limits.items) {
          model.items.push({ id: nextTwoByTwoItemId(), name: "New item", x_score: 3, y_score: 3 });
          renderForm();
        }
      }, model.items.length >= limits.items));
      model.items.forEach((item, index) => {
        const box = document.createElement("div");
        box.className = "item";
        const line = document.createElement("div");
        line.className = "matrix-item-row";
        const label = document.createElement("span");
        label.className = "matrix-item-label";
        label.textContent = `Item ${index + 1}`;
        const nameInput = input(item.name || item.label, value => {
          item.name = value;
          delete item.label;
        }, "Item name");
        const xInput = input(item.x_score, value => item.x_score = Number(value), "X");
        xInput.className = "score-input";
        xInput.inputMode = "numeric";
        xInput.title = "X score 1-5";
        const yInput = input(item.y_score, value => item.y_score = Number(value), "Y");
        yInput.className = "score-input";
        yInput.inputMode = "numeric";
        yInput.title = "Y score 1-5";
        line.append(
          label,
          nameInput,
          xInput,
          yInput,
          button("Remove", () => {
            model.items.splice(index, 1);
            renderForm();
          })
        );
        box.appendChild(line);
        items.appendChild(box);
      });
      formRoot.appendChild(items);
    }

    function nextTwoByTwoItemId() {
      const nextNumber = (Array.isArray(model.items) ? model.items.length : 0) + 1;
      const existingPrefix = [...(model.items || [])]
        .reverse()
        .map(item => String(item.id || "").match(/^([A-Za-z]+)/))
        .find(Boolean);
      if (existingPrefix) return `${existingPrefix[1]}${nextNumber}`;
      const prefixes = {
        action_priority: "A",
        risk_benefit: "O",
        evidence_impact: "C",
        value_feasibility: "F",
        urgency_importance: "T",
        custom: "I"
      };
      return `${prefixes[model.preset] || "I"}${nextNumber}`;
    }

    function applyTwoByTwoPreset(preset) {
      const template = TWO_BY_TWO_PRESET_TEMPLATES[preset] || TWO_BY_TWO_PRESET_TEMPLATES.action_priority;
      const notes = model.notes || "";
      model = {
        diagram_type: "two_by_two_matrix",
        preset,
        title: template.title,
        language: "auto",
        notes,
        theme: "business_simple",
        score_scale: { min: 1, max: 5 },
        show_side_table: true,
        show_legend: true,
        output: "svg",
        items: template.items.map(item => ({ ...item }))
      };
      if (template.x_axis) model.x_axis = template.x_axis;
      if (template.y_axis) model.y_axis = template.y_axis;
      renderForm();
    }

    function renderFmeaForm() {
      model.diagram_type = "fmea_table";
      model.fmea_type = model.fmea_type || "process";
      model.language = model.language || "en";
      model.project = model.project && typeof model.project === "object" ? model.project : {};
      model.rows = Array.isArray(model.rows) ? model.rows : [];
      model.notes = Array.isArray(model.notes)
        ? model.notes
        : String(model.notes || "").split(/\r?\n/).map(note => note.trim()).filter(Boolean);

      formRoot.appendChild(row("Title", input(model.title, value => model.title = value, "Process FMEA")));
      formRoot.appendChild(row("Goal", input(model.goal, value => model.goal = value, "Visible FMEA goal")));
      formRoot.appendChild(row("FMEA Type", select(model.fmea_type, ["process", "design"], value => model.fmea_type = value)));

      const project = section("Project / Review Info", "Visible in the Review Info card. Owner here is the overall FMEA owner; row owner is edited per failure mode.");
      const projectGrid = document.createElement("div");
      projectGrid.className = "fmea-project-grid";
      projectGrid.append(
        fmeaField("Project", input(model.project.name, value => model.project.name = value, "Project name")),
        fmeaField("Owner", input(model.project.owner, value => model.project.owner = value, "Overall owner")),
        fmeaField("Review Frequency", input(model.project.review_frequency, value => model.project.review_frequency = value, "Weekly during pilot build")),
        fmeaField("Last Review Date", input(model.project.last_review_date, value => model.project.last_review_date = value, "YYYY-MM-DD"))
      );
      project.appendChild(projectGrid);
      formRoot.appendChild(project);

      const limits = LIMITS.fmea_table;
      const rows = section("FMEA Rows", `Use focused rows. S/O/D scores must be ${limits.scoreMin}-${limits.scoreMax}; RPN is calculated as S × O × D. The renderer compacts row margins first, then expands canvas height when needed.`);
      rows.querySelector(".section-title").appendChild(button("Add Row", () => {
        if (model.rows.length < limits.rows) {
          model.rows.push({
            id: `F${model.rows.length + 1}`,
            item_function: "New item / function",
            failure_mode: "Potential failure mode",
            failure_effects: [],
            failure_causes: [],
            prevention_controls: [],
            detection_controls: [],
            severity: 5,
            occurrence: 4,
            detection: 4,
            recommended_actions: [],
            owner: "",
            target_completion: "",
            status: "Open"
          });
          renderForm();
        }
      }, model.rows.length >= limits.rows));
      model.rows.forEach((item, index) => {
        normalizeFmeaRow(item, index);
        const box = roadmapCard(`Row ${item.id || index + 1}`, () => {
          model.rows.splice(index, 1);
          renderForm();
        });
        box.classList.add("fmea-row-card");
        const top = document.createElement("div");
        top.className = "fmea-row-top";
        top.append(
          fmeaField("ID", input(item.id, value => item.id = value, "F1")),
          fmeaField("Item / Function", input(item.item_function, value => item.item_function = value, "Item / function")),
          fmeaField("Failure Mode", input(item.failure_mode, value => item.failure_mode = value, "Potential failure mode"))
        );
        const meta = document.createElement("div");
        meta.className = "fmea-row-meta";
        meta.append(
          fmeaField("Owner", input(item.owner, value => item.owner = value, "Owner")),
          fmeaField("Target", input(item.target_completion, value => item.target_completion = value, "YYYY-MM-DD")),
          fmeaField("Status", select(item.status || "Open", ["Open", "Planned", "In Progress", "Completed", "At Risk", "Delayed"], value => item.status = value))
        );
        const scoreStrip = document.createElement("div");
        scoreStrip.className = "fmea-score-strip";
        scoreStrip.append(
          fmeaField("S", scoreInput(item.severity, value => item.severity = value, "Severity 1-10")),
          fmeaField("O", scoreInput(item.occurrence, value => item.occurrence = value, "Occurrence 1-10")),
          fmeaField("D", scoreInput(item.detection, value => item.detection = value, "Detection 1-10"))
        );
        const rpn = document.createElement("div");
        rpn.className = "fmea-rpn-preview";
        rpn.textContent = `RPN: ${fmeaRpn(item) || "-"}`;
        scoreStrip.appendChild(rpn);

        const textGrid = document.createElement("div");
        textGrid.className = "fmea-text-grid";
        textGrid.append(
          fmeaField("Effects", textarea(listToTextarea(item.failure_effects), value => item.failure_effects = textareaToList(value))),
          fmeaField("Causes", textarea(listToTextarea(item.failure_causes), value => item.failure_causes = textareaToList(value))),
          fmeaField("Prevention Controls", textarea(listToTextarea(item.prevention_controls), value => item.prevention_controls = textareaToList(value))),
          fmeaField("Detection Controls", textarea(listToTextarea(item.detection_controls), value => item.detection_controls = textareaToList(value))),
          fmeaField("Recommended Actions", textarea(listToTextarea(item.recommended_actions), value => item.recommended_actions = textareaToList(value)), "full")
        );
        box.append(top, meta, scoreStrip, textGrid);
        rows.appendChild(box);
      });
      formRoot.appendChild(rows);

      const notes = section("Notes", "Visible in the Notes panel. Keep each note short.");
      notes.appendChild(textarea(listToTextarea(model.notes), value => model.notes = textareaToList(value)));
      formRoot.appendChild(notes);
    }

    function normalizeFmeaRow(item, index) {
      item.id = item.id || `F${index + 1}`;
      item.failure_effects = Array.isArray(item.failure_effects) ? item.failure_effects : textareaToList(item.failure_effects);
      item.failure_causes = Array.isArray(item.failure_causes) ? item.failure_causes : textareaToList(item.failure_causes);
      item.prevention_controls = Array.isArray(item.prevention_controls) ? item.prevention_controls : textareaToList(item.prevention_controls);
      item.detection_controls = Array.isArray(item.detection_controls) ? item.detection_controls : textareaToList(item.detection_controls);
      item.recommended_actions = Array.isArray(item.recommended_actions) ? item.recommended_actions : textareaToList(item.recommended_actions);
      delete item.icon;
    }

    function fmeaRpn(item) {
      const s = Number(item.severity);
      const o = Number(item.occurrence);
      const d = Number(item.detection);
      if (![s, o, d].every(Number.isFinite)) return "";
      return s * o * d;
    }

    function listToTextarea(value) {
      if (Array.isArray(value)) return value.join("\n");
      return String(value || "");
    }

    function textareaToList(value) {
      if (Array.isArray(value)) return value;
      return String(value || "").split(/\r?\n/).map(item => item.trim()).filter(Boolean);
    }

    function renderRoadmapForm() {
      model.diagram_type = "roadmap_timeline";
      model.preset = model.preset || "swimlane_roadmap";
      model.language = model.language || "en";
      model.time_granularity = model.time_granularity || (model.preset === "milestone_timeline" ? "month" : "quarter");
      delete model.subtitle;
      formRoot.appendChild(row("Title", input(model.title, value => model.title = value, "Roadmap / Timeline")));
      formRoot.appendChild(row("Goal", input(model.goal, value => model.goal = value, "Visible goal statement")));
      formRoot.appendChild(row("Preset", select(model.preset, ["swimlane_roadmap", "milestone_timeline"], value => applyRoadmapPreset(value))));
      formRoot.appendChild(row("Time Granularity", select(model.time_granularity, ["month", "quarter"], value => applyRoadmapGranularity(value))));
      if (model.preset === "milestone_timeline") renderRoadmapMilestoneForm();
      else renderRoadmapSwimlaneForm();
    }

    function renderRoadmapSwimlaneForm() {
      model.lane_type = model.lane_type || "theme";
      model.time_periods = Array.isArray(model.time_periods) ? model.time_periods : (Array.isArray(model.periods) ? model.periods : []);
      delete model.periods;
      model.lanes = Array.isArray(model.lanes) ? model.lanes : [];
      model.initiatives = Array.isArray(model.initiatives) ? model.initiatives : [];
      model.milestones = Array.isArray(model.milestones) ? model.milestones : [];
      model.decision_points = Array.isArray(model.decision_points) ? model.decision_points : [];
      if (!model.time_periods.length) {
        model.time_periods = buildRoadmapPeriods(roadmapDateRange(), model.time_granularity || "quarter");
      }
      model.show_table = model.show_table !== false;
      model.show_summary_panel = model.show_summary_panel !== false;
      formRoot.appendChild(row("Lane Type", input(model.lane_type, value => model.lane_type = value, "theme")));
      const options = document.createElement("div");
      options.className = "toolbar";
      options.append(
        checkbox("Show table", model.show_table, value => model.show_table = value),
        checkbox("Show summary panel", model.show_summary_panel, value => model.show_summary_panel = value)
      );
      formRoot.appendChild(row("Options", options));
      renderRoadmapPeriods();
      renderRoadmapLanes();
      renderRoadmapInitiatives();
      renderRoadmapMarkers("Milestones", "milestones", "key_milestone");
      renderRoadmapMarkers("Decision Points", "decision_points", "decision");
      renderRoadmapNotes();
    }

    function renderRoadmapMilestoneForm() {
      model.milestones = Array.isArray(model.milestones) ? model.milestones : [];
      model.phases = Array.isArray(model.phases) ? model.phases : [];
      model.show_detail_cards = model.show_detail_cards !== false;
      model.show_table = model.show_table !== false;
      const options = document.createElement("div");
      options.className = "toolbar";
      options.append(
        checkbox("Show detail cards", model.show_detail_cards, value => model.show_detail_cards = value),
        checkbox("Show table", model.show_table, value => model.show_table = value)
      );
      formRoot.appendChild(row("Options", options));
      renderRoadmapTimelineMilestones();
      renderRoadmapPhases();
      renderRoadmapNotes();
    }

    function renderRoadmapPeriods() {
      const periods = section("Time Periods", "Edit the visible label and date range. Period IDs and header subtitles are generated from the selected granularity.");
      periods.querySelector(".section-title").appendChild(button("Add Period", () => {
        model.time_periods.push(nextRoadmapPeriod());
        renderForm();
      }));
      model.time_periods.forEach((period, index) => {
        normalizeRoadmapPeriod(period, model.time_granularity || "quarter");
        const line = document.createElement("div");
        line.className = "roadmap-row roadmap-period-row";
        line.append(
          input(period.label, value => period.label = value, "Label"),
          input(period.start, value => {
            period.start = value;
            normalizeRoadmapPeriod(period, model.time_granularity || "quarter");
          }, "Start"),
          input(period.end, value => {
            period.end = value;
            normalizeRoadmapPeriod(period, model.time_granularity || "quarter");
          }, "End"),
          button("Remove", () => {
            model.time_periods.splice(index, 1);
            renderForm();
          })
        );
        periods.appendChild(line);
      });
      formRoot.appendChild(periods);
    }

    function renderRoadmapLanes() {
      const lanes = section("Lanes", "Lane IDs are used by initiatives, milestones, and decision points.");
      lanes.querySelector(".section-title").appendChild(button("Add Lane", () => {
        model.lanes.push({ id: `lane_${model.lanes.length + 1}`, name: "New Lane", color: "blue" });
        renderForm();
      }));
      model.lanes.forEach((lane, index) => {
        const line = document.createElement("div");
        line.className = "roadmap-row roadmap-lane-row";
        line.append(
          input(lane.id, value => lane.id = value, "ID"),
          input(lane.name, value => lane.name = value, "Lane name"),
          select(lane.color || "blue", ["blue", "teal", "purple", "green", "orange", "red", "gray"], value => lane.color = value),
          button("Remove", () => {
            model.lanes.splice(index, 1);
            renderForm();
          })
        );
        lanes.appendChild(line);
      });
      formRoot.appendChild(lanes);
    }

    function renderRoadmapInitiatives() {
      const laneOptions = roadmapLaneOptions();
      const initiatives = section("Initiatives", "Bars keep their real start and end dates; labels are truncated in the diagram when needed.");
      initiatives.querySelector(".section-title").appendChild(button("Add Initiative", () => {
        model.initiatives.push({ id: `R${model.initiatives.length + 1}`, lane_id: laneOptions[0] || "lane_1", name: "New Initiative", start: "2026-01-01", end: "2026-03-31", owner: "", status: "planned" });
        renderForm();
      }));
      model.initiatives.forEach((item, index) => {
        const box = roadmapCard(`Initiative ${item.id || index + 1}`, () => {
            model.initiatives.splice(index, 1);
            renderForm();
        });
        const fields = document.createElement("div");
        fields.className = "roadmap-card-grid";
        fields.append(
          roadmapField("ID", input(item.id, value => item.id = value, "ID")),
          roadmapField("Name", input(item.name, value => item.name = value, "Initiative name")),
          roadmapField("Lane", select(item.lane_id, includeOption(laneOptions, item.lane_id), value => item.lane_id = value)),
          roadmapField("Status", select(item.status || "planned", ["planned", "in_progress", "completed", "at_risk"], value => item.status = value)),
          roadmapField("Start", input(item.start, value => item.start = value, "Start")),
          roadmapField("End", input(item.end, value => item.end = value, "End")),
          roadmapField("Owner", input(item.owner, value => item.owner = value, "Owner"))
        );
        box.appendChild(fields);
        initiatives.appendChild(box);
      });
      formRoot.appendChild(initiatives);
    }

    function renderRoadmapMarkers(title, field, defaultType) {
      const laneOptions = roadmapLaneOptions();
      const markers = section(title, "Markers use lane IDs and dates; same-date markers are automatically separated by the renderer.");
      markers.querySelector(".section-title").appendChild(button(`Add ${title.slice(0, -1)}`, () => {
        model[field].push({ id: nextRoadmapId(field), lane_id: laneOptions[0] || "lane_1", name: "New Marker", date: "2026-01-01", type: defaultType });
        renderForm();
      }));
      model[field].forEach((marker, index) => {
        const box = roadmapCard(`${title.slice(0, -1)} ${marker.id || index + 1}`, () => {
            model[field].splice(index, 1);
            renderForm();
        });
        const fields = document.createElement("div");
        fields.className = "roadmap-card-grid";
        fields.append(
          roadmapField("ID", input(marker.id, value => marker.id = value, "ID")),
          roadmapField("Name", input(marker.name, value => marker.name = value, "Name")),
          roadmapField("Lane", select(marker.lane_id, includeOption(laneOptions, marker.lane_id), value => marker.lane_id = value)),
          roadmapField("Date", input(marker.date, value => marker.date = value, "Date")),
          roadmapField("Type", select(marker.type || defaultType, ["key_milestone", "decision", "launch", "review", "milestone", "start"], value => marker.type = value))
        );
        box.appendChild(fields);
        markers.appendChild(box);
      });
      formRoot.appendChild(markers);
    }

    function renderRoadmapTimelineMilestones() {
      const milestones = section("Milestones", "Milestone rows feed the timeline nodes, detail cards, and milestone table.");
      milestones.querySelector(".section-title").appendChild(button("Add Milestone", () => {
        model.milestones.push({ id: `T${model.milestones.length + 1}`, name: "New Milestone", date: "2026-01-01", type: "milestone", owner: "", status: "planned", output: "" });
        renderForm();
      }));
      model.milestones.forEach((marker, index) => {
        const box = roadmapCard(`Milestone ${marker.id || index + 1}`, () => {
            model.milestones.splice(index, 1);
            renderForm();
        });
        const fields = document.createElement("div");
        fields.className = "roadmap-card-grid";
        fields.append(
          roadmapField("ID", input(marker.id, value => marker.id = value, "ID")),
          roadmapField("Name", input(marker.name, value => marker.name = value, "Milestone name")),
          roadmapField("Date", input(marker.date, value => marker.date = value, "Date")),
          roadmapField("Type", select(marker.type || "milestone", ["start", "milestone", "key_milestone", "decision", "review", "launch"], value => marker.type = value)),
          roadmapField("Status", select(marker.status || "planned", ["planned", "in_progress", "completed", "at_risk"], value => marker.status = value)),
          roadmapField("Owner", input(marker.owner, value => marker.owner = value, "Owner")),
          roadmapField("Output", input(marker.output, value => marker.output = value, "Milestone output or decision basis"), "full")
        );
        box.appendChild(fields);
        milestones.appendChild(box);
      });
      formRoot.appendChild(milestones);
    }

    function renderRoadmapPhases() {
      const phases = section("Phases", "Phase bands are time ranges below the milestone axis.");
      phases.querySelector(".section-title").appendChild(button("Add Phase", () => {
        model.phases.push({ name: "New Phase", start: "2026-01-01", end: "2026-03-31" });
        renderForm();
      }));
      model.phases.forEach((phase, index) => {
        const line = document.createElement("div");
        line.className = "roadmap-row roadmap-period-row";
        line.append(
          input(phase.name, value => phase.name = value, "Phase name"),
          input(phase.start, value => phase.start = value, "Start"),
          input(phase.end, value => phase.end = value, "End"),
          button("Remove", () => {
            model.phases.splice(index, 1);
            renderForm();
          })
        );
        phases.appendChild(line);
      });
      formRoot.appendChild(phases);
    }

    function renderRoadmapNotes() {
      model.notes = Array.isArray(model.notes)
        ? model.notes
        : String(model.notes || "").split(/\r?\n/).map(note => note.trim()).filter(Boolean);
      const notes = section("Notes", "Visible in the notes or summary area. Keep each note short.");
      notes.querySelector(".section-title").appendChild(button("Add Note", () => {
        model.notes.push("New note");
        renderForm();
      }));
      model.notes.forEach((note, index) => {
        const line = document.createElement("div");
        line.className = "inline";
        line.append(
          input(note, value => model.notes[index] = value, "Note"),
          button("Remove", () => {
            model.notes.splice(index, 1);
            renderForm();
          })
        );
        notes.appendChild(line);
      });
      formRoot.appendChild(notes);
    }

    function roadmapLaneOptions() {
      const options = (Array.isArray(model.lanes) ? model.lanes : [])
        .map(lane => lane.id)
        .filter(Boolean);
      return options.length ? options : ["lane_1"];
    }

    function includeOption(options, value) {
      const clean = String(value || "");
      if (!clean || options.includes(clean)) return options;
      return [clean, ...options];
    }

    function nextRoadmapId(field) {
      const prefix = field === "decision_points" ? "D" : "M";
      return `${prefix}${(Array.isArray(model[field]) ? model[field].length : 0) + 1}`;
    }

    function dateFromIso(value) {
      const match = /^(\d{4})-(\d{2})-(\d{2})$/.exec(String(value || "").trim());
      if (!match) return null;
      const year = Number(match[1]);
      const month = Number(match[2]);
      const day = Number(match[3]);
      const date = new Date(Date.UTC(year, month - 1, day));
      return Number.isNaN(date.getTime()) ? null : date;
    }

    function pad2(value) {
      return String(value).padStart(2, "0");
    }

    function formatIsoDate(date) {
      return `${date.getUTCFullYear()}-${pad2(date.getUTCMonth() + 1)}-${pad2(date.getUTCDate())}`;
    }

    function startOfMonthDate(date) {
      return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth(), 1));
    }

    function endOfMonthDate(date) {
      return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + 1, 0));
    }

    function startOfQuarterDate(date) {
      const quarterMonth = Math.floor(date.getUTCMonth() / 3) * 3;
      return new Date(Date.UTC(date.getUTCFullYear(), quarterMonth, 1));
    }

    function endOfQuarterDate(date) {
      const start = startOfQuarterDate(date);
      return new Date(Date.UTC(start.getUTCFullYear(), start.getUTCMonth() + 3, 0));
    }

    function addMonths(date, count) {
      return new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + count, 1));
    }

    function roadmapQuarter(date) {
      return Math.floor(date.getUTCMonth() / 3) + 1;
    }

    function roadmapMonthName(monthIndex) {
      return ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"][monthIndex];
    }

    function roadmapPeriodLabel(start, granularity) {
      if (granularity === "month") return `${start.getUTCFullYear()} ${roadmapMonthName(start.getUTCMonth())}`;
      return `${start.getUTCFullYear()} Q${roadmapQuarter(start)}`;
    }

    function roadmapPeriodSubtitle(start, granularity) {
      if (granularity === "month") return "";
      const firstMonth = Math.floor(start.getUTCMonth() / 3) * 3;
      return `${roadmapMonthName(firstMonth)} - ${roadmapMonthName(firstMonth + 2)}`;
    }

    function roadmapPeriodId(start, granularity) {
      if (granularity === "month") return `${start.getUTCFullYear()}${pad2(start.getUTCMonth() + 1)}`;
      return `${start.getUTCFullYear()}Q${roadmapQuarter(start)}`;
    }

    function makeRoadmapPeriod(startDate, granularity) {
      const start = granularity === "month" ? startOfMonthDate(startDate) : startOfQuarterDate(startDate);
      const end = granularity === "month" ? endOfMonthDate(start) : endOfQuarterDate(start);
      return {
        id: roadmapPeriodId(start, granularity),
        label: roadmapPeriodLabel(start, granularity),
        subtitle: roadmapPeriodSubtitle(start, granularity),
        start: formatIsoDate(start),
        end: formatIsoDate(end)
      };
    }

    function normalizeRoadmapPeriod(period, granularity) {
      const start = dateFromIso(period.start);
      if (!start) return;
      period.id = roadmapPeriodId(start, granularity);
      period.subtitle = roadmapPeriodSubtitle(start, granularity);
      if (!String(period.label || "").trim()) {
        period.label = roadmapPeriodLabel(start, granularity);
      }
    }

    function roadmapDateRange() {
      const dates = [];
      const addDate = value => {
        const date = dateFromIso(value);
        if (date) dates.push(date);
      };
      (Array.isArray(model.time_periods) ? model.time_periods : []).forEach(period => {
        addDate(period.start);
        addDate(period.end);
      });
      (Array.isArray(model.initiatives) ? model.initiatives : []).forEach(item => {
        addDate(item.start);
        addDate(item.end);
      });
      (Array.isArray(model.milestones) ? model.milestones : []).forEach(marker => addDate(marker.date));
      (Array.isArray(model.decision_points) ? model.decision_points : []).forEach(marker => addDate(marker.date));
      (Array.isArray(model.phases) ? model.phases : []).forEach(phase => {
        addDate(phase.start);
        addDate(phase.end);
      });
      if (!dates.length) {
        return { start: new Date(Date.UTC(2025, 3, 1)), end: new Date(Date.UTC(2026, 2, 31)) };
      }
      dates.sort((a, b) => a.getTime() - b.getTime());
      return { start: dates[0], end: dates[dates.length - 1] };
    }

    function buildRoadmapPeriods(range, granularity) {
      const start = granularity === "month" ? startOfMonthDate(range.start) : startOfQuarterDate(range.start);
      const end = granularity === "month" ? endOfMonthDate(range.end) : endOfQuarterDate(range.end);
      const step = granularity === "month" ? 1 : 3;
      const periods = [];
      let cursor = start;
      while (cursor.getTime() <= end.getTime() && periods.length < 120) {
        periods.push(makeRoadmapPeriod(cursor, granularity));
        cursor = addMonths(cursor, step);
      }
      return periods.length ? periods : [makeRoadmapPeriod(new Date(Date.UTC(2025, 3, 1)), granularity)];
    }

    function nextRoadmapPeriod() {
      const granularity = model.time_granularity === "month" ? "month" : "quarter";
      const periods = Array.isArray(model.time_periods) ? model.time_periods : [];
      const lastEnd = periods.length ? dateFromIso(periods[periods.length - 1].end) : null;
      const nextStart = lastEnd ? addMonths(startOfMonthDate(lastEnd), 1) : new Date(Date.UTC(2026, 0, 1));
      return makeRoadmapPeriod(nextStart, granularity);
    }

    function applyRoadmapGranularity(value) {
      const granularity = value === "month" ? "month" : "quarter";
      model.time_granularity = granularity;
      if (model.preset === "swimlane_roadmap") {
        model.time_periods = buildRoadmapPeriods(roadmapDateRange(), granularity);
      }
      renderForm();
    }

    function applyRoadmapPreset(preset) {
      const template = ROADMAP_PRESET_TEMPLATES[preset] || ROADMAP_PRESET_TEMPLATES.swimlane_roadmap;
      model = JSON.parse(JSON.stringify(template));
      delete model.subtitle;
      renderForm();
    }

    $("newBtn").addEventListener("click", () => loadTemplate().catch(error => setStatus(error.message, "error")));
    $("loadBtn").addEventListener("click", () => loadFile());
    fileInput.addEventListener("change", () => loadSelectedFile(fileInput.files[0]).catch(error => setStatus(error.message, "error")));
    $("loadRecentBtn").addEventListener("click", () => loadRecent().catch(error => setStatus(error.message, "error")));
    $("saveBtn").addEventListener("click", () => saveJson().catch(error => setStatus(error.message, "error")));
    $("saveAsBtn").addEventListener("click", () => openSaveAsDialog());
    $("saveAsJsonBtn").addEventListener("click", () => saveAsSource("json").catch(error => setStatus(error.message, "error")));
    $("saveAsMarkdownBtn").addEventListener("click", () => saveAsSource("markdown").catch(error => setStatus(error.message, "error")));
    $("saveAsCancelBtn").addEventListener("click", () => closeSaveAsDialog());
    saveAsDialog.addEventListener("click", event => {
      if (event.target === saveAsDialog) closeSaveAsDialog();
    });
    $("renderBtn").addEventListener("click", () => renderSvg().catch(error => setStatus(error.message, "error")));
    $("exportBtn").addEventListener("click", () => exportPng().catch(error => setStatus(error.message, "error")));
    $("openSvgBtn").addEventListener("click", () => openSvgStandalone());
    $("openBtn").addEventListener("click", () => openFolder().catch(error => setStatus(error.message, "error")));
    $("helpBtn").addEventListener("click", () => openHelpDialog());
    $("helpCloseBtn").addEventListener("click", () => closeHelpDialog());
    helpDialog.addEventListener("click", event => {
      if (event.target === helpDialog) closeHelpDialog();
    });
    document.addEventListener("keydown", event => {
      if (event.key === "Escape") {
        closeSaveAsDialog();
        closeHelpDialog();
      }
    });
    $("zoomOutBtn").addEventListener("click", () => setPreviewZoom(previewZoom - 0.1));
    $("zoomInBtn").addEventListener("click", () => setPreviewZoom(previewZoom + 0.1));
    $("zoomFitBtn").addEventListener("click", () => setPreviewZoom(1));
    typeEl.addEventListener("change", () => {
      nameEl.value = currentType() === "fishbone"
        ? "my-analysis"
        : currentType() === "fault_tree"
          ? "startup-failure"
          : currentType() === "exclusion_tree"
            ? "startup-checks"
            : currentType() === "two_by_two_matrix"
              ? "priority-matrix"
              : currentType() === "roadmap_timeline"
                ? "product-roadmap"
                : "process-fmea";
      loadTemplate().catch(error => setStatus(error.message, "error"));
    });
    nameEl.addEventListener("input", () => updateValidation());

    refreshRecent();
    loadTemplate().catch(error => setStatus(error.message, "error"));
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
