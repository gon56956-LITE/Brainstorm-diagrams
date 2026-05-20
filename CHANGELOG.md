# Changelog

## 0.5.0 - 2026-05-19

### Roadmap Timeline

- Added `roadmap_timeline` SVG rendering with `swimlane_roadmap` and `milestone_timeline` presets.
- Added JSON and Markdown templates, work creation/render/export scripts, double-click launchers, maintained testcases, and stresscases.
- Added verification coverage for roadmap templates, entrypoints, PNG export, stable SVG groups/classes, and dense canvas expansion.

## 0.4.0 - 2026-05-18

### Two-By-Two Matrix

- Added `two_by_two_matrix` SVG rendering with action-priority, risk-benefit, evidence-impact, value-feasibility, urgency-importance, and custom presets.
- Added JSON and Markdown templates, work creation/render/export scripts, maintained testcases, stresscases, and natural-language examples.
- Added browser-builder support and documentation for two-axis prioritization and comparison matrices.
- Kept language output single-language by default with `language: auto | en | zh`; diagrams do not auto-render English/Chinese pairs.

## 0.1.4 - 2026-05-13

### Multi-Diagram Structure

- Moved maintained fishbone regression files under `testcases/fishbone/`.
- Moved optional fishbone stress review files under `stresscases/fishbone/`.
- Moved fishbone natural-language examples under `naturalcases/fishbone/`.
- Moved local fishbone work outputs under `work/fishbone/`.
- Updated fishbone work, export, stresscase, naturalcase, and verification scripts to use diagram-type scoped directories.
- Updated README, SKILL, and maintenance references for the diagram-type scoped folder structure.

## 0.1.3 - 2026-05-12

### Workflow And User Tools

- Renamed maintained regression examples to `testcases/`.
- Added user-copyable Markdown and JSON templates under `templates/`.
- Added `scripts/new_fishbone.py` to create user-owned work files from templates.
- Added `scripts/render_work.py` to regenerate SVGs from user-owned work inputs.
- Added `scripts/export_png.py` to export generated work SVGs to PNG for quick sharing.
- Added double-click `.cmd` launchers for non-technical users.
- Added a double-click menu option for PNG export.
- Added safe work-name validation and menu notes to keep user diagrams inside `work/`.
- Added a double-click menu option to regenerate stresscase SVGs.

### Layout And Rendering

- Added two-line wrapping for long category card labels and Chinese category icon aliases.
- Added automatic SVG canvas expansion for dense fishbone diagrams while preserving fixed font, card, and line sizes.
- Improved dense-content layout by spacing rows by visual height and expanding crowded subcategory branches.
- Added content-aware top/bottom category assignment, footprint-aware x placement, and dense collision regression coverage.
- Replaced straight subcategory child brackets with compact hand-drawn SVG curly braces.
- Tightened subcategory child row spacing while keeping child bullets outside the subcategory cards.
- Added content-density branch lengths so sparse categories render with shorter main branches and subcategory categories keep at least medium branches.

### Natural Language

- Added Codex skill workflow documentation for natural-language fishbone drafting into structured Markdown.
- Added `references/natural_language_prompt_template.md` as a reusable prompt workflow for natural-language fishbone drafts.
- Added `references/natural_language_review_checklist.md` for semantic review of natural-language fishbone drafts.
- Added `naturalcases/` with a source-text and expected-Markdown example for natural-language extraction.
- Added an English optical-module naturalcase to protect product design / manufacturing extraction and confirmed Lucide badge mappings.

### Badges

- Added a Lucide SVG badge candidate library and blue-styled review catalog for product design, manufacturing, industrial application, communication, network, data-center, validation, reliability, and field-use scenarios.
- Expanded Lucide badge candidates for cloud, network, data-center compute, storage, device, and service-integration scenarios.
- Added confirmed Lucide badge mappings for system, architecture, optical, thermal, mechanical, electrical, materials, manufacturing, reliability, field-use, test, verification, cost, and business categories.
- Improved PNG export support for Lucide-style nested SVG groups and inherited stroke styling.

### Validation And Documentation

- Renamed verification to `scripts/verify_testcases.py` and added template structure checks.
- Added `scripts/verify_naturalcases.py` to protect naturalcase structure and renderability.
- Added optional `stresscases/` manual visual review area with a full-density fishbone stresscase and renderer script.
- Added `scripts/verify_stresscases.py` to protect optional stresscase structure without making it a formal regression testcase.
- Added `references/visual_review_checklist.md` for manual review of dense fishbone stresscases.
- Added `references/maintenance_checklist.md` for renderer, badge, natural-language, testcase, and release verification.
- Updated regenerated fishbone SVG testcases.
- Added formal stress-test testcases for five primary causes and five subcategories with three child causes each.
- Added `scripts/verify_testcases.py` to regenerate testcases and check key SVG layout invariants.
- Documented the current skill workflow, maintained testcases, templates, and layout invariants.

## 0.1.2 - 2026-05-12

- Added input diagnostics for defaults, truncation, ignored nested markdown, and compatibility fields.
- Added mixed cause and subcategory entries under each main fishbone category.
- Added subcategory cards without badges and up to three child causes per subcategory.
- Added mixed Markdown and JSON subcategory examples.
- Updated subcategory layout to use horizontal connectors, alternating left/right entry placement, and outside bracketed child bullets.
- Removed decorative trailing lines after real primary cause text.

## 0.1.1 - 2026-05-12

- Refined the fishbone SVG layout toward the image2 sample style.
- Added stronger category cards with circular icon badges.
- Added faint background dot and line decorations.
- Reworked the right-side topic card hierarchy.
- Removed the default upper-left title and tightened text sizing to reduce overflow.
- Moved branch anchors and bullet rows closer to the reference layout.
- Removed automatic bilingual label rendering and default slogan text in the topic card.
- Recalculated primary branch and bullet positioning around a 75-degree branch angle.
- Balanced upper and lower branch lengths and moved bullet markers closer to the branch line.
- Added distinct built-in icons for functions, performance, reliability, and cost categories.

## 0.1.0 - 2026-05-12

- Added initial `brainstorm-diagrams` skill structure.
- Added deterministic fishbone SVG generation.
- Added JSON and structured Markdown input support.
- Added lightweight roadmap, input contract, redraw workflow, visual style contract, and implementation checklist.
