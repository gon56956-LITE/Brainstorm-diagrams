# Brainstorm Diagrams Skill Spec: Roadmap / Timeline

## 1. Purpose

This document defines the `roadmap_timeline` diagram module for the `brainstorm-diagrams` Codex skill.

The purpose of this module is to generate clean, PPT-ready roadmap and timeline diagrams for planning, sequencing, and communicating initiatives over time.

The diagram should follow the same business-simple visual style used by the existing `fishbone`, `fault_tree`, `exclusion_tree`, and `two_by_two_matrix` modules.

This module is intended for:

- product roadmap planning
- product family or product model planning
- technology roadmap planning
- process improvement planning
- project milestone communication
- phased execution plans
- release planning
- cross-team initiative planning
- management review presentations

---

## 2. Diagram Type

```json
{
  "diagram_type": "roadmap_timeline"
}
```

The `roadmap_timeline` diagram type supports two presets:

```json
{
  "preset": "swimlane_roadmap"
}
```

```json
{
  "preset": "milestone_timeline"
}
```

### Recommended default

If the user asks for a roadmap and gives multiple products, models, teams, modules, workstreams, or themes, use:

```json
{
  "diagram_type": "roadmap_timeline",
  "preset": "swimlane_roadmap"
}
```

If the user asks for a simple timeline, milestone line, project timeline, or key dates only, use:

```json
{
  "diagram_type": "roadmap_timeline",
  "preset": "milestone_timeline"
}
```

If the user does not specify a preset, infer it from the input structure.

---

## 3. Preset Overview

| Preset | Main Use Case | Visual Structure | Complexity |
|---|---|---|---|
| `swimlane_roadmap` | Multi-lane planning across products, models, themes, modules, regions, or teams | Time axis + horizontal swimlanes + initiative bars + milestones | Full roadmap |
| `milestone_timeline` | Simple sequence of key events or project stages | Single timeline + milestone nodes | Lightweight timeline |

---

## 4. Preset 1: Swimlane Roadmap

### 4.1 Purpose

`swimlane_roadmap` is used to show multiple parallel tracks over time.

It answers questions such as:

- What initiatives happen in each lane?
- Which workstreams run in parallel?
- What is the sequence across product models or modules?
- Where are the key milestones, launch dates, decision points, and reviews?
- Are there overlaps, dependencies, or resource conflicts?

### 4.2 Typical lane meanings

The lane meaning must be configurable through `lane_type`.

```json
{
  "lane_type": "product_model"
}
```

Supported recommended `lane_type` values:

| lane_type | Meaning | Example Lanes |
|---|---|---|
| `theme` | Strategic themes or work themes | Customer Value, Platform & Tech, Operations, Compliance |
| `product_model` | Different models in the same product family | Model A, Model B, Model C, Premium Model |
| `product_generation` | Product generations | Gen 1, Gen 2, Gen 3 |
| `platform_module` | Technical modules or subsystems | Optical Engine, Control Board, Firmware, Packaging |
| `team` | Responsible teams | Hardware, Software, Operations, Quality |
| `region` | Market or launch regions | China, EU, US, APAC |
| `customer_segment` | Customer or market segments | Enterprise, Consumer, Industrial |
| `workstream` | Project workstreams | Design, Validation, Manufacturing, Launch |

Important: `lane_type` is not a separate preset. It is the semantic meaning of the swimlanes.

### 4.3 Common stage labels

For product model roadmaps, common initiative/stage labels may include:

- Concept
- Requirement Freeze
- Architecture
- Design
- Prototype
- EVT
- DVT
- PVT
- Pilot
- MP / Mass Production
- Launch
- Upgrade
- EOL

For technology roadmaps, common labels may include:

- Research
- Feasibility Study
- Prototype
- Integration
- Validation
- Platform Release
- Scale-up

For process improvement roadmaps, common labels may include:

- Current State Review
- Gap Analysis
- Process Design
- Pilot
- Deployment
- Continuous Improvement

---

## 5. Preset 2: Milestone Timeline

### 5.1 Purpose

