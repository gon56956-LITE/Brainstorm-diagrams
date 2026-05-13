# Brainstorm Diagrams Skill Specification

## 1. Purpose

Create a reusable Codex skill named `brainstorm-diagrams`.

The skill generates clean, PowerPoint-ready structured thinking diagrams for brainstorming, product design, process design, failure analysis, root-cause analysis, and solution exploration.

Version 1 implementation scope is intentionally narrow:

- Implement only the `fishbone` diagram type.
- Design the architecture so additional diagram types can be added in later versions without changing the overall skill name or input model.

The first supported diagram should be a clean, corporate-style fishbone / Ishikawa / cause-and-effect diagram with a left-to-right flow and a rounded rectangle problem block on the right.

This skill should generate deterministic, editable vector output, preferably SVG, rather than using AI raster image generation.

## 2. Two-Level Skill Architecture

The skill has two conceptual layers:

### 2.1 Skill Layer

Skill name:

```text
brainstorm-diagrams
```

The skill-level responsibility is to help users choose and generate an appropriate structured thinking diagram.

It should support requests such as:

- brainstorming a topic
- product design exploration
- process design or optimization
- failure analysis
- root-cause analysis
- cause-and-effect mapping
- solution exploration
- workshop facilitation visuals
- PPT-ready structured diagrams

### 2.2 Diagram Type Layer

The skill should expose a `diagram_type` parameter.

Version 1 supports:

```text
fishbone
```

Future versions may support:

```text
mind_map
affinity_diagram
two_by_two_matrix
process_flow
swimlane
sipoc
fmea
fault_tree
five_whys
concept_map
qfd_house_of_quality
customer_journey_map
morphological_matrix
```

The skill should be designed so new diagram types can be added through additional templates, generators, and validation rules.

## 3. Version 1 Scope

Version 1 must implement only:

```text
diagram_type = fishbone
```

Do not implement the future diagram types yet. The code and documentation may mention them as future extension points, but the first implementation should remain focused and stable.

Version 1 output must be:

- SVG by default
- PNG only if explicitly requested and if a reliable conversion method is available
- PowerPoint-ready
- visually clean and professional
- editable and scalable

## 4. Recommended Skill Folder Structure

Recommended folder name:

```text
brainstorm-diagrams/
```

Recommended directory structure:

```text
brainstorm-diagrams/
├── SKILL.md
├── scripts/
│   ├── generate_diagram.py
│   └── renderers/
│       └── fishbone.py
├── templates/
│   ├── fishbone.template.md
│   └── fishbone.template.json
├── testcases/
│   ├── fishbone.input.example.json
│   └── fishbone.output.example.svg
├── references/
│   ├── diagram_types.md
│   └── visual_style_contract.md
└── README.md
```

The top-level script should dispatch by `diagram_type`.

For version 1, dispatch should accept only `fishbone` and return a clear error for unsupported diagram types.

## 5. SKILL.md Metadata

Use this metadata in `SKILL.md`:

```yaml
---
name: brainstorm-diagrams
description: Generate clean, PPT-ready structured brainstorming diagrams for product design, process design, failure analysis, root-cause analysis, and solution exploration. Version 1 supports business-simple fishbone / Ishikawa diagrams as SVG.
---
```

## 6. When to Use This Skill

Use this skill when the user asks for any of the following:

- brainstorm diagram
- structured brainstorming visual
- fishbone diagram
- Ishikawa diagram
- cause-and-effect diagram
- root-cause analysis diagram
- failure analysis diagram
- product design brainstorming diagram
- process design brainstorming diagram
- problem decomposition diagram
- solution exploration diagram
- PPT-ready analysis visual

If the user does not specify a diagram type, the skill should either:

1. choose `fishbone` when the request is about causes, factors, failure analysis, root-cause analysis, or influence categories; or
2. suggest available diagram types and ask the user to choose.

Because version 1 only implements `fishbone`, the skill should default to `fishbone` when a visual is requested and the request is compatible with a fishbone structure.

Do not use this skill for:

