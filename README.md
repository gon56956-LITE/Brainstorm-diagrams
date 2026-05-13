# brainstorm-diagrams

`brainstorm-diagrams` is a Codex skill for generating clean, PPT-ready structured brainstorming diagrams.

Version `0.1.0` implements a deterministic SVG fishbone / Ishikawa renderer with a business-simple visual style.

## What This Is

`brainstorm-diagrams` is a Codex skill with a small local toolchain inside it.

From Codex's perspective, it is a skill: `SKILL.md` and the reference files define when to use it, how inputs should be interpreted, what visual rules to follow, and how output should be verified.

From a non-technical user's perspective, it is also a small local tool: double-click launchers and scripts can create, regenerate, and verify fishbone SVG files without writing Python code.

In short:

```text
skill = usage rules, layout rules, and workflow knowledge
tools = the local scripts and double-click launchers that perform the work
```

## What Works Now

- `diagram_type="fishbone"`
- JSON input
- Structured Markdown input
- Codex-assisted natural-language fishbone drafting into editable Markdown
- SVG output
- PNG export from generated work SVG files
- Automatic canvas expansion for dense fishbone content while keeping fonts, cards, and line widths fixed
- Lucide-based blue badge candidate library, with confirmed category mappings used by the renderer
- Default six-category fishbone when categories are missing

## Not Implemented Yet

- Redrawing from existing fishbone files
- Redrawing from whiteboard photos
- Other diagram types

## Non-Technical User Workflow

The easiest way to use this package is to double-click:

```text
鱼骨图工具.cmd
```

English fallback:

```text
fishbone_tool.cmd
```

The menu can create a new fishbone diagram, regenerate a work SVG after editing, or run verification.

Menu options:

- `1. Create new fishbone diagram`
  - Enter a diagram name, such as `my-analysis`.
  - Names may use lowercase letters, numbers, hyphen, and underscore only.
  - Choose Markdown unless you specifically need JSON.
  - The tool creates `work/my-analysis.md` and `work/my-analysis.svg`.
- `2. Regenerate work SVG`
  - Use this after editing `work/my-analysis.md` or `work/my-analysis.json`.
  - Enter the same diagram name, such as `my-analysis`.
  - The tool updates `work/my-analysis.svg`.
- `3. Export work SVG to PNG`
  - Converts `work/my-analysis.svg` to `work/my-analysis.png`.
  - Use PNG for quick sharing in chat, email, Word, or places where SVG is inconvenient.
- `4. Verify testcases and templates`
  - Runs the built-in checks for renderer layout, maintained testcases, and templates.
- `5. Render stresscases`
  - Regenerates intentionally dense SVGs for manual visual review after layout changes.
- `6. Verify stresscases`
  - Checks the optional stresscase structure without making it a formal regression testcase.

Typical usage:

1. Double-click `鱼骨图工具.cmd`.
2. Choose `1` to create a new diagram.
3. Edit the generated file in `work/`.
4. Double-click `鱼骨图工具.cmd` again.
5. Choose `2` to regenerate the SVG.
6. Open the SVG in `work/` to inspect the result.

The `work/` folder is for your own diagrams. The `testcases/` folder is for regression tests, `templates/` is for protected starting templates, `stresscases/` is for optional manual visual checks, and `naturalcases/` is for natural-language extraction examples.

Diagram names are file names under `work/`. Use safe names such as `my-analysis` or `customer_complaints_v1`; do not enter spaces, folders, `..`, or full paths.

## Natural-Language Drafting

Codex can turn raw customer feedback or workshop notes into a structured fishbone Markdown draft before rendering. This is a skill workflow, not a local `.cmd` menu feature: Codex performs the semantic extraction, then the existing local tools render the resulting Markdown.

Example prompt:

```text
根据下面客户反馈生成鱼骨图草稿，文件名 customer-complaints：

最近客户投诉集中在交付周期变长、包装破损、售后响应慢、现场安装说明不清楚、
不同供应批次质量波动，以及内部测试覆盖不到真实使用场景。
```

Expected output:

- `work/customer-complaints.md`
- `work/customer-complaints.svg`
- Optional `work/customer-complaints.png`

Natural-language drafts should use categories found in the source text, not default categories. See `references/natural_language_extraction.md`.
For a reusable Codex prompt shape, see `references/natural_language_prompt_template.md`.
Use `references/natural_language_review_checklist.md` to review whether the generated draft stayed faithful to the source text.
See `naturalcases/` for source text and expected Markdown examples.

## Badge Library

Fishbone category cards use simple circular badges. The renderer includes a small set of hand-drawn fallback icons and a curated Lucide SVG candidate library under `assets/lucide-candidates/`.

Only confirmed semantic mappings are active in the renderer. For example, `system` maps to `workflow`, `architecture` maps to `network`, `materials` maps to `boxes`, and `business` maps to `chart-no-axes-column-increasing`. Other Lucide SVGs remain in the candidate library for future product design, manufacturing, industrial application, communication, network, data-center, validation, reliability, and field-use scenarios.

