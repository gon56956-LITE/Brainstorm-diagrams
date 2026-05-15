#!/usr/bin/env python3
"""Local HTML editor for brainstorm diagrams."""

from __future__ import annotations

import argparse
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
from urllib.parse import parse_qs, urlparse

from generate_diagram import parse_structured_markdown


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
GENERATE = ROOT / "scripts" / "generate_diagram.py"
EXPORT_FISHBONE = ROOT / "scripts" / "export_png.py"
EXPORT_FAULT_TREE = ROOT / "scripts" / "export_fault_tree_png.py"
EXPORT_EXCLUSION_TREE = ROOT / "scripts" / "export_exclusion_tree_png.py"
PYTHON = Path(sys.executable)
SAFE_NAME_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,63}$")

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
        "label": "Exclusion Tree",
        "work": ROOT / "work" / "exclusion-tree",
        "template": TEMPLATES / "exclusion-tree.template.json",
        "export": EXPORT_EXCLUSION_TREE,
    },
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Start the local brainstorm diagram HTML editor.")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8765, help="Port to bind (default: 8765)")
    parser.add_argument("--no-open", action="store_true", help="Do not open the browser automatically")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    server = ThreadingHTTPServer((args.host, args.port), DiagramBuilderHandler)
    url = f"http://{args.host}:{args.port}/"
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
        raise ValueError("diagram_type must be fishbone, fault_tree, or exclusion_tree.")
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
    #previewBox svg {
      width: 100%;
      height: auto;
      background: #fff;
      border: 1px solid var(--line);
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
      <span>Edit JSON-backed fishbone, fault-tree, and exclusion-tree diagrams without touching Markdown.</span>
    </div>
  </header>
  <main>
    <section class="panel editor">
      <div class="row">
        <label for="diagramType">Diagram type</label>
        <select id="diagramType">
          <option value="fishbone">Fishbone</option>
          <option value="fault_tree">Fault Tree</option>
          <option value="exclusion_tree">Exclusion Tree</option>
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
          <li>Exclusion Tree: 1 target problem, recommended 3-6 sequential check points, each check has one Yes path and one No cause card.</li>
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
      exclusion_tree: { checks: 6, minChecks: 3 }
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
      if (diagramType === "exclusion_tree") return "Exclusion Tree";
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
      const svg = previewBox.querySelector("svg");
      if (!svg) return;
      svg.style.width = Math.round(previewZoom * 100) + "%";
      svg.style.maxWidth = "none";
      svg.style.height = "auto";
    }

    function setPreviewSvg(svgText) {
      previewBox.innerHTML = svgText;
      applyPreviewZoom();
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
      } else {
        requireText(errors, "Problem", oneLanguageValue(model.problem, "text"));
        const checks = Array.isArray(model.checks) ? model.checks : [];
        if (checks.length < 1) errors.push("Exclusion tree needs at least 1 check point.");
        if (checks.length > LIMITS.exclusion_tree.checks) errors.push(`Exclusion tree supports up to ${LIMITS.exclusion_tree.checks} check points.`);
        checks.forEach((check, index) => {
          requireText(errors, `Check Point ${index + 1} question`, oneLanguageValue(check, "text"));
          requireText(errors, `Check Point ${index + 1} fail cause`, oneLanguageValue(check.fail_conclusion, "text"));
        });
        requireText(errors, "Final Pass Conclusion", oneLanguageValue(model.final_pass_conclusion, "text"));
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
      setPreviewSvg(result.svg);
      previewMeta.textContent = safeName() + ".svg";
      rememberRecent();
      setStatus(result.message, "ok");
    }

    async function exportPng() {
      const result = await api("/api/export", {
        method: "POST",
        body: JSON.stringify({ diagram_type: currentType(), name: safeName() })
      });
      setStatus(result.message, "ok");
    }

    async function openFolder() {
      const result = await api("/api/open-folder", {
        method: "POST",
        body: JSON.stringify({ diagram_type: currentType() })
      });
      setStatus(result.message, "ok");
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

    async function loadSvgIfExists() {
      try {
        const response = await fetch(`/api/svg?diagram_type=${encodeURIComponent(currentType())}&name=${encodeURIComponent(safeName())}`);
        const text = await response.text();
        if (response.ok) {
          setPreviewSvg(text);
          previewMeta.textContent = safeName() + ".svg";
        }
      } catch (_error) {}
    }

    function syncDiagramType() {
      model.diagram_type = currentType();
      if (model.diagram_type === "exclusion_tree") cleanExclusionTreeModel();
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

    function renderForm() {
      formRoot.innerHTML = "";
      if (currentType() === "fishbone") renderFishboneForm();
      else if (currentType() === "fault_tree") renderFaultTreeForm();
      else renderExclusionTreeForm();
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
      const checks = section("Check Points", `Use ${limits.minChecks}-${limits.checks} sequential checks. Each check has one Yes/Pass path and one No/Fail conclusion.`);
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
      nameEl.value = currentType() === "fishbone" ? "my-analysis" : currentType() === "fault_tree" ? "startup-failure" : "startup-checks";
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
