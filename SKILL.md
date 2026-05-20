---
name: brainstorm-diagrams
description: Generate clean, PPT-ready structured brainstorming and analysis diagrams for product design, process design, failure analysis, root-cause analysis, cause-and-effect mapping, solution exploration, fishbone / Ishikawa diagrams, fault tree analysis, exclusion tree troubleshooting, two-by-two prioritization matrices, and roadmap timelines. Supports business-simple fishbone, fault_tree, exclusion_tree, two_by_two_matrix, and roadmap_timeline SVG diagrams from JSON or structured Markdown.
---

# Brainstorm Diagrams

Use this skill to create structured thinking diagrams for brainstorming, root-cause analysis, product design, process design, and solution exploration.

Current version supports `diagram_type="fishbone"`, `diagram_type="fault_tree"`, `diagram_type="exclusion_tree"`, `diagram_type="two_by_two_matrix"`, and `diagram_type="roadmap_timeline"` as editable SVG output. Work SVGs can also be exported to PNG for sharing, and Codex-assisted natural-language drafting currently supports fishbone, fault tree, exclusion tree, and two-by-two matrix. For non-technical fishbone users, prefer the double-click launcher after the draft structure exists:

```text
鱼骨图工具.cmd
```

English fallback:

```text
fishbone_tool.cmd
```

For non-technical fault-tree users, use the dedicated launcher:

```text
故障树工具.cmd
```

English fallback:

```text
fault_tree_tool.cmd
```

For non-technical exclusion-tree users, use the dedicated launcher:

```text
排除树工具.cmd
```

English fallback:

```text
exclusion_tree_tool.cmd
```

For non-technical two-by-two matrix users, use the dedicated launcher:

```text
二乘二矩阵工具.cmd
```

English fallback:

```text
two_by_two_matrix_tool.cmd
```

For non-technical roadmap timeline users, use the dedicated launcher:

```text
路线图时间线工具.cmd
```

English fallback:

```text
roadmap_timeline_tool.cmd
```

For a browser-based local editor that supports fishbone, fault tree, exclusion tree, two-by-two matrix, and roadmap timeline, use:

```text
图表编辑器.cmd
```

English fallback:

```text
diagram_builder.cmd
```

Command-line usage is also available:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\new_fishbone.py my-analysis --format md
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\new_fault_tree.py startup-failure --format md
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\new_exclusion_tree.py startup-checks --format md
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\new_two_by_two_matrix.py priority-matrix --format md --preset action_priority
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\new_roadmap_timeline.py product-roadmap --format md --preset swimlane_roadmap
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\diagram_builder_server.py
```

This creates a user-owned input and initial SVG under `work/fishbone/`, `work/fault-tree/`, `work/exclusion-tree/`, `work/two-by-two-matrix/`, or `work/roadmap-timeline/`. To render an existing input directly, use `scripts/generate_diagram.py`.
Work names must be safe file stems: lowercase letters, numbers, hyphen, and underscore only, such as `my-analysis` or `customer_complaints_v1`.

## Supported Diagram Types

- `fishbone`: divergent cause brainstorming and category-based problem decomposition.
- `fault_tree`: logical failure decomposition with a top event, event detail panel, AND/OR gates, intermediate events, and basic event leaves.
- `exclusion_tree`: sequential exclusion tree troubleshooting and root-cause elimination with one main checkpoint path, Yes/Pass continuation, No/Fail conclusion cards, and a final no-issue-found outcome.
- `two_by_two_matrix`: two-axis option comparison and prioritization using quadrant item summaries and a complete side decision table; supports 4-20 scored items with 1-5 X/Y scores, and default language is auto-detected, not bilingual.
- `roadmap_timeline`: roadmap or milestone timeline planning with `swimlane_roadmap` and `milestone_timeline` presets, periods, phases, lane initiatives, milestones, decision points, and optional summary/table panels.

After editing a `work/fishbone/` input, regenerate it with:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_work.py my-analysis
```

After editing a `work/fault-tree/` input, regenerate it with:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_fault_tree_work.py startup-failure
```

After editing a `work/exclusion-tree/` input, regenerate it with:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_exclusion_tree_work.py startup-checks
```

