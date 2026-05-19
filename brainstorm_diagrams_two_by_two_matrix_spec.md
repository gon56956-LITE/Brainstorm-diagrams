# Brainstorm Diagrams Skill Spec: `two_by_two_matrix`

## 1. Purpose

This document defines the `two_by_two_matrix` diagram type for the `brainstorm-diagrams` skill.

The purpose of this diagram type is to provide a reusable 2x2 matrix framework for structured brainstorming, screening, prioritization, and decision support.

The visual structure remains consistent across use cases, while the business meaning is controlled by an optional `preset` parameter.

The user should not need to understand or explicitly specify presets. The skill should infer the preset from natural language whenever possible.

---

## 2. Relationship to the Overall Skill

Skill name:

```text
brainstorm-diagrams
```

Diagram type:

```text
two_by_two_matrix
```

Recommended role in the skill:

```text
fishbone               = divergent cause brainstorming
fault_tree             = logical failure decomposition
exclusion_tree         = verification and elimination workflow
two_by_two_matrix      = quick prioritization and screening
cause_screening_matrix = detailed scoring and ranking
```

The `two_by_two_matrix` diagram is a general visual structure. Specific business meanings should be handled through `preset`.

---

## 3. Core Design Principle

Use two layers:

```text
diagram_type = visual structure
preset       = business interpretation
```

Example:

```json
{
  "diagram_type": "two_by_two_matrix",
  "preset": "action_priority"
}
```

Do not create separate diagram types for every 2x2 use case.

For example, avoid:

```text
action_priority_matrix
risk_benefit_matrix
evidence_impact_matrix
value_feasibility_matrix
```

Instead, use:

```text
diagram_type = two_by_two_matrix
preset = action_priority | risk_benefit | evidence_impact | value_feasibility | urgency_importance
```

---

## 4. User Experience Requirement

The preset is an optional advanced parameter.

The user may say:

```text
Make an action priority matrix.
```

The skill should internally map this to:

```json
{
  "diagram_type": "two_by_two_matrix",
  "preset": "action_priority"
}
```

The user may say:

```text
Put these failure causes into a 2x2 matrix by evidence and impact.
```

The skill should internally map this to:

```json
{
  "diagram_type": "two_by_two_matrix",
  "preset": "evidence_impact"
}
```

The user may say:

```text
Help me compare these product features by customer value and feasibility.
```

The skill should internally map this to:

```json
{
  "diagram_type": "two_by_two_matrix",
  "preset": "value_feasibility"
}
```

Do not force the user to select a preset unless the intent is genuinely ambiguous.

---

## 5. First Supported Presets

The first implementation should support these presets:

```json
{
  "supported_presets": [
    "action_priority",
    "risk_benefit",
    "evidence_impact",
    "value_feasibility",
    "urgency_importance"
  ]
}
```

Optional future presets:

```json
{
  "future_presets": [
    "cost_performance",
    "impact_confidence",
    "complexity_value"
  ]
}
```

---

## 6. Preset Overview

| Preset | Main Use Case | X Axis | Y Axis | Main Output |
|---|---|---|---|---|
| `action_priority` | Action prioritization | Effort | Impact | What to do first |
| `risk_benefit` | Project or option decision | Risk | Benefit | Whether risk is justified |
| `evidence_impact` | Failure analysis cause screening | Evidence | Impact | Which causes to verify first |
| `value_feasibility` | Product feature screening | Technical Feasibility | Customer Value | Which features to build or explore |
| `urgency_importance` | Task or issue management | Urgency | Importance | What to do, schedule, delegate, or drop |

Important axis direction rule:

- For `effort`, `risk`, `urgency`, and `cost`, moving right generally means more of that property.
- For `feasibility`, moving right means easier or more feasible.
- The quadrant labels must respect the axis direction.

---

## 7. Shared Visual Style

The diagram must match the existing `brainstorm-diagrams` business-simple style used by fishbone, fault tree, and exclusion tree.

### 7.1 Overall Style

Use:

- White or very light gray background.
- Navy blue, light blue, gray, and white palette.
- Clean corporate presentation style.
- 16:9 canvas, default 1920 x 1080.
- SVG as the primary output format.
- PPT-ready layout.
- Thin, crisp vector shapes.
- No decorative illustration-heavy style.
- No 3D, realistic, cartoon, or hand-drawn appearance.

### 7.2 Recommended Palette

```json
{
  "background": "#F7FAFD",
  "panel_fill": "#FFFFFF",
  "navy": "#0B3A75",
  "blue": "#2F80ED",
  "light_blue": "#EAF3FF",
  "pale_blue": "#F3F8FF",
  "gray_text": "#4B5563",
  "light_gray": "#E5E7EB",
  "mid_gray": "#9CA3AF",
  "success": "#2E7D32",
  "warning": "#F59E0B",
  "danger": "#C62828"
}
```

