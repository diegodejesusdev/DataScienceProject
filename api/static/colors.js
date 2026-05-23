'use strict';

// Semantic color constants — ConstruNorte Data Visualization System
// See .claude/skills/data-visualization-colors/SKILL.md

const COLORS_MODELO = {
  baseline_ma4: '#E67E22',
  lightgbm:     '#9B59B6',
  xgboost:      '#16A085',
  prophet:      '#E91E63',
  real:         '#1F4E78',
};

const COLORS_ABC = {
  A: '#10B981',  // emerald — high value concentration
  B: '#6366F1',  // indigo — medium
  C: '#64748B',  // slate — neutral long tail, NOT red
};

// Semantic color by ABC×XYZ segment type
const COLORS_SEGMENTO = {
  AX: '#10B981', AY: '#10B981',            // star
  AZ: '#6366F1',                            // strategic
  BX: '#6366F1', BY: '#6366F1',            // strategic
  BZ: '#64748B',                            // routine
  CX: '#64748B', CY: '#64748B',            // routine
  CZ: '#475569',                            // long tail — dark slate
};

const COLORS_ALERTA = {
  alta:  '#DC2626',  // red — real operational problem
  media: '#F59E0B',  // amber
  baja:  '#0EA5E9',  // sky
};
