# Visual Review Checklist

Use this checklist after changing fishbone layout logic, especially row spacing, branch length, footprint planning, or canvas expansion.

## Stresscase Review

1. Regenerate the stresscase SVG:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_stresscases.py
```

2. Verify the stresscase structure:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\verify_stresscases.py
```

3. Open `stresscases/fishbone/full-stress.svg` and inspect it by eye.

## What To Check

- Spine clearance: child bullets and child text near the spine should not touch or cross the horizontal spine.
- Category-card clearance: child bullets and child text near category cards should not touch or crowd the large category cards.
- Alternation: each category should still alternate entries left and right instead of pushing all dense subcategories to one side.
- Horizontal spacing: adjacent category groups should have readable gaps between child lists, braces, cards, and labels.
- Topic safety: the topic block should stay on the right with visible whitespace between it and the nearest category content.
- Canvas behavior: dense diagrams may grow wider or taller, but fonts, card sizes, icon sizes, and line widths should not be scaled down.
- Readability: at the full `8 category x 5 subcategory x 3 child cause` stress level, labels should still be individually readable.

## Passing Standard

The stresscase does not need to look compact. It should look deliberately roomy, stable, and readable. Prefer a larger SVG canvas over cramped text or collisions.