Use status colors sparingly. The primary visual identity should remain navy, light blue, gray, and white.

### 7.3 Typography

Use common fonts only:

```text
Arial, Helvetica, Microsoft YaHei, sans-serif
```

Recommended hierarchy:

| Element | Size | Weight |
|---|---:|---|
| Slide title | 34-42 px | Bold |
| Subtitle | 18-22 px | Regular |
| Axis label | 18-22 px | Bold |
| Quadrant title | 20-24 px | Bold |
| Item label | 14-18 px | Regular or medium |
| Table header | 14-16 px | Bold |
| Table cell | 12-15 px | Regular |

---

## 8. Default Layout

Default canvas:

```json
{
  "width": 1920,
  "height": 1080,
  "ratio": "16:9"
}
```

Recommended layout:

```text
Top: title and subtitle
Left / center: 2x2 matrix
Right: supporting table or summary panel
Bottom: legend or brief interpretation note
```

Recommended geometry:

```json
{
  "canvas": {"width": 1920, "height": 1080},
  "margin": 80,
  "title_area_height": 120,
  "matrix": {
    "x": 110,
    "y": 190,
    "width": 1080,
    "height": 720
  },
  "side_panel": {
    "x": 1240,
    "y": 190,
    "width": 600,
    "height": 720
  },
  "footer": {
    "x": 110,
    "y": 930,
    "width": 1730,
    "height": 80
  }
}
```

If no right-side table is requested, the matrix may be centered and enlarged.

---

## 9. Matrix Structure

The 2x2 matrix must contain:

1. Horizontal x-axis.
2. Vertical y-axis.
3. Four quadrants.
4. Quadrant names.
5. Optional quadrant descriptions.
6. Data points representing items.
7. Axis direction labels such as Low / High.
8. Optional legend.
9. Optional right-side table.

### 9.1 Quadrant Layout

Use a clean square or near-square matrix.

Quadrants:

```text
Top-left     = high Y, low X
Top-right    = high Y, high X
Bottom-left  = low Y, low X
Bottom-right = low Y, high X
```

Use subtle fill colors. Do not make the quadrant backgrounds too saturated.

Recommended quadrant fills:

```json
{
  "top_left": "#EAF3FF",
  "top_right": "#F3F8FF",
  "bottom_left": "#FFFFFF",
  "bottom_right": "#F8FAFC"
}
```

### 9.2 Axis Labels

Axis labels must change by preset.

Default label format:

```text
Single language selected by language mode
```

Example:

```text
Impact
Effort
```

Use English for English input, Chinese for Chinese input, or the explicitly requested language. Do not render English/Chinese paired labels by default.

### 9.3 Data Points

Data points should be rendered as small circular or rounded pill markers.

Recommended marker style:

```json
{
  "shape": "circle",
  "diameter": 32,
  "fill": "#FFFFFF",
  "stroke": "#0B3A75",
  "stroke_width": 2,
  "label": "ID"
}
```

If the item name is short, show the name next to the marker. If item names are long, show only IDs in the matrix and list details in the right-side table.

### 9.4 Data Point Positioning

The v1 renderer uses numeric x/y scores for quadrant classification, side-table scoring, and deterministic sorting. It does not render precise scatter or bubble positions.

Default score scale:

```json
{
  "min": 1,
  "max": 5
}
```

If only quadrant is provided, place the item within the specified quadrant using deterministic spacing.

---

## 10. Shared Input Schema

The `two_by_two_matrix` should accept the following common schema.

```json
{
  "diagram_type": "two_by_two_matrix",
  "preset": "action_priority",
  "title": "Action Priority Matrix",
  "subtitle": "Prioritize improvement actions by impact and effort",
  "language": "auto",
  "style": "business_simple",
  "canvas": "16:9",
  "output": "svg",
  "score_scale": {
    "min": 1,
    "max": 5
  },
  "items": [
    {
      "id": "A1",
      "name": "Automate report generation",
      "x_score": 2,
      "y_score": 5,
      "notes": "Low implementation effort, high productivity impact"
    }
  ],
  "show_side_table": true,
  "show_legend": true
}
```

The skill should also accept natural language input and convert it into this schema.

---

## 11. Preset: `action_priority`

### 11.1 Purpose

Use this preset to prioritize actions, improvement ideas, project tasks, or workshop outputs.

Typical user requests:

```text
Make an action priority matrix.
Prioritize these improvement actions.
Put these actions into impact vs effort.
Which actions should we do first?
```

