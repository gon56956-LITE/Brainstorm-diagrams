# Redraw Workflow

This is a Phase 2 design note. Redraw is not implemented in version 1.

## Goal

Convert an existing fishbone diagram or whiteboard photo into the shared fishbone model, then redraw it using the deterministic SVG renderer.

## Sources

- SVG: extract visible text and simple structure when possible.
- PPTX: extract shapes and text when possible.
- PDF: extract text or render pages before inspection.
- PNG/JPG/photo: use image understanding or OCR.

## Process

1. Identify the topic or problem statement.
2. Identify category labels.
3. Identify cause items under each category.
4. Mark uncertain or illegible content.
5. Ask the user to confirm uncertain extraction results.
6. Normalize to the fishbone input contract.
7. Render as `business_simple` SVG.

## Default Policy

Do not copy the old visual style directly. Redraw into the standard clean corporate style unless the user explicitly requests a different supported style.