- realistic fish illustrations
- decorative mascot graphics
- freeform AI-generated concept art
- charts based on numeric data, unless a future diagram type explicitly supports them
- general flowcharts, unless future `process_flow` support is implemented

## 7. Diagram Type Selection Logic

Version 1 should implement this selection logic:

```text
If diagram_type is provided:
  - If diagram_type == "fishbone", generate fishbone.
  - Otherwise, explain that only fishbone is supported in version 1.

If diagram_type is not provided:
  - If the task involves causes, contributing factors, root cause, failure analysis, design variables, process factors, or brainstorm categories, use fishbone.
  - Otherwise, briefly explain that version 1 supports fishbone and ask for structured inputs if necessary.
```

Future diagram selection guidance:

| User intent | Future recommended diagram type |
|---|---|
| Free idea generation | mind_map |
| Sorting many sticky notes | affinity_diagram |
| Prioritization | two_by_two_matrix |
| Process design | process_flow or swimlane |
| Process boundary definition | sipoc |
| Failure mode prioritization | fmea |
| Logical failure decomposition | fault_tree |
| Quick root-cause questioning | five_whys |
| Concept relationships | concept_map |
| Customer needs to engineering metrics | qfd_house_of_quality |
| User experience exploration | customer_journey_map |
| Product concept combination | morphological_matrix |

## 8. Version 1 Fishbone Diagram Requirements

The generated fishbone diagram must follow these rules:

1. The diagram direction must be left to right.
2. The main spine must be a horizontal line or arrow running from left to right.
3. The right side must contain the problem, target, design challenge, or analysis topic.
4. The right-side problem block must be a simple rounded rectangle.
5. The right-side problem block must not be a triangle.
6. The right-side block must not look like a fish head.
7. Do not draw fish eyes, mouths, fins, scales, tails, skeletons, or organic fish shapes.
8. The left side may use simple chevrons or arrow marks to imply direction.
9. The style must be corporate, clean, and suitable for PowerPoint.
10. Text must remain readable and should not overlap.
11. The output should be editable and scalable.

## 9. Fishbone Use Cases

The fishbone template should work for at least these use cases:

### 9.1 Failure Analysis

Typical categories:

- People / 人员
- Process / 流程
- Equipment / 设备
- Material / 材料
- Method / 方法
- Environment / 环境

### 9.2 Product Design Brainstorming

Typical categories:

- User Needs / 用户需求
- Functions / 功能
- Performance / 性能
- Reliability / 可靠性
- Cost / 成本
- Manufacturability / 可制造性

### 9.3 Process Design

Typical categories:

- Input / 输入
- Workflow / 流程
- Roles / 角色
- Tools / 工具
- Controls / 控制
- Output / 输出

### 9.4 General Structured Brainstorming

Default categories if the user provides none:

- People / 人员
- Process / 流程
- Tools / 工具
- Environment / 环境
- Methods / 方法
- Materials / 材料

## 10. Input Schema

The skill should accept either natural language or JSON.

Recommended JSON schema:

```json
{
  "diagram_type": "fishbone",
  "title": "Brainstorm Diagram",
  "topic": "Improve product reliability",
  "topic_zh": "提升产品可靠性",
  "subtitle": "Structured Brainstorming",
  "language": "bilingual",
  "output": "svg",
  "theme": "business_simple",
  "canvas": "16:9",
  "categories": [
    {
      "name_en": "People",
      "name_zh": "人员",
      "icon": "person",
      "items": ["Skill gap", "Role clarity", "Training"]
    }
  ]
}
```

### 10.1 Required Fields

Minimum input:

```json
{
  "diagram_type": "fishbone",
  "topic": "Problem or design challenge"
}
```

If categories are missing, use the default six categories.

### 10.2 Optional Fields

```text
title
topic_zh
subtitle
language
output
theme
canvas
brand_color
logo_placeholder
categories[].name_en
categories[].name_zh
categories[].icon
categories[].items
```

### 10.3 Language Modes

Supported language values:

```text
bilingual
english
chinese
```

Default:

```text
bilingual
```

## 11. Output Requirements

Default output:

```text
SVG
```

Optional output:

```text
PNG
```

The output should be suitable for:

- insertion into PowerPoint
- scaling without quality loss
- light editing in vector tools
- sharing as a workshop or review artifact

The final message after generation should include:

- generated file path
- output format
- short description of the diagram type and theme

## 12. Fishbone Default Visual Style

The default fishbone style is:

```text
business_simple
```

This style means:

- flat vector design
- clean sans-serif typography
- white or very light gray background
- navy blue, light blue, gray, and white palette
- rounded rectangles
- thin connector lines
- small circular nodes
- subtle shadows only if professional
- minimal background decoration
- strong whitespace
- executive-review-friendly appearance

## 13. Color Palette

Default palette:

```json
{
  "background": "#FFFFFF",
  "background_alt": "#F7FAFD",
  "navy": "#0B3A75",
  "blue": "#1E5AA8",
  "light_blue": "#D9E8F7",
  "pale_blue": "#F3F8FE",
  "gray": "#7A8797",
  "light_gray": "#D6DEE8",
  "text": "#16324F",
  "muted_text": "#52677A"
}
```

Optional category accent colors:

```json
{
  "people": "#0B5CAD",
  "process": "#168DAA",
  "tools": "#F28C28",
  "environment": "#4B9B6A",
  "methods": "#7E5AC8",
  "materials": "#5C7FA3"
}
```

## 14. Typography

Use common fonts only:

```css
font-family: Arial, Helvetica, "Microsoft YaHei", "Noto Sans CJK SC", sans-serif;
```

Recommended font sizes for a 1920 x 1080 SVG:

- Category English label: 26-32 px
- Category Chinese label: 18-24 px
- Topic title in problem block: 32-44 px
- Topic Chinese subtitle: 22-30 px
- Bullet text: 18-22 px
- Small labels: 16-18 px

All text should remain horizontal. Do not rotate labels.

## 15. Fishbone Default Layout

### 15.1 Canvas

Default canvas:

```text
width: 1920
height: 1080
aspect ratio: 16:9
```

### 15.2 Main Spine

Recommended default geometry:

```text
spine_start_x: 220
spine_end_x: 1500
spine_y: 540
stroke: #0B3A75
stroke_width: 5
```

The main spine should terminate before the problem block and point toward it with a simple line arrow. The arrow should not form a large triangular fish head.

### 15.3 Left Direction Marker

Use chevrons, not a fish tail:

```text
2 or 3 layered chevrons at x = 80 to 180
color: navy and light blue
```

The left direction marker should look like a business arrow motif, not a biological fish tail.

### 15.4 Right Topic / Problem Block

The right-side block is the key design constraint.

Recommended geometry:

```text
x: 1520
y: 360
width: 300
height: 360
rx: 18
ry: 18
fill: #F8FBFF
stroke: #0B3A75
stroke_width: 3
```

It should contain:

- topic or problem statement
- optional Chinese topic
- optional short subtitle such as `Better Solution`, `Design Challenge`, or `Failure Mode`

Forbidden shapes for the right-side block:

- polygon
- triangle
- large arrowhead
- fish head
- ellipse
- circle
- blob
- organic shape

### 15.5 Branches

For six categories:

- three categories above the spine
- three categories below the spine

For four categories:

- two above
- two below

For five categories:

- three above
- two below, or two above and three below depending on spacing

For seven or eight categories:

- distribute evenly along the spine
- reduce label width or bullet count if necessary
- avoid text overlap

Each branch should include:

- circular node on the main spine
- diagonal connector line
- rounded category label
- optional icon badge
- 0-5 bullet items

## 16. Visual Style Contract

The diagram must use a clean corporate vector style.

### 16.1 Shape Language

Use only simple geometric shapes:

- lines
- circles
- rounded rectangles
- chevrons
- simple icon outlines

Avoid:

- organic shapes
- cartoon styling
- hand-drawn styling
- 3D shapes
- heavy gradients
- realistic fish elements
- decorative marine elements

