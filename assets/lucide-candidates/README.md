# Lucide Candidate Badges

This folder contains a curated subset of SVG icons downloaded from Lucide Static.

- Source: https://lucide.dev/
- Package CDN: https://unpkg.com/lucide-static@1.14.0/icons/
- License: ISC License
- Purpose: candidate badge review and future badge adaptation for `brainstorm-diagrams`

These files are not all active renderer badges. Some have confirmed mappings in the fishbone renderer, while the rest are retained as a reusable candidate library for product design, manufacturing, industrial application, communication, network, data-center, validation, reliability, and field-use scenarios.

Run this to regenerate the blue-styled review board:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_lucide_candidate_catalog.py
```

Output:

```text
work/lucide-badge-candidates.svg
```
