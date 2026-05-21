# brainstorm-diagrams

`brainstorm-diagrams` is a Codex skill for generating clean, PPT-ready structured brainstorming diagrams.

Version `0.5.0` implements deterministic SVG renderers for business-simple fishbone / Ishikawa diagrams, fault tree analysis diagrams, sequential exclusion-tree troubleshooting diagrams, two-by-two prioritization matrices, and roadmap timelines.

## What This Is

`brainstorm-diagrams` is a Codex skill with a small local toolchain inside it.

From Codex's perspective, it is a skill: `SKILL.md` and the reference files define when to use it, how inputs should be interpreted, what visual rules to follow, and how output should be verified.

From a non-technical user's perspective, it is also a small local tool: double-click launchers and scripts can create, regenerate, and verify fishbone, fault-tree, exclusion-tree, two-by-two matrix, and roadmap timeline SVG files without writing Python code.

In short:

```text
skill = usage rules, layout rules, and workflow knowledge
tools = the local scripts and double-click launchers that perform the work
```

## What Works Now

- `diagram_type="fishbone"`
- `diagram_type="fault_tree"`
- `diagram_type="exclusion_tree"`
- `diagram_type="two_by_two_matrix"`
- `diagram_type="roadmap_timeline"`
- `diagram_type="fmea_table"`
- JSON input
- Structured Markdown input
- Fault tree top events, event detail panels, AND/OR gates, intermediate events, and basic event leaves
- Fault tree nested mixed-gate subtrees, such as an OR branch containing an AND condition
- Sequential exclusion-tree target problems, one main checkpoint path, Yes/Pass continuation paths, No/Fail root-cause cards, and final no-issue-found cards
- Codex-assisted natural-language fishbone, fault-tree, exclusion-tree, two-by-two matrix, and roadmap timeline drafting into editable Markdown
- Roadmap timeline JSON and structured Markdown rendering for swimlane roadmaps and milestone timelines
- SVG output
- PNG export from generated work SVG files
- Automatic canvas expansion for dense fishbone and nested fault-tree content while keeping fonts, cards, and line widths fixed
- Lucide-based blue badge candidate library, with confirmed category mappings used by the renderer
- Default six-category fishbone when categories are missing

## Not Implemented Yet

- Redrawing from existing fishbone files
- Redrawing from whiteboard photos
- Probability calculation, Boolean simplification, and dynamic fault tree semantics
- Parallel exclusion-tree lanes and complex nested decision logic beyond the linear Yes/No troubleshooting path

## Non-Technical User Workflow

The easiest way to use this package is to double-click:

```text
鱼骨图工具.cmd
```

English fallback:

```text
fishbone_tool.cmd
```

Fault tree has its own non-technical launcher:

```text
故障树工具.cmd
```

English fallback:

```text
fault_tree_tool.cmd
```

Exclusion tree has its own non-technical launcher:

```text
排除树工具.cmd
```

English fallback:

```text
exclusion_tree_tool.cmd
```

Two-by-two matrix has its own non-technical launcher:

```text
二乘二矩阵工具.cmd
```

English fallback:

```text
two_by_two_matrix_tool.cmd
```

Roadmap timeline has its own non-technical launcher:

```text
路线图时间线工具.cmd
```

English fallback:

```text
roadmap_timeline_tool.cmd
```

FMEA table has its own non-technical launcher:

```text
fmea_table_tool.cmd
```

For a browser-based editor, use the unified local builder:

```text
图表编辑器.cmd
```

English fallback:

```text
diagram_builder.cmd
```

The fishbone, fault-tree, exclusion-tree, two-by-two matrix, and roadmap timeline menus can create a new diagram, regenerate a work SVG after editing, export PNG, or run verification. The browser builder edits structured JSON for fishbone, fault-tree, exclusion-tree, two-by-two matrix, and roadmap timeline through a local HTML form, saves into the matching `work/<diagram-type>/` folder, and reuses the same SVG/PNG renderers.

Menu options:

- `1. Create new fishbone diagram`
  - Enter a diagram name, such as `my-analysis`.
  - Names may use lowercase letters, numbers, hyphen, and underscore only.
  - Choose Markdown unless you specifically need JSON.
  - The tool creates `work/fishbone/my-analysis.md` and `work/fishbone/my-analysis.svg`.
- `2. Regenerate work SVG`
  - Use this after editing `work/fishbone/my-analysis.md` or `work/fishbone/my-analysis.json`.
  - Enter the same diagram name, such as `my-analysis`.
  - The tool updates `work/fishbone/my-analysis.svg`.
- `3. Export work SVG to PNG`
  - Converts `work/fishbone/my-analysis.svg` to `work/fishbone/my-analysis.png`.
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
3. Edit the generated file in `work/fishbone/`.
4. Double-click `鱼骨图工具.cmd` again.
5. Choose `2` to regenerate the SVG.
6. Open the SVG in `work/fishbone/` to inspect the result.