`milestone_timeline` is a lightweight single-line timeline used to communicate key dates or stages.

It answers questions such as:

- What are the key project milestones?
- What is the sequence from kickoff to launch?
- What happened first, next, and last?
- What are the major review or decision points?

### 5.2 Visual structure

The milestone timeline should use:

- one horizontal time axis
- milestone nodes placed along the axis
- labels above or below each node
- optional phase bands or short date ranges
- optional status chips
- optional small summary table

### 5.3 When to use milestone timeline

Use this preset when the input contains:

- a single project or initiative
- a list of key events
- key dates without multiple lanes
- simple project phases
- management summary timeline

Examples:

```text
Create a timeline for our product launch milestones.
```

```text
Make a simple timeline from concept review to launch.
```

```text
Show key decision points for this program.
```

---

## 6. Visual Style Contract

All roadmap and timeline diagrams must follow the existing `brainstorm-diagrams` business-simple style.

### 6.1 Overall style

- Clean corporate presentation style
- White or very light gray background
- Navy blue as the primary color
- Light blue and gray as neutral support colors
- Limited accent colors for categories, statuses, or lanes
- No decorative illustration-heavy style
- No cartoon, hand-drawn, or 3D effects
- Ready for PowerPoint executive review

### 6.2 Color palette

Recommended colors:

```text
Primary navy:       #0B3A75
Dark navy:          #082B59
Light blue:         #DCEBFF
Pale blue:          #F3F8FF
Medium blue:        #3B73D9
Border blue:        #9DBCE8
Text navy:          #0B234A
Muted text gray:    #5F6F86
Grid line:          #D8E1EE
Background:         #FFFFFF or #F7FAFD
```

Optional lane accent colors:

```text
Blue:      #2F6BFF
Teal:      #2C9C96
Purple:    #7A5CCB
Orange:    #F0A22E
Green:     #2E9D5B
Red:       #D64545  only for risk or blocked status
Gray:      #8A96A8
```

### 6.3 Typography

Use common sans-serif fonts:

```text
Arial, Helvetica, Microsoft YaHei, sans-serif
```

Recommended hierarchy:

- Main title: 40-48 px, bold, navy
- Subtitle: 20-24 px, regular or medium
- Time period headers: 18-22 px, bold, white text on navy background
- Lane labels: 18-22 px, bold
- Initiative labels: 14-18 px, medium
- Table text: 12-15 px
- Notes and legends: 12-14 px

### 6.4 Shape language

Use simple geometric vector shapes:

- rounded rectangles
- horizontal bars
- straight lines
- circles
- stars for major milestones
- diamonds for decision points
- small status dots
- simple line icons

Avoid:

- realistic illustrations
- people illustrations
- 3D effects
- heavy shadows
- cluttered gradients
- excessive decoration

### 6.5 Layout ratio

Default canvas:

```json
{
  "width": 1920,
  "height": 1080,
  "aspect_ratio": "16:9"
}
```

The layout should be optimized for a single PPT slide.

---

## 7. Swimlane Roadmap Layout Specification

### 7.1 Recommended page structure

A full swimlane roadmap slide should contain:

1. Title and subtitle area
2. Optional goal or scope line
3. Legend box
4. Main roadmap grid
5. Optional initiative table
6. Optional milestone / decision point summary panel
7. Optional notes panel

Recommended composition:

```text
+--------------------------------------------------------------+
| Title / Subtitle                                      Legend  |
| Goal line                                                     |
|--------------------------------------------------------------|
| Lane labels | Time grid with initiative bars and milestones  |
|--------------------------------------------------------------|
| Initiative table                         | Milestones / Notes |
+--------------------------------------------------------------+
```

### 7.2 Time axis

The time axis should run left to right.

Supported time granularities:

```text
month
quarter
half_year
year
custom_phase
```

Default:

```json
{
  "time_granularity": "quarter"
}
```

Examples of time headers:

```text
2025 Q2
Apr - Jun
```

```text
2026 H1
Jan - Jun
```

```text
Phase 1
Concept
```

### 7.3 Lanes

Each lane is a horizontal row.

