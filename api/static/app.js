'use strict';

// ── Constantes ────────────────────────────────────────────────────────────────

const COLORES = {
  primario:   '#1F4E78',
  baseline:   '#E67E22',
  lightgbm:   '#9B59B6',
  xgboost:    '#16A085',
  prophet:    '#E91E63',
  verde:      '#27AE60',
  rojo:       '#C0392B',
  slate400:   '#94A3B8',
  slate700:   '#334155',
  slate800:   '#1E293B',
};

const NOMBRES_MODELO = {
  baseline_ma4: 'Baseline (MA-4)',
  lightgbm:     'LightGBM',
  xgboost:      'XGBoost',
  prophet:      'Prophet',
};

const COLOR_MODELO = {
  baseline_ma4: COLORES.baseline,
  lightgbm:     COLORES.lightgbm,
  xgboost:      COLORES.xgboost,
  prophet:      COLORES.prophet,
};

const SEMANAS = [
  '2025-10-06','2025-10-13','2025-10-20','2025-10-27',
  '2025-11-03','2025-11-10','2025-11-17','2025-11-24',
  '2025-12-01','2025-12-08','2025-12-15','2025-12-22','2025-12-29',
  '2026-01-05','2026-01-12','2026-01-19','2026-01-26',
  '2026-02-02','2026-02-09','2026-02-16','2026-02-23',
  '2026-03-02','2026-03-09','2026-03-16','2026-03-23','2026-03-30',
];

// ── Helpers ───────────────────────────────────────────────────────────────────

function configChart() {
  if (typeof Chart === 'undefined') return;
  Chart.defaults.color = COLORES.slate400;
  Chart.defaults.borderColor = COLORES.slate800;
}

async function apiFetch(path) {
  const res = await fetch(path);
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(err?.detail?.message || `HTTP ${res.status}`);
  }
  return res.json();
}

function fmt(n, decimals = 0) {
  if (n == null) return '—';
  return Number(n).toLocaleString('es-CO', { maximumFractionDigits: decimals });
}

function fmtPct(n) {
  if (n == null) return '—';
  return `${n > 0 ? '+' : ''}${Number(n).toFixed(1)}%`;
}

function fmtCOP(v) {
  if (v == null) return '—';
  if (v >= 1_000_000_000)
    return '$' + (v / 1_000_000).toLocaleString('es-CO', { maximumFractionDigits: 0 }) + 'M';
  if (v >= 1_000_000)
    return '$' + (v / 1_000_000).toLocaleString('es-CO', { maximumFractionDigits: 1 }) + 'M';
  if (v >= 1_000)
    return '$' + (v / 1_000).toLocaleString('es-CO', { maximumFractionDigits: 0 }) + 'K';
  return '$' + Number(v).toFixed(0);
}

function destroyChart(ref) {
  if (ref && typeof ref.destroy === 'function') ref.destroy();
}

// ── Componente Alpine ─────────────────────────────────────────────────────────

