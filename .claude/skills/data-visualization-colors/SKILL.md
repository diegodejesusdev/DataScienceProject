# Data Visualization Colors — Semantic Color System

## Core Principle
Color = meaning, not decoration.
Red MUST be reserved for actual problems, errors, or operational alerts.
Red MUST NOT be used for neutral categories (class C in ABC is not bad).

## Semantic Palette

Models (consistent across all charts):
- Baseline (MA-4): #E67E22 (orange)
- LightGBM: #9B59B6 (purple)
- XGBoost: #16A085 (teal)
- Prophet: #E91E63 (pink)
- Real data: #1F4E78 (dark blue)

ABC class (value concentration, NOT performance):
- A: #10B981 (emerald — high value)
- B: #6366F1 (indigo — medium)
- C: #64748B (slate — neutral, NOT red)

ABC×XYZ matrix segments:
- AX, AY (star): #10B981 (emerald)
- AZ, BX, BY (strategic): #6366F1 (indigo)
- BZ, CX, CY (routine): #64748B (slate)
- CZ (long tail): #475569 (dark slate — neutral, NOT red)

Alerts (ONLY for operational alerts):
- High: #DC2626 (red)
- Medium: #F59E0B (amber)
- Low: #0EA5E9 (sky)

Performance (measuring error/accuracy — here red IS correct):
- Excellent: #16A34A
- Good: #84CC16
- Moderate: #F59E0B
- Poor: #DC2626

## Anti-patterns (NEVER)
- Red for Class C in ABC matrices
- Red for non-error cells in heatmaps
- More than 5 colors in a single chart
- Rainbow gradients for ordinal categories

## Decision checklist before assigning any color
1. Does red here mean something is actually wrong?
2. Would a colorblind user understand the meaning?
3. Does the gradient match the semantic direction?
4. Is this color communicating or just decorating?