Each lane should have:

- icon, optional
- lane name
- lane subtitle, optional
- lane color, optional
- horizontal band or row background

Lane label area should be fixed-width on the left.

Recommended lane label width:

```text
220-280 px
```

Recommended roadmap grid width:

```text
1300-1500 px
```

### 7.4 Initiative bars

An initiative bar represents an activity with a start and end date or phase.

Recommended style:

- rounded rectangle
- light fill color based on lane or theme
- border color slightly darker than fill
- centered label
- optional status dot at the end
- optional progress indicator, if provided

Bar height:

```text
32-44 px
```

Corner radius:

```text
6-10 px
```

### 7.5 Milestones

A milestone is a point event on the timeline.

Recommended shapes:

| Type | Shape |
|---|---|
| Normal milestone | filled circle |
| Key milestone | star |
| Decision point | diamond |
| Launch | star or flag icon |
| Review | diamond or outlined circle |

Milestone labels should be short.

If labels overlap, place some above the bar and some below, or move them to a side summary panel.

### 7.6 Dependencies

Dependencies are optional.

If present, use:

- thin dashed line
- arrow head
- gray-blue stroke
- avoid crossing too many bars

Default behavior: omit dependency lines unless explicitly requested.

### 7.7 Status

Supported status values:

```text
planned
in_progress
completed
at_risk
blocked
delayed
```

Recommended status visual:

| Status | Visual |
|---|---|
| planned | gray dot |
| in_progress | blue dot |
| completed | green dot or check |
| at_risk | orange dot or warning icon |
| blocked | red dot or stop icon |
| delayed | orange/red outline |

Do not overuse strong red. Red should only indicate blocked or serious risk.

---

## 8. Milestone Timeline Layout Specification

### 8.1 Recommended page structure

A milestone timeline slide should contain:

1. Title and subtitle
2. Single horizontal timeline axis
3. Milestone nodes
4. Optional phase bands
5. Optional detail cards
6. Optional summary table or notes

Recommended composition:

```text
+--------------------------------------------------------------+
| Title / Subtitle                                      Legend  |
|--------------------------------------------------------------|
|        o--------◆--------★--------o--------◆--------★        |
|      Kickoff   Review   Launch   Pilot     MP      Close     |
|--------------------------------------------------------------|
| Optional milestone details / notes / owners                  |
+--------------------------------------------------------------+
```

### 8.2 Timeline axis

Use a horizontal line with arrow or no arrow depending on context.

Recommended:

- navy stroke
- 3-4 px width
- subtle tick marks
- date labels below or above

### 8.3 Milestone nodes

Use consistent milestone shapes:

| Milestone Type | Shape |
|---|---|
| start | filled circle |
| review | diamond |
| key milestone | star |
| launch | star or flag |
| decision | diamond |
| end | filled circle or check |

### 8.4 Detail cards

If a milestone needs details, use a small rounded rectangle near the node.

Detail card fields may include:

- milestone name
- date
- owner
- status
- key output

Avoid long paragraphs inside milestone cards.

---

## 9. Input Schema

### 9.1 Shared schema

```json
{
  "diagram_type": "roadmap_timeline",
  "preset": "swimlane_roadmap",
  "title": "Product Family Roadmap",
  "title_zh": "产品族路线图",
  "subtitle": "Roadmap across product models and key development phases",
  "subtitle_zh": "按产品型号展示关键开发阶段",
  "goal": "Align product model launches and validation milestones.",
  "language": "bilingual",
  "style": "business_simple",
  "canvas": {
    "width": 1920,
    "height": 1080,
    "aspect_ratio": "16:9"
  }
}
```

### 9.2 Swimlane roadmap schema

