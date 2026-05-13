# Visual Style Contract

Use a clean corporate vector style suitable for PowerPoint.

## Required

- Left-to-right fishbone direction.
- Main spine as a horizontal line.
- Right-side topic block as a rounded rectangle.
- White or very light gray background.
- Navy, blue, light blue, gray, and white palette.
- Horizontal readable text.
- Simple lines, circles, rounded rectangles, and chevrons.

## Image2-Style Layout

- Use a long horizontal spine with a small line arrow before the topic block.
- Place the default six categories as three upper cards and three lower cards.
- Use deep-blue upper cards, pale-blue lower cards, and a white circular icon badge in each card.
- Category card labels may wrap to two compact lines when the label is too long for one line.
- Category icon badges should match common English and Chinese category names, including human/operator, machine/equipment, material/supply, method/process, environment/logistics, and test/measurement categories.
- Keep branch connectors steep and clean, around 75 degrees from the horizontal spine, with circular nodes on the spine.
- Render primary causes as short secondary bones: a hollow anchor circle on the main branch, a short horizontal connector, and cause text.
- Render primary entries on alternating sides of each main branch to reduce vertical crowding.
- Do not draw decorative trailing lines after real cause text; use placeholder lines only for empty rows.
- Put subcategory anchor circles on the main branch, connect them horizontally to text-only subcategory cards, and show child causes with compact curly braces and bullets outside the card.
- Use a `{` curly brace for right-side subcategory children and a `}` curly brace for left-side children. Draw braces as inline SVG paths with no external dependency.
- Keep child cause rows compact, about 19-20px apart, with the brace vertically centered on the child bullet list.
- Let each category branch length respond to content density while preserving the 75-degree connector angle: sparse categories can use shorter branches, standard categories keep the default branch length, and categories with subcategories stay at least medium length.
- Keep primary cause and subcategory rows centered within the vertical segment between the main spine and the category card edge.
- Keep the topic block as a separate right-side information card with a small target icon and topic text; do not add slogan text by default.
- Keep sparse diagrams on the base `1920x1080` canvas. For dense diagrams, expand the SVG canvas and move the topic block to the right-side safe area instead of shrinking typography or card sizes.
- Keep background dots and circuit-like line decorations faint and non-dominant.

## Forbidden

- fish head
- fish tail
- fish eye
- fish mouth
- fish scales
- fish fins
- skeleton fish
- ocean waves
- bubbles
- marine decoration
- triangle problem block
- organic blob topic block
- glossy 3D effects

## Typography

Use common fonts:

```css
Arial, Helvetica, "Microsoft YaHei", "Noto Sans CJK SC", sans-serif
```

Keep category labels bold and bullet text concise.