function app() {
  return {
    // ── navegación ──
    tab: 'resumen',
    loaded: {},
    tabs: [
      { id: 'resumen',       label: 'Resumen',        icon: 'bar-chart-3'    },
      { id: 'pronosticos',   label: 'Pronósticos',    icon: 'trending-up'    },
      { id: 'modelos',       label: 'Modelos',        icon: 'git-compare'    },
      { id: 'clasificacion', label: 'Clasificación',  icon: 'layers'         },
      { id: 'insights',      label: 'Insights',       icon: 'alert-triangle' },
    ],

    // ── resumen ──
    resumen:        null,
    metricasGlobal: null,
    loadingRes:     false,
    errorRes:       null,

    // ── pronósticos/top ──
    topData:        null,
    loadingTop:     false,
    errorTop:       null,
    topFecha:       '2026-01-05',
    topCentro:      '',
    topLimit:       20,
    semanas:        SEMANAS,

    // ── drawer sku ──
    drawerOpen:     false,
    skuData:        null,
    skuLoading:     false,
    skuError:       null,

    // ── modelos ──
    metricasData:   null,
    loadingMet:     false,
    errorMet:       null,
    metSplit:       'test_2026',
    metSegmento:    'global',

    // ── insights ──
    insightsTab:    'crecimiento',
    crecData:       null,
    loadingCrec:    false,
    errorCrec:      null,
    crecFecha:      '2026-01-05',
    crecSoloAB:     false,
    alertasData:    null,
    loadingAlertas: false,
    errorAlertas:   null,
    alertasFecha:   '2026-01-05',
    alertasUmbral:  100,
    alertasSoloAB:  true,

    // ── instancias de chart ──
    _skuChart:      null,

    // ─────────────────────────────────────────────────────────────────────────

    async init() {
      configChart();
      await this.loadResumen();
      this.$nextTick(() => {
        if (window.lucide) lucide.createIcons();
      });
    },

    async switchTab(t) {
      this.tab = t;
      this.$nextTick(() => { if (window.lucide) lucide.createIcons(); });
      if (this.loaded[t]) return;
      this.loaded[t] = true;
      switch (t) {
        case 'pronosticos':   await this.loadTop(); break;
        case 'modelos':       await this.loadMetricas(); break;
        case 'clasificacion': break; // datos ya vienen del resumen
        case 'insights':      await this.loadCrecimiento(); break;
      }
    },

    // ── Resumen ───────────────────────────────────────────────────────────────

    async loadResumen() {
      this.loadingRes = true; this.errorRes = null;
      try {
        [this.resumen, this.metricasGlobal] = await Promise.all([
          apiFetch('/api/clasificacion/resumen'),
          apiFetch('/api/metricas/comparacion?split=test_2026&segmento=global'),
        ]);
      } catch (e) {
        this.errorRes = e.message;
      } finally {
        this.loadingRes = false;
      }
    },

    get kpiMaeLightgbm() {
      if (!this.metricasGlobal) return null;
      return this.metricasGlobal.modelos.find(m => m.modelo === 'lightgbm')?.mae;
    },
    get kpiMejora() {
      if (!this.metricasGlobal) return null;
      return this.metricasGlobal.modelos.find(m => m.modelo === 'lightgbm')?.mejora_vs_baseline_pct;
    },

    barModelos() {
      if (!this.metricasGlobal) return [];
      const modelos = this.metricasGlobal.modelos
        .filter(m => m.modelo !== 'prophet')
        .sort((a, b) => b.mae - a.mae);
      const maxMae = Math.max(...modelos.map(m => m.mae));
      return modelos.map(m => ({
        nombre: NOMBRES_MODELO[m.modelo] || m.nombre_amigable,
        mae:    m.mae,
        pct:    Math.round((m.mae / maxMae) * 100),
        color:  COLOR_MODELO[m.modelo] || COLORES.slate700,
      }));
    },

    get barrasABC() {
      if (!this.resumen?.distribucion_abc) return [];
      const dist    = this.resumen.distribucion_abc;
      const colores = { A: '#27AE60', B: '#F59E0B', C: '#C0392B' };
      return ['A', 'B', 'C'].map(clase => ({
        clase,
        color:      colores[clase],
        num_skus:   (dist[clase]?.num_skus || 0).toLocaleString('es-CO'),
        porcentaje: (dist[clase]?.porcentaje_skus || 0).toFixed(1),
      }));
    },

    // ── Pronósticos ───────────────────────────────────────────────────────────

    async loadTop() {
      this.loadingTop = true; this.errorTop = null;
      try {
        const params = new URLSearchParams({
          fecha: this.topFecha,
          limit: this.topLimit,
          modelo: 'lightgbm',
        });
        if (this.topCentro) params.set('centro', this.topCentro);
        this.topData = await apiFetch(`/api/pronosticos/top?${params}`);
      } catch (e) {
        this.errorTop = e.message;
      } finally {
        this.loadingTop = false;
      }
    },

    async openSKU(item) {
      this.drawerOpen = true;
      this.skuLoading = true;
      this.skuData = null;
      this.skuError = null;
      destroyChart(this._skuChart);
      try {
        this.skuData = await apiFetch(`/api/pronosticos/sku/${item}`);
        this.$nextTick(() => this.initSkuChart());
      } catch (e) {
        this.skuError = e.message;
      } finally {
        this.skuLoading = false;
      }
    },

    closeSKU() {
      this.drawerOpen = false;
      destroyChart(this._skuChart);
      this._skuChart = null;
    },

    initSkuChart() {
      const canvas = document.getElementById('skuChart');
      if (!canvas || !this.skuData) return;
      destroyChart(this._skuChart);
      const serie = this.skuData.serie;
      const labels = serie.map(p => p.fecha.slice(5));  // MM-DD
      const real   = serie.map(p => p.cantidad_real);
      const pred   = serie.map(p => p.cantidad_predicha_principal);
      const base   = serie.map(p => p.cantidad_predicha_baseline);

      this._skuChart = new Chart(canvas, {
        type: 'line',
        data: {
          labels,
          datasets: [
            {
              label: 'Real',
              data: real,
              borderColor: '#60a5fa',
              backgroundColor: 'rgba(96,165,250,0.08)',
              borderWidth: 1.8,
              pointRadius: 0,
              tension: 0.3,
              fill: true,
              spanGaps: false,
            },
            {
              label: 'LightGBM',
              data: pred,
              borderColor: COLORES.lightgbm,
              borderWidth: 2,
              pointRadius: 0,
              tension: 0.3,
              spanGaps: false,
            },
            {
              label: 'Baseline',
              data: base,
              borderColor: COLORES.baseline,
              borderWidth: 1.5,
              borderDash: [4, 3],
              pointRadius: 0,
              tension: 0.3,
              spanGaps: false,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          interaction: { mode: 'index', intersect: false },
          plugins: {
            legend: { labels: { color: COLORES.slate400, boxWidth: 18, font: { size: 11 } } },
          },
          scales: {
            x: { grid: { color: COLORES.slate800 }, ticks: { color: COLORES.slate400, maxTicksLimit: 12, maxRotation: 45 } },
            y: { grid: { color: COLORES.slate800 }, ticks: { color: COLORES.slate400 } },
          },
        },
      });
    },

    // ── Modelos ───────────────────────────────────────────────────────────────

    async loadMetricas() {
      this.loadingMet = true; this.errorMet = null;
      try {
        const params = new URLSearchParams({ split: this.metSplit, segmento: this.metSegmento });
        this.metricasData = await apiFetch(`/api/metricas/comparacion?${params}`);
      } catch (e) {
        this.errorMet = e.message;
        this.metricasData = null;
      } finally {
        this.loadingMet = false;
      }
    },

    bestMae() {
      if (!this.metricasData) return Infinity;
      return Math.min(...this.metricasData.modelos.map(m => m.mae));
    },

    // ── Clasificación ─────────────────────────────────────────────────────────

    heatCell(abc, xyz) {
      if (!this.resumen) return { num_skus: 0, valor_total: 0 };
      return this.resumen.matriz_segmentos.find(s => s.clase_abc === abc && s.clase_xyz === xyz)
        || { num_skus: 0, valor_total: 0 };
    },

    heatClass(abc, xyz) {
      if (!this.resumen) return 'heat-xs';
      const maxSkus = Math.max(...this.resumen.matriz_segmentos.map(s => s.num_skus));
      const cell = this.heatCell(abc, xyz);
      const r = cell.num_skus / maxSkus;
      if (r > 0.7) return 'heat-xl';
      if (r > 0.4) return 'heat-lg';
      if (r > 0.15) return 'heat-md';
      if (r > 0.03) return 'heat-sm';
      return 'heat-xs';
    },

    // ── Insights ──────────────────────────────────────────────────────────────

    async loadCrecimiento() {
      this.loadingCrec = true; this.errorCrec = null;
      try {
        const params = new URLSearchParams({
          fecha_objetivo: this.crecFecha,
          limit: 15,
          solo_clase_ab: this.crecSoloAB,
        });
        this.crecData = await apiFetch(`/api/insights/crecimiento?${params}`);
      } catch (e) {
        this.errorCrec = e.message;
      } finally {
        this.loadingCrec = false;
      }
    },

    async loadAlertas() {
      this.loadingAlertas = true; this.errorAlertas = null;
      try {
        const params = new URLSearchParams({
          fecha_objetivo: this.alertasFecha,
          umbral_cambio_pct: this.alertasUmbral,
          solo_clase_ab: this.alertasSoloAB,
        });
        this.alertasData = await apiFetch(`/api/insights/alertas?${params}`);
      } catch (e) {
        this.errorAlertas = e.message;
      } finally {
        this.loadingAlertas = false;
      }
    },

    switchInsightsTab(t) {
      this.insightsTab = t;
      if (t === 'crecimiento' && !this.crecData) this.loadCrecimiento();
      if (t === 'alertas'     && !this.alertasData) this.loadAlertas();
    },

    // ── Helpers UI ────────────────────────────────────────────────────────────
    fmt,
    fmtPct,
    fmtCOP,

    badgeABC(clase) {
      return clase === 'A' ? 'badge-a' : clase === 'B' ? 'badge-b' : 'badge-c';
    },
    badgeSeveridad(sev) {
      return sev === 'alta' ? 'badge-alta' : sev === 'media' ? 'badge-media' : 'badge-baja';
    },
    flechaCambio(pct) {
      return pct > 10 ? '▲' : pct < -10 ? '▼' : '─';
    },
    colorCambio(pct) {
      return pct > 10 ? 'text-emerald-400' : pct < -10 ? 'text-red-400' : 'text-slate-400';
    },
  };
}
