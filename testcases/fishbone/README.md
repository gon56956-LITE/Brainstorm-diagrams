# Fishbone Testcases

This folder contains maintained fishbone testcase input/output pairs used for renderer regression checks. Regenerate and verify them with:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\verify_testcases.py
```

## Basic Testcases

- `fishbone.input.example.json` -> `fishbone.output.example.svg`
  - Baseline JSON testcase with six categories and ordinary primary causes.
- `fishbone.input.example.md` -> `fishbone.output.example.svg`
  - Baseline structured Markdown input. It writes to the same baseline output path when rendered directly.

## Subcategory Testcases

- `fishbone.subcategory.example.md` -> `fishbone.subcategory.output.md.svg`
  - Structured Markdown subcategory input using indented bullets.
- `fishbone.subcategory.example.json` -> `fishbone.subcategory.output.json.svg`
  - Equivalent JSON subcategory input using `{ "subcategory": "...", "items": [...] }`.

## Stress Tests

- `fishbone.five-primary.example.json` -> `fishbone.five-primary.output.svg`
  - Densest ordinary primary-cause case: one category with five primary causes.
- `fishbone.five-subcategories.example.json` -> `fishbone.five-subcategories.output.svg`
  - Densest subcategory case: one category with five subcategories, each with three child causes.
- `fishbone.dense-collision.example.json` -> `fishbone.dense-collision.output.svg`
  - Mixed dense upper-category collision case with neighboring subcategories.