```json
{
  "diagram_type": "roadmap_timeline",
  "preset": "swimlane_roadmap",
  "lane_type": "product_model",
  "time_granularity": "quarter",
  "time_periods": [
    {
      "id": "2025Q2",
      "label": "2025 Q2",
      "subtitle": "Apr - Jun",
      "start": "2025-04-01",
      "end": "2025-06-30"
    },
    {
      "id": "2025Q3",
      "label": "2025 Q3",
      "subtitle": "Jul - Sep",
      "start": "2025-07-01",
      "end": "2025-09-30"
    }
  ],
  "lanes": [
    {
      "id": "model_a",
      "name": "Model A",
      "name_zh": "型号 A",
      "subtitle": "Entry Level",
      "color": "blue",
      "icon": "box"
    },
    {
      "id": "model_b",
      "name": "Model B",
      "name_zh": "型号 B",
      "subtitle": "Standard",
      "color": "teal",
      "icon": "layers"
    }
  ],
  "initiatives": [
    {
      "id": "A1",
      "lane_id": "model_a",
      "name": "Concept Design",
      "name_zh": "概念设计",
      "start": "2025-04-01",
      "end": "2025-06-30",
      "owner": "Product Team",
      "status": "completed"
    },
    {
      "id": "A2",
      "lane_id": "model_a",
      "name": "EVT",
      "name_zh": "工程验证测试",
      "start": "2025-07-01",
      "end": "2025-09-30",
      "owner": "Engineering Team",
      "status": "in_progress"
    }
  ],
  "milestones": [
    {
      "id": "M1",
      "lane_id": "model_a",
      "name": "EVT Complete",
      "name_zh": "EVT 完成",
      "date": "2025-09-15",
      "type": "key_milestone"
    }
  ],
  "decision_points": [
    {
      "id": "D1",
      "lane_id": "model_b",
      "name": "Architecture Review",
      "name_zh": "架构评审",
      "date": "2025-08-15"
    }
  ],
  "show_table": true,
  "show_summary_panel": true
}
```

### 9.3 Milestone timeline schema

```json
{
  "diagram_type": "roadmap_timeline",
  "preset": "milestone_timeline",
  "title": "Launch Timeline",
  "title_zh": "发布里程碑时间线",
  "time_granularity": "month",
  "milestones": [
    {
      "id": "T1",
      "name": "Kickoff",
      "name_zh": "项目启动",
      "date": "2025-04-01",
      "type": "start",
      "owner": "PMO",
      "status": "completed"
    },
    {
      "id": "T2",
      "name": "Design Review",
      "name_zh": "设计评审",
      "date": "2025-06-15",
      "type": "review",
      "owner": "Engineering",
      "status": "in_progress"
    },
    {
      "id": "T3",
      "name": "Launch",
      "name_zh": "发布",
      "date": "2025-10-01",
      "type": "launch",
      "owner": "Product Team",
      "status": "planned"
    }
  ],
  "phases": [
    {
      "name": "Design Phase",
      "name_zh": "设计阶段",
      "start": "2025-04-01",
      "end": "2025-06-30"
    },
    {
      "name": "Validation Phase",
      "name_zh": "验证阶段",
      "start": "2025-07-01",
      "end": "2025-09-30"
    }
  ],
  "show_detail_cards": true,
  "show_table": false
}
```

---

## 10. Output Requirements

The generator must output:

1. SVG by default
2. Optional PNG export if requested
3. Valid, browser-openable SVG
4. PPT-ready 16:9 layout

Recommended output file naming:

```text
roadmap_timeline_swimlane_roadmap.svg
roadmap_timeline_milestone_timeline.svg
```

If PNG is requested:

```text
roadmap_timeline_swimlane_roadmap.png
roadmap_timeline_milestone_timeline.png
```

---

## 11. Natural Language Inference Rules

The skill should infer preset and lane type from natural language.

### 11.1 Preset inference

Use `swimlane_roadmap` when the user mentions:

- roadmap
- product roadmap
- product family roadmap
- product model roadmap
- platform roadmap
- technology roadmap
- multiple products
- multiple models
- multiple teams
- multiple regions
- swimlane
- workstreams
- parallel tracks

Use `milestone_timeline` when the user mentions:

- simple timeline
- milestone timeline
- key milestones
- project timeline
- launch timeline
- sequence of events
- one-line timeline
- single timeline

### 11.2 Lane type inference