The `work/` folder is for your own diagrams, grouped by diagram type such as `work/fishbone/`. The `testcases/`, `stresscases/`, and `naturalcases/` folders are also grouped by diagram type, such as `testcases/fishbone/`. `templates/` contains protected starting templates.

Fault tree usage is the same pattern: double-click `故障树工具.cmd`, create a named diagram, edit the generated file in `work/fault-tree/`, then regenerate the SVG from the same menu.

Sequential exclusion-tree usage is also the same pattern: double-click `排除树工具.cmd`, create a named diagram, edit the generated file in `work/exclusion-tree/`, then regenerate the SVG from the same menu.

Two-by-two matrix usage is the same pattern: double-click `二乘二矩阵工具.cmd`, create a named matrix, edit the generated file in `work/two-by-two-matrix/`, then regenerate the SVG or export PNG from the same menu.

Browser-builder usage is similar: double-click `图表编辑器.cmd`, choose a diagram type, edit the form, save JSON, render SVG, and export PNG from the browser page.

Two-by-two matrix usage is also available through the browser builder and command-line scripts: create with `scripts/new_two_by_two_matrix.py <name> --format md --preset action_priority`, edit in `work/two-by-two-matrix/`, then regenerate with `scripts/render_two_by_two_matrix_work.py`. Supported presets are `action_priority`, `risk_benefit`, `evidence_impact`, `value_feasibility`, `urgency_importance`, and `custom`. Use 4-20 items with X/Y scores from 1 to 5; the Decision Table shows every item.

Roadmap timeline usage is available through the browser builder and command-line scripts: create with `scripts/new_roadmap_timeline.py <name> --format md --preset swimlane_roadmap`, edit in `work/roadmap-timeline/`, then regenerate with `scripts/render_roadmap_timeline_work.py`. Supported presets are `swimlane_roadmap` and `milestone_timeline`.

FMEA table usage is available through command-line scripts: create with `scripts/new_fmea_table.py <name> --format md`, edit in `work/fmea-table/`, then regenerate with `scripts/render_fmea_table_work.py`. FMEA table currently supports core rendering and PNG export, not browser-builder editing or natural-language extraction.

Diagram names are file names under `work/fishbone/`, `work/fault-tree/`, `work/exclusion-tree/`, `work/two-by-two-matrix/`, `work/roadmap-timeline/`, or `work/fmea-table/`. Use safe names such as `my-analysis`, `startup-failure`, `startup-checks`, `priority-matrix`, `product-roadmap`, `process-fmea`, or `customer_complaints_v1`; do not enter spaces, folders, `..`, or full paths.

## Natural-Language Drafting

Codex can turn raw customer feedback, workshop notes, failure notes, or troubleshooting notes into a structured Markdown draft before rendering. This is a skill workflow, not a local `.cmd` menu feature: Codex performs the semantic extraction, then the existing local tools render the resulting Markdown.

Use fishbone for broad cause brainstorming, fault tree for logical top-event decomposition or parallel cause branches, sequential exclusion tree for one-path troubleshooting or cause-elimination checks, two-by-two matrix for option comparison or prioritization across two scoring dimensions, and roadmap timeline for phase, milestone, or initiative planning over time.

Example prompt:

```text
根据下面客户反馈生成鱼骨图草稿，文件名 customer-complaints：

最近客户投诉集中在交付周期变长、包装破损、售后响应慢、现场安装说明不清楚、
不同供应批次质量波动，以及内部测试覆盖不到真实使用场景。
```

Expected output:

- `work/fishbone/customer-complaints.md`
- `work/fishbone/customer-complaints.svg`
- Optional `work/fishbone/customer-complaints.png`

Natural-language drafts should use structures found in the source text, not default categories, generic fault branches, or generic troubleshooting steps. See `references/natural_language_extraction.md`.
For a reusable Codex prompt shape, see `references/natural_language_prompt_template.md`.
Use `references/natural_language_review_checklist.md` to review whether the generated draft stayed faithful to the source text.
See `naturalcases/fishbone/`, `naturalcases/fault-tree/`, `naturalcases/exclusion-tree/`, `naturalcases/two-by-two-matrix/`, and `naturalcases/roadmap-timeline/` for source text and expected Markdown examples.

## Badge Library

Fishbone category cards use simple circular badges. The renderer includes a small set of hand-drawn fallback icons and a curated Lucide SVG candidate library under `assets/lucide-candidates/`.

