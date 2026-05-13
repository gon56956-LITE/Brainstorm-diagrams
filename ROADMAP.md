# Roadmap

## Phase 1: Fishbone SVG Core

- Generate business-simple fishbone diagrams as SVG.
- Support JSON and structured Markdown input.
- Keep rendering deterministic and dependency-free.

## Phase 2: Redraw Existing Fishbone

- Extract topic, categories, and items from existing fishbone files or whiteboard photos.
- Confirm uncertain extraction results before rendering.
- Redraw into the same business-simple fishbone style.

## Phase 3: Natural-Language Extraction

- Extract fishbone structure from longer business descriptions.
- Ask for confirmation when topic or categories are ambiguous.
- Reuse the same renderer and input contract.

## Phase 4: More Diagram Types

- Add new renderers behind `diagram_type`.
- Candidate types: mind map, affinity diagram, process flow, SIPOC, FMEA, fault tree, five whys, concept map, customer journey map.