After editing a `work/two-by-two-matrix/` input, regenerate it with:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_two_by_two_matrix_work.py priority-matrix
```

After editing a `work/roadmap-timeline/` input, regenerate it with:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_roadmap_timeline_work.py product-roadmap
```

Export a generated work SVG to PNG with:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\export_png.py my-analysis
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\export_fault_tree_png.py startup-failure
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\export_exclusion_tree_png.py startup-checks
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\export_two_by_two_matrix_png.py priority-matrix
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\export_roadmap_timeline_png.py product-roadmap
```

PNG export is intended for SVGs generated by this tool, not arbitrary third-party SVG files.

Fishbone category badges use confirmed semantic mappings from a curated Lucide SVG candidate library in `assets/lucide-candidates/`. The renderer should only map categories to Lucide badges when the category meaning is confirmed; keep extra Lucide files as future candidates, not automatic mappings.

Regenerate the badge review board with:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_lucide_candidate_catalog.py
```

Run the maintained testcase, template, and layout checks after renderer changes:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\verify_testcases.py
```

For manual visual review after dense-layout changes, regenerate stresscases:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_stresscases.py
```

To protect the optional stresscase structure:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\verify_stresscases.py
```

To protect natural-language extraction examples:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\verify_naturalcases.py
```

## Inputs

Prefer JSON for automation and structured Markdown for user-authored briefs.

- JSON: use `diagram_type` to select `fishbone`, `fault_tree`, `exclusion_tree`, `two_by_two_matrix`, or `roadmap_timeline`; fishbone follows `references/input_contract.md`, fault tree follows `brainstorm_diagrams_fault_tree_spec.md`, exclusion tree follows `brainstorm_diagrams_exclusion_tree_spec.md`, two-by-two matrix follows `brainstorm_diagrams_two_by_two_matrix_spec.md`, and roadmap timeline follows `brainstorm_diagrams_roadmap_timeline_spec.md`.
- Markdown fishbone: use `#` for the topic, `##` for categories, and bullet lists for cause items.
- Markdown fault tree: include `diagram_type: fault_tree` front matter, use `#` for the top event, optional `Event Detail:` bullets for the left-side detail panel, `Gate: OR` or `Gate: AND` for logic gates, `##` for intermediate events, and bullets for basic event leaves.
- Markdown exclusion tree: include `diagram_type: exclusion_tree` front matter, use `#` for the target problem, `##` for checkpoints, and recognized key-value lines such as `Icon:`, `Pass:`, `Fail:`, `Fail Conclusion:`, `Fail Detail:`, and `Final Pass Conclusion:`.
- Markdown two-by-two matrix: include `diagram_type: two_by_two_matrix` front matter, a `preset`, optional `language`, a `#` title, and an items table with `Item`, `X`, and `Y` columns. Use 4-20 items; X/Y scores must be 1-5. Use top-level `notes:` only when the user wants a visible notes area; do not add item-level notes or a subtitle unless explicitly requested.
- Markdown roadmap timeline: include `diagram_type: roadmap_timeline` front matter, a `preset` (`swimlane_roadmap` or `milestone_timeline`), optional `language`, a `#` title, and tables for `Periods`, plus either `Lanes`/`Initiatives` or `Milestones`.
- Markdown subcategories: a primary bullet with indented bullets becomes a subcategory with child causes.
- Starting templates live in `templates/`; copy them before authoring a new diagram.
- Browser editor: `scripts/diagram_builder_server.py` edits the existing JSON contracts through a local HTML UI and saves into the appropriate `work/<diagram-type>/` folder; it is not a new input schema.
- Browser editor controls should expose only fields that non-technical users need to decide and that affect rendered content. Do not expose hidden metadata, unused title/subtitle fields, renderer-derived icons, or fixed semantic labels such as Yes/No.
- Natural-language source text: Codex must first extract a structured Markdown draft using `references/natural_language_extraction.md` and `references/natural_language_prompt_template.md`; do not pass raw `.txt` directly to `scripts/generate_diagram.py` for semantic extraction.

## Workflow