### 11.2 Axes

```json
{
  "x_axis": "Effort / 执行难度",
  "x_low": "Low Effort / 低难度",
  "x_high": "High Effort / 高难度",
  "y_axis": "Impact / 影响力",
  "y_low": "Low Impact / 低影响",
  "y_high": "High Impact / 高影响"
}
```

### 11.3 Quadrants

| Quadrant | Meaning | Recommendation |
|---|---|---|
| Top-left | Quick Wins / 快速获胜 | Do first |
| Top-right | Major Projects / 重点项目 | Plan and phase |
| Bottom-left | Fill-ins / 可选机会 | Do when capacity allows |
| Bottom-right | Time Sinks / 投入产出低 | Defer or drop |

### 11.4 Side Table Columns

Use execution-oriented columns.

```json
{
  "columns": [
    "ID",
    "Action Item",
    "Impact",
    "Effort",
    "Quadrant",
    "Priority",
    "Recommended Action"
  ]
}
```

### 11.5 Default Priority Mapping

```text
Quick Wins     -> P1
Major Projects -> P2
Fill-ins       -> P3
Time Sinks     -> P4
```

### 11.6 Example Input

```json
{
  "diagram_type": "two_by_two_matrix",
  "preset": "action_priority",
  "title": "Action Priority Matrix",
  "items": [
    {"id": "A1", "name": "Automate weekly report", "x_score": 2, "y_score": 5},
    {"id": "A2", "name": "Redesign approval workflow", "x_score": 5, "y_score": 5},
    {"id": "A3", "name": "Update checklist format", "x_score": 1, "y_score": 2},
    {"id": "A4", "name": "Build custom dashboard", "x_score": 5, "y_score": 2}
  ]
}
```

---

## 12. Preset: `risk_benefit`

### 12.1 Purpose

Use this preset to compare initiatives, project options, technical choices, supplier changes, or process changes by expected benefit and risk.

Typical user requests:

```text
Compare these options by risk and benefit.
Make a risk-benefit matrix.
Which option has the best risk-return balance?
```

### 12.2 Axes

```json
{
  "x_axis": "Risk / 风险",
  "x_low": "Low Risk / 低风险",
  "x_high": "High Risk / 高风险",
  "y_axis": "Benefit / 收益",
  "y_low": "Low Benefit / 低收益",
  "y_high": "High Benefit / 高收益"
}
```

### 12.3 Quadrants

| Quadrant | Meaning | Recommendation |
|---|---|---|
| Top-left | Attractive / 优先推进 | Proceed |
| Top-right | Strategic Bet / 战略押注 | Proceed with mitigation |
| Bottom-left | Safe but Limited / 安全但价值有限 | Low priority |
| Bottom-right | Avoid / 避免 | Do not pursue |

### 12.4 Side Table Columns

Use decision-risk-oriented columns.

```json
{
  "columns": [
    "ID",
    "Option / Initiative",
    "Benefit",
    "Risk",
    "Risk Mitigation",
    "Quadrant",
    "Decision"
  ]
}
```

### 12.5 Default Decision Mapping

```text
Attractive        -> Proceed
Strategic Bet     -> Mitigate and review
Safe but Limited  -> Low priority
Avoid             -> Avoid
```

### 12.6 Example Input

```json
{
  "diagram_type": "two_by_two_matrix",
  "preset": "risk_benefit",
  "title": "Risk-Benefit Matrix",
  "items": [
    {"id": "O1", "name": "Switch supplier", "x_score": 4, "y_score": 5, "risk_mitigation": "Dual-source during transition"},
    {"id": "O2", "name": "Minor process update", "x_score": 1, "y_score": 2, "risk_mitigation": "Standard approval"}
  ]
}
```

---

## 13. Preset: `evidence_impact`

### 13.1 Purpose

Use this preset to screen possible causes after fishbone or fault tree brainstorming.

It is especially useful for failure analysis, root-cause screening, customer complaint review, and troubleshooting.

Typical user requests:

```text
Screen these causes by evidence and impact.
Put possible causes into an evidence-impact matrix.
Which causes should we verify first?
Which causes have high impact but weak evidence?
```

### 13.2 Axes

```json
{
  "x_axis": "Evidence / 证据强度",
  "x_low": "Weak Evidence / 证据弱",
  "x_high": "Strong Evidence / 证据强",
  "y_axis": "Impact / 影响程度",
  "y_low": "Low Impact / 低影响",
  "y_high": "High Impact / 高影响"
}
```

### 13.3 Quadrants

