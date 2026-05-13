# Stresscases

This folder contains optional fishbone stresscases for manual visual review.

Stresscases are not maintained regression outputs like `testcases/`. They are intentionally dense examples used when changing layout logic and checking the generated SVG by eye.

To regenerate all stresscase SVG files:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\render_stresscases.py
```

The double-click launcher also provides:

```text
4. Render stresscases
5. Verify stresscases
```

To verify stresscase structure without treating it as a regression testcase:

```powershell
& "C:\Users\gon56956\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" scripts\verify_stresscases.py
```

For the manual eye check, use `references/visual_review_checklist.md`.

Current stresscases:

- `full-stress.md` -> `full-stress.svg`