| User wording | lane_type |
|---|---|
| different models, product models, SKUs | `product_model` |
| product generations, Gen 1 / Gen 2 | `product_generation` |
| modules, subsystems, components | `platform_module` |
| teams, departments, owners | `team` |
| markets, regions, countries | `region` |
| customer types, segments | `customer_segment` |
| themes, strategic pillars | `theme` |
| workstreams | `workstream` |

### 11.3 Default fallback

If no clear lane type is provided, use:

```json
{
  "lane_type": "theme"
}
```

If no preset is provided and the input has more than one lane, use `swimlane_roadmap`.

If the input has only a list of dated milestones, use `milestone_timeline`.

---

## 12. Tables and Side Panels

### 12.1 Swimlane roadmap table

For `swimlane_roadmap`, include an optional initiative table below the main roadmap if `show_table` is true.

Recommended columns:

| Column | Description |
|---|---|
| ID | Initiative ID |
| Initiative / 项目 | Initiative name |
| Lane / 泳道 | Product model, theme, team, etc. |
| Owner / 负责人 | Owner |
| Start | Start date |
| End | End date |
| Duration | Duration |
| Key Milestone | Key milestone name/date |
| Status | Planned, in progress, completed, etc. |

### 12.2 Milestone summary panel

For `swimlane_roadmap`, include a right-side summary panel if `show_summary_panel` is true.

Recommended sections:

- Key Milestones
- Decision Points
- Risks / Notes

### 12.3 Milestone timeline detail table

For `milestone_timeline`, a table is optional. If shown, use:

| Column | Description |
|---|---|
| Date | Milestone date |
| Milestone | Milestone name |
| Owner | Responsible owner |
| Status | Status |
| Output | Expected output |

---

## 13. Component Library

The implementation should use reusable SVG components.

Recommended components:

```text
TitleBlock
LegendBox
TimeHeader
RoadmapGrid
LaneLabel
InitiativeBar
MilestoneMarker
DecisionPointMarker
StatusDot
DependencyArrow
SummaryPanel
InitiativeTable
MilestoneTimelineAxis
MilestoneDetailCard
NotesPanel
```

Do not create completely separate code paths for every visual variation. Use shared components and preset-specific layout configuration.

---

## 14. Implementation Guidance for Codex

### 14.1 Recommended directory structure

```text
brainstorm-diagrams/
├─ SKILL.md
├─ references/
│  ├─ visual_style_contract.md
│  ├─ roadmap_timeline_spec.md
│  └─ roadmap_timeline_examples.md
├─ assets/
│  └─ roadmap_timeline/
│     ├─ swimlane_roadmap_reference.png
│     └─ milestone_timeline_reference.png
├─ examples/
│  ├─ roadmap_swimlane_product_model_input.json
│  ├─ roadmap_swimlane_theme_input.json
│  └─ roadmap_milestone_timeline_input.json
├─ templates/
│  ├─ roadmap_swimlane.svg.j2
│  └─ roadmap_milestone_timeline.svg.j2
└─ scripts/
   └─ generate_diagram.py
```

### 14.2 Generator behavior

The generator should:

1. Parse JSON input.
2. Infer preset if missing.
3. Infer lane type if missing.
4. Normalize dates and time periods.
5. Compute x positions based on dates or custom phases.
6. Compute y positions based on lanes.
7. Render the SVG using reusable components.
8. Avoid overlapping labels where possible.
9. Add legend and notes only when useful.
10. Validate that SVG is well-formed.

### 14.3 Date handling

The generator should support:

- explicit ISO dates: `YYYY-MM-DD`
- quarterly periods
- monthly periods
- custom phases

If exact dates are not provided, allow symbolic periods such as:

```json
{
  "start_period": "2025 Q2",
  "end_period": "2025 Q3"
}
```

But internal rendering should normalize to a timeline scale.

### 14.4 Label overlap handling

If milestone labels overlap:

- alternate labels above and below the timeline
- reduce font size within allowed limits
- move long descriptions to summary panel
- truncate long labels with ellipsis only if necessary

If initiative bars are too short for labels:

- place label outside the bar
- or use a numbered marker and table reference

---