| Quadrant | Meaning | Recommendation |
|---|---|---|
| Top-right | Priority Causes / 优先原因 | Verify first or act |
| Top-left | Critical Hypotheses / 关键假设 | Collect data or run quick test |
| Bottom-right | Known Minor Causes / 已知次要原因 | Monitor or low-priority fix |
| Bottom-left | Low Priority / 低优先级 | Defer or exclude |

Note: This preset is different from `action_priority` because high evidence is good and points to confidence, not effort.

### 13.4 Side Table Columns

Use verification-oriented columns.

```json
{
  "columns": [
    "ID",
    "Possible Cause",
    "Evidence",
    "Impact",
    "Verification Method",
    "Quadrant",
    "Next Action"
  ]
}
```

### 13.5 Default Action Mapping

```text
Priority Causes     -> Verify first
Critical Hypotheses -> Get data
Known Minor Causes  -> Monitor
Low Priority        -> Defer or exclude
```

### 13.6 Example Input

```json
{
  "diagram_type": "two_by_two_matrix",
  "preset": "evidence_impact",
  "title": "Cause Screening: Evidence vs Impact",
  "items": [
    {
      "id": "C1",
      "name": "Power module fault",
      "x_score": 4,
      "y_score": 5,
      "verification_method": "Measure output voltage under load"
    },
    {
      "id": "C2",
      "name": "Firmware timing issue",
      "x_score": 2,
      "y_score": 5,
      "verification_method": "Check event logs and reproduce with debug firmware"
    },
    {
      "id": "C3",
      "name": "Operator handling variation",
      "x_score": 4,
      "y_score": 2,
      "verification_method": "Review handling records"
    }
  ]
}
```

---

## 14. Preset: `value_feasibility`

### 14.1 Purpose

Use this preset to screen product features, product concepts, technical ideas, design options, or roadmap candidates.

Typical user requests:

```text
Compare features by customer value and technical feasibility.
Make a value-feasibility matrix.
Which features should we build first?
Which ideas need technical exploration?
```

### 14.2 Axes

```json
{
  "x_axis": "Technical Feasibility / 技术可行性",
  "x_low": "Low Feasibility / 低可行性",
  "x_high": "High Feasibility / 高可行性",
  "y_axis": "Customer Value / 客户价值",
  "y_low": "Low Value / 低价值",
  "y_high": "High Value / 高价值"
}
```

### 14.3 Quadrants

| Quadrant | Meaning | Recommendation |
|---|---|---|
| Top-right | Build Now / 优先开发 | Implement soon |
| Top-left | Explore / 技术探索 | Prototype or research |
| Bottom-right | Nice to Have / 可选功能 | Backlog |
| Bottom-left | Avoid / 不建议 | Drop or defer |

### 14.4 Side Table Columns

Use product-planning-oriented columns.

```json
{
  "columns": [
    "ID",
    "Feature / Concept",
    "Customer Value",
    "Technical Feasibility",
    "Dependency",
    "Quadrant",
    "Product Decision"
  ]
}
```

### 14.5 Default Decision Mapping

```text
Build Now    -> Build
Explore      -> Prototype
Nice to Have -> Backlog
Avoid        -> Drop
```

### 14.6 Example Input

```json
{
  "diagram_type": "two_by_two_matrix",
  "preset": "value_feasibility",
  "title": "Feature Screening: Value vs Feasibility",
  "items": [
    {"id": "F1", "name": "Auto calibration", "x_score": 4, "y_score": 5, "dependency": "Sensor stability"},
    {"id": "F2", "name": "AI optimization mode", "x_score": 2, "y_score": 5, "dependency": "Model validation"},
    {"id": "F3", "name": "New color theme", "x_score": 5, "y_score": 2, "dependency": "UI resources"}
  ]
}
```

---

## 15. Preset: `urgency_importance`

### 15.1 Purpose

Use this preset to prioritize tasks, issues, meeting topics, escalations, or team actions.

This is similar to the Eisenhower Matrix.

Typical user requests:

```text
Organize these tasks by urgency and importance.
Make an urgency-importance matrix.
Which items should I do, schedule, delegate, or drop?
```

### 15.2 Axes

```json
{
  "x_axis": "Urgency / 紧急性",
  "x_low": "Not Urgent / 不紧急",
  "x_high": "Urgent / 紧急",
  "y_axis": "Importance / 重要性",
  "y_low": "Low Importance / 低重要性",
  "y_high": "High Importance / 高重要性"
}
```

### 15.3 Quadrants

| Quadrant | Meaning | Recommendation |
|---|---|---|
| Top-right | Do Now / 立即处理 | Act immediately |
| Top-left | Schedule / 计划安排 | Schedule and protect time |
| Bottom-right | Delegate / 委派处理 | Delegate or simplify |
| Bottom-left | Eliminate / 删除 | Drop or ignore |

