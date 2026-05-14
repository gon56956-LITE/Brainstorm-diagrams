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


ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "templates"
GENERATE = ROOT / "scripts" / "generate_diagram.py"
EXPORT_FISHBONE = ROOT / "scripts" / "export_png.py"
EXPORT_FAULT_TREE = ROOT / "scripts" / "export_fault_tree_png.py"
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
        raise ValueError("diagram_type must be fishbone or fault_tree.")
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
      grid-template-columns: minmax(500px, 0.95fr) minmax(520px, 1.05fr);
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
    button {
      border: 1px solid #a9bfda;
      border-radius: 6px;
      padding: 8px 11px;
      background: #fff;
      color: var(--navy);
      font-weight: 700;
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
      <span>Edit JSON-backed fishbone and fault-tree diagrams without touching Markdown.</span>
    </div>
  </header>
  <main>
    <section class="panel editor">
      <div class="row">
        <label for="diagramType">Diagram type</label>
        <select id="diagramType">
          <option value="fishbone">Fishbone</option>
          <option value="fault_tree">Fault Tree</option>
        </select>
      </div>
      <div class="row">
        <label for="diagramName">Diagram name</label>
        <input id="diagramName" value="my-analysis" pattern="[a-z0-9][a-z0-9_-]{0,63}">
      </div>
      <div class="toolbar">
        <button id="newBtn">Load Template</button>
        <button id="loadBtn">Load Saved</button>
        <button id="saveBtn">Save JSON</button>
        <button id="renderBtn" class="primary">Render SVG</button>
        <button id="exportBtn">Export PNG</button>
        <button id="openBtn">Open Work Folder</button>
      </div>
      <div id="status" class="status"></div>
      <div id="formRoot"></div>
    </section>
    <section class="panel preview">
      <div class="preview-toolbar">
        <strong>SVG Preview</strong>
        <span id="previewMeta" class="status"></span>
      </div>
      <div id="previewBox"><div class="empty">Click Render SVG to preview the diagram.</div></div>
    </section>
  </main>
  <script>
    const LIMITS = {
      fishbone: { categories: 8, minCategories: 4, entries: 5, children: 3 },
      fault_tree: { first: 5, children: 4, nestedChildren: 4 }
    };
    let model = {};

    const $ = (id) => document.getElementById(id);
    const typeEl = $("diagramType");
    const nameEl = $("diagramName");
    const formRoot = $("formRoot");
    const statusEl = $("status");
    const previewBox = $("previewBox");
    const previewMeta = $("previewMeta");

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

    async function loadSaved() {
      const data = await api(`/api/load?diagram_type=${encodeURIComponent(currentType())}&name=${encodeURIComponent(safeName())}`);
      model = data.data;
      renderForm();
      await loadSvgIfExists();
      setStatus("Saved JSON loaded.", "ok");
    }

    async function saveJson() {
      syncDiagramType();
      const result = await api("/api/save", {
        method: "POST",
        body: JSON.stringify({ diagram_type: currentType(), name: safeName(), data: model })
      });
      setStatus(result.message, "ok");
    }

    async function renderSvg() {
      syncDiagramType();
      const result = await api("/api/render", {
        method: "POST",
        body: JSON.stringify({ diagram_type: currentType(), name: safeName(), data: model })
      });
      previewBox.innerHTML = result.svg;
      previewMeta.textContent = safeName() + ".svg";
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

    async function loadSvgIfExists() {
      try {
        const response = await fetch(`/api/svg?diagram_type=${encodeURIComponent(currentType())}&name=${encodeURIComponent(safeName())}`);
        const text = await response.text();
        if (response.ok) {
          previewBox.innerHTML = text;
          previewMeta.textContent = safeName() + ".svg";
        }
      } catch (_error) {}
    }

    function syncDiagramType() {
      model.diagram_type = currentType();
    }

    function input(value, onInput, placeholder = "") {
      const el = document.createElement("input");
      el.value = value || "";
      el.placeholder = placeholder;
      el.addEventListener("input", () => onInput(el.value));
      return el;
    }

    function textarea(value, onInput) {
      const el = document.createElement("textarea");
      el.value = value || "";
      el.addEventListener("input", () => onInput(el.value));
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
      el.addEventListener("change", () => onChange(el.value));
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
      else renderFaultTreeForm();
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
            sub.className = "nested item";
            const subHead = document.createElement("div");
            subHead.className = "item-head";
            subHead.appendChild(input(item.subcategory, value => item.subcategory = value, "Subcategory"));
            subHead.appendChild(button("Remove", () => {
              category.items.splice(itemIndex, 1);
              renderForm();
            }));
            sub.appendChild(subHead);
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
              sub.appendChild(line);
            });
            sub.appendChild(button("Add Child Cause", () => {
              if (item.items.length < limits.children) {
                item.items.push("New child cause");
                renderForm();
              }
            }, item.items.length >= limits.children));
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
      const events = section("First-Level Events", `Up to ${limits.first} first-level intermediate events. Each intermediate event supports up to ${limits.children} direct children. Nested intermediate events can contain up to ${limits.nestedChildren} basic leaves.`);
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

    $("newBtn").addEventListener("click", () => loadTemplate().catch(error => setStatus(error.message, "error")));
    $("loadBtn").addEventListener("click", () => loadSaved().catch(error => setStatus(error.message, "error")));
    $("saveBtn").addEventListener("click", () => saveJson().catch(error => setStatus(error.message, "error")));
    $("renderBtn").addEventListener("click", () => renderSvg().catch(error => setStatus(error.message, "error")));
    $("exportBtn").addEventListener("click", () => exportPng().catch(error => setStatus(error.message, "error")));
    $("openBtn").addEventListener("click", () => openFolder().catch(error => setStatus(error.message, "error")));
    typeEl.addEventListener("change", () => {
      nameEl.value = currentType() === "fishbone" ? "my-analysis" : "startup-failure";
      loadTemplate().catch(error => setStatus(error.message, "error"));
    });

    loadTemplate().catch(error => setStatus(error.message, "error"));
  </script>
</body>
</html>
"""


if __name__ == "__main__":
    raise SystemExit(main())