1. For structured Markdown/JSON, normalize the user input into the selected diagram data model.
2. For natural-language source text, first choose the diagram type, then extract the appropriate structured Markdown using `references/natural_language_extraction.md`; use `references/natural_language_prompt_template.md` as the execution template when drafting from raw text.
3. For a new blank/template diagram, run `scripts/new_fishbone.py <name> --format md`, `scripts/new_fault_tree.py <name> --format md`, `scripts/new_exclusion_tree.py <name> --format md`, `scripts/new_two_by_two_matrix.py <name> --format md --preset action_priority`, or `scripts/new_roadmap_timeline.py <name> --format md --preset swimlane_roadmap`; use `--format json` when needed.
4. For a Codex-assisted natural-language draft, write the extracted Markdown to `work/<diagram-type>/<name>.md`; use safe file stems only.
5. Render a fishbone work input with `scripts/render_work.py <name>`, a fault-tree work input with `scripts/render_fault_tree_work.py <name>`, an exclusion-tree work input with `scripts/render_exclusion_tree_work.py <name>`, a two-by-two work input with `scripts/render_two_by_two_matrix_work.py <name>`, or a roadmap work input with `scripts/render_roadmap_timeline_work.py <name>`; if both Markdown and JSON inputs exist for the same name, pass `--format md` or `--format json`.
6. Optionally run the matching PNG export script when the user needs a PNG for quick sharing.
7. For non-technical editing, run `diagram_builder.cmd` or `scripts/diagram_builder_server.py`; the browser UI should save JSON, render SVG, and export PNG using the same work folders and renderers.
8. Read the printed `Diagnostics:` block for defaults, truncation, ignored nesting, and compatibility notices.
9. Check the generated SVG for readability and adherence to `references/visual_style_contract.md`.
10. For natural-language drafts, review semantic quality with `references/natural_language_review_checklist.md`; use `naturalcases/fishbone/`, `naturalcases/fault-tree/`, and `naturalcases/exclusion-tree/` as examples, not as generated output storage.
11. For naturalcase edits, run `scripts/verify_naturalcases.py`.
12. For renderer, badge, testcase, template, work-entrypoint, browser-builder, extraction-doc, or export edits, run `scripts/verify_testcases.py` before finishing.
13. For dense layout changes, also run `scripts/render_stresscases.py`, run `scripts/verify_stresscases.py`, and inspect the relevant `stresscases/<diagram-type>/full-stress.svg` by eye using `references/visual_review_checklist.md`.

## Universal Layout Quality Rules

- Every connector must visibly start from a source element boundary, anchor, chip, or branch point and visibly end at a target boundary, anchor, chip, or arrowhead; do not allow connector paths to appear broken or to begin from empty space.
- Derive branch target positions from the source element whenever the relationship is local. Avoid forcing related cards into a single global column unless that column itself communicates the hierarchy better.
- When several related cards would otherwise share one column, prefer staggered or stepped placement that preserves each card's association with its source and reduces long parallel connector runs.
- Cards may use a stable width for visual rhythm, but their height must be calculated from wrapped text, detail rows, icons, and padding. Expand cards and canvas height instead of shrinking fonts, clipping text, or hiding core business content.
- Text wrapping must use the actual text column inside the card, accounting for icons, padding, and CJK double-width characters; no text line may extend beyond the card boundary.
- Terminal or outcome cards should be placed under their natural incoming branch anchor whenever space allows. Do not push a terminal card to a decorative side position if that forces unnecessary elbow connectors.
- Auxiliary panels such as legends and usage notes should be placed as high as the available non-colliding region allows; do not let unrelated content in another column create wasted canvas height.
- Decorative background marks must stay in edge whitespace that cannot be confused with content or connectors. If a renderer cannot guarantee that, omit the decoration.
- Render user-authored labels in the language the user supplied. Do not automatically expand single-language input into bilingual output; use bilingual rendering only when explicitly requested or when the user provided both languages for that purpose.
- Prefer renderer-derived visual aids, such as badges/icons, over asking non-technical users to choose decorative or inferable presentation details.
- Do not use ellipses for primary business meaning such as event labels, root causes, check questions, or final conclusions. Truncation is acceptable only for minor decorative or nonessential labels.
- Renderer verification should protect against broken connectors, incoherent overlap, text outside cards, cards outside the canvas, and layout regressions in dense cases.

## Fishbone Layout Rules