### 15.4 Side Table Columns

Use task-management-oriented columns.

```json
{
  "columns": [
    "ID",
    "Task / Issue",
    "Importance",
    "Urgency",
    "Owner",
    "Due Date",
    "Quadrant",
    "Action"
  ]
}
```

### 15.5 Default Action Mapping

```text
Do Now    -> Do now
Schedule  -> Schedule
Delegate  -> Delegate
Eliminate -> Drop
```

### 15.6 Example Input

```json
{
  "diagram_type": "two_by_two_matrix",
  "preset": "urgency_importance",
  "title": "Urgency-Importance Matrix",
  "items": [
    {"id": "T1", "name": "Prepare customer review", "x_score": 5, "y_score": 5, "owner": "Team lead", "due_date": "This week"},
    {"id": "T2", "name": "Update template library", "x_score": 2, "y_score": 3, "owner": "Ops", "due_date": "Next month"}
  ]
}
```

---

## 16. Optional Future Preset: `cost_performance`

This preset is useful for engineering option comparison, supplier comparison, material selection, or design trade-off.

Axes:

```json
{
  "x_axis": "Cost / 成本",
  "y_axis": "Performance / 性能"
}
```

Quadrants:

| Quadrant | Meaning | Recommendation |
|---|---|---|
| Top-left | Best Value / 最优性价比 | Select first |
| Top-right | Premium Option / 高端方案 | Use for premium or critical cases |
| Bottom-left | Budget Option / 低成本方案 | Use for non-critical cases |
| Bottom-right | Poor Value / 不推荐 | Avoid |

Side table columns:

```json
{
  "columns": [
    "ID",
    "Option",
    "Performance",
    "Cost",
    "Constraint",
    "Quadrant",
    "Recommendation"
  ]
}
```

---

## 17. Optional Future Preset: `impact_confidence`

This preset is useful for innovation ideas, early R&D hypotheses, product experiments, and uncertain opportunities.

Axes:

```json
{
  "x_axis": "Confidence / 信心程度",
  "y_axis": "Impact / 潜在影响"
}
```

Quadrants:

| Quadrant | Meaning | Recommendation |
|---|---|---|
| Top-right | Strong Bets / 强推荐 | Prioritize |
| Top-left | Big Bets / 高潜力假设 | Experiment first |
| Bottom-right | Incremental Improvements / 小改进 | Do if low cost |
| Bottom-left | Weak Ideas / 弱想法 | Defer |

Side table columns:

```json
{
  "columns": [
    "ID",
    "Idea / Hypothesis",
    "Impact",
    "Confidence",
    "Key Assumption",
    "Experiment",
    "Quadrant",
    "Next Step"
  ]
}
```

---

## 18. Optional Future Preset: `complexity_value`

This preset is useful for software, platform, process, or system improvement work.

Axes:

```json
{
  "x_axis": "Complexity / 复杂度",
  "y_axis": "Value / 价值"
}
```

Quadrants:

| Quadrant | Meaning | Recommendation |
|---|---|---|
| Top-left | Quick Wins / 快速收益 | Do first |
| Top-right | Strategic Work / 战略工作 | Phase and plan |
| Bottom-left | Minor Improvements / 小优化 | Backlog |
| Bottom-right | Avoid / 避免 | Do not pursue |

Side table columns:

```json
{
  "columns": [
    "ID",
    "Work Item",
    "Value",
    "Complexity",
    "Dependency",
    "Quadrant",
    "Recommendation"
  ]
}
```

---

## 19. Side Table Design

### 19.1 Principle

The matrix layout stays the same. The right-side table changes by preset.

The side table should help the viewer understand:

1. What each point represents.
2. Why it appears in that quadrant.
3. What the recommended next action is.

### 19.2 Shared Table Fields

All presets should support these internal fields:

```json
{
  "shared_fields": [
    "id",
    "name",
    "x_score",
    "y_score",
    "quadrant",
    "priority_or_decision",
    "recommendation"
  ]
}
```

### 19.3 Preset-Specific Fields

Each preset defines its displayed columns.

For example:

```json
{
  "preset": "evidence_impact",
  "display_columns": [
    "ID",
    "Possible Cause",
    "Evidence",
    "Impact",
    "Verification Method",
    "Quadrant",
    "Next Action"
  ]
}
```

### 19.4 Table Rendering Rules

- Use a navy header row.
- Use white or very pale blue body rows.
- Use light gray row separators.
- Use small rounded status chips for priority, action, or decision.
- Keep text concise.
- Support up to 20 items. The side decision table must show every item; inputs above 20 should be rejected with a clear error.
- The matrix body may summarize dense quadrants, but it must not imply that table rows were omitted.
- Do not shrink text below readability.