Only confirmed semantic mappings are active in the renderer. For example, `system` maps to `workflow`, `architecture` maps to `network`, `materials` maps to `boxes`, and `business` maps to `chart-no-axes-column-increasing`. Other Lucide SVGs remain in the candidate library for future product design, manufacturing, industrial application, communication, network, data-center, validation, reliability, and field-use scenarios.

Regenerate the blue-styled review board with:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_lucide_candidate_catalog.py
```

Output:

```text
work/fishbone/lucide-badge-candidates.svg
```

`scripts/verify_testcases.py` protects the key Lucide files and checks that the review catalog still renders as well-formed SVG.

## Command-Line Usage

Command-line usage is available for technical users or automation:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\new_fishbone.py my-analysis --format md
```

This creates `work/fishbone/my-analysis.md` and `work/fishbone/my-analysis.svg` from the Markdown template. Use `--format json` for the JSON template. Existing work files are not overwritten unless `--force` is passed.

After editing a work input, regenerate its SVG with:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_work.py my-analysis
```

If both `work/fishbone/my-analysis.md` and `work/fishbone/my-analysis.json` exist, pass `--format md` or `--format json`.

Export an existing work SVG to PNG:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\export_png.py my-analysis
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\export_fault_tree_png.py startup-failure
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\export_exclusion_tree_png.py startup-checks
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\export_two_by_two_matrix_png.py priority-matrix
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\export_roadmap_timeline_png.py product-roadmap
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\export_fmea_table_png.py process-fmea
```

SVG remains the primary editable output. PNG is a convenience format for quick sharing.
The PNG exporters are intended for SVGs generated by this tool, not arbitrary third-party SVG files.

Render any input file directly:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\generate_diagram.py templates\fishbone.template.json output.svg
```

Markdown input works the same way:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\generate_diagram.py templates\fishbone.template.md output.svg
```

Fault tree templates render through the same dispatcher:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\generate_diagram.py templates\fault-tree.template.json output.svg
```

For user-owned fault-tree work files, use the fault-tree entrypoints:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\new_fault_tree.py startup-failure --format md
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_fault_tree_work.py startup-failure
```

For user-owned exclusion-tree work files, use the exclusion-tree entrypoints:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\new_exclusion_tree.py startup-checks --format md
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_exclusion_tree_work.py startup-checks
```

For user-owned roadmap timeline work files, use the roadmap entrypoints:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\new_roadmap_timeline.py product-roadmap --format md --preset swimlane_roadmap
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_roadmap_timeline_work.py product-roadmap
```

Start the local HTML builder with:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\diagram_builder_server.py
```

Markdown fault tree inputs must declare `diagram_type: fault_tree` in front matter:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\generate_diagram.py templates\fault-tree.template.md output.svg
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

Fishbone Markdown:

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

Fault tree Markdown:

```markdown
---
diagram_type: fault_tree
title: Fault Tree Analysis
subtitle: Top Event - System Fails to Start
show_legend: true
---

# System Fails to Start
Gate: OR

Event Detail:
- Observed during cold start after overnight storage
- Scope: units from batch A
- Impact: startup blocked until power cycle

## Power Issue
Gate: OR
- No Power Supply
- Power Module Fault

## Control Unit Issue
Gate: AND
- Firmware Crash
- Controller Fault
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
For fault tree, see `templates/fault-tree.template.json` and `brainstorm_diagrams_fault_tree_spec.md`.
For roadmap timeline, see `templates/roadmap-timeline.template.json` and `brainstorm_diagrams_roadmap_timeline_spec.md`.
For FMEA table, see `templates/fmea-table.template.json` and `brainstorm_diagrams_fmea_table_spec.md`.
Fault tree JSON may include `event_detail` for the left-side detail panel; `top_event.description` is also accepted as a fallback. Fault tree uses `layout_mode="review_compact"` by default: first-level events are arranged across the page, while children inside each subtree connect through a vertical trunk with leftward branch lines for review readability.
Nested intermediate events may use their own `gate`, allowing one first-level event subtree to contain both AND and OR logic while each direct child group still has one gate.

## Templates

- `templates/fishbone.template.md`
- `templates/fishbone.template.json`
- `templates/fault-tree.template.md`
- `templates/fault-tree.template.json`
- `templates/exclusion-tree.template.md`
- `templates/exclusion-tree.template.json`
- `templates/two-by-two-matrix.template.md`
- `templates/two-by-two-matrix.template.json`
- `templates/roadmap-timeline.template.md`
- `templates/roadmap-timeline.template.json`
- `templates/fmea-table.template.md`
- `templates/fmea-table.template.json`

Copy a template, edit the content, then render it with `scripts/generate_diagram.py`.

## Work Files