### 16.2 Problem / Topic Block

The right-side topic block must be a rounded rectangle.

Recommended settings:

```text
width: 300 px
height: 360 px
corner radius: 18-24 px
fill: #F8FBFF
border: #0B3A75
border width: 3 px
```

It must not be:

- triangle
- arrowhead block
- fish head
- ellipse
- blob
- polygon
- organic shape

### 16.3 Main Spine

The main spine should be a horizontal line from left to right.

Recommended settings:

```text
stroke: #0B3A75
stroke width: 4-5 px
```

A small line arrow may point into the topic block, but it must not create a triangular head block.

### 16.4 Left Direction Marker

Use 2-3 chevrons.

Chevrons should be abstract direction markers only.

Do not use:

- fish tail
- forked biological tail
- fins
- marine silhouettes

### 16.5 Branches

Branches should be diagonal thin lines connected to circular nodes on the spine.

- Upper branches lean upward.
- Lower branches lean downward.
- Stroke: #0B3A75 or #6E93BD.
- Stroke width: 2 px.

### 16.6 Category Labels

Category labels should be rounded rectangles.

Recommended styling:

- top categories: navy fill with white text, or white fill with navy border
- bottom categories: light blue fill with navy text
- optional simple line icon in circular badge
- avoid large decorative icons

### 16.7 Bullet Lines

Bullet areas should remain visually light.

Use:

- small hollow circles
- thin gray horizontal lines
- optional short bullet text

Avoid long paragraphs inside the diagram.

### 16.8 Background

Use:

- white or #F7FAFD background
- optional subtle dotted grid
- optional faint circuit-line decoration

Background decoration must be low opacity and must not compete with the diagram.

### 16.9 Typography

Use:

```text
Arial, Helvetica, Microsoft YaHei, Noto Sans CJK SC, sans-serif
```

Rules:

- category English label should be bold
- Chinese label should be smaller and regular weight
- all text should be horizontal
- avoid vertical labels
- avoid decorative fonts

### 16.10 Visual Density

The diagram should look suitable for executive and cross-functional review.

Rules:

- maintain generous whitespace
- avoid clutter
- keep bullet text short
- avoid more than five bullets per category
- use consistent spacing between branches

## 17. Example Input

```json
{
  "diagram_type": "fishbone",
  "title": "Structured Brainstorming",
  "topic": "Improve Product Reliability",
  "topic_zh": "提升产品可靠性",
  "subtitle": "Design Challenge",
  "language": "bilingual",
  "output": "svg",
  "theme": "business_simple",
  "categories": [
    {
      "name_en": "User Needs",
      "name_zh": "用户需求",
      "icon": "person",
      "items": ["Usage scenario", "Pain points", "Expectation"]
    },
    {
      "name_en": "Functions",
      "name_zh": "功能",
      "icon": "layers",
      "items": ["Core function", "Optional feature", "Interface"]
    },
    {
      "name_en": "Performance",
      "name_zh": "性能",
      "icon": "speed",
      "items": ["Accuracy", "Speed", "Capacity"]
    },
    {
      "name_en": "Reliability",
      "name_zh": "可靠性",
      "icon": "shield",
      "items": ["Failure mode", "Lifetime", "Robustness"]
    },
    {
      "name_en": "Cost",
      "name_zh": "成本",
      "icon": "coin",
      "items": ["BOM", "Manufacturing", "Maintenance"]
    },
    {
      "name_en": "Manufacturing",
      "name_zh": "制造",
      "icon": "factory",
      "items": ["Process window", "Yield", "Scalability"]
    }
  ]
}
```

## 18. Implementation Guidance

Use Python.

Recommended approach:

1. Parse input JSON or construct JSON from natural language.
2. Validate `diagram_type`.
3. Dispatch to the appropriate renderer.
4. For version 1, use `renderers/fishbone.py`.
5. Render SVG through a Jinja2 template.
6. Escape all text safely.
7. Save output SVG.
8. Optionally convert SVG to PNG if requested.