### 19.5 Status Chips

Recommended status chip style:

```json
{
  "shape": "rounded_rectangle",
  "height": 24,
  "corner_radius": 12,
  "font_size": 12,
  "fill": "#EAF3FF",
  "stroke": "#6E93BD",
  "text_color": "#0B3A75"
}
```

Use stronger colors only for explicit actions such as Avoid, Drop, Verify first, or Do now.

---

## 20. Natural Language Inference

The skill should infer presets from common terms.

### 20.1 Inference Rules

| User Language | Inferred Preset |
|---|---|
| action priority, quick wins, impact vs effort, prioritize actions | `action_priority` |
| risk benefit, risk return, trade-off, risk vs reward | `risk_benefit` |
| evidence impact, causes, failure causes, root cause screening, FA screening | `evidence_impact` |
| value feasibility, feature priority, customer value, product roadmap | `value_feasibility` |
| urgency importance, Eisenhower, task priority, do schedule delegate | `urgency_importance` |
| cost performance, supplier selection, material trade-off | `cost_performance` |
| impact confidence, idea confidence, experiment priority | `impact_confidence` |
| value complexity, complexity vs value, system improvement | `complexity_value` |

### 20.2 Fallback Rules

If the user asks for a generic 2x2 matrix and does not provide dimensions:

Use `action_priority` as the default preset.

```json
{
  "diagram_type": "two_by_two_matrix",
  "preset": "action_priority"
}
```

If the user provides custom axes:

Use:

```json
{
  "diagram_type": "two_by_two_matrix",
  "preset": "custom",
  "x_axis": "...",
  "y_axis": "..."
}
```

Only ask for clarification if both axes and business intent are missing and the user expects a precise output.

---

## 21. Custom Preset

Support a custom preset for user-defined axes.

Example:

```json
{
  "diagram_type": "two_by_two_matrix",
  "preset": "custom",
  "x_axis": "Manufacturing Difficulty / 制造难度",
  "y_axis": "Customer Differentiation / 客户差异化",
  "quadrants": {
    "top_left": "High Differentiation / Low Difficulty",
    "top_right": "High Differentiation / High Difficulty",
    "bottom_left": "Low Differentiation / Low Difficulty",
    "bottom_right": "Low Differentiation / High Difficulty"
  },
  "items": []
}
```

For custom preset, use generic side table columns:

```json
{
  "columns": [
    "ID",
    "Item",
    "X Score",
    "Y Score",
    "Quadrant",
    "Recommendation"
  ]
}
```

---

## 22. Output Requirements

Primary output:

```text
SVG
```

Optional output:

```text
PNG
```

SVG is preferred because:

- It is scalable.
- It can be inserted into PowerPoint.
- It preserves sharp vector graphics.
- It is deterministic and editable.

The generator should not use raster AI image generation.

---

## 23. Recommended File Structure

```text
brainstorm-diagrams/
├─ SKILL.md
├─ specs/
│  ├─ fishbone.md
│  ├─ fault_tree.md
│  ├─ exclusion_tree.md
│  └─ two_by_two_matrix.md
├─ scripts/
│  ├─ generate_fishbone.py
│  ├─ generate_fault_tree.py
│  ├─ generate_exclusion_tree.py
│  └─ generate_two_by_two_matrix.py
├─ templates/
│  ├─ fishbone.business_simple.svg.j2
│  ├─ fault_tree.business_simple.svg.j2
│  ├─ exclusion_tree.business_simple.svg.j2
│  └─ two_by_two_matrix.business_simple.svg.j2
├─ examples/
│  ├─ two_by_two_action_priority.json
│  ├─ two_by_two_evidence_impact.json
│  ├─ two_by_two_value_feasibility.json
│  └─ two_by_two_output_example.svg
└─ README.md
```

---

## 24. Implementation Guidance

Use Python.

Recommended libraries:

```text
jinja2
xml.etree.ElementTree
cairosvg, optional for PNG export
```

The generator should:

1. Parse JSON input.
2. Infer preset if missing.
3. Load preset config.
4. Compute quadrant for each item.
5. Compute item coordinates.
6. Generate side table content from preset-specific columns.
7. Render SVG using a Jinja2 template.
8. Validate SVG is well formed.
9. Optionally export PNG.

---

## 25. Preset Config Design

Codex should implement preset configuration as data, not hard-coded layout branches.

Example:

