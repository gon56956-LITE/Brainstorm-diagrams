# Layout Invariants

These constraints capture the current fishbone layout behavior. Keep them stable unless intentionally redesigning the renderer and updating `scripts/verify_testcases.py`.

## Structural Invariants

- The SVG root must be well-formed XML.
- The right-side topic block must be a rounded `<rect>` with `id="topic-block"`.
- The renderer must not introduce fish-shaped or marine decorative elements.
- Sparse diagrams keep the base `1920x1080` canvas.
- Dense diagrams may expand the SVG canvas automatically; fixed visual elements such as fonts, cards, and line widths must not be scaled down to make content fit.
- On expanded canvases, the spine, chevrons, branch anchors, and topic block must use the dynamic canvas geometry rather than fixed `1920x1080` coordinates.
- Input models stay stable:
  - Markdown subcategories use indented bullets.
  - JSON subcategories use `{ "subcategory": "...", "items": [...] }`.
  - Plain strings remain ordinary primary causes.

## Branch Length Invariants

- Category branch angle remains about 75 degrees.
- Branch length base tiers remain ordered by content load:
  - sparse ordinary causes: `180`
  - standard ordinary causes: `230`
  - any category containing a subcategory: `270`
- Dense subcategory categories may expand beyond the base tier to fit actual row heights.
- The spine remains centered in the current canvas while each category card moves closer or farther from the spine according to its tier.
- Category placement is planned before rendering; top/bottom assignment balances content load while preserving input-relative order within each half.
- Six categories remain balanced as three upper and three lower branches.
- Upper and lower categories share column x positions; categories in the same column must use the same spine anchor.
- Left-side content must stay outside the chevron-safe area.
- Right-side content must stay outside the topic-safe area, including when the topic block moves right on an expanded canvas.
- Long category card labels wrap to at most two lines inside the category card.
- Category badge icons match common English and Chinese aliases before falling back to the generic icon.

## Cause Row Invariants

- Cause rows are centered within the vertical segment between the spine and the category card edge.
- Cause row spacing is based on actual visual height, so subcategories with child causes reserve more vertical space than ordinary primary causes.
- Each category uses one start side and alternates all real entries left/right, including subcategories.
- Category column positions are based on estimated left/right footprints, not simple equal spacing.
- Ordinary primary causes render as short secondary bones:
  - anchor circle on the main branch
  - short horizontal connector
  - cause text outside the connector
- Connector lines render before the white-filled anchor circles so lines do not show through the circles.
- Primary causes alternate left and right around each main branch.

## Subcategory Invariants

- Subcategories render as anchor circle, horizontal connector, text-only rounded card, curly brace, and child bullets.
- Right-side subcategory child lists use a `{` brace.
- Left-side subcategory child lists use a `}` brace.
- Braces are hand-drawn SVG paths, not external assets or dependencies.
- Child cause rows remain compact at about 19-20px spacing.
- Braces are vertically centered on the child bullet list and aligned with the subcategory card center.

## Verification

Run this before finishing renderer or example changes:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\verify_testcases.py
```
