# Naturalcases

This folder contains natural-language source examples and expected structured Markdown drafts.

Naturalcases are examples for Codex semantic extraction quality. They are not renderer regression outputs and should not contain generated SVG or PNG files.

Use them with:

- `references/natural_language_extraction.md`
- `references/natural_language_review_checklist.md`

Current cases:

- `reliability-power-drop.source.txt` -> `reliability-power-drop.expected.md`
- `optical-module-stability.source.txt` -> `optical-module-stability.expected.md`

The second case covers an English product design / manufacturing / application scenario and protects the confirmed Lucide badge mappings for technical categories such as system architecture, optical design, thermal design, mechanical design, electrical design, materials, and manufacturing.

The expected Markdown shows one acceptable draft. Future Codex runs may phrase category or cause labels differently, but they should preserve the source meaning and stay within the fishbone input contract.