```python
PRESETS = {
    "action_priority": {
        "title": "Action Priority Matrix",
        "x_axis": "Effort / 执行难度",
        "x_low": "Low Effort / 低难度",
        "x_high": "High Effort / 高难度",
        "y_axis": "Impact / 影响力",
        "y_low": "Low Impact / 低影响",
        "y_high": "High Impact / 高影响",
        "quadrants": {
            "top_left": {
                "label": "Quick Wins / 快速获胜",
                "recommendation": "Do first",
                "priority": "P1"
            },
            "top_right": {
                "label": "Major Projects / 重点项目",
                "recommendation": "Plan and phase",
                "priority": "P2"
            },
            "bottom_left": {
                "label": "Fill-ins / 可选机会",
                "recommendation": "Do when possible",
                "priority": "P3"
            },
            "bottom_right": {
                "label": "Time Sinks / 投入产出低",
                "recommendation": "Defer or drop",
                "priority": "P4"
            }
        },
        "table_columns": [
            "ID",
            "Action Item",
            "Impact",
            "Effort",
            "Quadrant",
            "Priority",
            "Recommended Action"
        ]
    }
}
```

---

## 26. Quadrant Calculation

Given scores:

```json
{
  "x_score": 4,
  "y_score": 2,
  "score_scale": {"min": 1, "max": 5}
}
```

Use midpoint:

```text
mid = (min + max) / 2
```

Classification:

```text
if y_score >= mid and x_score < mid:  top_left
if y_score >= mid and x_score >= mid: top_right
if y_score < mid and x_score < mid:   bottom_left
if y_score < mid and x_score >= mid:  bottom_right
```

Use `>= mid` consistently so that middle values go to the high side.

For a 1-5 scale, score 3 is treated as high.

---

## 27. Handling Many Items

Recommended rules:

| Number of items | Rendering approach |
|---:|---|
| 1-8 | Show labels directly in the matrix and table |
| 9-20 | Show concise quadrant summaries in the matrix, details for every item in the table |
| >20 | Reject the input and ask the author to split or reduce the item list |

Avoid overcrowding the matrix.

If multiple items overlap, apply deterministic jitter within a small radius.

---

## 28. Label Collision Handling

The renderer should avoid unreadable label overlap.

Recommended strategy:

1. If item count <= 8, place labels near markers.
2. If labels overlap, switch to ID-only markers.
3. Always show full item names in the side table.
4. Never reduce font size below 11 px.

---

## 29. Language Support

Support language modes:

```json
{
  "language": "auto | en | zh"
}
```

Default:

```text
auto
```

In `auto` mode, infer the display language from the input. English input should produce English labels. Chinese input should produce Chinese labels. The diagram should not show English/Chinese paired labels unless the user explicitly provides such labels as source content.

---

## 30. Visual Quality Checks

Before returning output, verify:

1. SVG opens in a browser.
2. Axis labels are visible and not clipped.
3. Quadrant labels are readable.
4. Item markers stay within matrix boundaries.
5. Side table does not overflow the slide.
6. Text is not too small.
7. Design matches business-simple style.
8. Color palette is consistent with fishbone, fault tree, and exclusion tree.
9. The diagram is suitable for PowerPoint.
10. No decorative 3D, cartoon, or realistic graphics are included.

---

## 31. Forbidden Design Choices

Do not use:

- 3D chart effects.
- Heavy shadows.
- Neon cyberpunk style.
- Cartoon icons.
- Realistic illustration.
- Hand-drawn style.
- Dense spreadsheet-like layout that is unreadable.
- Highly saturated quadrant colors.
- Unlabeled axes.
- Axis directions that contradict quadrant names.

---

## 32. Example: Full `action_priority` Input

```json
{
  "diagram_type": "two_by_two_matrix",
  "preset": "action_priority",
  "title": "Action Priority Matrix",
  "subtitle": "Prioritize improvement actions by impact and effort",
  "language": "auto",
  "style": "business_simple",
  "score_scale": {"min": 1, "max": 5},
  "items": [
    {"id": "A1", "name": "Automate weekly report", "x_score": 2, "y_score": 5, "owner": "Ops"},
    {"id": "A2", "name": "Redesign approval workflow", "x_score": 5, "y_score": 5, "owner": "Process"},
    {"id": "A3", "name": "Standardize checklist", "x_score": 1, "y_score": 3, "owner": "Quality"},
    {"id": "A4", "name": "Build custom dashboard", "x_score": 5, "y_score": 2, "owner": "IT"},
    {"id": "A5", "name": "Update training material", "x_score": 2, "y_score": 3, "owner": "Training"}
  ],
  "show_side_table": true,
  "show_legend": true,
  "output": "svg"
}
```

---

## 33. Example: Full `evidence_impact` Input