Regenerate the blue-styled review board with:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_lucide_candidate_catalog.py
```

Output:

```text
work/lucide-badge-candidates.svg
```

`scripts/verify_testcases.py` protects the key Lucide files and checks that the review catalog still renders as well-formed SVG.

## Command-Line Usage

Command-line usage is available for technical users or automation:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\new_fishbone.py my-analysis --format md
```

This creates `work/my-analysis.md` and `work/my-analysis.svg` from the Markdown template. Use `--format json` for the JSON template. Existing work files are not overwritten unless `--force` is passed.

After editing a work input, regenerate its SVG with:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_work.py my-analysis
```

If both `work/my-analysis.md` and `work/my-analysis.json` exist, pass `--format md` or `--format json`.

Export an existing work SVG to PNG:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\export_png.py my-analysis
```

SVG remains the primary editable output. PNG is a convenience format for quick sharing.
The PNG exporter is intended for SVGs generated by this fishbone tool, not arbitrary third-party SVG files.

Render any input file directly:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\generate_diagram.py templates\fishbone.template.json output.svg
```

Markdown input works the same way:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\generate_diagram.py templates\fishbone.template.md output.svg
```

Do not use raw `.txt` input as a semantic extractor. Plain text passed directly to `generate_diagram.py` is treated as a simple topic fallback; Codex should first convert natural language into structured Markdown.

Verify all maintained testcases, templates, and layout invariants:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\verify_testcases.py
```

Regenerate optional stresscase SVGs for manual visual review:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_stresscases.py
```

Verify optional stresscase structure:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\verify_stresscases.py
```

Verify natural-language extraction examples:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\verify_naturalcases.py
```

## Developer Maintenance

Use `references/maintenance_checklist.md` before finishing renderer, badge, natural-language, testcase, template, or launcher changes.

For substantial changes, run the full verification set:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\verify_testcases.py
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\verify_stresscases.py
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\verify_naturalcases.py
cmd /c fishbone_tool.cmd verify
```

## Structured Markdown Format

```markdown
# Improve Product Reliability

## User Needs
- Usage scenario
- Pain points
- Expectation

## Performance
- Accuracy
- Speed
- Capacity
```

## Subcategories

Indented bullets turn a primary item into a subcategory. Subcategory cards are rendered without badges, and each subcategory can show up to three child causes.
Primary entries alternate left and right around the main branch. Subcategories use a horizontal connector and an outside curly brace for child bullets.

```markdown
# Customer Field Failures

## People
- Training
  - Onboarding
  - Skill matrix
  - Certification
- Role clarity
```

After generation, the CLI prints `Diagnostics:` so users can see when categories or item lists were defaulted, truncated, or ignored.
Dense diagrams may also report that the canvas was expanded. Sparse diagrams stay at the base `1920x1080` size; crowded diagrams grow the SVG canvas so the category groups keep their normal readable size instead of being squeezed together.

## JSON Format

See `templates/fishbone.template.json` and `references/input_contract.md`.

## Templates

- `templates/fishbone.template.md`
- `templates/fishbone.template.json`

Copy a template, edit the content, then render it with `scripts/generate_diagram.py`.

## Work Files

`scripts/new_fishbone.py` creates user-owned inputs and SVGs in `work/`. This directory is for local authoring output, separate from `testcases/` regression files.

## Stresscases

`stresscases/` contains intentionally dense diagrams for manual visual review. They are useful after layout changes because they make spacing problems obvious, but they are not part of the maintained regression testcase set.

`scripts/verify_stresscases.py` protects this area from structural drift: it checks that the full-density SVG expands beyond the base canvas, keeps the topic block on the right, preserves the expected category and brace counts, and does not render `README.md` as an SVG.

Use `references/visual_review_checklist.md` when inspecting the generated stresscase by eye.

- `stresscases/full-stress.md` -> `stresscases/full-stress.svg`

## Naturalcases

`naturalcases/` contains source text and expected structured Markdown examples for Codex-assisted natural-language fishbone drafting. It does not store generated SVG or PNG outputs.

- `naturalcases/reliability-power-drop.source.txt` -> `naturalcases/reliability-power-drop.expected.md`
- `naturalcases/optical-module-stability.source.txt` -> `naturalcases/optical-module-stability.expected.md`

The optical-module case covers an English product design / manufacturing / application scenario and protects confirmed Lucide badge mappings for technical categories.

## Maintained Testcases

- `testcases/fishbone.input.example.json` -> `testcases/fishbone.output.example.svg`
- `testcases/fishbone.subcategory.example.md` -> `testcases/fishbone.subcategory.output.md.svg`
- `testcases/fishbone.subcategory.example.json` -> `testcases/fishbone.subcategory.output.json.svg`
- `testcases/fishbone.five-primary.example.json` -> `testcases/fishbone.five-primary.output.svg`
- `testcases/fishbone.five-subcategories.example.json` -> `testcases/fishbone.five-subcategories.output.svg`
- `testcases/fishbone.dense-collision.example.json` -> `testcases/fishbone.dense-collision.output.svg`