`scripts/new_fishbone.py`, `scripts/new_fault_tree.py`, `scripts/new_exclusion_tree.py`, `scripts/new_two_by_two_matrix.py`, `scripts/new_roadmap_timeline.py`, and `scripts/new_fmea_table.py` create user-owned inputs and SVGs in their matching `work/<diagram-type>/` folders. These directories are for local authoring output, separate from maintained regression files.

## Stresscases

`stresscases/fishbone/`, `stresscases/fault-tree/`, `stresscases/exclusion-tree/`, `stresscases/two-by-two-matrix/`, and `stresscases/roadmap-timeline/` contain intentionally dense diagrams for manual visual review. They are useful after layout changes because they make spacing problems obvious, but they are not part of the maintained regression testcase set.

`scripts/verify_stresscases.py` protects this area from structural drift: it checks that the full-density SVG expands beyond the base canvas, keeps the topic block on the right, preserves the expected category and brace counts, and does not render `README.md` as an SVG.

Use `references/visual_review_checklist.md` when inspecting the generated stresscase by eye.

- `stresscases/fishbone/full-stress.md` -> `stresscases/fishbone/full-stress.svg`
- `stresscases/fault-tree/full-stress.json` -> `stresscases/fault-tree/full-stress.svg`
- `stresscases/fault-tree/nested-gates.json` -> `stresscases/fault-tree/nested-gates.svg`
- `stresscases/exclusion-tree/full-stress.json` -> `stresscases/exclusion-tree/full-stress.svg`
- `stresscases/roadmap-timeline/full-stress.json` -> `stresscases/roadmap-timeline/full-stress.svg`
- `stresscases/roadmap-timeline/milestone-dense.json` -> `stresscases/roadmap-timeline/milestone-dense.svg`

## Naturalcases

`naturalcases/` contains source text and expected structured Markdown examples for Codex-assisted natural-language drafting. It does not store generated SVG or PNG outputs.

- `naturalcases/fishbone/reliability-power-drop.source.txt` -> `naturalcases/fishbone/reliability-power-drop.expected.md`
- `naturalcases/fishbone/optical-module-stability.source.txt` -> `naturalcases/fishbone/optical-module-stability.expected.md`
- `naturalcases/fault-tree/startup-intermittent-failure.source.txt` -> `naturalcases/fault-tree/startup-intermittent-failure.expected.md`
- `naturalcases/exclusion-tree/field-link-dropout.source.txt` -> `naturalcases/exclusion-tree/field-link-dropout.expected.md`
- `naturalcases/two-by-two-matrix/priority-options.source.txt` -> `naturalcases/two-by-two-matrix/priority-options.expected.md`
- `naturalcases/roadmap-timeline/optical-module-release-roadmap.source.txt` -> `naturalcases/roadmap-timeline/optical-module-release-roadmap.expected.md`

The optical-module case covers an English product design / manufacturing / application scenario and protects confirmed Lucide badge mappings for technical categories.

## Maintained Testcases

- `testcases/fishbone/fishbone.input.example.json` -> `testcases/fishbone/fishbone.output.example.svg`
- `testcases/fishbone/fishbone.subcategory.example.md` -> `testcases/fishbone/fishbone.subcategory.output.md.svg`
- `testcases/fishbone/fishbone.subcategory.example.json` -> `testcases/fishbone/fishbone.subcategory.output.json.svg`
- `testcases/fishbone/fishbone.five-primary.example.json` -> `testcases/fishbone/fishbone.five-primary.output.svg`
- `testcases/fishbone/fishbone.five-subcategories.example.json` -> `testcases/fishbone/fishbone.five-subcategories.output.svg`
- `testcases/fishbone/fishbone.dense-collision.example.json` -> `testcases/fishbone/fishbone.dense-collision.output.svg`
- `testcases/fault-tree/fault-tree.input.example.json` -> `testcases/fault-tree/fault-tree.output.example.svg`
- `testcases/fault-tree/fault-tree.input.example.md` -> `testcases/fault-tree/fault-tree.output.md.svg`
- `testcases/fault-tree/fault-tree.mixed-gates.example.json` -> `testcases/fault-tree/fault-tree.mixed-gates.output.svg`
- `testcases/fault-tree/fault-tree.nested-gates.example.json` -> `testcases/fault-tree/fault-tree.nested-gates.output.svg`
- `testcases/fault-tree/fault-tree.multi-nested.example.json` -> `testcases/fault-tree/fault-tree.multi-nested.output.svg`
- `testcases/roadmap-timeline/roadmap.swimlane.example.json` -> `testcases/roadmap-timeline/roadmap.swimlane.output.svg`
- `testcases/roadmap-timeline/roadmap.milestone.example.json` -> `testcases/roadmap-timeline/roadmap.milestone.output.svg`
- `testcases/roadmap-timeline/roadmap.markdown.example.md` -> `testcases/roadmap-timeline/roadmap.markdown.output.svg`