- Keep the topic block as a rounded SVG `<rect>` with `id="topic-block"`.
- Render ordinary primary causes as short secondary bones: anchor circle on the main branch, short horizontal connector, then text.
- Draw connector lines before anchor circles so the white-filled circles mask lines inside the circle.
- Render subcategories as anchor circle, horizontal connector, text-only card, outside curly brace, and child bullets.
- Right-side subcategory children use a `{` brace; left-side children use a `}` brace.
- Keep branch length density tiers ordered as sparse primary causes < standard primary causes < subcategory branches.
- Preserve the current compact branch length base tiers unless intentionally changing layout tests: `180 / 230 / 270`.
- Allow dense subcategory branches to expand beyond the base tier when actual row heights require it.
- Keep sparse diagrams at the base `1920x1080` canvas, but automatically expand the SVG canvas for dense content instead of shrinking fonts, cards, or line widths.
- When the canvas expands, keep the topic block on the right side of the dynamic canvas and keep the spine, chevrons, and category anchors aligned to the dynamic spine center.
- Keep cause rows centered within the vertical segment between the spine and the category card edge.
- Space cause rows by actual visual height so subcategories with child bullets do not overlap neighboring rows.
- Plan top/bottom category placement by content load, while preserving input-relative order within each half.
- Keep every category internally left/right alternating, including subcategory entries.
- Place categories horizontally by estimated left/right footprint instead of simple equal spacing.
- Use `testcases/fishbone/fishbone.five-primary.*` and `testcases/fishbone/fishbone.five-subcategories.*` as stress tests for the densest supported category content.
- Use `stresscases/fishbone/full-stress.*` as an optional manual visual stresscase; it is deliberately denser than normal regression testcases.
- Use `naturalcases/fishbone/*.source.txt`, `naturalcases/fishbone/*.expected.md`, `naturalcases/fault-tree/*.source.txt`, `naturalcases/fault-tree/*.expected.md`, `naturalcases/exclusion-tree/*.source.txt`, and `naturalcases/exclusion-tree/*.expected.md` as semantic extraction examples; do not place generated SVG/PNG files there.
- Keep `templates/fishbone.template.*`, `templates/fault-tree.template.*`, `templates/exclusion-tree.template.*`, `templates/two-by-two-matrix*.template.*`, and `templates/roadmap-timeline*.template.*` parseable and structurally complete; `scripts/verify_testcases.py` protects them from accidental deletion or malformed edits.
- Keep `assets/lucide-candidates/` as the reusable Lucide badge library. `scripts/verify_testcases.py` protects required mapped icons and verifies the candidate catalog can still render.
- Keep user-authored fishbone files in `work/fishbone/`; do not mix them into `testcases/fishbone/`, `templates/`, `stresscases/fishbone/`, or `naturalcases/fishbone/`.
- Keep user-authored fault-tree files in `work/fault-tree/`; do not mix them into `testcases/fault-tree/`, `templates/`, or `stresscases/fault-tree/`.
- Keep user-authored exclusion-tree files in `work/exclusion-tree/`; do not mix them into `testcases/exclusion-tree/`, `templates/`, or `stresscases/exclusion-tree/`.
- Keep user-authored roadmap timeline files in `work/roadmap-timeline/`; do not mix them into `testcases/roadmap-timeline/`, `templates/`, or `stresscases/roadmap-timeline/`.

## Fault Tree Layout Rules

- Keep the top event as a navy rounded SVG `<rect>` with `id="top-event-block"`.
- When `event_detail` exists, render it as a left-side rounded detail panel with `id="fault-event-detail-panel"` instead of using the old title-only area.
- Use top-down orthogonal connectors from parent event to gate, then to child events.
- Render AND and OR gates with visually distinct symbols and stable classes: `fault-gate-and` and `fault-gate-or`.
- Use nested intermediate events when one first-level event subtree needs both AND and OR logic; do not mix AND/OR among direct children of one gate.
- Prefer 3-5 first-level intermediate events for review clarity, but allow up to 8 first-level events when the source has distinct major branches.
- Render intermediate events as pale-blue rounded rectangles and basic events as white rounded rectangles without internal marker icons.
- Size basic event cards from their label content while preserving readable minimum dimensions.
- Use `layout_mode="review_compact"` by default: first-level events are horizontal, and basic events stack vertically under their parent to avoid extreme wide canvases.
- In `review_compact`, draw each first-level subtree with a vertical trunk and leftward branch lines so direct children and nested intermediate events read as separate hierarchy levels.
- Allow dense nested fault-tree content to expand the SVG height instead of clipping event cards or shrinking text.
- Keep the legend enabled by default for templates and testcases.
- Keep generated fault-tree regression files in `testcases/fault-tree/`.
- Use `stresscases/fault-tree/full-stress.*` after fault-tree layout changes to check wide-canvas behavior, long labels, event detail, legend, and mixed gates.
- Use `testcases/fault-tree/fault-tree.nested-gates.*` and `stresscases/fault-tree/nested-gates.*` to protect nested AND/OR subtrees.