```json
{
  "diagram_type": "two_by_two_matrix",
  "preset": "evidence_impact",
  "title": "Cause Screening Matrix",
  "subtitle": "Screen possible causes by evidence strength and impact",
  "language": "auto",
  "style": "business_simple",
  "score_scale": {"min": 1, "max": 5},
  "items": [
    {
      "id": "C1",
      "name": "Power module fault",
      "x_score": 4,
      "y_score": 5,
      "verification_method": "Measure output voltage under load"
    },
    {
      "id": "C2",
      "name": "Firmware timing issue",
      "x_score": 2,
      "y_score": 5,
      "verification_method": "Check logs and reproduce with debug firmware"
    },
    {
      "id": "C3",
      "name": "Connector contamination",
      "x_score": 3,
      "y_score": 4,
      "verification_method": "Inspect connector under microscope"
    },
    {
      "id": "C4",
      "name": "Operator handling variation",
      "x_score": 4,
      "y_score": 2,
      "verification_method": "Review process records"
    },
    {
      "id": "C5",
      "name": "Ambient temperature drift",
      "x_score": 2,
      "y_score": 2,
      "verification_method": "Check environmental logs"
    }
  ],
  "show_side_table": true,
  "show_legend": true,
  "output": "svg"
}
```

---

## 34. Suggested `SKILL.md` Addition

Add this section to the main `SKILL.md` for `brainstorm-diagrams`:

```markdown
## Diagram Type: two_by_two_matrix

Use `two_by_two_matrix` when the user wants to prioritize, screen, compare, or classify items using two dimensions.

The diagram type supports presets. Presets define the business meaning of the axes, quadrant labels, side table columns, and recommended actions.

Supported presets:
- `action_priority`: Impact vs Effort for action prioritization.
- `risk_benefit`: Benefit vs Risk for project or option decisions.
- `evidence_impact`: Impact vs Evidence for cause screening and failure analysis.
- `value_feasibility`: Customer Value vs Technical Feasibility for product design.
- `urgency_importance`: Importance vs Urgency for task and issue management.

Do not require the user to specify a preset explicitly. Infer it from natural language whenever possible. If no preset can be inferred, default to `action_priority`.

Always use the business-simple visual style: white or light background, navy and light-blue accents, clean typography, clear axis labels, readable quadrant labels, and optional right-side table.
```

---

## 35. Codex Implementation Prompt

Use the following prompt when asking Codex to implement this module:

```text
Implement the `two_by_two_matrix` diagram type for the existing `brainstorm-diagrams` skill.

The implementation must generate PPT-ready SVG diagrams in the same business-simple visual style as the fishbone, fault_tree, and exclusion_tree templates.

Use a single reusable two-by-two matrix SVG template. Do not create separate diagram types for action priority, risk-benefit, evidence-impact, value-feasibility, or urgency-importance. Instead, implement a `preset` parameter that controls axis labels, quadrant names, side table columns, and recommended actions.

First supported presets:
- action_priority
- risk_benefit
- evidence_impact
- value_feasibility
- urgency_importance

The user should not need to specify preset explicitly. Add natural-language inference rules so phrases such as "impact vs effort", "risk benefit", "evidence impact", "value feasibility", and "urgency importance" map to the correct preset. If preset is missing and cannot be inferred, default to action_priority.

The SVG layout should include:
- title and subtitle
- large 2x2 matrix on the left or center
- optional side table on the right
- axis labels with Low/High direction labels
- quadrant labels and short descriptions
- item markers positioned by x_score and y_score
- readable side table with preset-specific columns
- optional legend or interpretation note

Use deterministic layout and avoid AI image generation. Validate that the SVG opens in a browser. Keep all text readable and avoid marker overlap where possible.
```

---

## 36. Version Plan

Recommended release plan:

```text
v0.1 fishbone
v0.2 fault_tree
v0.3 exclusion_tree
v0.4 two_by_two_matrix with presets
v0.5 cause_screening_matrix
v0.6 process_flow / swimlane
v0.7 qfd_house_of_quality / morphological_matrix
```

The `two_by_two_matrix` module should be implemented as v0.4 because it is a general screening and prioritization layer that can support product design, process design, failure analysis, and brainstorming follow-up.

---

## 37. Final Acceptance Criteria

The implementation is acceptable when:

1. It generates a valid SVG for each first-supported preset.
2. Each preset has correct axes and quadrant labels.
3. Each preset has different right-side table columns where appropriate.
4. The style visually matches the existing business-simple diagram family.
5. The diagram can be inserted into PowerPoint.
6. Natural language can infer common presets.
7. The user can still provide a custom two-axis matrix.
8. The diagram remains readable with at least 8 items.
9. It avoids overcomplicating the user interface by keeping `preset` optional and inferable.
10. It does not create separate diagram types for each 2x2 business use case.