## 15. Validation Rules

Before returning the final file, verify:

### General

- SVG opens in a browser.
- Diagram is 16:9 and PPT-ready.
- Style matches business-simple visual system.
- Text is readable.
- No major label overlap.
- Navy/light-blue/gray visual system is used consistently.

### Swimlane roadmap

- Time axis runs left to right.
- Lane labels are clearly visible.
- Every initiative belongs to a valid lane.
- Bars align with correct time periods.
- Milestones are positioned correctly by date or period.
- Decision points use diamond markers.
- Status indicators are consistent.

### Milestone timeline

- Timeline is single-line or clearly sequential.
- Milestones appear in chronological order.
- Key milestones are visually emphasized.
- Labels are readable and not overcrowded.

---

## 16. Anti-Patterns and Forbidden Outputs

Do not generate:

- decorative infographic without usable planning structure
- random icons without meaning
- overly colorful consumer-style design
- 3D timeline
- cartoon roadmap
- winding road illustration unless explicitly requested
- overly complex Gantt chart with unreadable text
- dense project management chart that cannot fit a PPT slide
- Mermaid-only output when user requests a visual file
- raster-only output when SVG is feasible

For this skill, roadmap/timeline should be clear, structured, and editable.

---

## 17. Relationship to Other Diagram Types

Within `brainstorm-diagrams`, this module is usually used after ideation and prioritization.

Recommended flow:

```text
mind_map / fishbone
        ↓
two_by_two_matrix / decision_matrix
        ↓
roadmap_timeline
```

For failure analysis or engineering action planning:

```text
fishbone / fault_tree
        ↓
exclusion_tree / cause_screening_matrix
        ↓
roadmap_timeline
```

For product design:

```text
qfd_house_of_quality / morphological_matrix
        ↓
two_by_two_matrix / decision_matrix
        ↓
roadmap_timeline
```

---

## 18. Example: Product Model Swimlane Roadmap

```json
{
  "diagram_type": "roadmap_timeline",
  "preset": "swimlane_roadmap",
  "lane_type": "product_model",
  "title": "Product Model Roadmap",
  "title_zh": "产品型号路线图",
  "subtitle": "Roadmap across models A, B, and C",
  "subtitle_zh": "按型号展示开发、验证与发布节奏",
  "time_granularity": "quarter",
  "time_periods": [
    {"id": "2025Q2", "label": "2025 Q2", "subtitle": "Apr - Jun", "start": "2025-04-01", "end": "2025-06-30"},
    {"id": "2025Q3", "label": "2025 Q3", "subtitle": "Jul - Sep", "start": "2025-07-01", "end": "2025-09-30"},
    {"id": "2025Q4", "label": "2025 Q4", "subtitle": "Oct - Dec", "start": "2025-10-01", "end": "2025-12-31"},
    {"id": "2026Q1", "label": "2026 Q1", "subtitle": "Jan - Mar", "start": "2026-01-01", "end": "2026-03-31"}
  ],
  "lanes": [
    {"id": "A", "name": "Model A", "name_zh": "型号 A", "subtitle": "Entry Level", "color": "blue"},
    {"id": "B", "name": "Model B", "name_zh": "型号 B", "subtitle": "Standard", "color": "teal"},
    {"id": "C", "name": "Model C", "name_zh": "型号 C", "subtitle": "Premium", "color": "purple"}
  ],
  "initiatives": [
    {"id": "A1", "lane_id": "A", "name": "Concept", "name_zh": "概念", "start": "2025-04-01", "end": "2025-06-30", "owner": "Product", "status": "completed"},
    {"id": "A2", "lane_id": "A", "name": "EVT", "name_zh": "工程验证", "start": "2025-07-01", "end": "2025-09-30", "owner": "Engineering", "status": "in_progress"},
    {"id": "A3", "lane_id": "A", "name": "Launch", "name_zh": "发布", "start": "2025-10-01", "end": "2025-12-31", "owner": "Product", "status": "planned"},
    {"id": "B1", "lane_id": "B", "name": "Architecture", "name_zh": "架构", "start": "2025-04-01", "end": "2025-09-30", "owner": "Engineering", "status": "in_progress"},
    {"id": "B2", "lane_id": "B", "name": "DVT", "name_zh": "设计验证", "start": "2025-10-01", "end": "2026-03-31", "owner": "Validation", "status": "planned"},
    {"id": "C1", "lane_id": "C", "name": "Feasibility", "name_zh": "可行性研究", "start": "2025-07-01", "end": "2025-12-31", "owner": "R&D", "status": "planned"}
  ],
  "milestones": [
    {"id": "M1", "lane_id": "A", "name": "Model A Launch", "name_zh": "型号 A 发布", "date": "2025-11-15", "type": "launch"},
    {"id": "M2", "lane_id": "B", "name": "DVT Complete", "name_zh": "DVT 完成", "date": "2026-03-15", "type": "key_milestone"}
  ],
  "decision_points": [
    {"id": "D1", "lane_id": "C", "name": "Go / No-Go", "name_zh": "是否立项", "date": "2025-12-01"}
  ],
  "show_table": true,
  "show_summary_panel": true
}
```