Recommended command:

```bash
python scripts/generate_diagram.py testcases/fishbone.input.example.json output.svg
```

Version 1 dispatch behavior:

```python
if diagram_type == "fishbone":
    render_fishbone(input_data, output_path)
else:
    raise ValueError("Unsupported diagram_type in version 1. Supported: fishbone")
```

## 19. Template Design Guidance

Use deterministic renderer code for the first version. User-copyable input templates live in:

```text
templates/fishbone.template.md
templates/fishbone.template.json
```

The renderer should output:

- SVG root with 1920 x 1080 viewBox
- background rectangle
- optional subtle grid or decorative lines
- left chevrons
- main spine
- branch nodes
- branch lines
- category labels
- bullet items
- right rounded topic block

Do not hardcode all text in the template. Text should come from input data.

## 20. Validation Rules

Before returning the file, validate:

1. SVG is well formed XML.
2. The output file exists.
3. The right topic block is implemented as a rounded rectangle, preferably `<rect rx="...">`.
4. No `<polygon>` or organic `<path>` is used for the right-side topic block.
5. The diagram direction is left to right.
6. No fish-specific decorative elements are present.
7. Text elements are escaped.
8. Category count is between 4 and 8, or defaults are applied.
9. Bullet count per category is limited to 5.
10. The SVG opens in a browser.

## 21. Prohibited Visual Elements

The fishbone diagram must not include:

- realistic fish
- cartoon fish
- fish head
- fish eye
- fish mouth
- fish scales
- fish fins
- biological fish tail
- skeleton fish illustration
- ocean waves
- bubbles
- underwater decoration
- large triangular right-side head
- organic blob problem block
- heavy 3D effects
- glossy presentation effects

## 22. Error Handling

If required content is missing:

- If `topic` is missing, use `Problem / Topic`.
- If `categories` are missing, use the default six categories.
- If a category has no items, show placeholder lines or leave bullet rows blank.
- If `diagram_type` is unsupported, explain supported types for the current version.

Example unsupported diagram response:

```text
This version of brainstorm-diagrams supports only diagram_type="fishbone". The requested diagram type can be added in a future version.
```

## 23. Future Extension Plan

Future versions may add new renderers under:

```text
scripts/renderers/
```

Each new diagram type should include:

- renderer Python module
- SVG template
- example input JSON
- validation rules
- visual style rules
- documentation in `references/diagram_types.md`

Potential future modules:

```text
renderers/mind_map.py
renderers/affinity_diagram.py
renderers/two_by_two_matrix.py
renderers/process_flow.py
renderers/swimlane.py
renderers/sipoc.py
renderers/fmea.py
renderers/fault_tree.py
renderers/five_whys.py
renderers/concept_map.py
renderers/qfd_house_of_quality.py
renderers/customer_journey_map.py
renderers/morphological_matrix.py
```

The common theme system should be shared across diagram types.

## 24. Acceptance Criteria

The implementation is acceptable when:

1. The skill folder is named `brainstorm-diagrams`.
2. `SKILL.md` uses the `brainstorm-diagrams` name and explains the broader scope.
3. Version 1 supports `diagram_type="fishbone"`.
4. Unsupported diagram types produce a clear version 1 limitation message.
5. The generated fishbone is left-to-right.
6. The right-side topic block is a rounded rectangle, not a triangle.
7. There are no realistic or cartoon fish elements.
8. The visual style is clean, business-simple, and PPT-ready.
9. The SVG is valid and opens in a browser.
10. Example input and output files are included.
11. The code structure allows future diagram types to be added cleanly.

## 25. One-Sentence Implementation Brief

Build a reusable Codex skill named `brainstorm-diagrams` that can generate PPT-ready structured brainstorming diagrams; version 1 implements only a business-simple fishbone diagram as deterministic SVG, while the architecture reserves `diagram_type` for future templates such as mind maps, affinity diagrams, process flows, SIPOC, FMEA, fault trees, and other design-analysis diagrams.
