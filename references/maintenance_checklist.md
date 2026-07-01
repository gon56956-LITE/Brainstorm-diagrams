# Maintenance Checklist

Use this checklist before finishing changes to `brainstorm-diagrams`.

## Renderer Or Layout Changes

- Run `scripts/verify_testcases.py`.
- Run `scripts/verify_stresscases.py`.
- Regenerate stresscases with `scripts/render_stresscases.py` when spacing, canvas, branch placement, or dense layout behavior changes.
- Visually inspect `stresscases/fishbone/full-stress.svg` with `references/visual_review_checklist.md` for overlap, clipped content, spine spacing, topic-block position, and readable category groups.
- Confirm `work/fishbone/` has no leftover `*tmp*` files.

## Badge Or Icon Changes

- Keep reusable Lucide SVGs in `assets/lucide-candidates/`.
- Add renderer mappings only for confirmed semantic matches.
- Regenerate the review board with `scripts/render_lucide_candidate_catalog.py`.
- Run `scripts/verify_testcases.py` to protect required mapped icons and catalog renderability.
- If new badge SVG structures affect PNG output, run `scripts/export_png.py` on a work diagram that uses those badges.

## Natural-Language Workflow Changes

- Update `references/natural_language_extraction.md` for rules.
- Update `references/natural_language_prompt_template.md` for reusable execution prompts.
- Update `references/natural_language_review_checklist.md` for review criteria.
- Add or update `naturalcases/fishbone/*.source.txt` and `naturalcases/fishbone/*.expected.md` when changing expected extraction behavior.
- Add or update `naturalcases/fault-tree/*.source.txt` and `naturalcases/fault-tree/*.expected.md` when changing fault-tree extraction behavior.
- Add or update `naturalcases/exclusion-tree/*.source.txt` and `naturalcases/exclusion-tree/*.expected.md` when changing exclusion-tree extraction behavior.
- Run `scripts/verify_naturalcases.py`.

## Templates, Testcases, And User Tools

- Keep `templates/` for copyable user starting points only.
- Keep `testcases/<diagram-type>/` for maintained regression inputs and outputs only.
- Keep `naturalcases/<diagram-type>/` free of generated SVG or PNG files.
- Keep `stresscases/<diagram-type>/` for optional visual stress review.
- Run `cmd /c fishbone_tool.cmd verify` after changes to double-click menu behavior or verification routing.

## Browser Builder Changes

- Manual acceptance on 2026-05-15 covered `diagram_builder.cmd`: New, Load File, Save JSON, Save As, Render SVG, Export PNG, Recent, Help, and Esc-close behavior; no issues were found.
- Keep the builder as a local editor for the existing JSON contracts, not a separate schema.
- Keep top-level actions compact enough to fit in one row: New, Load File, Save JSON, Save As, Render SVG, Export PNG, Work Folder, Help.
- Keep `scripts/verify_testcases.py` covering builder template loading, loaded JSON/Markdown parsing, work JSON save, SVG render, PNG export, PNG/SVG dimension match, unsafe name rejection, preview zoom UI, Recent, Help, Save As, and warning-not-blocking validation.
- After builder UI changes, run `scripts/verify_testcases.py` and manually smoke-test `diagram_builder.cmd` when button flow, file loading, browser save dialogs, or modal behavior changes.

## Full Verification Set

Run this set before closing a substantial change:

```powershell
python scripts\verify_testcases.py
python scripts\verify_stresscases.py
python scripts\verify_naturalcases.py
cmd /c fishbone_tool.cmd verify
```