---

## 19. Example: Lightweight Milestone Timeline

```json
{
  "diagram_type": "roadmap_timeline",
  "preset": "milestone_timeline",
  "title": "Program Launch Timeline",
  "title_zh": "项目发布关键时间线",
  "subtitle": "Key milestones from kickoff to launch",
  "subtitle_zh": "从启动到发布的关键节点",
  "milestones": [
    {"id": "T1", "name": "Kickoff", "name_zh": "启动", "date": "2025-04-01", "type": "start", "owner": "PMO", "status": "completed"},
    {"id": "T2", "name": "Design Freeze", "name_zh": "设计冻结", "date": "2025-06-30", "type": "key_milestone", "owner": "Engineering", "status": "planned"},
    {"id": "T3", "name": "Pilot Build", "name_zh": "试产", "date": "2025-08-15", "type": "milestone", "owner": "Operations", "status": "planned"},
    {"id": "T4", "name": "Launch", "name_zh": "发布", "date": "2025-10-01", "type": "launch", "owner": "Product", "status": "planned"}
  ],
  "show_detail_cards": true,
  "show_table": false
}
```

---

## 20. Codex Implementation Prompt

Use this prompt when asking Codex to implement the module:

```text
Implement the `roadmap_timeline` diagram module for the existing `brainstorm-diagrams` skill.

The module must support two presets:
1. `swimlane_roadmap` for multi-lane roadmap planning.
2. `milestone_timeline` for lightweight single-line milestone timelines.

Use the existing business-simple visual system: white/light background, navy primary color, light-blue panels, subtle gray grid, rounded rectangles, clean sans-serif typography, and PPT-ready 16:9 SVG output.

For `swimlane_roadmap`, support configurable `lane_type`, including product_model, theme, product_generation, platform_module, team, region, customer_segment, and workstream. Lanes must not be hard-coded as themes only. The same template must be able to show different product models as lanes.

For `milestone_timeline`, create a simpler one-line timeline with milestone markers, labels, and optional detail cards.

Implement reusable SVG components for time headers, lane labels, initiative bars, milestones, decision points, status dots, legends, tables, and notes panels.

Inputs must be accepted as JSON. If `preset` is missing, infer it from the input. If multiple lanes are present, use `swimlane_roadmap`. If only a list of dated milestones is present, use `milestone_timeline`.

Output valid SVG by default and optional PNG if requested. Validate that the generated SVG opens in a browser, has readable labels, and is suitable for PowerPoint.
```

---

## 21. Version Plan

Recommended integration into `brainstorm-diagrams`:

```text
v0.1 fishbone
v0.2 fault_tree
v0.3 exclusion_tree
v0.4 two_by_two_matrix
v0.5 roadmap_timeline
```

For `roadmap_timeline`:

```text
v0.5.1 swimlane_roadmap
v0.5.2 milestone_timeline
```

The swimlane roadmap should be treated as the primary roadmap capability. The milestone timeline should be lightweight but supported for user convenience.