## Sequential Exclusion Tree Layout Rules

- Keep the target problem as a navy rounded SVG `<rect>` with `id="exclusion-top-event-block"`.
- When `event_detail` exists, render it as a left-side rounded detail panel with `id="exclusion-event-detail-panel"` instead of using a title-only area.
- Use top-to-bottom elimination logic: each checkpoint asks a testable Yes/No question.
- Render Yes/Pass and No/Fail chips at the same height for each checkpoint.
- Render No/Fail as red chips that branch right, drop downward outside the cause-card column, and then point into the corresponding root-cause or likely-cause conclusion card.
- Keep stable SVG markers for validation: `exclusion-checkpoint`, `exclusion-pass-chip`, `exclusion-fail-chip`, `exclusion-fail-conclusion`, `exclusion-final-pass`, `exclusion-tree-legend`, and `exclusion-how-to-use`.
- Keep the default diagram PPT-friendly at 1920px wide, and expand height for dense six-check cases instead of shrinking fonts or clipping cards.
- Use only simple inline SVG icons listed in `templates/exclusion-tree.template.*`; do not depend on external icon fonts or network assets.
- Use `testcases/exclusion-tree/*` and `stresscases/exclusion-tree/full-stress.*` after exclusion-tree layout changes.

## Roadmap Timeline Layout Rules

- Keep the root SVG group as `id="roadmap-timeline"`.
- Use `preset="swimlane_roadmap"` for lane-based roadmap planning and `preset="milestone_timeline"` for event/milestone sequences.
- Render single-language labels by default. Only use bilingual label pairs when `language: bilingual` or paired source fields explicitly request it.
- Keep base canvas at least 1920x1080, and expand width or height for dense timelines rather than shrinking fonts or clipping labels.
- In swimlane roadmaps, reserve the extra milestone/decision marker band only for lanes that actually contain markers; marker-free lanes should stay compact.
- Preserve stable SVG identifiers and classes for validation: `roadmap-grid`, `roadmap-lane`, `roadmap-initiative`, `roadmap-milestone`, `roadmap-table`, `roadmap-summary-panel`, and `roadmap-legend`.
- Use `testcases/roadmap-timeline/*` and `stresscases/roadmap-timeline/*` after roadmap renderer changes.

## Current Limits

- Implemented diagram types: `fishbone`, `fault_tree`, `exclusion_tree`, `two_by_two_matrix`, `roadmap_timeline`.
- Each main category renders up to five primary entries; each subcategory renders up to three child causes.
- Fault tree MVP supports a top event, event detail panel, AND/OR gates, up to 8 first-level intermediate events, second-level intermediate events, and basic event leaves. It does not calculate probabilities, simplify Boolean logic, or support dynamic fault tree semantics.
- Exclusion tree MVP supports a target problem, 3-6 sequential checkpoints on one main path, Yes/Pass continuation, No/Fail conclusion cards, a final pass conclusion, legend, and how-to-use panel. It does not support parallel troubleshooting lanes, complex nested decision trees, or multi-condition branching.
- Two-by-two matrix supports 4-20 scored items with X/Y scores from 1 to 5; the matrix body may summarize crowded quadrants, while the side decision table renders every item.
- Roadmap timeline MVP supports swimlane roadmap and milestone timeline presets with periods, optional phases, initiatives, milestones, decision points, summary/table panels, browser-builder UI support, and PNG export.
- Natural-language extraction is a Codex skill workflow, not an offline local script or `.cmd` menu feature.
- Redrawing existing fishbone files or whiteboard photos is planned but not implemented.
